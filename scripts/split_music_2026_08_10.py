# ruff: noqa: E501
"""「音楽」ドメインを5分類に再編する(2026-08-10・ドラフト/未実行)。

ユーザー要望: 既存の`音楽`ドメイン(341語)を、内容に基づいて次の5分類に
再編する:

- `音楽(楽器)`: 楽器そのもの・楽器の部品・演奏技法に関する語
  (例: violin, fret, embouchure, plectrum 等)。本スクリプトでは
  楽器名・パーツ/道具(fret, capo, mouthpiece, rosin, guitar pick,
  tuning fork, metronome, humbucker, tube amp, DI box 等)・楽器の
  物理的な演奏技法(fingering, strum, pizzicato, glissando, arpeggio,
  tremolo, trill, mute (instrument) 等)を含む。choir⇔orchestraの対称性
  から、器楽アンサンブルである`orchestra`もここに含めた。
- `音楽(ジャンル)`: 音楽ジャンル・様式 (例: jazz, reggae, baroque,
  bebop 等)。
- `音楽(専門)`: 音楽理論・音響・業界用語 (例: counterpoint, time
  signature, royalty, A&R, mastering 等)。楽典/記譜法(sharp, tie,
  time signature等)・音楽理論(counterpoint, modulation等)・音響
  (timbre, overtone等)・業界/レコード収集用語(A&R, royalties, LP,
  matrix number, crate-digging等)・演奏家の役職(session musician,
  maestro, virtuoso等)をまとめてこの1分類に集約した。
- `音楽(歌・声楽)`: 歌唱・声楽・作詞に関する語 (例: vibrato, falsetto,
  lyricist, a cappella 等)。声種(soprano/tenor等)・オペラ声楽用語
  (aria, libretto, prima donna等)・ラップの韻律/リリック用語(bar (rap),
  flow (rap), rhyme scheme, ghostwriter等)も含む。`vibrato`は楽器
  演奏でも使われる語だがユーザー指定の分類例に従いここに含めた。
- `音楽(他)`: 上記4つのいずれにも明確に当てはまらない語(演奏会場・
  観客・一般的すぎる語など)。前例スクリプトの"unclassified"に相当する
  受け皿だが、今回はユーザー指示により実際に`音楽(他)`domainへ移す。

341語は`SELECT english FROM words WHERE domain='音楽'`で全件取得した上で
1件ずつ目視し、5つのPython setに人力で振り分けた(部分一致等の機械的
分類は行っていない)。

フレーズ側は既存`音楽の演奏`scene(47件)を同様の方針で
`音楽(楽器)の英語`/`音楽(専門)の英語`/`音楽(歌・声楽)の英語`/
`音楽(他)の英語`に再分類する。今回の47件には明確に「ジャンル」を扱う
文が無かったため、`音楽(ジャンル)の英語`sceneは作成していない
(該当が薄いカテゴリを無理に作らない、というタスク指示に従った)。

前例スクリプト`scripts/split_automotive_embedded_2026_08_09.py`と同じ
手法(setに無い語は`[WARN] unclassified`として警告表示・UPDATE文で実際に
再分類・最後に旧domain/sceneの残件数を確認するverificationブロック)を
踏襲している。

【重要】このスクリプトはファイルを作成するのみで、実行はしていない。
341語規模の分類は誤分類のリスクがあるため、投入前に人間または別プロセス
によるレビューを想定している。DBを実際に変更するには下記コマンドを
レビュー後に実行すること。

Run:  python scripts/split_music_2026_08_10.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

OLD_WORD_DOMAIN = "音楽"
OLD_PHRASE_SCENE = "音楽の演奏"

NEW_WORD_DOMAIN_INSTRUMENT = "音楽(楽器)"
NEW_WORD_DOMAIN_GENRE = "音楽(ジャンル)"
NEW_WORD_DOMAIN_EXPERT = "音楽(専門)"
NEW_WORD_DOMAIN_VOCAL = "音楽(歌・声楽)"
NEW_WORD_DOMAIN_OTHER = "音楽(他)"

NEW_PHRASE_SCENE_INSTRUMENT = "音楽(楽器)の英語"
NEW_PHRASE_SCENE_EXPERT = "音楽(専門)の英語"
NEW_PHRASE_SCENE_VOCAL = "音楽(歌・声楽)の英語"
NEW_PHRASE_SCENE_OTHER = "音楽(他)の英語"


# --- 音楽(楽器): 楽器名・楽器パーツ/道具・物理的な演奏技法 (84語) ---
INSTRUMENT_WORDS = {
    # 楽器名(主要)
    "instrument", "orchestra", "guitar", "violin", "drum", "flute",
    "trumpet", "saxophone", "keyboard", "recorder",
    # 楽器名(オーケストラ・クラシック系)
    "cello", "viola", "double bass", "harp", "clarinet", "oboe",
    "bassoon", "piccolo", "French horn", "trombone", "tuba", "cornet",
    "timpani", "xylophone", "marimba", "snare drum", "cymbal",
    "tambourine", "triangle (instrument)", "congas", "bongos",
    "bagpipes", "banjo", "mandolin", "ukulele", "accordion", "sitar",
    "didgeridoo", "harmonica", "grand piano", "upright piano",
    "bass drum", "clapper", "cowbell", "kazoo", "glockenspiel",
    "hi-hat", "pan flute",
    # 楽器名(電子/バンド系)・機材
    "synthesizer", "electric guitar", "bass guitar", "turntable",
    "drum machine", "MIDI controller", "amplifier (music)",
    "effects pedal", "humbucker", "tube amp", "DI box",
    # 楽器の部品・道具
    "pedal", "capo", "fret", "guitar pick", "mouthpiece", "rosin",
    "tuning fork", "metronome", "music stand",
    # 合奏の楽器グループ・器楽性を示す語
    "woodwind section", "brass section", "string section",
    "rhythm section", "conductor's baton", "instrumental",
    "transposing instrument",
    # 物理的な演奏技法
    "fingering", "scale practice", "strum", "glissando", "arpeggio",
    "tremolo", "pizzicato", "mute (instrument)", "trill",
}

# --- 音楽(ジャンル): ジャンル・様式 (32語) ---
GENRE_WORDS = {
    "jazz", "rock", "pop", "classical music", "blues", "hip-hop",
    "folk", "country", "R&B", "reggae", "EDM", "punk", "metal",
    "disco", "gospel music", "soul music", "K-pop", "funk", "techno",
    "house music", "indie", "lo-fi", "alternative", "synth-pop",
    "orchestral", "ambient", "bluegrass", "grunge", "ska",
    "musical crossover", "genre-bending", "trap (music)",
}

# --- 音楽(専門): 楽典/記譜法・音楽理論・音響・業界/レコード用語 (167語) ---
EXPERT_WORDS = {
    # 基礎理論語彙
    "compose", "composer", "melody", "rhythm", "harmony", "tempo",
    "chord", "beat", "genre", "improvise", "pitch", "octave",
    "accompaniment", "audition",
    # 楽曲形式
    "symphony", "concerto", "sonata", "opera", "overture",
    # 記譜法・楽典
    "musical note", "staff", "clef", "treble clef", "bass clef",
    "sharp", "flat", "natural", "key signature", "time signature",
    "measure", "bar line", "rest", "whole note", "half note",
    "quarter note", "eighth note", "tie", "slur", "accidental",
    "ledger line", "scale", "major key", "minor key", "key",
    "interval", "tonic", "dominant", "semitone", "whole tone",
    "transpose", "crescendo", "decrescendo", "forte", "sheet music",
    "lead sheet", "chord chart", "tablature", "repeat sign",
    "dal segno", "da capo", "first ending", "second ending",
    "cut time", "fermata", "coda sign", "triplet", "pickup measure",
    "volta", "compound time", "tuplet", "concert pitch", "anacrusis",
    "tacet", "out of tune",
    # 演奏指示(テンポ/アーティキュレーション)
    "allegro", "andante", "adagio", "legato", "staccato", "ritardando",
    "rubato", "staccato marking",
    # 音楽理論(和声・対位法・装飾等)
    "grace note", "syncopation", "cadenza", "counterpoint",
    "polyphony", "modulation (key)", "cadence", "dissonance",
    "consonance", "timbre", "overtone", "ostinato", "motif", "coda",
    "key change", "atonal", "chromatic", "enharmonic",
    "secondary dominant", "augmented chord", "pedal point",
    "retrograde", "sonata form", "exposition", "recapitulation",
    "leitmotif", "basso continuo", "figured bass",
    "twelve-tone technique", "just intonation", "equal temperament",
    "circle of fifths", "appoggiatura", "passing tone", "suspension",
    "hemiola", "perfect pitch", "polymeter",
    # 学習・スキル
    "etude", "sight-reading",
    # 制作/スタジオ用語
    "mixing", "mastering", "sample (audio)", "loop", "overdub",
    "multitrack", "reverb", "equalizer", "click track",
    "sidechain compression", "backing track", "cover song",
    "punch-in",
    # 業界・興行用語
    "session musician", "A&R", "royalties", "setlist", "soundcheck",
    "maestro", "virtuoso", "accompanist", "understudy",
    "principal player", "first chair", "mixtape", "hype man",
    "co-sign", "record deal",
    # レコード/ヴァイナル収集用語
    "vinyl", "LP", "EP", "B-side", "dead wax", "matrix number",
    "gatefold", "liner notes", "crate-digging", "bootleg",
    "white label", "test pressing", "audiophile", "stylus", "tonearm",
    "tape hiss", "reel-to-reel",
}

# --- 音楽(歌・声楽): 歌唱・声楽・作詞・ラップの韻律/リリック (40語) ---
VOCAL_WORDS = {
    # 歌・作詞の基礎語彙
    "choir", "lyrics", "chorus", "verse", "vocalist", "bridge (song)",
    "hook", "a cappella", "solfege", "karaoke", "lullaby", "hum",
    "vibrato",
    # 声種・声楽技法
    "soprano", "alto", "tenor", "bass", "baritone", "mezzo-soprano",
    "falsetto", "bel canto", "tessitura", "coloratura",
    # オペラ・声楽の役職/用語
    "aria", "diva", "prima donna", "libretto",
    # ラップの韻律/リリック用語
    "bar (rap)", "flow (rap)", "freestyle rap", "punchline (rap)",
    "wordplay", "rhyme scheme", "ad-lib", "diss track", "battle rap",
    "spoken word", "delivery (vocal)", "ghostwriter", "cadence (rap)",
}

# --- 音楽(他): 上記4分類に明確には当てはまらない語 (18語) ---
OTHER_WORDS = {
    "duet", "tune", "soundtrack", "ensemble", "encore", "music class",
    "recital", "warm-up", "audience", "mainstream", "underground",
    "orchestra pit", "concert hall", "opera house", "standing ovation",
    "curtain call", "box seat", "supertitles",
}


# --- フレーズ: 音楽(楽器)の英語 (17件) ---
INSTRUMENT_PHRASES = {
    "Could you tune your instrument before we start?",
    "She played the solo with incredible vibrato.",
    "The conductor raised the baton and the orchestra fell silent.",
    "I just started taking guitar lessons last month.",
    "Can you show me how to hold the bow correctly?",
    "My fingers hurt from pressing the strings.",
    "I keep losing the beat when I try to play along.",
    "Do I need to buy a metronome for practice?",
    "The recital is coming up and I still can't play it from memory.",
    "How do I know if my violin is out of tune?",
    "Which finger goes on which fret for this chord?",
    "Should I use a pick or just my fingers to strum?",
    "Can you recommend a good beginner-friendly ukulele?",
    "I practiced the same scale for twenty minutes straight.",
    "That guitar tone comes from a tube amp cranked up loud.",
    "I swapped in a humbucker for a fatter, warmer tone.",
    "That synth line was run through an arpeggiator for that classic sound.",
}

# --- フレーズ: 音楽(専門)の英語 (26件) ---
EXPERT_PHRASES = {
    "Let's run through the setlist once more.",
    "The band did a quick soundcheck before the show.",
    "I want to learn how to read sheet music properly.",
    "I found a first pressing of this album at a flea market.",
    "The vinyl has some surface noise, but the mix still sounds warm.",
    "Check the dead wax for the matrix number before you buy it.",
    "This reissue was remastered from the original analog tapes.",
    "He's been crate-digging at record shops all weekend.",
    "The bootleg recording captures the whole show from the audience.",
    "This test pressing never got an official release.",
    "The loudness war really flattened the dynamics on that remaster.",
    "You can hear the tape hiss on the original master reel.",
    "The gatefold sleeve has amazing liner notes from the original sessions.",
    "This passage modulates to the relative minor in the development section.",
    "The cadence resolves from the dominant seventh straight to the tonic.",
    "Try voicing that chord with the third on top for a brighter sound.",
    "The composer uses a secondary dominant to tonicize the subdominant.",
    "Notice how the melody is presented in retrograde in the final variation.",
    "The piece is written using equal temperament, so every key sounds the same.",
    "Analyze the form — it's a textbook example of sonata form.",
    "That appoggiatura really adds tension before it resolves.",
    "The strings enter with a pedal point under the shifting harmonies.",
    "In just intonation, the intervals are tuned to pure ratios rather than equal steps.",
    "This voice leading avoids parallel fifths between the outer parts.",
    "The hemiola in the third movement always throws off the audience's sense of the beat.",
    "Take a moment to work through the circle of fifths with your students.",
}

# --- フレーズ: 音楽(歌・声楽)の英語 (3件) ---
VOCAL_PHRASES = {
    "Can you switch to the bridge section?",
    "The soprano's tessitura sits a little too high for this aria.",
    "Her coloratura passages require flawless breath control.",
}

# --- フレーズ: 音楽(他)の英語 (1件) ---
OTHER_PHRASES = {
    "I get really nervous performing in front of an audience.",
}
# 音楽(ジャンル)の英語: 該当するフレーズが47件中に無かったため作成しない。


def main() -> int:
    with db() as conn:
        rows = conn.execute(
            "SELECT id, english FROM words WHERE domain=?", (OLD_WORD_DOMAIN,)
        ).fetchall()
        w_instrument = w_genre = w_expert = w_vocal = w_other = w_unclassified = 0
        for r in rows:
            eng = r["english"]
            if eng in INSTRUMENT_WORDS:
                conn.execute("UPDATE words SET domain=? WHERE id=?",
                             (NEW_WORD_DOMAIN_INSTRUMENT, r["id"]))
                w_instrument += 1
            elif eng in GENRE_WORDS:
                conn.execute("UPDATE words SET domain=? WHERE id=?",
                             (NEW_WORD_DOMAIN_GENRE, r["id"]))
                w_genre += 1
            elif eng in EXPERT_WORDS:
                conn.execute("UPDATE words SET domain=? WHERE id=?",
                             (NEW_WORD_DOMAIN_EXPERT, r["id"]))
                w_expert += 1
            elif eng in VOCAL_WORDS:
                conn.execute("UPDATE words SET domain=? WHERE id=?",
                             (NEW_WORD_DOMAIN_VOCAL, r["id"]))
                w_vocal += 1
            elif eng in OTHER_WORDS:
                conn.execute("UPDATE words SET domain=? WHERE id=?",
                             (NEW_WORD_DOMAIN_OTHER, r["id"]))
                w_other += 1
            else:
                print(f"  [WARN] unclassified word: {eng!r} (id={r['id']})")
                w_unclassified += 1

        prows = conn.execute(
            "SELECT id, english FROM phrases WHERE scene=?", (OLD_PHRASE_SCENE,)
        ).fetchall()
        p_instrument = p_expert = p_vocal = p_other = p_unclassified = 0
        for r in prows:
            eng = r["english"]
            if eng in INSTRUMENT_PHRASES:
                conn.execute("UPDATE phrases SET scene=? WHERE id=?",
                             (NEW_PHRASE_SCENE_INSTRUMENT, r["id"]))
                p_instrument += 1
            elif eng in EXPERT_PHRASES:
                conn.execute("UPDATE phrases SET scene=? WHERE id=?",
                             (NEW_PHRASE_SCENE_EXPERT, r["id"]))
                p_expert += 1
            elif eng in VOCAL_PHRASES:
                conn.execute("UPDATE phrases SET scene=? WHERE id=?",
                             (NEW_PHRASE_SCENE_VOCAL, r["id"]))
                p_vocal += 1
            elif eng in OTHER_PHRASES:
                conn.execute("UPDATE phrases SET scene=? WHERE id=?",
                             (NEW_PHRASE_SCENE_OTHER, r["id"]))
                p_other += 1
            else:
                print(f"  [WARN] unclassified phrase: {eng!r} (id={r['id']})")
                p_unclassified += 1

    print(
        f"words -> 音楽(楽器): {w_instrument}, 音楽(ジャンル): {w_genre}, "
        f"音楽(専門): {w_expert}, 音楽(歌・声楽): {w_vocal}, 音楽(他): {w_other}, "
        f"unclassified: {w_unclassified}"
    )
    print(
        f"phrases -> 音楽(楽器)の英語: {p_instrument}, 音楽(専門)の英語: {p_expert}, "
        f"音楽(歌・声楽)の英語: {p_vocal}, 音楽(他)の英語: {p_other}, "
        f"unclassified: {p_unclassified}"
    )

    with db() as conn:
        remaining = conn.execute(
            "SELECT COUNT(*) FROM words WHERE domain=?", (OLD_WORD_DOMAIN,)
        ).fetchone()[0]
        remaining_p = conn.execute(
            "SELECT COUNT(*) FROM phrases WHERE scene=?", (OLD_PHRASE_SCENE,)
        ).fetchone()[0]
        print(f"remaining in old word domain: {remaining}, old phrase scene: {remaining_p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
