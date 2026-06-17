"""Vocabulary management + quiz endpoints (§3 of the requirements)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import db
from ..schemas import AttemptIn, WordCreate, WordUpdate
from ..services.spaced_repetition import (
    MASTERED_THRESHOLD,
    clamp,
    pick_weighted,
    record_attempt,
    selection_weight,
    set_known,
)

VAGUE_BONUS = 10  # 「うろ覚え」ボタンで加点する mastery

router = APIRouter(prefix="/api/words", tags=["vocabulary"])


def _word_dict(row) -> dict:
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
    desc: bool = False,            # 降順にするか（昇順/降順トグル）
    domain: str | None = None,
    level: str | None = None,
    level_min: str | None = None,   # 下限（細スケール）
    level_max: str | None = None,   # 上限
    out_of_range: bool = False,     # 「範囲外」も含める
    include_banned: bool = False,
    mastered: str | None = None,   # 'only' | 'hide' | None(=全部)
):
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
    from ..services.auth import current_user_id
    from ..services.progress import user_items_subquery
    src = user_items_subquery("words")  # 先頭の ? = user_id
    with db() as conn:
        rows = conn.execute(
            f"SELECT * FROM {src} AS words{clause} ORDER BY {order}",
            [current_user_id(), *params],
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
    from ..services.auth import current_user_id
    with db() as conn:
        rows = pick_weighted(
            conn, limit=limit, exclude_banned=not include_banned,
            user_id=current_user_id(),
        )
        return [_word_dict(r) for r in rows]


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
    """「覚えた」ボタン(per-user): mastery を満点(200)に。known=false で解除。"""
    from ..services.auth import current_user_id
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM words WHERE id = ?", (word_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, "単語が見つかりません")
        new = set_known(conn, word_id, payload.known, table="words",
                        user_id=current_user_id())
    return {"ok": True, "mastery": new, "known": payload.known}


@router.post("/{word_id}/vague")
def mark_vague(word_id: int):
    """「うろ覚え」ボタン(per-user): mastery を +10（0..200でクランプ）。"""
    from ..services.auth import current_user_id
    from ..services import progress as P
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM words WHERE id = ?", (word_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, "単語が見つかりません")
        uid = current_user_id()
        cur = P.get_progress(conn, uid, "words", word_id)
        new = clamp(cur["mastery"] + VAGUE_BONUS)
        P.upsert_progress(conn, uid, "words", word_id, mastery=new)
    return {"ok": True, "mastery": new}


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

    with db() as conn:
        row = conn.execute(
            "SELECT english, japanese, example, detail FROM words "
            "WHERE id = ?", (word_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "単語が見つかりません")
        if row["detail"] and not regen:
            try:
                return {"ok": True, "cached": True,
                        "detail": _json.loads(row["detail"])}
            except ValueError:
                pass
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
        "origin(語源・由来。語源に出てくる語(例: amine/アミン等)があれば、その語が"
        "何を意味するかも一言添えて分かりやすく), "
        "trivia(豆知識), explanation(使い方・ニュアンスの解説). "
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
    返り値: {found: {小文字キー: {id, english, japanese, level, example,
    has_detail}}}。"""
    keys = []
    seen = set()
    for w in payload.words or []:
        k = (w or "").strip().lower()
        if k and k not in seen:
            seen.add(k)
            keys.append(k)
    if not keys:
        return {"found": {}}
    found: dict[str, dict] = {}
    with db() as conn:
        # 小文字一致でまとめて引く（IN 句）。語数は詳細1件ぶんで小さい。
        qmarks = ",".join("?" * len(keys))
        rows = conn.execute(
            f"SELECT id, english, japanese, level, example, detail "
            f"FROM words WHERE LOWER(english) IN ({qmarks})", keys
        ).fetchall()
    for r in rows:
        k = r["english"].strip().lower()
        if k in found:
            continue  # 同綴り重複は先勝ち
        found[k] = {
            "id": r["id"], "english": r["english"],
            "japanese": r["japanese"], "level": r["level"],
            "example": r["example"],
            "has_detail": bool((r["detail"] or "").strip()),
        }
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
