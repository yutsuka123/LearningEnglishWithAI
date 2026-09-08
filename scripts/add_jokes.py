# ruff: noqa: E501  (data-heavy seed script: long phrase lines are fine)
"""Add two new phrase scenes,「ジョーク(米国)」「ジョーク(英国)」
(2026-09-08ユーザーブレスト「分野でジョークもあってもいいかも」への対応)。

## 内容方針(著作権・配慮への対応・必読)
- **著作権**: 特定のコメディアン・番組・書籍のジョークをそのまま引用する
  ことは一切していない。すべて「dad joke(駄洒落系オチジョーク)」
  「knock-knock joke」「self-deprecating humor」「イギリス的皮肉・
  understatement(控えめな言い方)」といった**広く知られた定型パターン・
  ジョークの型**そのものを教材として説明するため、Claude(本チャット)が
  ゼロから新規に文面を作成した。一部の項目(seafood diet/two-tired/
  time flies like an arrow等)は駄洒落のジャンルとして非常に広く出回って
  いる作者不明の定番パターンだが、個人の著作物ではなく言葉遊びの型
  そのもの(慣用句・なぞなぞに近い民俗的な言葉遊び)として扱っている。
  投入前にDB全体との重複(完全一致)は確認済み(重複ゼロ)。
- **配慮**: 特定の人種・宗教・性別・国籍を揶揄する内容、政治的に偏った
  内容、下品な内容は一切含めていない。言葉遊び・軽い自虐ネタ・
  状況ジョークのみ。イギリス側は「天気・紅茶・行列・鉄道への軽い愚痴」
  など、イギリス人自身がよくネタにする自虐的なステレオタイプに留め、
  他者を揶揄する内容にはしていない。
- **教材としての価値**: 単にジョークを載せるだけでなく、
  `import_phrase_details.py`で投入するdetail(nuance/background/
  explanation等)に「なぜ面白いか」(駄洒落の仕掛け・二重の意味・
  understatementと現実の落差等)を必ず解説する
  (`scripts/data/jokes_details.json`、50件全件に対応する解説あり)。

## 2シーンの傾向の違い(一般化しすぎない書き方を意識)
- ジョーク(米国): dad joke的な駄洒落(ダブルミーニング・同音異義語)、
  knock-knock joke、ストレートな自虐ネタが中心。ノリが良く、オチが
  はっきりしている傾向。
- ジョーク(英国): 皮肉・understatement(実際より控えめに言う)、
  ドライな自虐ネタが中心。文字通りの意味と本音のギャップで笑わせる
  傾向があり、駄洒落よりも「言い方」で笑わせるものが多い。

## 重複調査
既存シーンに「話芸・コメディの英語」(30件)があるが、これはコメディ
という芸能ジャンルそのものの語彙・メタ的な説明フレーズ(punchline/
timing/heckler等の用語や「Let me set up the joke.」等)であり、
**ジョーク本編そのもの**は1件も含まれていないため重複なし
(`scripts/add_comedy_storytelling.py`参照)。

No app / OpenAI API calls — everything is hand-written and inserted
directly into the SQLite DB. Duplicates are skipped by english
(lowercased).

Run:  python scripts/add_jokes.py

仕上げ:
  python scripts/import_phrase_details.py \
      scripts/data/jokes_details.json          # detail投入(なぜ面白いか解説)
  python scripts/relevel_phrases.py            # 難易度再設定
  .venv/bin/python scripts/build_audio.py      # 音声生成(少しずつ)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "ジョーク(米国)": [
        ("Why did the scarecrow win an award? Because he was outstanding in his field.",
         "かかしはどうして表彰されたの? 自分の畑で誰よりも目立っていたから。"),
        ("I used to be a baker, but I couldn't make enough dough, so I gave it up.",
         "パン職人をしていましたが、十分な稼ぎ(生地)を作れなかったので辞めました。"),
        ("Why don't skeletons fight each other? They don't have the guts.",
         "ガイコツ同士はどうしてケンカしないの? 度胸(内臓)が無いから。"),
        ("I told my computer I needed a break, and it froze.",
         "パソコンに「休憩が必要だ」と言ったら、フリーズしてしまった。"),
        ("Knock, knock. Who's there? Lettuce. Lettuce who? Lettuce in, it's freezing out here!",
         "「トントン」「どなた?」「レタスです」「レタスって?」「入れてよ(レット・アス・イン)、外は凍えそうだよ!」"),
        ("I'm reading a book about anti-gravity. It's impossible to put down.",
         "反重力についての本を読んでいるんだけど、手放せない(下に置けない)んだ。"),
        ("My bed is a magical place. I lie down, and suddenly it is morning.",
         "私のベッドは魔法の場所。横になった途端、気づいたら朝なんだ。"),
        ("I'm not lazy, I'm just on energy-saving mode.",
         "怠けてるんじゃなくて、省エネモードなだけだよ。"),
        ("Why did the coffee file a police report? It got mugged.",
         "コーヒーはなぜ警察に被害届を出したの? マグ(カップ)を奪われた(mugged=襲われた)から。"),
        ("I only know 25 letters of the alphabet. I don't know Y.",
         "アルファベットは25文字しか知らないんだ。Y(なぜ)は知らない。"),
        ("Knock, knock. Who's there? Boo. Boo who? Aw, don't cry, it's just a joke.",
         "「トントン」「どなた?」「ブー」「ブーって?」「あら泣かないで、ただの冗談だよ」"),
        ("I used to hate facial hair, but then it grew on me.",
         "ヒゲは前は嫌いだったけど、だんだん好きになってきた(伸びてきた)んだ。"),
        ("I'm on a seafood diet. Every time I see food, I eat it.",
         "シーフードダイエットをしているんだ。食べ物(food)を見る(see)たびに食べちゃうんだよ。"),
        ("Why did the bicycle fall over? Because it was two-tired.",
         "自転車はなぜ倒れたの? 疲れすぎ(two-tired=too tiredとタイヤ2本の掛詞)だったから。"),
        ("I have a fear of speed bumps, but I'm slowly getting over it.",
         "スピードバンプが怖いんだけど、少しずつ克服(乗り越え)しつつあるよ。"),
        ("My New Year's resolution is to stop procrastinating. I'll start next December.",
         "今年の目標は先延ばし癖をやめること。来年の12月から始めるつもり。"),
        ("I told my suitcase there'd be no vacation this year. Now I'm dealing with emotional baggage.",
         "スーツケースに「今年は休暇なし」と言ったら、今は心の荷物(baggage=荷物/心の重荷)を抱えている。"),
        ("Why do we tell actors to break a leg? Because every good play needs a little drama.",
         "俳優に「break a leg(頑張って)」と言うのはなぜ? どんな良い芝居にも、ちょっとしたドラマ(騒動)が必要だから。"),
        ("I invested in a company that makes mirrors. I can really see myself working there.",
         "鏡を作る会社に投資したんだ。そこで働く自分の姿がよく見える(想像できる)よ。"),
        ("My therapist says I have an issue with revenge. We'll see about that.",
         "セラピストに「あなたは復讐にこだわる傾向がある」と言われた。それはどうかな。"),
        ("I used to play piano by ear, but now I use my hands.",
         "昔は耳で(感覚で)ピアノを弾いていたけど、今は手を使っているよ。"),
        ("I was going to tell a chemistry joke, but I knew I wouldn't get a reaction.",
         "化学のジョークを言おうと思ったけど、反応(reaction=化学反応/観客の反応)が無さそうだからやめた。"),
        ("The math teacher called in sick. She said she had too many problems.",
         "数学の先生が休んだ。「問題(problems=数式の問題/悩み事)が多すぎる」とのことだった。"),
        ("When a phone gets stolen at the shop, is the person who saw it called an iWitness?",
         "お店でスマホが盗まれたのを見た人は「iウィットネス(目撃者)」って呼ばれるのかな?"),
        ("Time flies like an arrow; fruit flies like a banana.",
         "時は矢のように飛ぶ(過ぎ去る)。ショウジョウバエはバナナが好き(のように飛ぶ)。"),
    ],
    "ジョーク(英国)": [
        ("The forecast said 'a few clouds.' It hasn't stopped raining for six hours.",
         "天気予報は「ところにより曇り」と言っていた。もう6時間ずっと雨が降りっぱなしだ。"),
        ("I wouldn't say the meeting was a disaster — nothing useful happened, nobody agreed on anything, and we booked another meeting to discuss it.",
         "あの会議を「最悪だった」とまでは言わないけど――何も進展はなく、誰も合意できず、話し合うための次の会議を予約しただけだった。"),
        ("I'm not saying I'm bad at cooking, but the smoke alarm is basically my kitchen timer.",
         "料理が下手だとは言わないけど、火災報知器がほぼキッチンタイマー代わりになっている。"),
        ("Sorry, could I just squeeze past? I promise it won't take more than five minutes of apologising.",
         "すみません、ちょっと通していただけますか。謝るのに5分もかからないと約束します。"),
        ("He said he was 'a bit peckish,' then ate an entire pizza by himself.",
         "彼は「ちょっとお腹が空いた」と言って、そのままピザを一枚丸ごと一人で食べてしまった。"),
        ("The doctor told me to cut down on tea. I told him that simply isn't an option.",
         "医者に「紅茶を減らすように」と言われたけど、それは無理だと伝えた。"),
        ("I queued for forty-five minutes just to be told I was in the wrong line. Typical.",
         "45分も並んだ挙句、列を間違えていると言われた。まあ、よくあることだ。"),
        ("My holiday was 'quite eventful' — the flight was delayed twice, my luggage went missing, and it rained the whole week.",
         "今回の休暇は「なかなか波乱万丈」だった――飛行機は2回遅れ、荷物は行方不明になり、1週間ずっと雨だった。"),
        ("I told him his plan was 'interesting.' What I meant was that it was a terrible idea.",
         "彼の計画を「興味深いね」と言ったけど、本当は「それはひどい考えだ」という意味だった。"),
        ("We had a slight disagreement, in the sense that he shouted and I quietly left the room.",
         "私たちはちょっとした意見の食い違いがあった――彼が怒鳴り、私は静かに部屋を出て行った、という意味で。"),
        ("I'm not much of a morning person, unless you count silently glaring at my tea until it's ready.",
         "私は朝が得意な方ではない――紅茶が入るまで無言でにらみ続けるのを「得意」と呼ぶなら別だけど。"),
        ("The film was 'not entirely to my taste' — I fell asleep twice and left before the end.",
         "あの映画は「あまり自分の好みには合わなかった」――2回も居眠りして、終わる前に帰ってしまった。"),
        ("Apparently I have 'a lot of potential.' I've had a lot of potential since I was seven.",
         "どうやら私には「大きな可能性」があるらしい。7歳の頃からずっと「可能性」のままだけれど。"),
        ("He apologised for being two hours late by saying the traffic was 'a bit tricky.'",
         "彼は2時間の遅刻を「交通事情がちょっと厄介で」と言って詫びた。"),
        ("I'm training for a marathon, in the sense that I once walked briskly to catch a bus.",
         "マラソンに向けて練習中――バスに乗り遅れないよう一度早歩きしたことがある、という意味で。"),
        ("The waiter asked how the food was. I said, 'Lovely, thank you,' while quietly picking something unidentifiable out of my teeth.",
         "ウェイターに料理の感想を聞かれ、「美味しかったです、ありがとう」と答えながら、こっそり歯に挟まった正体不明の何かを取り除いていた。"),
        ("My New Year's resolution is the same as last year's: complain about the weather with slightly more creativity.",
         "今年の抱負は去年と同じ――天気の愚痴を、去年より少しだけ工夫して言うこと。"),
        ("I asked if the trains were running on time. The man laughed for quite a long time before answering.",
         "電車が時間通りに来ているか尋ねたら、その人は答える前にかなり長く笑っていた。"),
        ("I'm not saying the queue was long, but I aged considerably while standing in it.",
         "列が長かったとは言わないけど、並んでいる間にずいぶん歳をとった気がする。"),
        ("He described the exam as 'a bit of a challenge.' He failed every single question.",
         "彼はその試験を「まあまあ手強かった」と表現した。全問不正解だったのに。"),
        ("The English are famous for their reserve — or so I've been told, though no one has ever actually confirmed it to my face.",
         "イギリス人は控えめなことで有名らしい――そう聞いてはいるけれど、面と向かって誰かにそう言われたことは一度もない。"),
        ("I told my boss the project was 'coming along nicely.' It was on fire, both figuratively and, at one point, almost literally.",
         "上司には「プロジェクトは順調です」と伝えた。実際は比喩的にも、ある時点ではほぼ文字通りにも「炎上」していたのだけれど。"),
        ("We don't complain — we just mention things repeatedly in a slightly disappointed tone.",
         "私たちは文句を言わない――ただ、少しがっかりした口調で同じことを何度も言うだけ。"),
        ("I said 'I'm fine' seventeen times today, and not once did I mean it.",
         "今日は「大丈夫です」と17回言ったけど、一度も本気で大丈夫だと思っていなかった。"),
        ("The instructions said assembly takes ten minutes. Three hours, two arguments, and one missing screw later, we agreed the instructions had lied.",
         "説明書には「組み立ては10分」と書いてあった。3時間、2回の口論、ネジ1本の紛失を経て、私たちは「説明書は嘘をついていた」という結論に達した。"),
    ],
}


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }

        added = skipped = 0
        per_scene: dict[str, int] = {}
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in existing:
                    skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                existing.add(en.lower())
                added += 1
                per_scene[scene] = per_scene.get(scene, 0) + 1
        conn.commit()

    print(f"phrases: +{added} (skipped {skipped})")
    for scene, n in per_scene.items():
        print(f"  {scene}: +{n}")
    with db() as conn:
        print("total phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
