#!/usr/bin/env python3
"""VPSホストのCPU/RAM/ディスク負荷を定期収集する（2026-08-20〜）。

サクラVPSはn8n(ailab)・ecopy等の他dockerプロジェクトと相乗りのため、
コンテナ内から見える値ではなく**ホスト全体**の値を見る必要がある。
analyze_access_log.py と同じ流儀で、ホストのpython3からcron実行し、
結果を data/server_stats.jsonl に追記する（アプリはこのファイルを
読むだけで、ここでは集計しない）。標準ライブラリのみに依存。

使い方(VPS上、eigo-appコンテナの外・ホストのpython3で実行を想定):
  cd /home/ubuntu/eigo && python3 scripts/collect_server_stats.py \
      --json-out data/server_stats.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone

# 5分間隔想定で30日分(8640件)を保持。それ以上古い行は収集のたびに
# 切り捨てる(ファイルが際限なく育たないようにするため)。
# 2026-08-30: 過去1ヶ月の最大負荷を見たいという要望に対応するため
# 7日分(2016件)から拡張(1行が小さいため30日分でも数MB程度)。
MAX_RECORDS = 8640


def _load_average() -> tuple[float, float, float]:
    load1, load5, load15 = os.getloadavg()
    return round(load1, 2), round(load5, 2), round(load15, 2)


def _mem_stats() -> dict:
    """/proc/meminfo から総量・使用量(MB)を算出(psutil不要)。"""
    info = {}
    with open("/proc/meminfo", encoding="utf-8") as f:
        for line in f:
            key, _, rest = line.partition(":")
            val = rest.strip().split()[0]
            info[key] = int(val)  # kB単位
    total_kb = info.get("MemTotal", 0)
    avail_kb = info.get("MemAvailable", info.get("MemFree", 0))
    used_kb = max(0, total_kb - avail_kb)
    pct = round(used_kb / total_kb * 100, 1) if total_kb else 0.0
    return {
        "mem_total_mb": round(total_kb / 1024, 1),
        "mem_used_mb": round(used_kb / 1024, 1),
        "mem_pct": pct,
    }


def _disk_stats(path: str = "/") -> dict:
    du = os.statvfs(path)
    total = du.f_frsize * du.f_blocks
    free = du.f_frsize * du.f_bavail
    used = total - free
    pct = round(used / total * 100, 1) if total else 0.0
    return {
        "disk_total_gb": round(total / 1024**3, 1),
        "disk_used_gb": round(used / 1024**3, 1),
        "disk_pct": pct,
    }


def _container_stats() -> dict:
    """`docker stats --no-stream` で全コンテナのCPU/MEM使用率を取る
    （相乗りの他プロジェクト全体の負荷を把握するのが目的のため、
    決め打ちフィルタはしない）。dockerが無い/権限が無い等で失敗した
    場合は空dictを返す(致命的ではないため、ホストのload/mem/disk収集
    自体は継続する)。"""
    try:
        out = subprocess.run(
            ["docker", "stats", "--no-stream", "--format",
             "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout
    except Exception:
        return {}
    result = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        name, cpu_perc, mem_usage = parts
        try:
            cpu_pct = float(cpu_perc.rstrip("%"))
        except ValueError:
            cpu_pct = None
        mem_mb = mem_usage.split("/")[0].strip()
        result[name] = {"cpu_pct": cpu_pct, "mem": mem_mb}
    return result


def collect() -> dict:
    load1, load5, load15 = _load_average()
    # 他テーブルのcreated_at(SQLiteのdatetime('now')・UTC naive)と同じ
    # 形式で保存する。フロントのfmtDateJST()がこの形式を前提にJSTへ
    # 変換するため、ここでJST付きISOを返すと二重変換でズレる。
    rec = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "load1": load1, "load5": load5, "load15": load15,
        "cpu_count": os.cpu_count() or 0,
    }
    rec.update(_mem_stats())
    rec.update(_disk_stats())
    containers = _container_stats()
    if containers:
        rec["containers"] = containers
    return rec


def append_jsonl(rec: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    lines = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            lines = [ln for ln in f if ln.strip()]
    lines.append(json.dumps(rec, ensure_ascii=False) + "\n")
    lines = lines[-MAX_RECORDS:]
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--json-out", required=True,
        help="スナップショットをJSON Linesで追記するファイルパス",
    )
    args = ap.parse_args()

    t0 = time.monotonic()
    rec = collect()
    rec["collect_ms"] = round((time.monotonic() - t0) * 1000)
    append_jsonl(rec, args.json_out)
    print(json.dumps(rec, ensure_ascii=False))


if __name__ == "__main__":
    main()
