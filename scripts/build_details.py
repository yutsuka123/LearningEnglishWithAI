"""Incrementally pre-generate & cache word "詳細" (品詞/意味/派生/類義/対義/
語源/豆知識/解説) into words.detail.

単語の「詳細」をボタン押下時に逐次生成するのではなく、あらかじめ全語ぶん作って
おくためのバッチ。`words.detail` にキャッシュ済みの語は飛ばして「次の未生成分」
だけを作る（=何度でも安全に再実行でき、毎回続きから進む）。アプリの「詳細」
ボタンの遅延生成とも共存する。

プロンプト/品質は app/routers/vocabulary.py の `word_detail` と同一（昨日改善した
レベル: 類義/対義のニュアンス注記・語源グロス・max_tokens 1500=途中で切らない）。
モデルは品質モデル(OPENAI_QUALITY_MODEL→既定 gpt-5.4-mini)を使用。

ガード: 1日コスト上限(AI_DAILY_COST_CAP_USD)は常に有効。上限に達したらそこで
止まり、次回に続きを生成する（保存済みスキップ）。分間レート制限は明示バッチ
なので外して連続生成する(rate_limit=False)。

使い方:
  python scripts/build_details.py                 # 全件（未生成分のみ）
  python scripts/build_details.py --limit 200     # 今回は200語まで
  python scripts/build_details.py --force         # 既存も作り直し
  python scripts/build_details.py --order id      # id順（既定は level順）
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_settings  # noqa: E402
from app.database import db  # noqa: E402
from app.services import ai  # noqa: E402

# vocabulary.py の word_detail と同一のシステムプロンプト（昨日改善版）。
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="今回作る最大語数（0=未生成を全件）")
    ap.add_argument("--force", action="store_true",
                    help="キャッシュ済みも作り直す")
    ap.add_argument("--order", choices=["level", "id"], default="level",
                    help="生成順（既定 level→id）")
    args = ap.parse_args()

    if not ai.is_enabled():
        print("OPENAI_API_KEY が未設定のため詳細生成できません。")
        return 1

    model = load_settings().quality_model
    order = ("level ASC, id ASC" if args.order == "level" else "id ASC")
    where = "" if args.force else (
        "WHERE COALESCE(TRIM(detail), '') = ''")
    sql = (f"SELECT id, english, japanese, example FROM words "
           f"{where} ORDER BY {order}")

    made = failed = 0
    stopped = None
    with db() as conn:
        start_cost = float(conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM ai_usage").fetchone()[0])
        rows = conn.execute(sql).fetchall()
        total = len(rows)
        print(f"対象 {total} 語 / モデル {model} / order={args.order}")
        for r in rows:
            if args.limit and made >= args.limit:
                break
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
                if res.error and ("未設定" in res.error
                                  or "初期化" in res.error):
                    stopped = "aierr"
                    break
                failed += 1  # 一時的エラー等はこの語を飛ばす
                continue
            data = _json_object(res.text)
            if not data:
                failed += 1
                continue
            conn.execute(
                "UPDATE words SET detail = ? WHERE id = ?",
                (json.dumps(data, ensure_ascii=False), r["id"]),
            )
            # 1語ごとにコミットして書込みロックを解放する。握ったままだと次語の
            # ai.chat 内 ai_usage 記録(別接続)が database is locked になる。
            conn.commit()
            made += 1
            if made % 20 == 0:
                tgt = args.limit or total
                print(f"  詳細 {made}/{tgt} … (失敗 {failed})")
        conn.commit()
        end_cost = float(conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM ai_usage").fetchone()[0])

    print("---")
    print(f"作成: +{made} 語 / 失敗(スキップ): {failed}")
    print(f"今回の概算費用: ${end_cost - start_cost:.4f}")
    if stopped == "cap":
        print("※1日のコスト上限に達したため中断しました。次回に続きを生成します。")
    elif stopped == "aierr":
        print("※AIを利用できず中断しました（キー設定等を確認）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
