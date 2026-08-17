"""利用状況イベントログ（画面表示・音声再生・ボタン押下）。

管理画面の「利用状況分析」で使う usage_events への書き込みだけを担う
薄いサービス。記録の失敗が本来の処理(音声再生・画面遷移)を妨げないよう、
常に best-effort（例外は握りつぶしてログのみ）で書き込む。
"""

from __future__ import annotations

import logging

from ..database import db
from . import auth

log = logging.getLogger(__name__)

VALID_KINDS = {"page", "play", "click"}


def log_event(kind: str, category: str = "", label: str = "") -> None:
    """usage_events に1件記録する。kind不正・DB失敗はどちらも無視する。"""
    if kind not in VALID_KINDS:
        return
    uid = auth.current_user_id()
    ip = auth.current_ip()
    try:
        with db() as conn:
            conn.execute(
                "INSERT INTO usage_events "
                "(user_id, ip, kind, category, label) VALUES (?, ?, ?, ?, ?)",
                (uid, ip, kind, (category or "")[:100], (label or "")[:150]),
            )
    except Exception:
        log.warning("usage_events記録に失敗", exc_info=True)
