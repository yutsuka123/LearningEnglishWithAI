"""利用状況イベントログ（画面表示・音声再生・ボタン押下）。

管理画面の「利用状況分析」で使う usage_events への書き込みだけを担う
薄いサービス。記録の失敗が本来の処理(音声再生・画面遷移)を妨げないよう、
常に best-effort（例外は握りつぶしてログのみ）で書き込む。
"""

from __future__ import annotations

import logging
import time as _time

from ..database import db
from . import auth

log = logging.getLogger(__name__)

VALID_KINDS = {
    "page", "play", "click",
    # 単語/フレーズの分野・シーン別の利用状況分析用(2026-08-19)。
    # 音声再生のタイミングでitem_id→分野/シーンを引いて記録する
    # (app/routers/learn.pyのtts_item)。
    "word_domain", "phrase_scene",
}


def log_event(kind: str, category: str = "", label: str = "") -> None:
    """usage_events に1件記録する。kind不正・DB失敗はどちらも無視する。"""
    if kind not in VALID_KINDS:
        return
    uid = auth.current_user_id()
    ip = auth.current_ip()
    gsid = auth.current_guest_sid()
    try:
        with db() as conn:
            conn.execute(
                "INSERT INTO usage_events "
                "(user_id, ip, kind, category, label, guest_sid) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (uid, ip, kind, (category or "")[:100], (label or "")[:150],
                 gsid),
            )
    except Exception:
        log.warning("usage_events記録に失敗", exc_info=True)


# フロントエンドの未捕捉JS例外の記録(2026-08-30)。1画面のバグが大量
# スパムにならないよう、ip_rate_limited(auth.py)とは別の専用カウンタで
# IPごと1分間20件までに制限する(超過分はDBを守るため静かに破棄)。
_CLIENT_ERROR_HITS: dict[str, list[float]] = {}
_CLIENT_ERROR_CAP_PER_MIN = 20


def record_client_error(
    kind: str, message: str, stack: str = "", url: str = "",
    line: int = 0, col: int = 0,
) -> None:
    """client_errors に1件記録する。レート制限超過・DB失敗はどちらも無視。"""
    ip = auth.current_ip() or "?"
    now = _time.monotonic()
    hits = [t for t in _CLIENT_ERROR_HITS.get(ip, []) if now - t < 60.0]
    if len(hits) >= _CLIENT_ERROR_CAP_PER_MIN:
        return
    hits.append(now)
    _CLIENT_ERROR_HITS[ip] = hits
    uid = auth.current_user_id()
    gsid = auth.current_guest_sid()
    try:
        with db() as conn:
            conn.execute(
                "INSERT INTO client_errors "
                "(user_id, ip, guest_sid, kind, message, stack, url, "
                "line, col) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (uid, ip, gsid, kind, (message or "")[:2000],
                 (stack or "")[:2000], (url or "")[:500], line, col),
            )
    except Exception:
        log.warning("client_errors記録に失敗", exc_info=True)
