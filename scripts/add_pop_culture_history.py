# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Extend the existing "大衆文化" domain with vocabulary spanning the history
of popular culture, from oral traditions in antiquity through the short-form
video era of the 2020s (Claude作成・2026-08-10・ユーザー要望).

対象語彙: 古代(口承伝統・民話・大道芸)、中世(吟遊詩人的存在としての道化師・
教訓劇・ギルド)、ルネッサンス(パトロン制度・活版印刷・街頭歌謡)、産業革命〜
近代(ミュージックホール・ペニー・ドレッドフル・ボードビル・マスメディア・
大量生産された娯楽)、1920年代(狂騒の20年代・ジャズ・エイジ・フラッパー・
禁酒法時代の酒場)、1960〜70年代(ヒッピー・カウンターカルチャー・フラワー
パワー・フェスティバル文化・サイケデリック・ディスコ)、1980年代(MTV世代・
シンセポップ・パワードレッシング・アーケードゲーム)、1990年代(グランジ・
ボーイズバンド・レイヴ文化・ダイヤルアップ時代のネット文化)、2000年代
(リアリティ番組ブーム・黎明期のソーシャルメディア・ブログ文化・エモ)、
2010年代(ミーム文化・スマートフォン文化・配信時代・ハッシュタグ・
アクティビズム)、2020年代(ショート動画・リモート文化・ノスタルジア・
リバイバル)。実在の人物・バンド・作品・イベントの固有名詞は避け、一般的な
文化現象・ムーブメントを指す語のみを収録。

domainは既存の"大衆文化"を再利用(新規ドメインは作らない)。他スクリプトが
既に同名の英単語を別ドメインで登録している場合(disco, grunge, guild,
minstrel, troubadour, town crier, patronage, mass production, renaissance
など)は、意味が重なる語だけ別表現(disco era, grunge scene, trade guild
など)に言い換えて重複を避けている。

フレーズは、ある時代の文化を懐かしむ・説明する・今と比べる場面で使う自然な
口語表現("Back in the day, we didn't have any of this." "It never really
went out of style." など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_pop_culture_history.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 古代 ---
    ("oral tradition", "口承伝統(口伝えで伝わる文化)", "名詞", "Many ancient myths survived only through oral tradition.", "大衆文化", "650"),
    ("folk tale", "民話・おとぎ話", "名詞", "Every region has its own folk tale about a clever animal.", "大衆文化", "500"),
    ("marketplace entertainment", "市場の大道芸・見世物", "名詞", "Jugglers and singers offered marketplace entertainment to passersby.", "大衆文化", "700"),
    # --- 中世 ---
    ("jester", "道化師", "名詞", "The jester's job was to make the whole court laugh.", "大衆文化", "600"),
    ("morality play", "教訓劇(道徳を教える寸劇)", "名詞", "A morality play taught audiences right from wrong through simple characters.", "大衆文化", "800"),
    ("trade guild", "同業者組合・ギルド", "名詞", "Traveling performers sometimes formed their own trade guild.", "大衆文化", "750"),
    # --- ルネッサンス ---
    ("Renaissance culture", "ルネサンス文化", "名詞", "Renaissance culture mixed classical art with new scientific curiosity.", "大衆文化", "700"),
    ("arts patronage", "芸術のパトロン制度・後援", "名詞", "Wealthy families supported painters through arts patronage.", "大衆文化", "800"),
    ("printing press", "活版印刷機", "名詞", "The printing press let stories reach far more readers than before.", "大衆文化", "600"),
    ("broadside ballad", "街頭で売られた印刷歌謡", "名詞", "Cheap broadside ballads spread news and gossip through song.", "大衆文化", "850"),
    # --- 産業革命〜近代 ---
    ("music hall", "ミュージックホール(大衆演芸場)", "名詞", "Working-class families spent their evenings at the music hall.", "大衆文化", "650"),
    ("penny dreadful", "安価な扇情的読み物", "名詞", "Cheap penny dreadfuls thrilled young readers with lurid stories.", "大衆文化", "800"),
    ("vaudeville", "ボードビル(寄席演芸)", "名詞", "Vaudeville shows mixed comedy, music, and short acts on one stage.", "大衆文化", "750"),
    ("mass media", "マスメディア", "名詞", "Mass media changed how quickly trends could spread nationwide.", "大衆文化", "550"),
    ("mass-produced entertainment", "大量生産された娯楽", "名詞", "Cheap printing turned storytelling into mass-produced entertainment.", "大衆文化", "750"),
    # --- 1920年代 ---
    ("Roaring Twenties", "狂騒の20年代", "名詞", "The Roaring Twenties are remembered for fast music and bold fashion.", "大衆文化", "650"),
    ("jazz age", "ジャズ・エイジ", "名詞", "The jazz age brought new dances into ordinary people's living rooms.", "大衆文化", "650"),
    ("flapper", "フラッパー(自由奔放な新しい女性像)", "名詞", "The flapper broke old rules about how women should dress and act.", "大衆文化", "700"),
    ("speakeasy", "禁酒法時代の非合法酒場", "名詞", "People whispered a password to get into the speakeasy.", "大衆文化", "750"),
    # --- 1960〜70年代 ---
    ("hippie", "ヒッピー", "名詞", "The hippie lifestyle valued peace, nature, and community over money.", "大衆文化", "550"),
    ("counterculture", "カウンターカルチャー・対抗文化", "名詞", "The counterculture of that decade rejected traditional careers and values.", "大衆文化", "700"),
    ("flower power", "フラワーパワー(反戦・愛の精神運動)", "名詞", "Flower power became a symbol of the movement's message of peace.", "大衆文化", "700"),
    ("festival culture", "フェスティバル文化", "名詞", "Festival culture brought thousands of strangers together for music and camping.", "大衆文化", "600"),
    ("psychedelic", "サイケデリックな", "形容詞", "The album cover used bright, psychedelic patterns.", "大衆文化", "650"),
    ("disco era", "ディスコ全盛期", "名詞", "During the disco era, dance floors filled with flashing lights.", "大衆文化", "600"),
    # --- 1980年代 ---
    ("MTV generation", "MTV世代", "名詞", "The MTV generation grew up watching music videos after school.", "大衆文化", "700"),
    ("synth-pop era", "シンセポップ全盛期", "名詞", "Bands in the synth-pop era relied on electronic keyboards instead of guitars.", "大衆文化", "650"),
    ("power dressing", "パワードレッシング(強さを演出する服装)", "名詞", "Power dressing meant sharp shoulders and confident colors at the office.", "大衆文化", "800"),
    ("arcade game", "アーケードゲーム", "名詞", "Kids lined up with coins to play the newest arcade game.", "大衆文化", "450"),
    # --- 1990年代 ---
    ("grunge scene", "グランジ・シーン", "名詞", "The grunge scene favored torn jeans over polished fashion.", "大衆文化", "650"),
    ("boy band", "ボーイズバンド", "名詞", "Every boy band of that decade had a matching dance routine.", "大衆文化", "500"),
    ("rave culture", "レイヴ文化", "名詞", "Rave culture centered on all-night dancing to electronic beats.", "大衆文化", "700"),
    ("dial-up internet culture", "ダイヤルアップ時代のネット文化", "名詞", "Dial-up internet culture meant waiting minutes just to load one page.", "大衆文化", "750"),
    # --- 2000年代 ---
    ("reality TV boom", "リアリティ番組ブーム", "名詞", "The reality TV boom turned ordinary people into overnight celebrities.", "大衆文化", "650"),
    ("early social media", "黎明期のソーシャルメディア", "名詞", "Early social media let friends post short updates about their day.", "大衆文化", "550"),
    ("blog culture", "ブログ文化", "名詞", "Blog culture gave anyone a place to publish their own opinions.", "大衆文化", "600"),
    ("emo subculture", "エモ・サブカルチャー", "名詞", "The emo subculture combined dark fashion with emotional lyrics.", "大衆文化", "700"),
    # --- 2010年代 ---
    ("meme culture", "ミーム文化", "名詞", "Meme culture turns a single image into a shared inside joke overnight.", "大衆文化", "500"),
    ("smartphone culture", "スマートフォン文化", "名詞", "Smartphone culture put entertainment and news in everyone's pocket.", "大衆文化", "500"),
    ("streaming era", "配信時代・ストリーミング時代", "名詞", "In the streaming era, viewers choose what to watch and when.", "大衆文化", "550"),
    ("hashtag activism", "ハッシュタグ・アクティビズム", "名詞", "Hashtag activism helped a single post reach millions within hours.", "大衆文化", "750"),
    # --- 2020年代 ---
    ("short-form video", "ショート動画", "名詞", "Short-form video keeps viewers hooked in under a minute.", "大衆文化", "450"),
    ("remote culture", "リモート文化", "名詞", "Remote culture normalized meetings from bedrooms and kitchens alike.", "大衆文化", "550"),
    ("nostalgia revival", "ノスタルジア・リバイバル(過去の再流行)", "名詞", "Every decade seems to enjoy a nostalgia revival of the one before it.", "大衆文化", "650"),
]

PHRASES: list[tuple[str, str]] = [
    ("Back in the day, we didn't have any of this.", "昔は、こんなもの一つもなかったよ。"),
    ("That trend really took off in that decade.", "そのトレンドはその年代に一気に広まったんだ。"),
    ("It's making a huge comeback lately.", "最近すごく再流行しているんだよね。"),
    ("That's such a throwback.", "それ、懐かしいね(昔にタイムスリップしたみたい)。"),
    ("Every generation has its own version of this.", "どの世代にも、それぞれのバージョンがあるものだね。"),
    ("I grew up watching that on TV every week.", "子供のころ、毎週それをテレビで見て育ったよ。"),
    ("This feels very of-the-moment.", "これ、すごく今っぽい感じだね。"),
    ("It was ahead of its time.", "それは時代を先取りしていたね。"),
    ("That style has aged surprisingly well.", "あのスタイルは意外と古びていないね。"),
    ("Kids today have no idea what that was like.", "今の子どもたちは、それがどんな感じだったか全然知らないだろうね。"),
    ("It defined an entire generation.", "それはある世代をまるごと象徴するものだった。"),
    ("Everyone was obsessed with it back then.", "当時はみんなそれに夢中だったよ。"),
    ("It's a bit before my time.", "それは私が生まれる少し前の話だね。"),
    ("We used to line up for hours to get one.", "昔はそれを手に入れるために何時間も並んだものだよ。"),
    ("That's basically the modern version of it.", "それは実質、現代版みたいなものだね。"),
    ("It never really went out of style.", "それは一度も本当に廃れたことがないんだ。"),
    ("I can't believe that used to be considered cool.", "あれがかつてかっこいいとされていたなんて信じられないよ。"),
    ("It's making its way back into fashion.", "それがまたファッションに戻ってきているね。"),
    ("That was such a defining moment for pop culture.", "あれは大衆文化にとって、まさに転換点だったね。"),
    ("We used to gather around one screen to watch it together.", "昔はみんなで一台の画面の前に集まって、それを一緒に見ていたものだよ。"),
    ("That whole scene had its own look and sound.", "あのシーン全体に、独自の見た目と音楽性があったんだ。"),
    ("It feels like a completely different era now.", "今となっては、まったく違う時代のように感じるね。"),
    ("That trend didn't last very long.", "あのトレンドはあまり長続きしなかったね。"),
    ("People still reference it today.", "今でもみんなそれを引き合いに出すよね。"),
    ("It's funny how these trends come back in cycles.", "こういうトレンドが周期的に戻ってくるのって面白いね。"),
    ("That was considered pretty rebellious at the time.", "当時、それはかなり反抗的だとみなされていたよ。"),
    ("You had to be there to really get it.", "その場にいないと本当の良さは分からなかったよ。"),
    ("It's still influencing culture today.", "それは今でも文化に影響を与え続けているんだ。"),
]


def main() -> int:
    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing_words:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing_words.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")

    with db() as conn:
        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in existing_phrases:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '大衆文化・エンタメの英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
