"""ゲーム機能(クロスワード等)の限定公開アクセス制御(2026-09-03)。

role='admin'ではない特定アカウントにだけ、ゲーム機能を限定的に開放する
ための仕組み。app/services/paypay.py の is_test_allowed と同じ方式
（対象が少人数のうちはDB管理にはせず、コード直書きのシンプルな方式で
運用する）だが、対象機能・ロールアウト対象者がPayPayとは別物のため
独立したモジュール・許可リストにしてある。
"""

from __future__ import annotations

_GAMES_TEST_ALLOWED_USERNAMES = {"ytsuka-biz1@nyangailab.com"}


def is_test_allowed(username: str) -> bool:
    """role='admin'でなくてもゲーム機能を使えるかどうか。"""
    return (username or "").strip().lower() in _GAMES_TEST_ALLOWED_USERNAMES
