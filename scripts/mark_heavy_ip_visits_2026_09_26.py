# ruff: noqa: E501
"""過去のlanding_visitsのうち、同一IPが短時間に大量に着地した行へbot_mark=5(MARK_HEAVY_IP)を付け直す(2026-09-26)。

新規の訪問はapp/main.pyが記録時に判定する(visitor_kind.is_heavy_ip)。これは、それ以前(例: 2026-09-23に1つのIPが
1時間に364回・UAは普通のブラウザでbot_mark=0のまま人間の訪問に混ざっていた)の分析を揃えるための1回限りの補正。
判定=visitor_kind.HEAVY_IP_LIMIT回以上/HEAVY_IP_WINDOW(10分)を、同一IP・自分の端末(is_internal=1)を除いて満たした窓に含まれる行。
logs.dbのlanding_visitsだけを更新(bot_markの列のみ)。dry-run既定・バックアップ+ロールバック・冪等。
バックアップは既定でDATA_DIR/script_backups(本番コンテナでもホストに残る)。dry-runは対象IPの内訳(短縮ハッシュ)を表示する。
使い方: python scripts/mark_heavy_ip_visits_2026_09_26.py [--apply | --rollback <バックアップJSON>] [--backup-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _db_safety import default_backup_dir, key_counts, print_counts, same_counts  # noqa: E402
from app.database import db  # noqa: E402
from app.services import visitor_kind  # noqa: E402

WINDOW_SEC = 600  # visitor_kind.HEAVY_IP_WINDOW(-10 minutes)と同じ


def _ts(s: str) -> float:
    return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--rollback", metavar="BACKUP_JSON")
    ap.add_argument("--backup-dir", default=None, help="既定 DATA_DIR/script_backups")
    args = ap.parse_args()
    with db() as conn:
        if args.rollback:
            rows = json.loads(Path(args.rollback).read_text(encoding="utf-8"))
            for r in rows:
                conn.execute("UPDATE landing_visits SET bot_mark = ? WHERE id = ?", (r["bot_mark"], r["id"]))
            conn.commit()
            print(f"ロールバック: {len(rows)}行のbot_markを戻しました")
            return 0
        total = conn.execute("SELECT COUNT(*) FROM landing_visits").fetchone()[0]
        before = key_counts(conn)
        per: dict[str, list[tuple[float, int, int]]] = defaultdict(list)
        for r in conn.execute(
            "SELECT id, ip, created_at, COALESCE(bot_mark, 0) AS m FROM landing_visits "
            "WHERE is_internal = 0 AND COALESCE(kind, 'visit') = 'visit' AND ip != '' ORDER BY created_at"):
            per[r["ip"]].append((_ts(r["created_at"]), r["id"], r["m"]))
        targets: list[int] = []
        ips = set()
        for ip, lst in per.items():
            hit = [False] * len(lst)
            j = 0
            for i, (t, _id, _m) in enumerate(lst):
                while t - lst[j][0] > WINDOW_SEC:
                    j += 1
                if i - j + 1 >= visitor_kind.HEAVY_IP_LIMIT:
                    for k in range(j, i + 1):
                        hit[k] = True
            for k, flag in enumerate(hit):
                if flag and lst[k][2] == 0:
                    targets.append(lst[k][1])
                    ips.add(ip)
        print(f"対象 {len(targets)}行 / {len(ips)}IP / landing_visits全体 {total}行(印を付けるのはbot_mark=0の行だけ)")
        # 適用前に「実ユーザーではないか」を判断できるよう、対象IPの内訳(IPは短縮ハッシュ)を出す
        import hashlib
        by_ip: dict[str, int] = defaultdict(int)
        first: dict[str, str] = {}
        tset = set(targets)
        for ip, lst in per.items():
            for t, _id, _m in lst:
                if _id in tset:
                    by_ip[ip] += 1
                    first.setdefault(ip, datetime.fromtimestamp(t, timezone.utc).strftime("%m/%d %H:%M"))
        for ip, n in sorted(by_ip.items(), key=lambda kv: -kv[1])[:20]:
            ua = conn.execute("SELECT user_agent FROM landing_visits WHERE ip = ? ORDER BY id LIMIT 1", (ip,)).fetchone()
            print(f"    [{hashlib.sha256(('f2b-' + ip).encode()).hexdigest()[:8]}] {n}行 初回{first[ip]}(UTC) UA={(ua[0] or '')[:48] if ua else ''}")
        if not args.apply or not targets:
            print("dry-runです(何も書いていません)。" if not args.apply else "対象なし。")
            return 0
        print_counts("更新前", before)
        bdir = Path(args.backup_dir) if args.backup_dir else default_backup_dir()
        bpath = bdir / f"backup_heavy_ip_{time.strftime('%Y%m%d_%H%M%S')}.json"
        bpath.parent.mkdir(parents=True, exist_ok=True)
        bpath.write_text(json.dumps([{"id": i, "bot_mark": 0} for i in targets]), encoding="utf-8")
        print(f"バックアップ: {bpath}")
        for i in targets:
            conn.execute("UPDATE landing_visits SET bot_mark = ? WHERE id = ? AND COALESCE(bot_mark, 0) = 0",
                         (visitor_kind.MARK_HEAVY_IP, i))
        conn.commit()
        after = conn.execute("SELECT COUNT(*) FROM landing_visits").fetchone()[0]
        after_counts = key_counts(conn)
    print_counts("更新後", after_counts)
    print(f"反映しました: {len(targets)}行(landing_visits {total}→{after}行・変わっていないこと)")
    if not same_counts(before, after_counts):
        print("⚠️ 主要テーブルの件数が更新前後で変わっています。直ちに--rollbackを検討してください。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
