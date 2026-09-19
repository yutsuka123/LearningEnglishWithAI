"""管理者専用の気づきメモ「メモ（管）」（2026-09-19ユーザー要望）。

単語/フレーズの詳細画面と設定画面にある管理者専用ボタンから、外出先などで
気づいたこと（「音声が間違っていた・訳を直したい」等）をその場で記録する
ログ。あとで集計・検索できるよう、1件ごとにタグを付ける（人間は画面の
タグ選択や本文中の`#タグ`、AIは`admin_memo_tags`テーブルへのSQLかこの
ファイルのAPIで検索・集計できる）。

- 認可: 全エンドポイント管理者(role=admin)専用（サーバー側で強制。
  フロントのボタン非表示は表示上の案内にすぎない）。
- 記録は追記のみ。本文の編集・削除は用意しない(ログだから)。状態だけ
  後から更新できる。
- 状態(2026-09-20〜): 起票(記録した直後) → 対応済み(直した) / 対応不要 /
  ペンディング(保留) → クローズ(確認まで終わり)。どの状態からどの状態へも
  移せる(戻す・やり直しも許す)。旧「未対応」は「起票」の別名として受け付ける。
- 保存先は core.db（users等と同じ、日々書き込まれるライブデータ側）。
"""

from __future__ import annotations

import re
import unicodedata

from fastapi import APIRouter
from pydantic import BaseModel

from ..database import db
from ..services import auth, errors
from ..services.auth import current_user_id

router = APIRouter(prefix="/api/admin-memos", tags=["admin-memos"])

SOURCES = {"word_detail", "phrase_detail", "settings"}
REF_KINDS = {"word", "phrase"}
STATUSES = ("起票", "対応済み", "対応不要", "ペンディング", "クローズ")
DEFAULT_STATUS = "起票"
# resolved_at(=決着した日時)を付ける状態。ペンディング/起票に戻したら消す。
_DONE_STATUSES = ("対応済み", "対応不要", "クローズ")
# 旧名の別名(AI/スクリプトが旧名で呼んでも動くように)。
_LEGACY_STATUS = {"未対応": "起票"}


def normalize_status(s: str) -> str:
    """旧名を新名に読み替える。未知の値はそのまま返す(呼び出し側で弾く)。"""
    s = (s or "").strip()
    return _LEGACY_STATUS.get(s, s)

# 画面ごとに必ず付ける自動タグ(「設定画面のメモだけ」等で絞り込めるように)。
_AUTO_TAG_BY_SOURCE = {
    "word_detail": "単語", "phrase_detail": "フレーズ", "settings": "設定",
}

BODY_MAX = 2000
TAG_MAX_LEN = 30
TAGS_MAX = 12
LIST_LIMIT_MAX = 500


def _require_admin(conn) -> None:
    me = auth.get_user(conn, current_user_id())
    if not me or me.get("role") != "admin":
        raise errors.http_error("2004", "管理者のみ利用できます。")


def normalize_tag(raw: str) -> str:
    """タグを表記ゆれの少ない形にそろえる(全角/半角・先頭の#・空白・英大小)。
    空白は`_`にする(タグ自体は空白を含まない1語として扱うため)。"""
    t = unicodedata.normalize("NFKC", raw or "").strip().lstrip("#").strip()
    t = re.sub(r"\s+", "_", t).lower()
    return t[:TAG_MAX_LEN]


def build_tags(body: str, given: list[str], source: str) -> list[str]:
    """画面で選んだタグ + 本文中の`#タグ` + 画面ごとの自動タグ。
    重複を除き、上限(TAGS_MAX)までを順序を保って返す。"""
    hashtags = re.findall(
        r"#([^\s#]+)", unicodedata.normalize("NFKC", body))
    out: list[str] = []
    for raw in [*given, *hashtags, _AUTO_TAG_BY_SOURCE.get(source, "")]:
        t = normalize_tag(raw)
        if t and t not in out:
            out.append(t)
    return out[:TAGS_MAX]


class MemoIn(BaseModel):
    body: str
    tags: list[str] = []
    source: str = ""
    ref_kind: str = ""
    ref_id: int | None = None
    ref_english: str = ""
    ref_japanese: str = ""


@router.post("")
def create_memo(payload: MemoIn):
    body = payload.body.strip()
    if not body:
        raise errors.http_error("7002", "メモの内容を入力してください。")
    if len(body) > BODY_MAX:
        raise errors.http_error(
            "7002", f"メモは{BODY_MAX}文字以内で入力してください。")
    source = payload.source if payload.source in SOURCES else ""
    ref_kind = payload.ref_kind if payload.ref_kind in REF_KINDS else ""
    ref_id = payload.ref_id if ref_kind else None
    tags = build_tags(body, payload.tags, source)
    with db() as conn:
        _require_admin(conn)
        cur = conn.execute(
            "INSERT INTO admin_memos (user_id, source, ref_kind, ref_id, "
            " ref_english, ref_japanese, body, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (current_user_id(), source, ref_kind, ref_id,
             payload.ref_english.strip()[:200],
             payload.ref_japanese.strip()[:200], body, DEFAULT_STATUS),
        )
        memo_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO admin_memo_tags (memo_id, tag) VALUES (?, ?)",
            [(memo_id, t) for t in tags],
        )
    return {"ok": True, "id": memo_id, "tags": tags}


def _like_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("")
def list_memos(
    q: str = "", tag: str = "", status: str = "", source: str = "",
    ref_kind: str = "", ref_id: int | None = None,
    limit: int = 100, offset: int = 0,
):
    """メモ一覧(新しい順)。絞り込みはすべてAND。
    - q: 本文・対象の英語/日本語に含まれるキーワード
    - tag: タグ(カンマ区切りで複数指定するとすべてを含むものだけ)
    - status: 起票 / 対応済み / 対応不要 / ペンディング / クローズ
      (旧名「未対応」は起票として扱う)
    返り値の`status_counts`は絞り込みに関係なく全メモの状態別件数。
    """
    status = normalize_status(status)
    limit = max(1, min(limit, LIST_LIMIT_MAX))
    offset = max(0, offset)
    conds: list[str] = []
    args: list = []
    if q.strip():
        like = f"%{_like_escape(q.strip())}%"
        conds.append(
            "(m.body LIKE ? ESCAPE '\\' OR m.ref_english LIKE ? ESCAPE '\\'"
            " OR m.ref_japanese LIKE ? ESCAPE '\\')")
        args += [like, like, like]
    for t in (normalize_tag(x) for x in tag.split(",")):
        if not t:
            continue
        conds.append(
            "EXISTS (SELECT 1 FROM admin_memo_tags t "
            "WHERE t.memo_id = m.id AND t.tag = ?)")
        args.append(t)
    if status in STATUSES:
        conds.append("m.status = ?")
        args.append(status)
    if source in SOURCES:
        conds.append("m.source = ?")
        args.append(source)
    if ref_kind in REF_KINDS:
        conds.append("m.ref_kind = ?")
        args.append(ref_kind)
        if ref_id is not None:
            conds.append("m.ref_id = ?")
            args.append(ref_id)
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    with db() as conn:
        _require_admin(conn)
        total = conn.execute(
            f"SELECT COUNT(*) FROM admin_memos m {where}", args
        ).fetchone()[0]
        rows = conn.execute(
            "SELECT m.id, m.source, m.ref_kind, m.ref_id, m.ref_english, "
            " m.ref_japanese, m.body, m.status, m.created_at, "
            " m.resolved_at, u.username, u.display_name "
            f"FROM admin_memos m LEFT JOIN users u ON u.id = m.user_id "
            f"{where} ORDER BY m.id DESC LIMIT ? OFFSET ?",
            [*args, limit, offset],
        ).fetchall()
        memos = [dict(r) for r in rows]
        by_status = {r["status"]: r["n"] for r in conn.execute(
            "SELECT status, COUNT(*) AS n FROM admin_memos GROUP BY status")}
        status_counts = {s: by_status.get(s, 0) for s in STATUSES}
        tags_by_memo: dict[int, list[str]] = {m["id"]: [] for m in memos}
        if memos:
            marks = ",".join("?" * len(memos))
            for r in conn.execute(
                "SELECT memo_id, tag FROM admin_memo_tags "
                f"WHERE memo_id IN ({marks}) ORDER BY rowid",
                [m["id"] for m in memos],
            ):
                tags_by_memo[r["memo_id"]].append(r["tag"])
    for m in memos:
        m["tags"] = tags_by_memo[m["id"]]
    return {"total": total, "memos": memos, "status_counts": status_counts}


@router.get("/tags")
def tag_counts(status: str = ""):
    """タグ別の件数(多い順)。絞り込みUIのチップ表示・集計用。"""
    status = normalize_status(status)
    conds = ""
    args: list = []
    if status in STATUSES:
        conds = "WHERE m.status = ?"
        args.append(status)
    with db() as conn:
        _require_admin(conn)
        rows = conn.execute(
            "SELECT t.tag, COUNT(*) AS count FROM admin_memo_tags t "
            f"JOIN admin_memos m ON m.id = t.memo_id {conds} "
            "GROUP BY t.tag ORDER BY count DESC, t.tag",
            args,
        ).fetchall()
    return {"tags": [dict(r) for r in rows]}


class StatusIn(BaseModel):
    status: str


@router.put("/{memo_id}/status")
def update_status(memo_id: int, payload: StatusIn):
    """状態を更新する(5種類のどれへでも移せる)。本文・タグは変えられない。
    resolved_atは対応済み/対応不要/クローズに**初めて入った時**に記録し、
    その間の移動(対応済み→クローズ等)では変えず、起票/ペンディングに
    戻したら消す。"""
    status = normalize_status(payload.status)
    if status not in STATUSES:
        raise errors.http_error("7002", "状態が正しくありません。")
    with db() as conn:
        _require_admin(conn)
        cur = conn.execute(
            "UPDATE admin_memos SET status = ?, "
            " resolved_at = CASE WHEN ? IN (?, ?, ?) "
            "   THEN COALESCE(resolved_at, datetime('now')) ELSE NULL END "
            "WHERE id = ?",
            (status, status, *_DONE_STATUSES, memo_id),
        )
        if cur.rowcount == 0:
            raise errors.http_error("7001", "メモが見つかりません。")
    return {"ok": True, "id": memo_id, "status": status}
