"""管理者CLI（§A マルチユーザー化）。

管理者がユーザーのID/パスワードを割当て、AI利用の日次/月次上限や前払い残高を
設定する。将来はユーザー自身が設定画面から変更できるようにする（当面はCLI）。

使い方:
  python scripts/admin.py init                      # スキーマ作成/移行
  python scripts/admin.py list
  python scripts/admin.py create <username> --password PASS [--role user|admin]
        [--display 表示名] [--daily 5.0] [--monthly 50.0] [--balance 500]
  python scripts/admin.py passwd <username> <newpass>
  python scripts/admin.py setcap <username> [--daily 5.0] [--monthly 50.0]
  python scripts/admin.py setbalance <username> <amount_jpy>   # 絶対値
  python scripts/admin.py charge <username> <delta_jpy>        # 増減
  python scripts/admin.py activate <username>
  python scripts/admin.py deactivate <username>

上限は USD（ai_usage.cost_usd と同単位）。残高は ¥。--daily 等に 0 を渡すと
グローバル既定にフォールバック（= 個別上限なし）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db, init_db  # noqa: E402
from app.services import auth  # noqa: E402


def _print_users(rows: list[dict]) -> None:
    if not rows:
        print("（ユーザーなし）")
        return
    print(f"{'id':>3} {'username':<16} {'role':<6} {'act':<3} "
          f"{'daily$':>7} {'month$':>7} {'¥bal':>9}")
    for u in rows:
        d = u["daily_cost_cap_usd"]
        m = u["monthly_cost_cap_usd"]
        b = u["balance_jpy"]
        print(f"{u['id']:>3} {u['username']:<16} {u['role']:<6} "
              f"{'on' if u['is_active'] else 'off':<3} "
              f"{('-' if d is None else d):>7} "
              f"{('-' if m is None else m):>7} "
              f"{('-' if b is None else round(b)):>9}")


def _require(conn, username: str) -> dict:
    u = auth.get_user_by_name(conn, username)
    if not u:
        print(f"エラー: ユーザー '{username}' が見つかりません。")
        sys.exit(1)
    return u


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")
    sub.add_parser("list")

    c = sub.add_parser("create")
    c.add_argument("username")
    c.add_argument("--password", default="")
    c.add_argument("--role", default="user", choices=["user", "admin"])
    c.add_argument("--display", default="")
    c.add_argument("--daily", type=float, default=None)
    c.add_argument("--monthly", type=float, default=None)
    c.add_argument("--balance", type=float, default=None)

    p = sub.add_parser("passwd")
    p.add_argument("username")
    p.add_argument("password")

    sc = sub.add_parser("setcap")
    sc.add_argument("username")
    sc.add_argument("--daily", type=float, default=None)
    sc.add_argument("--monthly", type=float, default=None)

    sb = sub.add_parser("setbalance")
    sb.add_argument("username")
    sb.add_argument("amount", type=float)

    ch = sub.add_parser("charge")
    ch.add_argument("username")
    ch.add_argument("delta", type=float)

    av = sub.add_parser("activate")
    av.add_argument("username")
    da = sub.add_parser("deactivate")
    da.add_argument("username")

    args = ap.parse_args()

    if args.cmd == "init":
        init_db()
        print("スキーマ作成/移行 完了。")
        return 0

    with db() as conn:
        if args.cmd == "list":
            _print_users(auth.list_users(conn))
        elif args.cmd == "create":
            if auth.get_user_by_name(conn, args.username):
                print(f"エラー: '{args.username}' は既に存在します。")
                return 1
            uid = auth.create_user(
                conn, args.username, args.password, role=args.role,
                display_name=args.display,
                daily_cap_usd=(args.daily or None),
                monthly_cap_usd=(args.monthly or None),
                balance_jpy=args.balance,
            )
            print(f"作成: id={uid} username={args.username} role={args.role}"
                  + ("" if args.password else "  ※パスワード未設定"
                     "（passwd で設定）"))
        elif args.cmd == "passwd":
            u = _require(conn, args.username)
            auth.set_password(conn, u["id"], args.password)
            print(f"パスワード更新: {args.username}")
        elif args.cmd == "setcap":
            u = _require(conn, args.username)
            auth.set_caps(conn, u["id"],
                          daily_cap_usd=(args.daily or None),
                          monthly_cap_usd=(args.monthly or None))
            print(f"上限更新: {args.username} daily={args.daily} "
                  f"monthly={args.monthly}")
        elif args.cmd == "setbalance":
            u = _require(conn, args.username)
            auth.set_balance(conn, u["id"], args.amount)
            print(f"残高設定: {args.username} = ¥{round(args.amount)}")
        elif args.cmd == "charge":
            u = _require(conn, args.username)
            new = auth.add_balance(conn, u["id"], args.delta)
            print(f"残高更新: {args.username} {args.delta:+} → ¥{round(new)}")
        elif args.cmd in ("activate", "deactivate"):
            u = _require(conn, args.username)
            auth.set_active(conn, u["id"], args.cmd == "activate")
            print(f"{args.username}: {'有効化' if args.cmd=='activate' else '無効化'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
