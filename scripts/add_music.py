# ruff: noqa: E501
"""Music vocabulary: notation, theory, piano, and school music terms.
Authored by Claude — no app/OpenAI API calls. Dedupe on english; back-fill
empty examples. domain="音楽". Run: python scripts/add_music.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

GROUPS: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "楽譜・記号": ("600", [
        ("musical note", "音符", "A musical note shows pitch and length."),
        ("staff", "五線譜", "Notes are written on the staff."),
        ("clef", "音部記号", "The clef sets the pitch of the lines."),
        ("treble clef", "ト音記号", "The treble clef marks the high notes."),
        ("bass clef", "ヘ音記号", "The bass clef marks the low notes."),
        ("sharp", "シャープ・嬰記号", "A sharp raises the note a half step."),
        ("flat", "フラット・変記号", "A flat lowers the note a half step."),
        ("natural", "ナチュラル・本位記号", "A natural cancels a sharp or flat."),
        ("key signature", "調号", "The key signature shows which notes are sharp."),
        ("time signature", "拍子記号", "The time signature here is four-four."),
        ("measure", "小節", "There are four beats in this measure."),
        ("bar line", "小節線", "A bar line divides the measures."),
        ("rest", "休符", "A rest is a moment of silence."),
        ("whole note", "全音符", "A whole note lasts four beats."),
        ("half note", "二分音符", "A half note lasts two beats."),
        ("quarter note", "四分音符", "A quarter note lasts one beat."),
        ("eighth note", "八分音符", "Two eighth notes equal one beat."),
        ("tie", "タイ", "A tie joins two notes into one sound."),
        ("slur", "スラー", "A slur means play the notes smoothly."),
        ("accidental", "臨時記号", "An accidental changes a single note."),
        ("ledger line", "加線", "Ledger lines extend above the staff."),
    ]),
    "音楽理論": ("700", [
        ("scale", "音階・スケール", "She practiced a C major scale."),
        ("major key", "長調", "The song is written in a major key."),
        ("minor key", "短調", "A minor key often sounds sad."),
        ("key", "調", "What key is this piece in?"),
        ("interval", "音程", "An octave is a wide interval."),
        ("tonic", "主音", "The tonic is the home note of a key."),
        ("dominant", "属音", "The dominant leads back to the tonic."),
        ("semitone", "半音", "A semitone is the smallest step."),
        ("whole tone", "全音", "A whole tone equals two semitones."),
        ("transpose", "移調する", "Transpose the song to a lower key."),
        ("dynamics", "強弱・ダイナミクス", "Dynamics control how loud or soft to play."),
        ("crescendo", "クレッシェンド", "A crescendo gradually grows louder."),
        ("decrescendo", "デクレッシェンド", "A decrescendo gradually grows softer."),
        ("forte", "フォルテ(強く)", "Play this passage forte."),
        ("accompaniment", "伴奏", "The piano provides the accompaniment."),
    ]),
    "ピアノ": ("600", [
        ("keyboard", "鍵盤", "She ran her fingers across the keyboard."),
        ("pedal", "ペダル", "The sustain pedal holds the sound."),
        ("grand piano", "グランドピアノ", "A grand piano fills the concert hall."),
        ("upright piano", "アップライトピアノ", "An upright piano fits a small room."),
        ("fingering", "運指", "The fingering is marked above the notes."),
        ("etude", "練習曲・エチュード", "She played a Chopin etude."),
        ("scale practice", "音階練習", "Daily scale practice builds finger skill."),
    ]),
    "学校・速度記号": ("600", [
        ("music class", "音楽の授業", "We sang together in music class."),
        ("recorder", "リコーダー", "Children learn the recorder at school."),
        ("choir", "合唱団", "She sings in the school choir."),
        ("sight-reading", "初見演奏", "Sight-reading is a valuable skill."),
        ("recital", "発表会・リサイタル", "She performed at the piano recital."),
        ("solfege", "ソルフェージュ(階名唱)", "Solfege uses do, re, and mi."),
        ("allegro", "アレグロ(速く)", "The first movement is marked allegro."),
        ("andante", "アンダンテ(歩く速さで)", "Play the andante section calmly."),
        ("adagio", "アダージョ(ゆるやかに)", "The adagio is slow and gentle."),
        ("legato", "レガート(なめらかに)", "Play the phrase smoothly, legato."),
        ("staccato", "スタッカート(短く切って)", "These notes are played staccato."),
        ("ritardando", "リタルダンド(だんだん遅く)", "End the piece with a ritardando."),
    ]),
}


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = filled = 0
        per_group: dict[str, int] = {}
        for group, (level, items) in GROUPS.items():
            for en, ja, ex in items:
                if en.lower() in existing:
                    conn.execute(
                        "UPDATE words SET example = ? WHERE "
                        "LOWER(english)=LOWER(?) AND COALESCE(example,'')=''",
                        (ex, en),
                    )
                    filled += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, ja, "", ex, "音楽", level),
                )
                existing.add(en.lower())
                added += 1
                per_group[group] = per_group.get(group, 0) + 1
    print(f"words: +{added} (例文補充 {filled})  {per_group}")
    with db() as conn:
        print("単語総数:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
