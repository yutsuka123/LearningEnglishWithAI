# ruff: noqa: E501
"""2026-08-30に追加した歴史/文学サブドメイン語彙151語だけを対象に、詳細JSON
(品詞/意味/例文/派生/類義/対義/語源/豆知識/発音記号/解説)を生成する。

`scripts/build_details.py`（全語対象・未生成分から順に処理）をそのまま使うと
既存のバックログ(detail未生成の他分野語)まで一緒に消費してしまい、範囲を
このバッチだけに絞れない。そこで`scripts/add_history_literature_subdomains_
2026_08_30.py`が持つ151件の(english, domain)組をそのままインポートして、
その組に一致する語だけをidで正確に特定してから処理する(homograph
(senate/guild/enlightenment/epoch)はenglishだけでは一意にならないため、
domainも合わせて照合)。

SYSTEMプロンプトは`build_details.py`/`app/routers/vocabulary.py`の
`word_detail`と同一のものを使う(標準パイプラインに合わせる)。ただし
以下2点を追加で行う(2026-08-30・ユーザー指示への対応):

1. **IPA表記の統一**: 2026-08-27に本プロジェクトは精密表記(ɹ/ɚ)を廃し
   `ɹ→r`・`ɚ→ər`の標準表記に統一済み(docs/TODO.md参照)。AIが精密表記で
   返してくることがあるため、保存前に機械的に置換する。
2. **example_ja_src の明示設定**: `word_detail`エンドポイント(生成時)は
   `data["example_ja_src"] = row["example"]`をセットしてから保存している
   が、`build_details.py`(バッチ版)はこれを欠いている。`example_ja_src`は
   `app/database.py`の`trg_words_example_ja_invalidate`トリガーが
   「example列が変更されたのにexample_ja_srcが追随していない場合に
   example_ja/example_ja_srcを自動削除する」ための整合性チェックに使われる
   ため、初回生成時から正しくセットしておく(将来exampleを直接編集した際に
   このトリガーが正しく機能するようにするため)。

Run:  python scripts/build_details_history_lit_batch_2026_08_30.py [--force]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_settings  # noqa: E402
from app.database import db  # noqa: E402
from app.services import ai  # noqa: E402

# build_details.py / word_detail と同一のシステムプロンプト。
SYSTEM = (
    "英単語の詳細情報を日本語でJSONのみ作成。キー: "
    "pronunciation(発音記号・IPA。米音を基本にスラッシュで囲む 例: /əˈbændən/), "
    "pos(主な品詞), meanings(意味の配列・主要な語義を複数), "
    "examples(配列[{en,ja}]・自然な例文1〜2個), "
    "example_ja(上記『既存例文』の自然な日本語訳。既存例文が無ければ空文字), "
    "derivatives(派生語の配列[{word,pos,ja}]・元が形容詞なら動詞/副詞/名詞"
    "形など他の品詞の関連語も含める), "
    "synonyms(類義語の配列[{word,note}]。note は各類義語の意味やニュアンス・"
    "使い分けの違いを簡潔に), "
    "antonyms(対義語の配列[{word,note}]), "
    "origin(語源・由来。可能なら接頭辞/語根/接尾辞に分解し各要素の意味を示す"
    "(例: abnormal = ab-「離れて」+ normal「正常」)。語源に出てくる語があれば"
    "その意味も一言添える), "
    "trivia(豆知識。関連が本当にあれば、著名人・聖書・哲学・有名な技術・歴史上の"
    "名言や出来事・有名な書籍や映画のセリフとの結びつきを1つ挙げる。無理に作らず"
    "自然なものだけ), "
    "explanation(使い方・ニュアンスの解説). "
    "簡潔に。必ず完結したJSONのみを出力（途中で切らない）。"
)


def _json_object(text: str) -> dict | None:
    a, b = text.find("{"), text.rfind("}")
    if a == -1 or b == -1:
        return None
    try:
        d = json.loads(text[a:b + 1])
        return d if isinstance(d, dict) else None
    except (json.JSONDecodeError, ValueError):
        return None


def _normalize_ipa(text: str) -> str:
    """2026-08-27の統一方針に合わせ、精密表記を標準表記へ機械的に変換する。
    ɹ(ターンドアール)→r、ɚ(R色母音)→ər。"""
    if not text:
        return text
    return text.replace("ɹ", "r").replace("ɚ", "ər")


def _normalize_detail_ipa(data: dict) -> None:
    """detail JSON内でIPAが出現しうるキーを正規化する(in-place)。"""
    if isinstance(data.get("pronunciation"), str):
        data["pronunciation"] = _normalize_ipa(data["pronunciation"])


def _load_batch_targets() -> list[tuple[str, str]]:
    """add_history_literature_subdomains_2026_08_30.py の WORDS から
    (english, domain) の組だけを取り出す(151件)。"""
    import importlib.util

    add_script = Path(__file__).resolve().parent / \
        "add_history_literature_subdomains_2026_08_30.py"
    spec = importlib.util.spec_from_file_location("_add_batch", add_script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return [(w[0], w[4]) for w in mod.WORDS]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                     help="既にdetailがある語も作り直す")
    args = ap.parse_args()

    if not ai.is_enabled():
        print("OPENAI_API_KEY が未設定のため詳細生成できません。")
        return 1

    targets = _load_batch_targets()
    model = load_settings().quality_model

    made = failed = already = notfound = 0
    stopped = None
    with db() as conn:
        # english+domain で正確にid特定(homographはdomainで一意化)。
        rows_by_key: dict[tuple[str, str], dict] = {}
        for en, domain in targets:
            r = conn.execute(
                "SELECT id, english, japanese, example, detail FROM words "
                "WHERE LOWER(english) = LOWER(?) AND domain = ?",
                (en, domain),
            ).fetchone()
            if r is None:
                notfound += 1
                print(f"  !! not found in DB: {en!r} [{domain}]")
                continue
            rows_by_key[(en, domain)] = dict(r)

        print(f"対象 {len(targets)} 件中、DB照合成功 {len(rows_by_key)} 件 "
              f"(未検出 {notfound})")

        start_cost = float(conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM ai_usage").fetchone()[0])

        for i, ((en, domain), r) in enumerate(rows_by_key.items(), start=1):
            if r["detail"] and not args.force:
                already += 1
                continue
            user = (
                f"単語: {r['english']}\n既知の訳: {r['japanese']}\n"
                f"既存例文: {r['example'] or 'なし'}"
            )
            res = ai.chat(SYSTEM, user, temperature=0.3, max_tokens=1500,
                          feature="detail", model=model, rate_limit=False)
            if not res.ok:
                if res.error and "上限" in res.error:
                    stopped = "cap"
                    break
                if res.error and ("未設定" in res.error or "初期化" in res.error):
                    stopped = "aierr"
                    break
                failed += 1
                print(f"  !! generation failed: {en!r} [{domain}]: {res.error}")
                continue
            data = _json_object(res.text)
            if not data:
                failed += 1
                print(f"  !! bad JSON: {en!r} [{domain}]")
                continue
            _normalize_detail_ipa(data)
            # word_detail()エンドポイントと同じくexample_ja_srcを明示設定。
            if (r["example"] or "").strip() and str(
                    data.get("example_ja") or "").strip():
                data["example_ja_src"] = (r["example"] or "").strip()
            conn.execute(
                "UPDATE words SET detail = ? WHERE id = ?",
                (json.dumps(data, ensure_ascii=False), r["id"]),
            )
            conn.commit()
            made += 1
            if made % 20 == 0:
                print(f"  詳細 {made}/{len(rows_by_key)} … (失敗 {failed})")

        conn.commit()
        end_cost = float(conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM ai_usage").fetchone()[0])

    print("---")
    print(f"作成: +{made} 語 / 既存スキップ: {already} / 失敗: {failed} / "
          f"未検出: {notfound}")
    print(f"今回の概算費用: ${end_cost - start_cost:.4f}")
    if stopped == "cap":
        print("※1日のコスト上限に達したため中断しました。次回に続きを生成します。")
    elif stopped == "aierr":
        print("※AIを利用できず中断しました（キー設定等を確認）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
