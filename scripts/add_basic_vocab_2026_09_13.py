# ruff: noqa: E501
"""基礎語彙ドメインの追加分(2026-09-13・authored by Claude)。

前回セッションで下書きした約145語がスクラッチパッド(セッション間で消える
一時領域)にしか保存されておらず失われたため、本セッションでリポジトリ内
ファイルとして作り直したもの。基礎語彙ドメインは level<500 の語が141語
しかなく(既存793語中)、初級〜初中級学習者(TOEIC 300〜490程度)が実際に
出会うのに欠けている日常語(具体物の名詞、基本動詞、基本形容詞、基本副詞・
前置詞・接続詞、家族・食べ物・自然の語彙など)を補うために作成した。

事前に `SELECT english FROM words`(全ドメイン、15,000語超)と
`SELECT english FROM words WHERE domain='基礎語彙'` の両方を確認し、
重複しない語のみを選定済み。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_basic_vocab_2026_09_13.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- level 300: 最も基礎的な日常語 ---
    ("table", "テーブル、机", "名詞", "There is a book on the table.", "基礎語彙", "300"),
    ("chair", "椅子", "名詞", "Please have a seat on that chair.", "基礎語彙", "300"),
    ("cup", "カップ、(取っ手付きの)コップ", "名詞", "He poured hot coffee into the cup.", "基礎語彙", "300"),
    ("bed", "ベッド", "名詞", "The children were already in bed by nine o'clock.", "基礎語彙", "300"),
    ("door", "ドア、扉", "名詞", "Someone knocked on the door.", "基礎語彙", "300"),
    ("window", "窓", "名詞", "She opened the window to let in some fresh air.", "基礎語彙", "300"),
    ("big", "大きい", "形容詞", "They live in a big house near the park.", "基礎語彙", "300"),
    ("small", "小さい", "形容詞", "We rented a small car for the trip.", "基礎語彙", "300"),
    ("hot", "熱い、暑い", "形容詞", "Be careful, the soup is very hot.", "基礎語彙", "300"),
    ("cold", "冷たい、寒い", "形容詞・名詞", "It's too cold to go outside without a coat.", "基礎語彙", "300"),
    # --- level 350: 基本動詞・基本形容詞 ---
    ("eat", "食べる", "動詞", "We usually eat dinner at seven.", "基礎語彙", "350"),
    ("run", "走る、経営する", "動詞", "He runs five kilometers every morning.", "基礎語彙", "350"),
    ("sleep", "眠る、睡眠", "動詞・名詞", "I didn't sleep well last night.", "基礎語彙", "350"),
    ("sit", "座る", "動詞", "Please sit down and make yourself comfortable.", "基礎語彙", "350"),
    ("stand", "立つ", "動詞", "The old man was standing at the bus stop.", "基礎語彙", "350"),
    ("open", "開ける、開いている", "動詞・形容詞", "Could you open the window a little?", "基礎語彙", "350"),
    ("close", "閉める、閉じている", "動詞・形容詞", "Please close the door when you leave.", "基礎語彙", "350"),
    ("buy", "買う", "動詞", "I need to buy some milk on the way home.", "基礎語彙", "350"),
    ("old", "古い、年をとった", "形容詞", "This is the oldest building in the city.", "基礎語彙", "350"),
    ("new", "新しい", "形容詞", "She just moved into a new apartment.", "基礎語彙", "350"),
    ("long", "長い", "形容詞・副詞", "It's a long way from here to the station.", "基礎語彙", "350"),
    ("short", "短い、背が低い", "形容詞", "We only have a short break between classes.", "基礎語彙", "350"),
    ("happy", "幸せな", "形容詞", "She looked really happy when she heard the news.", "基礎語彙", "350"),
    ("sad", "悲しい", "形容詞", "He felt sad when his best friend moved away.", "基礎語彙", "350"),
    ("box", "箱", "名詞", "She put all the old photos in a cardboard box.", "基礎語彙", "350"),
    ("bag", "かばん、袋", "名詞", "He forgot his bag on the train.", "基礎語彙", "350"),
    # --- level 400: 自然 ---
    ("sun", "太陽", "名詞", "The sun rises in the east.", "基礎語彙", "400"),
    ("moon", "月", "名詞", "A full moon was shining over the lake.", "基礎語彙", "400"),
    ("sky", "空", "名詞", "The sky turned orange as the sun went down.", "基礎語彙", "400"),
    ("rain", "雨", "名詞・動詞", "It started to rain just as we left the house.", "基礎語彙", "400"),
    ("snow", "雪", "名詞・動詞", "The mountains were covered with snow.", "基礎語彙", "400"),
    ("wind", "風", "名詞", "A strong wind blew all the leaves off the tree.", "基礎語彙", "400"),
    ("river", "川", "名詞", "They fish in the river every weekend.", "基礎語彙", "400"),
    ("lake", "湖", "名詞", "We rented a small boat and rowed across the lake.", "基礎語彙", "400"),
    ("mountain", "山", "名詞", "They spent the weekend hiking in the mountains.", "基礎語彙", "400"),
    ("forest", "森", "名詞", "A narrow path led deep into the forest.", "基礎語彙", "400"),
    ("island", "島", "名詞", "The only way to reach the island is by boat.", "基礎語彙", "400"),
    ("desert", "砂漠", "名詞", "Very little rain falls in the desert.", "基礎語彙", "400"),
    # --- level 400: 食べ物 ---
    ("bread", "パン", "名詞", "She bought a fresh loaf of bread from the bakery.", "基礎語彙", "400"),
    ("butter", "バター", "名詞", "Spread some butter on the toast.", "基礎語彙", "400"),
    ("cheese", "チーズ", "名詞", "This pizza has a lot of cheese on it.", "基礎語彙", "400"),
    ("milk", "牛乳", "名詞・動詞", "Could you buy a carton of milk on your way home?", "基礎語彙", "400"),
    ("egg", "卵", "名詞", "She fried two eggs for breakfast.", "基礎語彙", "400"),
    ("meat", "肉", "名詞", "He doesn't eat meat anymore.", "基礎語彙", "400"),
    ("soup", "スープ", "名詞", "She made a pot of vegetable soup for dinner.", "基礎語彙", "400"),
    ("salad", "サラダ", "名詞", "I'll just have a salad for lunch today.", "基礎語彙", "400"),
    ("sandwich", "サンドイッチ", "名詞", "He made a sandwich with cheese and ham.", "基礎語彙", "400"),
    ("snack", "軽食、おやつ", "名詞・動詞", "The kids had a snack after school.", "基礎語彙", "400"),
    ("breakfast", "朝食", "名詞", "What did you have for breakfast this morning?", "基礎語彙", "400"),
    ("lunch", "昼食", "名詞", "Let's have lunch together sometime this week.", "基礎語彙", "400"),
    ("dinner", "夕食", "名詞", "We're having pasta for dinner tonight.", "基礎語彙", "400"),
    ("spoon", "スプーン", "名詞", "He stirred his coffee with a spoon.", "基礎語彙", "400"),
    # --- level 400: 家族・人 ---
    ("parent", "親", "名詞", "Both of her parents work at the same hospital.", "基礎語彙", "400"),
    ("cousin", "いとこ", "名詞", "My cousin is coming to visit us next month.", "基礎語彙", "400"),
    ("aunt", "おば", "名詞", "My aunt lives just down the street from us.", "基礎語彙", "400"),
    ("uncle", "おじ", "名詞", "My uncle taught me how to fish when I was young.", "基礎語彙", "400"),
    ("nephew", "甥", "名詞", "My sister's son, my nephew, just turned ten.", "基礎語彙", "400"),
    ("niece", "姪", "名詞", "I'm taking my niece to the zoo this Saturday.", "基礎語彙", "400"),
    ("neighbor", "隣人", "名詞", "Our neighbor kindly watered our plants while we were away.", "基礎語彙", "400"),
    ("guest", "客", "名詞", "We're expecting ten guests for the party tonight.", "基礎語彙", "400"),
    ("husband", "夫", "名詞", "Her husband works as an engineer downtown.", "基礎語彙", "400"),
    ("wife", "妻", "名詞", "His wife is a teacher at the local elementary school.", "基礎語彙", "400"),
    # --- level 400: 基本動詞 ---
    ("drink", "飲む", "動詞・名詞", "Would you like something to drink?", "基礎語彙", "400"),
    ("wash", "洗う", "動詞", "Don't forget to wash your hands before dinner.", "基礎語彙", "400"),
    ("push", "押す", "動詞・名詞", "Push the door open; it's not locked.", "基礎語彙", "400"),
    ("pull", "引く", "動詞", "Pull the rope as hard as you can.", "基礎語彙", "400"),
    ("catch", "つかまえる", "動詞", "Try to catch the ball with both hands.", "基礎語彙", "400"),
    ("hold", "持つ、開催する", "動詞", "Could you hold this bag for a second?", "基礎語彙", "400"),
    ("break", "壊す、休憩", "動詞・名詞", "Be careful not to break the glass.", "基礎語彙", "400"),
    ("cut", "切る", "動詞・名詞", "She cut the cake into eight equal pieces.", "基礎語彙", "400"),
    ("drive", "運転する", "動詞", "She drives to work every day.", "基礎語彙", "400"),
    ("ride", "乗る", "動詞・名詞", "He rides his bike to school every morning.", "基礎語彙", "400"),
    ("sing", "歌う", "動詞", "She loves to sing in the shower.", "基礎語彙", "400"),
    ("hug", "抱きしめる", "動詞・名詞", "She gave her son a big hug before he left.", "基礎語彙", "400"),
    # --- level 400: 基本形容詞 ---
    ("clean", "きれいな、掃除する", "形容詞・動詞", "Please keep your room clean.", "基礎語彙", "400"),
    ("dry", "乾いた", "形容詞・動詞", "Make sure your hair is completely dry before you go outside.", "基礎語彙", "400"),
    ("wet", "濡れた", "形容詞・動詞", "Don't sit down, the paint is still wet.", "基礎語彙", "400"),
    ("dark", "暗い", "形容詞・名詞", "It gets dark very early in winter.", "基礎語彙", "400"),
    ("bright", "明るい", "形容詞", "The kitchen is very bright in the morning sun.", "基礎語彙", "400"),
    ("quiet", "静かな", "形容詞", "Please be quiet in the library.", "基礎語彙", "400"),
    ("busy", "忙しい", "形容詞", "I'm too busy to talk right now.", "基礎語彙", "400"),
    ("free", "自由な、無料の", "形容詞・動詞", "Are you free this weekend?", "基礎語彙", "400"),
    # --- level 400: 前置詞 ---
    ("above", "〜の上に", "前置詞・副詞", "The plane flew above the clouds.", "基礎語彙", "400"),
    ("below", "〜の下に", "前置詞・副詞", "The temperature dropped below zero last night.", "基礎語彙", "400"),
    ("behind", "〜の後ろに", "前置詞・副詞", "The car parked right behind ours.", "基礎語彙", "400"),
    ("between", "〜の間に", "前置詞", "She sat between her two brothers.", "基礎語彙", "400"),
    ("through", "〜を通って", "前置詞・副詞", "We drove through the tunnel in just a few minutes.", "基礎語彙", "400"),
    ("near", "〜の近くに", "前置詞・形容詞・副詞", "The hotel is very near the airport.", "基礎語彙", "400"),
    # --- level 450: 自然・地形 ---
    ("storm", "嵐", "名詞", "A storm is expected to hit the coast tonight.", "基礎語彙", "450"),
    ("fog", "霧", "名詞", "Thick fog covered the entire valley this morning.", "基礎語彙", "450"),
    ("ice", "氷", "名詞", "Would you like some ice in your drink?", "基礎語彙", "450"),
    ("beach", "浜辺", "名詞", "We spent the whole afternoon relaxing on the beach.", "基礎語彙", "450"),
    ("sand", "砂", "名詞", "The children played happily in the sand.", "基礎語彙", "450"),
    ("mud", "泥", "名詞", "His boots were completely covered in mud.", "基礎語彙", "450"),
    ("hill", "丘", "名詞", "There's a great view from the top of that hill.", "基礎語彙", "450"),
    ("stone", "石", "名詞", "He skipped a flat stone across the lake.", "基礎語彙", "450"),
    # --- level 450: 食べ物・身近な物 ---
    ("pepper", "こしょう", "名詞", "Add a little salt and pepper to taste.", "基礎語彙", "450"),
    ("sauce", "ソース", "名詞", "This pasta comes with a rich tomato sauce.", "基礎語彙", "450"),
    ("flavor", "味、風味", "名詞", "This ice cream comes in ten different flavors.", "基礎語彙", "450"),
    ("meal", "食事", "名詞", "This is the best meal I've had in weeks.", "基礎語彙", "450"),
    ("bowl", "ボウル", "名詞", "She mixed the flour and eggs in a large bowl.", "基礎語彙", "450"),
    ("plate", "皿", "名詞", "He put a slice of cake on each plate.", "基礎語彙", "450"),
    ("blanket", "毛布", "名詞・動詞", "She pulled the blanket up to keep warm.", "基礎語彙", "450"),
    ("bottle", "瓶、ボトル", "名詞", "He filled the bottle with cold water.", "基礎語彙", "450"),
    ("curtain", "カーテン", "名詞", "She opened the curtains to let the sunlight in.", "基礎語彙", "450"),
    ("drawer", "引き出し", "名詞", "He keeps his socks in the top drawer.", "基礎語彙", "450"),
    # --- level 450: 家族・人 ---
    ("sibling", "きょうだい", "名詞", "She is the only one without any siblings.", "基礎語彙", "450"),
    ("stranger", "見知らぬ人", "名詞", "A stranger asked me for directions to the station.", "基礎語彙", "450"),
    ("couple", "カップル、2、3の", "名詞", "A young couple was walking hand in hand along the beach.", "基礎語彙", "450"),
    ("grandparent", "祖父母", "名詞", "My grandparents live in a small town by the sea.", "基礎語彙", "450"),
    # --- level 450: 動詞 ---
    ("promise", "約束する", "動詞・名詞", "He promised to call her as soon as he arrived.", "基礎語彙", "450"),
    ("protect", "守る", "動詞", "Wearing a helmet helps protect your head.", "基礎語彙", "450"),
    ("escape", "逃げる", "動詞・名詞", "The prisoner tried to escape but was quickly caught.", "基礎語彙", "450"),
    ("search", "探す", "動詞・名詞", "They searched the whole house for the missing keys.", "基礎語彙", "450"),
    ("rescue", "救助する", "動詞・名詞", "Firefighters rescued the cat from the tall tree.", "基礎語彙", "450"),
    ("defend", "守る、防御する", "動詞", "The team defended their lead until the very end.", "基礎語彙", "450"),
    ("attack", "攻撃する", "動詞・名詞", "The soldiers were ordered to attack at dawn.", "基礎語彙", "450"),
    ("invent", "発明する", "動詞", "Who invented the telephone?", "基礎語彙", "450"),
    ("repair", "修理する", "動詞・名詞", "It took the mechanic two hours to repair the car.", "基礎語彙", "450"),
    ("forgive", "許す", "動詞", "She finally forgave her brother for the argument.", "基礎語彙", "450"),
    ("praise", "褒める", "動詞・名詞", "The teacher praised the students for their hard work.", "基礎語彙", "450"),
    ("warn", "警告する", "動詞", "The sign warns drivers about the sharp curve ahead.", "基礎語彙", "450"),
    ("greet", "あいさつする", "動詞", "She greeted every guest with a warm smile.", "基礎語彙", "450"),
    ("welcome", "歓迎する", "動詞・形容詞・名詞", "They welcomed us warmly into their home.", "基礎語彙", "450"),
    ("celebrate", "祝う", "動詞", "We celebrated her birthday with a big cake.", "基礎語彙", "450"),
    ("argue", "議論する、口論する", "動詞", "The two brothers argued about who would drive.", "基礎語彙", "450"),
    ("blame", "責める", "動詞・名詞", "Don't blame yourself for what happened.", "基礎語彙", "450"),
    ("chase", "追いかける", "動詞・名詞", "The dog chased the ball across the yard.", "基礎語彙", "450"),
    # --- level 450: 感情・性格の形容詞 ---
    ("jealous", "嫉妬した", "形容詞", "He felt a little jealous of his friend's new car.", "基礎語彙", "450"),
    ("curious", "好奇心の強い", "形容詞", "The curious child kept asking why the sky is blue.", "基礎語彙", "450"),
    ("impatient", "我慢できない", "形容詞", "She grew impatient waiting in the long line.", "基礎語彙", "450"),
    ("ashamed", "恥ずかしく思って", "形容詞", "He felt ashamed of how he had treated his friend.", "基礎語彙", "450"),
    ("lonely", "孤独な", "形容詞", "He felt lonely after moving to a new city.", "基礎語彙", "450"),
    ("relaxed", "リラックスした", "形容詞", "She looked completely relaxed on vacation.", "基礎語彙", "450"),
    ("brave", "勇敢な", "形容詞", "It was brave of her to speak up in front of everyone.", "基礎語彙", "450"),
    ("shy", "内気な", "形容詞", "He was too shy to introduce himself to the new students.", "基礎語彙", "450"),
    ("honest", "正直な", "形容詞", "Please be honest with me about how you feel.", "基礎語彙", "450"),
    ("cruel", "残酷な", "形容詞", "It would be cruel to leave the dog outside in this weather.", "基礎語彙", "450"),
    # --- level 450: つなぎ言葉 ---
    ("furthermore", "さらに", "副詞", "The plan is expensive; furthermore, it will take years to complete.", "基礎語彙", "450"),
    ("besides", "〜に加えて", "前置詞・副詞", "Besides English, she speaks French and Spanish.", "基礎語彙", "450"),
    ("particularly", "特に", "副詞", "It's particularly cold this week.", "基礎語彙", "450"),
    ("currently", "現在", "副詞", "She is currently working on a new project.", "基礎語彙", "450"),
    ("previously", "以前に", "副詞", "She had previously worked as a nurse for ten years.", "基礎語彙", "450"),
    ("occasionally", "時々", "副詞", "We occasionally go out for dinner on weekdays.", "基礎語彙", "450"),
    ("thus", "このように、従って", "副詞", "The bridge was closed, and thus we had to take a longer route.", "基礎語彙", "450"),
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
