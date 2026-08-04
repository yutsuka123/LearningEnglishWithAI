# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for OVERSEAS AUCTION / COLLECTOR ENGLISH,
authored by Claude.

Focus (フレーズ集の手薄な領域を補強): トレーディングカード・アンティーク・
コイン/切手・フィギュア/おもちゃ・古書・ミリタリア(ミリタリー関連の収集品)
といった、時計・カメラ・オーディオ機器(scripts/add_gear_reviews.py で既出)
とは異なる収集ジャンルを対象に、海外オークション(eBay等)やコレクター向け
フォーラムで出品説明を読み書きし、安全に交渉するための英語を扱う。

状態・真贋まわりの語彙(mint condition, near mint, foxing, provenance,
hairline crack, restoration work, certificate of authenticity)、交渉・
取引フレーズ(オファーを打診する、価格が確定かどうか尋ねる、同梱発送を
交渉する、ノークレーム・ノーリターンの確認)、配送・輸入フレーズ
(保険付き発送、税関申告、輸入関税の可能性、梱包を丁寧にしてほしいと
依頼する)をカバーする。

【重要な制約】このバッチでは、真贋を「確実に見分ける方法」を教える
フレーズは一切含めない。本アプリは真贋鑑定スキルを教えるものではない
ため、すべてのフレーズは「出品者に真贋・状態を確認するための質問」
または「説明文中の注意すべき言い回しに気づく」という枠組みに留めて
いる(例: 「本物であることを確認していただけますか」「出品説明に来歴の
記載がなく、その点が気になります」)。「こうすれば偽物と見分けられる」
という断定的な鑑定手法は書いていない。この制約は上記の通り明示的に
遵守した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_collector_auctions.py
      python scripts/add_collector_auctions.py --missing-words   # report only

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
    "海外オークション・コレクター英語": [
        # --- 状態を表す語彙 ---
        ("The listing describes it as mint condition.", "出品説明には「ミント・コンディション(未使用に近い最良の状態)」とあります。"),
        ("It's graded near mint, with just a bit of shelf wear.", "「ニアミント(ほぼ完璧に近い状態)」評価で、わずかな保管による傷みがあるだけです。"),
        ("Could you describe the condition in more detail than the listing shows?", "出品説明に書かれている以上に、状態を詳しく教えていただけますか。"),
        ("Are there any flaws that aren't visible in the photos?", "写真では見えないキズや欠陥はありますか。"),
        ("There's some foxing on the pages, which is common for a book this old.", "ページにフォクシング(古い紙に出る茶色いシミ)が見られますが、この年代の本ではよくあることです。"),
        ("Could you take a close-up photo of the corners?", "角の部分を接写した写真をいただけますか。"),
        ("It has a hairline crack near the base — can you confirm it doesn't affect stability?", "台座付近に髪の毛ほどの細いヒビがありますが、安定性には影響しないか確認していただけますか。"),
        ("The edges show some wear, but the surface is otherwise clean.", "縁には多少の使用感がありますが、表面はそれ以外きれいです。"),
        ("Is there any restoration work on this piece?", "この品に修復作業は施されていますか。"),
        ("The listing mentions it's been re-touched — could you clarify what that involved?", "出品説明に「補修されている」とありますが、具体的にどのような作業か教えていただけますか。"),
        ("Has this been professionally cleaned or altered in any way?", "プロによるクリーニングや何らかの手を加えられたことはありますか。"),
        ("Could you show a photo under natural light rather than a flash?", "フラッシュではなく自然光で撮った写真を見せていただけますか。"),
        # --- 真贋・出所を尋ねる語彙(断定的な鑑定は行わない) ---
        ("Could you confirm this comes with a certificate of authenticity?", "これには真贋証明書が付属していることを確認していただけますか。"),
        ("Does the listing include any information about provenance?", "出品説明には来歴(所有・入手の経緯)についての情報が含まれていますか。"),
        ("The listing doesn't mention provenance, which concerns me a little.", "出品説明に来歴の記載がなく、その点が少し気になります。"),
        ("Is this the original part, or has it been replaced at some point?", "これはオリジナルの部品ですか、それとも過去に交換されたものですか。"),
        ("Could you tell me where and when you originally acquired this?", "いつ、どこでこれを入手されたか教えていただけますか。"),
        ("Do you have any paperwork or receipts from the original purchase?", "購入時の書類や領収書はお持ちですか。"),
        ("I noticed the listing doesn't say whether this is a reproduction — could you clarify?", "出品説明にこれが複製品かどうかの記載がないようですが、教えていただけますか。"),
        ("Buyer beware — the listing is vague about whether this part is original.", "この部品がオリジナルかどうか、出品説明があいまいなので注意が必要です。"),
        ("A listing with no close-up photos of the maker's mark makes me cautious.", "製造者の刻印の接写がない出品は、慎重になります。"),
        ("Could you confirm whether this is a period-correct piece or a later addition?", "これが年代の合ったオリジナルの部分か、後から加えられたものか確認していただけますか。"),
        ("I'd like a second opinion before bidding on something this valuable.", "これほど高価なものに入札する前に、第三者の意見も聞きたいです。"),
        ("Vague wording like 'as is, no guarantees' is worth reading carefully.", "「現状渡し、保証なし」といったあいまいな表現は注意深く読む価値があります。"),
        # --- 交渉・取引フレーズ ---
        ("Would you consider an offer of 80 dollars?", "80ドルでのオファーはご検討いただけますか。"),
        ("Is the price firm, or is there room to negotiate?", "価格は確定していますか、それとも交渉の余地はありますか。"),
        ("I'll take it if you can do combined shipping with my other order.", "他の注文と同梱発送していただけるなら、購入します。"),
        ("Would you be willing to bundle these two lots together?", "この2点をまとめて出品していただくことは可能ですか。"),
        ("This is a final sale, with no returns accepted.", "これは最終セールで、返品は受け付けていません。"),
        ("What's your best price if I buy more than one?", "複数購入する場合、一番安くしていただける価格はいくらですか。"),
        ("I'm interested, but only at a lower price point.", "興味はありますが、もう少し安くないと難しいです。"),
        ("Let's meet in the middle on the price.", "価格については折衷案で合意しましょう。"),
        ("I'll place a bid once I've confirmed the shipping cost.", "送料を確認してから入札します。"),
        ("The reserve price hasn't been met yet.", "最低落札価格(リザーブ)にまだ達していません。"),
        ("Bidding closes in about two hours.", "入札はあと約2時間で締め切られます。"),
        ("I was outbid at the last minute.", "土壇場で他の人に競り落とされてしまいました。"),
        ("Would you accept payment in installments?", "分割払いには対応していただけますか。"),
        ("Please don't relist this before giving me a chance to make an offer.", "私がオファーを出す機会をいただく前に再出品しないでください。"),
        ("I'm a returning buyer — do you offer any discount for repeat customers?", "リピーターの買い手なのですが、常連客向けの割引はありますか。"),
        ("Could you hold this item for me for 24 hours?", "この商品を24時間取り置きしていただけますか。"),
        # --- 出品・購入後のやり取り ---
        ("I'll leave positive feedback once the item arrives safely.", "商品が無事に届いたら良い評価を残します。"),
        ("Could you send me additional photos before I commit to buying?", "購入を決める前に追加の写真を送っていただけますか。"),
        ("I noticed the price dropped — is that a typo, or intentional?", "価格が下がったようですが、これは誤記でしょうか、それとも意図的なものですか。"),
        ("Please let me know if this item sells before I finalize payment.", "支払いを完了する前に売り切れた場合は教えてください。"),
        # --- 配送・輸入フレーズ ---
        ("Could you ship this with insured shipping?", "これを保険付きで発送していただけますか。"),
        ("Please pack it securely — it's fragile.", "壊れやすいので、しっかり梱包してください。"),
        ("Could you use extra padding around the corners?", "角の部分に追加の緩衝材を入れていただけますか。"),
        ("This may be subject to import duty when it arrives.", "到着時に輸入関税がかかる可能性があります。"),
        ("I'll need to fill out a customs declaration form for this shipment.", "この荷物については税関申告書に記入する必要があります。"),
        ("Could you mark the customs form as a gift to lower the declared value?", "税関申告書に贈答品と記載して申告額を下げていただけますか。"),
        ("I'd rather you declare the full value — I don't want any issues at customs.", "税関でトラブルにならないよう、正しい金額で申告していただきたいです。"),
        ("Does the shipping cost include tracking?", "送料には追跡サービスが含まれていますか。"),
        ("How long does international shipping usually take?", "国際発送には通常どのくらいかかりますか。"),
        ("Could you ship it in a rigid box rather than a padded envelope?", "クッション封筒ではなく、硬い箱で発送していただけますか。"),
        ("The package arrived damaged — could we discuss a partial refund?", "荷物が破損して届きました。一部返金についてご相談できますか。"),
        ("Please declare the item accurately on the customs form.", "税関申告書には商品を正確に記載してください。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("collectible", "収集品・コレクターズアイテム", "名詞", "This figure has become a sought-after collectible.", "コレクター", "700"),
    ("provenance", "来歴・所有履歴", "名詞", "The auction house asked for proof of provenance.", "コレクター", "900"),
    ("authentic", "本物の・真正の", "形容詞", "Could you confirm this is authentic?", "コレクター", "700"),
    ("counterfeit", "偽造品・模造品", "名詞", "Buyers should be cautious of counterfeit items in this category.", "コレクター", "800"),
    ("reproduction", "複製品・レプリカ", "名詞", "The listing doesn't say if it's a reproduction.", "コレクター", "800"),
    ("aftermarket", "純正部品ではない・社外の", "形容詞", "Is this an aftermarket part or the original one?", "コレクター", "800"),
    ("foxing", "フォクシング(古紙に出る茶色いシミ)", "名詞", "There's some foxing along the edges of the pages.", "コレクター", "900"),
    ("hairline crack", "髪の毛ほどの細いヒビ", "名詞", "It has a hairline crack near the base.", "コレクター", "900"),
    ("condition report", "状態説明書(出品物の状態をまとめた資料)", "名詞", "Could you send me the condition report before I bid?", "コレクター", "900"),
    ("appraisal", "鑑定・査定", "名詞", "I'd like to get an appraisal before I sell it.", "コレクター", "800"),
    ("militaria", "ミリタリア(軍事関連の収集品)", "名詞", "This dealer specializes in militaria from the era.", "コレクター", "900"),
    ("lot", "(オークションの)出品ロット", "名詞", "This lot includes three separate items.", "コレクター", "700"),
    ("reserve price", "最低落札価格", "名詞", "The reserve price hasn't been met yet.", "コレクター", "800"),
    ("outbid", "より高値を付けて競り落とす", "動詞", "I was outbid in the final seconds.", "コレクター", "800"),
    ("bundle", "まとめて売る・同梱する", "動詞", "Would you be willing to bundle these two items?", "コレクター", "700"),
    ("insured shipping", "保険付き発送", "名詞", "Could you ship this with insured shipping?", "コレクター", "700"),
    ("customs declaration", "税関申告(書)", "名詞", "I need to fill out a customs declaration for this package.", "コレクター", "800"),
    ("buyer's premium", "落札手数料(落札価格に上乗せされる手数料)", "名詞", "Remember the buyer's premium adds to the final price.", "コレクター", "900"),
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
