# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""武道・格闘技(流派別)+日本文化(茶道・華道)+宗教（日本）(仏教宗派)の拡充
(2026-08-18)。

ユーザー要望:「スポーツを趣味・エンタメから独立させたので、武道・格闘技の
中の古典的な武道も充実させてください。ボクシング、柔道、剣道、忍術(充実
させてください。どこに入れるか検討してください)、合気道、その他いろいろ。
茶道・華道も充実させてください(趣味や文化に分類)。宗教（日本）の分野に
ついて、修験道の分類が適切か確認、仏教哲学・輪廻についても充実させて
ください」

- 「武道・格闘技」(既存28語、2026-08-18に趣味・エンタメからスポーツとして
  独立した際に流派を問わない汎用武道語彙のみ収録済み): 流派別の専門語彙が
  ゼロだったため、ボクシング・柔道・剣道・忍術・合気道・古武術(古流)の
  各流派specific語彙を追加。ボクシングのjab/hook/uppercutは既存DBに別義語
  (予防接種/曲のフック/既存の球技・アウトドアスポーツドメインのuppercut)
  として存在するため、意図的にsouthpaw/cross punch等の他の本格的な
  ボクシング語彙で代替(uppercutは再追加しない)。剣道のmen/kote/doは英単語
  として汎用すぎる/衝突する(men=manの複数形、do=助動詞)ため、
  "target area (men, kote, do)"の1語にまとめて解説する形にした。忍術は
  歴史上のスキルセットとして中立的に(暴力賛美を避けて)記述、既存の
  「忍者」(歴史ドメインの人物名詞)とは別物として追加。合気道の
  "harmony"は既存の音楽ドメインの"harmony"(和声)と衝突するため
  "spirit of harmony"として追加。judo throwの"throw"も既存の
  ゲーム・Discordドメインの別義語("throw"=形勢を台無しにする)と衝突する
  ため"judo throw"の複合語で追加。
- 「日本文化」(既存25語、価値観・社会慣習系語彙が中心で茶道・華道の
  具体語彙は皆無だった): 既存の"tea ceremony"(歴史ドメイン)・"ikebana"
  (芸術ドメイン)・"matcha"(和食ドメイン)はそのまま残し、道具(茶筅・茶杓・
  茶碗)・茶室での役割(亭主・客)・作法・侘び寂び・一期一会・「道」の概念・
  華道の流派(池坊)・非対称性の美意識等、より専門的な語彙を追加。
- 「宗教（日本）」(既存41語、2026-08-18新設・修験道は山岳信仰として正しく
  収録済みで移動不要): 日本の仏教宗派(浄土宗・日蓮宗・真言宗・天台宗・
  密教)と、既存の「宗教」ドメインにある汎用的な仏教概念(nirvana/dharma/
  sutra/impermanence/reincarnation等、宗派を問わない仏教哲学として既存)
  とは重複しない日本仏教特有の概念(阿弥陀仏・法華経・曼荼羅・公案・悟り
  (satori)・写経)を追加。

No AI calls — 単語・フレーズとも直接手書きでSQLiteへ投入。既存語との重複は
english(小文字)で判定してスキップ。

Run:  python scripts/add_martial_arts_tea_buddhism.py
      python scripts/add_martial_arts_tea_buddhism.py --missing-words   # report only
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- 武道・格闘技: ボクシング・柔道・剣道・忍術・合気道・古武術 --------------
# english, japanese, part_of_speech, example, domain, level
MARTIAL_ARTS: list[tuple[str, str, str, str, str, str]] = [
    # ボクシング
    ("southpaw", "サウスポー(右構えではなく左構えの選手)", "名詞", "The southpaw's unusual stance confused his orthodox opponent.", "武道・格闘技", "600"),
    ("cross punch", "クロス(利き手で相手を狙う直線的なパンチ)", "名詞", "He landed a hard cross punch that ended the round.", "武道・格闘技", "600"),
    ("ringside", "リングサイド(リング脇の特等席)", "名詞", "Fans paid a premium for ringside seats at the championship fight.", "武道・格闘技", "500"),
    ("split decision", "判定分かれ(僅差の判定勝ち)", "名詞", "The judges scored it a split decision after twelve close rounds.", "武道・格闘技", "700"),
    ("knockdown", "ノックダウン(打たれて倒れること)", "名詞", "A single knockdown in round three shifted the momentum of the fight.", "武道・格闘技", "600"),
    ("technical knockout", "テクニカルノックアウト(TKO)", "名詞", "The referee stopped the fight and declared a technical knockout in the fourth round.", "武道・格闘技", "650"),
    ("weight class", "階級(体重別の区分)", "名詞", "Boxers compete only against opponents in the same weight class.", "武道・格闘技", "550"),
    ("corner man", "コーナーマン(休憩中に選手を世話するスタッフ)", "名詞", "Between rounds, his corner man wiped his face and gave him instructions.", "武道・格闘技", "650"),
    # 柔道
    ("ippon", "一本(柔道で一撃勝ちとなる最高得点)", "名詞", "She won the match with a clean ippon less than a minute into the bout.", "武道・格闘技", "600"),
    ("waza-ari", "技あり(一本に次ぐ得点)", "名詞", "Two waza-ari scores used to combine into a single ippon under the old rules.", "武道・格闘技", "700"),
    ("osaekomi", "抑え込み(相手を一定時間押さえつける固め技)", "名詞", "He held his opponent down in osaekomi until the referee called time.", "武道・格闘技", "750"),
    ("randori", "乱取り(自由に技をかけ合う実戦形式の稽古)", "名詞", "Randori lets students test their techniques against a partner who is actually resisting.", "武道・格闘技", "650"),
    ("ukemi", "受け身(安全に転ぶための受け身の技術)", "名詞", "Beginners practice ukemi for weeks before they are allowed to try throws.", "武道・格闘技", "600"),
    ("judo throw", "柔道の投げ技", "名詞", "A well-timed judo throw can end a match in a matter of seconds.", "武道・格闘技", "550"),
    ("judogi", "柔道着", "名詞", "She tightened the belt of her judogi before stepping onto the mat.", "武道・格闘技", "500"),
    ("obi", "帯(柔道・空手などで使う帯)", "名詞", "His black obi showed years of dedicated training.", "武道・格闘技", "450"),
    ("tatami mat", "畳(柔道場の床に敷く敷物)", "名詞", "Judo matches are held on thick tatami mats to cushion falls.", "武道・格闘技", "450"),
    # 剣道
    ("shinai", "竹刀(剣道で使う竹製の刀)", "名詞", "Practitioners strike each other with a shinai instead of a real blade.", "武道・格闘技", "550"),
    ("bogu", "防具(剣道で身につける一式の防護具)", "名詞", "Putting on the full bogu takes a few minutes before practice begins.", "武道・格闘技", "650"),
    ("target area (men, kote, do)", "面・小手・胴などの有効打突部位", "名詞", "In kendo, points are scored only by striking specific target areas such as men, kote, and do.", "武道・格闘技", "700"),
    ("kiai", "気合(打つ瞬間に発する気迫のこもった掛け声)", "名詞", "A sharp kiai accompanies every strike in kendo.", "武道・格闘技", "600"),
    ("zanshin", "残心(技を決めた後も油断しない心構え)", "名詞", "Zanshin means staying alert and ready even after a strike lands successfully.", "武道・格闘技", "800"),
    # 忍術(歴史的なスキルセットとして中立的に記述)
    ("ninjutsu", "忍術(忍者が用いた技術体系)", "名詞", "Ninjutsu combined stealth, disguise, and survival skills developed in feudal Japan.", "武道・格闘技", "600"),
    ("stealth", "隠密性・気づかれずに行動すること", "名詞", "Ninja relied on stealth to gather information without being detected.", "武道・格闘技", "500"),
    ("infiltration", "潜入", "名詞", "Historical accounts describe ninja infiltration of enemy castles under cover of night.", "武道・格闘技", "650"),
    ("disguise", "変装", "名詞", "A skilled ninja could use disguise to pass as a merchant or a traveling monk.", "武道・格闘技", "500"),
    ("shuriken", "手裏剣(手投げの小型武器)", "名詞", "The shuriken was often used as a distraction rather than as a primary weapon.", "武道・格闘技", "600"),
    ("kunai", "クナイ(元は農具・道具だった小型の刃物)", "名詞", "The kunai began as a farming and digging tool before becoming linked to ninja.", "武道・格闘技", "700"),
    ("evasion", "回避・逃走の技術", "名詞", "Evasion techniques allowed a ninja to escape a situation without ever fighting.", "武道・格闘技", "600"),
    # 合気道
    ("blending technique", "合わせ技(相手の力の流れに合わせて制する技術)", "名詞", "Aikido's blending technique redirects an attacker's force instead of meeting it head-on.", "武道・格闘技", "700"),
    ("wrist lock", "手首の関節技", "名詞", "A controlled wrist lock can subdue an opponent without causing serious injury.", "武道・格闘技", "600"),
    ("redirect", "(力の向きを)そらす・転じる", "動詞", "Instead of blocking the punch directly, she redirected its force to the side.", "武道・格闘技", "550"),
    ("spirit of harmony", "和の精神(争わず調和を重んじる合気道の理念)", "名詞", "Aikido's philosophy centers on the spirit of harmony rather than on defeating an opponent.", "武道・格闘技", "750"),
    # 古武術(古流)
    ("koryu", "古流(近代以前から伝わる伝統的な武術の流派)", "名詞", "Some koryu schools trace their techniques back more than four hundred years.", "武道・格闘技", "750"),
    ("bujutsu", "武術(実戦での役立ちを目的とした伝統的な武芸)", "名詞", "Bujutsu originally referred to the practical combat skills used by samurai.", "武道・格闘技", "700"),
    ("naginata", "薙刀(長い柄のついた刃物武器)", "名詞", "The naginata was used by samurai in battle and later became associated with women of samurai households.", "武道・格闘技", "700"),
    ("bo staff", "棒(武術で使う長い木の棒)", "名詞", "Students practice striking and blocking with a wooden bo staff.", "武道・格闘技", "600"),
    ("iaido", "居合道(刀を素早く抜いて型を行い納める武道)", "名詞", "Iaido focuses on the precise draw, cut, and re-sheathing of a sword.", "武道・格闘技", "750"),
    ("kobudo", "古武道(沖縄などに伝わる伝統的な武器術)", "名詞", "Okinawan kobudo includes weapons developed from everyday farm tools.", "武道・格闘技", "800"),
    ("bushido", "武士道(武士が重んじた倫理規範)", "名詞", "Bushido stressed loyalty, honor, and self-discipline as core values for the samurai class.", "武道・格闘技", "650"),
]

# --- 日本文化: 茶道(道具・作法・美意識)・華道 ---------------------------------
TEA_AND_IKEBANA: list[tuple[str, str, str, str, str, str]] = [
    ("tea room", "茶室(茶道を行うための部屋)", "名詞", "The tea ceremony takes place in a small, quiet room called a tea room.", "日本文化", "550"),
    ("chasen", "茶筅(抹茶を点てるための竹製の道具)", "名詞", "The host whisks the matcha into a froth using a bamboo chasen.", "日本文化", "650"),
    ("chashaku", "茶杓(抹茶をすくうための竹製のさじ)", "名詞", "The host measures the matcha into the bowl with a chashaku.", "日本文化", "750"),
    ("chawan", "茶碗(茶道で抹茶を飲むための碗)", "名詞", "Each guest admires the chawan before drinking the tea inside it.", "日本文化", "650"),
    ("tea ceremony host", "亭主(茶道で客をもてなす主人役)", "名詞", "The tea ceremony host prepares each bowl of matcha by hand for the guests.", "日本文化", "600"),
    ("tea ceremony guest", "客(茶道でもてなしを受ける側)", "名詞", "As the tea ceremony guest, you bow before receiving the bowl of tea.", "日本文化", "600"),
    ("tea ceremony etiquette", "茶道の作法", "名詞", "Learning tea ceremony etiquette can take years of practice and quiet observation.", "日本文化", "650"),
    ("wabi-sabi", "侘び寂び(不完全さや儚さの中に美を見出す美意識)", "名詞", "Wabi-sabi finds quiet beauty in things that are simple, worn, or imperfect.", "日本文化", "700"),
    ("ichigo ichie", "一期一会(一生に一度の出会いとして大切にする心構え)", "名詞", "Ichigo ichie reminds participants to treasure each tea gathering as a once-in-a-lifetime meeting.", "日本文化", "800"),
    ("the Way (do)", "道(茶道・華道・剣道などに共通する「道」の概念)", "名詞", "The suffix -do, meaning 'the Way,' links tea ceremony, flower arrangement, and martial arts as lifelong paths of practice.", "日本文化", "750"),
    ("flower arrangement", "生け花・華道(花を美しく生ける技芸)", "名詞", "Flower arrangement developed in Japan into the refined art known as ikebana.", "日本文化", "500"),
    ("seasonal branch", "季節の枝(生け花で季節感を表すために使う枝)", "名詞", "Ikebana arrangements often include a seasonal branch to reflect the time of year.", "日本文化", "650"),
    ("Ikenobo", "池坊(最も古い生け花の流派)", "名詞", "Ikenobo is considered the oldest school of ikebana, founded centuries ago in Kyoto.", "日本文化", "800"),
    ("asymmetry", "非対称性(生け花で重んじられる美の原則)", "名詞", "Ikebana values asymmetry over perfect symmetry, aiming for a natural sense of balance.", "日本文化", "700"),
    ("vase", "花瓶(生け花で使う器)", "名詞", "Every ikebana arrangement is carefully composed within a simple vase.", "日本文化", "400"),
    ("tokonoma", "床の間(掛け軸や生け花を飾る座敷の飾り床)", "名詞", "A seasonal flower arrangement is often displayed in the tokonoma alcove.", "日本文化", "750"),
]

# --- 宗教（日本）: 日本仏教の宗派・特有の仏教哲学 -----------------------------
BUDDHISM_JAPAN: list[tuple[str, str, str, str, str, str]] = [
    ("Jodo", "浄土宗(阿弥陀仏の救いを説く日本仏教の宗派)", "名詞", "Jodo, or Pure Land Buddhism, teaches that chanting Amida Buddha's name leads to rebirth in paradise.", "宗教（日本）", "700"),
    ("Nichiren Buddhism", "日蓮宗(法華経を中心とする日本仏教の宗派)", "名詞", "Nichiren Buddhism centers its practice on chanting the title of the Lotus Sutra.", "宗教（日本）", "750"),
    ("Shingon Buddhism", "真言宗(密教の要素を取り入れた日本仏教の宗派)", "名詞", "Shingon Buddhism incorporates esoteric rituals, mantras, and mandalas into its practice.", "宗教（日本）", "800"),
    ("Tendai Buddhism", "天台宗(法華経を重んじ比叡山を本山とする日本仏教の宗派)", "名詞", "Tendai Buddhism, centered on Mount Hiei, later gave rise to several other Japanese Buddhist schools.", "宗教（日本）", "800"),
    ("esoteric Buddhism", "密教(秘儀的な儀式や象徴を重視する仏教の一派)", "名詞", "Esoteric Buddhism uses secret rituals, mantras, and symbolic art to transmit its teachings.", "宗教（日本）", "800"),
    ("Amida Buddha", "阿弥陀仏(浄土宗・浄土真宗で信仰される仏)", "名詞", "Followers of Pure Land Buddhism pray to Amida Buddha for rebirth in the Pure Land.", "宗教（日本）", "750"),
    ("Lotus Sutra", "法華経(日蓮宗・天台宗で重視される経典)", "名詞", "The Lotus Sutra is central to the teachings of both Tendai and Nichiren Buddhism.", "宗教（日本）", "800"),
    ("mandala", "曼荼羅(密教で用いられる象徴的な図像)", "名詞", "A mandala represents the universe in symbolic, geometric form.", "宗教（日本）", "750"),
    ("koan", "公案(禅における問答形式の修行課題)", "名詞", "Zen students meditate on a koan, a paradoxical question with no single logical answer.", "宗教（日本）", "800"),
    ("satori", "悟り(禅における瞬間的な目覚めや気づき)", "名詞", "Satori refers to the sudden flash of insight that Zen practice seeks to cultivate.", "宗教（日本）", "800"),
    ("shakyo", "写経(経典を書き写す修行)", "名詞", "Copying sutras by hand, called shakyo, is practiced as a form of moving meditation.", "宗教（日本）", "850"),
]

# --- フレーズ: 道場での作法・茶道華道の作法(既存登録済みシーンのみ使用) ------
PHRASES_BUDO: list[tuple[str, str]] = [
    ("Bow when you enter and leave the dojo.", "道場に入るときも出るときも一礼しましょう。"),
    ("Line up in order of rank before practice begins.", "稽古が始まる前に、段位の順に並びます。"),
    ("Always show respect to your training partner.", "稽古相手には常に敬意を払いましょう。"),
    ("Ninjutsu is studied today mainly as a historical martial art, not as a tool for violence.", "忍術は今日では主に歴史的な武術として学ばれており、暴力の道具としてではありません。"),
    ("Aikido techniques redirect an attacker's energy rather than opposing it head-on.", "合気道の技は、相手の力に真っ向から逆らうのではなく、その力の方向を転じます。"),
    ("A judo throw relies on timing and balance more than raw strength.", "柔道の投げ技は、力そのものよりもタイミングとバランスがものを言います。"),
    ("Even after landing a clean strike in kendo, keep your zanshin.", "剣道できれいに一本を決めた後も、残心を忘れないでください。"),
]

PHRASES_NIHONBUNKA: list[tuple[str, str]] = [
    ("Turn the tea bowl slightly before you drink from it.", "飲む前に茶碗を少し回します。"),
    ("It's polite to compliment the tea bowl before you start drinking.", "飲み始める前に茶碗を褒めるのが礼儀です。"),
    ("In ikebana, empty space is just as important as the flowers themselves.", "生け花では、花そのものと同じくらい余白(空間)も大切にされます。"),
    ("The suffix -do links tea ceremony, calligraphy, and martial arts as lifelong paths of practice.", "「道」という接尾辞は、茶道・書道・武道を、生涯かけて磨く『道』として結び付けています。"),
    ("Wabi-sabi finds quiet beauty in things that are simple, worn, or imperfect.", "侘び寂びは、簡素で使い込まれ、不完全なものの中に静かな美を見出します。"),
]

ALL_WORDS: list[tuple[str, str, str, str, str, str]] = (
    MARTIAL_ARTS + TEA_AND_IKEBANA + BUDDHISM_JAPAN
)
ALL_PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "武道・格闘技の英語": PHRASES_BUDO,
    "日本文化": PHRASES_NIHONBUNKA,
}


def report_missing() -> None:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
    covered = {w[0].lower() for w in ALL_WORDS}
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
        for en, ja, pos, ex, domain, level in ALL_WORDS:
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
        for scene, phrases in ALL_PHRASES_BY_SCENE.items():
            for en, ja in phrases:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    with db() as conn:
        print(
            "武道・格闘技 total:",
            conn.execute(
                "SELECT COUNT(*) FROM words WHERE domain='武道・格闘技'"
            ).fetchone()[0],
            "| 日本文化 total:",
            conn.execute(
                "SELECT COUNT(*) FROM words WHERE domain='日本文化'"
            ).fetchone()[0],
            "| 宗教（日本） total:",
            conn.execute(
                "SELECT COUNT(*) FROM words WHERE domain='宗教（日本）'"
            ).fetchone()[0],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
