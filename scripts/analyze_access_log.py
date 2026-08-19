#!/usr/bin/env python3
"""Caddyのアクセスログ(study.log, JSON Lines)を日別に集計する。

生ログはCaddy側でサイズロールオフ(10MB×5世代)されて消えていくため、
このスクリプトの集計結果を data/analytics/access_summary.jsonl に
日次で追記して残す(2026-08-13〜)。個々のIPアドレスそのものは
出力に残さず、件数・ページ別内訳・参照元・bot判定などの集計値のみを
記録する。

使い方(VPS上、eigo-appコンテナの外・ホストのpython3で実行を想定):
  docker exec aipoc-web cat /var/log/caddy/study.log \
    | python3 scripts/analyze_access_log.py \
        --json-out data/analytics/access_summary.jsonl

  # ローテーション済みの過去ログ(.gz)も含めたい場合はまとめて展開してパイプする:
  for f in study-*.log.gz; do zcat "$f"; done | cat - study.log \
    | python3 scripts/analyze_access_log.py \
        --json-out data/analytics/access_summary.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

# 日本時間(UTC+9、夏時間なし)の日付境界で集計する(2026-08-19〜)。
# zoneinfo("Asia/Tokyo")はVPSホスト側にtzdataが無いと失敗しうるため、
# 固定オフセットで代用する(JSTはDSTが無いのでこれで常に正確)。
JST = timezone(timedelta(hours=9))

# LLMO(生成AIに見つかる/引用される)観点で特に把握したいAIクローラー。
AI_CRAWLERS = [
    "GPTBot", "ChatGPT-User", "OAI-SearchBot", "ClaudeBot", "Claude-Web",
    "anthropic-ai", "PerplexityBot", "Perplexity-User", "Google-Extended",
    "Bytespider", "CCBot", "Applebot-Extended", "cohere-ai", "Diffbot",
    "meta-externalagent",
]
SEARCH_BOTS = [
    "Googlebot", "bingbot", "DuckDuckBot", "YandexBot", "Baiduspider",
    "Slurp", "Sogou",
]


def classify_ua(ua: str) -> str:
    if not ua:
        return "unknown"
    low = ua.lower()
    for name in AI_CRAWLERS:
        if name.lower() in low:
            return f"ai_crawler:{name}"
    for name in SEARCH_BOTS:
        if name.lower() in low:
            return f"search_bot:{name}"
    if any(k in low for k in
           ("bot", "crawler", "spider", "curl", "python-requests", "wget")):
        return "other_bot"
    return "human"


def _first(headers: dict, key: str) -> str:
    v = headers.get(key) or headers.get(key.lower())
    if not v:
        return ""
    return v[0] if isinstance(v, list) else v


def aggregate(lines) -> dict:
    by_day = defaultdict(lambda: {
        "total": 0,
        "ips": set(),
        "human_ips": set(),
        "paths": Counter(),
        "human_paths": Counter(),
        "categories": Counter(),
        "referrers": Counter(),
    })
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        ts = d.get("ts")
        if ts is None:
            continue
        day = datetime.fromtimestamp(ts, tz=JST).strftime("%Y-%m-%d")
        req = d.get("request", {}) or {}
        ip = req.get("remote_ip", "") or ""
        uri = (req.get("uri", "") or "").split("?")[0]
        headers = req.get("headers", {}) or {}
        ua = _first(headers, "User-Agent")
        ref = _first(headers, "Referer")

        b = by_day[day]
        b["total"] += 1
        if ip:
            b["ips"].add(ip)
        b["paths"][uri] += 1
        cat = classify_ua(ua)
        b["categories"][cat] += 1
        if cat == "human":
            b["human_paths"][uri] += 1
            if ip:
                b["human_ips"].add(ip)
        if ref:
            try:
                netloc = urlparse(ref).netloc or ref
            except ValueError:
                netloc = ref
            b["referrers"][netloc] += 1
    return by_day


def to_records(by_day: dict) -> list[dict]:
    records = []
    for day in sorted(by_day):
        b = by_day[day]
        records.append({
            "date": day,
            "total_requests": b["total"],
            "unique_ips": len(b["ips"]),
            "unique_human_ips": len(b["human_ips"]),
            "categories": dict(b["categories"]),
            "top_paths": b["paths"].most_common(10),
            "top_human_paths": b["human_paths"].most_common(10),
            "top_referrers": b["referrers"].most_common(5),
        })
    return records


def render_text(records: list[dict]) -> str:
    out = []
    for r in records:
        out.append(f"=== {r['date']} ===")
        out.append(f"  総リクエスト数: {r['total_requests']}")
        out.append(
            f"  ユニークIP数: {r['unique_ips']}"
            f"(うち人間らしきIP: {r['unique_human_ips']})")
        out.append(f"  内訳: {r['categories']}")
        if r["top_human_paths"]:
            out.append("  よく見られたページ(人間らしきアクセスのみ):")
            for path, cnt in r["top_human_paths"]:
                out.append(f"    {cnt:5d}  {path}")
        if r["top_referrers"]:
            out.append("  参照元(Referer):")
            for ref, cnt in r["top_referrers"]:
                out.append(f"    {cnt:5d}  {ref}")
        out.append("")
    return "\n".join(out)


def append_json(records: list[dict], path: str) -> int:
    """日付をキーに既存分とマージして書き戻す(同日は今回の集計で上書き、
    今回のログ範囲に含まれない過去日はそのまま残す)。当日分を含む
    ログを日次cronで繰り返し実行しても、当日の件数が正しく更新される。"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    merged: dict[str, dict] = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    merged[rec["date"]] = rec
                except (ValueError, KeyError):
                    pass
    updated = 0
    for r in records:
        if r["date"] not in merged or merged[r["date"]] != r:
            updated += 1
        merged[r["date"]] = r
    with open(path, "w", encoding="utf-8") as f:
        for date in sorted(merged):
            f.write(json.dumps(merged[date], ensure_ascii=False) + "\n")
    return updated


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "logfile", nargs="?",
        help="Caddy JSON Lines ログのパス(省略時はstdin)",
    )
    ap.add_argument(
        "--json-out",
        help="日次集計をJSON Linesで追記するファイルパス",
    )
    args = ap.parse_args()

    if args.logfile:
        with open(args.logfile, encoding="utf-8") as f:
            by_day = aggregate(f)
    else:
        by_day = aggregate(sys.stdin)

    records = to_records(by_day)
    print(render_text(records))

    if args.json_out:
        n = append_json(records, args.json_out)
        print(f"({args.json_out} に{n}日分を追記しました。既存日は上書きしていません)")


if __name__ == "__main__":
    main()
