# ruff: noqa: E501
"""クロスワードAIヒント生成/照査のモデル比較ベンチマーク(2026-09-07・
ユーザー指示「品質を保ち高速化できそうな3モデルで評価、現モデルも
あわせて4モデル、照査モデルも高速化」)。

設計(ユーザー承認済みの縮小版):
  A. 全206分野 × 1語数(8語) × 生成4モデル
     -> 品質の分野網羅性チェック(全分野で崩れないか)。
  B. 代表2分野(物理・料理) × 4語数(3/20/40/50) × 生成4モデル
     -> 語数によるレイテンシのスケーリング。
  C. Bと同条件 × 照査3モデル(現行quality_model+候補2つ)
     -> 照査(レビュー)側の高速化余地。
  D. 生成された全ヒントを、固定の"判定者"モデル(quality_model)で
     app/routers/games.pyの_REVIEW_JA_SYSTEMと同じ基準により自動採点
     (ok/ng)し、品質の代理指標とする。人手レビューの代わりの近似値である
     点に注意(本文まとめ時に明記すること)。

本番のapp/routers/games.py _ensure_ai_hints/_review_ai_hintsと同じ
CHUNKサイズ・システムプロンプト・温度・max_tokensを流用し、
ai.chat(..., rate_limit=False)で明示的に許可された一括バッチとして呼ぶ
(app/services/ai.pyのchat()docstring参照)。

出力: docs/BENCHMARK_CROSSWORD_MODELS_RESULT.jsonl (生データ・随時追記)
      呼び出し側で集計してMarkdownにまとめる(別途)。

実行: python scripts/benchmark_crossword_hint_models.py [--smoke]
  --smoke: 動作確認用の極小規模(3分野×1語数×1モデル)だけ実行して終了。
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services import ai  # noqa: E402
from app.routers.games import (  # noqa: E402
    _JA_HINT_SYSTEM, _REVIEW_JA_SYSTEM, _json_array,
)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "vocabulary.db"
OUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "docs" / "BENCHMARK_CROSSWORD_MODELS_RESULT.jsonl"
)

# 2026-09-07・ユーザー指示でClaudeも候補に追加。短い定型JSON生成という
# タスク特性上、大型(Opus/Sonnet)は不要と判断しHaiku 4.5のみ採用
# (OpenAI側のmini系と役割が対応する速度・価格重視ティア)。
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
# 参考: Anthropic公式サイト2026-09時点の掲載価格($/1Mトークン)。
# ai.pyのPRICING辞書と同じ(input, output)の形。
CLAUDE_PRICING = {CLAUDE_MODEL: (1.00, 5.00)}

GEN_MODELS = ["gpt-5.6-luna", "gpt-4o-mini", "gpt-4.1-mini", "gpt-5.4-mini",
              CLAUDE_MODEL]
REVIEW_MODELS = ["gpt-5.4-mini", "gpt-4o-mini", "gpt-4.1-mini", CLAUDE_MODEL]
JUDGE_MODEL = "gpt-5.4-mini"  # 品質の代理指標を出す固定の判定者(OpenAI側で統一)


class _ClaudeResult:
    """app.services.ai.AIResultと同じインターフェース
    (ok/text/error/cost_usd/prompt_tokens/output_tokens)を持つ、
    Claude呼び出し用の軽量ラッパー。"""

    def __init__(self, ok, text="", error=None, cost_usd=0.0,
                 prompt_tokens=0, output_tokens=0):
        self.ok = ok
        self.text = text
        self.error = error
        self.cost_usd = cost_usd
        self.prompt_tokens = prompt_tokens
        self.output_tokens = output_tokens


_claude_client = None


def _get_claude_client():
    global _claude_client
    if _claude_client is None:
        import anthropic
        _claude_client = anthropic.Anthropic()  # ANTHROPIC_API_KEY を自動使用
    return _claude_client


def _claude_chat(system: str, user: str, *, temperature: float,
                  max_tokens: int, model: str) -> _ClaudeResult:
    # 2026-09-07発覚: インストール済みanthropic SDK(1.4.0)の
    # messages.create()にtemperatureパラメータが存在しない
    # (Message | Stream形状のシグネチャに含まれない)。この比較テストでは
    # 速度・品質の比較が主目的であり、既定温度のままでも横並び比較として
    # 成立するため、temperature引数は送らずAPI既定値に任せる。
    try:
        client = _get_claude_client()
        resp = client.messages.create(
            model=model, max_tokens=max_tokens,
            system=system, messages=[{"role": "user", "content": user}],
        )
        text = "".join(
            block.text for block in resp.content if block.type == "text")
        in_tok = resp.usage.input_tokens
        out_tok = resp.usage.output_tokens
        price_in, price_out = CLAUDE_PRICING.get(model, (0.0, 0.0))
        cost = in_tok / 1_000_000 * price_in + out_tok / 1_000_000 * price_out
        return _ClaudeResult(
            ok=True, text=text, cost_usd=cost,
            prompt_tokens=in_tok, output_tokens=out_tok)
    except Exception as exc:  # noqa: BLE001 - ベンチマークなので広く捕捉
        return _ClaudeResult(ok=False, error=str(exc))


def _is_claude(model: str) -> bool:
    return model.startswith("claude-")

GEN_CHUNK = 8     # app/routers/games.py _ensure_ai_hints と同じ
REVIEW_CHUNK = 10  # app/routers/games.py _review_ai_hints と同じ
SCALE_DOMAINS = ["物理", "料理"]
SCALE_COUNTS = [3, 20, 40, 50]
BREADTH_COUNT = 8

_out_lock = None


def _append_result(rec: dict) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _fetch_words(conn: sqlite3.Connection, domain: str, n: int) -> list[dict]:
    rows = conn.execute(
        "SELECT id, english, japanese FROM words WHERE domain = ? "
        "ORDER BY RANDOM() LIMIT ?", (domain, n),
    ).fetchall()
    return [{"id": r["id"], "english": r["english"], "japanese": r["japanese"]}
            for r in rows]


def _all_domains(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT domain, COUNT(*) c FROM words GROUP BY domain "
        "HAVING c >= 3 ORDER BY domain").fetchall()
    return [r["domain"] for r in rows]


def _gen_batch(words: list[dict], model: str) -> dict:
    """_ensure_ai_hintsの1バッチぶんを模した単発呼び出し。
    modelが"claude-"始まりならAnthropic経由、それ以外はOpenAI経由
    (app.services.ai.chat)で呼ぶ。"""
    listing = "\n".join(f"{w['english']} | {w['japanese']}" for w in words)
    t0 = time.monotonic()
    if _is_claude(model):
        r = _claude_chat(
            _JA_HINT_SYSTEM, f"単語(英語 | 日本語訳):\n{listing}",
            temperature=0.4, max_tokens=1200, model=model)
    else:
        r = ai.chat(
            _JA_HINT_SYSTEM, f"単語(英語 | 日本語訳):\n{listing}",
            temperature=0.4, max_tokens=1200,
            feature="benchmark_crossword_gen", model=model, rate_limit=False,
        )
    elapsed = time.monotonic() - t0
    hints: dict[str, str] = {}
    if r.ok:
        for item in _json_array(r.text):
            en = str(item.get("english", "")).strip().upper()
            hint = str(item.get("hint", "")).strip()
            if en and hint:
                hints[en] = hint
    return {
        "elapsed": elapsed, "ok": r.ok, "error": r.error,
        "cost_usd": r.cost_usd, "prompt_tokens": r.prompt_tokens,
        "output_tokens": r.output_tokens, "hints": hints,
        "n_words": len(words), "n_hints_returned": len(hints),
    }


def _review_batch(
    items: list[tuple[dict, str]], model: str,
) -> dict:
    """_review_ai_hintsの1バッチぶんを模した単発呼び出し。
    items: [(word_dict, hint_text), ...]"""
    listing = "\n".join(
        f"{w['english']} | 訳:{w['japanese']} | ヒント:{hint}"
        for w, hint in items)
    t0 = time.monotonic()
    if _is_claude(model):
        r = _claude_chat(
            _REVIEW_JA_SYSTEM, f"チェック対象:\n{listing}",
            temperature=0.0, max_tokens=600, model=model)
    else:
        r = ai.chat(
            _REVIEW_JA_SYSTEM, f"チェック対象:\n{listing}",
            temperature=0.0, max_tokens=600,
            feature="benchmark_crossword_review", model=model,
            rate_limit=False,
        )
    elapsed = time.monotonic() - t0
    flagged = set()
    if r.ok:
        for item in _json_array(r.text):
            if str(item.get("verdict", "")).strip().lower() == "ng":
                en = str(item.get("english", "")).strip().upper()
                if en:
                    flagged.add(en)
    return {
        "elapsed": elapsed, "ok": r.ok, "error": r.error,
        "cost_usd": r.cost_usd, "n_items": len(items),
        "n_flagged": len(flagged), "flagged": sorted(flagged),
    }


def _chunks(lst: list, n: int) -> list[list]:
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def run_breadth(conn: sqlite3.Connection, domains: list[str]) -> None:
    """A: 全分野 x 1語数(8語) x 生成4モデル。"""
    print(f"[breadth] {len(domains)} domains x {len(GEN_MODELS)} models "
          f"= {len(domains) * len(GEN_MODELS)} calls")
    jobs = []
    for domain in domains:
        words = _fetch_words(conn, domain, BREADTH_COUNT)
        if len(words) < 3:
            continue
        for model in GEN_MODELS:
            jobs.append((domain, words, model))

    def _run(job):
        domain, words, model = job
        res = _gen_batch(words, model)
        hints_map = res.pop("hints")
        rec = {
            "phase": "breadth", "domain": domain, "model": model,
            "word_count": len(words), **res,
            "words": [w["english"] for w in words],
            "hints_map": hints_map,
        }
        _append_result(rec)
        return rec

    done = 0
    with ThreadPoolExecutor(max_workers=16) as ex:
        futures = [ex.submit(_run, j) for j in jobs]
        for f in as_completed(futures):
            f.result()
            done += 1
            if done % 50 == 0:
                print(f"[breadth] {done}/{len(jobs)} done")
    print(f"[breadth] complete: {done} calls")


def run_scaling(conn: sqlite3.Connection) -> dict:
    """B+C: 代表2分野 x 4語数 x 生成4モデル(+各条件で照査3モデル)。
    戻り値: {(domain, count, model): {"hints": {...}}} 生成結果
    (照査フェーズで参照するため)。"""
    gen_results: dict = {}
    total_gen_calls = 0
    for domain in SCALE_DOMAINS:
        max_n = max(SCALE_COUNTS)
        pool = _fetch_words(conn, domain, max_n)
        if len(pool) < max_n:
            print(f"[scaling] warning: domain={domain} has only "
                  f"{len(pool)} words (<{max_n})")
        for count in SCALE_COUNTS:
            words = pool[:count]
            if len(words) < 3:
                continue
            for model in GEN_MODELS:
                total_gen_calls += len(_chunks(words, GEN_CHUNK))
    print(f"[scaling-gen] domains={SCALE_DOMAINS} counts={SCALE_COUNTS} "
          f"models={GEN_MODELS} -> ~{total_gen_calls} batch calls")

    def _run_one(domain, words, model):
        batches = _chunks(words, GEN_CHUNK)
        t0 = time.monotonic()
        with ThreadPoolExecutor(max_workers=min(8, len(batches))) as ex:
            results = list(ex.map(lambda b: _gen_batch(b, model), batches))
        wall = time.monotonic() - t0
        merged_hints: dict[str, str] = {}
        for r in results:
            merged_hints.update(r["hints"])
        total_cost = sum(r["cost_usd"] for r in results)
        n_errors = sum(1 for r in results if not r["ok"])
        rec = {
            "phase": "scaling_gen", "domain": domain, "model": model,
            "word_count": len(words), "n_batches": len(batches),
            "wall_elapsed": wall, "cost_usd": total_cost,
            "n_batch_errors": n_errors,
            "n_hints_returned": len(merged_hints),
            "batch_elapsed": [r["elapsed"] for r in results],
            "batch_errors": [r["error"] for r in results if not r["ok"]],
        }
        _append_result({**rec, "words": [w["english"] for w in words]})
        gen_results[(domain, len(words), model)] = {
            "words": words, "hints": merged_hints,
        }
        return rec

    for domain in SCALE_DOMAINS:
        pool = _fetch_words(conn, domain, max(SCALE_COUNTS))
        for count in SCALE_COUNTS:
            words = pool[:count]
            if len(words) < 3:
                continue
            for model in GEN_MODELS:
                rec = _run_one(domain, words, model)
                print(f"[scaling-gen] domain={domain} n={count} "
                      f"model={model} wall={rec['wall_elapsed']:.1f}s "
                      f"cost=${rec['cost_usd']:.5f} "
                      f"errors={rec['n_batch_errors']}")
    return gen_results


def run_review_scaling(gen_results: dict) -> None:
    """C: Bの生成結果(現行モデルgpt-5.6-lunaの出力)を、照査3モデルで
    レビューし速度を比較。"""
    base_model = "gpt-5.6-luna"
    for domain in SCALE_DOMAINS:
        for count in SCALE_COUNTS:
            key = (domain, count, base_model)
            if key not in gen_results:
                continue
            words = gen_results[key]["words"]
            hints = gen_results[key]["hints"]
            items = [(w, hints[w["english"].upper()]) for w in words
                     if w["english"].upper() in hints]
            if not items:
                continue
            batches = _chunks(items, REVIEW_CHUNK)
            for model in REVIEW_MODELS:
                t0 = time.monotonic()
                with ThreadPoolExecutor(
                        max_workers=min(8, len(batches))) as ex:
                    results = list(ex.map(
                        lambda b: _review_batch(b, model), batches))
                wall = time.monotonic() - t0
                total_cost = sum(r["cost_usd"] for r in results)
                n_errors = sum(1 for r in results if not r["ok"])
                n_flagged = sum(r["n_flagged"] for r in results)
                rec = {
                    "phase": "review_scaling", "domain": domain,
                    "gen_model": base_model, "review_model": model,
                    "word_count": len(items), "n_batches": len(batches),
                    "wall_elapsed": wall, "cost_usd": total_cost,
                    "n_batch_errors": n_errors, "n_flagged": n_flagged,
                }
                _append_result(rec)
                print(f"[review-scaling] domain={domain} n={len(items)} "
                      f"review_model={model} wall={wall:.1f}s "
                      f"flagged={n_flagged}/{len(items)} "
                      f"errors={n_errors}")


def run_quality_judge(conn: sqlite3.Connection, domains: list[str]) -> None:
    """D: breadthフェーズで生成された各(domain, model)のヒントを、固定の
    判定者モデル(JUDGE_MODEL)でok/ng判定し、品質の代理指標にする。
    breadthのJSONLを読み直して対象を作る(再生成せず既存の記録を使う)。"""
    if not OUT_PATH.exists():
        print("[judge] no breadth results found, skip")
        return
    breadth_recs = []
    with open(OUT_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("phase") == "breadth" and rec.get("ok"):
                breadth_recs.append(rec)
    print(f"[judge] {len(breadth_recs)} breadth generation records to judge")

    # sqlite3接続はメインスレッドでのみ使う(ThreadPoolExecutorのワーカー
    # スレッドから同じconnを触るとProgrammingErrorになるため、必要な
    # domain->{english:japanese}を先にメインスレッドで全部引いておく)。
    # hints_mapのキーは_gen_batchで.upper()されている一方、DBのenglish列は
    # 原文の大小文字のままなので、突き合わせは大文字キーで統一する
    # (2026-09-07発覚: この不一致で全件がjapanese=""になりjudgeが常に
    # スキップされていた)。
    id_by_domain: dict[str, dict[str, str]] = {}
    for domain in {r["domain"] for r in breadth_recs}:
        rows = conn.execute(
            "SELECT english, japanese FROM words WHERE domain = ?",
            (domain,)).fetchall()
        id_by_domain[domain] = {
            r["english"].upper(): r["japanese"] for r in rows}

    def _get_word_pairs(domain: str, english_list: list[str]) -> list[dict]:
        jp = id_by_domain.get(domain, {})
        return [{"english": e, "japanese": jp.get(e.upper(), "")}
                for e in english_list]

    def _run(rec):
        domain = rec["domain"]
        hints = rec.get("hints_map") or {}
        if not hints:
            return None
        pairs = _get_word_pairs(domain, list(hints.keys()))
        items = [(p, hints[p["english"]]) for p in pairs if p["japanese"]]
        if not items:
            return None
        result = _review_batch(items, JUDGE_MODEL)
        out = {
            "phase": "quality_judge", "domain": domain,
            "gen_model": rec["model"], "judge_model": JUDGE_MODEL,
            "n_items": len(items), "n_flagged": result["n_flagged"],
            "flagged": result["flagged"], "ok": result["ok"],
            "error": result["error"],
        }
        _append_result(out)
        return out

    done = 0
    with ThreadPoolExecutor(max_workers=16) as ex:
        futures = [ex.submit(_run, r) for r in breadth_recs]
        for f in as_completed(futures):
            f.result()
            done += 1
            if done % 50 == 0:
                print(f"[judge] {done}/{len(breadth_recs)} done")
    print(f"[judge] complete: {done}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--skip-breadth", action="store_true")
    ap.add_argument("--skip-scaling", action="store_true")
    ap.add_argument("--skip-judge", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.smoke:
        domains = _all_domains(conn)[:3]
        print(f"[smoke] domains={domains}")
        run_breadth(conn, domains)
        return

    domains = _all_domains(conn)
    if not args.skip_breadth:
        run_breadth(conn, domains)
    gen_results = {}
    if not args.skip_scaling:
        gen_results = run_scaling(conn)
        run_review_scaling(gen_results)
    if not args.skip_judge:
        run_quality_judge(conn, domains)
    print(f"done. results appended to {OUT_PATH}")


if __name__ == "__main__":
    main()
