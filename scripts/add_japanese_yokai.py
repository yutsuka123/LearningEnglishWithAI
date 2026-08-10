# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Expand domain='生物(想像上)' with Japanese folklore creatures/yokai,
authored by Claude (2026-08-10・ユーザー要望).

既存の domain='生物(想像上)' には dragon, phoenix, unicorn, kraken, elf,
fairy など**西洋の空想上の生物のみ**30語が入っており、日本古来の妖怪・
霊獣は一切無かった(2026-08-10確認)。本スクリプトはそのギャップを埋め、
外国人に日本の妖怪・伝承上の生物を英語で説明できる語彙を追加する。

対象語彙: 鳳凰(Ho-o)、麒麟(Kirin)、龍神(Ryujin)、天狗(Tengu)、河童(Kappa)、
狐の霊的存在(Kitsune)、九尾の狐(nine-tailed fox)、狸の妖怪(Tanuki)、
雪女(Yuki-onna)、座敷わらし(Zashiki-warashi)、鵺(Nue)、
八岐大蛇(Yamata no Orochi)、土蜘蛛(Tsuchigumo)、絡新婦(Jorogumo)、
猫又(Nekomata)、化け猫(Bakeneko)、ろくろ首(Rokurokubi)、件(Kudan)、
アマビエ(Amabie)、つちのこ(Tsuchinoko)、鬼(Oni)、妖怪の総称(Yokai)、
海坊主(Umibozu)、ぬらりひょん(Nurarihyon)、鬼火(Onibi)、貉(Mujina)、
一反木綿(Ittan-momen)、変化する者(Shapeshifter)。

"dragon" "phoenix" など既存の西洋語と見出し語(english)が一致するとdedup
でスキップされる仕様のため、Ho-o(鳳凰)・Ryujin(龍神)のように和の呼称や
神格名を見出しに使い、生物学的分類ではなく文化紹介に必要な一般名詞的な
ローマ字表記とした(既存DBの shogun / ronin / gyudon 等と同様、長音は
マクロンを使わず簡略化した表記に統一)。

level は既存の生物(想像上)語彙(400〜800)と同じスケールに合わせ、河童・
天狗・鬼など日本人以外にも比較的知られている語は450〜550、土蜘蛛・件・
ぬらりひょんなど専門的・稀な語は750〜850とした。

phrasesは新規scene「妖怪・日本の伝承の英語」を作成し、外国人に日本の
妖怪・伝承を紹介する場面で使う自然な英語表現＋正確な日本語訳を収録した。

No app / OpenAI API calls — everything is hand-written and inserted
directly into the SQLite DB. Duplicates are skipped by english
(lowercased).

Run:  python scripts/add_japanese_yokai.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- よく知られた妖怪・霊獣 ---
    ("Kappa", "河童(川や池に住むとされる緑色の妖怪)", "名詞", "Kappa are said to live in rivers and ponds and love cucumbers.", "生物(想像上)", "450"),
    ("Oni", "鬼(角と牙を持つ日本の鬼・悪魔)", "名詞", "An oni is usually depicted with horns, sharp fangs, and colorful skin.", "生物(想像上)", "450"),
    ("Tengu", "天狗(山に住むとされる赤い顔と長い鼻を持つ妖怪)", "名詞", "Tengu are often depicted with red faces and long noses in Japanese art.", "生物(想像上)", "500"),
    ("Kitsune", "狐(人を化かす霊力を持つとされる狐の霊的存在)", "名詞", "In folktales, a kitsune can transform into a beautiful woman to trick travelers.", "生物(想像上)", "500"),
    ("Tanuki", "狸(人を化かすとされるタヌキの妖怪)", "名詞", "Statues of a tanuki are often placed outside restaurants for good luck.", "生物(想像上)", "500"),
    ("Yokai", "妖怪(日本の伝承に登場する超自然的な存在の総称)", "名詞", "Yokai is a general term for supernatural creatures in Japanese folklore.", "生物(想像上)", "500"),
    ("nine-tailed fox", "九尾の狐", "名詞", "The nine-tailed fox is a powerful and cunning spirit found in East Asian folklore.", "生物(想像上)", "550"),
    ("Shapeshifter", "変化(へんげ)する者・化け物", "名詞", "Many yokai, such as the fox and the tanuki, are known as shapeshifters.", "生物(想像上)", "550"),
    ("Yuki-onna", "雪女(雪山や吹雪に現れるとされる女性の妖怪)", "名詞", "Yuki-onna is said to appear during snowstorms and lure travelers to their doom.", "生物(想像上)", "600"),
    ("Ho-o", "鳳凰(想像上の霊鳥、日本の\"不死鳥\")", "名詞", "The Ho-o is sometimes called the Japanese phoenix and appears on many kimono designs.", "生物(想像上)", "600"),
    ("Kirin", "麒麟(首の長い伝説の霊獣、平和の象徴とされる)", "名詞", "The Kirin is a legendary creature said to appear only in times of peace and prosperity.", "生物(想像上)", "650"),
    ("Amabie", "アマビエ(疫病の流行を予言し身を守るとされる妖怪)", "名詞", "Images of Amabie became popular online as a symbol of protection during epidemics.", "生物(想像上)", "700"),
    ("Tsuchinoko", "ツチノコ(太い胴体を持つとされる伝説の蛇)", "名詞", "The tsuchinoko is a legendary snake-like creature that some people claim to have seen.", "生物(想像上)", "700"),
    ("Ryujin", "龍神(海を治めるとされる龍の神)", "名詞", "Ryujin is the dragon god believed to rule over the sea in Japanese mythology.", "生物(想像上)", "700"),
    # --- やや専門的な妖怪 ---
    ("Yamata no Orochi", "八岐大蛇(八つの頭と尾を持つ巨大な大蛇)", "名詞", "Yamata no Orochi is a giant eight-headed serpent from Japanese mythology.", "生物(想像上)", "750"),
    ("Zashiki-warashi", "座敷わらし(家に住み着き幸運をもたらすとされる子供の霊)", "名詞", "A zashiki-warashi is a child spirit believed to bring good fortune to the house it lives in.", "生物(想像上)", "750"),
    ("Nekomata", "猫又(年を経て尾が二股に分かれ化けるとされる猫)", "名詞", "According to legend, a cat can become a nekomata after living for many years.", "生物(想像上)", "750"),
    ("Onibi", "鬼火(夜に浮遊するとされる怪しい炎)", "名詞", "Onibi are eerie floating lights said to appear near graveyards at night.", "生物(想像上)", "750"),
    ("Nue", "鵺(猿の顔・狸の胴体・虎の脚・蛇の尾を持つ合成獣)", "名詞", "The Nue is a chimera-like creature with the head of a monkey and the body of a raccoon dog.", "生物(想像上)", "800"),
    ("Tsuchigumo", "土蜘蛛(人を襲うとされる巨大な蜘蛛の妖怪)", "名詞", "Tsuchigumo were depicted as giant spider-like creatures that ambushed travelers.", "生物(想像上)", "800"),
    ("Bakeneko", "化け猫(人語を話し人を化かすとされる猫の妖怪)", "名詞", "A bakeneko is said to gain supernatural powers and even speak human language.", "生物(想像上)", "800"),
    ("Rokurokubi", "ろくろ首(首が長く伸びるとされる妖怪)", "名詞", "A rokurokubi looks human by day but can stretch its neck at night.", "生物(想像上)", "800"),
    ("Umibozu", "海坊主(船を沈めるとされる海の妖怪)", "名詞", "An umibozu is said to rise from the sea and capsize ships during storms.", "生物(想像上)", "800"),
    ("Mujina", "貉(人を化かすとされるアナグマやタヌキ類の妖怪)", "名詞", "A mujina is a shape-shifting creature similar to a badger in old Japanese tales.", "生物(想像上)", "800"),
    # --- 特に専門的・稀な妖怪 ---
    ("Jorogumo", "絡新婦(美女に化けるとされる蜘蛛の妖怪)", "名詞", "A jorogumo is said to disguise itself as a beautiful woman to lure victims.", "生物(想像上)", "850"),
    ("Kudan", "件(人面牛身で予言をするとされる妖怪)", "名詞", "A kudan has the body of a cow and the face of a human, and is said to predict the future.", "生物(想像上)", "850"),
    ("Nurarihyon", "ぬらりひょん(妖怪たちの頭領とされる存在)", "名詞", "Nurarihyon is often described as the leader of all the yokai.", "生物(想像上)", "850"),
    ("Ittan-momen", "一反木綿(夜に飛び人を襲うとされる布の妖怪)", "名詞", "Ittan-momen is a long strip of cloth that is said to fly through the night sky.", "生物(想像上)", "850"),
]

PHRASES: list[tuple[str, str]] = [
    ("Would you like to hear a story about Japanese monsters?", "日本の妖怪についての話を聞きたいですか？"),
    ("Yokai is a Japanese word for supernatural creatures and spirits.", "妖怪とは、超自然的な生き物や霊を指す日本語です。"),
    ("Japanese folklore has hundreds of different yokai, each with its own story.", "日本の伝承には何百もの妖怪がおり、それぞれに固有の物語があります。"),
    ("Kappa are said to live in rivers and ponds.", "河童は川や池に住むと言われています。"),
    ("Have you heard of the nine-tailed fox in Japanese folklore?", "日本の伝承に出てくる九尾の狐について聞いたことがありますか？"),
    ("Tengu are usually pictured with a long red nose.", "天狗は通常、長い赤い鼻を持つ姿で描かれます。"),
    ("Kitsune are believed to be able to shape-shift into humans.", "狐は人間に化けることができると信じられています。"),
    ("Legend says a tanuki can disguise itself as a teapot.", "伝説によれば、狸は茶釜に化けることができるそうです。"),
    ("Yuki-onna appears in snowstorms in many old stories.", "雪女は多くの古い物語で吹雪の中に現れます。"),
    ("A zashiki-warashi is said to bring good luck to a household.", "座敷わらしは家に幸運をもたらすと言われています。"),
    ("The Ho-o is sometimes called the Japanese phoenix.", "鳳凰は「日本のフェニックス」と呼ばれることもあります。"),
    ("The Kirin is a symbol of peace and good fortune.", "麒麟は平和と幸運の象徴です。"),
    ("Ryujin is believed to control the tides of the sea.", "龍神は海の潮の満ち引きを司ると信じられています。"),
    ("Yamata no Orochi was an eight-headed serpent defeated by a god.", "八岐大蛇は神によって退治された八つの頭を持つ大蛇でした。"),
    ("Oni are often shown carrying a big iron club.", "鬼はよく大きな鉄の棍棒を持った姿で描かれます。"),
    ("Amabie became famous online as a symbol against disease.", "アマビエは病を防ぐ象徴としてネット上で有名になりました。"),
    ("Some people in rural Japan claim to have seen a tsuchinoko.", "日本の田舎では、ツチノコを見たと主張する人もいます。"),
    ("In folklore, a cat that lives too long can become a nekomata.", "伝承では、長生きしすぎた猫は猫又になるとされています。"),
    ("Umibozu are said to appear on calm nights and sink ships.", "海坊主は静かな夜に現れ、船を沈めると言われています。"),
    ("That old house is said to be haunted by a rokurokubi.", "あの古い家にはろくろ首が出ると言われています。"),
    ("Many yokai stories were originally told to teach children a lesson.", "多くの妖怪の物語は、もともと子供に教訓を教えるために語られました。"),
    ("This picture scroll shows the night parade of a hundred demons.", "この絵巻物には百鬼夜行が描かれています。"),
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
                "VALUES (?, ?, '妖怪・日本の伝承の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
