# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add vocabulary for three nature/science observation hobbies: AMATEUR
ASTRONOMY, BIRDWATCHING/BIRDING, and MINERAL/ROCK COLLECTING (rockhounding),
authored by Claude (2026-08-04・ユーザー要望).

This is pure vocabulary-teaching content — it does not imply the app
identifies species, minerals, or celestial objects. It just teaches the
English terms a hobbyist would use.

Focus:
  1. 天文 (amateur astronomy) — 既存の `天文` ドメイン(86語)は太陽系/恒星名/
     物理用語が中心で、実際に観望会に参加する際の実践語彙（望遠鏡の部品、
     観望会そのもの、天体写真、ファーストライトなど）が手薄だったため補強。
     domain は既存の `天文` に合わせる。
  2. 野鳥観察 (birding) — 双眼鏡、図鑑、渡り鳥、猛禽類、迷鳥など、趣味として
     の野鳥観察に必要な語彙。専用ドメインが無いため、既存の `アウトドア・
     レジャー` ドメイン（キャンプ/釣り等と同じ「屋外の趣味」カテゴリ）に含める。
  3. 鉱物・岩石採集 (rockhounding) — 鉱物標本、晶洞、モース硬度、へき開など、
     石集めを趣味にする人向けの語彙。既存の `地学` ドメインは天気/地質学の
     学術語彙が中心なので混同を避け、こちらも趣味語彙として `アウトドア・
     レジャー` ドメインに含める。

既存語彙との衝突（telescope / constellation / galaxy / light pollution /
observatory / meteor shower / fossil 等）は事前に確認済み。これらは他ドメ
インや `天文` ドメインに既に存在するため、実行時は english(lower) の重複
チェックで自動的にスキップされる。english side に "(mineral)" / "(rock)"
のような曖昧さ回避の注記を付けた語（cleavage (mineral), matrix (rock)）は
既存の add_astronomy.py の "satellite (moon)" と同じ書式に倣った。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_astronomy_birding_minerals.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 天文 (amateur astronomy, domain: 天文) ---
    ("telescope", "望遠鏡", "名詞", "He set up his telescope in the backyard before the sky got fully dark.", "天文", "500"),
    ("stargazing", "星空観察", "名詞", "Stargazing is a relaxing hobby that just needs a dark sky and some patience.", "天文", "500"),
    ("constellation", "星座", "名詞", "She learned to trace the constellation Orion across the winter sky.", "天文", "550"),
    ("galaxy", "銀河", "名詞", "On a clear night you can just make out the galaxy's spiral arms.", "天文", "600"),
    ("meteor shower", "流星群", "名詞", "We stayed up late to watch the meteor shower peak after midnight.", "天文", "600"),
    ("observatory", "天文台", "名詞", "The observatory on the mountain opens to visitors on weekends.", "天文", "600"),
    ("star party", "スターパーティー（愛好家が集まる観望会）", "名詞", "Dozens of amateurs brought their telescopes to the star party.", "天文", "650"),
    ("eyepiece", "接眼レンズ", "名詞", "Swapping the eyepiece changes how much magnification you get.", "天文", "700"),
    ("light pollution", "光害", "名詞", "Light pollution from the city washes out the fainter stars.", "天文", "750"),
    ("nebula", "星雲", "名詞", "Through the eyepiece, the nebula looked like a faint gray smudge.", "天文", "750"),
    ("exoplanet", "系外惑星（太陽系の外にある惑星）", "名詞", "Astronomers have confirmed thousands of exoplanets so far.", "天文", "750"),
    ("aperture", "口径（望遠鏡のレンズや鏡の直径）", "名詞", "A wider aperture lets the telescope gather more light.", "天文", "750"),
    ("astrophotography", "天体写真撮影", "名詞", "He got into astrophotography soon after buying his first telescope.", "天文", "800"),
    ("magnitude", "等級（天体の明るさを表す数値）", "名詞", "A star with a lower magnitude number appears brighter.", "天文", "800"),
    ("deep-sky object", "深宇宙天体（銀河・星雲・星団などの遠方の天体）", "名詞", "Galaxies and nebulae are both classified as deep-sky objects.", "天文", "800"),
    ("tracking mount", "追尾式マウント（星の動きに合わせて自動で望遠鏡を動かす架台）", "名詞", "A tracking mount keeps the target centered as the sky slowly rotates.", "天文", "800"),
    ("first light", "ファーストライト（新しい望遠鏡・観測装置で最初に観測すること）", "名詞", "The new observatory captured its first light image last week.", "天文", "850"),
    ("occultation", "掩蔽（えんぺい：ある天体が別の天体に隠される現象）", "名詞", "The Moon will pass in front of Jupiter in tonight's occultation.", "天文", "900"),
    # --- 野鳥観察 (birding, domain: アウトドア・レジャー) ---
    ("birdwatching", "バードウォッチング", "名詞", "Birdwatching got popular with her after she moved near the lake.", "アウトドア・レジャー", "450"),
    ("binoculars", "双眼鏡", "名詞", "Bring a good pair of binoculars if you want to see birds up close.", "アウトドア・レジャー", "500"),
    ("nest", "巣", "名詞", "A pair of swallows built a nest under the eaves of the house.", "アウトドア・レジャー", "500"),
    ("birdsong", "鳥のさえずり", "名詞", "We woke up to birdsong coming from the garden.", "アウトドア・レジャー", "550"),
    ("field guide", "図鑑（野外で使う識別用のガイドブック）", "名詞", "She checked the field guide to identify the bird's markings.", "アウトドア・レジャー", "600"),
    ("migratory bird", "渡り鳥", "名詞", "Migratory birds pass through this wetland every spring and fall.", "アウトドア・レジャー", "600"),
    ("songbird", "鳴禽（めいきん：鳴き声で知られる小鳥）", "名詞", "A songbird perched on the fence and sang for several minutes.", "アウトドア・レジャー", "600"),
    ("birding hotspot", "バードウォッチングの人気スポット", "名詞", "The reservoir is a well-known birding hotspot in autumn.", "アウトドア・レジャー", "650"),
    ("waterfowl", "水鳥（カモ・ガンなど）", "名詞", "The marsh is a popular spot for watching waterfowl in winter.", "アウトドア・レジャー", "700"),
    ("spotting scope", "観察用望遠鏡（単眼鏡）", "名詞", "He set up a spotting scope on a tripod to watch the shorebirds.", "アウトドア・レジャー", "700"),
    ("life list", "ライフリスト（生涯に観察した鳥の記録）", "名詞", "Spotting the eagle added a brand-new species to his life list.", "アウトドア・レジャー", "750"),
    ("plumage", "羽毛（鳥の羽の色や模様）", "名詞", "The male's bright plumage makes it easy to tell him from the female.", "アウトドア・レジャー", "750"),
    ("raptor", "猛禽類（タカ・ワシなど肉食の鳥）", "名詞", "A raptor circled high above the field, hunting for prey.", "アウトドア・レジャー", "750"),
    ("molt", "換羽（かんう：鳥が古い羽を新しい羽に生え替わらせること）", "名詞", "Birds often look a little ragged while they molt.", "アウトドア・レジャー", "800"),
    ("fledgling", "巣立ったばかりのひな鳥", "名詞", "The fledgling took its first clumsy flight from the branch.", "アウトドア・レジャー", "800"),
    ("twitcher", "トゥイッチャー（珍しい鳥を追いかけ回す熱心なバードウォッチャー）", "名詞", "A group of twitchers drove three hours to see the rare warbler.", "アウトドア・レジャー", "850"),
    ("vagrant", "迷鳥（本来の生息域から外れて現れる珍しい鳥）", "名詞", "Birders rushed to the coast when a vagrant from Asia was reported.", "アウトドア・レジャー", "900"),
    # --- 鉱物・岩石採集 (rockhounding, domain: アウトドア・レジャー) ---
    ("gem", "宝石（原石・貴石）", "名詞", "He turned the rough gem into a small polished stone.", "アウトドア・レジャー", "400"),
    ("fossil", "化石", "名詞", "She found a small fossil pressed into a flat gray rock.", "アウトドア・レジャー", "500"),
    ("field trip", "野外採集・巡検", "名詞", "Our rock club organizes a field trip to the quarry every spring.", "アウトドア・レジャー", "550"),
    ("quartz", "石英", "名詞", "Clear quartz is one of the easiest minerals to find on a hike.", "アウトドア・レジャー", "600"),
    ("rock tumbler", "ロックタンブラー（石を回転させて磨く機械）", "名詞", "She polished the beach stones in a rock tumbler for two weeks.", "アウトドア・レジャー", "700"),
    ("mineral specimen", "鉱物標本", "名詞", "He keeps every mineral specimen labeled with the date and location.", "アウトドア・レジャー", "700"),
    ("crystal formation", "結晶形成・結晶のかたち", "名詞", "The cave is famous for its striking crystal formations.", "アウトドア・レジャー", "750"),
    ("semi-precious stone", "半貴石", "名詞", "Amethyst and agate are both popular semi-precious stones.", "アウトドア・レジャー", "750"),
    ("geode", "晶洞（ジオード：内部に結晶が育つ丸い岩石）", "名詞", "When they cracked the geode open, it was lined with purple crystals.", "アウトドア・レジャー", "800"),
    ("gem cutting", "宝石研磨・カット", "名詞", "Gem cutting takes a steady hand and a lot of patience.", "アウトドア・レジャー", "800"),
    ("rockhound", "ロックハウンド（鉱物・化石収集を趣味にする人）", "名詞", "My uncle is a lifelong rockhound with boxes of specimens in the garage.", "アウトドア・レジャー", "800"),
    ("rockhounding", "ロックハウンディング（趣味としての鉱物・化石採集）", "名詞", "They spent the whole weekend rockhounding along the dry riverbed.", "アウトドア・レジャー", "850"),
    ("matrix (rock)", "母岩（鉱物や化石を包んでいる周囲の岩石）", "名詞", "The crystals were still attached to their original matrix.", "アウトドア・レジャー", "850"),
    ("Mohs hardness scale", "モース硬度計（鉱物の硬さを1〜10の数値で表す尺度）", "名詞", "Geologists use the Mohs hardness scale to help identify unknown minerals.", "アウトドア・レジャー", "900"),
    ("cleavage (mineral)", "へき開（鉱物が特定の方向にきれいに割れる性質）", "名詞", "Mica's cleavage lets you peel it apart into thin, flat sheets.", "アウトドア・レジャー", "900"),
]

PHRASES: list[tuple[str, str]] = [
    ("Can I look through your telescope?", "望遠鏡を覗かせてもらえますか？"),
    ("What's the magnification on this?", "これの倍率はどれくらいですか？"),
    ("The sky is really clear tonight.", "今夜は空がとても澄んでいますね。"),
    ("Do you know what constellation that is?", "あれが何座か分かりますか？"),
    ("How big is your telescope's aperture?", "その望遠鏡の口径はどれくらいですか？"),
    ("There's a meteor shower peaking tonight.", "今夜は流星群がピークを迎えます。"),
    ("We drove out of the city to escape the light pollution.", "光害を避けるために街の外まで車で行きました。"),
    ("I finally got my telescope's first light last night.", "昨夜、ついに望遠鏡のファーストライトを迎えました。"),
    ("The observatory is open to the public on Fridays.", "その天文台は金曜日に一般公開されています。"),
    ("I spotted a rare bird today.", "今日は珍しい鳥を見つけました。"),
    ("What kind of bird is that?", "あれは何の鳥ですか？"),
    ("Bring your binoculars, we might see something good.", "双眼鏡を持ってきて、良いものが見られるかもしれません。"),
    ("Let's check the field guide.", "図鑑で確認しましょう。"),
    ("Let's add this to your life list.", "これをあなたのライフリストに加えましょう。"),
    ("This place is a great birding hotspot in the morning.", "ここは朝には絶好のバードウォッチングスポットです。"),
    ("Is this mineral specimen for sale?", "この鉱物標本は販売されていますか？"),
    ("Where did you find this fossil?", "この化石はどこで見つけたのですか？"),
    ("This rock has a beautiful crystal formation inside.", "この岩の中にはきれいな結晶ができています。"),
    ("Is this quartz or just plain glass?", "これは石英ですか、それともただのガラスですか？"),
    ("How hard is this mineral on the Mohs scale?", "この鉱物はモース硬度でどれくらいの硬さですか？"),
    ("Do you want to join our rock club's field trip?", "私たちの岩石クラブの巡検に参加しませんか？"),
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

        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        ph_added = ph_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in ph_existing:
                ph_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '天文・野鳥・鉱物観察の英語')",
                (en, ja),
            )
            ph_existing.add(en.lower())
            ph_added += 1

    print(f"words: +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
