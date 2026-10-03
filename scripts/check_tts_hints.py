"""app/services/tts_hints.py(TTSに渡す綴りの読み替え)の検査(2026-10-03)。

読み替えが要る語だけが変わり、それ以外のテキストは1文字も変わらない(=既存のtts_cacheキー・音声が不変)ことを確かめる。
本番・外部には触れない。  .venv/bin/python scripts/check_tts_hints.py   # 0=全部OK
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.tts_hints import spoken_text  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("  OK   " if cond else "  FAIL ") + name + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


print("== 読み替えされる(冠詞と紛れる外来表現のa/à・roman à clef)")
CASES = {
    "a cappella": "ah cappella",
    "A cappella": "Ah cappella",
    "a capella": "ah capella",
    "The choir sang the closing song a cappella, with no instruments.":
        "The choir sang the closing song ah cappella, with no instruments.",
    "a cappella-style harmonies": "ah cappella-style harmonies",
    "à la carte": "ah lah carte",
    "À la carte menu": "Ah lah carte menu",
    "a la carte": "ah lah carte",
    "Could I order à la carte instead?": "Could I order ah lah carte instead?",
    "The à la carte menu lets you choose exactly what you want.":
        "The ah lah carte menu lets you choose exactly what you want.",
    "pie à la mode": "pie ah lah mode",
    "roman à clef": "roh-mahn ah klay",
    "Roman à clef": "Roh-mahn ah klay",
    "romans à clef": "roh-mahnz ah klay",
    "Readers tried to identify the real people hidden behind the characters in the roman à clef.":
        "Readers tried to identify the real people hidden behind the characters in the roh-mahn ah klay.",
    "roman a clef": "roh-mahn ah klay",
    "roman-à-clef": "roh-mahn ah klay",            # 英語ではハイフン綴りも一般的
    "A LA CARTE": "Ah LAH CARTE",                  # 全大文字でも"LAh"(綴り読みされうる形)にしない
}
for src, want in CASES.items():
    got = spoken_text(src)
    check(f"{src!r} → {want!r}", got == want, got)

print("== 変わらない(普通の冠詞・別の語・音楽のclef・ローマ)")
SAME = [
    "a cat", "a capable person", "a capital idea", "a cap", "a cappellas are rare",   # 末尾が別の語
    "She has a la... pause", "a lazy day", "a labour of love", "a carte blanche",
    "treble clef", "a bass clef", "the clef sign", "Roman Empire", "a Roman soldier", "roman numerals",
    "pre-a cappella", "Alla breve", "ala carte menu", "prêt-à-porter", "Penne alla vodka", "the star Capella",
    "for the sake of it", "I like to drink warm tea.", "", "a",
]
for t in SAME:
    check(f"{t!r} は不変", spoken_text(t) == t, spoken_text(t))

print("== 既存の読み替え(sake・日本語由来語)は不変")
check("sake → sah-kee", spoken_text("a bottle of sake") == "a bottle of sah-kee")
check("for the sake of: 不変", spoken_text("for the sake of peace") == "for the sake of peace")
check("sente → sen-tay", spoken_text("sente") == "sen-tay")
check("組み合わせ: sakeとa cappella", spoken_text("sake and a cappella") == "sah-kee and ah cappella")

print()
if FAILS:
    print(f"❌ 失敗 {len(FAILS)} 件: " + ", ".join(FAILS))
    raise SystemExit(1)
print("✅ すべて成功")
