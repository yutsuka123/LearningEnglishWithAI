"""Mini-phrase (ミニフレーズ) management + quiz.

Phrases are practised exactly like words: both directions (英→日 / 日→英),
per-direction accuracy, and a forgetting-curve schedule.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..database import db
from ..services.taxonomy import PHRASE_CATEGORIES, group_by_category
from ..services.spaced_repetition import (
    DEFAULT_MASTERY_CONFIG,
    MASTERED_THRESHOLD,
    MasteryConfig,
    clamp,
    mark_vague as _mark_vague,
    record_attempt,
    selection_weight,
    select_for_review,
    set_known,
    set_perfect,
)
from .vocabulary import (
    LEVEL_ORDER, OUT_OF_RANGE, _current_mastery_cfg, _level_range,
)

router = APIRouter(prefix="/api/phrases", tags=["phrases"])


class PhraseCreate(BaseModel):
    english: str = Field(min_length=1)
    japanese: str = Field(min_length=1)
    scene: str = ""


class PhraseAttempt(BaseModel):
    phrase_id: int
    direction: str  # 'ja2en' | 'en2ja'
    correct: bool
    result: str | None = None  # 'correct' | 'vague' | 'wrong'


class KnownIn(BaseModel):
    known: bool = True


def _phrase_filter(
    scene: str | None, level_min: str | None, level_max: str | None,
    out_of_range: bool, include_banned: bool, mastered: str | None,
    category: str | None = None,
    mastered_threshold: int = MASTERED_THRESHOLD,
) -> tuple[list[str], list]:
    """フレーズ一覧/フラッシュフレーズ共通のフィルタWHERE句を組み立てる
    （単語版`_word_filter`のフレーズ版）。列は素の名前(scene/level/mastery)
    で参照。返り値は(条件リスト, パラメータ)。"""
    where: list[str] = []
    params: list = []
    if scene:
        scenes = [s for s in scene.split(",") if s]
        ph = ",".join("?" * len(scenes))
        where.append(f"COALESCE(scene, '') IN ({ph})")
        params += scenes
    elif category:
        cat_scenes = PHRASE_CATEGORIES.get(category, [])
        if cat_scenes:
            ph = ",".join("?" * len(cat_scenes))
            where.append(f"COALESCE(scene, '') IN ({ph})")
            params += cat_scenes
    if level_min or level_max:
        allowed = _level_range(level_min, level_max)
        ph = ",".join("?" * len(allowed))
        cond = f"COALESCE(level, '') IN ({ph})"
        p = list(allowed)
        if out_of_range:
            cond = f"({cond} OR COALESCE(level, '') = ?)"
            p.append(OUT_OF_RANGE)
        where.append(cond)
        params += p
    if not include_banned:
        # 「範囲外」レベルのチェックはレベル絞り込みにのみ作用させる。
        # ここで緩めると、禁止用語チェックを入れていなくてもレベルが
        # 「範囲外」の禁止用語が表示されてしまうため(2026-08-17修正)。
        where.append("COALESCE(scene, '') NOT LIKE '禁止%'")
    if mastered == "only":
        where.append(f"mastery >= {mastered_threshold}")
    elif mastered == "hide":
        where.append(f"mastery < {mastered_threshold}")
    return where, params


def _phrase_dict(
    row, free_ids: set[int] | None = None,
    cfg: MasteryConfig = DEFAULT_MASTERY_CONFIG,
) -> dict:
    d = dict(row)
    # detail(JSON)は一覧では送らず、有無フラグだけ返す（応答を軽く保つ、
    # 単語(words)と同じ扱い）。
    d["has_detail"] = bool((d.pop("detail", "") or "").strip())
    d["selection_priority"] = selection_weight(d["mastery"], cfg.mastered_threshold)
    d["mastered"] = d["mastery"] >= cfg.mastered_threshold
    d["perfect"] = bool(d.get("perfect", 0))
    d["accuracy"] = (
        round(d["times_correct"] / d["times_asked"] * 100)
        if d["times_asked"]
        else None
    )
    # 🔒無料範囲外の表示用（単語版`_word_dict`と同じ扱い・2026-08-12）。
    if free_ids is not None:
        d["is_free_range"] = d["id"] in free_ids
    return d


@router.get("")
def list_phrases(
    scene: str | None = None,
    category: str | None = None,   # 大分類（scene未指定時のみ有効）
    sort: str = "mastery",
    desc: bool = False,            # 降順にするか（昇順/降順トグル）
    level_min: str | None = None,
    level_max: str | None = None,
    out_of_range: bool = False,
    include_banned: bool = False,
    mastered: str | None = None,   # 'only' | 'hide' | None(=全部)
    deck_id: int | None = None,    # 自分のフレーズ帳で絞り込み(2026-08-09)
    free_range_only: bool = False,  # 🔊無料で再生できる範囲のみ(2026-08-11)
):
    from ..services.auth import current_user_allow_banned
    include_banned = include_banned and current_user_allow_banned()
    col = {
        "mastery": "mastery",
        "english": "english COLLATE NOCASE",
        "scene": "scene",
        "recent": "last_studied",
        "added": "id",
        "accuracy": (
            "CASE WHEN times_asked > 0 "
            "THEN times_correct * 1.0 / times_asked ELSE -1 END"
        ),
    }.get(sort, "mastery")
    direction = "DESC" if desc else "ASC"
    # タイブレークは英字アルファベット順ではなく登録順(id)。理由:
    # 「直訳で失礼に響く表現→丁寧な言い方」のような意図的なペア構成の
    # シーンで、mastery=0が並ぶ初回表示時にアルファベット順だとペアが
    # ばらばらになってしまうため(2026-08-04ユーザー指摘)。
    order = f"{col} {direction}, id ASC"
    conds, params = [], []
    if scene:
        # カンマ区切りで複数シーン指定可（チェックボックスでの複数選択に
        # 対応・単一指定時も同じIN句で動作）。
        scenes = [s for s in scene.split(",") if s]
        ph = ",".join("?" * len(scenes))
        conds.append(f"scene IN ({ph})")
        params += scenes
    elif category:
        cat_scenes = PHRASE_CATEGORIES.get(category, [])
        if cat_scenes:
            ph = ",".join("?" * len(cat_scenes))
            conds.append(f"COALESCE(scene, '') IN ({ph})")
            params += cat_scenes
    if level_min or level_max:
        allowed = _level_range(level_min, level_max)
        ph = ",".join("?" * len(allowed))
        cond = f"COALESCE(level, '') IN ({ph})"
        p = list(allowed)
        if out_of_range:
            cond = f"({cond} OR COALESCE(level, '') = ?)"
            p.append(OUT_OF_RANGE)
        conds.append(cond)
        params += p
    if not include_banned:
        # 「範囲外」レベルのチェックはレベル絞り込みにのみ作用させる。
        # ここで緩めると、禁止用語チェックを入れていなくてもレベルが
        # 「範囲外」の禁止用語が表示されてしまうため(2026-08-17修正)。
        conds.append("COALESCE(scene, '') NOT LIKE '禁止%'")
    from ..services import access_tiers
    from ..services.auth import current_user_id, is_guest_user_id
    from ..services.progress import user_items_subquery
    src = user_items_subquery("phrases")  # 先頭 ? = user_id
    with db() as conn:
        uid = current_user_id()
        cfg = _current_mastery_cfg(conn)
        if mastered == "only":
            conds.append(f"mastery >= {cfg.mastered_threshold}")
        elif mastered == "hide":
            conds.append(f"mastery < {cfg.mastered_threshold}")
        is_guest = is_guest_user_id(conn, uid)
        if deck_id is not None:
            owned = conn.execute(
                "SELECT 1 FROM phrase_decks WHERE id = ? AND user_id = ?",
                (deck_id, uid),
            ).fetchone()
            if not owned:
                raise HTTPException(404, "フレーズ帳が見つかりません")
            conds = conds + [
                "phrases.id IN (SELECT phrase_id FROM deck_phrases "
                "WHERE deck_id = ?)"
            ]
            params = params + [deck_id]
        if free_range_only:
            fr_clause, fr_params = access_tiers.free_range_id_filter(
                "phrase", guest=is_guest,
            )
            conds = conds + [fr_clause]
            params = params + fr_params
        where = (" WHERE " + " AND ".join(conds)) if conds else ""
        rows = conn.execute(
            f"SELECT * FROM {src} AS phrases{where} ORDER BY {order}",
            [uid, *params],
        ).fetchall()
        free_ids = access_tiers.free_range_ids(
            conn, "phrase", guest=is_guest)
        return [_phrase_dict(r, free_ids, cfg) for r in rows]


@router.get("/facets")
def facets():
    """フィルタUI用: レベル範囲の選択肢（細スケール順・範囲外を除く）。"""
    with db() as conn:
        present = {
            r["level"] for r in conn.execute(
                "SELECT DISTINCT level FROM phrases WHERE COALESCE(level,'')<>''"
            ).fetchall()
        }
    return {"range_levels": [lv for lv in LEVEL_ORDER if lv in present]}


@router.get("/scenes")
def list_scenes(include_banned: bool = False, include_hidden: bool = False):
    """シーン(scene)の一覧＋大分類ごとのグルーピング。
    `scenes`は既存互換のフラット配列、`scene_groups`が新設の階層情報。
    include_hidden=false（既定）のとき、設定画面でユーザーが非表示に
    したシーン(user_settings.hidden_scenes)を候補から除外する。"""
    from ..services.auth import current_user_allow_banned, \
        current_user_id, get_user_settings
    include_banned = include_banned and current_user_allow_banned()
    ban = "" if include_banned else "AND scene NOT LIKE '禁止%' "
    with db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT scene FROM phrases WHERE scene <> '' "
            f"{ban}ORDER BY scene"
        ).fetchall()
        scenes = [r["scene"] for r in rows]
        if not include_hidden:
            hidden = set(
                get_user_settings(conn, current_user_id())
                .get("hidden_scenes", []))
            if hidden:
                scenes = [s for s in scenes if s not in hidden]
    return {
        "scenes": scenes,
        "scene_groups": group_by_category(scenes, PHRASE_CATEGORIES),
    }


@router.post("", status_code=201)
def create_phrase(payload: PhraseCreate):
    """フレーズカタログの追加は管理者専用(2026-08-10〜)。単語の
    create_word/update_wordと同じ理由(カタログは全ユーザー共有・フロントの
    追加フォームもadmin-only表示)でサーバー側を強制する。"""
    from ..services import auth
    with db() as conn:
        me = auth.get_user(conn, auth.current_user_id())
        if not me or me.get("role") != "admin":
            raise HTTPException(403, "フレーズの追加は管理者のみ行えます。")
        cur = conn.execute(
            "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
            (payload.english, payload.japanese, payload.scene),
        )
        row = conn.execute(
            "SELECT * FROM phrases WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return _phrase_dict(row)


@router.post("/{phrase_id}/known")
def mark_known(phrase_id: int, payload: KnownIn):
    """「覚えた」ボタン(per-user): mastery を加点(既定+200・満点でクランプ)、
    復習間隔も最長へ。known=false で解除（mastery/間隔とも復活させる）。
    加点量・満点は詳細設定でユーザーが調整可能(2026-08-18)。"""
    from ..services.auth import current_user_id
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM phrases WHERE id = ?", (phrase_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, "フレーズが見つかりません")
        r = set_known(conn, phrase_id, payload.known, table="phrases",
                      user_id=current_user_id(), cfg=_current_mastery_cfg(conn))
    return {"ok": True, "known": payload.known, **r}


class PerfectIn(BaseModel):
    perfect: bool = True


@router.post("/{phrase_id}/perfect")
def mark_perfect(phrase_id: int, payload: PerfectIn):
    """「完全に覚えた」ボタン(per-user): 満点に固定し、以後は忘却曲線で
    減らなくなる。perfect=falseで解除すると通常の「覚えた」相当に戻り、
    忘却曲線の対象にも戻る(2026-08-18)。"""
    from ..services.auth import current_user_id
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM phrases WHERE id = ?", (phrase_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, "フレーズが見つかりません")
        r = set_perfect(conn, phrase_id, payload.perfect, table="phrases",
                        user_id=current_user_id(), cfg=_current_mastery_cfg(conn))
    return {"ok": True, **r}


@router.post("/{phrase_id}/vague")
def mark_vague(phrase_id: int):
    """「うろ覚え」ボタン(per-user): mastery を加点(既定+30・満点でクランプ)、
    復習間隔も約2日後に更新する。加点量は詳細設定でユーザーが調整可能
    (2026-08-18)。"""
    from ..services.auth import current_user_id
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM phrases WHERE id = ?", (phrase_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, "フレーズが見つかりません")
        r = _mark_vague(conn, phrase_id, table="phrases",
                        user_id=current_user_id(), cfg=_current_mastery_cfg(conn))
    return {"ok": True, **r}


@router.delete("/{phrase_id}", status_code=204)
def delete_phrase(phrase_id: int):
    """フレーズの完全削除は管理者専用(2026-08-09〜、単語と同じ理由)。

    学習記録(user_phrase_progress)を持つフレーズは削除しない
    (2026-08-12〜、単語のdelete_wordと同じ理由・ON DELETE CASCADEによる
    無警告データ消失を防ぐ)。"""
    from ..services import auth
    with db() as conn:
        me = auth.get_user(conn, auth.current_user_id())
        if not me or me.get("role") != "admin":
            raise HTTPException(403, "フレーズの削除は管理者のみ行えます。")
        has_progress = conn.execute(
            "SELECT 1 FROM user_phrase_progress WHERE phrase_id = ? LIMIT 1",
            (phrase_id,),
        ).fetchone()
        if has_progress:
            raise HTTPException(
                409, "このフレーズには学習記録があるため削除できません。"
                "一覧から除外したい場合は、シーンを「禁止」で始まる名前に"
                "変更してください。")
        cur = conn.execute("DELETE FROM phrases WHERE id = ?", (phrase_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "フレーズが見つかりません")


def _json_object(text: str) -> dict | None:
    import json
    raw = (text or "").strip()
    s, e = raw.find("{"), raw.rfind("}")
    if s == -1 or e == -1:
        return None
    try:
        d = json.loads(raw[s:e + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    return d if isinstance(d, dict) else None


@router.post("/{phrase_id}/detail")
def phrase_detail(phrase_id: int, regen: bool = False):
    """フレーズの詳細情報をAIで生成してキャッシュ（単語のdetailと同じ方式・
    2回目以降はキャッシュを返す）。格言・慣用句・誤解されやすい言い回し・
    マナーに関わる表現は補足を厚く、普通の日常フレーズは軽くと、AI側で
    重要度に応じて濃淡をつける（全フレーズに詳細が必要なわけではないため、
    ボタンを押した時だけ生成し、少しずつDBに蓄積する運用を想定）。"""
    import json as _json

    from ..config import load_settings
    from ..services import ai
    from ..services.auth import (
        current_user_allow_banned, current_user_id, is_guest_user_id,
    )

    with db() as conn:
        row = conn.execute(
            "SELECT english, japanese, scene, detail FROM phrases "
            "WHERE id = ?", (phrase_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "フレーズが見つかりません")
        # 一覧(`_phrase_filter`)を経由しないID直指定のため、ここでも
        # 禁止用語チェックが必須(2026-08-17セキュリティ修正・IDを
        # 知っていれば`allow_banned=False`のユーザーにも詳細生成/表示
        # されてしまっていた)。
        scene = row["scene"] or ""
        if scene.startswith("禁止") and not current_user_allow_banned():
            raise HTTPException(404, "フレーズが見つかりません")
        # 詳細の閲覧は2026-08-11よりtierを問わず常時無料
        # （docs/ACCESS_TIERS.md「機能アクセス表」参照）。ただし**未生成の
        # 詳細を新たにAIで作る**のは実コストが発生するため、未ログインの
        # ゲスト(①)には許可しない(2026-08-11・ゲスト本実装時に発見)。
        if row["detail"] and not regen:
            try:
                return {"ok": True, "cached": True,
                        "detail": _json.loads(row["detail"])}
            except ValueError:
                pass
        if is_guest_user_id(conn, current_user_id()):
            return {
                "ok": False,
                "error": "詳細の生成はログインすると利用できます。",
            }
    if not ai.is_enabled():
        return {"ok": False, "error": "OPENAI_API_KEY が未設定です。"}
    system = (
        "英語フレーズの詳細情報を日本語でJSONのみ作成する英語講師です。"
        "このフレーズが(a)格言・ことわざ・歴史的に有名な発言・出典のある"
        "引用、(b)よく使われる重要な慣用表現、(c)直訳すると誤解を招く/"
        "字面と実際の意味がずれている言い回し、(d)使う場面や相手を間違えると"
        "失礼・不自然になるマナーに関わる表現、のいずれかに該当するなら"
        "深く濃い内容にし、当てはまらないありふれた日常フレーズなら軽めで"
        "よい（無理に話を作らない・該当しない項目は空文字でよい）。"
        "キー: "
        "nuance(意味のニュアンス・フォーマル度・実際に使われる場面), "
        "similar_expressions(類似表現/言い換えの配列[{en,ja,diff}]。diffは"
        "元のフレーズとのニュアンス・丁寧さ・使う場面の違い。2〜4個程度), "
        "background(由来・歴史的背景。格言/名言なら誰がいつどんな文脈で"
        "言った/書いたか、出典、時代背景まで踏み込む。慣用句ならその語源。"
        "普通のフレーズで特筆すべき由来が無ければ空文字), "
        "caution(誤解されやすい点、または失礼・マナー違反になりうる点の"
        "具体的な注意。該当しなければ空文字), "
        "trivia(豆知識。関連する文化的背景・著名な引用例・映画や書籍での"
        "使用例など、本当に自然なものがあれば1つ。無ければ空文字), "
        "explanation(総合的な使い方の解説。1〜2文で簡潔に). "
        "必ず完結したJSONのみを出力（途中で切らない）。"
    )
    user = (
        f"フレーズ: {row['english']}\n日本語訳: {row['japanese']}\n"
        f"シーン: {row['scene'] or '指定なし'}"
    )
    r = ai.chat(system, user, temperature=0.4, max_tokens=1200,
                feature="phrase_detail", model=load_settings().quality_model)
    if not r.ok:
        return {"ok": False, "error": r.error}
    data = _json_object(r.text)
    if not data:
        return {"ok": False, "error": "詳細の生成に失敗しました。"}
    with db() as conn:
        conn.execute(
            "UPDATE phrases SET detail = ? WHERE id = ?",
            (_json.dumps(data, ensure_ascii=False), phrase_id),
        )
    return {"ok": True, "cached": False, "detail": data}


@router.get("/quiz")
def quiz(
    limit: int = 10,
    include_banned: bool = False,
    scene: str | None = None,
    level_min: str | None = None,
    level_max: str | None = None,
    out_of_range: bool = False,
    mastered: str | None = None,   # 'only' | 'hide' | None
    free_range_only: bool = False,  # 🔊無料で再生できる範囲のみ(2026-08-12)
    deck_id: int | None = None,    # 自分のフレーズ帳で絞り込み(2026-08-18)
):
    """フラッシュフレーズと共用。シーン/レベル/覚えた状態でフィルタ可能
    （単語版`/api/words/quiz`と同じインタフェース、列だけscene違い）。
    deck_idを指定すると、そのフレーズ帳(自分の所有分のみ)に含まれる
    フレーズだけに絞り込む(シーン/レベル等の他条件と併用可)。"""
    from ..services import access_tiers
    from ..services.auth import (
        current_user_allow_banned, current_user_id, is_guest_user_id,
    )
    include_banned = include_banned and current_user_allow_banned()
    with db() as conn:
        uid = current_user_id()
        cfg = _current_mastery_cfg(conn)
        where, params = _phrase_filter(
            scene, level_min, level_max, out_of_range, include_banned,
            mastered, mastered_threshold=cfg.mastered_threshold,
        )
        is_guest = is_guest_user_id(conn, uid)
        if deck_id is not None:
            owned = conn.execute(
                "SELECT 1 FROM phrase_decks WHERE id = ? AND user_id = ?",
                (deck_id, uid),
            ).fetchone()
            if not owned:
                raise HTTPException(404, "フレーズ帳が見つかりません")
            where = where + [
                "id IN (SELECT phrase_id FROM deck_phrases "
                "WHERE deck_id = ?)"
            ]
            params = params + [deck_id]
        if free_range_only:
            fr_clause, fr_params = access_tiers.free_range_id_filter(
                "phrase", guest=is_guest,
            )
            where = where + [fr_clause]
            params = params + fr_params
        where_extra = " AND ".join(where)
        rows = select_for_review(
            conn, table="phrases", limit=limit,
            exclude_banned=False,  # banned は _phrase_filter 側で処理済み
            user_id=uid,
            where_extra=where_extra, params_extra=tuple(params),
            cfg=cfg,
        )
        free_ids = access_tiers.free_range_ids(
            conn, "phrase", guest=is_guest)
        return [_phrase_dict(r, free_ids, cfg) for r in rows]


class PhraseRestoreIn(BaseModel):
    mastery: int
    review_level: int | None = None
    next_review: str | None = None


@router.post("/{phrase_id}/restore")
def restore_progress(phrase_id: int, payload: PhraseRestoreIn):
    """直前の採点を取り消す（フラッシュフレーズの「戻る」）。単語版
    `restore_progress`(vocabulary.py)と同じ方式。"""
    from ..services.auth import current_user_id
    from ..services import progress as P
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM phrases WHERE id = ?", (phrase_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, "フレーズが見つかりません")
        cfg = _current_mastery_cfg(conn)
        fields: dict = {"mastery": clamp(payload.mastery, cfg.mastery_max),
                        "perfect": 0}
        if payload.review_level is not None:
            fields["review_level"] = payload.review_level
        fields["next_review"] = payload.next_review
        P.upsert_progress(
            conn, current_user_id(), "phrases", phrase_id, **fields)
    return {"ok": True, "mastery": fields["mastery"]}


@router.post("/attempt")
def attempt(payload: PhraseAttempt):
    from ..services.auth import current_user_allow_banned, current_user_id
    with db() as conn:
        # 禁止用語IDへの学習記録の直接書き込みも拒否する(2026-08-17・
        # fable監査で発見: これを許すと`/api/learn/assess`のAI診断文
        # 経由で禁止用語の英文/和訳が漏れる)。
        if not current_user_allow_banned():
            banned = conn.execute(
                "SELECT 1 FROM phrases WHERE id = ? AND scene LIKE '禁止%'",
                (payload.phrase_id,),
            ).fetchone()
            if banned:
                raise HTTPException(404, "フレーズが見つかりません")
        try:
            result = record_attempt(
                conn,
                payload.phrase_id,
                payload.direction,
                payload.correct,
                result=payload.result,
                table="phrases",
                attempts_table="phrase_attempts",
                id_column="phrase_id",
                user_id=current_user_id(),
                cfg=_current_mastery_cfg(conn),
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        return result
