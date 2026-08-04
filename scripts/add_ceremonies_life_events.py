# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated vocabulary and phrases for 冠婚葬祭 (major life-ceremony
occasions: weddings, funerals/mourning, and other formal life-event
ceremonies), authored by Claude (2026-08-04・ユーザー要望: 「冠婚葬祭 英単語と、
フレーズ フレーズはスピーチ、哀悼の言葉、喪主挨拶など他も」).

DBを確認したところ、結婚式・お葬式・冠婚葬祭のフォーマルなスピーチに関する
語彙・フレーズは一切存在しなかった（既存の「恋愛」ドメインに engagement /
anniversary / honeymoon / newlyweds / fiancé(e) はあるが、結婚式そのものの
語彙や弔事の語彙は皆無）。そのため新しいドメイン '冠婚葬祭' を作成する。

【トーンについての方針】
弔事・お悔やみ関連の内容は、誠実さと敬意を最優先に扱う。特定の宗教の葬儀
儀礼を前提としない、キリスト教・無宗教・その他どの文化的背景の読者にも
通用する、温かく普遍的な言葉づかいを選んだ。日本の仏式葬儀の慣習
（焼香・戒名・香典など）は「宗教的な祈りの文言」としてではなく、あくまで
「文化的な事実の説明」として英語で描写している。下品・不謹慎・軽薄な
表現は一切含まない。結婚式関連の内容は、温かく祝福に満ちた、心からの
言葉を選んだ。

Covers:
  - WORDS in a new domain='冠婚葬祭' (~60 words): wedding vocabulary,
    funeral/mourning vocabulary (including Japanese Buddhist funeral customs
    explained descriptively in English), and other life-event/coming-of-age
    vocabulary.
  - PHRASES in scene='結婚式のスピーチ英語': giving a wedding toast/speech.
  - PHRASES in scene='お悔やみの言葉': expressing condolences in person or
    in writing.
  - PHRASES in scene='喪主挨拶・弔辞の英語': the chief mourner's greeting to
    guests at a funeral/wake, and eulogy-style language.

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased). Verified
against the live `words` and `phrases` tables before writing this file: zero
case-insensitive overlap.

Run:  python scripts/add_ceremonies_life_events.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "結婚式のスピーチ英語": [
        # --- スピーチの切り出し ---
        ("On behalf of everyone here, I'd like to say a few words.", "皆を代表して、一言お祝いの言葉を述べさせていただきます。"),
        ("I've known the groom since we were kids, and it's an honor to stand up here today.", "新郎とは子供の頃からの付き合いで、今日ここに立てることを光栄に思います。"),
        ("For those who don't know me, I'm the bride's older sister.", "私のことをご存じない方のために申し上げますと、私は新婦の姉です。"),
        ("Thank you all for being here to celebrate this special day with them.", "今日という特別な日をお二人と一緒に祝うため、皆様お集まりいただきありがとうございます。"),
        ("I've been asked to say a few words, and I couldn't be happier to do so.", "一言お話しするよう頼まれましたが、こんなに嬉しいことはありません。"),
        # --- 新郎新婦への祝福 ---
        ("To the happy couple!", "幸せなお二人に乾杯！"),
        ("Wishing you a lifetime of love and laughter.", "一生涯、愛と笑いに満ちた人生を。"),
        ("You two are perfect for each other.", "お二人は本当にお似合いです。"),
        ("I've never seen two people more in love.", "これほど愛し合っている二人を見たことがありません。"),
        ("May your love grow stronger with each passing year.", "年を重ねるごとに、お二人の愛がさらに深まりますように。"),
        ("Here's to a marriage filled with joy, laughter, and endless adventures.", "喜びと笑いと尽きない冒険に満ちた結婚生活に乾杯。"),
        ("You make such a wonderful team.", "お二人は本当に素晴らしいチームですね。"),
        # --- 乾杯・スピーチの締めくくり ---
        ("Please join me in raising a glass to the bride and groom.", "皆様、ご一緒にグラスを掲げて新郎新婦に乾杯しましょう。"),
        ("To the bride and groom!", "新郎新婦に乾杯！"),
        ("Please raise your glasses and join me in a toast.", "グラスを掲げて、乾杯にご唱和ください。"),
        ("Let's all raise a glass to the newlyweds.", "新婚のお二人に、皆で乾杯しましょう。"),
        ("Cheers to the bride and groom!", "新郎新婦に、乾杯！"),
        ("Congratulations again, and cheers to your new life together.", "改めておめでとうございます、そして新しい人生の門出に乾杯。"),
        # --- 一般的な結婚祝いの言葉 ---
        ("Congratulations on your special day.", "特別な日に、おめでとうございます。"),
        ("Wishing you both a lifetime of happiness.", "お二人の末永い幸せをお祈りしています。"),
        ("Best wishes to the both of you on your wedding day.", "ご結婚おめでとうございます、末永くお幸せに。"),
        ("What a beautiful ceremony that was.", "本当に美しい式でしたね。"),
        ("You looked absolutely stunning today.", "今日は本当に輝いていましたね。"),
        ("I'm so happy for you both.", "お二人のこと、本当に嬉しく思います。"),
        ("Congratulations, and thank you for letting us be part of your big day.", "おめでとうございます、そして大切な日に立ち会わせていただきありがとうございます。"),
    ],
    "お悔やみの言葉": [
        # --- 直接会って伝える言葉 ---
        ("I'm so sorry for your loss.", "このたびはご愁傷様です。"),
        ("Please accept my deepest condolences.", "心よりお悔やみ申し上げます。"),
        ("He will be deeply missed.", "彼のことは、これからも深く惜しまれることでしょう。"),
        ("She will be deeply missed by everyone who knew her.", "彼女を知る誰もが、深い喪失感を覚えることでしょう。"),
        ("My thoughts are with you and your family.", "あなたとご家族のことを、心から思っています。"),
        ("Is there anything I can do to help during this difficult time?", "この大変な時期に、私に何かできることはありますか。"),
        ("I'll always remember him fondly.", "彼のことは、いつまでも温かい思い出として覚えています。"),
        ("I'll always remember her fondly.", "彼女のことは、いつまでも温かい思い出として覚えています。"),
        ("Please let me know if you need anything.", "何か必要なことがあれば、どうぞ教えてください。"),
        ("Sending you strength during this difficult time.", "この大変な時期に、あなたに力が宿りますように。"),
        ("I'm here for you, whatever you need.", "必要な時は、いつでもそばにいます。"),
        ("Please don't hesitate to reach out if you need company.", "そばにいてほしい時は、遠慮なく声をかけてください。"),
        # --- お悔やみカード・手紙で伝える言葉 ---
        ("Words cannot express how sorry I am for your loss.", "言葉では言い表せないほど、このたびのことを残念に思っています。"),
        ("He was a wonderful person, and he will be truly missed.", "彼は本当に素晴らしい人でした、心から惜しまれます。"),
        ("She touched so many lives, and her memory will live on.", "彼女は多くの人の人生に影響を与え、その思い出はこれからも生き続けるでしょう。"),
        ("I was so saddened to hear of your loss.", "このたびのご不幸を伺い、深く心を痛めております。"),
        ("Please know that you're in my thoughts and prayers.", "あなたのことを、いつも心に留めています。"),
        ("May you find comfort in the memories you shared together.", "共に過ごした思い出の中に、少しでも安らぎが見つかりますように。"),
        ("Our deepest sympathy to you and your family.", "あなたとご家族に、心よりお悔やみ申し上げます。"),
        ("Our hearts go out to you and your family.", "あなたとご家族のことを、深く案じております。"),
        ("There are no words that can truly ease this loss, but please know we're thinking of you.", "この悲しみを和らげる言葉はありませんが、私たちがあなたのことを思っていることを知っていてください。"),
        ("He lived a full and meaningful life.", "彼は充実した、意義深い人生を送りました。"),
        ("She will forever hold a special place in our hearts.", "彼女はこれからもずっと、私たちの心の中で特別な存在であり続けます。"),
        ("We're keeping you in our hearts during this time.", "この時期、あなたのことをずっと心にかけています。"),
        ("I was deeply saddened to learn of his passing.", "彼が亡くなられたと伺い、深く悲しんでおります。"),
    ],
    "喪主挨拶・弔辞の英語": [
        # --- 喪主から参列者への挨拶 ---
        ("On behalf of my family, thank you all for coming today.", "家族を代表して、本日はお集まりいただき誠にありがとうございます。"),
        ("My father passed away peacefully on the morning of the tenth.", "父は10日の朝、安らかに息を引き取りました。"),
        ("My mother passed away peacefully, surrounded by her family.", "母は家族に見守られながら、安らかに息を引き取りました。"),
        ("We're deeply grateful for your support during this time.", "この時期に賜りましたご支援に、心より感謝申し上げます。"),
        ("Thank you all for your kind words and support over the past few days.", "ここ数日、皆様から温かいお言葉とご支援をいただき、ありがとうございました。"),
        ("Your presence here today means more to us than words can say.", "本日皆様にお越しいただけたこと、言葉に尽くせないほど感謝しております。"),
        ("On behalf of the family, I want to thank each and every one of you for being here.", "家族を代表して、本日お越しいただいた皆様お一人お一人に感謝申し上げます。"),
        ("I'll close by saying thank you, on behalf of my whole family, for the love you've shown us.", "最後になりますが、家族を代表して、皆様からいただいた温かいお心遣いに感謝申し上げます。"),
        ("We invite you to join us for a reception following the service.", "式の後にはお別れの会を予定しておりますので、ぜひご参加ください。"),
        ("Thank you for taking the time out of your busy lives to be here with us today.", "お忙しい中、本日はお時間を割いてお越しいただき、ありがとうございます。"),
        # --- 弔辞・故人を偲ぶ言葉 ---
        ("He touched so many lives.", "彼は本当に多くの人々の人生に、深い影響を与えました。"),
        ("She touched so many lives, and we're grateful to share her story with you today.", "彼女は多くの人々の人生に影響を与えました。今日、皆様にその思い出を語れることに感謝しています。"),
        ("Thank you for honoring his memory with us today.", "本日は彼の思い出を共に偲んでいただき、ありがとうございます。"),
        ("Thank you for honoring her memory with us today.", "本日は彼女の思い出を共に偲んでいただき、ありがとうございます。"),
        ("I'd like to share a few memories of my father.", "父についての思い出を、少しお話しさせていただきたいと思います。"),
        ("I'd like to share a few memories of my mother.", "母についての思い出を、少しお話しさせていただきたいと思います。"),
        ("We take great comfort in knowing how many lives he touched.", "彼がどれほど多くの人の人生に関わってきたかを知り、大きな慰めを感じています。"),
        ("It would have meant so much to him to see everyone gathered here today.", "今日こうして皆様が集まってくださったことを、彼はとても喜んだことでしょう。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 結婚関連語彙 ---
    ("officiant", "結婚式を執り行う人（司式者）", "名詞", "The officiant asked the couple to exchange rings.", "冠婚葬祭", "750"),
    ("best man", "新郎の付き添い役（男性の介添人代表）", "", "The best man gave a heartfelt toast at the reception.", "冠婚葬祭", "550"),
    ("maid of honor", "新婦の付き添い役（介添人代表）", "", "The maid of honor helped the bride get ready before the ceremony.", "冠婚葬祭", "600"),
    ("bridal party", "新郎新婦の付き添い一同", "", "The whole bridal party lined up for photos before the ceremony.", "冠婚葬祭", "650"),
    ("wedding vows", "結婚の誓いの言葉", "", "They wrote their own wedding vows instead of using the traditional ones.", "冠婚葬祭", "600"),
    ("wedding reception", "結婚式の披露宴", "", "The wedding reception was held in a garden overlooking the sea.", "冠婚葬祭", "550"),
    ("wedding toast", "結婚式での祝辞・乾杯の挨拶", "", "The bride's sister gave a moving wedding toast.", "冠婚葬祭", "600"),
    ("first dance", "新郎新婦最初のダンス", "", "The couple's first dance was to their favorite song.", "冠婚葬祭", "550"),
    ("bouquet", "ブーケ（花束）", "名詞", "The bride tossed her bouquet to the crowd of guests.", "冠婚葬祭", "500"),
    ("wedding registry", "結婚祝いの欲しい物リスト", "", "They set up a wedding registry at a home goods store.", "冠婚葬祭", "650"),
    ("rehearsal dinner", "結婚式前夜のリハーサルディナー", "", "Close family and friends gathered for the rehearsal dinner the night before.", "冠婚葬祭", "700"),
    ("save-the-date", "結婚式の日取りを知らせる事前案内状", "", "We mailed out the save-the-dates six months before the wedding.", "冠婚葬祭", "650"),
    ("RSVP", "出欠のご返信（をお願いします）", "", "Please RSVP by the end of the month so we can finalize the seating.", "冠婚葬祭", "500"),
    ("plus-one", "同伴者一名", "名詞", "Each guest was invited to bring a plus-one.", "冠婚葬祭", "550"),
    ("seating chart", "席次表", "", "The seating chart took hours to finalize.", "冠婚葬祭", "650"),
    ("wedding favor", "引き出物・プチギフト", "", "Each table had small jars of honey as a wedding favor.", "冠婚葬祭", "650"),
    ("marriage proposal", "結婚の申し込み・プロポーズ", "", "His marriage proposal took place at the same restaurant where they had their first date.", "冠婚葬祭", "550"),
    ("prenup", "婚前契約（書）", "名詞", "They decided to sign a prenup before the wedding.", "冠婚葬祭", "700"),
    ("groom", "新郎", "名詞", "The groom couldn't stop smiling as the bride walked down the aisle.", "冠婚葬祭", "400"),
    ("bride", "新婦", "名詞", "The bride wore her grandmother's wedding dress.", "冠婚葬祭", "400"),
    ("bridesmaid", "新婦の付き添い人（女性）", "名詞", "She asked her three closest friends to be her bridesmaids.", "冠婚葬祭", "500"),
    ("groomsman", "新郎の付き添い人（男性）", "名詞", "Each groomsman wore a matching navy suit.", "冠婚葬祭", "550"),
    ("wedding anniversary", "結婚記念日", "", "They celebrated their tenth wedding anniversary with a trip to Italy.", "冠婚葬祭", "500"),
    # --- 葬儀・弔い関連語彙 ---
    ("funeral home", "葬儀場", "", "The funeral home helped the family arrange every detail of the service.", "冠婚葬祭", "550"),
    ("wake", "通夜", "名詞", "Friends and family gathered for the wake the evening before the funeral.", "冠婚葬祭", "500"),
    ("visitation", "弔問（遺族への面会・お悔やみの訪問）", "名詞", "Visitation hours were held at the funeral home the day before the service.", "冠婚葬祭", "700"),
    ("eulogy", "弔辞", "名詞", "His closest friend delivered a heartfelt eulogy at the memorial service.", "冠婚葬祭", "800"),
    ("pallbearer", "棺を担ぐ人", "名詞", "Six of his grandsons served as pallbearers.", "冠婚葬祭", "750"),
    ("chief mourner", "喪主", "", "As the chief mourner, she thanked every guest personally after the service.", "冠婚葬祭", "800"),
    ("condolences", "お悔やみの言葉", "名詞", "Colleagues from across the company sent their condolences.", "冠婚葬祭", "650"),
    ("sympathy card", "お悔やみカード", "", "She wrote a short, heartfelt message inside the sympathy card.", "冠婚葬祭", "600"),
    ("obituary", "死亡記事・お悔やみ欄", "名詞", "The obituary described him as a devoted father and a lifelong volunteer.", "冠婚葬祭", "700"),
    ("memorial service", "追悼式", "", "The memorial service was held a few weeks after the funeral so relatives from abroad could attend.", "冠婚葬祭", "650"),
    ("urn", "骨壺", "名詞", "The urn was placed on a small table surrounded by photographs.", "冠婚葬祭", "650"),
    ("burial", "埋葬", "名詞", "The burial took place at a quiet cemetery just outside the city.", "冠婚葬祭", "600"),
    ("cremation", "火葬", "名詞", "The family chose cremation, as he had requested.", "冠婚葬祭", "700"),
    ("headstone", "墓石", "名詞", "They chose a simple headstone engraved with his favorite quote.", "冠婚葬祭", "650"),
    ("moment of silence", "黙祷", "", "The whole room observed a moment of silence in his memory.", "冠婚葬祭", "600"),
    ("bereaved family", "遺族", "", "The community organized meals for the bereaved family during the first week.", "冠婚葬祭", "800"),
    ("mourning period", "喪に服す期間", "", "In many cultures, the mourning period lasts about a year.", "冠婚葬祭", "750"),
    ("incense offering", "焼香（日本の仏式葬儀で香を焚いて故人を弔う慣習）", "", "Guests took turns making an incense offering in front of the altar.", "冠婚葬祭", "800"),
    ("posthumous Buddhist name", "戒名（かいみょう。日本の仏式葬儀で故人に授けられる新しい名前）", "", "The monk chose a posthumous Buddhist name for her grandfather during the ceremony.", "冠婚葬祭", "900"),
    ("koden", "香典（日本で弔問の際に遺族へ渡す金銭の贈り物）", "名詞", "Guests brought koden in a special envelope to the wake.", "冠婚葬祭", "850"),
    ("condolence gift", "お悔やみの品・弔慰の贈り物", "", "They sent a condolence gift of fruit and flowers to the family.", "冠婚葬祭", "700"),
    ("send flowers", "（弔事で）花を贈る", "", "We decided to send flowers to the family instead of attending in person.", "冠婚葬祭", "550"),
    ("mourn", "喪に服す・（人の死を）悼む", "動詞", "The whole town mourned the loss of their longtime mayor.", "冠婚葬祭", "700"),
    ("grieve", "深く悲しむ", "動詞", "It's important to give yourself time to grieve.", "冠婚葬祭", "650"),
    ("deceased", "故人（の）", "名詞", "The deceased's family thanked everyone for their kindness.", "冠婚葬祭", "700"),
    ("widow", "未亡人", "名詞", "She has been a widow for three years now.", "冠婚葬祭", "550"),
    ("widower", "やもめ（男性）", "名詞", "He became a widower shortly after retiring.", "冠婚葬祭", "600"),
    ("wreath", "（葬儀用の）花輪", "名詞", "A large wreath stood beside the entrance to the chapel.", "冠婚葬祭", "550"),
    ("hearse", "霊柩車", "名詞", "The hearse led the procession slowly through town.", "冠婚葬祭", "700"),
    ("funeral procession", "葬列", "", "Neighbors stopped and bowed their heads as the funeral procession passed.", "冠婚葬祭", "700"),
    # --- その他の人生の節目・儀式 ---
    ("coming-of-age ceremony", "成人式", "", "Every January, young adults across Japan attend a coming-of-age ceremony.", "冠婚葬祭", "750"),
    ("milestone birthday", "節目の誕生日（還暦や米寿など）", "", "Her family threw a big party for her milestone birthday.", "冠婚葬祭", "600"),
    ("christening", "幼児洗礼式・命名の儀式", "名詞", "The baby's christening was held at a small church near her grandparents' house.", "冠婚葬祭", "700"),
    ("naming ceremony", "命名式", "", "They held a small naming ceremony a month after the baby was born.", "冠婚葬祭", "650"),
    ("graduation ceremony", "卒業式", "", "Families gathered on the lawn for the graduation ceremony.", "冠婚葬祭", "550"),
    ("retirement party", "退職祝いのパーティー", "", "His coworkers threw him a retirement party after thirty years at the company.", "冠婚葬祭", "550"),
    ("death anniversary", "命日・祥月命日（故人を偲ぶ記念日）", "", "The family visits the grave every year on his death anniversary.", "冠婚葬祭", "750"),
]


# --- insertion --------------------------------------------------------------

def main() -> int:
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
