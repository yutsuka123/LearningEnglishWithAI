"""Vocabulary management + quiz endpoints (§3 of the requirements)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import db
from ..schemas import AttemptIn, WordCreate, WordUpdate
from ..services.spaced_repetition import (
    MASTERED_THRESHOLD,
    pick_weighted,
    record_attempt,
    selection_weight,
    set_known,
)

router = APIRouter(prefix="/api/words", tags=["vocabulary"])


def _word_dict(row) -> dict:
    d = dict(row)
    d["selection_priority"] = selection_weight(d["mastery"])
    d["mastered"] = d["mastery"] >= MASTERED_THRESHOLD
    accuracy = (
        round(d["times_correct"] / d["times_asked"] * 100)
        if d["times_asked"]
        else None
    )
    d["accuracy"] = accuracy
    return d




BANNED_DOMAIN = "禁止用語"

# レベルの細スケール順（範囲外は別扱い＝チェックで明示的に含める）。
LEVEL_ORDER = [
    "300-", "300", "400", "500", "600", "700", "800", "900", "990", "990+",
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


@router.get("")
def list_words(
    sort: str = "mastery",
    domain: str | None = None,
    level: str | None = None,
    level_min: str | None = None,   # 下限（細スケール）
    level_max: str | None = None,   # 上限
    out_of_range: bool = False,     # 「範囲外」も含める
    include_banned: bool = False,
    mastered: str | None = None,   # 'only' | 'hide' | None(=全部)
):
    order = {
        "mastery": "mastery ASC, last_studied ASC",
        "english": "english COLLATE NOCASE ASC",
        "recent": "last_studied DESC",
        "level": "level ASC, english COLLATE NOCASE ASC",
        "domain": "domain ASC, english COLLATE NOCASE ASC",
        "accuracy": (
            "CASE WHEN times_asked > 0 "
            "THEN times_correct * 1.0 / times_asked ELSE -1 END DESC"
        ),
    }.get(sort, "mastery ASC, last_studied ASC")
    where: list[str] = []
    params: list = []
    if domain:
        where.append("COALESCE(domain, '') = ?")
        params.append(domain)
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
        # 範囲外(=禁止用語)も見たい場合は、そのレベルだけ除外を緩める。
        if out_of_range:
            where.append(
                "(COALESCE(domain, '') <> ? OR COALESCE(level, '') = ?)")
            params += [BANNED_DOMAIN, OUT_OF_RANGE]
        else:
            where.append("COALESCE(domain, '') <> ?")
            params.append(BANNED_DOMAIN)
    if mastered == "only":
        where.append(f"mastery >= {MASTERED_THRESHOLD}")
    elif mastered == "hide":
        where.append(f"mastery < {MASTERED_THRESHOLD}")
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    with db() as conn:
        rows = conn.execute(
            f"SELECT * FROM words{clause} ORDER BY {order}", params
        ).fetchall()
        return [_word_dict(r) for r in rows]


@router.get("/facets")
def facets(include_banned: bool = False):
    """フィルタUI用の分野(domain)・レベル(level)の選択肢一覧。
    include_banned=true のとき「禁止用語」も分野候補に含める。"""
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
    return {
        "domains": domains, "levels": levels,
        "range_levels": range_levels,
    }


@router.post("", status_code=201)
def create_word(payload: WordCreate):
    with db() as conn:
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
    with db() as conn:
        cur = conn.execute("DELETE FROM words WHERE id = ?", (word_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "単語が見つかりません")


@router.get("/quiz")
def quiz(limit: int = 10, include_banned: bool = False):
    """Return a weighted set of words to quiz (probability ∝ 100 - mastery)."""
    with db() as conn:
        rows = pick_weighted(
            conn, limit=limit, exclude_banned=not include_banned
        )
        return [_word_dict(r) for r in rows]


@router.post("/attempt")
def attempt(payload: AttemptIn):
    with db() as conn:
        try:
            result = record_attempt(
                conn, payload.word_id, payload.direction, payload.correct,
                result=payload.result,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        return result


class KnownIn(BaseModel):
    known: bool = True


@router.post("/{word_id}/known")
def mark_known(word_id: int, payload: KnownIn):
    """「覚えた」ボタン: mastery を満点(200)に。known=false で解除。"""
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM words WHERE id = ?", (word_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, "単語が見つかりません")
        new = set_known(conn, word_id, payload.known, table="words")
    return {"ok": True, "mastery": new, "known": payload.known}


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
    from ..services.metrics import toeic_estimate, word_buckets

    with db() as conn:
        b = word_buckets(conn, "words")
    b["toeic_estimate"] = toeic_estimate(
        b["avg_mastery"], b["mastered"], b["total"]
    )
    return b
