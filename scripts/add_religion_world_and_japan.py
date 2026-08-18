# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""「宗教」ドメインの拡充 + 新設「宗教（日本）」ドメインの投入(2026-08-18)。

ユーザー要望:「人文の宗教を 宗教と 宗教（日本）で分けたい」
「単なる宗教はキリスト教の原罪とか、キリスト教およびキリスト教以外に
おいても主なものを充実させてください。日本人の教養および外国にいって
こまらない教養としての英語です」
「日本は神社仏閣山岳信仰八百万の神他 全国各地の主な宗教（アイヌも含む）
注 教材として無難なところをいきたいので最近の新興宗教は含まない」

- 「宗教」(既存112語): キリスト教の基礎教養語彙(原罪・十戒・旧約/新約聖書・
  カトリック/プロテスタント/正教会・待降節/四旬節等)と、宗教横断の一般語彙
  (世俗・迷信・一神教/多神教等)を補強。既存の112語は世界の主要宗教
  (キリスト教/イスラム教/ユダヤ教/仏教/ヒンドゥー教/シク教等)を広く
  カバー済みのため、そこと重複しない「一般教養として欠けていた基礎語」に
  絞った。
- 「宗教（日本）」(新設): 神道(神社・鳥居・神・お祓い・しめ縄・絵馬・
  おみくじ・お守り・神楽等)、日本の仏教(寺・仏像・線香・仏壇・禅・数珠・
  初詣・法要等)、山岳信仰(修験道・山伏・霊山・滝行等)、八百万の神/
  アニミズム的な自然信仰、そして地域信仰としてアイヌ(カムイ等)・
  琉球/沖縄(御嶽・ノロ等)を収録。新興宗教は意図的に除外。
  既存の「宗教」ドメインにあった torii/kami は日本特有語のためこちらへ
  移設済み(本スクリプト実行前に手動UPDATE済み)。
- フレーズは「宗教（日本）」シーンで、神社仏閣を訪れる際の作法・外国人に
  日本の宗教文化を説明する場面を中心に収録(taxonomy.pyにも新規登録)。

No AI calls — 単語・フレーズとも直接手書きでSQLiteへ投入。既存語との重複は
english(小文字)で判定してスキップ(同綴り別義語は意図的に無視して投入する
設計 — 例: 「宗教」ドメインには既に医療分野の"temple"[こめかみ]がある
ため、仏教寺院の意味は"Buddhist temple"という複合語で投入し衝突を回避)。

Run:  python scripts/add_religion_world_and_japan.py
      python scripts/add_religion_world_and_japan.py --missing-words   # report only
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- 宗教(世界の宗教・一般教養) ---------------------------------------------
# english, japanese, part_of_speech, example, domain, level
RELIGION_WORLD: list[tuple[str, str, str, str, str, str]] = [
    ("cross", "十字架", "名詞", "She wears a small gold cross around her neck.", "宗教", "350"),
    ("Bible", "聖書", "名詞", "He reads a passage from the Bible every morning.", "宗教", "400"),
    ("heaven", "天国", "名詞", "In many religions, the good are believed to go to heaven.", "宗教", "400"),
    ("angel", "天使", "名詞", "The painting shows an angel watching over the city.", "宗教", "400"),
    ("devil", "悪魔", "名詞", "The devil is often depicted as a tempter in folklore.", "宗教", "450"),
    ("miracle", "奇跡", "名詞", "Believers described the recovery as a miracle.", "宗教", "450"),
    ("Christmas", "クリスマス", "名詞", "Christmas is celebrated on December 25th in most Christian countries.", "宗教", "300"),
    ("Easter", "復活祭・イースター", "名詞", "Easter marks the resurrection of Jesus in Christian belief.", "宗教", "400"),
    ("Old Testament", "旧約聖書", "名詞", "The Old Testament is shared scripture for Jews and Christians.", "宗教", "500"),
    ("New Testament", "新約聖書", "名詞", "The New Testament records the life and teachings of Jesus.", "宗教", "500"),
    ("Genesis", "創世記(旧約聖書の最初の書)", "名詞", "Genesis describes the creation of the world.", "宗教", "600"),
    ("Exodus", "出エジプト記(旧約聖書)", "名詞", "Exodus tells the story of the Israelites leaving Egypt.", "宗教", "650"),
    ("original sin", "原罪", "名詞", "In Christian theology, original sin is inherited from Adam and Eve.", "宗教", "550"),
    ("Ten Commandments", "十戒", "名詞", "The Ten Commandments are central to Jewish and Christian ethics.", "宗教", "550"),
    ("Pope", "ローマ教皇", "名詞", "The Pope leads the Roman Catholic Church.", "宗教", "500"),
    ("Vatican", "バチカン(教皇庁)", "名詞", "The Vatican is the spiritual center of the Catholic Church.", "宗教", "550"),
    ("Catholic", "カトリック(教徒)の", "形容詞", "She was raised in a devout Catholic family.", "宗教", "500"),
    ("Protestant", "プロテスタント(新教徒)の", "形容詞", "Protestant churches split from the Catholic Church in the Reformation.", "宗教", "500"),
    ("Orthodox", "正教会の", "形容詞", "Orthodox Christianity is dominant in Russia and Greece.", "宗教", "600"),
    ("denomination", "(キリスト教などの)教派", "名詞", "There are hundreds of Protestant denominations worldwide.", "宗教", "650"),
    ("sect", "宗派・分派", "名詞", "The group split off from the main sect over doctrine.", "宗教", "600"),
    ("confession", "告解・懺悔", "名詞", "Catholics traditionally make confession to a priest.", "宗教", "650"),
    ("crucifix", "十字架像", "名詞", "A wooden crucifix hung above the altar.", "宗教", "700"),
    ("purgatory", "煉獄", "名詞", "In Catholic teaching, purgatory is a state of purification before heaven.", "宗教", "750"),
    ("heresy", "異端", "名詞", "His teachings were condemned as heresy by the church.", "宗教", "750"),
    ("Lent", "四旬節(レント)", "名詞", "Many Christians give up something for Lent.", "宗教", "700"),
    ("Advent", "待降節(アドベント)", "名詞", "Advent calendars count down the days before Christmas.", "宗教", "750"),
    ("Nativity", "キリスト降誕(の場面)", "名詞", "The church put up a Nativity scene for Christmas.", "宗教", "700"),
    ("manger", "(家畜の)飼い葉桶", "名詞", "According to the story, Jesus was born in a manger.", "宗教", "750"),
    ("secular", "世俗の・宗教と無関係の", "形容詞", "Japan is a largely secular society with religious customs.", "宗教", "500"),
    ("pagan", "異教徒(の)", "名詞", "Many pagan traditions were absorbed into later festivals.", "宗教", "600"),
    ("monotheism", "一神教", "名詞", "Judaism, Christianity, and Islam are all forms of monotheism.", "宗教", "650"),
    ("polytheism", "多神教", "名詞", "Ancient Greek religion was a form of polytheism.", "宗教", "650"),
    ("folklore", "民間伝承", "名詞", "The story has survived for centuries in local folklore.", "宗教", "500"),
    ("superstition", "迷信", "名詞", "Avoiding the number 13 is a common superstition.", "宗教", "500"),
    ("omen", "前兆・兆し", "名詞", "A black cat crossing your path is seen as a bad omen in some cultures.", "宗教", "650"),
    ("providence", "(神の)摂理", "名詞", "She thanked providence for her narrow escape.", "宗教", "750"),
    ("vow", "誓い", "名詞", "The monks took a vow of silence.", "宗教", "500"),
    ("oath", "誓約", "名詞", "He swore a sacred oath before the altar.", "宗教", "550"),
    ("icon", "イコン(聖画像)", "名詞", "The chapel walls are covered with painted icons.", "宗教", "650"),
    ("relic", "聖遺物", "名詞", "The cathedral houses a relic believed to be a saint's bone.", "宗教", "700"),
    ("sacrifice", "生贄・供犠", "名詞", "Ancient rituals sometimes included animal sacrifice.", "宗教", "500"),
    ("offering", "供物・捧げ物", "名詞", "Worshippers left offerings of fruit at the altar.", "宗教", "550"),
    ("veneration", "崇敬", "名詞", "Saints are held in great veneration by Catholics.", "宗教", "750"),
    ("goddess", "女神", "名詞", "Athena was worshipped as the goddess of wisdom.", "宗教", "400"),
]

# --- 宗教（日本）: 神道・日本の仏教・山岳信仰・八百万の神・地域信仰 -----------
RELIGION_JAPAN: list[tuple[str, str, str, str, str, str]] = [
    # 神道
    ("Shinto", "神道", "名詞", "Shinto is Japan's indigenous religion, centered on kami.", "宗教（日本）", "400"),
    ("Shinto shrine", "神社", "名詞", "A red torii gate marks the entrance to the Shinto shrine.", "宗教（日本）", "400"),
    ("Shinto priest", "神主・神職", "名詞", "The Shinto priest performed a purification ritual for the new building.", "宗教（日本）", "550"),
    ("purification rite", "お祓い・清めの儀式", "名詞", "Visitors wash their hands and mouth in a purification rite before entering.", "宗教（日本）", "600"),
    ("shimenawa", "しめ縄(神域を示す注連縄)", "名詞", "A thick shimenawa rope hangs across the shrine gate.", "宗教（日本）", "750"),
    ("ema", "絵馬(願い事を書く木の板)", "名詞", "Visitors write their wishes on a small wooden ema.", "宗教（日本）", "700"),
    ("omikuji", "おみくじ(運勢を占う紙)", "名詞", "She drew an omikuji and hoped for good fortune.", "宗教（日本）", "700"),
    ("omamori", "お守り", "名詞", "He bought an omamori for traffic safety.", "宗教（日本）", "650"),
    ("kagura", "神楽(神道の神聖な舞)", "名詞", "The shrine hosts a kagura performance during the autumn festival.", "宗教（日本）", "750"),
    ("kamidana", "神棚(家庭用の神道の祭壇)", "名詞", "The shop keeps a small kamidana above the entrance for good fortune.", "宗教（日本）", "750"),
    ("ujigami", "氏神(地域の守護神)", "名詞", "Every neighborhood traditionally has its own ujigami.", "宗教（日本）", "750"),
    ("nature deity", "自然神", "名詞", "Many nature deities are worshipped as guardians of mountains and rivers.", "宗教（日本）", "600"),
    ("yaoyorozu no kami", "八百万の神(あらゆるものに宿るとされる無数の神々)", "名詞", "Yaoyorozu no kami reflects the belief that spirits dwell in nature itself.", "宗教（日本）", "700"),
    ("sacred tree", "御神木", "名詞", "A rope is tied around the sacred tree to mark it as holy.", "宗教（日本）", "600"),
    ("sacred rock", "磐座(神が宿るとされる岩)", "名詞", "The sacred rock behind the shrine is said to house a kami.", "宗教（日本）", "750"),
    ("household deity", "家の神", "名詞", "Offerings are placed daily before the household deity.", "宗教（日本）", "650"),
    # 日本の仏教
    ("Buddhist temple", "寺・寺院", "名詞", "The Buddhist temple has stood in the mountains for centuries.", "宗教（日本）", "350"),
    ("pagoda", "五重塔などの仏塔", "名詞", "The five-story pagoda is the temple's most famous landmark.", "宗教（日本）", "550"),
    ("Buddha statue", "仏像", "名詞", "A giant bronze Buddha statue sits at the center of the temple grounds.", "宗教（日本）", "500"),
    ("incense", "お香・線香", "名詞", "Visitors light incense before praying at the temple.", "宗教（日本）", "450"),
    ("temple bell", "梵鐘", "名詞", "The temple bell is rung 108 times on New Year's Eve.", "宗教（日本）", "650"),
    ("butsudan", "仏壇(家庭用の仏教の祭壇)", "名詞", "The family gathers in front of the butsudan on the anniversary of a death.", "宗教（日本）", "700"),
    ("Zen", "禅", "名詞", "Zen emphasizes meditation as a path to enlightenment.", "宗教（日本）", "400"),
    ("zazen", "座禅(禅の座って行う瞑想)", "名詞", "Visitors can try zazen at the temple on weekend mornings.", "宗教（日本）", "650"),
    ("prayer beads", "数珠", "名詞", "He holds prayer beads while chanting a sutra.", "宗教（日本）", "650"),
    ("hatsumode", "初詣(新年最初の参拝)", "名詞", "Millions of people make hatsumode visits in the first days of January.", "宗教（日本）", "600"),
    ("memorial service", "法要", "名詞", "The family held a memorial service on the third anniversary of his death.", "宗教（日本）", "700"),
    ("kaimyo", "戒名(死後に授けられる仏教の名)", "名詞", "A Buddhist priest chose a kaimyo for the deceased.", "宗教（日本）", "800"),
    ("ancestor veneration", "祖先崇拝", "名詞", "Ancestor veneration remains an important part of Japanese family life.", "宗教（日本）", "650"),
    # 山岳信仰
    ("mountain worship", "山岳信仰", "名詞", "Mountain worship treats certain peaks as the dwelling places of gods.", "宗教（日本）", "600"),
    ("sacred mountain", "霊山", "名詞", "Mount Fuji has long been treated as a sacred mountain.", "宗教（日本）", "600"),
    ("Shugendo", "修験道(山岳修行を中心とする信仰)", "名詞", "Shugendo blends Shinto and Buddhist practices around mountain training.", "宗教（日本）", "800"),
    ("yamabushi", "山伏(修験道の修行者)", "名詞", "A yamabushi in white robes led the group up the sacred trail.", "宗教（日本）", "800"),
    ("ascetic practice", "修行", "名詞", "Monks undergo years of ascetic practice before ordination.", "宗教（日本）", "650"),
    ("waterfall meditation", "滝行(滝に打たれて行う修行)", "名詞", "He tried waterfall meditation as part of a traditional training retreat.", "宗教（日本）", "800"),
    ("sacred site", "霊場", "名詞", "The mountain trail links eighty-eight sacred sites.", "宗教（日本）", "700"),
    # アイヌ・琉球など地域の信仰
    ("Ainu", "アイヌ(民族)", "名詞", "The Ainu are the indigenous people of Hokkaido and northern Japan.", "宗教（日本）", "500"),
    ("Ainu religion", "アイヌの信仰", "名詞", "Ainu religion centers on spirits called kamuy that dwell in nature.", "宗教（日本）", "700"),
    ("kamuy", "カムイ(アイヌの神霊)", "名詞", "In Ainu belief, a kamuy can take the form of a bear, an owl, or fire itself.", "宗教（日本）", "750"),
    ("oral tradition", "口承伝承", "名詞", "Ainu epics were passed down through oral tradition rather than writing.", "宗教（日本）", "650"),
    ("guardian spirit", "守護霊", "名詞", "A guardian spirit was believed to watch over each household.", "宗教（日本）", "600"),
    ("utaki", "御嶽(琉球の聖地)", "名詞", "Villagers still visit the utaki to pray for a good harvest.", "宗教（日本）", "800"),
    ("Ryukyuan religion", "琉球の信仰", "名詞", "Ryukyuan religion centers on female priestesses and sacred groves.", "宗教（日本）", "750"),
    ("noro", "ノロ(琉球の女性神官)", "名詞", "A noro leads the village's traditional prayer rituals.", "宗教（日本）", "850"),
]

# --- 宗教（日本）フレーズ: 神社仏閣での作法・外国人への説明 -------------------
PHRASES_JAPAN: list[tuple[str, str]] = [
    ("Bow once before passing through the torii gate.", "鳥居をくぐる前に一礼しましょう。"),
    ("Please walk on the side of the path, not the center.", "参道の中央ではなく端を歩いてください（中央は神様の通り道とされます）。"),
    ("Wash your hands and rinse your mouth at the purification fountain.", "手水舎で手を洗い、口をすすいでください。"),
    ("Bow twice, clap twice, then bow once more.", "二礼二拍手一礼の作法で参拝します。"),
    ("Make a small offering before you pray.", "お参りの前に小さなお賽銭をあげましょう。"),
    ("You can write your wish on an ema and hang it up.", "願い事を絵馬に書いて掛けることができます。"),
    ("If you draw a bad fortune, you can tie it to the rack instead of taking it home.", "凶が出たら持ち帰らずに結んでいく人も多いです。"),
    ("This omamori is said to bring good luck for traffic safety.", "このお守りは交通安全のご利益があるとされています。"),
    ("Please remove your shoes before entering the main hall.", "本堂に入る前に靴を脱いでください。"),
    ("Photography isn't allowed inside the temple's main hall.", "本堂の中は撮影禁止です。"),
    ("Ring the bell gently to greet the deity before you pray.", "参拝の前に鈴を軽く鳴らして神様に挨拶します。"),
    ("Many Japanese people visit both a shrine and a temple without seeing a conflict.", "多くの日本人は神社とお寺の両方にお参りしても矛盾を感じません。"),
    ("Shinto deals with this world, while Buddhism traditionally deals with the afterlife.", "神道はこの世を、仏教は伝統的にあの世を扱うとされます。"),
    ("Weddings are often Shinto-style, while funerals are usually Buddhist.", "結婚式は神前式が多く、葬式は仏式が多いです。"),
    ("We believe that spirits can dwell in mountains, trees, and even stones.", "山や木、石にも霊が宿ると考えられています。"),
    ("Mount Fuji has been worshipped as a sacred mountain for centuries.", "富士山は何世紀にもわたって霊山として信仰されてきました。"),
    ("The Ainu traditionally saw bears and owls as forms taken by kamuy.", "アイヌは伝統的にクマやフクロウをカムイの化身と見なしてきました。"),
    ("On New Year's, we make our first shrine visit of the year.", "お正月には初詣に行きます。"),
    ("Families gather at the family altar to honor their ancestors.", "家族は仏壇の前に集まり、先祖を敬います。"),
    ("The temple bell is rung 108 times to mark the New Year.", "除夜の鐘は新年を迎えるために108回鳴らされます。"),
]


def report_missing() -> None:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
    covered = {w[0].lower() for w in (RELIGION_WORLD + RELIGION_JAPAN)}
    missing = sorted(w for w in covered if w not in existing)
    print(f"words not yet covered ({len(missing)}): {', '.join(missing)}")


def main() -> int:
    if "--missing-words" in sys.argv:
        report_missing()
        return 0

    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        w_added = w_skipped = 0
        for en, ja, pos, ex, domain, level in RELIGION_WORLD + RELIGION_JAPAN:
            if en.lower() in w_existing:
                w_skipped += 1
                print(f"  skip (exists): {en}")
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
        for en, ja in PHRASES_JAPAN:
            if en.lower() in ph_existing:
                ph_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, ?)",
                (en, ja, "宗教（日本）"),
            )
            ph_existing.add(en.lower())
            ph_added += 1

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    with db() as conn:
        print(
            "宗教 total:",
            conn.execute(
                "SELECT COUNT(*) FROM words WHERE domain='宗教'"
            ).fetchone()[0],
            "| 宗教（日本） total:",
            conn.execute(
                "SELECT COUNT(*) FROM words WHERE domain='宗教（日本）'"
            ).fetchone()[0],
            "| 宗教（日本）phrases:",
            conn.execute(
                "SELECT COUNT(*) FROM phrases WHERE scene='宗教（日本）'"
            ).fetchone()[0],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
