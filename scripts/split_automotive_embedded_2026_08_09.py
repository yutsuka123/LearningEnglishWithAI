# ruff: noqa: E501
"""「車載組込み開発」ドメインを3分類に再編する(2026-08-09)。

ユーザー要望: 「車載組み込み開発は→分類を組み込み開発・車載開発用語・
自動車産業とし、それぞれ適切に分類し単語、フレーズ拡張しましょう」。

既存の`車載組込み開発`domain(単語109語)・`車載組込み開発の英語`scene
(フレーズ49件)を、内容に基づいて以下2つへ再分類する
(`自動車産業`は既存語が無いため本スクリプトでは再分類対象なし。
別途新規語彙をadd_automotive_industry_2026_08_09.py等で追加する):

- `組み込み開発`: 自動車に限らない一般的な組込みソフト/RTOS/ハードウェア
  インタフェース・検証手法(V-model/MILS-SILS-HILS-PILS等)・一般的な
  機能安全概念(FMEA/redundancy/fail-safe等)。
- `車載開発`: CAN/LIN/FlexRay/AUTOSAR/ISO26262/ASIL/ECU/ADAS等、
  自動車固有の規格・プロトコル・車両制御に関する語。

Run:  python scripts/split_automotive_embedded_2026_08_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

OLD_WORD_DOMAIN = "車載組込み開発"
OLD_PHRASE_SCENE = "車載組込み開発の英語"

EMBEDDED_GENERAL_WORDS = {
    "V-model", "MILS", "SILS", "HILS", "PILS", "requirement traceability",
    "unit test level", "integration test level", "system test level",
    "acceptance test", "back-to-back testing", "fault injection testing",
    "functional safety", "fail-safe", "fail-operational", "safety goal",
    "hazard analysis", "FMEA", "redundancy", "watchdog timer", "safe state",
    "RTOS", "task scheduling", "interrupt latency", "memory footprint",
    "board support package", "cross-compilation", "target hardware",
    "bench test", "closed-loop control", "open-loop control",
    "sensor signal", "over-the-air update", "OTA", "bit-banging",
    "volatile keyword", "linker script", "safety element out of context",
    "rate monotonic scheduling", "priority inversion", "context switch",
    "GPIO", "debounce", "pull-up resistor", "UART", "SPI", "I2C", "JTAG",
    "PWM", "duty cycle", "hysteresis", "common cause failure",
    "diagnostic coverage", "MC/DC coverage", "freedom from interference",
}

AUTOMOTIVE_WORDS = {
    "CAN bus", "CAN frame", "LIN bus", "FlexRay", "automotive Ethernet",
    "gateway ECU", "in-vehicle network", "diagnostic trouble code", "DTC",
    "OBD-II", "UDS", "CAN ID", "bus load", "network topology", "ISO 26262",
    "ASIL", "ECU", "ECU flashing", "calibration data", "A2L file",
    "AUTOSAR", "basic software", "application software layer",
    "hardware abstraction layer", "in-vehicle test", "cold start test",
    "key-on/key-off cycle", "powertrain", "chassis control",
    "body control module", "ADAS", "sensor fusion", "drive-by-wire",
    "brake-by-wire", "telematics", "infotainment system", "CAN FD",
    "bit stuffing", "bus arbitration", "CAN transceiver",
    "termination resistor", "bus-off", "RTE", "security access",
    "seed-and-key authentication", "end-to-end protection", "DBC file",
    "CAPL", "XCP protocol", "J1939", "SENT protocol", "bus guardian",
    "limp-home mode", "torque vectoring",
}

EMBEDDED_GENERAL_PHRASES = {
    "Can we run this on the HILS bench first?",
    "We found the root cause during back-to-back testing.",
    "The watchdog timer reset the ECU unexpectedly.",
    "Let's move this test case from SILS to HILS.",
    "What's causing the interrupt latency spike?",
    "We need to update the requirement traceability matrix.",
    "We're cross-compiling for the target hardware this afternoon.",
    "The safety goal wasn't fully covered by the current test cases.",
    "Let's run an FMEA on the new sensor architecture.",
    "Is the redundant actuator wired to a separate power supply?",
    "We can push this fix out as an over-the-air update.",
    "Let's check whether it's still in open-loop control at that point.",
    "Can you prove freedom from interference between these two partitions?",
    "That looks like a common cause failure, not two independent faults.",
    "What's the diagnostic coverage for this safety mechanism?",
    "We still need MC/DC coverage before this can ship.",
    "We ended up bit-banging it since there was no free peripheral.",
    "Add some hysteresis so the warning light doesn't flicker.",
    "Did you forget the volatile keyword on that register variable?",
    "Check the linker script if the vector table isn't landing at the right address.",
    "We had a priority inversion because the low-priority task was holding the mutex.",
    "Which GPIO pin is the status LED wired to?",
    "Don't forget to debounce that button in software.",
    "Let's check the signal on the oscilloscope before blaming the firmware.",
    "I think we have a race condition between the ISR and the main loop.",
    "Is this a fail-safe or fail-operational requirement?",
}

NEW_WORD_DOMAIN_GENERAL = "組み込み開発"
NEW_WORD_DOMAIN_AUTOMOTIVE = "車載開発"
NEW_PHRASE_SCENE_GENERAL = "組み込み開発の英語"
NEW_PHRASE_SCENE_AUTOMOTIVE = "車載開発の英語"


def main() -> int:
    with db() as conn:
        rows = conn.execute(
            "SELECT id, english FROM words WHERE domain=?", (OLD_WORD_DOMAIN,)
        ).fetchall()
        w_general = w_auto = w_unclassified = 0
        for r in rows:
            if r["english"] in EMBEDDED_GENERAL_WORDS:
                conn.execute("UPDATE words SET domain=? WHERE id=?",
                             (NEW_WORD_DOMAIN_GENERAL, r["id"]))
                w_general += 1
            elif r["english"] in AUTOMOTIVE_WORDS:
                conn.execute("UPDATE words SET domain=? WHERE id=?",
                             (NEW_WORD_DOMAIN_AUTOMOTIVE, r["id"]))
                w_auto += 1
            else:
                print(f"  [WARN] unclassified word: {r['english']!r} (id={r['id']})")
                w_unclassified += 1

        prows = conn.execute(
            "SELECT id, english FROM phrases WHERE scene=?", (OLD_PHRASE_SCENE,)
        ).fetchall()
        p_general = p_auto = p_unclassified = 0
        for r in prows:
            if r["english"] in EMBEDDED_GENERAL_PHRASES:
                conn.execute("UPDATE phrases SET scene=? WHERE id=?",
                             (NEW_PHRASE_SCENE_GENERAL, r["id"]))
                p_general += 1
            else:
                conn.execute("UPDATE phrases SET scene=? WHERE id=?",
                             (NEW_PHRASE_SCENE_AUTOMOTIVE, r["id"]))
                p_auto += 1

    print(f"words -> 組み込み開発: {w_general}, 車載開発: {w_auto}, unclassified: {w_unclassified}")
    print(f"phrases -> 組み込み開発の英語: {p_general}, 車載開発の英語: {p_auto}")

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
