# ruff: noqa: E501
"""詳細画面の「例文」と「訳」のズレを直す（DBのみ変更・アプリ再起動不要）。

■ 何が起きていたか（2026-08-22 ユーザー指摘 → 調査で確定）
  詳細ポップアップは
    例文 = words.example
    訳   = detail(JSON).example_ja
  を別々に表示している。ところが `scripts/backfill_example_ja.py` は
  **英単語名だけで突き合わせて** example_ja をマージする作りだったため、
  後から words.example が別の文に差し替わっても example_ja が古いまま残り、
  「例文と訳が別の文」という状態になっていた。
  例) GPIO
      例文: We toggled a spare GPIO pin to trigger the oscilloscope.
      訳  : このボードのGPIOピンを使ってLEDを制御した。   ← 別の文の訳

  本番実測(12,085語): example_ja が detail.examples[] 内の**同じ英文の訳**と
  食い違うものが 2,463 件。うち約 2,400 件は「まったく別の文の訳」だった。

■ 直し方の考え方（安全側に倒す）
  detail.examples[] の各要素は {en, ja} が同じAI生成呼び出しで対になって
  作られているので、`examples[i].en == words.example` である要素の `ja` は
  **その例文の訳として信頼できる**。これを正とする。

  ただし「単に言い回しが違うだけ」のものまで置換すると改悪になる
  （実測例: overdue「期限を過ぎています」→「提出期限を過ぎている」、
  coalition は examples 側に تشکیل というペルシャ語混入があった）。
  そこで **文字bi-gramのJaccard類似度**で切り分ける:

    類似度 < 0.55            → 別の文の訳とみなして examples 側で置換
    examples側が現行訳に内包 → 連結事故（訳が2文以上）とみなして置換
    それ以外                 → 現行訳を温存（触らない）

  さらに、置換候補に日本語が1文字も無い/別言語の文字が混ざる場合は
  **置換しない**（壊れたデータで上書きしないため）。

■ 再発防止
  置換の有無にかかわらず、`detail.example_ja_src` に「その訳が対応する英文」
  を記録する。以後 words.example が差し替わったら src と一致しなくなるので、
  アプリ側（app/routers/vocabulary.py）で**古い訳を表示しない**判定ができる。

使い方（VPSのコンテナ内・DBだけ書き換えるので再起動不要）:
    docker cp scripts/fix_example_ja.py eigo-app:/app/scripts/
    docker exec -i eigo-app python scripts/fix_example_ja.py            # 確認のみ
    docker exec -i eigo-app python scripts/fix_example_ja.py --apply    # 実行
    docker exec -i eigo-app python scripts/fix_example_ja.py --report /data/fix_report.json

オプション:
    --apply           実際にDBを更新する（既定はドライラン）
    --threshold 0.55  置換する類似度の上限
    --report PATH     置換内容を JSON で書き出す（レビュー用）
    --stamp-only      置換はせず example_ja_src の記録だけ行う
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# 日本語の教材に出るはずのない文字体系（壊れた候補で上書きしないための番人）。
_FOREIGN = re.compile(
    "[Ѐ-ӿ֐-׿؀-ۿ܀-ݏ"
    "ऀ-ॿ฀-๿က-႟가-힯]"
)
_JA = re.compile(r"[぀-ゟ゠-ヿ一-鿿]")


def _txt(v) -> str:
    if isinstance(v, list):
        return " ".join(_txt(x) for x in v if x)
    if isinstance(v, dict):
        return _txt(v.get("ja") or v.get("en") or "")
    return str(v or "")


def _norm_en(s) -> str:
    s = _txt(s).strip().lower()
    return re.sub(r"[\s　]+", " ", s).rstrip(".!?").strip()


def _squeeze(s: str) -> str:
    """句読点・空白を落として比較しやすくする。"""
    return re.sub(r"[\s　、。・「」『』（）()\.,!?;:／/]+", "", s or "")


def _bigrams(s: str) -> set[str]:
    t = _squeeze(s)
    return {t[i:i + 2] for i in range(len(t) - 1)} or ({t} if t else set())


def similarity(a: str, b: str) -> float:
    A, B = _bigrams(a), _bigrams(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def usable(cand: str) -> bool:
    """置換候補として使ってよい訳か（日本語があり、別言語混入が無い）。"""
    c = (cand or "").strip()
    return bool(c) and bool(_JA.search(c)) and not _FOREIGN.search(c)


def decide(example: str, example_ja: str, alt: str, threshold: float
           ) -> tuple[bool, str]:
    """(置換するか, 理由)。alt は同じ英文に対する detail.examples 側の訳。"""
    if not alt or not usable(alt):
        return False, "候補が使えない(空/別言語混入/日本語なし)"
    cur = (example_ja or "").strip()
    if not cur:
        return True, "訳が空"
    if _norm_en(cur) == _norm_en(alt):
        return False, "同一"
    # 現行訳に候補がまるごと含まれる = 別の文の訳が連結されている事故。
    if _squeeze(alt) and _squeeze(alt) in _squeeze(cur) and \
            len(_squeeze(cur)) > len(_squeeze(alt)):
        return True, "連結(訳が2文以上)"
    # 現行訳が日本語でない（英文がそのまま入っている）。
    if not _JA.search(cur):
        return True, "訳が日本語でない"
    s = similarity(cur, alt)
    if s < threshold:
        return True, f"別の文の訳(類似度{s:.2f})"
    return False, f"言い回しの違いのみ(類似度{s:.2f})→温存"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--threshold", type=float, default=0.55)
    ap.add_argument("--report", default="")
    ap.add_argument("--stamp-only", action="store_true")
    args = ap.parse_args()

    changed = stamped = kept = no_alt = 0
    report: list[dict] = []
    reasons: dict[str, int] = {}

    with db() as conn:
        rows = conn.execute(
            "SELECT id, english, japanese, domain, example, detail FROM words"
        ).fetchall()
        for r in rows:
            ex = (r["example"] or "").strip()
            if not ex:
                continue
            try:
                d = json.loads(r["detail"] or "{}")
            except Exception:
                continue
            if not isinstance(d, dict):
                continue
            cur = _txt(d.get("example_ja")).strip()
            alt = ""
            for e in (d.get("examples") or []):
                if isinstance(e, dict) and _norm_en(e.get("en")) == _norm_en(ex):
                    alt = _txt(e.get("ja")).strip()
                    break
            dirty = False
            if not args.stamp_only:
                if not alt:
                    no_alt += 1
                    do, why = False, "照合できる訳が無い(手作業での確認が必要)"
                else:
                    do, why = decide(ex, cur, alt, args.threshold)
                reasons[why.split("(")[0]] = \
                    reasons.get(why.split("(")[0], 0) + 1
                if do:
                    report.append({
                        "id": r["id"], "english": r["english"],
                        "domain": r["domain"], "example": ex,
                        "before": cur, "after": alt, "reason": why,
                    })
                    d["example_ja"] = alt
                    cur = alt
                    changed += 1
                    dirty = True
                else:
                    kept += 1
            # 由来の記録（置換の有無によらず全件）。
            if cur and d.get("example_ja_src") != ex:
                d["example_ja_src"] = ex
                stamped += 1
                dirty = True
            if dirty and args.apply:
                conn.execute(
                    "UPDATE words SET detail = ? WHERE id = ?",
                    (json.dumps(d, ensure_ascii=False), r["id"]),
                )
        if args.apply:
            conn.commit()

    print(f"{'実行' if args.apply else 'ドライラン'}: "
          f"置換 {changed} / 温存 {kept} / 照合先なし {no_alt} / "
          f"由来を記録 {stamped}")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"    {k:<24} {v}")
    if args.report:
        Path(args.report).write_text(
            json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"→ 置換内容: {args.report}")
    if not args.apply:
        print("※ 実際に更新するには --apply を付けてください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
