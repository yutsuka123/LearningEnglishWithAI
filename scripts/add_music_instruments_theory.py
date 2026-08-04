# ruff: noqa: E501  (data-heavy seed script: long word/example lines are fine)
"""Bulk-add curated vocabulary for MUSIC: instruments (beyond the common set
already in the DB) and specialist/technical music terms, authored by Claude.

背景: DB には既に音楽ドメインの単語が81件ある（フルート/ギター/ドラム等の
定番楽器、五線譜/音符/調号などの基礎記譜、アダージョ/アレグロ等のテンポ・
強弱のイタリア語用語、コード/ハーモニー/スケール等の基礎理論）。本スクリプト
はそれらと重複しない領域を追加する。

Sub-batch 1 (+50): 楽器の拡充。
  - オーケストラ弦楽器（チェロ、ヴィオラ、コントラバス、ハープ）
  - 木管楽器（クラリネット、オーボエ、ファゴット、ピッコロ）
  - 金管楽器（フレンチホルン、トロンボーン、チューバ、コルネット）
  - 打楽器（ティンパニ、シロフォン、マリンバ、スネアドラム、シンバル、
    タンバリン、トライアングル、コンガ、ボンゴ）
  - 世界の民族楽器（バグパイプ、バンジョー、マンドリン、ウクレレ、
    アコーディオン、シタール、ディジュリドゥ、ハーモニカ）
  - 現代/電子楽器（シンセサイザー、エレキギター、ベースギター、
    ターンテーブル、ドラムマシン、MIDIコントローラー、アンプ、
    エフェクトペダル）
  - 楽器編成の語彙（木管セクション、金管セクション、弦楽セクション、
    リズムセクション、指揮棒、オーケストラピット）

Sub-batch 2 (+50): 専門的・技術的な音楽用語。
  - 演奏技法（ビブラート、グリッサンド、アルペジオ、トレモロ、
    ピチカート、ミュート、トリル、装飾音、シンコペーション、カデンツァ）
  - 理論/作曲（対位法、ポリフォニー、転調、終止形、不協和音、協和音、
    音色、倍音、オスティナート、モチーフ、コーダ、ブリッジ、フック、
    転調、無調、半音階）
  - 制作/レコーディング（ミキシング、マスタリング、サンプル、ループ、
    オーバーダブ、マルチトラック、リバーブ、イコライザー、
    クリックトラック、セッションミュージシャン、A&R、印税、
    セットリスト、サウンドチェック）
  - アンサンブル/演奏者の役職（マエストロ、ヴィルトゥオーゾ、
    伴奏者、代役、首席奏者、コンサートマスター相当のファーストチェア）

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_music_instruments_theory.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する
（本スクリプトのレベルは仮の目安）。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "音楽の演奏": [
        ("Could you tune your instrument before we start?", "始める前に楽器のチューニングをしてもらえますか？"),
        ("Let's run through the setlist once more.", "セットリストをもう一度通してみましょう。"),
        ("The band did a quick soundcheck before the show.", "バンドは本番前に手早くサウンドチェックをした。"),
        ("She played the solo with incredible vibrato.", "彼女は見事なビブラートでソロを演奏した。"),
        ("The conductor raised the baton and the orchestra fell silent.", "指揮者がタクトを上げると、オーケストラは静まり返った。"),
        ("Can you switch to the bridge section?", "ブリッジのパートに移ってもらえますか？"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- Sub-batch 1: Instruments (+50) --------------------------------
    # Orchestral strings
    ("cello", "チェロ", "名詞", "She has played the cello since she was six.", "音楽", "400"),
    ("viola", "ヴィオラ", "名詞", "The viola sits between the violin and cello in pitch.", "音楽", "500"),
    ("double bass", "コントラバス", "名詞", "The double bass provides the low end of the string section.", "音楽", "550"),
    ("harp", "ハープ", "名詞", "The harpist plucked a gentle arpeggio.", "音楽", "450"),
    # Woodwinds
    ("clarinet", "クラリネット", "名詞", "He picked up the clarinet in middle school.", "音楽", "450"),
    ("oboe", "オーボエ", "名詞", "The oboe gives the orchestra its tuning note.", "音楽", "550"),
    ("bassoon", "ファゴット", "名詞", "The bassoon has a deep, reedy tone.", "音楽", "600"),
    ("piccolo", "ピッコロ", "名詞", "The piccolo is the smallest and highest member of the flute family.", "音楽", "550"),
    # Brass
    ("French horn", "フレンチホルン", "名詞", "The French horn blends warmly with the strings.", "音楽", "550"),
    ("trombone", "トロンボーン", "名詞", "He slides the trombone to change pitch.", "音楽", "450"),
    ("tuba", "チューバ", "名詞", "The tuba anchors the brass section from below.", "音楽", "500"),
    ("cornet", "コルネット", "名詞", "The cornet looks like a trumpet but has a mellower sound.", "音楽", "650"),
    # Percussion
    ("timpani", "ティンパニ", "名詞", "The timpani rolled dramatically before the finale.", "音楽", "650"),
    ("xylophone", "シロフォン（木琴）", "名詞", "The kids took turns hitting the xylophone.", "音楽", "500"),
    ("marimba", "マリンバ", "名詞", "The marimba has a warmer sound than the xylophone.", "音楽", "650"),
    ("snare drum", "スネアドラム（小太鼓）", "名詞", "The snare drum kept a crisp, steady beat.", "音楽", "550"),
    ("cymbal", "シンバル", "名詞", "He crashed the cymbal at the end of the song.", "音楽", "500"),
    ("tambourine", "タンバリン", "名詞", "She shook the tambourine in time with the music.", "音楽", "450"),
    ("triangle (instrument)", "トライアングル", "名詞", "The triangle adds a light, ringing accent.", "音楽", "400"),
    ("congas", "コンガ", "名詞", "The congas gave the song a Latin groove.", "音楽", "650"),
    ("bongos", "ボンゴ", "名詞", "He tapped out a quick rhythm on the bongos.", "音楽", "650"),
    # World / folk instruments
    ("bagpipes", "バグパイプ", "名詞", "The bagpipes echoed across the hills.", "音楽", "600"),
    ("banjo", "バンジョー", "名詞", "The banjo gives bluegrass music its twangy sound.", "音楽", "550"),
    ("mandolin", "マンドリン", "名詞", "She strummed a folk tune on the mandolin.", "音楽", "600"),
    ("ukulele", "ウクレレ", "名詞", "He learned three chords on the ukulele in an afternoon.", "音楽", "400"),
    ("accordion", "アコーディオン", "名詞", "The accordion is common in folk and tango music.", "音楽", "500"),
    ("sitar", "シタール", "名詞", "The sitar is central to classical Indian music.", "音楽", "700"),
    ("didgeridoo", "ディジュリドゥ", "名詞", "The didgeridoo produces a deep, droning sound.", "音楽", "750"),
    ("harmonica", "ハーモニカ", "名詞", "He played a bluesy riff on the harmonica.", "音楽", "450"),
    # Modern / electronic
    ("synthesizer", "シンセサイザー", "名詞", "The keyboardist layered strings using a synthesizer.", "音楽", "550"),
    ("electric guitar", "エレキギター", "名詞", "He plugged in his electric guitar before the show.", "音楽", "450"),
    ("bass guitar", "ベースギター", "名詞", "The bass guitar locks in with the drums to hold the groove.", "音楽", "450"),
    ("turntable", "ターンテーブル", "名詞", "The DJ scratched the record on the turntable.", "音楽", "600"),
    ("drum machine", "ドラムマシン", "名詞", "The producer programmed a beat on the drum machine.", "音楽", "600"),
    ("MIDI controller", "MIDIコントローラー", "名詞", "She triggers samples with a MIDI controller.", "音楽", "700"),
    ("amplifier (music)", "アンプ", "名詞", "Turn up the amplifier a little for the solo.", "音楽", "500"),
    ("effects pedal", "エフェクトペダル", "名詞", "He stepped on the effects pedal to add distortion.", "音楽", "650"),
    # Instrument-family vocabulary
    ("woodwind section", "木管セクション", "名詞", "The woodwind section carries the main melody here.", "音楽", "700"),
    ("brass section", "金管セクション", "名詞", "The brass section punched in with a bold fanfare.", "音楽", "700"),
    ("string section", "弦楽セクション", "名詞", "The string section swells beneath the vocal line.", "音楽", "700"),
    ("rhythm section", "リズムセクション", "名詞", "The rhythm section kept the whole band locked together.", "音楽", "700"),
    ("conductor's baton", "指揮棒", "名詞", "The conductor's baton cut sharply through the air.", "音楽", "650"),
    ("orchestra pit", "オーケストラピット", "名詞", "The musicians tuned up in the orchestra pit before the curtain rose.", "音楽", "650"),
    # A few more common instruments to round out coverage
    ("bass drum", "バスドラム（大太鼓）", "名詞", "The bass drum thumped a steady four-beat pulse.", "音楽", "500"),
    ("clapper", "クラッパー（拍子木）", "名詞", "The clapper marked the start of each take.", "音楽", "800"),
    ("cowbell", "カウベル", "名詞", "The producer said the track needed more cowbell.", "音楽", "600"),
    ("kazoo", "カズー", "名詞", "The kazoo makes a buzzy, comic sound.", "音楽", "600"),
    ("glockenspiel", "グロッケンシュピール（鉄琴）", "名詞", "The glockenspiel adds a bright, bell-like tone.", "音楽", "700"),
    ("hi-hat", "ハイハット", "名詞", "The drummer kept time with a tight hi-hat pattern.", "音楽", "650"),
    ("pan flute", "パンフルート", "名詞", "The pan flute is made of tubes of different lengths.", "音楽", "600"),

    # --- Sub-batch 2: Specialist / technical music terms (+50) ---------
    # Performance technique
    ("vibrato", "ビブラート", "名詞", "The violinist added vibrato to make the note sing.", "音楽", "800"),
    ("glissando", "グリッサンド（滑奏）", "名詞", "The pianist slid a glissando down the keys.", "音楽", "850"),
    ("arpeggio", "アルペジオ（分散和音）", "名詞", "She practiced arpeggios up and down the scale.", "音楽", "750"),
    ("tremolo", "トレモロ", "名詞", "The strings played a tremolo to build tension.", "音楽", "850"),
    ("pizzicato", "ピチカート", "名詞", "The cellist plucked the strings pizzicato instead of using the bow.", "音楽", "900"),
    ("mute (instrument)", "弱音器・音を弱める", "動詞", "Brass players mute the horn for a softer tone.", "音楽", "700"),
    ("trill", "トリル（装飾的な急速交互演奏）", "名詞", "The flute part ends with a bright trill.", "音楽", "800"),
    ("grace note", "装飾音", "名詞", "A grace note slides quickly into the main note.", "音楽", "850"),
    ("syncopation", "シンコペーション", "名詞", "Jazz relies heavily on syncopation to feel off-beat.", "音楽", "800"),
    ("cadenza", "カデンツァ（独奏者の即興的技巧部分）", "名詞", "The soloist improvised a dazzling cadenza before the finale.", "音楽", "950"),
    # Theory / composition
    ("counterpoint", "対位法", "名詞", "Bach was a master of counterpoint.", "音楽", "900"),
    ("polyphony", "ポリフォニー（多声音楽）", "名詞", "The choir's polyphony wove several melodies together.", "音楽", "900"),
    ("modulation (key)", "転調", "名詞", "The chorus features a modulation up a whole step.", "音楽", "800"),
    ("cadence", "終止形（カデンツ）", "名詞", "The piece ends on a perfect cadence.", "音楽", "800"),
    ("dissonance", "不協和音", "名詞", "The composer used dissonance to create unease.", "音楽", "800"),
    ("consonance", "協和音", "名詞", "The chord resolves from dissonance into consonance.", "音楽", "800"),
    ("timbre", "音色", "名詞", "Each instrument has its own unique timbre.", "音楽", "750"),
    ("overtone", "倍音", "名詞", "The overtone gives the note its rich color.", "音楽", "850"),
    ("ostinato", "オスティナート（反復音型）", "名詞", "The bassline repeats as an ostinato throughout the song.", "音楽", "950"),
    ("motif", "モチーフ（動機）", "名詞", "The four-note motif returns in every movement.", "音楽", "800"),
    ("coda", "コーダ（終結部）", "名詞", "The symphony closes with a triumphant coda.", "音楽", "800"),
    ("bridge (song)", "ブリッジ（サビ前後の橋渡し部分）", "名詞", "The bridge changes the mood before the final chorus.", "音楽", "650"),
    ("hook", "フック（耳に残る印象的な部分）", "名詞", "The song's hook gets stuck in your head instantly.", "音楽", "600"),
    ("key change", "転調", "名詞", "The key change gives the last chorus extra energy.", "音楽", "700"),
    ("atonal", "無調の", "形容詞", "The piece is atonal, with no fixed key center.", "音楽", "900"),
    ("chromatic", "半音階の", "形容詞", "The passage moves in a chromatic scale.", "音楽", "800"),
    # Production / recording
    ("mixing", "ミキシング", "名詞", "The engineer spent hours mixing the vocals and drums.", "音楽", "700"),
    ("mastering", "マスタリング", "名詞", "Mastering makes the whole album sound consistent.", "音楽", "750"),
    ("sample (audio)", "サンプル（音源の抜粋）", "名詞", "The producer looped a drum sample from an old record.", "音楽", "650"),
    ("loop", "ループ（繰り返し再生する音源）", "名詞", "He built the beat around a simple guitar loop.", "音楽", "600"),
    ("overdub", "オーバーダブ（重ね録り）", "名詞", "She recorded harmony vocals as an overdub.", "音楽", "800"),
    ("multitrack", "マルチトラック", "名詞", "The band recorded each instrument on a separate multitrack.", "音楽", "800"),
    ("reverb", "リバーブ（残響効果）", "名詞", "A little reverb makes the vocal sound bigger.", "音楽", "650"),
    ("equalizer", "イコライザー", "名詞", "He used the equalizer to cut some harsh high frequencies.", "音楽", "700"),
    ("click track", "クリックトラック（メトロノーム音源）", "名詞", "The drummer recorded to a click track for a steady tempo.", "音楽", "800"),
    ("session musician", "セッションミュージシャン", "名詞", "A session musician was hired to play strings on the album.", "音楽", "800"),
    ("A&R", "A&R（新人発掘・契約担当）", "名詞", "The A&R rep signed the band after seeing them live.", "音楽", "950"),
    ("royalties", "印税（著作権使用料）", "名詞", "Songwriters earn royalties every time their song is streamed.", "音楽", "850"),
    ("setlist", "セットリスト", "名詞", "The band changed the setlist for the encore.", "音楽", "650"),
    ("soundcheck", "サウンドチェック", "名詞", "The crew ran a soundcheck an hour before doors opened.", "音楽", "650"),
    # Ensemble / performance roles
    ("maestro", "マエストロ（巨匠指揮者）", "名詞", "The maestro raised his hands and the hall fell silent.", "音楽", "850"),
    ("virtuoso", "ヴィルトゥオーゾ（名手）", "名詞", "She is a violin virtuoso admired around the world.", "音楽", "900"),
    ("accompanist", "伴奏者", "名詞", "The singer thanked her accompanist after the recital.", "音楽", "800"),
    ("understudy", "代役", "名詞", "The understudy stepped in when the lead singer got sick.", "音楽", "800"),
    ("principal player", "首席奏者", "名詞", "The principal player leads each section during rehearsal.", "音楽", "850"),
    ("first chair", "首席の座（各パートの首席奏者の席）", "名詞", "She won first chair after a competitive audition.", "音楽", "850"),
    # A few more technical terms rounding out the batch
    ("staccato marking", "スタッカート記号", "名詞", "The staccato marking tells you to play the notes short.", "音楽", "750"),
    ("perfect pitch", "絶対音感", "名詞", "He can name any note instantly thanks to perfect pitch.", "音楽", "850"),
    ("transposing instrument", "移調楽器", "名詞", "The clarinet is a transposing instrument.", "音楽", "990"),
    ("polymeter", "ポリメーター（複数拍子の重なり）", "名詞", "The drummer experimented with polymeter across two time signatures.", "音楽", "990+"),
]


# --- insertion --------------------------------------------------------------


def main() -> int:
    with db() as conn:
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }

        ph_added = ph_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
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

    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("totals -> phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
              "words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
