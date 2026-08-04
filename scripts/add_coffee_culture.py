# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for COFFEE TASTING / CAFÉ CULTURE ENGLISH,
authored by Claude.

Focus (フレーズ集の手薄な領域を補強): コーヒーのテイスティング・カフェ文化に
関する英語。単なる注文フレーズではなく、実際の味覚体験と英単語を結びつける
テイスティング表現（酸味・ボディ・フレーバーノート・後味など）、産地・生産
に関する語彙（シングルオリジン、農園、品種、標高、精製方法、カッピング）、
抽出・淹れ方の語彙（ハンドドリップ、フレンチプレス、エスプレッソ抽出、粉量、
挽き目、チャネリング、サードウェーブコーヒー）、海外のカフェで注文・会話
する際の定型表現、そして海外のコーヒーレビュー動画・ロースターの解説・
YouTubeコンテンツを聞き取るための語彙を体系的に強化する。

意図的にコーヒーのみに範囲を絞っている（アルコール類は年齢確認・広告規制の
懸念から別枠で扱う方針のため、本バッチには含めない）。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_coffee_culture.py
      python scripts/add_coffee_culture.py --missing-words   # report only

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "コーヒー・テイスティング英語": [
        # --- テイスティング表現・風味の表現 ---
        ("This has a really bright acidity.", "これは酸味が際立っていますね。〔明るく心地よい酸味〕"),
        ("It's quite full-bodied for a light roast.", "浅煎りにしては、かなりコクがありますね。"),
        ("I'm getting notes of stone fruit in this one.", "これは核果系の香りを感じますね。〔桃やアプリコットのような〕"),
        ("There's a nice floral aroma to it.", "花のような良い香りがしますね。"),
        ("It has an earthy, almost woody quality.", "土っぽさというか、木のような質感がありますね。"),
        ("I'm picking up some nutty, chocolatey notes.", "ナッツやチョコレートのような風味を感じます。"),
        ("The finish is really clean.", "後味がとてもすっきりしていますね。"),
        ("It's well balanced between sweetness and acidity.", "甘みと酸味のバランスが良いですね。"),
        ("This coffee has a syrupy mouthfeel.", "口当たりがシロップのように濃厚ですね。"),
        ("There's a lingering aftertaste of dark chocolate.", "ダークチョコレートのような後味が残りますね。"),
        ("It tastes a bit winey, almost like berries.", "ワインのような、ベリーに近い風味がしますね。"),
        ("This cup is more citrusy than I expected.", "思ったより柑橘系の風味がしますね。"),
        ("The sweetness really comes through once it cools down.", "冷めてくると甘みがはっきり出てきますね。"),
        ("It's a bit muddy on the palate.", "口の中でやや雑味がありますね。〔ネガティブな評価〕"),
        ("That's a really clean cup, no off-flavors at all.", "雑味のない、きれいな一杯ですね。"),
        # --- 産地・生産に関する表現 ---
        ("Is this a single-origin coffee or a blend?", "これはシングルオリジンですか、それともブレンドですか？"),
        ("It's grown on a small estate in Ethiopia.", "エチオピアの小さな農園で栽培されたものです。"),
        ("What varietal is this?", "これは何という品種ですか？"),
        ("It's a Bourbon varietal grown at high altitude.", "高地で栽培されたブルボン種です。"),
        ("Higher altitude usually means more acidity.", "標高が高いほど酸味が強くなる傾向があります。"),
        ("Was this naturally processed or washed?", "これはナチュラル製法ですか、それともウォッシュト製法ですか？"),
        ("The natural process really brings out the fruitiness.", "ナチュラル製法だとフルーティーさがより引き立ちますね。"),
        ("Honey process beans tend to be sweeter.", "ハニープロセスの豆は甘みが強くなる傾向があります。"),
        ("This lot scored 87 on the cupping table.", "このロットはカッピングで87点でした。"),
        ("You can really taste the terroir in this one.", "これは産地の風土がしっかり味に出ていますね。"),
        ("Who's the producer behind this coffee?", "この豆の生産者はどなたですか？"),
        ("This was harvested at the peak of the season.", "旬のピーク時に収穫されたものです。"),
        # --- 抽出・淹れ方に関する表現 ---
        ("Could I get that as a pour-over instead?", "それをハンドドリップでいただけますか？"),
        ("I usually brew this with a French press.", "普段はフレンチプレスで淹れています。"),
        ("The extraction took about 28 seconds.", "抽出には約28秒かかりました。"),
        ("What dose are you using for this shot?", "このショットは何グラムの粉を使っていますか？"),
        ("I got an eighteen-gram yield from an eighteen-gram dose.", "18グラムの粉から18グラムの抽出量を得ました。〔1対1の比率〕"),
        ("You'll want a finer grind size for espresso.", "エスプレッソにはもっと細かい挽き目が必要ですね。"),
        ("Try a coarser grind if it's tasting bitter.", "苦く感じるなら、もっと粗い挽き目を試してみてください。"),
        ("There's some channeling happening in the puck.", "パックの中でチャネリングが起きていますね。〔抽出のお湯が偏る現象〕"),
        ("That's a classic sign of third-wave coffee culture.", "それはサードウェーブコーヒー文化の典型的な特徴ですね。"),
        ("Let the coffee bloom for about thirty seconds first.", "まず30秒ほど蒸らしてください。〔ハンドドリップの最初の工程〕"),
        ("Tamp it evenly so the water flows through consistently.", "お湯が均一に通るよう、平らにタンピングしてください。"),
        ("I'm using a 1-to-16 ratio for this pour-over.", "このハンドドリップでは1対16の比率を使っています。"),
        ("This shot looks under-extracted, kind of sour and thin.", "このショットは抽出不足に見えますね、酸っぱくて薄い感じです。"),
        ("It's a bit over-extracted, quite bitter and harsh.", "少し抽出過多ですね、かなり苦くてえぐみがあります。"),
        ("Let's dial in the grinder before we start.", "始める前にグラインダーの設定を調整しましょう。〔味が最適になるよう微調整する〕"),
        # --- カフェでの注文・会話表現 ---
        ("What's your house blend like?", "こちらのハウスブレンドはどんな感じですか？"),
        ("Could I get a flat white, please?", "フラットホワイトをいただけますか？"),
        ("Do you have any single-origin options today?", "本日シングルオリジンの豆はありますか？"),
        ("What's the story behind this bean?", "この豆の背景を教えていただけますか？"),
        ("This has a really clean finish, I love it.", "これはとても後味がすっきりしていて、気に入りました。"),
        ("Honestly, it tastes a bit under-extracted to me.", "正直、少し抽出不足のように感じます。"),
        ("Could you recommend something with a lighter roast?", "浅煎りのものでおすすめはありますか？"),
        ("I'd love to try it as a pour-over if that's possible.", "可能であればハンドドリップで試してみたいです。"),
        ("What roast level would you suggest for this bean?", "この豆にはどのくらいの焙煎度合いがおすすめですか？"),
        ("Is this bean better suited to espresso or filter brewing?", "この豆はエスプレッソ向きですか、それともフィルター向きですか？"),
        ("Could I get a taste before I decide?", "決める前に少し試飲させていただけますか？"),
        # --- 海外のレビュー動画・ロースター解説を聞き取るための表現 ---
        ("Today we're cupping three different washed Ethiopians.", "今日はエチオピア産のウォッシュト豆を3種類カッピングします。"),
        ("Let's crack open a fresh bag and see how it smells.", "新しい袋を開けて香りを確かめてみましょう。"),
        ("The notes of stone fruit really come through on this one.", "これは核果系の風味がしっかり感じられますね。"),
        ("This roast really brings out the chocolatey sweetness.", "この焙煎はチョコレートのような甘みをよく引き出していますね。"),
        ("I'll leave a link to this roaster in the description.", "この焙煎業者へのリンクは概要欄に貼っておきます。"),
        ("Let me know in the comments what you'd like me to review next.", "次に何をレビューしてほしいか、コメントで教えてください。"),
        ("Overall, this is a solid daily-drinker at a great price.", "全体として、これは価格も手頃な日常使いに良い一杯です。〔毎日飲むのに適した豆〕"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("acidity", "酸味・酸味の質", "名詞", "This coffee has a bright, citrusy acidity.", "コーヒー", "700"),
    ("mouthfeel", "口当たり・舌触り", "名詞", "The mouthfeel is silky and smooth.", "コーヒー", "800"),
    ("varietal", "（コーヒー豆の）品種", "名詞", "Bourbon is a popular coffee varietal.", "コーヒー", "800"),
    ("cupping", "カッピング（コーヒーの品質評価法）", "名詞", "They hold a cupping session every morning.", "コーヒー", "800"),
    ("terroir", "産地の風土（味への影響）", "名詞", "You can really taste the terroir in this cup.", "コーヒー", "800"),
    ("extraction", "（コーヒーの）抽出", "名詞", "The extraction took about 28 seconds.", "コーヒー", "700"),
    ("crema", "クレマ（エスプレッソ上部の泡層）", "名詞", "Look at that thick, golden crema.", "コーヒー", "800"),
    ("barista", "バリスタ", "名詞", "The barista recommended the house blend.", "コーヒー", "500"),
    ("blend", "ブレンド（複数豆の配合）", "名詞", "This is our signature blend.", "コーヒー", "500"),
    ("grind", "挽き具合・挽いたコーヒー粉", "名詞", "You'll need a finer grind for espresso.", "コーヒー", "600"),
    ("dose", "（抽出に使う）豆の量", "名詞", "I used an eighteen-gram dose for this shot.", "コーヒー", "700"),
    ("channeling", "チャネリング（抽出時に湯が偏って通る現象）", "名詞", "Channeling can ruin an otherwise good shot.", "コーヒー", "800"),
    ("astringent", "渋みのある", "形容詞", "An under-extracted shot can taste astringent.", "コーヒー", "800"),
    ("aftertaste", "後味", "名詞", "It leaves a pleasant, chocolatey aftertaste.", "コーヒー", "600"),
    ("roaster", "焙煎業者・焙煎機", "名詞", "This roaster is known for light, fruity roasts.", "コーヒー", "600"),
    ("tamp", "（コーヒー粉を）押し固める・タンピングする", "動詞", "Tamp the grounds evenly before brewing.", "コーヒー", "800"),
    ("single-origin", "シングルオリジンの（単一産地の）", "形容詞", "It's a single-origin coffee from Ethiopia.", "コーヒー", "700"),
    ("full-bodied", "コクのある・ボディがしっかりした", "形容詞", "This espresso blend is rich and full-bodied.", "コーヒー", "700"),
]


# --- insertion --------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_STOP = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "for", "with", "from", "by", "as", "is", "are", "was", "were", "be", "been",
    "do", "does", "did", "have", "has", "had", "will", "would", "can", "could",
    "should", "may", "might", "must", "i", "you", "he", "she", "it", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our",
    "their", "this", "that", "these", "those", "here", "there", "what", "when",
    "where", "who", "how", "why", "not", "no", "yes", "so", "up", "out", "off",
    "down", "let", "lets", "please", "thanks", "thank", "ok", "okay", "im",
    "ill", "id", "ive", "dont", "cant", "wont", "isnt", "thats", "whats",
    "very", "just", "too", "more", "some", "any", "all", "one", "two", "get",
    "got", "go", "going", "like", "want", "need", "make", "made", "take",
    "see", "now", "today", "tonight", "good", "well", "back", "about", "over",
    "into", "than", "then", "again", "really", "much", "many", "wish", "mind",
    "could", "would", "shall", "rather", "ever", "way", "instead", "kind",
    "quite", "bit", "little", "before", "start", "look", "leave", "love",
    "next", "great", "price", "story", "behind", "different", "three",
}


def _content_words(phrases: list[tuple[str, str]]) -> set[str]:
    out: set[str] = set()
    for en, _ in phrases:
        for tok in _WORD_RE.findall(en.lower()):
            w = tok.strip("'-")
            if len(w) >= 4 and w not in _STOP:
                out.add(w)
    return out


def report_missing() -> None:
    """Print content words used in the new phrases that are not yet in `words`
    and not covered by the WORDS list above (authoring aid)."""
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
    covered = {w[0].lower() for w in WORDS}
    all_phrases = [p for lst in PHRASES_BY_SCENE.values() for p in lst]
    missing = sorted(
        w for w in _content_words(all_phrases)
        if w not in existing and w not in covered
    )
    print(f"missing content words ({len(missing)}):")
    print(", ".join(missing))


def main() -> int:
    if "--missing-words" in sys.argv:
        report_missing()
        return 0

    with db() as conn:
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }

        ph_added = ph_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1

        w_added = w_skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in w_existing:
                w_skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            w_existing.add(en.lower())
            w_added += 1

    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("totals -> phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
              "words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
