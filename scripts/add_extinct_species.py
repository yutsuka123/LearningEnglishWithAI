# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add vocabulary and phrases for extinct animals, extinct plants, and the
general concepts of extinction and paleontology, authored by Claude
(2026-08-10・ユーザー要望).

対象語彙:
- 恐竜関連の基本語(dinosaur, fossil, extinction, prehistoric,
  paleontologist, excavation 等)と、学術用語として一般的に使われる代表的
  な恐竜の学名(Tyrannosaurus rex, Triceratops, Velociraptor, Stegosaurus,
  Brachiosaurus)・翼竜(Pterodactyl)。
- 恐竜以外の絶滅動物(dodo, woolly mammoth, saber-toothed tiger,
  passenger pigeon, thylacine/Tasmanian tiger, great auk, Steller's sea
  cow, Irish elk 等)。
- 絶滅植物の代表例(Wood's cycad, Franklinia alatamaha, St Helena olive)
  および「絶滅危惧種」「植物の絶滅」に関する一般語彙(endangered plant,
  extinct in the wild, herbarium specimen, last known specimen 等)。
- 絶滅の原因・概念に関する一般語彙(habitat loss, mass extinction,
  endangered species, conservation, de-extinction 等)。

domainは動物側を`動物(絶滅)`、植物側を`植物(絶滅)`とする(既存分類の拡張。
新規ドメインは作らない)。実在の学名的な種名は学術用語として一般的に使われる
ため使用しているが、特定の企業・作品・実在の人物名などの固有名詞は使用しない。

フレーズは博物館の展示解説・図鑑・ドキュメンタリー番組で使うような、絶滅種
を紹介・説明する自然な英文("This species went extinct about 65 million
years ago." など)。sceneは新規に`絶滅種・古生物学の英語`とする。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_extinct_species.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 恐竜・古生物学の基本語 ---
    ("dinosaur", "恐竜", "名詞", "Children love learning about dinosaurs that lived millions of years ago.", "動物(絶滅)", "350"),
    ("fossil", "化石", "名詞", "Scientists found a dinosaur fossil buried in the rock.", "動物(絶滅)", "400"),
    ("extinction", "絶滅", "名詞", "The extinction of the dinosaurs happened about 66 million years ago.", "動物(絶滅)", "500"),
    ("extinct", "絶滅した", "形容詞", "This species has been extinct for thousands of years.", "動物(絶滅)", "450"),
    ("prehistoric", "先史時代の", "形容詞", "Prehistoric animals roamed the earth long before humans existed.", "動物(絶滅)", "550"),
    ("paleontologist", "古生物学者", "名詞", "A paleontologist studies fossils to learn about ancient life.", "動物(絶滅)", "700"),
    ("paleontology", "古生物学", "名詞", "Paleontology helps us understand how life on Earth has changed.", "動物(絶滅)", "750"),
    ("excavation", "発掘", "名詞", "The excavation uncovered an almost complete dinosaur skeleton.", "動物(絶滅)", "700"),
    ("skeleton", "骨格", "名詞", "The museum displays a full dinosaur skeleton in the main hall.", "動物(絶滅)", "500"),
    ("predator", "捕食者", "名詞", "Tyrannosaurus rex was one of the largest predators of its time.", "動物(絶滅)", "550"),
    ("herbivore", "草食動物", "名詞", "Triceratops was a herbivore that ate low-growing plants.", "動物(絶滅)", "650"),
    ("carnivore", "肉食動物", "名詞", "Velociraptor was a small but fast carnivore.", "動物(絶滅)", "600"),
    ("Tyrannosaurus rex", "ティラノサウルス", "名詞", "Tyrannosaurus rex had powerful jaws and tiny arms.", "動物(絶滅)", "600"),
    ("Triceratops", "トリケラトプス", "名詞", "Triceratops used its three horns to defend itself from predators.", "動物(絶滅)", "600"),
    ("Velociraptor", "ヴェロキラプトル", "名詞", "Velociraptor was much smaller than movies usually show.", "動物(絶滅)", "650"),
    ("Stegosaurus", "ステゴサウルス", "名詞", "Stegosaurus had large bony plates along its back.", "動物(絶滅)", "650"),
    ("Brachiosaurus", "ブラキオサウルス", "名詞", "Brachiosaurus had an extremely long neck for reaching tall trees.", "動物(絶滅)", "650"),
    ("Pterodactyl", "翼竜", "名詞", "A Pterodactyl could glide through the air on its leathery wings.", "動物(絶滅)", "700"),
    ("asteroid impact", "隕石衝突", "名詞", "Many scientists believe an asteroid impact wiped out the dinosaurs.", "動物(絶滅)", "750"),
    ("mass extinction", "大量絶滅", "名詞", "The dinosaurs disappeared during a mass extinction event.", "動物(絶滅)", "750"),
    # --- 恐竜以外の絶滅動物 ---
    ("dodo", "ドードー", "名詞", "The dodo was a flightless bird that once lived on Mauritius.", "動物(絶滅)", "550"),
    ("woolly mammoth", "ケナガマンモス", "名詞", "The woolly mammoth was covered in thick fur to survive the cold.", "動物(絶滅)", "600"),
    ("mammoth", "マンモス", "名詞", "A frozen mammoth was discovered in the Siberian ice.", "動物(絶滅)", "500"),
    ("saber-toothed tiger", "サーベルタイガー(剣歯虎)", "名詞", "The saber-toothed tiger had two extremely long, sharp canine teeth.", "動物(絶滅)", "700"),
    ("passenger pigeon", "リョコウバト", "名詞", "The passenger pigeon once flew in flocks that darkened the sky.", "動物(絶滅)", "700"),
    ("thylacine", "フクロオオカミ(タスマニアタイガー)", "名詞", "The thylacine looked like a dog but was actually a marsupial.", "動物(絶滅)", "850"),
    ("Tasmanian tiger", "タスマニアタイガー(フクロオオカミの通称)", "名詞", "The last known Tasmanian tiger died in a zoo in 1936.", "動物(絶滅)", "750"),
    ("great auk", "オオウミガラス", "名詞", "The great auk was a large flightless seabird hunted to extinction.", "動物(絶滅)", "800"),
    ("Steller's sea cow", "ステラーカイギュウ", "名詞", "Steller's sea cow was discovered by Europeans and hunted to extinction within decades.", "動物(絶滅)", "850"),
    ("Irish elk", "オオツノジカ", "名詞", "The Irish elk had the largest antlers of any known deer species.", "動物(絶滅)", "800"),
    ("quagga", "クアッガ(絶滅した半縞馬)", "名詞", "The quagga was a subspecies of zebra with stripes only on the front of its body.", "動物(絶滅)", "850"),
    ("moa", "モア(絶滅した巨鳥)", "名詞", "The moa was a giant flightless bird that once lived in New Zealand.", "動物(絶滅)", "800"),
    ("flightless bird", "飛べない鳥", "名詞", "Many extinct island species were flightless birds with no natural predators.", "動物(絶滅)", "600"),
    ("subspecies", "亜種", "名詞", "This subspecies went extinct while its close relatives survived.", "動物(絶滅)", "700"),
    ("last known specimen", "最後に確認された個体・標本", "名詞", "The last known specimen of the species died in captivity.", "動物(絶滅)", "800"),
    ("overhunting", "乱獲", "名詞", "Overhunting was the main cause of the species' extinction.", "動物(絶滅)", "750"),
    ("de-extinction", "脱絶滅(絶滅種を復活させる試み)", "名詞", "Some scientists are researching de-extinction to bring back the woolly mammoth.", "動物(絶滅)", "900"),
    # --- 絶滅植物 ---
    ("Wood's cycad", "ウッズソテツ", "名詞", "Wood's cycad is now extinct in the wild, with only cultivated specimens remaining.", "植物(絶滅)", "900"),
    ("Franklinia alatamaha", "フランクリンの木", "名詞", "Franklinia alatamaha has not been seen growing in the wild since the early 1800s.", "植物(絶滅)", "900"),
    ("St Helena olive", "セントヘレナオリーブ", "名詞", "The St Helena olive was declared extinct in 2003.", "植物(絶滅)", "900"),
    ("endangered plant", "絶滅危惧植物", "名詞", "This endangered plant grows in only one small valley.", "植物(絶滅)", "600"),
    ("extinct in the wild", "野生絶滅", "形容詞句", "The plant is extinct in the wild but survives in botanical gardens.", "植物(絶滅)", "800"),
    ("herbarium specimen", "腊葉標本(押し葉標本)", "名詞", "Researchers studied an old herbarium specimen to identify the lost species.", "植物(絶滅)", "900"),
    ("botanical garden", "植物園", "名詞", "The botanical garden preserves seeds from endangered plant species.", "植物(絶滅)", "550"),
    ("seed bank", "種子バンク", "名詞", "A seed bank stores seeds in case a plant species disappears in the wild.", "植物(絶滅)", "700"),
    # --- 絶滅の原因・概念 ---
    ("habitat loss", "生息地の喪失", "名詞", "Habitat loss is one of the biggest threats to wildlife today.", "動物(絶滅)", "700"),
    ("endangered species", "絶滅危惧種", "名詞", "The organization works to protect endangered species around the world.", "動物(絶滅)", "500"),
    ("conservation", "保護・保全", "名詞", "Conservation efforts helped save the species from extinction.", "植物(絶滅)", "600"),
    ("invasive species", "外来種・侵略的外来種", "名詞", "An invasive species can drive native animals to extinction.", "動物(絶滅)", "750"),
    ("climate change", "気候変動", "名詞", "Climate change is pushing many species closer to extinction.", "植物(絶滅)", "500"),
]

PHRASES: list[tuple[str, str]] = [
    ("This species went extinct about 65 million years ago.", "この種はおよそ6500万年前に絶滅しました。"),
    ("The exhibit features a full-size dinosaur skeleton.", "この展示は実物大の恐竜の骨格が目玉です。"),
    ("Scientists believe an asteroid impact caused the mass extinction.", "科学者たちは、隕石の衝突が大量絶滅を引き起こしたと考えています。"),
    ("This fossil was discovered in a rock layer over 70 million years old.", "この化石は7000万年以上前の地層から発見されました。"),
    ("The dodo became extinct within a century of its discovery by humans.", "ドードーは人間に発見されてから1世紀足らずで絶滅しました。"),
    ("The last woolly mammoths survived on a remote island until about 4,000 years ago.", "最後のケナガマンモスは、約4000年前まで人里離れた島で生き延びていました。"),
    ("Overhunting drove the passenger pigeon from billions to zero in a few decades.", "乱獲によって、リョコウバトは数十億羽から数十年でゼロになりました。"),
    ("This specimen is one of the few remaining examples of the species.", "この標本は、この種に残された数少ない個体の一つです。"),
    ("The thylacine is often cited as a tragic example of human-caused extinction.", "フクロオオカミは、人間が引き起こした絶滅の悲劇的な例としてよく挙げられます。"),
    ("Please do not touch the display case containing the fossil.", "化石が入っているこの展示ケースには触れないでください。"),
    ("Paleontologists carefully brush away the sediment to reveal the bones.", "古生物学者たちは、骨を露出させるために堆積物を丁寧に払い落とします。"),
    ("This model shows what the animal may have looked like when it was alive.", "この模型は、この動物が生きていた頃の姿を再現したものです。"),
    ("The species is now classified as extinct in the wild.", "この種は現在、野生絶滅と分類されています。"),
    ("Habitat loss remains the leading cause of extinction today.", "生息地の喪失は今日でも絶滅の主な原因です。"),
    ("Conservationists hope to prevent this species from disappearing entirely.", "自然保護活動家たちは、この種が完全に姿を消すのを防ごうとしています。"),
    ("Only a handful of herbarium specimens of this plant still exist.", "この植物の腊葉標本は、今ではごくわずかしか現存していません。"),
    ("The seeds are stored in a seed bank to protect the species' genetic diversity.", "種子は、この種の遺伝的多様性を守るために種子バンクに保存されています。"),
    ("Some researchers are exploring de-extinction using preserved DNA.", "一部の研究者は、保存されたDNAを使った脱絶滅の研究を進めています。"),
    ("This bird was flightless and had no natural predators before humans arrived.", "この鳥は飛べず、人間が到来するまで天敵がいませんでした。"),
    ("The museum's collection includes fossils from every continent.", "この博物館のコレクションには、すべての大陸から集められた化石が含まれています。"),
    ("Take a closer look at the teeth to see how this predator hunted.", "この捕食者がどう狩りをしていたか、歯をよく観察してみましょう。"),
    ("New evidence suggests the animal may have lived in herds.", "新たな証拠から、この動物は群れで暮らしていた可能性が示唆されています。"),
    ("The exhibit walks visitors through the timeline of mass extinctions on Earth.", "この展示では、地球上の大量絶滅の歴史を時系列でたどることができます。"),
    ("Its closest living relative can still be found in tropical forests.", "この生物に最も近い現存種は、今も熱帯林に生息しています。"),
    ("The species was declared extinct after decades without a confirmed sighting.", "この種は、数十年にわたり確認された目撃例がなかったため絶滅と宣言されました。"),
    ("Climate change is expected to push more species toward extinction this century.", "気候変動により、今世紀中にさらに多くの種が絶滅の危機に追い込まれると予想されています。"),
    ("This cast was made from the original fossil to protect it from damage.", "このレプリカは、元の化石を損傷から守るために作られたものです。"),
    ("The documentary follows scientists searching for traces of the lost species.", "このドキュメンタリーは、失われた種の痕跡を追う科学者たちを追跡します。"),
    ("Please keep your voice down near the fossil excavation display.", "化石発掘の展示の近くでは、お静かにお願いいたします。"),
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
                "VALUES (?, ?, '絶滅種・古生物学の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
