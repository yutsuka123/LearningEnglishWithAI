# ruff: noqa: E501
"""新規大分類「新語・流行」新設(2026-09-09・authored by Claude)。ユーザー提起「2020年代とくに2026年はやりの英語」。流行(2025)/新語(2025)/流行(2026)/新語(2026)の4分野。生成ではなくWebSearchでの実地調査(Merriam-Webster/Oxford/Collins/Cambridge/Dictionary.comの年間新語・Word of the Year等)に基づく。2026年分は今年まだ8ヶ月強のため件数が少ない(3件)のは意図的な保守的判断(捏造回避を優先)。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_slang_trends_2026_09_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("slop", "質の低いAI生成コンテンツ、特に大量生産される中身の薄い画像・動画・文章・広告などを指す語。もとは『(豚などの)残飯・食べ滓』『泥状のもの』を意味する古い単語だったが、2020年代半ばの生成AI普及に伴い『AIスロップ(AI slop)』という新しい意味で急速に広まった。", "名詞", "My social media feed is completely clogged with AI slop these days — fake photos, fake news, fake everything.", "流行（2025）", "450"),
    ("rage bait", "怒りや炎上を意図的に誘発するように作られたSNS投稿・オンラインコンテンツのこと。閲覧数・反応数(エンゲージメント)を稼ぐ目的で、わざと挑発的・不快な内容を発信する行為やその投稿自体を指す。", "名詞", "That article was pure rage bait — it was designed to make people angry enough to share it.", "流行（2025）", "450"),
    ("parasocial", "有名人・インフルエンサー・フィクションのキャラクター・AIチャットボットなどに対して一方的に抱く『疑似的な親密さ』を表す形容詞。相手は自分のことを知らないが、自分だけが親近感や関係性を感じている状態を指す(『パラソーシャル』とカタカナ表記されることもある)。", "形容詞", "She has a parasocial relationship with her favorite YouTuber, even though he has no idea she exists.", "流行（2025）", "600"),
    ("six-seven", "特に意味を持たない、10代を中心に流行した掛け声・合いの手のようなスラング。数字の『6』と『7』を英語でそのまま口にする(『6-7』『67』とも表記される)。文脈によって『まあまあ』『どっちともいえない』のようなニュアンスで使われることもあるが、本質的には『brain rot(脳が溶けるようなネットスラング文化)』を象徴する、意味の定まらない流行語。", "間投詞", "The kid just yelled '6-7!' in the middle of class for absolutely no reason.", "流行（2025）", "300"),
    ("gerrymander", "自党に有利になるよう不自然な形に選挙区の境界線を操作すること(またはその選挙区そのもの)。日本語の『ゲリマンダー』はこの語のカタカナ表記。動詞としても名詞としても使われる。", "動詞", "Critics accused the state legislature of gerrymandering the new congressional map to favor one party.", "流行（2025）", "650"),
    ("conclave", "非公開で行われる重要な会議、特にローマ・カトリック教会が新しい教皇を選出するために枢機卿だけで行う『コンクラーベ(教皇選挙会議)』を指す語。転じて、一般に『秘密裏の重要な会合』全般を指すこともある。", "名詞", "Cardinals from around the world gathered in Rome for the conclave to elect the new pope.", "流行（2025）", "600"),
    ("touch grass", "『(ネットばかり見ていないで)外に出て気分転換しろ』という意味の命令形スラング。文字通りには『芝生に触れる』だが、実際に芝生を触るという意味ではなく、『インターネットから離れて現実世界に戻れ』という比喩的な忠告・からかいとして使われる。", "動詞", "You've been arguing about this meme for three hours — go touch grass.", "流行（2025）", "350"),
    ("aura farming", "SNSなどで、さりげない仕草や振る舞いによって『かっこよさ』『カリスマ性』を演出し、自分の“オーラ”を高めようとする行為・意識のこと。日本語の『オーラを稼ぐ』に近いニュアンス。", "名詞", "He walked into the room in slow motion, clearly aura farming for the camera.", "流行（2025）", "400"),
    ("tradwife", "『伝統的な(traditional)』と『専業主婦(housewife)』を組み合わせた語で、家事・育児・夫への従属といった“伝統的な”性別役割分担のライフスタイルを理想化し、SNSで発信する女性(またはその生き方)を指す。フェミニズムへの反動的な文化現象として議論の的になっている。", "名詞", "The tradwife influencer posts videos of herself baking bread from scratch and deferring to her husband's decisions.", "流行（2025）", "500"),
    ("delulu", "『delusional(妄想的、現実離れした)』を短縮したスラング。特に恋愛や将来の見通しについて、根拠のない楽観的な思い込みをしていることを指す(良い意味でも自虐的な意味でも使われる)。", "形容詞", "I know he probably doesn't like me back, but I'm staying delulu about it.", "流行（2025）", "320"),
    ("vibe coding", "AIに自然言語で指示を出しながらコードを書いてもらい、細かい実装を厳密に理解・管理せずに“雰囲気(vibe)”でソフトウェア開発を進める、生成AI時代の新しいプログラミングスタイル。", "名詞", "He built the entire prototype in a weekend just by vibe coding with an AI assistant, without really reading the generated code.", "新語（2025）", "550"),
    ("clanker", "AIロボットやチャットボット、自動化されたシステムなど『人間の仕事を奪うAI・機械』全般を指す、やや侮蔑的なスラング。人間に対する差別用語のような響きを模して使われる、AI・自動化への反感を込めた俗語。", "名詞", "The delivery robot got stuck on the curb again — stupid clanker.", "新語（2025）", "420"),
    ("performative male", "本心からというより、女性から好印象を持たれることを意識して『フェミニズムに理解がある』『繊細で優しい』といった振る舞いを“演じている”ように見える男性を揶揄するミーム的な語。抹茶ラテを持つ、フェミニズム関連の本を読む、インディー系の女性アーティストを聴く、といった“お約束”の記号とセットで語られることが多い。", "名詞", "He brought a feminist essay collection to the coffee shop and ordered a matcha latte — total performative male behavior.", "新語（2025）", "500"),
    ("broligarchy", "『bro(男仲間)』と『oligarchy(寡頭政治)』を組み合わせた語で、テック業界の富裕な男性経営者たちが政治的影響力を握る、あるいはそれを志向する状況を批判的に指す造語。", "名詞", "Journalists have started using the term 'broligarchy' to describe how a handful of tech billionaires now sit close to political power.", "新語（2025）", "650"),
    ("skibidi", "特定の固定した意味を持たない、若年層のインターネットミーム発のスラング。文脈によって『かっこいい』『変な・ダサい』のような意味で使われたり、単なる口癖・合いの手として意味なく使われたりする。", "感嘆詞", "The kids kept shouting 'skibidi' back and forth, and none of the adults had any idea what it meant.", "新語（2025）", "300"),
    ("mouse jiggler", "パソコンのマウスカーソルを自動的に動かし続けることで、離席中でも『パソコンを操作中=仕事中』であるように見せかけるための小型装置やソフトウェアのこと。リモートワークで在席監視ソフトの目を欺くために使われる。", "名詞", "He bought a mouse jiggler so his laptop would show him as 'active' while he took long lunch breaks.", "新語（2025）", "500"),
    ("kinda chic", "SNS（TikTok/Instagram）で2026年に流行したミーム表現。「kinda chic to ~」の形で、伝統的には『シック（上品・おしゃれ）』とはみなされない日常的なこと（自分らしくいること、体型の多様性を受け入れること、失敗を笑い飛ばすことなど）を、あえて『それもちょっとシックだよね』と前向きに言い換える言い回し。", "表現", "It's kinda chic to spill soup all over your shirt at lunch and then confidently wear that stained shirt at your next meeting.", "流行（2026）", "600"),
    ("jelly", "「嫉妬している、うらやましい」という意味のイギリス発のくだけたスラング形容詞。jealousの口語的な言い換え・短縮として使われる。この語義自体は以前から俗語として存在したが、2026年3月にオックスフォード英語辞典（OED）が正式な語義として新たに収録した。", "形容詞", "Don't be jelly just because I got tickets to the concert and you didn't.", "新語（2026）", "650"),
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
