# ruff: noqa: E501
"""Chemistry vocabulary: organic/inorganic terms, substances, periodic-table
elements, and (as factual dictionary entries only) explosives/poisons —
names + neutral definitions, NO synthesis or usage instructions. Authored by
Claude — no app/OpenAI API calls. Dedupe on english; back-fill empty examples.
domain="化学". Run: python scripts/add_chemistry.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# group -> (level, [(english, japanese, example)])
GROUPS: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "基礎物質": ("500", [
        ("water", "水", "Water is made of hydrogen and oxygen."),
        ("carbon dioxide", "二酸化炭素", "Plants absorb carbon dioxide."),
        ("oxygen", "酸素", "We breathe in oxygen."),
        ("hydrogen", "水素", "Hydrogen is the lightest element."),
        ("nitrogen", "窒素", "Air is mostly nitrogen."),
        ("sugar", "糖・砂糖", "Sugar dissolves in water."),
        ("glucose", "ブドウ糖・グルコース", "Cells use glucose for energy."),
        ("starch", "デンプン", "Rice is rich in starch."),
        ("salt", "塩", "Table salt is sodium chloride."),
        ("vitamin", "ビタミン", "Oranges contain vitamin C."),
        ("protein", "タンパク質", "Meat is high in protein."),
        ("mineral", "ミネラル・無機物", "Milk provides calcium and minerals."),
    ]),
    "酸・塩基": ("700", [
        ("acid", "酸", "Lemon juice is a weak acid."),
        ("alkali", "アルカリ", "Soap is mildly alkali."),
        ("base", "塩基", "A base neutralizes an acid."),
        ("salt (compound)", "塩（えん・化合物）", "An acid and a base form a salt."),
        ("sulfuric acid", "硫酸", "Sulfuric acid is highly corrosive."),
        ("nitric acid", "硝酸", "Nitric acid is a strong oxidizer."),
        ("hydrochloric acid", "塩酸", "Hydrochloric acid is in stomach fluid."),
        ("acetic acid", "酢酸", "Vinegar contains acetic acid."),
        ("citric acid", "クエン酸", "Citric acid gives lemons their sourness."),
        ("ammonia", "アンモニア", "Ammonia has a sharp smell."),
        ("sodium hydroxide", "水酸化ナトリウム", "Sodium hydroxide is caustic."),
        ("neutralization", "中和", "Neutralization produces water and salt."),
        ("corrosive", "腐食性の", "The acid is highly corrosive."),
        ("pH indicator", "pH指示薬", "The pH indicator turned red."),
    ]),
    "有機化学": ("800", [
        ("organic compound", "有機化合物", "Methane is a simple organic compound."),
        ("hydrocarbon", "炭化水素", "Petroleum is a mix of hydrocarbons."),
        ("alcohol", "アルコール", "Ethanol is a type of alcohol."),
        ("ethanol", "エタノール", "Ethanol is used as a fuel and solvent."),
        ("methanol", "メタノール", "Methanol is toxic if swallowed."),
        ("ester", "エステル", "Esters often smell fruity."),
        ("benzene", "ベンゼン", "Benzene has a ring structure."),
        ("ethylene", "エチレン", "Ethylene is used to make plastics."),
        ("methane", "メタン", "Methane is the main component of natural gas."),
        ("propane", "プロパン", "Propane fuels portable stoves."),
        ("polymer", "重合体・ポリマー", "Plastic is a synthetic polymer."),
        ("monomer", "単量体・モノマー", "Monomers link to form polymers."),
        ("aldehyde", "アルデヒド", "Formaldehyde is a common aldehyde."),
        ("ketone", "ケトン", "Acetone is a simple ketone."),
        ("carboxylic acid", "カルボン酸", "Acetic acid is a carboxylic acid."),
        ("amine", "アミン", "Amines contain nitrogen."),
        ("phenol", "フェノール", "Phenol is used in disinfectants."),
        ("glycerol", "グリセロール・グリセリン", "Glycerol is found in soap."),
        ("acetone", "アセトン", "Acetone removes nail polish."),
        ("functional group", "官能基", "A functional group defines reactivity."),
    ]),
    "石油・素材": ("700", [
        ("petroleum", "石油", "Petroleum is refined into many products."),
        ("crude oil", "原油", "Crude oil is pumped from underground."),
        ("naphtha", "ナフサ", "Naphtha is a raw material for plastics."),
        ("kerosene", "灯油・ケロシン", "Kerosene is used for heating."),
        ("refinery", "精製所", "Crude oil is processed at a refinery."),
        ("synthetic fiber", "合成繊維", "Nylon is a synthetic fiber."),
        ("nylon", "ナイロン", "Nylon is strong and elastic."),
        ("polyester", "ポリエステル", "The shirt is made of polyester."),
        ("resin", "樹脂", "Epoxy resin sets very hard."),
        ("rubber", "ゴム", "Tires are made of rubber."),
        ("plastic", "プラスチック", "Plastic does not break down easily."),
        ("fiber", "繊維", "Cotton is a natural fiber."),
    ]),
    "元素": ("700", [
        ("element", "元素", "Gold is a chemical element."),
        ("periodic table", "周期表", "Elements are arranged in the periodic table."),
        ("helium", "ヘリウム", "Helium makes balloons float."),
        ("lithium", "リチウム", "Lithium is used in batteries."),
        ("carbon", "炭素", "Diamond is pure carbon."),
        ("sodium", "ナトリウム", "Sodium reacts violently with water."),
        ("magnesium", "マグネシウム", "Magnesium burns with a bright light."),
        ("aluminum", "アルミニウム", "Aluminum is light and strong."),
        ("silicon", "ケイ素・シリコン", "Silicon is used in computer chips."),
        ("phosphorus", "リン", "Phosphorus glows in the dark."),
        ("sulfur", "硫黄", "Sulfur smells like rotten eggs."),
        ("chlorine", "塩素", "Chlorine disinfects swimming pools."),
        ("potassium", "カリウム", "Bananas are rich in potassium."),
        ("calcium", "カルシウム", "Calcium strengthens bones."),
        ("iron", "鉄", "Iron rusts in damp air."),
        ("copper", "銅", "Copper conducts electricity well."),
        ("zinc", "亜鉛", "Zinc protects steel from rust."),
        ("silver", "銀", "Silver tarnishes over time."),
        ("mercury", "水銀", "Mercury is a liquid metal."),
        ("lead", "鉛", "Lead is heavy and toxic."),
        ("uranium", "ウラン", "Uranium is used as nuclear fuel."),
        ("plutonium", "プルトニウム", "Plutonium is highly radioactive."),
        ("neon", "ネオン", "Neon glows in signs."),
        ("argon", "アルゴン", "Argon is an inert gas."),
        ("platinum", "白金・プラチナ", "Platinum is a precious metal."),
        ("titanium", "チタン", "Titanium is strong and light."),
    ]),
    # 爆薬・毒物: 名称と中立的な説明のみ（製法・用法は記載しない）。
    "爆薬・毒物": ("800", [
        ("explosive", "爆発物・爆薬", "The explosive must be handled with care."),
        ("gunpowder", "火薬", "Gunpowder was invented in ancient China."),
        ("dynamite", "ダイナマイト", "Nobel invented dynamite in 1867."),
        ("TNT", "TNT（トリニトロトルエン）", "TNT is a well-known explosive."),
        ("nitroglycerin", "ニトログリセリン", "Nitroglycerin is dangerously unstable."),
        ("detonator", "起爆装置・雷管", "A detonator sets off the charge."),
        ("poison", "毒", "The bottle was labeled as poison."),
        ("toxin", "毒素", "Some bacteria release toxins."),
        ("venom", "（動物の）毒", "Snake venom can be deadly."),
        ("cyanide", "シアン化物・青酸", "Cyanide is a fast-acting poison."),
        ("potassium cyanide", "青酸カリ", "Potassium cyanide is extremely toxic."),
        ("arsenic", "ヒ素", "Arsenic is a poisonous element."),
        ("strychnine", "ストリキニーネ", "Strychnine is a powerful poison."),
        ("opium", "アヘン", "Opium comes from the poppy plant."),
        ("sarin", "サリン", "Sarin is a banned nerve agent."),
        ("mustard gas", "マスタードガス（イペリット）", "Mustard gas was used in World War I."),
        ("nerve agent", "神経剤", "Nerve agents are banned chemical weapons."),
        ("chemical weapon", "化学兵器", "Chemical weapons are banned by treaty."),
        ("radioactive", "放射性の", "Radioactive waste is stored carefully."),
        ("carcinogen", "発がん性物質", "Asbestos is a known carcinogen."),
    ]),
}


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = filled = 0
        per_group: dict[str, int] = {}
        for group, (level, items) in GROUPS.items():
            for en, ja, ex in items:
                if en.lower() in existing:
                    conn.execute(
                        "UPDATE words SET example = ? WHERE "
                        "LOWER(english)=LOWER(?) AND COALESCE(example,'')=''",
                        (ex, en),
                    )
                    filled += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, ja, "", ex, "化学", level),
                )
                existing.add(en.lower())
                added += 1
                per_group[group] = per_group.get(group, 0) + 1
    print(f"words: +{added} (例文補充 {filled})  {per_group}")
    with db() as conn:
        print("単語総数:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
