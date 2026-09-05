"""ゲーム機能(クロスワード等)の限定公開アクセス制御(2026-09-03)。

role='admin'ではない特定アカウントにだけ、ゲーム機能を限定的に開放する
ための仕組み。app/services/paypay.py の is_test_allowed と同じ方式
（対象が少人数のうちはDB管理にはせず、コード直書きのシンプルな方式で
運用する）だが、対象機能・ロールアウト対象者がPayPayとは別物のため
独立したモジュール・許可リストにしてある。

2026-09-05ユーザー要望でゲーム機能を招待ユーザー(友人への alpha 配布
アカウント)にも開放。「招待ユーザー」の判定基準は
app/routers/system.py の `_user_filter_sql` が管理画面の集計フィルタで
既に使っている定義(email未設定=自己サインアップではない配布アカウント)
をそのまま流用する。
"""

from __future__ import annotations

_GAMES_TEST_ALLOWED_USERNAMES = {"ytsuka-biz1@nyangailab.com"}


def is_test_allowed(username: str) -> bool:
    """role='admin'でなくてもゲーム機能を使えるかどうか(個別許可リスト)。"""
    return (username or "").strip().lower() in _GAMES_TEST_ALLOWED_USERNAMES


def is_invited_user(username: str, email: str) -> bool:
    """招待ユーザー(自己サインアップではなく管理者が配布したアカウント)
    かどうか。email列が空文字のアカウントがこれにあたる
    (app/routers/system.py `_user_filter_sql` の「招待ユーザー」判定と
    同じ基準)。ただし疑似ユーザー__guest__もemail=''のため明示的に除外
    する(2026-09-05fable監査で発覚: 除外しないと未ログイン訪問者にも
    games_test_allowed=trueが返り、ゲームタブが見えてしまっていた
    ・app/services/auth.pyのensure_guest_user_id参照)。"""
    from .auth import GUEST_USERNAME
    if (username or "").strip().lower() == GUEST_USERNAME:
        return False
    return (email or "").strip() == ""


def can_access(username: str, email: str) -> bool:
    """admin以外でゲーム機能を使えるかどうかの統合判定
    (個別許可リスト または 招待ユーザー)。"""
    return is_test_allowed(username) or is_invited_user(username, email)
