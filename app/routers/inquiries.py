"""お問い合わせ・要望フォーム（2026-08-06・手動対応前提）。

ユーザーが送信した内容を inquiries テーブルに保存するだけのシンプルな
仕組み。自動振り分け・自動返信は行わず、管理者が管理画面で一覧を見て
手動対応する運用（`docs/TODO.md` に自動化の検討事項として記録）。
"""

from __future__ import annotations

from fastapi import APIRouter

from ..services import errors
from pydantic import BaseModel

from ..database import db
from ..services.auth import current_user_id

router = APIRouter(prefix="/api/inquiries", tags=["inquiries"])

KINDS = {
    "要望", "お問い合わせ", "ログインできない", "技術的トラブル",
    "課金トラブル", "機能に関する要望", "訳・音声の間違えに関する報告",
    "応援メッセージ", "感想", "その他",
    # 「パスワード再発行」はここに入れない(2026-10-04・第3回照査H-A): 依頼は`app/routers/password_reset.py`が
    # サーバーで本文を作って直接保存する。汎用の送信口で受け付けると、登録した人が先頭行(見出し+登録メール)まで
    # 偽造した依頼を何件でも作れてしまい、他人の依頼の上限を食う・相違の赤警告を迂回する、ことができる。
    # 未知の種別は「その他」に落ちる。
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
        raise errors.http_error("7002", "内容を入力してください。")
    email = payload.email.strip().lower()
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        raise errors.http_error(
            "2010", "メールアドレス（返信先）を正しく入力してください。")
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
        raise errors.http_error("2004", "管理者のみ閲覧できます。")


# 管理画面を開くたびに全件を読み込まないための上限(認証不要の「パスワード再発行」の依頼が積まれても重くならないように・2026-10-04)。
_LIST_LIMIT = 300


@router.get("")
def list_inquiries():
    """管理者専用: 新しい順で返す(最大_LIST_LIMIT件)。上限を超えるときは**未対応を優先**して選ぶ
    (荒らしの依頼で未対応の問い合わせが一覧から黙って消えないように・2026-10-04第3回照査M-C)。
    表示順は常に新しい順。`total`=全件数、`limit`=上限(画面が「全N件のうち…」と案内できるように)。"""
    with db() as conn:
        _require_admin(conn)
        rows = conn.execute(
            "SELECT i.id, i.kind, i.name, i.email, i.content, i.status, "
            " i.created_at, u.username, u.display_name "
            "FROM inquiries i LEFT JOIN users u ON u.id = i.user_id "
            "WHERE i.id IN (SELECT id FROM inquiries ORDER BY (status = '対応済み'), id DESC LIMIT ?) "
            "ORDER BY i.id DESC", (_LIST_LIMIT,)
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]
    return {"inquiries": [dict(r) for r in rows], "total": total, "limit": _LIST_LIMIT}


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
            raise errors.http_error("7001", "見つかりません。")
    return {"ok": True}
