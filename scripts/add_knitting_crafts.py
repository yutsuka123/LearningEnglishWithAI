# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for READING OVERSEAS KNITTING / CROCHET PATTERNS
AND NEEDLECRAFT COMMUNITY ENGLISH, authored by Claude.

Focus (フレーズ集の手薄な領域を補強): 編み物・かぎ針編みは海外のパターン
(Ravelry, Etsy, ブログ, YouTube)やコミュニティが非常に豊富だが、パターン
特有の略語体系(k, p, sl st, yo, k2togなど)と、米国式・英国式で用語が食い
違う罠(single crochet / double crochetが指す編み目が全く異なる、など)が
あるため、機械翻訳では正確に読み解けない。この領域は初心者が最初につまずく
「パターンの略語が読めない」という壁を取り除くことに価値がある。

編み物略語: k(表編み)、p(裏編み)、sl st(すべり目)、yo(かけ目)、
inc/dec(増し目/減らし目)、k2tog、ssk、co/bo(作り目/伏せ止め)、
RS/WS(表面/裏面)、st(s)(目)を扱う。

かぎ針編み略語: ch(鎖編み)、sc(細編み)、dc(長編み)を扱う。特に
sc/dcが指す編み目が米国式と英国式で異なる(UK single crochet = US slip
stitch相当、UK double crochet = US single crochet)という初心者が
必ず引っかかる罠を明示的に注記する。

パターン読解の語彙: gauge/tension swatch(ゲージ/テンションの見本編み)、
right side facing、work even、repeat from *、place marker、block the
finished piece を扱う。

素材・毛糸の語彙: worsted weight、fingering weight、skein、ply、ombre、
variegatedを扱う。

コミュニティ・フォーラム表現: frogging(ほどく)、パターンの米国式/英国式
変換依頼、ゲージが合わず針サイズを変えた、といった実際にRavelryやSNSで
交わされる会話表現を扱う。

さらに刺繍など隣接手芸の基礎語彙(backstitch, satin stitch, start a new
project, I'm on row 40 of 60)も軽く触れる。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_knitting_crafts.py
      python scripts/add_knitting_crafts.py --missing-words   # report only

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
    "編み物・かぎ針編みの海外パターン読解": [
        # --- 編み物の基本略語 ---
        ("K means knit, and p means purl.", "kは表編み、pは裏編みという意味です。"),
        ("Knit every row until the piece measures 10 inches.", "編地が10インチになるまで、全段を表編みしてください。"),
        ("Purl the wrong-side rows.", "裏面の段は裏編みしてください。"),
        ("Sl st means slip stitch — just move the stitch from one needle to the other without knitting it.", "sl stはすべり目という意味です。編まずに片方の針からもう片方へ目を移すだけです。"),
        ("Yo means yarn over — wrap the yarn around the needle to create a new stitch.", "yoはかけ目という意味で、針に糸を巻き付けて新しい目を作ります。"),
        ("Inc means increase, so you're adding a stitch here.", "incは増し目という意味なので、ここで目を1目増やします。"),
        ("Dec means decrease, so you're reducing the stitch count.", "decは減らし目という意味なので、目数を減らします。"),
        ("K2tog means knit two stitches together as one.", "k2togは2目を一緒に表編みして1目にすることです。"),
        ("Ssk stands for slip, slip, knit — it's a left-leaning decrease.", "sskはslip, slip, knitの略で、左に傾く減らし目です。"),
        ("Co means cast on — that's how you start the first row of stitches.", "coは作り目という意味で、最初の段の目を作ることです。"),
        ("Bo means bind off, which is how you finish and secure the last row.", "boは伏せ止めという意味で、最後の段を編み終えて目を留める方法です。"),
        ("RS means the right side, the side that will show on the outside.", "RSは表面のことで、外側に見える面を指します。"),
        ("WS means the wrong side, the side that faces inward.", "WSは裏面のことで、内側を向く面を指します。"),
        ("St or sts is short for stitch or stitches.", "stまたはstsはstitch(目)またはstitches(複数の目)の略です。"),
        # --- かぎ針編みの基本略語 ---
        ("Ch means chain — that's your foundation row.", "chは鎖編みという意味で、土台の段になります。"),
        ("Sc means single crochet.", "scは細編みという意味です。"),
        ("Dc means double crochet.", "dcは長編みという意味です。"),
        # --- 米国式・英国式の罠 ---
        ("Careful — US and UK crochet terms use the same words for different stitches.", "注意してください。米国式と英国式のかぎ針編みは同じ言葉でも指す編み目が違います。"),
        ("A US single crochet is called a double crochet in UK terms.", "米国式の細編み(single crochet)は、英国式では二重編み(double crochet)と呼ばれます。"),
        ("A US double crochet is called a treble crochet in the UK.", "米国式の長編み(double crochet)は、英国式では長々編み(treble crochet)と呼ばれます。"),
        ("This pattern is written in US terms, so double-check before you start if you learned UK terms.", "このパターンは米国式の用語で書かれているので、英国式で覚えた方は始める前によく確認してください。"),
        # --- パターン読解の語彙 ---
        ("Knit a gauge swatch before you start the actual project.", "本編みを始める前に、ゲージを測るための見本編みを編んでください。"),
        ("My gauge doesn't match the pattern, so I need to adjust my needle size.", "ゲージがパターンと合わないので、針のサイズを調整する必要があります。"),
        ("Check your tension swatch against the gauge listed in the pattern.", "自分のテンション見本編みを、パターンに記載されたゲージと照らし合わせてください。"),
        ("With right side facing, knit across the row.", "表面を手前にして、その段を編んでください。"),
        ("Work even in pattern until the piece measures 15 inches.", "編地が15インチになるまで、模様通りに増減なく編み続けてください。"),
        ("Repeat from * to the end of the row.", "*から段の終わりまで繰り返してください。"),
        ("Place a marker to mark the beginning of the round.", "編み始めの位置に目印(マーカー)を付けてください。"),
        ("Slip the marker every time you pass it.", "マーカーを通過するたびにそのまま移してください。"),
        ("Block the finished piece to even out the stitches.", "編み目を整えるため、仕上がった編地をブロッキング(水通しして形を整える)してください。"),
        ("Seam the shoulders together using mattress stitch.", "マットレスステッチで肩を綴じ合わせてください。"),
        ("Weave in the loose ends when you finish a section.", "パーツを編み終えたら、糸端を編み目に編み込んで始末してください。"),
        # --- 素材・毛糸の語彙 ---
        ("This pattern calls for worsted weight yarn.", "このパターンはワーステッド(並太)の毛糸を使います。"),
        ("Fingering weight yarn is much thinner, so it takes longer to knit.", "フィンガリング(極細)の毛糸はずっと細いので、編むのに時間がかかります。"),
        ("I bought three skeins of this yarn, just to be safe.", "念のため、この毛糸を3かせ買いました。"),
        ("This yarn is a 4-ply, so it works well for socks.", "この毛糸は4プライ(4本撚り)なので、靴下によく合います。"),
        ("The ombre yarn shades gradually from light to dark.", "オンブレ染めの毛糸は、明るい色から濃い色へと段階的に変化します。"),
        ("I love how variegated yarn creates a random color pattern as you knit.", "バリエガーテッド(色が不規則に変化する)毛糸は、編むとランダムな色柄になるのが好きです。"),
        # --- コミュニティ・フォーラム表現 ---
        ("I'm frogging this row — I made a mistake ten rows back.", "この段はほどいています。10段前に間違えてしまったので。"),
        ("This pattern is written for US terms, just so you know.", "念のためお伝えしますが、このパターンは米国式の用語で書かれています。"),
        ("Could someone convert this pattern to UK terms for me?", "どなたかこのパターンを英国式の用語に変換していただけませんか。"),
        ("My gauge is off, so I sized down a needle.", "ゲージが合わなかったので、針を1サイズ小さくしました。"),
        ("I'm on row 40 of 60, so I'm almost done with this section.", "60段中40段目まで来たので、このセクションはもうすぐ終わりです。"),
        ("I started a new project last night — a simple beanie.", "昨夜、新しいプロジェクトを始めました。シンプルなビーニーです。"),
        ("Would you mind sharing the pattern link?", "パターンのリンクを共有していただけますか。"),
    ],
    "手芸コミュニティ英語": [
        # --- 刺繍の基礎語彙 ---
        ("Backstitch is a simple, sturdy stitch that's great for outlines.", "バックステッチはシンプルで丈夫なステッチで、輪郭を縫うのに最適です。"),
        ("Satin stitch is used to fill in a shape smoothly.", "サテンステッチは形をなめらかに埋めるのに使われます。"),
        ("Use a French knot for the flower centers.", "花の中心にはフレンチノットを使ってください。"),
        ("Transfer the design onto the fabric before you start stitching.", "縫い始める前に、図案を布に写してください。"),
        ("Hoop the fabric tightly so it doesn't pucker while you stitch.", "縫っている間に布がたるまないよう、刺繍枠にしっかり張ってください。"),
        # --- 全般的なプロジェクト進行の表現 ---
        ("I'm going to start a new project this weekend.", "今週末、新しいプロジェクトを始める予定です。"),
        ("I'm about halfway through the blanket.", "ブランケットはだいたい半分まで進みました。"),
        ("How long did this project take you to finish?", "このプロジェクトを完成させるのにどれくらいかかりましたか。"),
        ("I ran out of yarn before I finished the sleeve.", "袖を編み終える前に毛糸が足りなくなりました。"),
        ("Do you have a pattern recommendation for beginners?", "初心者向けのおすすめパターンはありますか。"),
        ("I frogged the whole thing and started over.", "全部ほどいて最初からやり直しました。"),
        ("This yarn is a bit splitty, so be careful with your needle tip.", "この毛糸は糸が割れやすいので、針先に気をつけてください。"),
        ("I love the texture this stitch pattern creates.", "このステッチパターンが作る質感がとても好きです。"),
        ("Could you recommend a good online pattern shop?", "おすすめのオンラインパターンショップを教えていただけますか。"),
        ("I joined a local craft circle that meets every Wednesday.", "毎週水曜に集まる地元の手芸サークルに参加しました。"),
        ("Show us a photo of your finished project!", "完成した作品の写真を見せてください！"),
        ("This is going to be a gift, so I want the finishing to look neat.", "これはプレゼントにする予定なので、仕上げをきれいにしたいです。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("stitch", "編み目・縫い目", "名詞", "Count your stitches before you start the next row.", "手芸", "500"),
    ("cast on", "作り目をする", "動詞", "Cast on 30 stitches using a long-tail cast-on.", "手芸", "700"),
    ("bind off", "伏せ止めする", "動詞", "Bind off all stitches once the scarf reaches the right length.", "手芸", "700"),
    ("gauge", "ゲージ(編み目の密度)", "名詞", "Knitting a gauge swatch first will save you a lot of frustration.", "手芸", "700"),
    ("swatch", "見本編み・試し編み", "名詞", "Wash and block your swatch the same way you'll treat the final piece.", "手芸", "800"),
    ("increase", "増し目・目を増やす", "動詞", "Increase one stitch at the beginning of every other row.", "手芸", "600"),
    ("decrease", "減らし目・目を減らす", "動詞", "Decrease evenly across the round to shape the crown.", "手芸", "600"),
    ("crochet hook", "かぎ針", "名詞", "Use a smaller crochet hook for a tighter fabric.", "手芸", "600"),
    ("knitting needle", "編み針", "名詞", "Circular knitting needles work well for large projects.", "手芸", "500"),
    ("skein", "かせ(毛糸の巻き)", "名詞", "One skein wasn't quite enough to finish the hat.", "手芸", "700"),
    ("worsted weight", "ワーステッド(並太)糸", "名詞", "Worsted weight yarn is a good default for beginner projects.", "手芸", "800"),
    ("fingering weight", "フィンガリング(極細)糸", "名詞", "Fingering weight yarn is popular for socks and shawls.", "手芸", "800"),
    ("variegated", "色が不規則に変化する", "形容詞", "The variegated yarn pooled in an interesting way on this pattern.", "手芸", "800"),
    ("frog", "編み目をほどく", "動詞", "I had to frog three rows to fix the mistake.", "手芸", "700"),
    ("block", "ブロッキングする(水通しして形を整える)", "動詞", "Block the sweater pieces before you seam them together.", "手芸", "700"),
    ("seam", "綴じ合わせる・縫い合わせる", "動詞", "Seam the side edges together with a whip stitch.", "手芸", "600"),
    ("marker", "目印・マーカー", "名詞", "Slip the marker whenever you reach it.", "手芸", "500"),
    ("colorwork", "配色編み", "名詞", "This is my first sweater with colorwork on the yoke.", "手芸", "800"),
    ("embroidery", "刺繍", "名詞", "She learned embroidery from her grandmother.", "手芸", "600"),
    ("backstitch", "バックステッチ", "名詞", "Backstitch is often the first stitch beginners learn.", "手芸", "700"),
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
    "could", "would", "shall", "rather", "ever", "way", "everyone", "everybody",
    "minute", "minutes", "second", "seconds", "little", "bit", "few", "keep",
    "sorry", "still", "afterward", "instead", "else", "same", "time", "next",
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
