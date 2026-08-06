# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add OMAKASE / SUSHI-COUNTER vocabulary and phrases, authored by Claude
(2026-08-04・ユーザー要望: 「フレーズ 英単語 和食など 時価でとか おまかせでとか
今日のおすすめ いい**入っているなど」「わさびぬきでお願いします
わさびいれてもいいですかなど」).

既存の scene='和食'(22件)は刺身・寿司・味噌汁・納豆・麺の
すすり方・箸のマナー・うどんとそばの違い・和牛・懐石・居酒屋・とんかつ・
日本酒ペアリングなど、和食文化を英語で「説明する」フレーズが中心だった。
このスクリプトはそこに、和食店・寿司店のホスト/スタッフが英語圏の
ゲストに対して使う、より実務寄りの語彙とフレーズを追加する:

- おまかせ(omakase)の説明 — シェフにお任せするスタイルであること
- 時価(market price)の説明 — 仕入れによって毎日価格が変わること
- 「今日はいいマグロが入っています」のような、本日のおすすめ・入荷の
  案内
- 寿司のカスタマイズ — 「わさび抜きで」「わさびを自分で入れてもいい？」
  など、わさびに関するやり取り
- 江戸前寿司・板前・大トロ/赤身・ガリなど、寿司カウンター特有の語彙

words の domain は '料理' に統一(既存の和食語彙と同じ domain)。
phrases の scene は既存の '和食' を継続利用(拡張)する。
level は ["300-","300","350","400","450","500","550","600","650","700",
"750","800","850","900","950","990","990+"] のスケールに沿って付与して
おり、一般的な語(sushi chef, sushi counter, catch of the dayなど)は
500〜650、江戸前・板前・大トロ/赤身のような専門的な寿司用語は
750〜900とした。

事前に既存DB(words ~7000件, phrases ~4200件)を全件チェックし、
sushi / sashimi / wasabi / soy sauce / pickled ginger / nigiri / unagi /
tasting menu / seasonal ingredients / counter seat / etiquette などが
既に存在することを確認済み。それらと重複する語(pickled ginger, gari,
nigiri, wasabi, tasting menu 等)はこのリストから除外している。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_omakase_sushi.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("omakase", "おまかせ(シェフに料理選びを一任するコース)", "名詞", "This restaurant only offers an omakase menu.", "料理", "650"),
    ("market price", "時価", "名詞", "The uni was priced at market price today.", "料理", "650"),
    ("chef's recommendation", "シェフのおすすめ", "名詞", "The chef's recommendation today is the bluefin toro.", "料理", "600"),
    ("catch of the day", "本日の水揚げ・今日獲れたもの", "名詞", "Ask your server about the catch of the day.", "料理", "550"),
    ("in-season fish", "旬の魚", "名詞", "In-season fish tastes best and often costs less.", "料理", "600"),
    ("edomae-style sushi", "江戸前寿司", "名詞", "Edomae-style sushi originated in Tokyo and often cures the fish before serving.", "料理", "850"),
    ("sushi counter", "寿司カウンター", "名詞", "We sat right at the sushi counter and watched the chef work.", "料理", "550"),
    ("sushi chef", "寿司職人", "名詞", "The sushi chef trained for over ten years before opening his own shop.", "料理", "500"),
    ("itamae", "板前(特に寿司職人を指すことが多い)", "名詞", "An itamae spends years mastering how to slice fish properly.", "料理", "850"),
    ("conveyor belt sushi", "回転寿司", "名詞", "Conveyor belt sushi is a cheap and casual way to enjoy a variety of dishes.", "料理", "500"),
    ("kaiten-zushi", "回転寿司(日本語そのままの呼び方)", "名詞", "Kaiten-zushi restaurants let you grab plates straight off the belt.", "料理", "700"),
    ("high-end sushi restaurant", "高級寿司店", "名詞", "A seat at a high-end sushi restaurant can cost tens of thousands of yen.", "料理", "600"),
    ("sushi etiquette", "寿司の食べ方の作法", "名詞", "Part of sushi etiquette is eating each piece in a single bite.", "料理", "650"),
    ("soy sauce dish", "醤油皿", "名詞", "Pour just a little soy sauce into the small dish.", "料理", "450"),
    ("freshly caught", "獲れたての", "形容詞", "This mackerel was freshly caught this morning.", "料理", "500"),
    ("wholesale fish market", "卸売魚市場", "名詞", "Many top sushi chefs buy their fish at the wholesale fish market before dawn.", "料理", "700"),
    ("prime cut", "極上の部位", "名詞", "This is a prime cut from the tuna's belly.", "料理", "700"),
    ("seasonal catch", "旬の漁獲", "名詞", "The seasonal catch changes throughout the year.", "料理", "650"),
    ("aged fish", "熟成させた魚", "名詞", "Some sushi chefs age fish for several days to deepen its flavor.", "料理", "800"),
    ("fatty tuna", "トロ(脂ののったマグロ)", "名詞", "Fatty tuna is the most prized part of the fish.", "料理", "600"),
    ("otoro", "大トロ", "名詞", "Otoro comes from the fattiest part of the tuna belly.", "料理", "850"),
    ("lean tuna", "赤身(脂の少ないマグロ)", "名詞", "Lean tuna has a lighter flavor than the fatty cuts.", "料理", "600"),
    ("akami", "赤身", "名詞", "Akami is the deep red, lean meat from the tuna's back.", "料理", "800"),
]

PHRASES: list[tuple[str, str]] = [
    ("This restaurant is omakase-only, meaning the chef decides what you'll eat.", "この店はおまかせのみで、シェフが何を出すか決めます。"),
    ("Just leave it to the chef — that's what omakase means.", "シェフにお任せください。それが「おまかせ」の意味です。"),
    ("Omakase usually costs more, but you get the freshest seasonal picks.", "おまかせは大抵値段が高くなりますが、その分一番旬で新鮮なものが食べられます。"),
    ("You won't see prices on an omakase menu — you just trust the chef.", "おまかせメニューには値段が書かれていません。シェフを信頼するだけです。"),
    ("This is priced at market rate, since the cost changes daily.", "これは時価です。仕入れの値段が毎日変わるためです。"),
    ("The price depends on today's catch, so I can't give you an exact number in advance.", "値段はその日の入荷次第なので、事前に正確な金額はお伝えできません。"),
    ("Market price items are usually the most prized cuts of the day.", "時価の商品は大抵その日一番の希少な部位です。"),
    ("We got some really good tuna in today.", "今日は本当に良いマグロが入っていますよ。"),
    ("The chef just got a great catch in this morning.", "シェフが今朝、素晴らしい入荷を受け取ったところです。"),
    ("I'd recommend today's special — it's the freshest thing we have.", "本日のおすすめをお勧めします。うちで一番新鮮なものです。"),
    ("What would you recommend today?", "今日は何がおすすめですか？"),
    ("What's fresh today?", "今日新鮮なものは何ですか？"),
    ("The uni came in fresh from Hokkaido this morning.", "今朝、北海道から新鮮なウニが入ってきました。"),
    ("Everything on the counter today was caught within the last day or two.", "今日カウンターに並んでいるものは、すべてここ1、2日で獲れたものです。"),
    ("No wasabi, please.", "わさび抜きでお願いします。"),
    ("Could you leave the wasabi out?", "わさびを入れないでいただけますか？"),
    ("Is it okay if I put wasabi in myself?", "自分でわさびを入れてもいいですか？"),
    ("Could you go easy on the wasabi?", "わさびを控えめにしていただけますか？"),
    ("I like it with extra wasabi.", "わさびは多めが好きです。"),
    ("Do you eat sushi with your hands or chopsticks?", "寿司は手で食べますか、それとも箸で食べますか？"),
    ("Should I dip the fish side or the rice side in soy sauce?", "醤油につけるのはネタ側ですか、それともシャリ側ですか？"),
    ("At a sushi counter, it's best to eat each piece in one bite.", "寿司カウンターでは、一貫を一口で食べるのが良いとされています。"),
    ("The pickled ginger is meant to cleanse your palate between pieces.", "ガリ(甘酢生姜)は、一貫ごとに口の中をリセットするためのものです。"),
    ("Otoro is the fattiest part of the tuna belly, and it melts in your mouth.", "大トロはマグロの腹の一番脂がのった部分で、口の中でとろけます。"),
    ("Akami has a leaner, more classic tuna flavor.", "赤身はより脂が少なく、昔ながらのマグロの味わいがあります。"),
    ("An itamae trains for years before being allowed to serve customers directly.", "板前はお客様に直接提供できるようになるまで、何年も修行を積みます。"),
    ("It's considered polite to eat sushi as soon as it's placed in front of you.", "寿司は出されたらすぐに食べるのが礼儀とされています。"),
    ("There's no need to add extra soy sauce — the chef has already seasoned it.", "追加で醤油をつける必要はありません。シェフがすでに味付けしています。"),
]


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
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

        p_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in p_existing:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '和食')",
                (en, ja),
            )
            p_existing.add(en.lower())
            p_added += 1

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
