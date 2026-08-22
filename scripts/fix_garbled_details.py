# ruff: noqa: E501, RUF001
"""詳細JSONに紛れ込んだ別言語の単語を日本語に直す（DBのみ変更・再起動不要）。

背景（2026-08-22）:
  訳文点検（`scripts/audit_translations.py`）で、詳細(detail)JSONの中に
  ペルシャ語・ヒンディー語・アラビア語・キリル文字が混ざった語が見つかった。
  AI生成時にごく低頻度で起きる「別言語のトークンが混入する」現象で、
  日本語の文の途中に外国語の単語が1つだけ入る形になっている。
    例) coalition: 「その政党たちは連立政権を تشکیلした。」（تشکیل=形成）
        marsh    : 「背の高い葦が沼地一面に густく生えている。」（густо=密に）

  一方で、**語源(origin)欄が正しくアラビア語/ヘブライ語/ハングル/タイ文字等を
  引用しているものは正常**（例: Torah のヘブライ語 תּוֹרָה、kimchi の 김치）。
  機械的に一括除去すると教材として価値のある語源記述を壊すため、
  **1件ずつ人が確認した置換表**をここに持つ方式にしてある。

置換表の作り方（次に見つかったとき）:
  1. `scripts/audit_translations.py` を流し、`data/translation_audit.json` の
     `detail_garbled` を見る。
  2. 語源欄で外国語を「引用している」だけのものは対象外。日本語の文の途中に
     外国語の単語が入っているものだけを FIXES に追記する。
  3. `--dry-run`（既定）で当たることを確認してから `--apply`。

使い方（VPSのコンテナ内）:
    docker cp scripts/fix_garbled_details.py eigo-app:/app/scripts/
    docker exec -i eigo-app python scripts/fix_garbled_details.py
    docker exec -i eigo-app python scripts/fix_garbled_details.py --apply
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (テーブル, id) -> [(置換前, 置換後), ...]
# detail JSON を文字列にした状態で置換するので、どのキーに入っていても直る。
# 置換前が見つからなければ「対象なし」として何もしない（冪等）。
FIXES: dict[tuple[str, int], list[tuple[str, str]]] = {
    ("words", 433): [("حاضرしている", "存在している")],
    ("words", 2169): [("入ること、 प्रवेश", "入ること、進入")],
    ("words", 2418): [("白黒の полос状の", "白黒の縞模様の")],
    ("words", 2657): [("「 ضد・反対して」", "「反対して・対抗して」"),
                      ("酸化に ضدするもの", "酸化に対抗するもの")],
    ("words", 2807): [("集まり、 समूह", "集まり、群")],
    ("words", 3158): [("香辛料の मिश्र合", "香辛料の混合")],
    ("words", 3575): [
        ("古英語 bēटल / bēटल? ではなく、古英語 bēटल（「小さな噛む虫」）に由来し",
         "古英語 bitela（「小さな噛む虫」）に由来し"),
    ],
    ("words", 3805): [("政治的 मुद्दについて", "政治的課題について")],
    ("words", 3806): [("連立、 गठ成された協力体制", "連立、結成された協力体制"),
                      ("連立政権を تشکیلした", "連立政権を形成した")],
    ("words", 3813): [("反対、 विरोध", "反対、抵抗"),
                      ("対立、 विरोध関係", "対立、敵対関係")],
    ("words", 3878): [("ライダー आधारितの", "ライダーに基づく")],
    ("words", 4048): [("平地、 मैदान", "平地、野原")],
    ("words", 4049): [("平地、 मैदान", "平地、野原")],
    ("words", 11883): [("特別な धार्मिक・文化的意味",
                        "特別な宗教的・文化的意味")],
    ("words", 11944): [("густく生えている", "密生している")],
    ("words", 11968): [("起伏、 राहत、安堵、救済", "起伏、緩和、安堵、救済")],
    ("words", 12027): [("これ以上 دفاعできなくなった",
                        "これ以上防御できなくなった")],
    ("phrases", 2109): [("친しい間柄", "親しい間柄")],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    done = miss = 0
    with db() as conn:
        for (table, row_id), pairs in FIXES.items():
            row = conn.execute(
                f"SELECT id, english, detail FROM {table} WHERE id = ?",
                (row_id,),
            ).fetchone()
            if not row or not (row["detail"] or "").strip():
                print(f"  [skip] {table}#{row_id} 見つからない/詳細なし")
                miss += 1
                continue
            raw = row["detail"]
            new = raw
            hit = []
            for before, after in pairs:
                # JSON文字列としてエスケープされた形でも当たるようにする。
                enc_b = json.dumps(before, ensure_ascii=False)[1:-1]
                enc_a = json.dumps(after, ensure_ascii=False)[1:-1]
                if enc_b in new:
                    new = new.replace(enc_b, enc_a)
                    hit.append(before)
            if not hit:
                print(f"  [済/対象なし] {table}#{row_id} {row['english']}")
                miss += 1
                continue
            # 壊れたJSONを書き込まないよう検証してから反映する。
            json.loads(new)
            print(f"  [直す] {table}#{row_id} {row['english']}: "
                  + " / ".join(hit))
            if args.apply:
                conn.execute(
                    f"UPDATE {table} SET detail = ? WHERE id = ?",
                    (new, row_id),
                )
            done += 1
        if args.apply:
            conn.commit()
    print(f"\n{'実行' if args.apply else 'ドライラン'}: "
          f"置換 {done} 件 / 対象なし {miss} 件")
    if not args.apply:
        print("※ 実際に更新するには --apply を付けてください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
