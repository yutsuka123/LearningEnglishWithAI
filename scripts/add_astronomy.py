# ruff: noqa: E501
"""Astronomy vocabulary: amateur basics, solar system, stars & galaxies,
cosmology / astrophysics, and observing instruments. Authored by Claude — no
app/OpenAI API calls. Dedupe on english; back-fill examples. domain="天文".
Run: python scripts/add_astronomy.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

GROUPS: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "太陽系": ("600", [
        ("solar system", "太陽系", "Eight planets orbit our solar system."),
        ("planet", "惑星", "Jupiter is the largest planet."),
        ("the Sun", "太陽", "The Sun is our nearest star."),
        ("the Moon", "月", "The Moon orbits the Earth."),
        ("Mercury", "水星", "Mercury is closest to the Sun."),
        ("Venus", "金星", "Venus is the brightest planet in the sky."),
        ("Mars", "火星", "Mars is known as the red planet."),
        ("Jupiter", "木星", "Jupiter has a Great Red Spot."),
        ("Saturn", "土星", "Saturn is famous for its rings."),
        ("Uranus", "天王星", "Uranus rotates on its side."),
        ("Neptune", "海王星", "Neptune is a distant blue planet."),
        ("Pluto", "冥王星", "Pluto is now classed as a dwarf planet."),
        ("dwarf planet", "準惑星", "Pluto is a dwarf planet."),
        ("asteroid", "小惑星", "An asteroid orbits between Mars and Jupiter."),
        ("asteroid belt", "小惑星帯", "Most asteroids lie in the asteroid belt."),
        ("comet", "彗星", "A comet has a long glowing tail."),
        ("meteor", "流星", "A meteor streaked across the night sky."),
        ("meteorite", "隕石", "A meteorite struck the desert."),
        ("gas giant", "巨大ガス惑星", "Jupiter is a gas giant."),
        ("satellite (moon)", "衛星", "The Moon is Earth's natural satellite."),
    ]),
    "恒星・銀河": ("700", [
        ("star", "恒星・星", "The Sun is an ordinary star."),
        ("galaxy", "銀河", "A galaxy contains billions of stars."),
        ("the Milky Way", "天の川銀河", "We live in the Milky Way."),
        ("Andromeda galaxy", "アンドロメダ銀河", "The Andromeda galaxy is approaching us."),
        ("galaxy cluster", "銀河団", "A galaxy cluster holds many galaxies."),
        ("nebula", "星雲", "A nebula is a cloud of gas and dust."),
        ("constellation", "星座", "Orion is a famous constellation."),
        ("supernova", "超新星", "A supernova is an exploding star."),
        ("white dwarf", "白色矮星", "Our Sun will end as a white dwarf."),
        ("red giant", "赤色巨星", "A red giant is a swollen, dying star."),
        ("neutron star", "中性子星", "A neutron star is incredibly dense."),
        ("pulsar", "パルサー", "A pulsar emits regular radio pulses."),
        ("black hole", "ブラックホール", "Not even light escapes a black hole."),
        ("star cluster", "星団", "The Pleiades form a star cluster."),
        ("binary star", "連星", "A binary star is two stars in orbit."),
    ]),
    "宇宙論・天体物理": ("900", [
        ("Big Bang", "ビッグバン", "The Big Bang began the universe."),
        ("redshift", "赤方偏移", "Redshift shows galaxies moving away."),
        ("blueshift", "青方偏移", "Blueshift means an object is approaching."),
        ("dark matter", "暗黒物質", "Dark matter is invisible but has mass."),
        ("dark energy", "暗黒エネルギー", "Dark energy speeds up the expansion."),
        ("light-year", "光年", "A light-year is a unit of distance."),
        ("parsec", "パーセク", "A parsec is about 3.26 light-years."),
        ("gravitational wave", "重力波", "Gravitational waves ripple through spacetime."),
        ("event horizon", "事象の地平面", "Nothing escapes past the event horizon."),
        ("singularity", "特異点", "A black hole hides a singularity at its core."),
        ("cosmic microwave background", "宇宙マイクロ波背景放射", "The cosmic microwave background is the Big Bang's afterglow."),
        ("expanding universe", "膨張する宇宙", "We live in an expanding universe."),
        ("luminosity", "光度", "Luminosity is a star's total energy output."),
        ("spectrum", "スペクトル", "A star's spectrum reveals its elements."),
        ("cosmology", "宇宙論", "Cosmology studies the whole universe."),
        ("astrophysics", "天体物理学", "Astrophysics applies physics to the stars."),
    ]),
    "観測機器": ("700", [
        ("telescope", "望遠鏡", "She viewed Saturn through a telescope."),
        ("refractor", "屈折望遠鏡", "A refractor focuses light with a lens."),
        ("reflector", "反射望遠鏡", "A reflector uses a curved mirror."),
        ("eyepiece", "接眼レンズ", "Swap the eyepiece for higher magnification."),
        ("aperture", "口径", "A larger aperture gathers more light."),
        ("focal length", "焦点距離", "The focal length affects the magnification."),
        ("observatory", "天文台", "The observatory sits on a dark mountain."),
        ("radio telescope", "電波望遠鏡", "A radio telescope detects faint signals."),
        ("space telescope", "宇宙望遠鏡", "A space telescope orbits above the air."),
        ("equatorial mount", "赤道儀", "An equatorial mount tracks the moving stars."),
    ]),
    "星座・恒星名": ("600", [
        ("Sirius", "シリウス(おおいぬ座α)", "Sirius is the brightest star in the night sky."),
        ("Betelgeuse", "ベテルギウス(オリオン座α)", "Betelgeuse is a red giant in Orion."),
        ("Rigel", "リゲル(オリオン座β)", "Rigel is a brilliant blue star."),
        ("Polaris", "北極星・ポラリス", "Polaris stays almost fixed above the north pole."),
        ("Vega", "ベガ(こと座)", "Vega shines high in the summer sky."),
        ("Altair", "アルタイル(わし座)", "Altair is the Eagle's brightest star."),
        ("Deneb", "デネブ(はくちょう座)", "Deneb marks the tail of the Swan."),
        ("Aldebaran", "アルデバラン(おうし座)", "Aldebaran glows orange in Taurus."),
        ("Antares", "アンタレス(さそり座)", "Antares is the red heart of Scorpius."),
        ("Arcturus", "アークトゥルス(うしかい座)", "Arcturus is a bright orange star."),
        ("Capella", "カペラ(ぎょしゃ座)", "Capella shines in the winter sky."),
        ("Canopus", "カノープス(りゅうこつ座)", "Canopus is the second brightest star."),
        ("Spica", "スピカ(おとめ座)", "Spica is a hot blue-white star."),
        ("Orion", "オリオン座", "Orion is easy to spot in winter."),
        ("Ursa Major", "おおぐま座", "The Big Dipper is part of Ursa Major."),
        ("Big Dipper", "北斗七星", "The Big Dipper points to the pole star."),
        ("Cassiopeia", "カシオペヤ座", "Cassiopeia looks like a letter W."),
        ("Scorpius", "さそり座", "Scorpius curves like a scorpion's tail."),
        ("Pleiades", "プレアデス星団・すばる", "The Pleiades are a sparkling star cluster."),
        ("Summer Triangle", "夏の大三角", "Vega, Deneb, and Altair form the Summer Triangle."),
        ("Southern Cross", "南十字星", "The Southern Cross guides sailors in the south."),
    ]),
    "基礎知識": ("600", [
        ("eclipse", "食(日食・月食)", "An eclipse happens when bodies line up."),
        ("solar eclipse", "日食", "A total solar eclipse is a rare sight."),
        ("lunar eclipse", "月食", "The Moon turns red in a lunar eclipse."),
        ("phase", "(月の)満ち欠け", "The Moon goes through its phases."),
        ("zodiac", "黄道十二星座・獣帯", "The zodiac follows the Sun's yearly path."),
        ("magnitude", "等級(明るさ)", "A lower magnitude means a brighter star."),
        ("light pollution", "光害", "Light pollution hides the faint stars."),
        ("meteor shower", "流星群", "A meteor shower will peak tonight."),
        ("celestial sphere", "天球", "Stars appear fixed on the celestial sphere."),
        ("pole star", "北極星", "The pole star marks true north."),
        ("light-gathering", "集光(力)", "A big mirror improves light-gathering."),
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
                    (en, ja, "", ex, "天文", level),
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
