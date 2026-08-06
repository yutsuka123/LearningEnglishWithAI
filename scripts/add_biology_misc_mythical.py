# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Add two new biology-related domains, authored by Claude (2026-08-06).

既存の生物語彙は主に「動物」「植物」のdomainに分類されていたが、
そのどちらにも収まらない語がある:

- domain='生物(その他)': ウイルス・細菌・菌類・原生生物など、動物学的にも
  植物学的にも分類しづらい生物学上の語(virus, bacteria, fungus, mold,
  yeast, protozoa, mushroom, lichen, algae, microbe, pathogen, spore,
  mycelium など)。理科・医療系のTOEIC語彙として有用。
- domain='生物(想像上)': ドラゴン・ユニコーン・フェニックス・人魚など、
  世界の神話・伝承・ファンタジー創作に一般的に登場する架空の生物種
  (dragon, unicorn, phoenix, mermaid, griffin, kraken, werewolf,
  vampire, centaur, pegasus, chimera, basilisk, sphinx, yeti, troll,
  goblin, fairy, elf, banshee など)。特定の版権作品専用のキャラクター
  ではなく、一般名詞として辞書に載る空想上の生物のみを対象とした。

いずれも words のみを追加する(phrasesの追加は不要)。level は
["300-","300","350","400","450","500","550","600","650","700","750",
"800","850","900","950","990","990+"] のスケールに沿って付与しており、
日常的によく使われる語(virus, dragon, mermaid, fairy など)は
400〜600、専門的・稀な語(mycelium, basilisk, gorgon など)は
700〜900程度とした。

No app / OpenAI API calls — everything is hand-written and inserted
directly into the SQLite DB. Duplicates are skipped by english
(lowercased).

Run:  python scripts/add_biology_misc_mythical.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 生物(その他): ウイルス・細菌・菌類・原生生物など ---
    ("virus", "ウイルス", "名詞", "The flu virus spreads quickly in winter.", "生物(その他)", "500"),
    ("bacteria", "細菌(複数形)", "名詞", "Bacteria can be either harmful or beneficial to humans.", "生物(その他)", "500"),
    ("bacterium", "細菌(単数形)", "名詞", "A single bacterium is too small to see with the naked eye.", "生物(その他)", "650"),
    ("fungus", "菌類・真菌(単数形)", "名詞", "Mold is a common type of fungus.", "生物(その他)", "600"),
    ("fungi", "菌類(複数形)", "名詞", "Mushrooms and yeast are both types of fungi.", "生物(その他)", "650"),
    ("mold", "カビ", "名詞", "Mold grew on the bread after a week.", "生物(その他)", "450"),
    ("yeast", "酵母", "名詞", "Yeast makes bread dough rise.", "生物(その他)", "500"),
    ("mushroom", "キノコ", "名詞", "We picked wild mushrooms in the forest.", "生物(その他)", "400"),
    ("protozoa", "原生動物(複数形)", "名詞", "Protozoa are single-celled organisms found in water.", "生物(その他)", "800"),
    ("protozoan", "原生動物(単数形)", "名詞", "A protozoan can move and hunt for food like an animal.", "生物(その他)", "850"),
    ("lichen", "地衣類", "名詞", "Lichen grows slowly on rocks and tree bark.", "生物(その他)", "800"),
    ("algae", "藻類", "名詞", "Algae can turn a pond green in summer.", "生物(その他)", "600"),
    ("microbe", "微生物", "名詞", "Trillions of microbes live inside the human gut.", "生物(その他)", "600"),
    ("microorganism", "微生物", "名詞", "A microscope is needed to see most microorganisms.", "生物(その他)", "650"),
    ("pathogen", "病原体", "名詞", "Doctors identified the pathogen causing the outbreak.", "生物(その他)", "750"),
    ("spore", "胞子", "名詞", "Fungi reproduce by releasing tiny spores into the air.", "生物(その他)", "750"),
    ("mycelium", "菌糸体", "名詞", "The mycelium spreads underground long before a mushroom appears.", "生物(その他)", "900"),
    ("parasite", "寄生生物", "名詞", "A tapeworm is a parasite that lives inside its host.", "生物(その他)", "700"),
    ("plankton", "プランクトン", "名詞", "Tiny fish feed on plankton near the ocean's surface.", "生物(その他)", "650"),
    ("amoeba", "アメーバ", "名詞", "An amoeba constantly changes shape as it moves.", "生物(その他)", "750"),
    ("virus strain", "ウイルス株", "名詞", "Scientists tracked a new virus strain spreading across the region.", "生物(その他)", "700"),
    ("slime mold", "変形菌・粘菌", "名詞", "Slime mold can solve simple mazes despite having no brain.", "生物(その他)", "850"),
    ("mildew", "うどんこ病菌・カビ", "名詞", "Mildew formed on the damp bathroom wall.", "生物(その他)", "550"),
    ("germ", "細菌・ばい菌(口語)", "名詞", "Wash your hands to get rid of germs.", "生物(その他)", "400"),
    ("truffle", "トリュフ(菌類)", "名詞", "Truffles are a rare and expensive type of fungus.", "生物(その他)", "700"),
    ("mycology", "菌類学", "名詞", "She studies mycology at the university.", "生物(その他)", "900"),
    ("E. coli", "大腸菌", "名詞", "E. coli is commonly found in the human intestine.", "生物(その他)", "750"),
    ("protist", "原生生物", "名詞", "Protists include algae, protozoa, and slime molds.", "生物(その他)", "850"),
    # --- 生物(想像上): 神話・伝承・ファンタジーの空想上の生物 ---
    ("dragon", "ドラゴン・竜", "名詞", "The knight fought a fire-breathing dragon.", "生物(想像上)", "400"),
    ("unicorn", "ユニコーン", "名詞", "A unicorn is often pictured as a white horse with a single horn.", "生物(想像上)", "450"),
    ("phoenix", "不死鳥・フェニックス", "名詞", "The phoenix is said to rise from its own ashes.", "生物(想像上)", "600"),
    ("mermaid", "人魚(女性)", "名詞", "The mermaid sang a beautiful song from the rocks.", "生物(想像上)", "450"),
    ("merman", "人魚(男性)", "名詞", "In the story, a merman guarded the sunken treasure.", "生物(想像上)", "700"),
    ("griffin", "グリフィン(鷲と獅子の合成獣)", "名詞", "A griffin has the body of a lion and the wings of an eagle.", "生物(想像上)", "750"),
    ("kraken", "クラーケン(巨大な海の怪物)", "名詞", "Sailors feared the kraken would drag their ship under the waves.", "生物(想像上)", "800"),
    ("werewolf", "狼男", "名詞", "The villagers believed a werewolf howled at every full moon.", "生物(想像上)", "550"),
    ("vampire", "吸血鬼", "名詞", "In the legend, a vampire could not enter a home uninvited.", "生物(想像上)", "500"),
    ("centaur", "ケンタウロス(半人半馬)", "名詞", "A centaur has the upper body of a human and the lower body of a horse.", "生物(想像上)", "800"),
    ("pegasus", "ペガサス(翼のある馬)", "名詞", "Pegasus is a winged horse from Greek mythology.", "生物(想像上)", "700"),
    ("chimera", "キメラ(合成獣)", "名詞", "The chimera in the myth had the head of a lion, a goat, and a snake.", "生物(想像上)", "850"),
    ("basilisk", "バジリスク(見た者を石化させる蛇)", "名詞", "Legend says a basilisk's gaze could turn a man to stone.", "生物(想像上)", "900"),
    ("sphinx", "スフィンクス(人頭獅子身の怪物)", "名詞", "The sphinx asked travelers a riddle before letting them pass.", "生物(想像上)", "750"),
    ("yeti", "イエティ・雪男", "名詞", "Some climbers claim to have seen footprints left by a yeti.", "生物(想像上)", "650"),
    ("troll", "トロール(北欧伝承の怪物)", "名詞", "In the folktale, a troll lived under the bridge and blocked travelers.", "生物(想像上)", "550"),
    ("goblin", "ゴブリン(小鬼)", "名詞", "A mischievous goblin was blamed for the missing keys.", "生物(想像上)", "550"),
    ("fairy", "妖精", "名詞", "According to the story, a fairy granted the child three wishes.", "生物(想像上)", "400"),
    ("elf", "エルフ(伝承上の妖精族)", "名詞", "In old folklore, an elf was a magical being living in the forest.", "生物(想像上)", "450"),
    ("banshee", "バンシー(死を予告する女の妖精)", "名詞", "Irish folklore says a banshee's wail warns of an approaching death.", "生物(想像上)", "850"),
    ("minotaur", "ミノタウロス(牛頭人身の怪物)", "名詞", "The minotaur lived at the center of a vast maze.", "生物(想像上)", "800"),
    ("gorgon", "ゴルゴン(蛇の髪を持つ怪物)", "名詞", "Anyone who looked directly at the gorgon turned to stone.", "生物(想像上)", "850"),
    ("harpy", "ハーピー(女の顔を持つ鳥の怪物)", "名詞", "A harpy was said to snatch food from travelers with its claws.", "生物(想像上)", "850"),
    ("leprechaun", "レプラコーン(アイルランド伝承の妖精)", "名詞", "A leprechaun is said to guard a pot of gold at the end of a rainbow.", "生物(想像上)", "600"),
    ("ghoul", "グール(死体を食らう怪物)", "名詞", "The old tale warned that a ghoul haunted the graveyard at night.", "生物(想像上)", "750"),
    ("hydra", "ヒュドラ(多頭の蛇の怪物)", "名詞", "Each time a head was cut off the hydra, two more grew back.", "生物(想像上)", "800"),
    ("cyclops", "サイクロプス(一つ目の巨人)", "名詞", "The cyclops had a single eye in the middle of its forehead.", "生物(想像上)", "750"),
    ("ogre", "鬼・オーガ", "名詞", "The ogre in the fairy tale lived alone in a dark cave.", "生物(想像上)", "550"),
    ("imp", "インプ(小悪魔)", "名詞", "A tiny imp played tricks on anyone who entered the house.", "生物(想像上)", "700"),
    ("sea serpent", "海の大蛇(伝説上の海獣)", "名詞", "Old maps sometimes showed a sea serpent lurking in unknown waters.", "生物(想像上)", "700"),
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

    print(f"words:   +{w_added} (skipped {w_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
