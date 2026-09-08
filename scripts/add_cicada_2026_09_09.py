# ruff: noqa: E501
"""セミ(cicada)の網羅的拡充(2026-09-09・authored by Claude)。ユーザー指示「虫は蝉に関しては網羅してほしい」。既存の動物(昆虫)ドメインに追加(新ドメインは作らない)。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_cicada_2026_09_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("Hyalessa maculaticollis", "ミンミンゼミの学名。英語には定着した通称がなく、学名でそのまま呼ばれることが多い。体長33〜36mmで緑と黒の斑紋があり、「ミーンミンミンミンミー」という鳴き声で知られる、日本の代表的なセミの一種。", "名詞句", "Hyalessa maculaticollis, known in Japan as the minminzemi, is instantly recognizable by its loud 'min-min-min' call echoing through the trees.", "動物(昆虫)", "720"),
    ("Platypleura kaempferi", "ニイニイゼミの学名。英語には定着した通称がなく、学名でそのまま呼ばれることが多い。体長20〜24mmと小型で、前翅に褐色のまだら模様があり(多くのセミの透明な翅と異なる)、他のセミより一足早く「チー…ジー…チッチッチ」と鳴き始める。", "名詞句", "Platypleura kaempferi, the niiniizemi, is usually the first cicada to start singing each summer in Japan.", "動物(昆虫)", "720"),
    ("Bear Cicada", "クマゼミの英語での呼び名(直訳)。日本産セミの中でも大型(体長4〜5cm)で、「シャシャシャ…」という非常に大きな鳴き声(80〜90デシベル)が特徴。近年は分布を北へ広げていることでも知られる。", "名詞句", "The Bear Cicada is one of the largest and loudest cicadas found in Japan, with a call that can reach nearly 90 decibels.", "動物(昆虫)", "650"),
    ("elongate cicada", "ツクツクボウシの英語名の一つ(別名Walker's cicada)。細長い体型が特徴で、「オーシツクツク」という独特の鳴き声で知られる、晩夏を告げるセミ。", "名詞句", "The elongate cicada, also called Walker's cicada, is known for its distinctive song that seems to speed up and then slow down again.", "動物(昆虫)", "650"),
    ("periodical cicada", "北米に生息し、13年または17年という長い周期で一斉に地上に出現する特異な生態を持つセミの一群。周期ゼミ。", "名詞句", "Periodical cicadas spend most of their lives underground before emerging in massive numbers once every 13 or 17 years.", "動物(昆虫)", "600"),
    ("13-year cicada", "北米のMagicicada属に属し、13年周期で一斉に地上に出現するグループの周期ゼミ。13年ゼミ。", "名詞句", "The 13-year cicadas mostly emerge in the southern United States, unlike their 17-year relatives further north.", "動物(昆虫)", "600"),
    ("17-year cicada", "北米のMagicicada属に属し、17年周期で一斉に地上に出現するグループの周期ゼミ。周期ゼミの中で最もよく知られるタイプ。17年ゼミ。", "名詞句", "The 17-year cicada is the most famous type of periodical cicada, emerging in vast numbers across the eastern United States.", "動物(昆虫)", "600"),
    ("cicada brood", "周期ゼミにおいて、同じ年にまとまって羽化・出現する地理的な個体群の単位。ローマ数字で番号が付けられる(例:ブルードX)。ブルード(セミの発生系統群)。", "名詞句", "Brood X is one of the best-known cicada broods, covering a huge swath of the eastern United States.", "動物(昆虫)", "650"),
    ("mass emergence", "周期ゼミなどが、天敵に食べ尽くされるのを防ぐために、極めて短期間に大量の個体が一斉に地上へ姿を現す現象。大量羽化・一斉出現。", "名詞句", "The mass emergence of periodical cicadas can exceed a million insects per acre in a single night.", "動物(昆虫)", "600"),
    ("dog-day cicada", "周期ゼミとは異なり、毎年夏(盛夏、いわゆる「ドッグデイズ」の時期)に見られる非周期性のセミの総称。北米のNeotibicen属などを指す。", "名詞句", "Dog-day cicadas appear every summer, unlike periodical cicadas that emerge only once every 13 or 17 years.", "動物(昆虫)", "600"),
    ("predator satiation", "捕食者が食べきれないほど大量の個体が同時に出現することで、種全体としての生存率を高める進化戦略。捕食者飽食(戦略)。", "名詞句", "Predator satiation is thought to be one reason periodical cicadas emerge in such enormous, synchronized numbers.", "動物(昆虫)", "750"),
    ("cicada nymph", "セミの幼虫。孵化後に地中に潜り、何年も木の根から出る液を吸って成長する地下生活の段階を指す。セミの幼虫(地中生活する若虫)。", "名詞句", "A cicada nymph can spend anywhere from one to seventeen years underground before it is ready to emerge.", "動物(昆虫)", "500"),
    ("instar", "昆虫などの節足動物が、脱皮と脱皮の間に過ごす発育段階。周期ゼミの幼虫は地中で5回のこの段階を経て成虫になる。齢(れい)。", "名詞", "A periodical cicada nymph passes through five instars underground before its final molt into a winged adult.", "動物(昆虫)", "700"),
    ("molting", "昆虫などが成長や変態のために古い外骨格(殻)を脱ぎ捨てる過程。セミの幼虫が地上に出て成虫へと姿を変える最後の脱皮はその代表例。脱皮(すること)。", "名詞", "A cicada's final molting transforms it from a wingless underground nymph into a winged adult.", "動物(昆虫)", "480"),
    ("cicada shell", "セミが羽化する際に木の幹などに残していく抜け殻を指す、日常的によく使われる表現。日本の夏の風物詩としてもおなじみの「セミの抜け殻」。", "名詞句", "Children in Japan love collecting cicada shells they find clinging to tree bark in summer.", "動物(昆虫)", "500"),
    ("tymbal", "オスのセミの腹部の付け根にある、波板状の発音器官。高速で振動させることで、体に対して非常に大きな鳴き声を作り出す。鼓膜状発音器官(セミの発音器官)。", "名詞", "A male cicada's tymbal vibrates so rapidly that it produces one of the loudest sounds made by any insect.", "動物(昆虫)", "700"),
    ("buzzing", "セミやハチなどの羽や発音器官が作り出す、ブンブン・ジーという連続した振動音。ブンブンいう音(羽音・振動音)。", "名詞・形容詞", "The buzzing of cicadas filled the air on the hot summer afternoon.", "動物(昆虫)", "420"),
    ("droning", "低く単調に鳴り響き続ける音。真夏にセミの声が途切れず響き渡る様子などを表す。低く単調に鳴り響く音。", "名詞・形容詞", "A droning chorus of cicadas rose and fell throughout the humid afternoon.", "動物(昆虫)", "450"),
    ("chirring", "コオロギやセミなど昆虫が出す、細かく震えるような連続音。チリチリ(ジリジリ)と鳴く音。", "名詞・形容詞", "The chirring of cicadas and crickets blended together into the background noise of the countryside evening.", "動物(昆虫)", "500"),
    ("cicada chorus", "多数のセミが同時に鳴き交わし、辺り一帯が音で満たされる現象。日本の夏を象徴する音風景でもある。セミの大合唱。", "名詞句", "The cicada chorus in midsummer can be so loud that it drowns out ordinary conversation outdoors.", "動物(昆虫)", "550"),
    ("cicada killer", "北米などに生息する大型のハチの一種で、セミを毒針で麻痺させて巣穴に運び、幼虫の餌とする。セミを狩る大型の狩りバチ(セミバチ)。", "名詞句", "A cicada killer will sting and paralyze a cicada before dragging it back to an underground burrow.", "動物(昆虫)", "600"),
]


def main() -> None:
    with db() as conn:
        existing = set()
        for r in conn.execute("SELECT english FROM words").fetchall():
            existing.add(r["english"].lower())
        inserted = 0
        skipped = 0
        for english, japanese, pos, example, domain, level in WORDS:
            if english.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (english, japanese, pos, example, domain, level),
            )
            existing.add(english.lower())
            inserted += 1
        print("inserted=" + str(inserted) + " skipped=" + str(skipped))


if __name__ == "__main__":
    main()
