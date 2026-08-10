# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Extend the existing "お祭り" domain/scene with festivals and annual events
from outside Japan, authored by Claude (2026-08-10・ユーザー要望).

対象語彙: アメリカ(マルディグラ、感謝祭パレード、独立記念日の花火、ハロウィン
のトリックオアトリート)、中国(春節、紅包、龍舞・獅子舞、中秋節、月餅、端午節・
ドラゴンボートレース)、スペイン(サン・フェルミン祭の牛追い、ラ・トマティーナ、
セマナ・サンタ、フラメンコ祭り)、イタリア(ヴェネツィアのカーニバル、シエナの
パリオ)、イギリス(ノッティングヒル・カーニバル、ガイ・フォークス・ナイト)、
フランス(パリ祭/フランス革命記念日、音楽の祭日)、韓国(保寧マッドフェスティ
バル、秋夕、燃燈会)の7地域の代表的な祭り・年中行事の語彙。祭りの固有名詞
(Mardi Gras, La Tomatina 等)は文化紹介に必要な一般名詞的表記として使用し、
特定の商業ブランド名・企業名は避けている。

フレーズは海外の祭りに参加する・体験を話す・日本の祭りと比較する場面で
実際に使う自然な口語表現。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_world_festivals.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- アメリカ ---
    ("Mardi Gras", "マルディグラ(告解火曜日の謝肉祭)", "名詞", "Mardi Gras parades fill the streets of New Orleans every year.", "お祭り", "650"),
    ("king cake", "キングケーキ(マルディグラで食べる伝統菓子)", "名詞", "Whoever finds the tiny baby hidden in the king cake gets good luck.", "お祭り", "750"),
    ("Thanksgiving Day parade", "感謝祭パレード", "名詞", "Giant balloons float above the crowd during the Thanksgiving Day parade.", "お祭り", "550"),
    ("parade balloon", "パレードの巨大バルーン", "名詞", "The parade balloon shaped like a cartoon character drew cheers from the kids.", "お祭り", "500"),
    ("Independence Day fireworks", "独立記念日の花火", "名詞", "Families gather on the riverbank to watch the Independence Day fireworks.", "お祭り", "500"),
    ("trick-or-treating", "トリックオアトリート(ハロウィンの家々を回る風習)", "名詞", "The kids went trick-or-treating around the neighborhood in their costumes.", "お祭り", "500"),
    # --- 中国 ---
    ("Chinese New Year", "春節(旧正月)", "名詞", "Families travel long distances to be together for Chinese New Year.", "お祭り", "450"),
    ("red envelope", "お年玉袋(紅包)", "名詞", "Children receive a red envelope filled with money from their relatives.", "お祭り", "550"),
    ("dragon dance", "龍舞", "名詞", "The dragon dance wound through the crowded street to loud drumming.", "お祭り", "600"),
    ("lion dance", "獅子舞", "名詞", "A lion dance performance is believed to bring good luck for the new year.", "お祭り", "600"),
    ("Mid-Autumn Festival", "中秋節", "名詞", "Families gather outdoors to watch the full moon during the Mid-Autumn Festival.", "お祭り", "550"),
    ("mooncake", "月餅", "名詞", "We exchanged boxes of mooncake with our neighbors.", "お祭り", "600"),
    ("Dragon Boat Festival", "端午節", "名詞", "The Dragon Boat Festival commemorates an ancient poet with boat races.", "お祭り", "650"),
    ("dragon boat race", "ドラゴンボートレース", "名詞", "Teams practice for months before the dragon boat race.", "お祭り", "600"),
    # --- スペイン ---
    ("running of the bulls", "牛追い祭り(サン・フェルミン祭)", "名詞", "Runners sprint ahead of the bulls during the running of the bulls in Pamplona.", "お祭り", "700"),
    ("La Tomatina", "ラ・トマティーナ(トマト投げ祭り)", "名詞", "Thousands of people throw ripe tomatoes at each other during La Tomatina.", "お祭り", "650"),
    ("Semana Santa", "セマナ・サンタ(聖週間)", "名詞", "Hooded penitents march through town during Semana Santa.", "お祭り", "750"),
    ("religious procession", "宗教的な行列", "名詞", "A religious procession moved slowly through the narrow streets.", "お祭り", "600"),
    ("flamenco festival", "フラメンコ祭り", "名詞", "Dancers in bright dresses perform at the flamenco festival every spring.", "お祭り", "600"),
    # --- イタリア ---
    ("Venice Carnival", "ヴェネツィアのカーニバル", "名詞", "Visitors wear elaborate masks during the Venice Carnival.", "お祭り", "600"),
    ("carnival mask", "カーニバルの仮面", "名詞", "Each carnival mask is hand-painted by a local artisan.", "お祭り", "550"),
    ("Palio di Siena", "シエナのパリオ(競馬祭)", "名詞", "The whole piazza fills with spectators for the Palio di Siena.", "お祭り", "750"),
    ("bareback horse race", "鞍なし競馬", "名詞", "Jockeys ride without a saddle in the bareback horse race.", "お祭り", "700"),
    ("medieval pageant", "中世風のページェント(行列)", "名詞", "A medieval pageant precedes the main event, complete with costumes and flags.", "お祭り", "700"),
    # --- イギリス ---
    ("Notting Hill Carnival", "ノッティングヒル・カーニバル", "名詞", "Steel drum music fills the air at the Notting Hill Carnival.", "お祭り", "600"),
    ("steel drum", "スティールドラム", "名詞", "A steel drum band led the procession down the street.", "お祭り", "600"),
    ("Guy Fawkes Night", "ガイ・フォークス・ナイト", "名詞", "People light bonfires and set off fireworks on Guy Fawkes Night.", "お祭り", "650"),
    ("bonfire", "たき火(ガイ・フォークス・ナイトで焚く大きな火)", "名詞", "Neighbors gathered around the bonfire to keep warm.", "お祭り", "450"),
    ("effigy", "人形(祭りで燃やされる象徴的な人形)", "名詞", "An effigy is traditionally burned on top of the bonfire.", "お祭り", "800"),
    # --- フランス ---
    ("Bastille Day", "フランス革命記念日(パリ祭)", "名詞", "Fireworks light up the Eiffel Tower every Bastille Day.", "お祭り", "550"),
    ("military parade", "軍事パレード", "名詞", "A military parade marches down the avenue every July 14th.", "お祭り", "550"),
    ("Fête de la Musique", "音楽の祭日", "名詞", "Musicians of every style perform for free during Fête de la Musique.", "お祭り", "700"),
    ("street musician", "ストリートミュージシャン", "名詞", "A street musician played the accordion on the corner.", "お祭り", "450"),
    ("street dance party", "野外ダンスパーティー(パリ祭前夜に広場で開かれる)", "名詞", "Locals gather for a street dance party the night before Bastille Day.", "お祭り", "650"),
    # --- 韓国 ---
    ("Boryeong Mud Festival", "保寧マッドフェスティバル", "名詞", "Visitors cover themselves in mud at the Boryeong Mud Festival every summer.", "お祭り", "650"),
    ("mud wrestling", "泥レスリング", "名詞", "The mud wrestling competition drew a huge, laughing crowd.", "お祭り", "600"),
    ("Chuseok", "秋夕(チュソク・韓国の秋の収穫祭)", "名詞", "Families return to their hometowns for Chuseok, much like Thanksgiving.", "お祭り", "600"),
    ("songpyeon", "松片(ソンピョン・秋夕に作るお餅)", "名詞", "We made songpyeon together the night before Chuseok.", "お祭り", "750"),
    ("Yeondeunghoe", "燃燈会(蓮灯会・釈迦の誕生日を祝う灯り祭り)", "名詞", "Thousands of lotus lanterns light up the streets during Yeondeunghoe.", "お祭り", "800"),
    ("lotus lantern", "蓮の灯篭", "名詞", "Volunteers carried a giant lotus lantern at the front of the parade.", "お祭り", "650"),
]

PHRASES: list[tuple[str, str]] = [
    ("Have you ever been to Mardi Gras in New Orleans?", "ニューオーリンズのマルディグラに行ったことがありますか？"),
    ("I caught so many beads during the parade.", "パレードでたくさんビーズをキャッチしました。"),
    ("We watched the Thanksgiving Day parade on TV every year.", "毎年テレビで感謝祭パレードを見ていました。"),
    ("The fireworks on the Fourth of July were incredible.", "独立記念日の花火はすごかったです。"),
    ("My kids went trick-or-treating with the neighbors.", "うちの子たちは近所の子と一緒にトリックオアトリートに行きました。"),
    ("Chinese New Year is the biggest holiday in my country.", "春節は私の国で一番大きな祝日です。"),
    ("My grandmother gave me a red envelope this year.", "今年、祖母がお年玉袋をくれました。"),
    ("We watched the lion dance perform outside the shop.", "お店の前で獅子舞の演技を見ました。"),
    ("Have you ever tried mooncake during the Mid-Autumn Festival?", "中秋節に月餅を食べたことがありますか？"),
    ("The dragon boat race was more intense than I expected.", "ドラゴンボートレースは思ったより白熱していました。"),
    ("I'd love to see the running of the bulls someday, but it looks dangerous.", "いつかサン・フェルミン祭の牛追いを見てみたいけど、危なそうですね。"),
    ("Would you ever join La Tomatina and get covered in tomatoes?", "ラ・トマティーナに参加してトマトまみれになってみたいですか？"),
    ("Semana Santa felt very solemn compared to a Japanese festival.", "セマナ・サンタは日本の祭りに比べてとても厳かに感じました。"),
    ("The Venice Carnival masks were more elaborate than I imagined.", "ヴェネツィアのカーニバルの仮面は想像より豪華でした。"),
    ("Have you seen the Palio horse race in Siena?", "シエナのパリオ(競馬)を見たことがありますか？"),
    ("The whole town gets involved in preparing for the Palio.", "パリオの準備には町全体が関わります。"),
    ("Notting Hill Carnival is one of the biggest street festivals in Europe.", "ノッティングヒル・カーニバルはヨーロッパ最大級のストリートフェスティバルの一つです。"),
    ("We lit a bonfire and watched fireworks on Guy Fawkes Night.", "ガイ・フォークス・ナイトにたき火を焚いて花火を見ました。"),
    ("Bastille Day fireworks over the Eiffel Tower are unforgettable.", "エッフェル塔の上に上がるパリ祭の花火は忘れられません。"),
    ("Street musicians perform everywhere during Fête de la Musique.", "音楽の祭日にはあちこちでストリートミュージシャンが演奏します。"),
    ("Have you ever been covered in mud at the Boryeong Mud Festival?", "保寧マッドフェスティバルで泥まみれになったことがありますか？"),
    ("Chuseok is a lot like Japanese Obon, isn't it?", "秋夕は日本のお盆によく似ていますよね。"),
    ("We made songpyeon together as a family before Chuseok.", "秋夕の前に家族でソンピョンを一緒に作りました。"),
    ("Lotus lanterns light up the whole street during Yeondeunghoe.", "燃燈会では通り全体が蓮の灯篭で照らされます。"),
    ("How is Mardi Gras different from a Japanese festival?", "マルディグラは日本の祭りとどう違いますか？"),
    ("Unlike Japanese festivals, some of these events last for weeks.", "日本の祭りと違って、これらの行事の中には数週間続くものもあります。"),
    ("I felt like the Chinese New Year fireworks were even louder than Japanese ones.", "春節の花火は日本のものよりさらに大きな音に感じました。"),
    ("Both festivals bring the whole community together, don't they?", "どちらの祭りも地域全体をまとめる役割がありますよね。"),
    ("I want to compare Halloween in the US with Japanese festivals someday.", "いつかアメリカのハロウィンと日本の祭りを比べてみたいです。"),
    ("Which overseas festival would you most like to experience?", "海外の祭りの中で一番体験してみたいのはどれですか？"),
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
                "VALUES (?, ?, 'お祭りの英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
