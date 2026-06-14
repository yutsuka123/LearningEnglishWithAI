# ruff: noqa: E501  (data-heavy seed script)
"""Add genre vocabulary (with examples) across many domains, authored by
Claude — no app/OpenAI API calls.

Domains: SF / サスペンス / 恋愛 / 世界史 / 日本史 / 遊び / 動物 / 植物 / 料理 / 数学.
Plus a few conversational phrases for 恋愛 and 料理.

Run:  python scripts/add_genres.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, japanese, example) per domain.
WORDS_BY_DOMAIN: dict[str, list[tuple[str, str, str]]] = {
    "SF": [
        ("spaceship", "宇宙船", "The spaceship landed on Mars."),
        ("starship", "恒星間宇宙船", "The starship jumped to another system."),
        ("galaxy", "銀河", "There are billions of stars in our galaxy."),
        ("alien", "異星人", "The alien spoke in a strange language."),
        ("extraterrestrial", "地球外生命体", "They searched for extraterrestrial life."),
        ("android", "アンドロイド", "The android looked completely human."),
        ("cyborg", "サイボーグ", "Half-machine, he was a cyborg."),
        ("hyperspace", "超空間", "The ship vanished into hyperspace."),
        ("warp", "ワープする", "Engage the warp drive!"),
        ("teleport", "瞬間移動する", "She teleported across the room."),
        ("time travel", "タイムトラベル", "Time travel is a popular sci-fi theme."),
        ("parallel universe", "平行世界", "He slipped into a parallel universe."),
        ("dystopia", "ディストピア", "The novel depicts a grim dystopia."),
        ("utopia", "理想郷", "They dreamed of building a utopia."),
        ("mutant", "突然変異体", "Radiation created the mutant creatures."),
        ("clone", "クローン", "The clone shared his memories."),
        ("wormhole", "ワームホール", "A wormhole links distant galaxies."),
        ("asteroid", "小惑星", "The ship dodged the asteroid belt."),
        ("interstellar", "星間の", "They began an interstellar voyage."),
        ("terraform", "テラフォーミングする", "Engineers terraformed the barren planet."),
        ("force field", "力場", "A force field protected the base."),
        ("telepathy", "テレパシー", "They communicated by telepathy."),
        ("invasion", "侵略", "The alien invasion began at dawn."),
        ("apocalypse", "終末・黙示録", "The film is set after the apocalypse."),
        ("singularity", "技術的特異点", "Some fear the AI singularity."),
        ("exoskeleton", "外骨格(強化スーツ)", "The soldier wore a powered exoskeleton."),
        ("artificial intelligence", "人工知能", "The ship was run by an artificial intelligence."),
        ("laser", "レーザー", "He fired the laser cannon."),
        ("colony", "(宇宙の)入植地", "Humans built a colony on the moon."),
        ("robot", "ロボット", "The robot obeyed every command."),
    ],
    "サスペンス": [
        ("clue", "手がかり", "The detective found an important clue."),
        ("alibi", "アリバイ", "His alibi did not hold up."),
        ("motive", "動機", "The police searched for a motive."),
        ("culprit", "犯人", "The culprit was caught on camera."),
        ("victim", "被害者", "The victim was found unharmed."),
        ("murder", "殺人", "She was accused of murder."),
        ("homicide", "殺人(事件)", "Detectives from homicide arrived."),
        ("detective", "探偵・刑事", "The detective questioned everyone."),
        ("conspiracy", "陰謀", "They uncovered a vast conspiracy."),
        ("betrayal", "裏切り", "The story turns on a betrayal."),
        ("suspense", "サスペンス", "The film is full of suspense."),
        ("twist", "どんでん返し", "The ending has a shocking twist."),
        ("cliffhanger", "続きが気になる結末", "The episode ended on a cliffhanger."),
        ("red herring", "ミスリードの手がかり", "The clue was just a red herring."),
        ("interrogation", "尋問", "The interrogation lasted all night."),
        ("forensics", "科学捜査", "Forensics matched the DNA."),
        ("autopsy", "検死", "The autopsy revealed the cause of death."),
        ("fingerprint", "指紋", "They lifted a fingerprint from the glass."),
        ("surveillance", "監視", "He was under police surveillance."),
        ("undercover", "潜入の", "She worked undercover for months."),
        ("stalker", "ストーカー", "A stalker followed her home."),
        ("accomplice", "共犯者", "He had an accomplice in the heist."),
        ("cover-up", "隠蔽", "The scandal was a cover-up."),
        ("eyewitness", "目撃者", "An eyewitness described the suspect."),
        ("blackmail", "恐喝(する)", "He tried to blackmail the senator."),
        ("kidnapping", "誘拐", "The kidnapping shocked the town."),
        ("suspenseful", "はらはらさせる", "It was a suspenseful thriller."),
        ("whodunit", "犯人当て(推理もの)", "I love a good whodunit."),
        ("plot twist", "筋の急展開", "Nobody saw the plot twist coming."),
        ("evidence", "証拠", "There was no evidence at the scene."),
    ],
    "恋愛": [
        ("crush", "片思いの相手", "I have a crush on my classmate."),
        ("ask out", "デートに誘う", "He finally asked her out."),
        ("first date", "初デート", "We went to a cafe on our first date."),
        ("fall in love", "恋に落ちる", "They fell in love at first sight."),
        ("soulmate", "運命の人", "She felt he was her soulmate."),
        ("fiancé", "婚約者(男性)", "Her fiancé proposed last spring."),
        ("fiancée", "婚約者(女性)", "He introduced his fiancée to us."),
        ("engagement", "婚約", "They announced their engagement."),
        ("propose", "プロポーズする", "He proposed on the beach."),
        ("honeymoon", "新婚旅行", "They spent their honeymoon in Italy."),
        ("anniversary", "記念日", "We celebrate our anniversary every year."),
        ("affection", "愛情", "She showed great affection for him."),
        ("jealousy", "嫉妬", "Jealousy ruined their relationship."),
        ("breakup", "別れ", "The breakup was hard on both of them."),
        ("heartbreak", "失恋・心痛", "He never recovered from the heartbreak."),
        ("flirt", "いちゃつく・口説く", "He likes to flirt at parties."),
        ("romance", "ロマンス・恋愛", "Their romance lasted a lifetime."),
        ("blind date", "お見合いデート", "A friend set me up on a blind date."),
        ("long-distance", "遠距離(恋愛)の", "They kept a long-distance relationship."),
        ("commitment", "真剣な関係・献身", "He's afraid of commitment."),
        ("cheating", "浮気", "Cheating destroyed their marriage."),
        ("make up", "仲直りする", "They argued but made up quickly."),
        ("confess", "(愛を)告白する", "She confessed her feelings to him."),
        ("sweetheart", "恋人・最愛の人", "He called her his sweetheart."),
        ("courtship", "求愛", "Their courtship lasted two years."),
        ("newlyweds", "新婚夫婦", "The newlyweds moved into a new home."),
        ("chemistry", "(人との)相性", "They had instant chemistry."),
        ("infatuation", "のぼせ上がり", "It was just a passing infatuation."),
        ("ex", "元恋人", "She ran into her ex at the party."),
        ("affair", "不倫・情事", "The affair was kept secret."),
    ],
    "世界史": [
        ("empire", "帝国", "The Roman Empire ruled for centuries."),
        ("dynasty", "王朝", "The dynasty lasted three hundred years."),
        ("revolution", "革命", "The revolution overthrew the king."),
        ("renaissance", "ルネサンス", "Art flourished during the Renaissance."),
        ("civilization", "文明", "Ancient civilization arose by the river."),
        ("colony", "植民地", "The colony declared independence."),
        ("independence", "独立", "They fought for independence."),
        ("monarchy", "君主制", "The country abolished the monarchy."),
        ("republic", "共和国", "Rome became a republic."),
        ("emperor", "皇帝", "The emperor commanded a huge army."),
        ("conquest", "征服", "The conquest changed the map of Europe."),
        ("crusade", "十字軍", "Knights joined the crusade."),
        ("feudalism", "封建制", "Feudalism shaped medieval society."),
        ("pharaoh", "ファラオ", "The pharaoh was buried in a pyramid."),
        ("gladiator", "剣闘士", "Gladiators fought in the arena."),
        ("plague", "疫病", "The plague killed millions."),
        ("treaty", "条約", "Both sides signed a peace treaty."),
        ("alliance", "同盟", "They formed a military alliance."),
        ("colonialism", "植民地主義", "Colonialism reshaped the world."),
        ("industrial revolution", "産業革命", "The industrial revolution began in Britain."),
        ("slavery", "奴隷制", "Slavery was finally abolished."),
        ("reformation", "宗教改革", "The Reformation split the church."),
        ("antiquity", "古代", "These ruins date from antiquity."),
        ("medieval", "中世の", "The castle is a medieval fortress."),
        ("dictator", "独裁者", "The dictator seized absolute power."),
        ("armistice", "休戦", "An armistice ended the fighting."),
        ("colonist", "入植者", "The colonists settled the new land."),
        ("rebellion", "反乱", "The rebellion was crushed."),
        ("nobility", "貴族", "The nobility owned most of the land."),
        ("ancient", "古代の", "Ancient Egypt fascinates historians."),
    ],
    "日本史": [
        ("samurai", "侍", "The samurai served his lord faithfully."),
        ("shogun", "将軍", "The shogun ruled from Edo."),
        ("shogunate", "幕府", "The Tokugawa shogunate lasted 260 years."),
        ("daimyo", "大名", "Each daimyo controlled his own domain."),
        ("ninja", "忍者", "The ninja moved silently in the dark."),
        ("katana", "刀", "The samurai drew his katana."),
        ("warrior", "武士", "He trained as a warrior from childhood."),
        ("warlord", "武将", "The warlord united several provinces."),
        ("clan", "氏族・一族", "The two clans were bitter rivals."),
        ("vassal", "家臣", "The vassal swore loyalty to his lord."),
        ("national isolation", "鎖国", "Japan kept a policy of national isolation."),
        ("restoration", "(維新の)復古", "The Meiji Restoration modernized Japan."),
        ("unification", "統一", "He achieved the unification of Japan."),
        ("tea ceremony", "茶道", "The tea ceremony is a refined art."),
        ("geisha", "芸者", "The geisha performed a traditional dance."),
        ("sumo", "相撲", "Sumo is Japan's national sport."),
        ("peasant", "農民", "The peasants paid taxes in rice."),
        ("merchant", "商人", "Merchants grew wealthy in the cities."),
        ("feudal", "封建の", "Japan had a feudal society for centuries."),
        ("civil war", "内乱・戦国の戦", "The country was torn by civil war."),
        ("edict", "布告・令", "The shogun issued a strict edict."),
        ("castle", "城", "The lord built a mighty castle."),
        ("retainer", "家臣・従者", "His loyal retainers followed him."),
        ("envoy", "使節", "An envoy was sent to China."),
        ("scroll", "巻物", "The history was recorded on a scroll."),
        ("imperial court", "朝廷", "The imperial court was in Kyoto."),
        ("conscription", "徴兵", "Modern Japan introduced conscription."),
        ("province", "国・地方", "He governed a distant province."),
        ("tribute", "貢ぎ物", "Smaller states paid tribute."),
        ("dynastic", "王朝の", "Power passed along dynastic lines."),
    ],
    "遊び": [
        ("hide-and-seek", "かくれんぼ", "The kids played hide-and-seek in the park."),
        ("tag", "鬼ごっこ", "Let's play tag after school."),
        ("hopscotch", "石けり(けんけんぱ)", "She drew a hopscotch grid with chalk."),
        ("jump rope", "縄跳び", "He can jump rope fifty times."),
        ("rock-paper-scissors", "じゃんけん", "We chose by rock-paper-scissors."),
        ("tug of war", "綱引き", "Our class won the tug of war."),
        ("marbles", "ビー玉遊び", "The boys played marbles in the dirt."),
        ("spinning top", "こま", "He spun the spinning top on the floor."),
        ("kite", "凧", "We flew a kite at the beach."),
        ("swing", "ブランコ", "The girl swung high on the swing."),
        ("slide", "すべり台", "Kids lined up for the slide."),
        ("seesaw", "シーソー", "They went up and down on the seesaw."),
        ("sandbox", "砂場", "Toddlers played in the sandbox."),
        ("jungle gym", "ジャングルジム", "He climbed to the top of the jungle gym."),
        ("leapfrog", "馬跳び", "The children played leapfrog."),
        ("dodgeball", "ドッジボール", "Dodgeball is popular at recess."),
        ("building blocks", "積み木", "The baby stacked the building blocks."),
        ("treasure hunt", "宝探し", "We organized a treasure hunt."),
        ("musical chairs", "椅子取りゲーム", "They played musical chairs at the party."),
        ("hopscotch grid", "けんけんぱの枠", "She hopped along the hopscotch grid."),
        ("board game", "ボードゲーム", "We played a board game on a rainy day."),
        ("card game", "カードゲーム", "Let's play a card game."),
        ("puzzle", "パズル", "She finished the jigsaw puzzle."),
        ("doll", "人形", "The girl dressed her doll."),
        ("teddy bear", "テディベア", "He sleeps with his teddy bear."),
        ("playground", "遊び場・公園", "The playground was full of children."),
        ("recess", "休み時間", "We play outside during recess."),
        ("piggyback", "おんぶ", "Dad gave her a piggyback ride."),
        ("blindman's buff", "目隠し鬼", "They played blindman's buff."),
        ("paper plane", "紙飛行機", "He folded a paper plane."),
    ],
    "動物": [
        ("mammal", "哺乳類", "A whale is a mammal, not a fish."),
        ("reptile", "爬虫類", "A snake is a reptile."),
        ("amphibian", "両生類", "A frog is an amphibian."),
        ("insect", "昆虫", "An ant is a tiny insect."),
        ("predator", "捕食者", "The lion is a fearsome predator."),
        ("prey", "獲物", "The rabbit became the eagle's prey."),
        ("herbivore", "草食動物", "A cow is a herbivore."),
        ("carnivore", "肉食動物", "A tiger is a carnivore."),
        ("omnivore", "雑食動物", "Bears are omnivores."),
        ("habitat", "生息地", "Pollution destroys their habitat."),
        ("species", "種", "This species is found only here."),
        ("endangered", "絶滅危惧の", "Pandas are an endangered species."),
        ("extinct", "絶滅した", "Dinosaurs are extinct."),
        ("migration", "渡り・移動", "Birds begin their migration in autumn."),
        ("hibernate", "冬眠する", "Bears hibernate through the winter."),
        ("nocturnal", "夜行性の", "Owls are nocturnal hunters."),
        ("livestock", "家畜", "The farmer raises livestock."),
        ("wildlife", "野生動物", "The park protects local wildlife."),
        ("fur", "毛皮", "The fox has thick winter fur."),
        ("claw", "かぎ爪", "The cat sharpened its claws."),
        ("fang", "牙", "The wolf bared its fangs."),
        ("hoof", "ひづめ", "The horse's hoof needs trimming."),
        ("beak", "くちばし", "The bird cracked the seed with its beak."),
        ("herd", "(牛などの)群れ", "A herd of cattle grazed nearby."),
        ("flock", "(鳥・羊の)群れ", "A flock of geese flew south."),
        ("swarm", "(虫の)群れ", "A swarm of bees filled the air."),
        ("tame", "飼いならす", "It took weeks to tame the horse."),
        ("breed", "品種・繁殖する", "They breed dogs on the farm."),
        ("mane", "たてがみ", "The lion shook its golden mane."),
        ("venom", "毒", "The snake injects venom through its fangs."),
    ],
    "植物": [
        ("stem", "茎", "Water travels up the stem."),
        ("leaf", "葉", "The leaf turned red in autumn."),
        ("petal", "花びら", "A petal fell from the rose."),
        ("blossom", "花(が咲く)", "The cherry trees are in blossom."),
        ("bud", "つぼみ", "The buds opened in spring."),
        ("seed", "種", "Plant the seed in moist soil."),
        ("pollen", "花粉", "Bees carry pollen between flowers."),
        ("photosynthesis", "光合成", "Plants make food by photosynthesis."),
        ("chlorophyll", "葉緑素", "Chlorophyll makes leaves green."),
        ("fertilizer", "肥料", "Add fertilizer to help it grow."),
        ("wither", "枯れる・しおれる", "The flowers withered in the heat."),
        ("thorn", "とげ", "The rose has sharp thorns."),
        ("vine", "つる", "A vine climbed up the wall."),
        ("shrub", "低木", "She trimmed the garden shrubs."),
        ("evergreen", "常緑樹", "Pines are evergreen trees."),
        ("deciduous", "落葉性の", "Maples are deciduous trees."),
        ("sap", "樹液", "Maple sap is boiled into syrup."),
        ("bark", "樹皮", "The bark of the oak is rough."),
        ("trunk", "幹", "The old tree has a thick trunk."),
        ("germinate", "発芽する", "The seeds germinate in a week."),
        ("moss", "苔", "Moss covered the damp stones."),
        ("fern", "シダ", "Ferns grow in the shade."),
        ("vegetation", "植生", "Dense vegetation covered the hill."),
        ("orchard", "果樹園", "We picked apples in the orchard."),
        ("perennial", "多年草", "This perennial blooms every year."),
        ("nectar", "蜜", "Butterflies sip nectar from flowers."),
        ("root", "根", "The roots reach deep into the soil."),
        ("sapling", "若木・苗木", "He planted a sapling in the yard."),
        ("blossom out", "花開く", "The garden blossomed out in May."),
        ("foliage", "葉・茂み", "The autumn foliage was beautiful."),
    ],
    "料理": [
        ("recipe", "レシピ", "Let me give you the recipe."),
        ("ingredient", "材料", "Mix all the ingredients in a bowl."),
        ("season", "味付けする", "Season the soup with salt and pepper."),
        ("simmer", "弱火で煮る", "Let it simmer for ten minutes."),
        ("boil", "ゆでる・沸かす", "Boil the pasta for nine minutes."),
        ("fry", "炒める・揚げる", "Fry the onions until golden."),
        ("deep-fry", "揚げる", "Deep-fry the chicken until crispy."),
        ("grill", "(網で)焼く", "Grill the fish over charcoal."),
        ("roast", "(オーブンで)焼く", "Roast the chicken for an hour."),
        ("bake", "(パン・菓子を)焼く", "Bake the cake at 180 degrees."),
        ("steam", "蒸す", "Steam the vegetables until tender."),
        ("stir-fry", "炒める", "Stir-fry the beef quickly."),
        ("marinate", "漬け込む", "Marinate the meat overnight."),
        ("chop", "刻む", "Chop the onions finely."),
        ("dice", "さいの目に切る", "Dice the carrots into small cubes."),
        ("mince", "みじん切りにする", "Mince the garlic."),
        ("peel", "皮をむく", "Peel the potatoes first."),
        ("knead", "(生地を)こねる", "Knead the dough for ten minutes."),
        ("whisk", "泡立てる", "Whisk the eggs until fluffy."),
        ("garnish", "飾り付ける", "Garnish the plate with parsley."),
        ("preheat", "予熱する", "Preheat the oven to 200 degrees."),
        ("ferment", "発酵させる", "Let the dough ferment overnight."),
        ("sauté", "ソテーする", "Sauté the mushrooms in butter."),
        ("mash", "つぶす", "Mash the potatoes with milk."),
        ("drain", "水気を切る", "Drain the pasta in a colander."),
        ("dough", "生地", "Roll out the dough thinly."),
        ("batter", "衣・(液状)生地", "Dip the shrimp in the batter."),
        ("broth", "だし・スープ", "Simmer the bones to make broth."),
        ("seasoning", "調味料", "It needs a little more seasoning."),
        ("tender", "柔らかい", "Cook until the meat is tender."),
    ],
    "数学": [
        ("addition", "足し算", "Addition is the first thing children learn."),
        ("subtraction", "引き算", "Subtraction takes one number from another."),
        ("multiplication", "掛け算", "Learn the multiplication table by heart."),
        ("division", "割り算", "Division splits a number into parts."),
        ("equation", "方程式", "Solve the equation for x."),
        ("fraction", "分数", "One half is a simple fraction."),
        ("decimal", "小数", "Round the decimal to two places."),
        ("percentage", "百分率", "What percentage got the answer right?"),
        ("quotient", "商", "The quotient of 10 by 2 is 5."),
        ("remainder", "余り", "7 divided by 2 leaves a remainder of 1."),
        ("integer", "整数", "Five is an integer."),
        ("prime number", "素数", "Seven is a prime number."),
        ("square root", "平方根", "The square root of 9 is 3."),
        ("exponent", "指数", "Two to the exponent three is eight."),
        ("algebra", "代数", "We study algebra in junior high."),
        ("geometry", "幾何学", "Geometry deals with shapes and angles."),
        ("calculus", "微積分", "Calculus is used in physics."),
        ("trigonometry", "三角法", "Trigonometry relates angles and sides."),
        ("derivative", "微分", "Find the derivative of the function."),
        ("integral", "積分", "Compute the integral over the interval."),
        ("angle", "角度", "The angle measures 90 degrees."),
        ("triangle", "三角形", "A triangle has three sides."),
        ("radius", "半径", "The radius is half the diameter."),
        ("diameter", "直径", "Measure the diameter of the circle."),
        ("circumference", "円周", "The circumference is pi times the diameter."),
        ("area", "面積", "Calculate the area of the rectangle."),
        ("volume", "体積", "The volume of the cube is 27."),
        ("probability", "確率", "The probability of heads is one half."),
        ("average", "平均", "The average of 2 and 4 is 3."),
        ("variable", "変数", "Let x be the unknown variable."),
    ],
}

# Conversational phrases for 恋愛 / 料理.
PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "恋愛": [
        ("Will you go out with me?", "付き合ってくれませんか？"),
        ("I have a crush on you.", "あなたに片思いしています。"),
        ("Will you marry me?", "結婚してくれますか？"),
        ("I've fallen for you.", "あなたに惚れてしまいました。"),
        ("Are you seeing anyone?", "付き合っている人はいますか？"),
        ("Let's just be friends.", "友達でいましょう。"),
        ("It's not you, it's me.", "あなたのせいじゃない、私のせいなの。"),
        ("I can't stop thinking about you.", "あなたのことが頭から離れません。"),
        ("You mean the world to me.", "あなたは私のすべてです。"),
        ("Let's make it official.", "正式に付き合いましょう。"),
        ("I think we should break up.", "別れた方がいいと思う。"),
        ("I'm head over heels for her.", "彼女に夢中なんだ。"),
        ("Do you want to grab dinner sometime?", "いつか食事でもどう？"),
        ("We have great chemistry.", "私たち、とても相性がいいね。"),
        ("I'll always be by your side.", "ずっとそばにいるよ。"),
    ],
    "料理": [
        ("Let me give you the recipe.", "レシピを教えますね。"),
        ("Season it to taste.", "お好みで味付けしてください。"),
        ("Let it simmer for ten minutes.", "10分ほど弱火で煮込んでください。"),
        ("Preheat the oven to 180 degrees.", "オーブンを180度に予熱してください。"),
        ("Chop the onions finely.", "玉ねぎを細かく刻んでください。"),
        ("Bring the water to a boil.", "お湯を沸騰させてください。"),
        ("Add a pinch of salt.", "塩をひとつまみ加えてください。"),
        ("Stir until smooth.", "なめらかになるまで混ぜてください。"),
        ("It needs a bit more seasoning.", "もう少し味付けが必要です。"),
        ("Let it cool before serving.", "出す前に冷ましてください。"),
        ("Whisk the eggs well.", "卵をよく溶きほぐしてください。"),
        ("Cook until the meat is tender.", "肉が柔らかくなるまで火を通してください。"),
        ("Drain the pasta.", "パスタの水気を切ってください。"),
        ("Marinate the chicken overnight.", "鶏肉を一晩漬け込んでください。"),
        ("Garnish with fresh herbs.", "新鮮なハーブを添えてください。"),
    ],
}


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }

        w_added = w_skipped = 0
        per_domain: dict[str, int] = {}
        for domain, items in WORDS_BY_DOMAIN.items():
            for en, ja, ex in items:
                if en.lower() in w_existing:
                    conn.execute(
                        "UPDATE words SET example = ? "
                        "WHERE LOWER(english) = LOWER(?) AND COALESCE(example, '') = ''",
                        (ex, en),
                    )
                    w_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, ja, "", ex, domain, "700"),
                )
                w_existing.add(en.lower())
                w_added += 1
                per_domain[domain] = per_domain.get(domain, 0) + 1

        ph_added = ph_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"  per domain: {per_domain}")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    with db() as conn:
        print(
            "totals -> phrases:",
            conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
            "words:",
            conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
