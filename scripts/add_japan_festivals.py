# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Extend the existing "お祭り" domain/scene with a deeper dive into Japanese
festivals explained to foreign visitors, authored by Claude (2026-08-10・
ユーザー要望).

対象語彙: 花火(打ち上げ花火の演出用語: fireworks display, firework shell,
starmine, chrysanthemum shell, willow shell, hand-held fireworks, fireworks
finale, fireworks viewing spot ※既存の"fireworks festival"とは別に演出面を
深掘り)、夏祭り全般(summer festival, Obon, shrine festival, festival music)、
御柱祭(諏訪大社の巨木を曳く祭り: Onbashira Festival, sacred log, log-riding,
log-pulling)、ねぶた祭り(青森の灯篭山車祭り: Nebuta Matsuri, lantern float,
haneto, wire-and-paper frame)、祇園祭(京都: Gion Matsuri, yamaboko float,
float procession, Yoiyama)、その他知名度の高い祭り(Tanabata, Awa Odori,
Sapporo Snow Festival, Jidai Matsuri, Danjiri Matsuri, Tenjin Matsuri)、
祭り紹介の一般語彙(UNESCO Intangible Cultural Heritage, centuries-old
tradition, fire festival)。個別の祭りの固有名詞(Gion Matsuri, Nebuta
Matsuri, Onbashira Festival 等)は「外国人に祭りを説明する際に実際に使われる
英語表記」として扱う(日本文化紹介に不可欠なため、他スクリプトの実在の人物・
企業・商品名禁止ルールとは別枠)。既存18語(bon odori, carnival, confetti,
costume contest, county fair, festival float, fireworks festival, game
booth, goldfish scooping, harvest festival, kakigori, lantern festival,
masquerade ball, mikoshi, parade float, street fair, taiko drumming,
yatai)とは重複しない語のみを追加する。

フレーズは外国人観光客に祭りを説明する・誘う・案内する際に実際に使う自然な
口語表現("Have you ever been to a Japanese summer festival?" など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_japan_festivals.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 花火(打ち上げ花火の演出用語) ---
    ("fireworks display", "花火の打ち上げ・花火ショー", "名詞", "The fireworks display lasted for over an hour.", "お祭り", "400"),
    ("firework shell", "(打ち上げ)花火玉", "名詞", "Each firework shell explodes into a different pattern in the sky.", "お祭り", "650"),
    ("starmine", "スターマイン(連続で打ち上がる速射花火)", "名詞", "The show ended with a starmine that lit up the whole sky.", "お祭り", "750"),
    ("chrysanthemum shell", "菊咲き(尾を引かず丸く開く花火)", "名詞", "A chrysanthemum shell opens into a perfect round shape with trailing sparks.", "お祭り", "800"),
    ("willow shell", "柳咲き(尾を引いて垂れ下がる花火)", "名詞", "The willow shell's golden sparks drooped slowly toward the river.", "お祭り", "800"),
    ("hand-held fireworks", "手持ち花火", "名詞", "Kids love lighting hand-held fireworks in the yard after dinner.", "お祭り", "500"),
    ("fireworks finale", "花火大会のフィナーレ・大トリ", "名詞", "The fireworks finale packs dozens of shells into just a few minutes.", "お祭り", "550"),
    ("fireworks viewing spot", "花火の観覧スポット", "名詞", "We got to the fireworks viewing spot two hours early to claim a seat.", "お祭り", "500"),
    # --- 夏祭り全般 ---
    ("summer festival", "夏祭り", "名詞", "Have you ever been to a Japanese summer festival?", "お祭り", "350"),
    ("Obon", "お盆(先祖の霊を迎える夏の行事)", "名詞", "Many people travel back to their hometown during Obon.", "お祭り", "500"),
    ("shrine festival", "神社の祭礼", "名詞", "The shrine festival includes a parade through the neighborhood.", "お祭り", "500"),
    ("festival music", "祭り囃子", "名詞", "You can hear the festival music from several blocks away.", "お祭り", "600"),
    # --- 御柱祭(諏訪大社) ---
    ("Onbashira Festival", "御柱祭(諏訪大社の巨木を曳く祭り)", "名詞", "The Onbashira Festival is held once every six years in Nagano.", "お祭り", "700"),
    ("sacred log", "御柱(祭りで曳かれる巨大な木)", "名詞", "Volunteers spend months preparing the sacred logs for the festival.", "お祭り", "650"),
    ("log-riding", "木落とし(丸太に乗って坂を滑り降りる神事)", "名詞", "Log-riding down the steep hillside is considered the festival's most dangerous moment.", "お祭り", "800"),
    ("log-pulling", "巨木を曳くこと", "名詞", "The whole town gathers for the log-pulling that brings the sacred logs to the shrine.", "お祭り", "700"),
    # --- ねぶた祭り(青森) ---
    ("Nebuta Matsuri", "ねぶた祭り(青森の灯篭山車祭り)", "名詞", "Nebuta Matsuri is famous for its giant illuminated floats.", "お祭り", "700"),
    ("lantern float", "ねぶた(灯りをともした巨大な灯籠山車)", "名詞", "Each lantern float depicts a warrior or a mythical scene.", "お祭り", "650"),
    ("haneto", "ハネト(ねぶた祭りで跳ねながら踊る踊り手)", "名詞", "Anyone can join in as a haneto if they rent the costume.", "お祭り", "800"),
    ("wire-and-paper frame", "針金と和紙で作る灯籠の骨組み", "名詞", "Each lantern float starts as a wire-and-paper frame lit from within.", "お祭り", "800"),
    # --- 祇園祭(京都) ---
    ("Gion Matsuri", "祇園祭(京都)", "名詞", "Gion Matsuri lasts the entire month of July in Kyoto.", "お祭り", "700"),
    ("yamaboko float", "山鉾(祇園祭で巡行する豪華な山車)", "名詞", "The yamaboko floats are pulled through the streets of Kyoto by hand.", "お祭り", "800"),
    ("float procession", "山車の巡行", "名詞", "The float procession is the highlight of many Japanese festivals.", "お祭り", "650"),
    ("Yoiyama", "宵山(祇園祭前夜祭の夜)", "名詞", "During Yoiyama, the streets are lit with lanterns and food stalls open early.", "お祭り", "800"),
    # --- その他知名度の高い祭り ---
    ("Tanabata", "七夕(星まつり)", "名詞", "Tanabata celebrates a legend about two stars that meet once a year.", "お祭り", "400"),
    ("Awa Odori", "阿波おどり(徳島の盆踊り)", "名詞", "Awa Odori is a lively dance festival held in Tokushima every August.", "お祭り", "700"),
    ("Sapporo Snow Festival", "さっぽろ雪まつり", "名詞", "The Sapporo Snow Festival features huge snow and ice sculptures.", "お祭り", "500"),
    ("Jidai Matsuri", "時代祭(京都)", "名詞", "Jidai Matsuri features a costume parade spanning Kyoto's entire history.", "お祭り", "750"),
    ("Danjiri Matsuri", "だんじり祭(岸和田などで行われる勇壮な曳き祭り)", "名詞", "Danjiri Matsuri is known for teams pulling heavy wooden carts at full speed.", "お祭り", "800"),
    ("Tenjin Matsuri", "天神祭(大阪)", "名詞", "Tenjin Matsuri ends with a fireworks display over the river in Osaka.", "お祭り", "750"),
    # --- 祭り紹介の一般語彙 ---
    ("UNESCO Intangible Cultural Heritage", "ユネスコ無形文化遺産", "名詞", "Some of these festivals are registered as UNESCO Intangible Cultural Heritage.", "お祭り", "900"),
    ("centuries-old tradition", "何百年も続く伝統", "名詞", "This festival is a centuries-old tradition passed down through generations.", "お祭り", "700"),
    ("fire festival", "火祭り(火を使う祭りの総称)", "名詞", "Some regions hold a fire festival in autumn to mark the changing season.", "お祭り", "600"),
]

PHRASES: list[tuple[str, str]] = [
    ("Have you ever been to a Japanese summer festival?", "日本の夏祭りに行ったことはありますか？"),
    ("The best fireworks displays are set off over a river or the sea.", "一番美しい花火大会は川や海の上で打ち上げられます。"),
    ("Each firework shell explodes into a different shape.", "一つ一つの花火玉が違う形に開きます。"),
    ("That rapid-fire sequence is called a starmine.", "あの連続で打ち上がる花火はスターマインと呼ばれています。"),
    ("Kids love lighting hand-held fireworks in the yard.", "子どもたちは庭で手持ち花火に火をつけるのが大好きです。"),
    ("We should get to the fireworks viewing spot early to grab a good seat.", "いい場所を取るために花火の観覧スポットには早めに行った方がいいですね。"),
    ("The finale lights up the whole sky at once.", "フィナーレでは空全体が一気に光に包まれます。"),
    ("Many people wear a yukata to summer festivals.", "多くの人が夏祭りに浴衣を着て行きます。"),
    ("Obon is when Japanese families welcome their ancestors' spirits home.", "お盆は日本の家族が先祖の霊を家に迎える時期です。"),
    ("The shrine festival includes a parade through the neighborhood.", "神社の祭礼では地域を練り歩くパレードがあります。"),
    ("You can hear the festival music from blocks away.", "祭り囃子は何ブロックも先から聞こえてきます。"),
    ("Onbashira is one of Japan's most dangerous festivals.", "御柱祭は日本で最も危険な祭りの一つです。"),
    ("Men ride the sacred logs down a steep hill during the Onbashira Festival.", "御柱祭では男たちが急な斜面を巨木の丸太に乗って滑り降ります。"),
    ("Every six years, the town gathers to haul the sacred logs to the shrine.", "6年に一度、町の人々が神社まで御柱を曳くために集まります。"),
    ("Nebuta Matsuri is famous for its giant illuminated floats.", "ねぶた祭りは巨大な灯りのついた山車で有名です。"),
    ("Each lantern float is made of wire and washi paper.", "一つ一つのねぶたは針金と和紙で作られています。"),
    ("The dancers who jump alongside the floats are called haneto.", "山車の横で跳ねながら踊る踊り手はハネトと呼ばれます。"),
    ("Anyone can join in as a haneto if you rent the costume.", "衣装をレンタルすれば誰でもハネトとして参加できます。"),
    ("Gion Matsuri lasts the entire month of July in Kyoto.", "祇園祭は京都で7月まるまる1か月間続きます。"),
    ("The yamaboko floats are pulled through the streets of Kyoto.", "山鉾は京都の通りを曳かれて進みます。"),
    ("The float procession is the highlight of the festival.", "山車の巡行は祭りの最大の見どころです。"),
    ("The night before the procession is called Yoiyama, and the streets are lit with lanterns.", "巡行前夜は宵山と呼ばれ、通りが提灯で照らされます。"),
    ("Tanabata celebrates a legend about two stars that meet once a year.", "七夕は年に一度出会う二つの星の伝説を祝う行事です。"),
    ("People write their wishes on strips of paper for Tanabata.", "七夕には人々が短冊に願い事を書きます。"),
    ("Awa Odori is a lively dance festival held in Tokushima every August.", "阿波おどりは毎年8月に徳島で開かれる賑やかな踊りの祭りです。"),
    ("The Sapporo Snow Festival features huge snow and ice sculptures.", "さっぽろ雪まつりでは巨大な雪像や氷像が展示されます。"),
    ("Some of these festivals are registered as UNESCO Intangible Cultural Heritage.", "これらの祭りの中にはユネスコ無形文化遺産に登録されているものもあります。"),
    ("This festival has been held for centuries.", "この祭りは何百年も続いています。"),
    ("Would you like to come watch the parade with us?", "一緒にパレードを見に来ませんか？"),
    ("It gets really crowded, so let's meet early.", "かなり混むので早めに待ち合わせましょう。"),
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
                "VALUES (?, ?, 'お祭りの英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
