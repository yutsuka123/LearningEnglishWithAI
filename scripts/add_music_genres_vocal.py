# ruff: noqa: E501  (data-heavy seed script: long word/example lines are fine)
"""Bulk-add music GENRE vocabulary, SHEET-MUSIC/NOTATION jargon, and
OPERA/VOCAL-MUSIC vocabulary, authored by Claude.

背景: `words` テーブルには既に81件の音楽語彙（楽器・基礎記譜・基礎理論）が
あるが、ジャンル名がほぼ皆無で、オペラ／声楽系も "opera" 一語のみだった。
本スクリプトはその手薄な領域を3本立てで補強する:

  1. ジャンル名（+34）: jazz / rock / pop など定番ジャンルから、
     bluegrass / ska / grunge のようなマイナー寄りのジャンル、
     mainstream / underground / genre-bending といったジャンル周辺語まで。
  2. 楽譜記号・記譜法（+21）: clef/staff/note-values/key-signature/
     time-signature/ledger-line/accidental/sharp/flat/natural など基礎は
     既存語彙でカバー済みのため対象外とし、dal segno・fermata・volta
     （一番/二番括弧）・tuplet/triplet・tacet・transposing instrument など
     一歩進んだ記譜用語を追加。
  3. オペラ・声楽（+20）: aria / libretto / overture といった作品構成語、
     soprano〜bass の声域名、falsetto/bel canto/vibrato などの発声技法、
     diva/prima donna/curtain call/standing ovation/opera house など
     鑑賞シーンの語彙。

domain は全件 "音楽"。既存の音楽語彙（scripts/add_music.py,
scripts/add_genres2.py 等）に倣い、品詞(part_of_speech)は空文字列で統一
し、日本語訳は「カタカナ表記(補足説明)」の形式にそろえた。

No app / OpenAI API calls — everything is hand-written and inserted
directly into the SQLite DB. Duplicates are skipped by english
(lowercased), matched against the ENTIRE `words` table (not just this
domain), so words that already exist under another domain (e.g. plain
"country", "classical", "soul", "gospel", "house", "crossover", "choir",
"chorus" which collide with existing rows) were deliberately reworded
(e.g. "classical music", "soul music", "gospel music", "house music",
"musical crossover") or dropped where the existing entry already covers
the concept.

Run:  python scripts/add_music_genres_vocal.py

NOTE: intentionally NOT run as part of authoring this file — a sibling
script (scripts/add_music_instruments_theory.py) may be inserting
instrument/theory content concurrently, and running both writers at once
risks a SQLite write-lock collision. A few terms below (grace note,
vibrato, transposing instrument) may also appear in that sibling batch;
the runtime dedup-by-english simply skips whichever one loses the race.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- words: (english, japanese, part_of_speech, example_sentence, domain, level) ---

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # === 1. ジャンル名 (genres) ==============================================
    ("jazz", "ジャズ", "", "Jazz often features improvisation between musicians.", "音楽", "300"),
    ("rock", "ロック", "", "He grew up listening to classic rock.", "音楽", "300"),
    ("pop", "ポップス(ポップミュージック)", "", "She writes catchy pop songs for the radio.", "音楽", "300"),
    ("classical music", "クラシック音楽", "", "He prefers classical music to pop.", "音楽", "350"),
    ("blues", "ブルース", "", "The blues has a soulful, melancholy feel.", "音楽", "400"),
    ("hip-hop", "ヒップホップ", "", "Hip-hop grew out of block parties in New York.", "音楽", "400"),
    ("folk", "フォーク(民俗音楽・フォークソング)", "", "He plays folk songs on an acoustic guitar.", "音楽", "400"),
    ("country", "カントリー(ミュージック)", "", "Country music often tells stories about rural life.", "音楽", "400"),
    ("R&B", "アールアンドビー(リズム&ブルース)", "", "Her voice suits smooth R&B ballads.", "音楽", "450"),
    ("reggae", "レゲエ", "", "Reggae music originated in Jamaica.", "音楽", "450"),
    ("EDM", "EDM(エレクトロニック・ダンス・ミュージック)", "", "The DJ mixed EDM tracks all night at the club.", "音楽", "500"),
    ("punk", "パンク(パンクロック)", "", "The band's punk sound was loud, fast, and raw.", "音楽", "500"),
    ("metal", "メタル(ヘヴィメタル)", "", "He loves the heavy guitar riffs of metal.", "音楽", "500"),
    ("disco", "ディスコ", "", "Disco was hugely popular in dance clubs in the 1970s.", "音楽", "500"),
    ("gospel music", "ゴスペル音楽", "", "Gospel music is rooted in church traditions.", "音楽", "500"),
    ("soul music", "ソウルミュージック", "", "Soul music blends gospel and R&B influences.", "音楽", "500"),
    ("K-pop", "Kポップ", "", "K-pop idols train for years before they debut.", "音楽", "500"),
    ("funk", "ファンク", "", "Funk music is known for its strong, danceable bass grooves.", "音楽", "550"),
    ("techno", "テクノ", "", "Techno music relies heavily on repetitive electronic beats.", "音楽", "550"),
    ("house music", "ハウスミュージック", "", "House music has a steady four-on-the-floor beat.", "音楽", "550"),
    ("indie", "インディーズ(独立系)", "", "The indie band recorded the album entirely on their own.", "音楽", "550"),
    ("lo-fi", "ローファイ", "", "She studies while listening to lo-fi beats.", "音楽", "600"),
    ("alternative", "オルタナティブ(オルタナ)", "", "Alternative rock became popular in the 1990s.", "音楽", "600"),
    ("synth-pop", "シンセポップ", "", "Synth-pop relies heavily on electronic keyboard sounds.", "音楽", "650"),
    ("orchestral", "オーケストラの・管弦楽の", "", "The film has a sweeping orchestral score.", "音楽", "650"),
    ("ambient", "アンビエント(環境音楽)", "", "Ambient music creates a calm, atmospheric mood.", "音楽", "650"),
    ("a cappella", "アカペラ", "", "The choir sang the closing song a cappella, with no instruments.", "音楽", "700"),
    ("bluegrass", "ブルーグラス", "", "Bluegrass features fast banjo and fiddle playing.", "音楽", "700"),
    ("grunge", "グランジ", "", "Grunge combined punk energy with a heavy guitar sound.", "音楽", "700"),
    ("mainstream", "主流の・メインストリームの", "", "The band moved from small clubs to mainstream radio.", "音楽", "700"),
    ("underground", "アンダーグラウンドの(音楽シーン)", "", "She discovered the band through the city's underground music scene.", "音楽", "700"),
    ("ska", "スカ", "", "Ska mixes upbeat rhythms with brass instruments.", "音楽", "750"),
    ("musical crossover", "クロスオーバー(異ジャンル融合)", "", "The album was a musical crossover between jazz and hip-hop.", "音楽", "800"),
    ("genre-bending", "ジャンルを超えた", "", "The album's genre-bending sound mixes jazz, hip-hop, and classical.", "音楽", "850"),

    # === 2. 楽譜記号・記譜法 (sheet music / notation) ========================
    ("lead sheet", "リードシート", "", "A lead sheet shows the melody, lyrics, and chord symbols.", "音楽", "700"),
    ("chord chart", "コードチャート(コード譜)", "", "The guitarist read from a simple chord chart.", "音楽", "700"),
    ("tablature", "タブ譜(タブラチュア)", "", "Guitar tablature, often called tab, shows which string and fret to play.", "音楽", "700"),
    ("repeat sign", "反復記号(リピート記号)", "", "The repeat sign tells you to play that section again.", "音楽", "750"),
    ("dal segno", "ダル・セーニョ(記号から繰り返せの指示)", "", "Dal segno tells the performer to go back to the segno sign.", "音楽", "800"),
    ("da capo", "ダ・カーポ(最初に戻れの指示)", "", "Da capo means to return to the very beginning of the piece.", "音楽", "800"),
    ("first ending", "一番括弧", "", "Skip the first ending and go straight to the second ending on the repeat.", "音楽", "800"),
    ("second ending", "二番括弧", "", "Play the second ending only after you take the repeat.", "音楽", "800"),
    ("cut time", "カットタイム(2/2拍子)", "", "Cut time is written as a C with a vertical line through it.", "音楽", "850"),
    ("fermata", "フェルマータ", "", "A fermata means to hold the note longer than its usual value.", "音楽", "850"),
    ("coda sign", "コーダ記号", "", "The coda sign shows the performer where to jump to the closing section.", "音楽", "850"),
    ("triplet", "三連符", "", "The triplet squeezes three notes into the space normally used for two.", "音楽", "850"),
    ("grace note", "装飾音符(グレースノート)", "", "A grace note is a quick decorative note played just before the main note.", "音楽", "850"),
    ("pickup measure", "弱起(ピックアップ小節)", "", "The pickup measure has fewer beats than a full measure.", "音楽", "850"),
    ("volta", "一番・二番括弧の総称(ヴォルタ)", "", "Volta brackets mark different endings for a repeated section.", "音楽", "900"),
    ("compound time", "複合拍子", "", "6/8 is a common compound time signature.", "音楽", "900"),
    ("tuplet", "連符", "", "A tuplet fits an unusual number of notes into a single beat.", "音楽", "900"),
    ("transposing instrument", "移調楽器", "", "The clarinet is a transposing instrument, so its written and sounding pitches differ.", "音楽", "900"),
    ("concert pitch", "コンサートピッチ(実音)", "", "Concert pitch is the actual sounding pitch, not the written one.", "音楽", "900"),
    ("anacrusis", "アナクルーシス(弱起)", "", "The melody begins with an anacrusis before the first strong beat.", "音楽", "950"),
    ("tacet", "タチェット(休みの指示)", "", "Tacet tells a musician to stay silent for that whole section.", "音楽", "950"),

    # === 3. オペラ・声楽 (opera / vocal music) ===============================
    ("concert hall", "コンサートホール", "", "The orchestra performed in a famous concert hall.", "音楽", "500"),
    ("opera house", "オペラハウス(歌劇場)", "", "The opera house was full for the premiere.", "音楽", "550"),
    ("soprano", "ソプラノ", "", "She has a powerful soprano voice.", "音楽", "600"),
    ("alto", "アルト", "", "He sings alto in the church choir.", "音楽", "600"),
    ("standing ovation", "スタンディングオベーション", "", "The audience gave the singers a standing ovation.", "音楽", "650"),
    ("tenor", "テノール", "", "The tenor hit the high note effortlessly.", "音楽", "650"),
    ("aria", "アリア", "", "The soprano sang a beautiful aria in the second act.", "音楽", "700"),
    ("bass", "バス(低音の男声)", "", "The bass singer provided the deep foundation of the chorus.", "音楽", "700"),
    ("diva", "ディーバ(歌姫)", "", "The opera diva received a standing ovation after the final aria.", "音楽", "700"),
    ("curtain call", "カーテンコール", "", "The cast took a curtain call after the performance.", "音楽", "700"),
    ("box seat", "ボックス席(特別観覧席)", "", "They watched the opera from a box seat above the stage.", "音楽", "700"),
    ("baritone", "バリトン", "", "His baritone voice was rich and warm.", "音楽", "750"),
    ("overture", "序曲(オーヴァチュア)", "", "The overture introduces the opera's main musical themes before the curtain rises.", "音楽", "800"),
    ("mezzo-soprano", "メゾソプラノ", "", "The mezzo-soprano sang the role of the queen.", "音楽", "800"),
    ("prima donna", "プリマドンナ(主役の女性歌手)", "", "The prima donna sang the leading role on opening night.", "音楽", "800"),
    ("vibrato", "ビブラート", "", "Her vibrato added warmth to the long held note.", "音楽", "800"),
    ("falsetto", "ファルセット(裏声)", "", "He sang the high note in falsetto.", "音楽", "850"),
    ("libretto", "台本(リブレット)", "", "The libretto for the opera was written in Italian.", "音楽", "850"),
    ("supertitles", "スーパータイトル(舞台上部の字幕)", "", "Supertitles above the stage translated the Italian lyrics.", "音楽", "850"),
    ("bel canto", "ベルカント(美しい歌唱法)", "", "Bel canto singing emphasizes a beautiful, smoothly connected tone.", "音楽", "950"),
]


# --- insertion --------------------------------------------------------------


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }

        w_added = w_skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in w_existing:
                w_skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            w_existing.add(en.lower())
            w_added += 1

    print(f"words: +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("totals -> words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
