"""Vocabulary management + quiz endpoints (§3 of the requirements)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import db
from ..schemas import AttemptIn, WordCreate, WordUpdate
from ..services.taxonomy import WORD_CATEGORIES, group_by_category
from ..services.spaced_repetition import (
    MASTERED_THRESHOLD,
    clamp,
    mark_vague as _mark_vague,
    record_attempt,
    selection_weight,
    set_known,
)

router = APIRouter(prefix="/api/words", tags=["vocabulary"])


def _word_dict(row, free_ids: set[int] | None = None) -> dict:
    d = dict(row)
    # detail(JSON)は一覧では送らず、有無フラグだけ返す（応答を軽く保つ）。
    d["has_detail"] = bool((d.pop("detail", "") or "").strip())
    d["selection_priority"] = selection_weight(d["mastery"])
    d["mastered"] = d["mastery"] >= MASTERED_THRESHOLD
    accuracy = (
        round(d["times_correct"] / d["times_asked"] * 100)
        if d["times_asked"]
        else None
    )
    d["accuracy"] = accuracy
    # 🔒無料範囲外の表示用（呼び出し元がfree_idsを渡した場合のみ付与・
    # 2026-08-12）。渡さない呼び出し(作成/更新等)ではフィールド自体を省く。
    if free_ids is not None:
        d["is_free_range"] = d["id"] in free_ids
    return d


BANNED_DOMAIN = "禁止用語"

# レベルの細スケール順（範囲外は別扱い＝チェックで明示的に含める）。
LEVEL_ORDER = [
    "300-", "300", "350", "400", "450", "500", "550", "600", "650",
    "700", "750", "800", "850", "900", "950", "990", "990+",
]
OUT_OF_RANGE = "範囲外"


def _level_range(level_min: str | None, level_max: str | None) -> list[str]:
    """下限〜上限から該当レベル一覧を返す（未指定は端まで）。"""
    def idx(lv, default):
        return LEVEL_ORDER.index(lv) if lv in LEVEL_ORDER else default
    lo = idx(level_min, 0)
    hi = idx(level_max, len(LEVEL_ORDER) - 1)
    if lo > hi:
        lo, hi = hi, lo
    return LEVEL_ORDER[lo:hi + 1]


def _word_filter(
    domain: str | None, level: str | None,
    level_min: str | None, level_max: str | None,
    out_of_range: bool, include_banned: bool, mastered: str | None,
    category: str | None = None,
) -> tuple[list[str], list]:
    """単語一覧/フラッシュカード共通のフィルタ WHERE 句を組み立てる。
    列は素の名前(domain/level/mastery)で参照（一覧の `AS words`・選抜の `AS t`
    どちらの別名でも解決可能）。返り値は (条件リスト, パラメータ)。
    ``category``(大分類)は``domain``が指定されない時のみ有効（大分類配下の
    全分野をOR検索）。``domain``はカンマ区切りで複数分野を指定可（チェック
    ボックスでの複数選択に対応・単一指定時も同じIN句で動作）。"""
    where: list[str] = []
    params: list = []
    if domain:
        domains = [d for d in domain.split(",") if d]
        ph = ",".join("?" * len(domains))
        # 主分類(domain列)に加え、word_domain_tags(§B17・同じ意味で複数
        # 分野に該当する語)でのタグ付けもOR条件に含める。テーブル別名は
        # 呼び出し元でwords/tどちらもあるため列名にプレフィックスを付けない。
        where.append(
            f"(COALESCE(domain, '') IN ({ph}) OR id IN "
            f"(SELECT word_id FROM word_domain_tags WHERE domain IN ({ph})))"
        )
        params += domains + domains
    elif category:
        cat_domains = WORD_CATEGORIES.get(category, [])
        if cat_domains:
            ph = ",".join("?" * len(cat_domains))
            where.append(
                f"(COALESCE(domain, '') IN ({ph}) OR id IN "
                f"(SELECT word_id FROM word_domain_tags "
                f"WHERE domain IN ({ph})))"
            )
            params += cat_domains + cat_domains
    if level:
        where.append("COALESCE(level, '') = ?")
        params.append(level)
    # レベル範囲（下限〜上限）＋範囲外チェック。
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
        where.append("COALESCE(domain, '') <> ?")
        params.append(BANNED_DOMAIN)
    if mastered == "only":
        where.append(f"mastery >= {MASTERED_THRESHOLD}")
    elif mastered == "hide":
        where.append(f"mastery < {MASTERED_THRESHOLD}")
    return where, params


@router.get("")
def list_words(
    sort: str = "mastery",
    desc: bool = False,            # 降順にするか（昇順/降順トグル）
    domain: str | None = None,
    category: str | None = None,   # 大分類（domain未指定時のみ有効）
    level: str | None = None,
    level_min: str | None = None,   # 下限（細スケール）
    level_max: str | None = None,   # 上限
    out_of_range: bool = False,     # 「範囲外」も含める
    include_banned: bool = False,
    mastered: str | None = None,   # 'only' | 'hide' | None(=全部)
    deck_id: int | None = None,    # 自分の単語帳で絞り込み(2026-08-09)
    free_range_only: bool = False,  # 🔊無料で再生できる範囲のみ(2026-08-11)
):
    from ..services.auth import (
        current_user_allow_banned, current_user_id, is_guest_user_id,
    )
    include_banned = include_banned and current_user_allow_banned()
    col = {
        "mastery": "mastery",
        "english": "english COLLATE NOCASE",
        "recent": "last_studied",
        "level": "level",
        "domain": "domain",
        "accuracy": (
            "CASE WHEN times_asked > 0 "
            "THEN times_correct * 1.0 / times_asked ELSE -1 END"
        ),
    }.get(sort, "mastery")
    direction = "DESC" if desc else "ASC"
    order = f"{col} {direction}, english COLLATE NOCASE ASC"
    where, params = _word_filter(
        domain, level, level_min, level_max, out_of_range,
        include_banned, mastered, category,
    )
    from ..services.progress import user_items_subquery
    src = user_items_subquery("words")  # 先頭の ? = user_id
    from ..services import access_tiers
    with db() as conn:
        uid = current_user_id()
        is_guest = is_guest_user_id(conn, uid)
        if deck_id is not None:
            owned = conn.execute(
                "SELECT 1 FROM decks WHERE id = ? AND user_id = ?",
                (deck_id, uid),
            ).fetchone()
            if not owned:
                raise HTTPException(404, "単語帳が見つかりません")
            where = where + [
                "words.id IN (SELECT word_id FROM deck_words "
                "WHERE deck_id = ?)"
            ]
            params = params + [deck_id]
        if free_range_only:
            fr_clause, fr_params = access_tiers.free_range_id_filter(
                "word", guest=is_guest,
            )
            where = where + [fr_clause]
            params = params + fr_params
        clause = (" WHERE " + " AND ".join(where)) if where else ""
        rows = conn.execute(
            f"SELECT * FROM {src} AS words{clause} ORDER BY {order}",
            [uid, *params],
        ).fetchall()
        free_ids = access_tiers.free_range_ids(conn, "word", guest=is_guest)
        return [_word_dict(r, free_ids) for r in rows]


@router.get("/facets")
def facets(include_banned: bool = False, include_hidden: bool = False):
    """フィルタUI用の分野(domain)・レベル(level)の選択肢一覧。
    include_banned=true のとき「禁止用語」も分野候補に含める。
    include_hidden=false（既定）のとき、設定画面でユーザーが非表示に
    した分野(user_settings.hidden_domains)を候補から除外する（一覧画面の
    フィルタ用）。設定画面自体はinclude_hidden=trueで全分野を取得する。"""
    from ..services.auth import current_user_allow_banned, \
        current_user_id, get_user_settings
    include_banned = include_banned and current_user_allow_banned()
    with db() as conn:
        domains = [
            r["domain"] for r in conn.execute(
                "SELECT DISTINCT domain FROM words "
                "WHERE COALESCE(domain, '') <> '' ORDER BY domain"
            ).fetchall()
        ]
        # 既定では禁止用語を分野候補から除外（表示トグルONなら含める）。
        if not include_banned:
            domains = [d for d in domains if d != BANNED_DOMAIN]
        if not include_hidden:
            hidden = set(
                get_user_settings(conn, current_user_id())
                .get("hidden_domains", []))
            if hidden:
                domains = [d for d in domains if d not in hidden]
        present = {
            r["level"] for r in conn.execute(
                "SELECT DISTINCT level FROM words WHERE COALESCE(level,'')<>''"
            ).fetchall()
        }
    # 細スケール順に整列（範囲外は末尾、未知のレベルはその後ろ）。
    levels = [lv for lv in LEVEL_ORDER if lv in present]
    if OUT_OF_RANGE in present:
        levels.append(OUT_OF_RANGE)
    levels += sorted(present - set(levels))
    # 範囲指定用（範囲外を除く）の順序付きレベル。
    range_levels = [lv for lv in LEVEL_ORDER if lv in present]
    domain_groups = group_by_category(domains, WORD_CATEGORIES)
    return {
        "domains": domains, "levels": levels,
        "range_levels": range_levels,
        "domain_groups": domain_groups,
    }


def _require_admin(conn) -> None:
    """単語カタログの追加・更新は管理者専用(2026-08-10〜)。カタログは全
    ユーザー共有のため、フロントの追加/インポートフォームも admin-only
    表示だが、API直叩きを塞ぐサーバー側の強制がなかった(delete_wordと
    同種の問題)。"""
    from ..services import auth
    me = auth.get_user(conn, auth.current_user_id())
    if not me or me.get("role") != "admin":
        raise HTTPException(403, "単語の追加・変更は管理者のみ行えます。")


@router.post("", status_code=201)
def create_word(payload: WordCreate):
    with db() as conn:
        _require_admin(conn)
        cur = conn.execute(
            "INSERT INTO words (english, japanese, part_of_speech, example) "
            "VALUES (?, ?, ?, ?)",
            (payload.english, payload.japanese, payload.part_of_speech, payload.example),
        )
        row = conn.execute(
            "SELECT * FROM words WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return _word_dict(row)


@router.put("/{word_id}")
def update_word(word_id: int, payload: WordUpdate):
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(400, "更新する項目がありません")
    sets = ", ".join(f"{k} = ?" for k in fields)
    with db() as conn:
        _require_admin(conn)
        cur = conn.execute(
            f"UPDATE words SET {sets} WHERE id = ?",
            (*fields.values(), word_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "単語が見つかりません")
        row = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
        return _word_dict(row)


@router.delete("/{word_id}", status_code=204)
def delete_word(word_id: int):
    """単語の完全削除は管理者専用(2026-08-09〜)。カタログは全ユーザー共有
    のため、一般ユーザーが個々の単語を削除できると他ユーザーにも影響する。
    「自分の一覧から外したい」場合は単語帳に入れない/単語帳から外すことで
    対応する（`app/routers/decks.py`）。

    学習記録(user_word_progress)を持つ単語は削除しない(2026-08-12〜)。
    `words`→`user_word_progress`のFKはON DELETE CASCADEのため、削除する
    と全ユーザーのその単語の習熟度・忘却曲線の記録が無警告で消えてしまう
    バグに近い挙動があった。既に学習履歴がある単語を除外したい場合は、
    分野を「禁止用語」に変更する（`banned_filter`で出題除外される）。"""
    from ..services import auth
    with db() as conn:
        me = auth.get_user(conn, auth.current_user_id())
        if not me or me.get("role") != "admin":
            raise HTTPException(403, "単語の削除は管理者のみ行えます。")
        has_progress = conn.execute(
            "SELECT 1 FROM user_word_progress WHERE word_id = ? LIMIT 1",
            (word_id,),
        ).fetchone()
        if has_progress:
            raise HTTPException(
                409, "この単語には学習記録があるため削除できません。"
                "一覧から除外したい場合は、分野を「禁止用語」に変更して"
                "ください。")
        cur = conn.execute("DELETE FROM words WHERE id = ?", (word_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "単語が見つかりません")


class DomainTagIn(BaseModel):
    domain: str


@router.get("/{word_id}/tags")
def list_word_tags(word_id: int):
    """指定単語の追加分野タグ一覧を返す（§B17・論点1-a）。主分類
    (words.domain)は含まない・タグのみ。"""
    with db() as conn:
        row = conn.execute(
            "SELECT id FROM words WHERE id = ?", (word_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "単語が見つかりません")
        rows = conn.execute(
            "SELECT domain FROM word_domain_tags WHERE word_id = ? "
            "ORDER BY domain", (word_id,),
        ).fetchall()
    return {"tags": [r["domain"] for r in rows]}


@router.post("/{word_id}/tags", status_code=201)
def add_word_tag(word_id: int, payload: DomainTagIn):
    """単語に追加の分野タグを付与する（同じ意味で複数分野に該当する語用。
    管理者専用）。既存の主分類(words.domain)と同じ値は追加不要のため拒否。"""
    domain = payload.domain.strip()
    if not domain:
        raise HTTPException(400, "domainを指定してください。")
    with db() as conn:
        _require_admin(conn)
        row = conn.execute(
            "SELECT domain FROM words WHERE id = ?", (word_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "単語が見つかりません")
        if (row["domain"] or "") == domain:
            raise HTTPException(
                400, "既に主分類として設定されている分野です。")
        conn.execute(
            "INSERT OR IGNORE INTO word_domain_tags (word_id, domain) "
            "VALUES (?, ?)", (word_id, domain),
        )
        rows = conn.execute(
            "SELECT domain FROM word_domain_tags WHERE word_id = ? "
            "ORDER BY domain", (word_id,),
        ).fetchall()
    return {"tags": [r["domain"] for r in rows]}


@router.delete("/{word_id}/tags/{domain}", status_code=204)
def remove_word_tag(word_id: int, domain: str):
    """単語から分野タグを削除する（管理者専用）。"""
    with db() as conn:
        _require_admin(conn)
        conn.execute(
            "DELETE FROM word_domain_tags WHERE word_id = ? AND domain = ?",
            (word_id, domain),
        )


@router.get("/quiz")
def quiz(
    limit: int = 10,
    include_banned: bool = False,
    domain: str | None = None,
    level: str | None = None,
    level_min: str | None = None,
    level_max: str | None = None,
    out_of_range: bool = False,
    mastered: str | None = None,   # 'only' | 'hide' | None
    free_range_only: bool = False,  # 🔊無料で再生できる範囲のみ(2026-08-12)
):
    """Return a weighted set of words to quiz (probability ∝ 100 - mastery).
    分野/レベル/覚えた状態でフィルタ可能（フラッシュカードと共用）。"""
    from ..services import access_tiers
    from ..services.auth import (
        current_user_allow_banned, current_user_id, is_guest_user_id,
    )
    include_banned = include_banned and current_user_allow_banned()
    from ..services.spaced_repetition import select_for_review
    where, params = _word_filter(
        domain, level, level_min, level_max, out_of_range,
        include_banned, mastered,
    )
    with db() as conn:
        uid = current_user_id()
        is_guest = is_guest_user_id(conn, uid)
        if free_range_only:
            fr_clause, fr_params = access_tiers.free_range_id_filter(
                "word", guest=is_guest,
            )
            where = where + [fr_clause]
            params = params + fr_params
        where_extra = " AND ".join(where)
        rows = select_for_review(
            conn, table="words", limit=limit,
            exclude_banned=False,  # banned は _word_filter 側で処理済み
            user_id=uid,
            where_extra=where_extra, params_extra=tuple(params),
        )
        free_ids = access_tiers.free_range_ids(conn, "word", guest=is_guest)
        return [_word_dict(r, free_ids) for r in rows]


@router.post("/attempt")
def attempt(payload: AttemptIn):
    from ..services.auth import current_user_id
    with db() as conn:
        try:
            result = record_attempt(
                conn, payload.word_id, payload.direction, payload.correct,
                result=payload.result, user_id=current_user_id(),
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        return result


class KnownIn(BaseModel):
    known: bool = True


@router.post("/{word_id}/known")
def mark_known(word_id: int, payload: KnownIn):
    """「覚えた」ボタン(per-user): mastery を満点(200)に、復習間隔も最長へ。
    known=false で解除（mastery/間隔とも復活させる）。"""
    from ..services.auth import current_user_id
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM words WHERE id = ?", (word_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, "単語が見つかりません")
        r = set_known(conn, word_id, payload.known, table="words",
                      user_id=current_user_id())
    return {"ok": True, "known": payload.known, **r}


@router.post("/{word_id}/vague")
def mark_vague(word_id: int):
    """「うろ覚え」ボタン(per-user): mastery を +10（0..200でクランプ）、
    復習間隔も約2日後に更新する。"""
    from ..services.auth import current_user_id
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM words WHERE id = ?", (word_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, "単語が見つかりません")
        r = _mark_vague(conn, word_id, table="words",
                        user_id=current_user_id())
    return {"ok": True, **r}


class RestoreIn(BaseModel):
    mastery: int
    review_level: int | None = None
    next_review: str | None = None


@router.post("/{word_id}/restore")
def restore_progress(word_id: int, payload: RestoreIn):
    """直前の採点を取り消す（フラッシュカードの「戻る」）。採点前にクライアントが
    控えた習得度/復習レベル/次回日を per-user 進捗へ書き戻す。"""
    from ..services.auth import current_user_id
    from ..services import progress as P
    fields: dict = {"mastery": clamp(payload.mastery)}
    if payload.review_level is not None:
        fields["review_level"] = payload.review_level
    # next_review は None(未学習に戻す) も許容して上書きする。
    fields["next_review"] = payload.next_review
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM words WHERE id = ?", (word_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, "単語が見つかりません")
        P.upsert_progress(conn, current_user_id(), "words", word_id, **fields)
    return {"ok": True, "mastery": fields["mastery"]}


def _json_object(text: str) -> dict | None:
    import json
    a, b = text.find("{"), text.rfind("}")
    if a == -1 or b == -1:
        return None
    try:
        d = json.loads(text[a:b + 1])
        return d if isinstance(d, dict) else None
    except (json.JSONDecodeError, ValueError):
        return None


@router.post("/{word_id}/detail")
def word_detail(word_id: int, regen: bool = False):
    """単語の詳細情報(品詞/意味複数/例文/派生/類義語/対義語/由来/豆知識/解説)を
    AIで生成してキャッシュ。2回目以降はキャッシュを返す（無料）。重いので
    ボタン押下時にだけ生成し、少しずつDBに蓄積する。"""
    import json as _json

    from ..config import load_settings
    from ..services import ai
    from ..services.auth import (
        current_user_allow_banned, current_user_id, is_guest_user_id,
    )

    with db() as conn:
        row = conn.execute(
            "SELECT english, japanese, example, detail, domain FROM words "
            "WHERE id = ?", (word_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "単語が見つかりません")
        # 一覧(`_word_filter`)を経由しないID直指定のため、ここでも
        # 禁止用語チェックが必須(2026-08-17セキュリティ修正・IDを
        # 知っていれば`allow_banned=False`のユーザーにも詳細生成/表示
        # されてしまっていた)。
        if row["domain"] == BANNED_DOMAIN and not current_user_allow_banned():
            raise HTTPException(404, "単語が見つかりません")
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
        "英単語の詳細情報を日本語でJSONのみ作成。キー: "
        "pronunciation(発音記号・IPA。米音を基本にスラッシュで囲む 例: /əˈbændən/), "
        "pos(主な品詞), meanings(意味の配列・主要な語義を複数), "
        "examples(配列[{en,ja}]・自然な例文1〜2個), "
        "example_ja(上記『既存例文』の自然な日本語訳。既存例文が無ければ空文字), "
        "derivatives(派生語の配列[{word,pos,ja}]・元が形容詞なら動詞/副詞/名詞"
        "形など他の品詞の関連語も含める), "
        "synonyms(類義語の配列[{word,note}]。note は各類義語の意味やニュアンス・"
        "使い分けの違いを簡潔に), "
        "antonyms(対義語の配列[{word,note}]), "
        "origin(語源・由来。可能なら接頭辞/語根/接尾辞に分解し各要素の意味を示す"
        "(例: abnormal = ab-「離れて」+ normal「正常」)。語源に出てくる語があれば"
        "その意味も一言添える), "
        "trivia(豆知識。関連が本当にあれば、著名人・聖書・哲学・有名な技術・歴史上の"
        "名言や出来事・有名な書籍や映画のセリフとの結びつきを1つ挙げる。無理に作らず"
        "自然なものだけ), "
        "explanation(使い方・ニュアンスの解説). "
        "簡潔に。必ず完結したJSONのみを出力（途中で切らない）。"
    )
    user = (
        f"単語: {row['english']}\n既知の訳: {row['japanese']}\n"
        f"既存例文: {row['example'] or 'なし'}"
    )
    r = ai.chat(system, user, temperature=0.3, max_tokens=1500,
                feature="detail", model=load_settings().quality_model)
    if not r.ok:
        return {"ok": False, "error": r.error}
    data = _json_object(r.text)
    if not data:
        return {"ok": False, "error": "詳細の生成に失敗しました。"}
    with db() as conn:
        conn.execute(
            "UPDATE words SET detail = ? WHERE id = ?",
            (_json.dumps(data, ensure_ascii=False), word_id),
        )
    return {"ok": True, "cached": False, "detail": data}


class ResolveIn(BaseModel):
    words: list[str]


@router.post("/resolve")
def resolve_words(payload: ResolveIn):
    """与えた英単語リストのうち、DBに登録済みのものを返す（類義語ジャンプ用）。
    詳細の synonyms/antonyms/derivatives の語をクリックでその語へ飛べるように、
    フロントが表示時にどれが登録済みかを引くための軽量エンドポイント。

    同綴りだが意味が違う語（§B17・論点1-b。例: agentのIT用語/スパイ用語/
    代理人の意味）は別々のwords行として登録される設計のため、1つの綴りに
    複数件ヒットしうる。返り値は{小文字キー: [{id, english, japanese,
    level, example, domain, has_detail}, ...]}で、キーごとに配列（1件でも
    配列）。フロント側で1件なら直接ジャンプ、複数なら選択させる。"""
    keys = []
    seen = set()
    for w in payload.words or []:
        k = (w or "").strip().lower()
        if k and k not in seen:
            seen.add(k)
            keys.append(k)
    if not keys:
        return {"found": {}}
    from ..services.auth import current_user_allow_banned
    found: dict[str, list[dict]] = {}
    with db() as conn:
        # 小文字一致でまとめて引く（IN 句）。語数は詳細1件ぶんで小さい。
        # 禁止用語は類義語ジャンプ用途でも意味・例文ごと漏れないよう除外
        # する(2026-08-17セキュリティ修正)。
        qmarks = ",".join("?" * len(keys))
        params = list(keys)
        ban = ""
        if not current_user_allow_banned():
            ban = " AND COALESCE(domain, '') <> ?"
            params.append(BANNED_DOMAIN)
        rows = conn.execute(
            f"SELECT id, english, japanese, level, example, domain, detail "
            f"FROM words WHERE LOWER(english) IN ({qmarks}){ban} "
            f"ORDER BY id", params
        ).fetchall()
    for r in rows:
        k = r["english"].strip().lower()
        found.setdefault(k, []).append({
            "id": r["id"], "english": r["english"],
            "japanese": r["japanese"], "level": r["level"],
            "example": r["example"], "domain": r["domain"],
            "has_detail": bool((r["detail"] or "").strip()),
        })
    return {"found": found}


class ImportIn(BaseModel):
    text: str
    generate_examples: bool = True


def _parse_word_list(text: str) -> list[tuple[str, str]]:
    """貼り付けたテキストから (英単語, 日本語) を抽出。タブ/カンマ区切りでも、
    『英語の行→日本語の行』が交互に並ぶ形式でも解析する。番号や記号は無視。"""
    import re
    import unicodedata

    def is_en(s: str) -> bool:
        return bool(re.search(r"[A-Za-z]", s)) and not re.search(
            r"[ぁ-んァ-ヶ一-鿿]", s)

    def is_ja(s: str) -> bool:
        return bool(re.search(r"[ぁ-んァ-ヶ一-鿿ー〜、。・]", s))

    pairs: list[tuple[str, str]] = []
    cur: str | None = None
    for raw in text.splitlines():
        s = unicodedata.normalize("NFKC", raw).strip()
        if not s:
            continue
        parts = re.split(r"\t|,|，|\s{2,}", s, maxsplit=1)
        if len(parts) == 2 and is_en(parts[0]) and is_ja(parts[1]):
            if cur:
                pairs.append((cur, ""))
                cur = None
            pairs.append((parts[0].strip(), parts[1].strip()))
            continue
        if s.isdigit() or s.startswith("+") or s == "0":
            continue
        if is_en(s):
            # 直前の英語に訳が無ければ英語のみで確定（訳はAIが生成）。
            if cur:
                pairs.append((cur, ""))
            cur = s.strip()
        elif is_ja(s) and cur:
            pairs.append((cur, s.strip()))
            cur = None
    if cur:
        pairs.append((cur, ""))
    return pairs


def _json_array(text: str) -> list:
    import json
    raw = text.strip()
    a, b = raw.find("["), raw.rfind("]")
    if a == -1 or b == -1:
        return []
    try:
        data = json.loads(raw[a:b + 1])
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def _ai_fill(pairs: list[tuple[str, str]]) -> dict:
    """AIで各語の正確な訳・品詞・例文を生成（訳ヒントが誤りなら修正）。"""
    from ..config import load_settings
    from ..services import ai

    model = load_settings().quality_model
    out: dict[str, dict] = {}
    for i in range(0, len(pairs), 20):
        batch = pairs[i:i + 20]
        listing = "\n".join(f"{e} | {j}" for e, j in batch)
        system = (
            "英単語学習データを作ります。各語について正確で簡潔な日本語訳・"
            "品詞・自然な英語例文・分野(domain)・難易度(level)を作成。"
            "訳ヒントが不正確なら正しい訳に直す。"
            "domain は 宗教/文学/歴史/口語/IT/ビジネス/ニュース/医療/旅行/法律/"
            "科学/教養 のいずれか、一般的な語なら空文字。"
            "level は TOEIC目安で 600/700/800 のいずれか。"
            "JSON配列のみ出力: "
            '[{"english":"..","japanese":"..","pos":"品詞","example":"..",'
            '"domain":"..","level":".."}]'
        )
        user = f"語(英語 | 訳ヒント):\n{listing}"
        r = ai.chat(system, user, temperature=0.3, max_tokens=2400,
                    feature="import", model=model)
        if r.ok:
            for it in _json_array(r.text):
                en = str(it.get("english", "")).strip()
                if en:
                    out[en.lower()] = {
                        "japanese": str(it.get("japanese", "")).strip(),
                        "pos": str(it.get("pos", "")).strip(),
                        "example": str(it.get("example", "")).strip(),
                        "domain": str(it.get("domain", "")).strip(),
                        "level": str(it.get("level", "")).strip(),
                    }
    return out


@router.post("/import")
def import_words(payload: ImportIn):
    from ..services import ai

    pairs = _parse_word_list(payload.text)
    with db() as conn:
        _require_admin(conn)
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
    new: list[tuple[str, str]] = []
    seen: set[str] = set()
    for en, ja in pairs:
        k = en.lower()
        if k in existing or k in seen:
            continue
        seen.add(k)
        new.append((en, ja))

    filled = {}
    if payload.generate_examples and ai.is_enabled() and new:
        filled = _ai_fill(new)

    rows = []
    for en, ja in new:
        f = filled.get(en.lower(), {})
        rows.append((
            en,
            f.get("japanese") or ja,
            f.get("pos", ""),
            f.get("example", ""),
            f.get("domain", ""),
            f.get("level", ""),
        ))
    with db() as conn:
        conn.executemany(
            "INSERT INTO words (english, japanese, part_of_speech, example, "
            "domain, level) VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
    return {
        "ok": True,
        "parsed": len(pairs),
        "added": len(rows),
        "skipped": len(pairs) - len(rows),
        "examples": sum(1 for r in rows if r[3]),
    }


@router.post("/retag")
def retag(batch: int = 30):
    """分野(domain)・レベル(level)が未設定の単語をAIで分類して付与。
    1回で batch 件処理し、残数を返す（スクリプトで繰り返し呼ぶ想定）。"""
    from ..config import load_settings
    from ..services import ai

    with db() as conn:
        _require_admin(conn)
    if not ai.is_enabled():
        return {"ok": False, "error": "OPENAI_API_KEY が未設定です。"}
    with db() as conn:
        rows = conn.execute(
            "SELECT id, english, japanese FROM words "
            "WHERE COALESCE(domain,'')='' AND COALESCE(level,'')='' "
            "LIMIT ?",
            (batch,),
        ).fetchall()
        remaining = conn.execute(
            "SELECT COUNT(*) AS c FROM words "
            "WHERE COALESCE(domain,'')='' AND COALESCE(level,'')=''"
        ).fetchone()["c"]
    if not rows:
        return {"ok": True, "tagged": 0, "remaining": 0}

    listing = "\n".join(f"{r['id']}\t{r['english']}\t{r['japanese']}"
                        for r in rows)
    system = (
        "各英単語に分野(domain)と難易度(level)を付けます。"
        "domain は 宗教/文学/歴史/口語/IT/ビジネス/ニュース/医療/旅行/法律/"
        "科学/教養 のいずれか。一般的でどれにも当てはまらなければ空文字。"
        "level は TOEIC目安で 600/700/800。"
        'JSON配列のみ: [{"id":1,"domain":"..","level":".."}]'
    )
    result = ai.chat(
        system, f"id\\t英語\\t訳:\n{listing}",
        temperature=0, max_tokens=1500,
        feature="retag", model=load_settings().quality_model,
    )
    if not result.ok:
        return {"ok": False, "error": result.error}
    tagged = 0
    with db() as conn:
        for it in _json_array(result.text):
            try:
                wid = int(it.get("id"))
            except (TypeError, ValueError):
                continue
            conn.execute(
                "UPDATE words SET domain = ?, level = ? WHERE id = ?",
                (str(it.get("domain", "")).strip(),
                 str(it.get("level", "")).strip() or "600", wid),
            )
            tagged += 1
    return {"ok": True, "tagged": tagged, "remaining": max(0, remaining - tagged)}


@router.get("/stats")
def stats():
    from ..services.auth import current_user_id, get_user_settings
    from ..services.metrics import toeic_estimate, word_buckets

    uid = current_user_id()
    with db() as conn:
        b = word_buckets(conn, "words", user_id=uid)
        self_toeic = get_user_settings(conn, uid).get("toeic_self")
    b["toeic_estimate"] = toeic_estimate(
        b["avg_mastery"], b["mastered"], b["total"],
        studied=b["studied"], self_declared=self_toeic,
    )
    return b
