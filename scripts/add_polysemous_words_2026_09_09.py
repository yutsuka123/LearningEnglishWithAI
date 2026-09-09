# ruff: noqa: E501
"""多義語(polysemous word)を新規テーマとして追加(2026-09-09・ユーザー指示)。

1つの綴りが文脈によって全く異なる複数の意味を持つ語(bank=銀行/土手等)を
収録する。句動詞(take off等)とは別カテゴリとして扱う方針
(ユーザー指示・scripts/add_phrasal_verbs_take_give_get_2026_09_09.py参照)。

大分類は句動詞と同じく既存の「英語表現」(和製英語・口語等と同じ
「英語表現のニュアンス」系)に合流させ、分野は単一の「多義語」1つ
(句動詞と違い1語あたりの意味数が少ないため動詞ごとの分割は不要。
app/services/taxonomy.py参照)。

同じ英単語(例: bank)が複数の異なる意味を持つ場合は、意味ごとに
別レコードとして登録する(既存の`agent`(3件・意味ごとに別レコード)と
同じ設計)。detailはachieve/acquire等の既存語彙と同じ豊富な形式
(pronunciation/pos/meanings/examples/derivatives/synonyms/antonyms/
origin/trivia/explanation)。特にoriginでは、同じ見出し語の複数の意味が
本当に同じ語源から分岐した「多義語」なのか、たまたま綴りが同じに
なっただけの別語源の「同綴異義語(ホモニム)」なのかを明記している
(これが多義語コンテンツの核心的価値)。

【既存他分野との重複について】bark/bear/bill/kind/light/mean/present/
scale/seal/soundは、投入前の調査で既に他分野(植物/基礎語彙/政治/物理/
統計学/音楽/動物等)に類似の意味が1件ずつ存在すると判明した。ただし
各エントリのorigin/explanationは「同じ語の他の意味」を前提に相互参照
して書かれているため、意味を間引くと文脈が壊れる。多義語分野は「1つの
語の複数の意味を並べて対比する」という別の学習目的を持つため、既存
分野との内容の重複は意図的に許容する方針とした(完全に同一の
(english, japanese)ペアのみ重複除外)。

内容はclaude-fable-5(Agent経由)が作成・自己レビュー済み(語源の
多義語/ホモニム判定の整合性確認、断定回避の見直し含む)。

データ本体: scripts/data/polysemous_words_2026_09_09.json
(50件・18見出し語、english/japanese/example/example_ja/detail)

No app / OpenAI API calls — 手書きデータをSQLiteへ直接投入。

Run:  python scripts/add_polysemous_words_2026_09_09.py

仕上げ: 音声生成が必要(build_audio.py等)。levelは目安値("400"一律)を
直接指定(relevel.pyは未実行・既存のB24バッチと同じ運用)。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DATA_PATH = Path(__file__).resolve().parent / "data" / "polysemous_words_2026_09_09.json"
DOMAIN = "多義語"
DEFAULT_LEVEL = "400"


def main() -> None:
    entries = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    with db() as conn:
        existing = {
            (r["english"].lower(), r["japanese"])
            for r in conn.execute(
                "SELECT english, japanese FROM words").fetchall()
        }
        inserted = 0
        skipped = 0
        for e in entries:
            english = e["english"]
            japanese = e["japanese"]
            key = (english.lower(), japanese)
            if key in existing:
                skipped += 1
                continue
            detail = e["detail"]
            pos = detail.get("pos") or ""
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level, detail) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (english, japanese, pos, e["example"], DOMAIN,
                 DEFAULT_LEVEL, json.dumps(detail, ensure_ascii=False)),
            )
            existing.add(key)
            inserted += 1
    print(f"inserted={inserted} skipped(dup)={skipped} total_source={len(entries)}")


if __name__ == "__main__":
    main()
