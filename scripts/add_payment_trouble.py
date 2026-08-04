# ruff: noqa: E501  (data-heavy seed script: long phrase lines are fine)
"""Top up "クレーム・抗議の英語" with money/payment-trouble phrases, authored
by Claude (2026-08-04・ユーザー要望「困ったときか抗議 おつりが足りないですよ」)。

会計時に困った・おかしいと感じた場面(おつり不足、金額の間違い、二重請求等)で
使う具体的なフレーズを追加する。既存のscripts/add_complaints_refusals.pyの
「クレーム・抗議の英語」シーンを拡張する形。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_payment_trouble.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

SCENE = "クレーム・抗議の英語"

PHRASES: list[tuple[str, str]] = [
    ("I think you've given me the wrong change.", "おつりが違っているようです。"),
    ("You're short on my change.", "おつりが足りないですよ。"),
    ("I'm afraid this isn't the right amount.", "恐れ入りますが、この金額は合っていません。"),
    ("Could you double-check the change, please?", "おつりをもう一度確認していただけますか？"),
    ("I gave you a twenty, not a ten.", "10ドルではなく20ドルをお渡ししました。"),
    ("I think I've been overcharged.", "請求額が多いようです。"),
    ("This doesn't match the price on the tag.", "値札の価格と合っていません。"),
    ("I was charged twice for the same item.", "同じ商品で二重に請求されています。"),
    ("Could you check the receipt with me?", "レシートを一緒に確認していただけますか？"),
    ("I'd like a refund for the difference.", "差額分を返金していただきたいのですが。"),
    ("Sorry to bother you, but the total looks off.", "お手数ですが、合計額がおかしいようです。"),
    ("Could you recount the change, please?", "おつりをもう一度数えていただけますか？"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        added = skipped = 0
        for en, ja in PHRASES:
            if en.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
                (en, ja, SCENE),
            )
            existing.add(en.lower())
            added += 1
    print(f"phrases: +{added} (skipped {skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
