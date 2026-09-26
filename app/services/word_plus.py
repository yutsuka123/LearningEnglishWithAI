"""単語詳細「詳細plus」(有料級コンテンツ・従量課金)のロジック(2026-09-26・オーナー確定仕様)。

## 仕様(オーナー確定 2026-09-26)
- 対象=`detail.native`(原語=語源の言語での表記・発音記号・(将来)音声)がある語。無料の詳細では「語源の言語+原語表記」
  までを出し、**原語の発音記号(IPA)と音声は「詳細plus」の中身**。
- 課金: 単語ごとに**0.25pt**(1pt=1円・残高から控除)・**その単語を初めて開いたときだけ**(2回目以降の再表示は無料)。
- **無課金ユーザーは10語分まで無料**(お試し・通算)。使い切ると、チャージ(残高>0.25pt)が要る。課金済みユーザーは初回から課金。
- 未登録ゲストは使えない(ログイン誘導)。管理者・テストアカウントは課金せず使える(動作確認用)。
- **機能フラグ`WORD_PLUS_ENABLED`(既定OFF)**: OFFの間は一般ユーザーには存在しない扱い(管理者だけプレビューできる)。
  原語音声が決まるまでは公開しない想定(オーナーが音声を確認して判断)。

## 不整合を防ぐ設計(お金が動くため)
- 課金と「開いた記録」(`word_plus_unlocks`・UNIQUE(user_id, word_id))は**同じトランザクション**(`BEGIN IMMEDIATE`で書き込みを直列化)。
  同じ語の同時リクエストや連打でも、課金されるのは1回だけ。残高は**ロック取得後に読み直して**判定する(負残高を作らない)。
- 残高の増減は必ず`auth.add_balance`(理由`word_plus`・監査台帳`balance_ledger`に1行)を通す。
- 有料項目(`native.ipa`・将来の音声)は、無料の詳細応答(`POST /api/words/{id}/detail`)から**取り除く**(`strip_plus_fields`)。
  JSONにそのまま入っていると、課金せずに読めてしまうため。
"""

from __future__ import annotations

import copy
import os
import sqlite3
from typing import Optional

PLUS_COST_JPY = 0.25
PLUS_FREE_TRIAL = 10
# native内の有料項目(無料の詳細応答からは外す)。textとromaji(=無料の「原語表記」)は残す。
PLUS_ONLY_NATIVE_KEYS = ("ipa", "audio")


class PlusError(Exception):
    """課金・権限の拒否。codeは`errors.ERROR_CODES`のコード。"""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def flag_enabled() -> bool:
    return os.getenv("WORD_PLUS_ENABLED", "0").strip().lower() in ("1", "true", "yes")


def is_staff(user: Optional[dict]) -> bool:
    """管理者・テストアカウント(課金せず使える)。"""
    return bool(user and (user.get("role") == "admin" or user.get("is_test")))


def available_for(user: Optional[dict]) -> bool:
    """この利用者に「詳細plus」を出してよいか(フラグON、または管理者/テスター=プレビュー)。"""
    return flag_enabled() or is_staff(user)


def strip_plus_fields(detail: dict) -> dict:
    """無料の詳細応答用に、有料項目(native.ipa等)を外したコピーを返す(元は変更しない)。"""
    if not isinstance(detail, dict):
        return detail
    native = detail.get("native")
    if not isinstance(native, dict) or not any(k in native for k in PLUS_ONLY_NATIVE_KEYS):
        return detail
    out = copy.copy(detail)
    out["native"] = {k: v for k, v in native.items() if k not in PLUS_ONLY_NATIVE_KEYS}
    return out


def plus_content(detail: dict) -> Optional[dict]:
    """「詳細plus」の中身(=原語の発音記号・音声)。**有料の中身(native.ipaまたはaudio)が実在する語だけ**が対象で、
    それ以外(原語表記のテキストだけの語)はNone=欄を出さず課金もしない(空の中身に課金しない・敵対的レビュー指摘)。"""
    if not isinstance(detail, dict) or not detail.get("origin_lang"):
        return None
    native = detail.get("native")
    if not isinstance(native, dict) or not native:
        return None
    audio = native.get("audio") if isinstance(native.get("audio"), dict) else None
    if not (native.get("ipa") or audio):
        return None
    return {
        "origin_lang": detail.get("origin_lang"),
        "origin_lang_name": detail.get("origin_lang_name") or "",
        "native": {
            "text": native.get("text") or "",
            "ipa": native.get("ipa") or "",
            "romaji": native.get("romaji") or "",
        },
        # 原語の音声(男声/女声)はまだ無い(オーナーの確認後に生成)。あれば{"male":..,"female":..}のように入れる。
        "audio": audio,
        "has_audio": bool(audio),
    }


def _never_paid(conn: sqlite3.Connection, uid: int) -> bool:
    """一度も課金を受けたことが無い一般ユーザーか(=無料お試しの対象)。`auth.has_ever_paid`(専用の判定)。"""
    from . import auth
    return not auth.has_ever_paid(conn, uid)


def _trial_used(conn: sqlite3.Connection, uid: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM word_plus_unlocks WHERE user_id = ? AND kind = 'trial'", (uid,)
    ).fetchone()[0]


def _balance(conn: sqlite3.Connection, uid: int) -> float:
    row = conn.execute("SELECT balance_jpy FROM users WHERE id = ?", (uid,)).fetchone()
    return float(row["balance_jpy"]) if row and row["balance_jpy"] is not None else 0.0


def status(conn: sqlite3.Connection, uid: int, word_id: int, user: Optional[dict]) -> dict:
    """課金せずに、いまの状態(開いた済みか・今回の扱い・無料お試しの残り・残高)を返す。UIの表示用。"""
    if is_staff(user):
        return {"unlocked": False, "mode": "staff", "cost_jpy": 0.0,
                "free_trial_left": None, "balance_jpy": _balance(conn, uid)}
    already = conn.execute(
        "SELECT 1 FROM word_plus_unlocks WHERE user_id = ? AND word_id = ?", (uid, word_id)
    ).fetchone() is not None
    left = max(0, PLUS_FREE_TRIAL - _trial_used(conn, uid))
    if already:
        mode, cost = "already", 0.0
    elif _never_paid(conn, uid) and left > 0:
        mode, cost = "trial", 0.0
    else:
        mode, cost = "paid", PLUS_COST_JPY
    return {"unlocked": already, "mode": mode, "cost_jpy": cost,
            "free_trial_left": left if _never_paid(conn, uid) else 0,
            "balance_jpy": _balance(conn, uid)}


def unlock(conn: sqlite3.Connection, uid: int, word_id: int, user: Optional[dict],
           expected_cost: Optional[float] = None) -> dict:
    """「詳細plus」を開く。初回だけ課金(またはお試し枠を消費)し、開いた記録を残す。呼び出し側の`db()`が
    commit/rollbackする。拒否は`PlusError`(コード)。課金と記録は同じトランザクション(BEGIN IMMEDIATE)。"""
    from . import auth

    if conn.in_transaction:
        # 呼び出し前に同じ接続で書き込みがあると「BEGIN IMMEDIATE」が失敗して全POSTが500になる。壊れ方を明示する。
        raise RuntimeError("word_plus.unlock: この接続で先に書き込みを行わないこと(トランザクションが開いています)")
    if is_staff(user):
        return {"mode": "staff", "charged_jpy": 0.0, "first_time": False}
    # 開いた済みなら読み取りだけで即返す(他の長い書き込みトランザクションを待たない=「無料の再表示」が固まらない)。
    if conn.execute("SELECT 1 FROM word_plus_unlocks WHERE user_id = ? AND word_id = ?", (uid, word_id)).fetchone():
        return {"mode": "already", "charged_jpy": 0.0, "first_time": False}
    # 書き込みが要るときだけ書き込みロックを取り、判定→課金→記録を直列化する(同時リクエストで二重課金・負残高にしない)。
    conn.execute("BEGIN IMMEDIATE")
    exists = conn.execute(
        "SELECT 1 FROM word_plus_unlocks WHERE user_id = ? AND word_id = ?", (uid, word_id)
    ).fetchone()
    if exists:   # ロック待ちの間に別リクエストが開いた(二重チェック)
        return {"mode": "already", "charged_jpy": 0.0, "first_time": False}
    never_paid = _never_paid(conn, uid)
    trial_ok = never_paid and _trial_used(conn, uid) < PLUS_FREE_TRIAL
    actual_cost = 0.0 if trial_ok else PLUS_COST_JPY
    if expected_cost is not None and abs(float(expected_cost) - actual_cost) > 1e-9:
        # 画面に表示した費用と実際の費用が食い違う(別タブでチャージした等)ときは、課金せず確認し直してもらう。
        raise PlusError("3025")
    if trial_ok:
        conn.execute(
            "INSERT INTO word_plus_unlocks (user_id, word_id, kind, charged_jpy) VALUES (?, ?, 'trial', 0)",
            (uid, word_id))
        return {"mode": "trial", "charged_jpy": 0.0, "first_time": True}
    if _balance(conn, uid) < PLUS_COST_JPY:
        # お試しを使い切った無課金ユーザー(3023)と、課金済みだが残高が足りないユーザー(3024)で案内を分ける。
        raise PlusError("3023" if never_paid else "3024")
    conn.execute(
        "INSERT INTO word_plus_unlocks (user_id, word_id, kind, charged_jpy) VALUES (?, ?, 'paid', ?)",
        (uid, word_id, PLUS_COST_JPY))
    auth.add_balance(conn, uid, -PLUS_COST_JPY, reason="word_plus", note=f"word:{word_id}")
    return {"mode": "paid", "charged_jpy": PLUS_COST_JPY, "first_time": True}
