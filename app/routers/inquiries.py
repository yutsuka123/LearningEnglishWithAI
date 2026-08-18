"""お問い合わせ・要望フォーム（2026-08-06・手動対応前提）。

ユーザーが送信した内容を inquiries テーブルに保存するだけのシンプルな
仕組み。自動振り分け・自動返信は行わず、管理者が管理画面で一覧を見て
手動対応する運用（`docs/TODO.md` に自動化の検討事項として記録）。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import db
from ..services.auth import current_user_id

router = APIRouter(prefix="/api/inquiries", tags=["inquiries"])

KINDS = {
    "要望", "お問い合わせ", "ログインできない", "技術的トラブル",
    "課金トラブル", "機能に関する要望", "訳・音声の間違えに関する報告",
    "応援メッセージ", "感想", "その他",
}


class InquiryIn(BaseModel):
    kind: str = "要望"
    name: str = ""
    email: str = ""
    content: str


@router.post("")
def create_inquiry(payload: InquiryIn):
    content = payload.content.strip()
    if not content:
        raise HTTPException(400, "内容を入力してください。")
    email = payload.email.strip().lower()
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            400, "メールアドレス（返信先）を正しく入力してください。")
    kind = payload.kind if payload.kind in KINDS else "その他"
    with db() as conn:
        conn.execute(
            "INSERT INTO inquiries (user_id, kind, name, email, content) "
            "VALUES (?, ?, ?, ?, ?)",
            (current_user_id(), kind, payload.name.strip(), email, content),
        )
    return {"ok": True}


def _require_admin(conn) -> None:
    from ..services import auth
    me = auth.get_user(conn, current_user_id())
    if not me or me.get("role") != "admin":
        raise HTTPException(403, "管理者のみ閲覧できます。")


@router.get("")
def list_inquiries():
    """管理者専用: 全件を新しい順で返す。"""
    with db() as conn:
        _require_admin(conn)
        rows = conn.execute(
            "SELECT i.id, i.kind, i.name, i.email, i.content, i.status, "
            " i.created_at, u.username, u.display_name "
            "FROM inquiries i LEFT JOIN users u ON u.id = i.user_id "
            "ORDER BY i.id DESC"
        ).fetchall()
    return {"inquiries": [dict(r) for r in rows]}


class StatusIn(BaseModel):
    status: str


@router.put("/{inquiry_id}/status")
def update_status(inquiry_id: int, payload: StatusIn):
    """管理者専用: 対応状況(未対応/対応済み)を更新する。"""
    with db() as conn:
        _require_admin(conn)
        cur = conn.execute(
            "UPDATE inquiries SET status = ? WHERE id = ?",
            (payload.status, inquiry_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "見つかりません。")
    return {"ok": True}
