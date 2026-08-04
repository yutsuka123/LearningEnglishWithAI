# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for WATCH / CAMERA / AUDIO-GEAR REVIEW ENGLISH,
authored by Claude.

Focus (フレーズ集の手薄な領域を補強): 腕時計・カメラ/レンズ・オーディオ機器と
いった趣味性の高いガジェットについて、海外のYouTubeレビュアーやフォーラム、
メーカーのスペックシートを日本語訳を待たずに直接読み聞きするための英語。
このホビー層は年齢層が比較的高く可処分所得も大きいため、価値提案は「海外の
レビューを直接読める・聞ける」ことと「海外価格と国内価格を比較できる」こと
にある。

腕時計: ムーブメントの種類(自動巻き・クォーツ・クロノグラフ・コンプリケー
ション)、ケース/素材の語彙(サファイアクリスタル、防水性能、ラグ幅)、レビュー
表現(価格以上の実力、この価格にしては仕上げが素晴らしい、ほどよい手首の存在感)、
購入・真贋確認の語彙(フルセット、箱と保証書、整備履歴、並行輸入)を扱う。

カメラ・レンズ: レビュー表現(ダイナミックレンジ、ボケ味、オートフォーカスの
追尾性能、手ブレ補正、ローリングシャッターが目立つ、色作りが撮って出しでも
素晴らしい)、スペックシート用語(センサーサイズ、開放絞り、ISO感度域、防塵
防滴)を扱う。

オーディオ: ヘッドホン/スピーカーのレビュー表現(サウンドステージ、温かい/
明るい/ニュートラルな音の傾向、ドライバー、インピーダンス、ミッドベースの
膨らみ、優れた解像度)を扱う。

さらに、カテゴリ横断のレビュー総括表現(結論・長所短所の整理、「買い替える
価値があるか」「おすすめできるか」)と購入判断の語彙(輸入関税、並行輸入、
海外から輸入すると保証が無効になる)もカバーする。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_gear_reviews.py
      python scripts/add_gear_reviews.py --missing-words   # report only

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
    "腕時計・レビュー英語": [
        # --- ムーブメントの種類 ---
        ("This is an automatic movement, so it doesn't need a battery.", "自動巻きムーブメントなので電池は不要です。"),
        ("It's a hand-wound movement, so you need to wind it every morning.", "手巻きムーブメントなので毎朝ゼンマイを巻く必要があります。"),
        ("Quartz movements are far more accurate than mechanical ones.", "クォーツムーブメントは機械式よりもはるかに精度が高いです。"),
        ("This chronograph has a 30-minute counter and a running seconds subdial.", "このクロノグラフには30分積算計とスモールセコンドが付いています。"),
        ("The power reserve on this movement is about 70 hours.", "このムーブメントのパワーリザーブ(ゼンマイの持続時間)は約70時間です。"),
        ("It has a date complication at the 3 o'clock position.", "3時位置に日付表示のコンプリケーション(付加機能)が付いています。"),
        ("The movement is chronometer-certified for accuracy.", "このムーブメントは精度についてクロノメーター認定を受けています。"),
        # --- ケース・素材の語彙 ---
        ("It has a sapphire crystal, so it should resist scratches well.", "サファイアクリスタルなので傷に強いはずです。"),
        ("The case measures 40 millimeters, which wears smaller than you'd expect.", "ケース径は40mmですが、見た目より小さく感じます。"),
        ("The lug width is 20 millimeters, so aftermarket straps are easy to find.", "ラグ幅は20mmなので社外品のストラップが探しやすいです。"),
        ("It's rated for 200 meters of water resistance.", "防水性能は200mです。"),
        ("The bezel action has a satisfying, tight click.", "ベゼルの操作感はカチッと締まりのある感触です。"),
        ("The case back is a display back, so you can see the movement.", "ケースバックはシースルーバックで、ムーブメントが見えます。"),
        ("The dial has a nice sunburst finish that catches the light.", "文字盤は光を受けて映える美しいサンバースト仕上げです。"),
        # --- レビュー表現 ---
        ("This watch punches above its price point.", "この時計は価格以上の実力があります。"),
        ("The finishing is excellent for the price.", "この価格にしては仕上げが素晴らしいです。"),
        ("It has a bit of wrist presence without being too bulky.", "大きすぎることなく、ほどよい存在感が手首にあります。"),
        ("The lume is legible even in near-total darkness.", "蓄光塗料はほぼ真っ暗な中でも視認できます。"),
        ("It wears comfortably thanks to the way the lugs curve downward.", "ラグが下向きにカーブしているおかげで着け心地が良いです。"),
        ("The bracelet has a bit of rattle when you shake your wrist.", "ブレスレットは手首を振るとわずかにガタつきます。"),
        # --- 購入・真贋確認の語彙 ---
        ("It comes as a full set, with the original box and papers.", "フルセット、つまりオリジナルの箱と保証書付きです。"),
        ("Always ask for the box and papers when buying a used watch.", "中古の時計を買うときは必ず箱と保証書の有無を確認してください。"),
        ("Do you have the service history for this piece?", "この時計のサービス履歴(整備記録)はありますか。"),
        ("It was bought through the grey market, so the warranty may not be valid locally.", "並行輸入(グレーマーケット)で購入されたので、現地での保証が無効な場合があります。"),
        ("Buying grey market usually means a lower price but no local warranty.", "並行輸入品は通常価格が安い一方、現地での保証がありません。"),
    ],
    "カメラ・レンズレビュー英語": [
        # --- レビュー表現 ---
        ("The dynamic range on this sensor is impressive.", "このセンサーのダイナミックレンジは素晴らしいです。"),
        ("The bokeh from this lens is really creamy.", "このレンズのボケ味は本当に滑らかです。"),
        ("Autofocus tracking locks onto the subject's eye instantly.", "オートフォーカスの追尾は瞬時に被写体の瞳に食いつきます。"),
        ("Image stabilization lets you shoot handheld at slower shutter speeds.", "手ブレ補正のおかげで手持ちでもより遅いシャッター速度で撮影できます。"),
        ("This camera has noticeable rolling shutter when you pan quickly.", "このカメラは素早くパンするとローリングシャッター現象が目立ちます。"),
        ("The color science is fantastic straight out of camera.", "色作り(カラーサイエンス)は撮って出しでも素晴らしいです。"),
        ("Skin tones look accurate without any extra color grading.", "追加の色調整なしでも肌色が自然に見えます。"),
        ("Low-light performance falls off noticeably above ISO 6400.", "ISO6400を超えると低照度性能が目に見えて落ちます。"),
        ("The autofocus hunts a bit in low-contrast scenes.", "コントラストの低いシーンではオートフォーカスが少し迷います(ハンチングします)。"),
        ("Detail retention in the shadows is excellent when you lift them in post.", "現像でシャドウを持ち上げても、ディテールがよく残っています。"),
        # --- スペックシート用語 ---
        ("The sensor size is full-frame, which helps in low light.", "センサーサイズはフルフレームで、低照度撮影に有利です。"),
        ("This lens has a maximum aperture of f/1.4.", "このレンズの開放絞りはf/1.4です。"),
        ("The native ISO range tops out at 51,200.", "標準ISO感度は最大51200までです。"),
        ("It's weather-sealed, so light rain shouldn't be an issue.", "防塵防滴仕様なので小雨でも問題ないはずです。"),
        ("The lens has an internal zoom, so the front element doesn't rotate.", "インナーズームなのでレンズ前玉が回転しません。"),
        ("Minimum focusing distance is just 20 centimeters.", "最短撮影距離はわずか20cmです。"),
        ("The body has in-body image stabilization rated at 7 stops.", "ボディ内手ブレ補正は7段分の効果があります。"),
        ("Continuous shooting tops out at 20 frames per second with the electronic shutter.", "電子シャッター使用時の連写速度は最大20コマ/秒です。"),
        ("The viewfinder shows a bit of lag in low light.", "ファインダーは低照度下だと若干のラグがあります。"),
        ("This lens renders flare beautifully instead of killing contrast.", "このレンズはフレアを汚く出さず、むしろ美しく表現します。"),
    ],
    "オーディオ機材レビュー英語": [
        # --- ヘッドホン・スピーカーのレビュー表現 ---
        ("The soundstage is surprisingly wide for a closed-back headphone.", "密閉型にしてはサウンドステージ(音の広がり)が驚くほど広いです。"),
        ("The tuning leans warm, with a relaxed treble.", "チューニングは温かみのある方向で、高音は落ち着いています。"),
        ("It has a fairly neutral tuning, so it works well for mixing.", "かなりニュートラルなチューニングなのでミックス作業にも向いています。"),
        ("This has a real mid-bass hump that some listeners will find fatiguing.", "ミッドベースの膨らみが結構あり、聴き疲れすると感じる人もいるでしょう。"),
        ("Detail retrieval is excellent, especially in the upper midrange.", "特に中高域において、解像度(ディテール表現)は素晴らしいです。"),
        ("The driver is a 40-millimeter dynamic unit.", "ドライバーは40mmのダイナミック型です。"),
        ("Impedance is low enough to drive straight from a phone.", "インピーダンスが低いのでスマホから直接ドライブできます。"),
        ("The bass is punchy but doesn't bleed into the mids.", "低音はパンチがありますが中音域に被ってきません。"),
        ("Vocals sound a touch recessed compared to the instruments.", "ボーカルは楽器隊と比べてやや引っ込んで聞こえます。"),
        ("The clamping force is on the tighter side right out of the box.", "開封直後は側圧がやや強めです。"),
        ("Instrument separation is excellent even in busy passages.", "音数の多いパッセージでも楽器の分離は優れています。"),
        ("It has a bright signature that favors upper frequencies.", "高域寄りの明るいサウンドシグネチャーです。"),
        # --- カテゴリ横断のレビュー総括表現 ---
        ("Here's the verdict: it's a solid buy if you value build quality over raw specs.", "結論としては、スペックよりも作りの良さを重視するなら十分買いです。"),
        ("Let's go through the pros and cons before we wrap up.", "まとめの前に、長所と短所を整理しましょう。"),
        ("Is it worth the upgrade from the previous model?", "前モデルからのアップグレードに見合う価値はありますか。"),
        ("Would I recommend it? Yes, but only at this price point.", "おすすめするかというと、はい、ただしこの価格でならです。"),
        ("Overall, it's a solid option if you can live with the trade-offs.", "総合的に見て、妥協点を受け入れられるなら良い選択肢です。"),
        ("It's not a night-and-day difference, but it's noticeable in side-by-side comparisons.", "劇的な違いではありませんが、並べて比較すると分かる差です。"),
        # --- 購入判断の語彙 ---
        ("You'll likely have to pay import duty if you order it from overseas.", "海外から注文すると輸入関税がかかる可能性が高いです。"),
        ("Grey-market imports are usually cheaper, but you lose local support.", "並行輸入品は通常安いですが、現地サポートを失います。"),
        ("The warranty voids if it's imported outside the official distributor.", "正規代理店以外からの輸入は保証が無効になります。"),
        ("Factor in the exchange rate and shipping before comparing overseas prices.", "海外価格を比較する前に為替と送料を考慮に入れてください。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("movement", "(時計の)ムーブメント・機構", "名詞", "This watch has a Swiss automatic movement.", "趣味・ガジェット", "700"),
    ("chronograph", "クロノグラフ(ストップウォッチ機能付き時計)", "名詞", "He wears a vintage chronograph to the office.", "趣味・ガジェット", "800"),
    ("complication", "(時計の)複雑機構・付加機能", "名詞", "A moon-phase complication adds a lot to the price.", "趣味・ガジェット", "900"),
    ("bezel", "ベゼル(文字盤の外枠)", "名詞", "The dive bezel rotates in one direction only.", "趣味・ガジェット", "800"),
    ("lug width", "ラグ幅(ストラップの取り付け幅)", "名詞", "Check the lug width before you order a new strap.", "趣味・ガジェット", "800"),
    ("sapphire crystal", "サファイアクリスタル(傷に強い風防素材)", "名詞", "A sapphire crystal barely scratches even with daily wear.", "趣味・ガジェット", "800"),
    ("water resistance", "防水性能", "名詞", "The water resistance is rated to 100 meters.", "趣味・ガジェット", "700"),
    ("grey market", "並行輸入市場", "名詞", "It was sold through the grey market, not an authorized dealer.", "趣味・ガジェット", "900"),
    ("service history", "(時計の)整備履歴", "名詞", "A watch with full service history holds its value better.", "趣味・ガジェット", "800"),
    ("dynamic range", "ダイナミックレンジ(明暗の再現幅)", "名詞", "This sensor has a wider dynamic range than the previous model.", "趣味・ガジェット", "800"),
    ("bokeh", "ボケ味(背景のぼやけ具合)", "名詞", "This lens produces smooth, creamy bokeh.", "趣味・ガジェット", "800"),
    ("autofocus", "オートフォーカス(自動焦点合わせ)", "名詞", "The autofocus struggles a little in dim light.", "趣味・ガジェット", "700"),
    ("image stabilization", "手ブレ補正", "名詞", "Image stabilization lets you shoot handheld at night.", "趣味・ガジェット", "800"),
    ("rolling shutter", "ローリングシャッター現象(高速動体の歪み)", "名詞", "Fast panning shots show visible rolling shutter.", "趣味・ガジェット", "900"),
    ("weather-sealed", "防塵防滴仕様の", "形容詞", "The body is weather-sealed against dust and light rain.", "趣味・ガジェット", "800"),
    ("color science", "色作り・カラーサイエンス", "名詞", "This brand's color science is known for accurate skin tones.", "趣味・ガジェット", "900"),
    ("soundstage", "サウンドステージ(音の広がり・定位感)", "名詞", "Open-back headphones usually have a wider soundstage.", "趣味・ガジェット", "800"),
    ("driver", "ドライバー(音を鳴らす振動板ユニット)", "名詞", "This headphone uses a large 50-millimeter driver.", "趣味・ガジェット", "700"),
    ("tuning", "(音の)チューニング・音作り", "名詞", "The tuning favors clarity over raw bass.", "趣味・ガジェット", "700"),
    ("import duty", "輸入関税", "名詞", "You may have to pay import duty on gear ordered from abroad.", "趣味・ガジェット", "800"),
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
