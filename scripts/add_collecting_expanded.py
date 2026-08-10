# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Expand the existing "コレクター" domain with genre-specific collecting
vocabulary and swap-meet/show-and-tell phrases, authored by Claude
(2026-08-10・ユーザー要望).

既存の18語(collectible, provenance, authentic, counterfeit, reproduction,
aftermarket, foxing, hairline crack, condition report, appraisal, militaria,
lot, reserve price, outbid, bundle, insured shipping, customs declaration,
buyer's premium)は真贋・状態評価・オークション取引まわりの一般語彙が中心
だったため、それとは別に「収集ジャンルごとの呼称」を厚めに追加する。

対象語彙: サイン(オートグラフ)収集(signed copy, inscription, certificate
of authenticity, memorabilia, autograph book, commemorative medal)、古書
収集(bibliophile, first edition, dust jacket, bookplate, association copy,
rebind, tight copy)、切手収集/philately(philately, philatelist,
perforation, watermark, postmark, first day cover, stamp hinge, mint
condition)、貨幣収集/numismatics(numismatics, numismatist, mint mark,
obverse, reverse, patina, uncirculated, coin album, proof coin)、紙幣収集
/notaphily(notaphily, serial number, star note)、exonumia(通貨に似た収集
物: exonumia, trade token)、交換会まわりの一般語(swap meet, want list)。
固有名詞は一切使用していない。

フレーズは収集家同士が実際に交わす会話(何を集めているか尋ねる、重複品を
交換する、コレクションを見せ合う、スワップミートで話す等)を収録。既存の
`scripts/add_collector_auctions.py` が "海外オークション・コレクター英語"
scene で海外オンラインオークション(eBay等)の出品説明の読み書き・価格交渉
・配送/税関まわりに特化しているのに対し、本ファイルは対面での収集家同士
の雑談・見せ合い・交換に焦点を当てており、scene が重複しないよう新規に
`コレクションの英語` scene を作成する。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_collecting_expanded.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- サイン(オートグラフ)収集 ---
    ("signed copy", "サイン入りの本・品", "名詞", "This is a signed copy of the author's first novel.", "コレクター", "500"),
    ("inscription", "(サインに添える)献辞・書き込み", "名詞", "The inscription includes the date and a short note to the recipient.", "コレクター", "700"),
    ("certificate of authenticity", "真贋証明書", "名詞", "The print comes with a certificate of authenticity.", "コレクター", "700"),
    ("memorabilia", "記念グッズ・思い出の品", "名詞", "He keeps his sports memorabilia in a locked case.", "コレクター", "600"),
    ("autograph book", "サイン帳", "名詞", "Fans lined up outside the theater with autograph books in hand.", "コレクター", "600"),
    ("commemorative medal", "記念メダル", "名詞", "The organizers gave every finisher a commemorative medal.", "コレクター", "600"),
    # --- 古書収集 ---
    ("bibliophile", "愛書家・本の収集家", "名詞", "As a bibliophile, she can't resist a used bookstore.", "コレクター", "850"),
    ("first edition", "初版本", "名詞", "A first edition in good condition can be quite valuable.", "コレクター", "600"),
    ("dust jacket", "(本の)ブックカバー", "名詞", "The dust jacket is torn, which lowers the book's value.", "コレクター", "700"),
    ("bookplate", "蔵書票", "名詞", "The bookplate inside the cover shows the book's original owner.", "コレクター", "750"),
    ("association copy", "由緒本(著者ゆかりの人物が所有していた本)", "名詞", "An association copy once owned by the author sells for more.", "コレクター", "900"),
    ("rebind", "(本を)綴じ直す", "動詞", "The library plans to rebind several damaged volumes.", "コレクター", "700"),
    ("tight copy", "綴じがまだしっかりした状態の本", "名詞", "Booksellers describe a tight copy as one whose binding still feels firm.", "コレクター", "850"),
    # --- 切手収集(philately) ---
    ("philately", "切手収集・郵趣", "名詞", "Philately remains one of the most popular collecting hobbies.", "コレクター", "850"),
    ("philatelist", "切手収集家", "名詞", "A philatelist can often date a stamp just by its design.", "コレクター", "850"),
    ("perforation", "(切手の)目打ち", "名詞", "Collectors check the perforation to help identify a stamp's edition.", "コレクター", "800"),
    ("watermark", "透かし", "名詞", "Hold the stamp up to the light to see the watermark.", "コレクター", "700"),
    ("postmark", "消印", "名詞", "The postmark shows exactly when and where the letter was sent.", "コレクター", "600"),
    ("first day cover", "初日カバー(発行初日の消印付き封筒)", "名詞", "He mailed the envelope to himself to create a first day cover.", "コレクター", "800"),
    ("stamp hinge", "切手貼付用ヒンジ", "名詞", "A stamp hinge lets you mount stamps without damaging the gum.", "コレクター", "800"),
    ("mint condition", "(未使用の)完全な状態", "名詞", "The stamp is still in mint condition, with the original gum intact.", "コレクター", "650"),
    # --- 貨幣収集(numismatics) ---
    ("numismatics", "貨幣学・コイン収集", "名詞", "Numismatics covers the study and collecting of coins and medals.", "コレクター", "850"),
    ("numismatist", "貨幣収集家", "名詞", "A numismatist appraised the old silver dollar for us.", "コレクター", "850"),
    ("mint mark", "(硬貨の)造幣局刻印", "名詞", "The mint mark tells you which facility produced the coin.", "コレクター", "750"),
    ("obverse", "(硬貨の)表面", "名詞", "The obverse of the coin shows a portrait of the ruler.", "コレクター", "800"),
    ("reverse", "(硬貨の)裏面", "名詞", "Turn the coin over to see the design on the reverse.", "コレクター", "600"),
    ("patina", "経年変化による皮膜・緑青", "名詞", "Collectors often prize the natural patina on old bronze coins.", "コレクター", "800"),
    ("uncirculated", "未流通の", "形容詞", "This coin is uncirculated and has never been used as currency.", "コレクター", "750"),
    ("coin album", "コインアルバム", "名詞", "He organizes his collection in a coin album by year.", "コレクター", "500"),
    ("proof coin", "プルーフコイン(特別仕上げの記念硬貨)", "名詞", "A proof coin is struck twice for an especially sharp finish.", "コレクター", "750"),
    # --- 紙幣収集(notaphily) ---
    ("notaphily", "紙幣収集", "名詞", "Notaphily is the collecting and study of paper money.", "コレクター", "900"),
    ("serial number", "通し番号・シリアルナンバー", "名詞", "Collectors sometimes pay extra for banknotes with a unique serial number.", "コレクター", "500"),
    ("star note", "スターノート(印刷ミス代替用の紙幣)", "名詞", "A star note is a replacement bill printed to fix a printing error.", "コレクター", "850"),
    # --- exonumia・交換会まわり ---
    ("exonumia", "エクソヌミア(通貨に似た収集物の総称)", "名詞", "Exonumia includes tokens and medals that aren't official currency.", "コレクター", "900"),
    ("trade token", "商店発行のトレードトークン", "名詞", "Trade tokens were once used in place of coins at certain shops.", "コレクター", "800"),
    ("swap meet", "交換会・スワップミート", "名詞", "Collectors traded duplicates at the monthly swap meet.", "コレクター", "600"),
    ("want list", "欲しい物リスト", "名詞", "Bring your want list so other collectors know what you're looking for.", "コレクター", "650"),
]

PHRASES: list[tuple[str, str]] = [
    ("What do you collect?", "何を集めているんですか？"),
    ("I mostly collect stamps from the early twentieth century.", "私は主に20世紀初頭の切手を集めています。"),
    ("How long have you been into numismatics?", "コイン収集(ヌミズマティクス)はどのくらい続けているんですか？"),
    ("I've been hunting for this one for years.", "何年もこれを探し続けています。"),
    ("Do you have any duplicates you'd trade?", "交換できる重複品はありますか？"),
    ("I'll add it to my want list.", "自分の欲しい物リストに加えておきます。"),
    ("Let's meet at the swap meet next month.", "来月のスワップミートで会いましょう。"),
    ("Mind if I take a closer look under the loupe?", "ルーペで詳しく見せてもらってもいいですか？"),
    ("This first edition still has its original dust jacket.", "この初版本には元のブックカバーがまだ付いています。"),
    ("The postmark dates it to well over a hundred years ago.", "消印から見ると100年以上前のものですね。"),
    ("I'd rather keep it ungraded for now.", "今のところ未鑑定のままにしておきたいです。"),
    ("Careful, the pages are quite fragile.", "気をつけて、ページがかなり傷みやすいので。"),
    ("I'll bring my whole collection to show you next time.", "次回はコレクション全部を持ってきてお見せしますね。"),
    ("This piece came from my grandfather's collection.", "この品は祖父のコレクションから受け継いだものです。"),
    ("It's a real find — I never expected to see one here.", "これは掘り出し物です。ここで見つかるとは思いませんでした。"),
    ("The binding is still tight, which is rare for its age.", "この年代の本にしては珍しく、綴じがまだしっかりしています。"),
    ("I keep my collection organized by year.", "コレクションは年代順に整理しています。"),
    ("Would you be open to an appraisal sometime?", "いつか鑑定してもらうのはどうですか？"),
    ("I trade mostly through the mail these days.", "最近は主に郵送でやり取りしています。"),
    ("That's a beautiful patina — I wouldn't clean it if I were you.", "きれいな経年変化ですね。私だったら磨きません。"),
    ("Let me check my binder for a duplicate.", "重複がないかバインダーを確認させてください。"),
    ("I'm trying to complete the whole set.", "セットを完成させようとしているんです。"),
    ("Do you specialize in any particular era?", "特定の時代を専門に集めていますか？"),
    ("I only display the pieces that are in the best shape.", "一番状態のいい品だけを飾っています。"),
    ("Feel free to handle it, just hold it by the edges.", "触っても大丈夫ですよ、縁を持ってくださいね。"),
    ("This one's not for sale, but I love showing it off.", "これは非売品ですが、見せびらかすのは大好きなんです。"),
    ("I picked this up at an estate sale last summer.", "これは去年の夏、遺品整理のセールで手に入れました。"),
    ("Are you looking to sell, trade, or just show?", "売りたいんですか、交換したいんですか、それともただ見せたいだけですか？"),
    ("I keep a spreadsheet of everything I own.", "持っている物は全部スプレッドシートで管理しています。"),
    ("Would you like to see the rest of my album?", "アルバムの残りも見てみますか？"),
    ("I inherited most of this from a family member.", "これのほとんどは家族から受け継いだものです。"),
    ("That's out of my price range, but it's gorgeous.", "それは予算オーバーですが、素晴らしいですね。"),
    ("I try to attend every collectors' meetup in the area.", "この地域のコレクター交流会にはできるだけ参加するようにしています。"),
]


def main() -> int:
    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing_words:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing_words.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")

    with db() as conn:
        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in existing_phrases:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, 'コレクションの英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
