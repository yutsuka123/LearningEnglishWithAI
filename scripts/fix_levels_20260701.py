"""新規追加語(2026-07-01)の TOEIC レベルを語ごとに補正する。

seed_domains_20260701.py はドメイン一律の level を付けたため、語ごとの実難易度と
ずれがある（例: hammer/nail/saw を 600、trash と declutter を同じ 400 など）。
本スクリプトは english→妥当 level の対応表で、本日追加した行だけを UPDATE する。

TOEIC 帯の目安:
  400 = 基礎日常語 / 500 = よく使う語 / 600 = 中級 / 700 = 中上級 /
  800 = 上級・専門 / 900 = 高度な専門用語

使い方:
  python scripts/fix_levels_20260701.py            # 適用
  python scripts/fix_levels_20260701.py --dry-run  # 変更内容だけ表示
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# english -> 妥当な TOEIC level（本日追加分のみ対象・50点単位）
LEVELS: dict[str, str] = {
    # IT / インターネット
    "browser": "400", "cookie": "450", "streaming": "450", "hotspot": "500",
    "cloud storage": "500", "IP address": "550", "domain name": "550",
    "VPN": "650", "data breach": "650", "bandwidth throttling": "700",
    "two-factor authentication": "650",
    # 政治(→ニュース)
    "democracy": "600", "opposition": "600", "election campaign": "600",
    "ballot": "600", "cabinet": "650", "diplomacy": "700",
    "approval rating": "700", "veto": "700", "coalition": "750",
    "constituency": "800", "referendum": "800", "amendment": "800",
    "bureaucracy": "800", "incumbent": "800", "lobbying": "800",
    "regime": "800", "caucus": "900",
    # 経営(→ビジネス)
    "market share": "600", "KPI": "700", "benchmark": "700",
    "cash flow": "650", "delegation": "700", "outsourcing": "700",
    "overhead": "700", "profit margin": "650", "restructuring": "750",
    "revenue stream": "700", "turnover": "650", "due diligence": "800",
    "procurement": "750", "liquidity crunch": "800",
    # 経済学
    "interest rate": "600", "unemployment rate": "600",
    "supply and demand": "600", "capital": "550", "exchange rate": "650",
    "trade deficit": "700", "purchasing power": "700",
    "household spending": "700", "bond": "650", "commodity": "700",
    "stimulus": "700", "gross domestic product": "750",
    "depreciation": "800", "liquidity": "800", "stagnation": "800",
    # 気象・地学
    "frost": "500", "drought": "600", "hail": "600", "gust": "650",
    "humidity": "550", "heat wave": "550", "thunderstorm": "550",
    "typhoon": "550", "visibility": "600", "overcast": "650",
    "landslide": "600", "cold front": "600", "evaporation": "600",
    "air mass": "700", "barometer": "700", "atmospheric pressure": "700",
    "cyclone": "700", "precipitation": "700", "low-pressure system": "700",
    "wind chill": "700", "fault line": "700", "volcanic eruption": "700",
    "meteorology": "800", "dew point": "800", "jet stream": "800",
    "bedrock": "800", "continental drift": "800", "geothermal": "800",
    "cumulonimbus": "900", "strata": "850", "subduction": "900",
    # 家電
    "filter": "400", "timer": "400", "microwave oven": "450",
    "air purifier": "500", "battery charger": "500", "power cord": "500",
    "dehumidifier": "600", "induction cooktop": "600", "thermostat": "600",
    "energy efficiency": "600", "standby power": "650",
    # DIY・工具(→機械工学)
    "hammer": "350", "nail": "350", "saw": "400", "screwdriver": "450",
    "wrench": "500", "pliers": "500", "clamp": "500", "level": "450",
    "washer": "500", "sandpaper": "500", "tape measure": "450",
    "utility knife": "500", "power tool": "500", "adhesive": "500",
    "hinge": "500", "chisel": "600", "bracket": "600", "workbench": "600",
    "varnish": "600", "grout": "700", "caulk": "700", "stud finder": "700",
    # ロボット工学(→機械工学)
    "controller": "700", "gripper": "700", "calibration": "800",
    "feedback loop": "800", "gyroscope": "800", "servo motor": "800",
    "path planning": "800", "obstacle avoidance": "800",
    "degrees per second": "800", "encoder": "800",
    "degrees of freedom": "900", "end effector": "900", "actuation": "900",
    "lidar": "900", "manipulator": "900", "odometry": "950",
    "teleoperation": "900",
    # 法律
    "bail": "700", "intellectual property": "700",
    "breach of contract": "800", "due process": "800",
    # 原子力(→物理)
    "contamination": "700", "nuclear reactor": "800", "chain reaction": "800",
    "meltdown": "800", "shielding": "800", "decay": "800",
    "radioactive waste": "800", "thermal power": "800", "control rod": "800",
    "reactor core": "800", "spent fuel": "800", "containment vessel": "900",
    "criticality": "900", "dosimeter": "900", "enrichment": "900",
    "moderator": "900", "gamma ray": "900", "decommissioning": "900",
    # 家事(→生活)
    "dust": "400", "fold": "400", "mop": "400", "rinse": "400",
    "wipe": "400", "trash": "400", "vacuum": "450", "hang out": "450",
    "scrub": "500", "stain": "500", "detergent": "500", "dishcloth": "500",
    "clothesline": "500", "spring cleaning": "550", "tidy up": "500",
    "household": "550", "leftovers": "500", "errand": "600",
    "declutter": "700",
    # 航空(管制・乗務 / 工学)(→航空・宇宙)
    "boarding pass": "500", "emergency exit": "500", "cabin crew": "600",
    "layover": "600", "standby": "600", "touchdown": "650",
    "air traffic control": "700", "callsign": "700", "clearance": "700",
    "heading": "700", "crosswind": "700", "cruising speed": "700",
    "landing gear": "700", "jet bridge": "700", "stall": "700",
    "apron": "800", "de-icing": "800", "flight level": "800",
    "go-around": "800", "holding pattern": "800", "purser": "800",
    "pushback": "800", "taxiway": "800", "transponder": "800",
    "cabin pressure": "800", "airfoil": "900", "airframe": "900",
    "angle of attack": "900", "avionics": "900", "bank angle": "900",
    "flight envelope": "900", "thermal protection": "900", "winglet": "900",
    # 電気・電子・無線(→電気電子)
    "digital": "500", "static": "550", "analog": "600", "antenna": "600",
    "noise": "600", "sensor": "600", "watt": "600", "wiring": "600",
    "power outage": "600", "power supply": "650", "bit": "600",
    "soldering": "650", "receiver": "650",
    "alternating current": "700", "direct current": "700",
    "circuit breaker": "700", "power grid": "700", "load": "700",
    "clock": "700", "register": "700", "electrode": "700",
    "solder joint": "700", "call sign": "700", "frequency band": "700",
    "gain": "750", "line of sight": "700", "relay station": "700",
    "repeater": "700", "signal strength": "700", "transmitter": "700",
    "amateur radio": "700", "switchgear": "800", "logic circuit": "800",
    "op-amp": "800", "oscilloscope": "800", "encoding": "800",
    "bandpass filter": "900", "bandwidth allocation": "900",
    "carrier wave": "900", "dipole": "900", "handheld transceiver": "900",
    "propagation": "850", "squelch": "900",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    changed = same = missing = 0
    with db() as conn:
        # 本日追加した新規語だけを対象にする
        rows = {r["english"]: r["level"] for r in conn.execute(
            "SELECT english, level FROM words WHERE created_at = date('now')")}
        for en, lvl in LEVELS.items():
            if en not in rows:
                missing += 1
                print(f"  [対象外/未検出] {en}")
                continue
            if rows[en] == lvl:
                same += 1
                continue
            changed += 1
            print(f"  {en}: {rows[en]} → {lvl}")
            if not args.dry_run:
                conn.execute(
                    "UPDATE words SET level = ? "
                    "WHERE english = ? AND created_at = date('now')",
                    (lvl, en))
        if not args.dry_run:
            conn.commit()

    # 対応表に無い新規語（=一律levelのまま妥当とみなした語）も一覧
    print("---")
    print(f"変更 {changed} / 据置 {same} / 未検出 {missing}")
    if args.dry_run:
        print("[dry-run] 適用しませんでした。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
