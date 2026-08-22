# ruff: noqa: E501
"""訳文の機械的な点検（単語の例文訳・単語の意味・フレーズ訳・詳細JSON）。

背景（2026-08-22ユーザー指摘）:
  詳細画面で「例文」と「訳」が食い違う語がある（例: GPIO の例文は
  "We toggled a spare GPIO pin to trigger the oscilloscope." なのに訳が
  「このボードのGPIOピンを使ってLEDを制御した。」）。原因は
  `scripts/backfill_example_ja.py` が **英単語名だけで突き合わせて**
  訳をマージする作りで、後から `words.example` が差し替わっても
  `detail.example_ja` が古いままになるため。

このスクリプトは **DBを一切変更しない**（読み取り専用）。
「怪しい」ものを機械的に絞り込んで JSON に書き出すだけ。実際に直すかは
人（Claude/ユーザー）が中身を見て判断する — 一括置換は改悪を生むため
（実測: `detail.examples[]` 側の訳に置換すると、既存の方が自然な訳まで
壊れるケースが多数あった）。

検出する異常:
  garbled       … 日本語として想定しない文字（アラビア/ペルシャ/キリル/
                  タイ文字など）が混入。過去のAI生成で実際に発生している。
  token_extra   … 訳にだけ出てくる略語/数字（例: 英文にないのに訳に「LED」）。
                  GPIO の事例はこれで捕まる。**最も当たりやすい指標**。
  token_missing … 英文にある略語/数字が訳に無い。
  extra_sentence… 英文は1文なのに訳が2文以上（別の例文の訳が連結された跡）。
  len_ratio     … 訳が英文に対して極端に長い/短い。
  same_as_word  … 例文訳が単語の意味そのまま（訳になっていない）。
  empty         … 訳が空。

出力: data/translation_audit.json
  {"words_example": [...], "words_meaning": [...], "phrases": [...],
   "detail_garbled": [...]}

使い方（VPSのコンテナ内）:
    docker cp scripts/audit_translations.py eigo-app:/app/scripts/
    docker exec -i eigo-app python scripts/audit_translations.py
    docker cp eigo-app:/app/data/translation_audit.json ./
オプション:
    --limit-per-flag 0   フラグごとの出力上限（0=無制限）
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import paths  # noqa: E402
from app.database import db  # noqa: E402

OUT = paths.data_dir / "translation_audit.json"

# 「文字化け／別言語混入」の検出。許可文字を列挙する方式にすると発音記号
# (IPA)や数学記号まで拾って誤検出だらけになったため、**日本語の教材に出る
# はずのない文字体系だけ**を名指しで拾う。過去にペルシャ語(تشکیل)の混入実績あり。
_FOREIGN = re.compile(
    "[Ѐ-ӿ"   # キリル
    "֐-׿"    # ヘブライ
    "؀-ۿ"    # アラビア/ペルシャ
    "܀-ݏ"    # シリア
    "ऀ-ॿ"    # デーヴァナーガリー
    "฀-๿"    # タイ
    "က-႟"    # ビルマ
    "가-힯"    # ハングル
    "䷀-䷿]"   # 六十四卦(誤生成の兆候)
)

# 略語(2文字以上の全大文字)・数字。訳文にはそのまま出るのが普通なので、
# 英文と訳文で集合がズレていたら別の文の訳が付いている可能性が高い。
_ACRONYM = re.compile(r"\b[A-Z][A-Z0-9]{1,}\b")
_NUMBER = re.compile(r"\d+")

# 訳文中の略語を拾う（全角英字も半角化して見る）。
def _tokens(text: str) -> set[str]:
    t = _to_hankaku(text)
    out = set(_ACRONYM.findall(t))
    out |= {n for n in _NUMBER.findall(t) if len(n) >= 1}
    return out


def _to_hankaku(s: str) -> str:
    return "".join(
        chr(ord(ch) - 0xFEE0) if "！" <= ch <= "～" else ch for ch in (s or "")
    )


def _txt(v) -> str:
    """detail の値は文字列のはずだが、過去データに list/dict が混ざる。"""
    if isinstance(v, list):
        return " ".join(_txt(x) for x in v if x)
    if isinstance(v, dict):
        return _txt(v.get("ja") or v.get("en") or "")
    return str(v or "")


def _garbled_chars(text: str) -> str:
    bad = set(_FOREIGN.findall(text or ""))
    return "".join(sorted(bad))


def _en_sentences(en: str) -> int:
    return max(1, len([s for s in re.split(r"[.!?]+", en) if s.strip()]))


def _ja_sentences(ja: str) -> int:
    return max(1, len([s for s in re.split(r"[。！？]+", ja) if s.strip()]))


def check_pair(en: str, ja: str, *, word_ja: str = "") -> list[str]:
    """英文と訳文の組を見て、当てはまる異常フラグを返す。"""
    flags: list[str] = []
    en = (en or "").strip()
    ja = (ja or "").strip()
    if not ja:
        return ["empty"]
    g = _garbled_chars(ja)
    if g:
        flags.append(f"garbled:{g}")
    en_tok, ja_tok = _tokens(en), _tokens(ja)
    # 数字は「10時」→「at 10」のように表記が変わることがあるので、
    # 略語(英字を含むもの)だけを厳しく見る。
    en_ac = {t for t in en_tok if any(c.isalpha() for c in t)}
    ja_ac = {t for t in ja_tok if any(c.isalpha() for c in t)}
    if ja_ac - en_ac:
        flags.append("token_extra:" + ",".join(sorted(ja_ac - en_ac)))
    if en_ac - ja_ac:
        flags.append("token_missing:" + ",".join(sorted(en_ac - ja_ac)))
    if _ja_sentences(ja) > _en_sentences(en):
        flags.append("extra_sentence")
    if en:
        ratio = len(ja) / len(en)
        # 日本語は英語より文字数が少なくなるのが普通(概ね0.35〜0.9倍)。
        if ratio > 1.15:
            flags.append(f"len_ratio:{ratio:.2f}")
        elif ratio < 0.20:
            flags.append(f"len_ratio:{ratio:.2f}")
    if word_ja and ja.strip("。") == word_ja.strip("。"):
        flags.append("same_as_word")
    return flags


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-per-flag", type=int, default=0)
    args = ap.parse_args()

    result: dict[str, list[dict]] = {
        "words_example": [], "phrases": [], "detail_garbled": [],
    }
    counts: dict[str, int] = {}

    def bump(flag: str) -> None:
        key = flag.split(":")[0]
        counts[key] = counts.get(key, 0) + 1

    with db() as conn:
        rows = conn.execute(
            "SELECT id, english, japanese, domain, example, detail "
            "FROM words"
        ).fetchall()
        for r in rows:
            ex = (r["example"] or "").strip()
            try:
                d = json.loads(r["detail"] or "{}")
            except Exception:
                d = {}
            eja = _txt(d.get("example_ja")).strip()
            # 詳細JSON全体の文字化けチェック（解説・豆知識なども表示される）
            whole = json.dumps(d, ensure_ascii=False)
            g = _garbled_chars(whole)
            if g:
                result["detail_garbled"].append({
                    "id": r["id"], "english": r["english"],
                    "domain": r["domain"], "chars": g,
                })
            if not ex:
                continue
            flags = check_pair(ex, eja, word_ja=r["japanese"])
            if flags:
                for f in flags:
                    bump(f)
                # 参考: detail.examples 側に同じ英文の訳があるか
                alt = ""
                for e in (d.get("examples") or []):
                    if isinstance(e, dict) and \
                       _norm(e.get("en")) == _norm(ex):
                        alt = _txt(e.get("ja")).strip()
                        break
                result["words_example"].append({
                    "id": r["id"], "english": r["english"],
                    "japanese": r["japanese"], "domain": r["domain"],
                    "example": ex, "example_ja": eja,
                    "alt_from_examples": alt, "flags": flags,
                })

        prows = conn.execute(
            "SELECT id, english, japanese, scene FROM phrases"
        ).fetchall()
        for r in prows:
            flags = check_pair(r["english"] or "", r["japanese"] or "")
            # フレーズは意訳が普通なので、長さ比の警告は誤検出が多い。
            # 文字化け・略語ズレ・空だけを見る。
            flags = [f for f in flags
                     if not f.startswith(("len_ratio", "extra_sentence"))]
            if flags:
                for f in flags:
                    bump("phrase_" + f.split(":")[0])
                result["phrases"].append({
                    "id": r["id"], "english": r["english"],
                    "japanese": r["japanese"], "scene": r["scene"],
                    "flags": flags,
                })

    if args.limit_per_flag:
        for k in result:
            result[k] = result[k][:args.limit_per_flag]

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("=== 単語の例文訳（words.example vs detail.example_ja）===")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k:<16} {v}")
    print(f"\n要確認 単語例文: {len(result['words_example'])} 件 / "
          f"フレーズ: {len(result['phrases'])} 件 / "
          f"詳細JSONの文字化け: {len(result['detail_garbled'])} 件")
    print(f"→ {OUT}")
    return 0


def _norm(s) -> str:
    s = _txt(s).strip().lower()
    s = re.sub(r"[\s　]+", " ", s)
    return s.rstrip(".!?").strip()


if __name__ == "__main__":
    sys.exit(main())
