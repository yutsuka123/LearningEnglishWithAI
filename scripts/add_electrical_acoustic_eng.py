# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""電気工学・電子工学の深掘り語（既存の「電気電子」に追加）＋音響工学
(新設), authored by Claude (2026-08-05・ユーザー要望:「電気工学　電子工学
…音響工学…増やしましょうか」＋「質は落とさないように、段階的に実装くだ
さい」).

既存の「電気電子」(78語)はアマチュア無線・回路部品が中心だったため、
電磁気学の法則・パワーエレクトロニクス・AD/DA変換等の理論語を補強。
「音響工学」は既存分野に該当が無かったため新設。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table.

Run:  python scripts/add_electrical_acoustic_eng.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

ELEC = "電気電子"
ACOUSTIC = "音響工学"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 電気工学・電子工学の深掘り語 ---
    ("Ohm's law", "オームの法則", "名詞", "Ohm's law relates voltage, current, and resistance in a simple equation.", ELEC, "700"),
    ("Kirchhoff's law", "キルヒホッフの法則", "名詞", "Kirchhoff's law says the currents flowing into a junction must equal the currents flowing out.", ELEC, "850"),
    ("electromagnetic induction", "電磁誘導", "名詞", "Electromagnetic induction generates a voltage when a magnetic field changes near a conductor.", ELEC, "850"),
    ("Faraday's law of induction", "ファラデーの電磁誘導の法則", "名詞", "Faraday's law of induction is the basis for how generators and transformers work.", ELEC, "900"),
    ("three-phase power", "三相電力", "名詞", "Three-phase power delivers electricity more efficiently than a single-phase line.", ELEC, "850"),
    ("power factor", "力率", "名詞", "A low power factor means the equipment draws more current than it actually needs.", ELEC, "900"),
    ("RLC circuit", "RLC回路", "名詞", "An RLC circuit combines a resistor, an inductor, and a capacitor.", ELEC, "900"),
    ("analog-to-digital converter", "アナログ-デジタル変換器（ADC）", "名詞", "An analog-to-digital converter turns a continuous voltage signal into numbers a computer can read.", ELEC, "850"),
    ("digital-to-analog converter", "デジタル-アナログ変換器（DAC）", "名詞", "A digital-to-analog converter turns numbers back into a smooth voltage signal.", ELEC, "850"),
    ("programmable logic controller (PLC)", "プログラマブルロジックコントローラ（PLC）", "名詞", "A programmable logic controller runs the automated sequence on a factory floor.", ELEC, "850"),
    ("power electronics", "パワーエレクトロニクス", "名詞", "Power electronics converts and controls electrical energy efficiently between voltages.", ELEC, "850"),
    ("inverter (power electronics)", "インバーター", "名詞", "An inverter converts direct current from a solar panel into alternating current for the home.", ELEC, "750"),
    ("motor driver", "モータードライバー", "名詞", "The motor driver controls how much current reaches the motor at any moment.", ELEC, "800"),
    ("battery management system", "バッテリーマネジメントシステム（BMS）", "名詞", "A battery management system keeps every cell charging and discharging safely.", ELEC, "850"),
    ("photodiode", "フォトダイオード", "名詞", "A photodiode converts light falling on it into a small electric current.", ELEC, "800"),
    ("ground fault", "地絡・接地障害", "名詞", "A ground fault sends current through an unintended path, often tripping a breaker.", ELEC, "850"),
    ("power supply unit", "電源ユニット", "名詞", "The power supply unit converts household AC into the DC voltages a computer needs.", ELEC, "650"),
    ("surge protector", "サージ保護器", "名詞", "A surge protector shields sensitive electronics from a sudden voltage spike.", ELEC, "700"),
    ("electromagnetic interference", "電磁干渉（EMI）", "名詞", "Electromagnetic interference from a nearby motor caused static on the radio.", ELEC, "850"),
    ("signal-to-noise ratio", "信号対雑音比（SNR）", "名詞", "A higher signal-to-noise ratio makes the recording sound much clearer.", ELEC, "800"),
    # --- 音響工学（新設） ---
    ("acoustics", "音響学・音響工学", "名詞", "Acoustics studies how sound behaves as it travels through air, water, or solid materials.", ACOUSTIC, "700"),
    ("acoustic engineer", "音響エンジニア", "名詞", "An acoustic engineer designed the concert hall to sound clear from every seat.", ACOUSTIC, "750"),
    ("decibel", "デシベル（dB）", "名詞", "A quiet library measures around thirty decibels.", ACOUSTIC, "650"),
    ("sound pressure level", "音圧レベル", "名詞", "The sound pressure level near the jet engine was dangerously high.", ACOUSTIC, "850"),
    ("reverberation", "残響", "名詞", "Reverberation in the empty stone church made every footstep echo.", ACOUSTIC, "800"),
    ("reverberation time", "残響時間", "名詞", "A shorter reverberation time makes speech easier to understand in a large room.", ACOUSTIC, "900"),
    ("echo (acoustics)", "エコー・反響", "名詞", "An echo bounced back from the canyon wall a few seconds later.", ACOUSTIC, "600"),
    ("soundproofing", "防音", "名詞", "Soundproofing on the walls kept the recording studio quiet inside.", ACOUSTIC, "700"),
    ("acoustic absorption", "吸音", "名詞", "Acoustic absorption panels reduce how much sound bounces around a room.", ACOUSTIC, "850"),
    ("acoustic insulation", "遮音", "名詞", "Acoustic insulation between floors keeps noise from traveling between apartments.", ACOUSTIC, "800"),
    ("resonant frequency", "共振周波数", "名詞", "A bridge can be damaged if wind matches its resonant frequency.", ACOUSTIC, "900"),
    ("sound wave", "音波", "名詞", "A sound wave needs a medium like air or water to travel through.", ACOUSTIC, "600"),
    ("waveform (acoustics)", "波形（音の）", "名詞", "The waveform on the screen showed a sharp spike at the moment of impact.", ACOUSTIC, "750"),
    ("frequency response", "周波数応答", "名詞", "A good speaker has a flat frequency response across the whole range of hearing.", ACOUSTIC, "850"),
    ("directivity (acoustics)", "指向性（音響の）", "名詞", "A microphone's directivity determines which direction it picks up sound from best.", ACOUSTIC, "900"),
    ("anechoic chamber", "無響室", "名詞", "Engineers test speakers inside an anechoic chamber where no sound reflects at all.", ACOUSTIC, "900"),
    ("ultrasound (acoustics)", "超音波", "名詞", "Ultrasound frequencies are too high for the human ear to hear.", ACOUSTIC, "700"),
    ("infrasound", "超低周波音", "名詞", "Infrasound below human hearing can still be felt as a vibration.", ACOUSTIC, "850"),
    ("noise cancellation", "ノイズキャンセリング", "名詞", "Noise cancellation headphones create an opposite wave to cancel out background sound.", ACOUSTIC, "750"),
    ("architectural acoustics", "建築音響学", "名詞", "Architectural acoustics shapes the ceiling of a concert hall to spread sound evenly.", ACOUSTIC, "900"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
