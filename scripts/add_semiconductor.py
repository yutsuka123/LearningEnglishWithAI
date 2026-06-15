# ruff: noqa: E501
"""Semiconductor vocabulary: devices, memory types, processors, fabrication,
and industry jargon. Authored by Claude — no app/OpenAI API calls. Dedupe on
english; back-fill empty examples. domain="半導体".

Run: python scripts/add_semiconductor.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# group -> (level, [(english, japanese, example)])
GROUPS: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "素子・種類": ("800", [
        ("semiconductor", "半導体", "Silicon is the most common semiconductor."),
        ("integrated circuit", "集積回路(IC)", "An integrated circuit packs many transistors."),
        ("chip", "半導体チップ", "The chip controls the whole device."),
        ("wafer", "ウェハー", "Chips are cut from a silicon wafer."),
        ("die", "ダイ・素子片", "Each die becomes one chip."),
        ("transistor", "トランジスタ", "A transistor switches or amplifies signals."),
        ("MOSFET", "電界効果トランジスタ(MOSFET)", "The MOSFET is the basic switch in chips."),
        ("LED", "発光ダイオード(LED)", "LEDs are efficient light sources."),
        ("n-type", "n型半導体", "N-type silicon has extra electrons."),
        ("p-type", "p型半導体", "P-type silicon has electron holes."),
        ("doping", "ドーピング・不純物添加", "Doping changes the conductivity."),
        ("dopant", "ドーパント・不純物", "Boron is a common dopant."),
        ("junction", "接合(pn接合)", "A pn junction forms a diode."),
        ("band gap", "バンドギャップ", "The band gap sets the material's behavior."),
        ("carrier", "キャリア(電荷担体)", "Electrons and holes are charge carriers."),
        ("gate", "ゲート(電極)", "Voltage on the gate controls the current."),
        ("substrate", "基板(半導体基板)", "The circuit sits on a silicon substrate."),
    ]),
    "メモリ": ("800", [
        ("RAM", "ランダムアクセスメモリ(RAM)", "RAM holds data while the computer runs."),
        ("ROM", "読み出し専用メモリ(ROM)", "ROM stores permanent firmware."),
        ("DRAM", "動的RAM(DRAM)", "DRAM must be refreshed constantly."),
        ("SRAM", "静的RAM(SRAM)", "SRAM is fast but expensive."),
        ("flash memory", "フラッシュメモリ", "Flash memory keeps data without power."),
        ("NAND flash", "NANDフラッシュ", "NAND flash stores data in SSDs."),
        ("NOR flash", "NORフラッシュ", "NOR flash allows fast random reads."),
        ("FRAM", "強誘電体メモリ(FeRAM/FRAM)", "FRAM is fast and non-volatile."),
        ("MRAM", "磁気抵抗メモリ(MRAM)", "MRAM stores bits magnetically."),
        ("EEPROM", "電気的消去可能ROM(EEPROM)", "EEPROM can be erased electrically."),
        ("cache", "キャッシュメモリ", "The cache speeds up the processor."),
        ("volatile memory", "揮発性メモリ", "Volatile memory loses data when powered off."),
        ("non-volatile memory", "不揮発性メモリ", "Non-volatile memory retains data."),
    ]),
    "プロセッサ": ("800", [
        ("CPU", "中央処理装置(CPU)", "The CPU executes program instructions."),
        ("GPU", "画像処理装置(GPU)", "A GPU accelerates graphics and AI."),
        ("microprocessor", "マイクロプロセッサ", "A microprocessor is a CPU on one chip."),
        ("microcontroller", "マイコン・マイクロコントローラ", "A microcontroller runs small devices."),
        ("SoC", "システムオンチップ(SoC)", "A smartphone uses a single SoC."),
        ("core", "コア", "This CPU has eight cores."),
        ("clock speed", "クロック周波数", "Higher clock speed means faster work."),
        ("instruction set", "命令セット", "ARM uses a different instruction set."),
        ("FPGA", "書き換え可能ロジック(FPGA)", "An FPGA can be reprogrammed in the field."),
        ("ASIC", "特定用途集積回路(ASIC)", "An ASIC is built for a single task."),
        ("NPU", "AI処理ユニット(NPU)", "The NPU speeds up neural networks."),
    ]),
    "製造": ("900", [
        ("fabrication", "製造・ファブ", "Chip fabrication needs a clean room."),
        ("photolithography", "フォトリソグラフィ", "Photolithography prints the circuit pattern."),
        ("etching", "エッチング", "Etching removes unwanted material."),
        ("deposition", "成膜・蒸着", "Deposition adds thin layers to the wafer."),
        ("ion implantation", "イオン注入", "Ion implantation dopes the silicon."),
        ("photoresist", "フォトレジスト", "Light hardens the photoresist."),
        ("photomask", "フォトマスク", "The photomask defines the pattern."),
        ("clean room", "クリーンルーム", "Chips are made in a clean room."),
        ("yield", "歩留まり", "A higher yield lowers the cost per chip."),
        ("process node", "プロセスノード", "The chip uses a five-nanometer node."),
        ("nanometer", "ナノメートル", "Transistors are only a few nanometers wide."),
        ("packaging", "パッケージング・封止", "Packaging protects the bare die."),
        ("dicing", "ダイシング(切断)", "Dicing cuts the wafer into chips."),
        ("annealing", "アニール・熱処理", "Annealing repairs the crystal lattice."),
        ("epitaxy", "エピタキシャル成長", "Epitaxy grows a clean crystal layer."),
    ]),
    "業界": ("900", [
        ("foundry", "ファウンドリ(受託製造)", "TSMC is a leading semiconductor foundry."),
        ("fabless", "ファブレス", "A fabless firm designs chips but does not make them."),
        ("IDM", "垂直統合型メーカー(IDM)", "Intel is a classic IDM."),
        ("tape-out", "テープアウト(設計完了)", "The chip design reached tape-out."),
        ("EDA", "電子設計自動化(EDA)", "EDA tools design the circuits."),
        ("Moore's law", "ムーアの法則", "Moore's law predicts shrinking transistors."),
        ("supply chain", "サプライチェーン", "A chip shortage disrupted the supply chain."),
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
                    (en, ja, "", ex, "半導体", level),
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
