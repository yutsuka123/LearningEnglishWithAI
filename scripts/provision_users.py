"""公開用アカウントを一括作成し、資格情報を .env(git管理外)に保管する。

セキュリティ方針:
- パスワードは **平文をDBに保存しない**（pbkdf2 ハッシュのみ・auth.py）。
- 生成した平文の控えは **.env（gitignore済・イメージ非同梱・要 chmod 600）**へ
  コメントとして追記し、画面にも一度だけ表示（管理者が各ユーザーへ配布）。
- フロントへは一切渡らない（認証はサーバ側でハッシュ照合・HttpOnly Cookie）。

作成内容（既存ユーザーはスキップ＝再実行安全。パスワードは再設定しない）:
- 管理者: yutakatsuadmin（role=admin・上限なし・禁止用語許可）
- 自分(ユーザー): yutakatsu（user・日次¥500/月¥2000・禁止用語不可）
- ユーザー×5: 8文字ID（user・同上限・禁止用語不可）

上限は「無料枠」。到達後は管理者チャージ(¥500/回)を消費（balance_jpy）。
"""

from __future__ import annotations

import secrets
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_settings, paths  # noqa: E402
from app.database import db, init_db  # noqa: E402
from app.services import auth  # noqa: E402

_ALNUM = string.ascii_uppercase + string.ascii_lowercase + string.digits
_ID_ALPH = string.ascii_lowercase + string.digits


def gen_password(n: int = 12) -> str:
    """記号なし・大文字小文字数字を各1文字以上含む n 文字パスワード。"""
    while True:
        pw = "".join(secrets.choice(_ALNUM) for _ in range(n))
        if (any(c.isupper() for c in pw) and any(c.islower() for c in pw)
                and any(c.isdigit() for c in pw)):
            return pw


def gen_id(n: int = 8) -> str:
    return "".join(secrets.choice(_ID_ALPH) for _ in range(n))


def main() -> int:
    init_db()  # スキーマ/マイグレーション適用（allow_banned 等）
    s = load_settings()
    rate = s.usd_jpy_rate or 155.0
    daily_usd = round(500.0 / rate, 4)     # ¥500/日
    monthly_usd = round(2000.0 / rate, 4)  # ¥2000/月

    # (username, role, caps?, allow_banned)
    plan = [
        ("yutakatsuadmin", "admin", False, True),   # 管理者: 上限なし・禁止許可
        ("yutakatsu", "user", True, False),         # 自分(ユーザー)
    ]
    for _ in range(5):                              # 8文字IDユーザー×5
        plan.append((gen_id(8), "user", True, False))

    created: list[tuple[str, str, str]] = []  # (username, role, password)
    with db() as conn:
        for username, role, capped, allow_banned in plan:
            if auth.get_user_by_name(conn, username):
                print(f"スキップ(既存): {username}")
                continue
            pw = gen_password(12)
            auth.create_user(
                conn, username, pw, role=role, display_name=username,
                daily_cap_usd=(daily_usd if capped else None),
                monthly_cap_usd=(monthly_usd if capped else None),
                balance_jpy=(0.0 if role == "user" else None),
                allow_banned=allow_banned,
            )
            created.append((username, role, pw))

    if not created:
        print("新規作成なし（全て既存）。")
        return 0

    # 資格情報を .env に追記（git管理外・コメント形式でdotenvに無害）。
    block = ["", "# ===== 公開用アカウント資格情報（厳重管理・配布後は削除推奨）====="]
    block.append(f"# 生成: 上限 日¥500(${daily_usd})/月¥2000(${monthly_usd})")
    for username, role, pw in created:
        block.append(f"#   {role:5} {username} : {pw}")
    block.append("# ================================================================")
    with open(paths.root / ".env", "a", encoding="utf-8") as f:
        f.write("\n".join(block) + "\n")

    print("\n=== 作成したアカウント（この表示は一度きり・安全に保管）===")
    print(f"{'role':6} {'username':16} password")
    for username, role, pw in created:
        print(f"{role:6} {username:16} {pw}")
    print("\n資格情報は .env 末尾にも追記しました（git管理外）。")
    print("※ サーバ配置時は chmod 600 .env。DBには平文を保存していません。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
