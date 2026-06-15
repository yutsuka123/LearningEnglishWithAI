"""AI-powered learning endpoints: material generation (news/reading/literature),
conversation role-play, writing feedback, and session start/end (§8-§14)."""

from __future__ import annotations

import json
from datetime import date

from fastapi import APIRouter, File, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..database import db
from ..schemas import (
    ConversationIn,
    GenerateIn,
    SessionEndIn,
    WritingFeedbackIn,
)
from ..config import load_settings
from ..services import ai, audio_store, persistence
from ..services.context_builder import build_context
from ..services.metrics import toeic_estimate, word_buckets
from ..services.spaced_repetition import select_for_review

router = APIRouter(prefix="/api/learn", tags=["learn"])

_LEVEL_NOTE = (
    "学習者は TOEIC 550〜600 程度で、短期目標 700 点・最終目標 800 点以上です。"
    "難しすぎず、少し背伸びするレベルで作成してください。"
)


@router.get("/context")
def context():
    """The compact context we feed to the AI (also useful for the UI to show)."""
    return {"context": build_context(), "ai_enabled": ai.is_enabled()}


@router.post("/generate")
def generate(payload: GenerateIn):
    """Generate study material for a given area/field and store it."""
    area_label = {
        "news": "ニュース記事",
        "reading": "リーディング教材",
        "literature": "文学の抜粋と解説",
        "listening": "リスニング用スクリプト",
    }.get(payload.area, payload.area)

    diff_note = (
        f" 難易度は『{payload.difficulty}』に合わせ、語彙・文構造・文章量を"
        "その水準にしてください（学習者プロフィールより難易度指定を優先）。"
        if payload.difficulty else ""
    )
    system = (
        "あなたは英語学習教材を作る講師です。" + _LEVEL_NOTE + diff_note +
        " 出力はMarkdownで、次の構成にしてください: "
        "(1) 英文本文、(2) 日本語訳、(3) 重要語彙(3〜6語・英語/日本語)、"
        "(4) 見出し『## Comprehension Questions』の下に内容理解問題を2問。"
        "内容理解問題は設問・選択肢・解答をすべて英語で書くこと"
        "（読み上げの言語を英語に統一するため。問題部分に日本語訳は付けない）。"
    )
    user = (
        f"{build_context()}\n\n"
        f"## 依頼\n分野/カテゴリ: {payload.field or '指定なし'}\n"
        f"種類: {area_label}\n"
        f"追加指示: {payload.instruction or 'なし'}\n"
        "上記の学習者に合わせた教材を1つ作成してください。"
    )
    result = ai.chat(system, user, max_tokens=1600, feature=payload.area)
    if not result.ok:
        return {"ok": False, "error": result.error}

    title = f"{payload.field or area_label} ({date.today().isoformat()})"
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO materials (area, field, title, body) VALUES (?, ?, ?, ?)",
            (payload.area, payload.field, title, result.text),
        )
        material_id = cur.lastrowid
    return {"ok": True, "id": material_id, "title": title, "body": result.text}


@router.get("/materials")
def list_materials(
    area: str | None = None, areas: str | None = None, limit: int = 100,
):
    """area 単一、または areas=カンマ区切りで複数領域の履歴を新しい順に。"""
    area_list = (
        [a.strip() for a in areas.split(",") if a.strip()] if areas
        else ([area] if area else [])
    )
    with db() as conn:
        if area_list:
            ph = ",".join("?" * len(area_list))
            rows = conn.execute(
                f"SELECT * FROM materials WHERE area IN ({ph}) "
                "ORDER BY id DESC LIMIT ?", (*area_list, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM materials ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


@router.get("/materials/{material_id}")
def get_material(material_id: int):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM materials WHERE id = ?", (material_id,)
        ).fetchone()
        if not row:
            return Response(content="not found", status_code=404,
                            media_type="text/plain")
        return dict(row)


@router.delete("/materials/{material_id}", status_code=204)
def delete_material(material_id: int):
    with db() as conn:
        conn.execute("DELETE FROM materials WHERE id = ?", (material_id,))


@router.post("/materials/{material_id}/known")
def material_known(material_id: int):
    with db() as conn:
        conn.execute(
            "UPDATE materials SET mastery = 200 WHERE id = ?", (material_id,))
    return {"ok": True, "mastery": 200}


@router.post("/materials/{material_id}/vague")
def material_vague(material_id: int):
    with db() as conn:
        row = conn.execute(
            "SELECT mastery FROM materials WHERE id = ?", (material_id,)
        ).fetchone()
        new = max(0, min(200, (row["mastery"] if row else 0) + 10))
        conn.execute(
            "UPDATE materials SET mastery = ? WHERE id = ?",
            (new, material_id))
    return {"ok": True, "mastery": new}


def _is_free_mode(payload: ConversationIn) -> bool:
    return payload.grp == "自由会話"


def _conversation_prompts(payload: ConversationIn) -> tuple[str, str]:
    if _is_free_mode(payload):
        system = (
            "あなたは万能の英語学習チューターです。" + _LEVEL_NOTE +
            " 学習者は英語でも日本語でも話します。日本語で話しかけられても"
            "歓迎し、英語学習に橋渡ししてください。要望に応じて何でも対応する: "
            "単語クイズ、フレーズ練習、リスニング(英文を読み上げ用に提示)、"
            "ライティング添削、文法説明、ロールプレイなど。"
            " まず自然な英語で短く応答し、必要なら日本語で簡潔に補足/解説。"
            "日本語で質問されて日本語で答える場合でも、英語の先生として必ず"
            "対応する英語表現や英文も添えること（英語学習につなげる）。"
            "学習者が『わからない』と言ったら、やさしく答えやヒントを示す。"
            "毎回さりげなく次の一歩を促してください。"
            " 改善後の英文を示すときは、最後の行に『【例】<改善後の自然な英文>』"
            "を1文だけ付けてください。"
        )
    else:
        system = (
            "あなたは親切な英会話パートナー兼コーチです。" + _LEVEL_NOTE +
            f" シーン: {payload.grp} / {payload.topic}。"
            " 自然な英語で短めに返答し、次に【コーチ】として学習者の文の"
            "良い点と直すべき点を日本語で1〜2行。"
            " さらに最後の行に『【例】<学習者が言える改善後の自然な英文>』"
            "を必ず1文付けてください（この英文は読み上げ用）。"
        )
    window = payload.history[-6:]
    transcript = "\n".join(
        f"{m.get('role')}: {m.get('content')}" for m in window
    )
    user = (
        f"{build_context()}\n\n## これまでの会話\n{transcript}\n\n"
        f"## 学習者の発話\n{payload.message}"
    )
    return system, user


def _log_conversation(role: str, content: str, mode: str) -> None:
    if not content.strip():
        return
    with db() as conn:
        conn.execute(
            "INSERT INTO conversation_log (role, content, mode) "
            "VALUES (?, ?, ?)",
            (role, content.strip(), mode),
        )


@router.post("/conversation")
def conversation(payload: ConversationIn):
    """Non-streaming conversation turn (used as a fallback)."""
    system, user = _conversation_prompts(payload)
    result = ai.chat(
        system, user, temperature=0.8, max_tokens=700, feature="conversation"
    )
    return {"ok": result.ok, "reply": result.text, "error": result.error}


@router.post("/conversation/stream")
def conversation_stream(payload: ConversationIn):
    """Streamed conversation turn for responsiveness (text/plain chunks)."""
    system, user = _conversation_prompts(payload)
    mode = "free" if _is_free_mode(payload) else (payload.topic or payload.grp)

    def gen():
        # Log the learner's message (real production for level judging).
        if payload.message and not payload.message.startswith("("):
            _log_conversation("user", payload.message, mode)
        full = []
        for chunk in ai.chat_stream(
            system, user, temperature=0.8,
            max_tokens=700, feature="conversation",
        ):
            full.append(chunk)
            yield chunk
        _log_conversation("assistant", "".join(full), mode)

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")


class TranslateIn(BaseModel):
    text: str


@router.post("/translate")
def translate(payload: TranslateIn):
    """英文を日本語に訳す（会話の「日本語訳を表示」用）。"""
    if not ai.is_enabled():
        return {"ok": False, "error": "OPENAI_API_KEY が未設定です。"}
    system = "次の英文を自然な日本語に訳してください。訳文のみ出力。"
    result = ai.chat(
        system, payload.text, temperature=0.2,
        max_tokens=600, feature="translate",
    )
    return {"ok": result.ok, "text": result.text, "error": result.error}


class ExampleIn(BaseModel):
    word: str


@router.post("/example")
def example_sentence(payload: ExampleIn):
    """単語を使った例文を1つ生成（英文＋日本語訳）。"""
    if not ai.is_enabled():
        return {"ok": False, "error": "OPENAI_API_KEY が未設定です。"}
    system = (
        "英単語を使った短い例文を1つ作ります。" + _LEVEL_NOTE +
        ' JSONのみ出力: {"english":"...","japanese":"...訳..."}'
    )
    result = ai.chat(
        system, f'単語: "{payload.word}"',
        temperature=0.5, max_tokens=200, feature="example",
    )
    if not result.ok:
        return {"ok": False, "error": result.error}
    raw = result.text.strip()
    s, e = raw.find("{"), raw.rfind("}")
    try:
        data = json.loads(raw[s:e + 1]) if s != -1 else {}
    except (json.JSONDecodeError, ValueError):
        data = {}
    return {
        "ok": True,
        "english": str(data.get("english", "")).strip(),
        "japanese": str(data.get("japanese", "")).strip(),
    }


@router.post("/reply-examples")
def reply_examples(payload: ConversationIn):
    """直近のAI発話に対する「返答例」を生成（答えに困ったとき用）。"""
    if not ai.is_enabled():
        return {"ok": False, "error": "OPENAI_API_KEY が未設定です。"}
    window = payload.history[-6:]
    transcript = "\n".join(
        f"{m.get('role')}: {m.get('content')}" for m in window
    )
    system = (
        "あなたは英会話コーチです。" + _LEVEL_NOTE +
        " 直近のAIの発話に対して、学習者が言える自然な返答例を3つ、"
        "英語＋日本語訳つきでMarkdownの箇条書きで示してください。短く実用的に。"
    )
    user = (
        f"## これまでの会話\n{transcript}\n\n"
        "学習者が次に言える英語の返答例を3つ提案してください。"
    )
    result = ai.chat(
        system, user, temperature=0.7,
        max_tokens=500, feature="reply_examples",
    )
    return {"ok": result.ok, "text": result.text, "error": result.error}


@router.get("/assess")
def assess():
    """学習データから現在のレベルをAIが判定（品質モデルを使用）。"""
    with db() as conn:
        wb = word_buckets(conn, "words")
        pb = word_buckets(conn, "phrases")
        studied = conn.execute(
            "SELECT english, japanese, times_asked, times_correct, "
            "ok_en2ja, ask_en2ja, ok_ja2en, ask_ja2en "
            "FROM words WHERE times_asked > 0 ORDER BY times_asked DESC"
        ).fetchall()
        convo = conn.execute(
            "SELECT content FROM conversation_log "
            "WHERE role = 'user' ORDER BY id DESC LIMIT 20"
        ).fetchall()

    total = wb["total"] + pb["total"]
    mastered = wb["mastered"] + pb["mastered"]
    avg = 0.0
    if total:
        avg = (wb["avg_mastery"] * wb["total"]
               + pb["avg_mastery"] * pb["total"]) / total
    est = toeic_estimate(avg, mastered, total)

    base = {
        "toeic_estimate": est,
        "studied_words": len(studied),
        "words": wb,
        "phrases": pb,
    }
    if not ai.is_enabled():
        base["ok"] = False
        base["error"] = "OPENAI_API_KEY が未設定です。"
        return base
    if not studied and not convo:
        base["ok"] = False
        base["error"] = "まだ学習データがありません。クイズや会話をしてください。"
        return base

    lines = []
    for w in studied:
        acc = round(w["times_correct"] / w["times_asked"] * 100)
        lines.append(
            f"{w['english']}({w['japanese']}): 正答{acc}% "
            f"英→日 {w['ok_en2ja']}/{w['ask_en2ja']} "
            f"日→英 {w['ok_ja2en']}/{w['ask_ja2en']}"
        )
    convo_block = ""
    if convo:
        utterances = "\n".join(f"- {c['content'][:160]}" for c in convo)
        convo_block = (
            "\n\n## 自由会話での学習者の発話（産出力の参考）\n" + utterances
        )
    system = (
        "あなたは経験豊富なTOEIC講師です。学習者の単語テスト結果"
        "と自由会話での発話から現在の実力を診断してください。"
        "会話の発話は文法・語彙・自然さの観点でも見てください。"
        "出力はMarkdownで、次の見出し: "
        "### 推定レベル(TOEICレンジ) / ### 強み / ### 弱み / "
        "### 次に強化すべき点 / ### おすすめ学習法。"
        "データが少ない場合はその旨も明記し、断定しすぎないこと。"
    )
    user = (
        f"{build_context()}\n\n## 単語テスト結果（{len(studied)}語）\n"
        + ("\n".join(lines) or "（まだなし）")
        + convo_block
        + f"\n\n## 参考: データ上のTOEIC目安 {est}点 / "
        f"平均習熟度 {round(avg, 1)} / 習得 {mastered}語"
    )
    qmodel = load_settings().quality_model
    result = ai.chat(
        system, user, temperature=0.4, max_tokens=1100,
        feature="assess", model=qmodel,
    )
    base["ok"] = result.ok
    base["assessment"] = result.text
    base["error"] = result.error
    base["model"] = qmodel
    return base


class GenItemsIn(BaseModel):
    kind: str = "word"   # 'word' | 'phrase'
    count: int = 10
    focus: str = ""      # テーマ・苦手分野など
    domain: str = ""     # 単語に付ける分野タグ（宗教/文学/IT 等・任意）


@router.post("/generate-items")
def generate_items(payload: GenItemsIn):
    """AIで単語/フレーズを生成してDBに追加（品質モデルを使用・重複は除外）。"""
    if not ai.is_enabled():
        return {"ok": False, "error": "OPENAI_API_KEY が未設定です。"}
    n = max(1, min(payload.count, 30))
    focus = payload.focus.strip() or "日常〜ビジネス・IT"
    qmodel = load_settings().quality_model

    if payload.kind == "phrase":
        system = (
            "英語学習用の実用フレーズをJSON配列のみで出力します。" + _LEVEL_NOTE
            + ' 形式: [{"english":"...","japanese":"...","scene":"..."}]'
        )
        user = (
            f"{build_context()}\n\nテーマ/場面: {focus}\n"
            f"そこで本当に使う自然なフレーズを{n}個。JSON配列のみ。"
        )
    else:
        system = (
            "英単語をJSON配列のみで出力します。" + _LEVEL_NOTE
            + ' 形式: [{"english":"...","japanese":"...",'
            '"pos":"品詞","example":"英語例文"}]'
        )
        user = (
            f"{build_context()}\n\nテーマ/苦手分野: {focus}\n"
            f"学習者の弱点補強に役立つ単語を{n}個。JSON配列のみ。"
        )

    result = ai.chat(
        system, user, temperature=0.5, max_tokens=1800,
        feature="gen_items", model=qmodel,
    )
    if not result.ok:
        return {"ok": False, "error": result.error}

    items = _parse_json_array(result.text)
    if not items:
        return {"ok": False, "error": "生成結果を解釈できませんでした。"}

    added, skipped = _insert_generated(payload.kind, items, payload.domain)
    return {"ok": True, "added": added, "skipped": skipped, "model": qmodel}


def _parse_json_array(text: str) -> list:
    raw = text.strip()
    start, end = raw.find("["), raw.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        data = json.loads(raw[start:end + 1])
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def _insert_generated(
    kind: str, items: list, domain: str = ""
) -> tuple[list, int]:
    added: list[dict] = []
    skipped = 0
    domain = (domain or "").strip()
    with db() as conn:
        if kind == "phrase":
            existing = {
                r["english"].lower()
                for r in conn.execute("SELECT english FROM phrases").fetchall()
            }
            for it in items:
                en = str(it.get("english", "")).strip()
                ja = str(it.get("japanese", "")).strip()
                if not en or not ja or en.lower() in existing:
                    skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, str(it.get("scene", "")).strip()),
                )
                existing.add(en.lower())
                added.append({"english": en, "japanese": ja})
        else:
            existing = {
                r["english"].lower()
                for r in conn.execute("SELECT english FROM words").fetchall()
            }
            for it in items:
                en = str(it.get("english", "")).strip()
                ja = str(it.get("japanese", "")).strip()
                if not en or not ja or en.lower() in existing:
                    skipped += 1
                    continue
                # AIがdomain/levelを返せばそれを優先、無ければ引数domain。
                dm = str(it.get("domain", "")).strip() or domain
                lv = str(it.get("level", "")).strip()
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, ja, str(it.get("pos", "")).strip(),
                     str(it.get("example", "")).strip(), dm, lv),
                )
                existing.add(en.lower())
                added.append({"english": en, "japanese": ja})
    return added, skipped


class TtsIn(BaseModel):
    text: str
    voice: str = "alloy"


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """音声→テキスト（言語自動判定）。英会話の音声入力に使用。"""
    audio = await file.read()
    text, error = ai.transcribe(audio, file.filename or "audio.webm")
    if error:
        return {"ok": False, "error": error}
    return {"ok": True, "text": text}


@router.post("/tts")
def tts(payload: TtsIn):
    """Return natural-voice MP3 audio for the given text (OpenAI TTS)."""
    audio, error = ai.synthesize_speech(payload.text, payload.voice)
    if error:
        # 422 lets the frontend fall back to the browser voice.
        return Response(content=error, status_code=422, media_type="text/plain")
    return Response(content=audio, media_type="audio/mpeg")


def _item_text(conn, item_type: str, item_id: int, kind: str) -> str | None:
    """番号(ID)から読み上げ対象テキストを取得。"""
    if item_type == "word":
        row = conn.execute(
            "SELECT english, example FROM words WHERE id = ?", (item_id,)
        ).fetchone()
        if not row:
            return None
        if kind == "example":
            return (row["example"] or "").strip() or None
        return (row["english"] or "").strip() or None
    if item_type == "phrase":
        row = conn.execute(
            "SELECT english FROM phrases WHERE id = ?", (item_id,)
        ).fetchone()
        return (row["english"].strip() if row else None) or None
    return None


@router.get("/tts/item")
def tts_item(
    item_type: str, item_id: int, voice: str = "ash", kind: str = "",
    speed: str = "learn",
):
    """番号(ID)で音声を取得。保存済みなら即返す(=無料)。無ければ合成して
    保存し、次回以降はトークン不要にする。type=word|phrase、kind は word/
    example/phrase。speed=learn(学習・ゆっくり明瞭) / native(自然な速さ)。"""
    item_type = item_type if item_type in audio_store.VALID_TYPES else "word"
    base = kind if kind in ("word", "example", "phrase") else (
        "phrase" if item_type == "phrase" else "word")
    speed = "native" if speed == "native" else "learn"
    skind = audio_store.storage_kind(base, speed)

    with db() as conn:
        cached = audio_store.get(conn, item_type, item_id, skind, voice)
        if cached is not None:
            return Response(content=cached, media_type="audio/mpeg")
        text = _item_text(conn, item_type, item_id, base)

    if not text:
        return Response(
            content="読み上げる本文がありません（例文なし等）。",
            status_code=422, media_type="text/plain",
        )

    audio, error = ai.synthesize_speech(text, voice, style=speed)
    if error:
        return Response(content=error, status_code=422,
                        media_type="text/plain")
    with db() as conn:
        audio_store.put(conn, item_type, item_id, skind, voice, audio)
    return Response(content=audio, media_type="audio/mpeg")


@router.post("/writing-feedback")
def writing_feedback(payload: WritingFeedbackIn):
    system = (
        "あなたは英作文の添削講師です。" + _LEVEL_NOTE +
        " 出力はMarkdownで、次の順に: 1) 添削後の自然な英文, "
        "2) 主な修正点(日本語の箇条書き), 3) より良くするヒント, "
        "4) 100点満点の評価。"
    )
    user = (
        f"カテゴリ: {payload.category or '指定なし'}\n"
        f"お題: {payload.prompt or '指定なし'}\n\n"
        f"## 学習者の英作文\n{payload.text}"
    )
    result = ai.chat(
        system, user, temperature=0.4,
        max_tokens=1000, feature="writing",
    )
    return {"ok": result.ok, "feedback": result.text, "error": result.error}


@router.post("/session/summary")
def session_summary(payload: SessionEndIn):
    """Ask the AI to produce the end-of-session outputs described in §14.
    Falls back to a template if AI is unavailable."""
    if not ai.is_enabled():
        return {
            "ok": False,
            "error": "OPENAI_API_KEY が未設定です。手動入力で保存できます。",
        }
    system = (
        "あなたは学習コーチです。本日の学習内容を踏まえ、以下のセクションを"
        "Markdownで日本語出力してください: ### 学習結果 / ### 新出単語 / "
        "### 苦手ポイント / ### 次回課題 / ### memory更新案 / ### study_log更新案。"
    )
    user = (
        f"{build_context()}\n\n## 本日の入力\n"
        f"学習内容: {payload.content}\n正答率: {payload.accuracy}\n"
        f"苦手: {payload.weak_points}\n次回希望: {payload.next_topic}\n"
        f"新出単語: {payload.new_words}"
    )
    result = ai.chat(
        system, user, temperature=0.5,
        max_tokens=1400, feature="session_summary",
    )
    return {"ok": result.ok, "summary": result.text, "error": result.error}


@router.post("/session/save")
def session_save(payload: SessionEndIn):
    """Persist a study session to the DB and append to study_log.md (§10, §12)."""
    with db() as conn:
        conn.execute(
            "INSERT INTO study_sessions "
            "(content, accuracy, weak_points, next_topic, new_words) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                payload.content,
                payload.accuracy,
                payload.weak_points,
                payload.next_topic,
                payload.new_words,
            ),
        )
    entry = persistence.format_session_entry(
        content=payload.content,
        accuracy=payload.accuracy,
        weak_points=payload.weak_points,
        next_topic=payload.next_topic,
        new_words=payload.new_words,
    )
    persistence.append_study_log(entry)
    return {"ok": True, "appended": entry}


@router.get("/daily")
def daily_session(
    words: int = 10, phrases: int = 10, include_banned: bool = False
):
    """Build a ~10-minute daily plan: vocab + mini-phrases + reading + writing.

    Up to 10 words and 10 phrases per session (learner's cap). Items are
    chosen by the forgetting-curve scheduler (due items first). Returns the
    concrete items so the client can run the fast part without AI calls.
    禁止用語は ``include_banned`` が真でない限り出題しない。"""
    n_words = max(1, min(words, 10))
    n_phrases = max(1, min(phrases, 10))
    ban = not include_banned

    with db() as conn:
        words_list = [
            {
                "id": r["id"],
                "english": r["english"],
                "japanese": r["japanese"],
                "example": r["example"],
                "mastery": r["mastery"],
            }
            for r in select_for_review(
                conn, table="words", limit=n_words, exclude_banned=ban
            )
        ]
        phrase_rows = select_for_review(
            conn, table="phrases", limit=n_phrases, exclude_banned=ban
        )
        phrases_list = [dict(r) for r in phrase_rows]

    plan = [
        {"step": "vocab", "label": "英単語テスト", "items": words_list},
        {"step": "phrases", "label": "ミニフレーズ", "items": phrases_list},
        {
            "step": "reading",
            "label": "リーディング (1題)",
            "items": [],
            "needs_ai": True,
        },
        {
            "step": "writing",
            "label": "ライティング (1題・音声応答可)",
            "items": [],
            "needs_ai": True,
        },
    ]
    return {"plan": plan, "ai_enabled": ai.is_enabled()}


# --- Voice / natural-language command interpreter ----------------------------

class CommandIn(BaseModel):
    text: str


_KNOWN_ACTIONS = (
    "navigate(tab): tab は dashboard/vocab/phrases/reading/writing/"
    "conversation/listening/news/literature/settings のいずれか。"
    " set_model(model), set_input_mode(mode: voice|text),"
    " start_daily(), save_session(), speak(text), none()"
)


@router.post("/command")
def interpret_command(payload: CommandIn):
    """Map a free-form (often spoken) instruction to an app action.

    With AI: returns a structured intent JSON. Without AI: keyword fallback
    so basic voice navigation works offline. The client executes the action;
    settings changes etc. are therefore voice-driven (ユーザー要望)."""
    text = payload.text.strip()
    if not text:
        return {"action": "none", "args": {}, "say": ""}

    if ai.is_enabled():
        system = (
            "ユーザーの日本語/英語の指示を、英語学習アプリの操作意図に変換します。"
            " 必ず次のJSONのみを返答: "
            '{"action": "...", "args": {...}, "say": "確認の一言"}。'
            f" 使えるaction: {_KNOWN_ACTIONS}"
        )
        result = ai.chat(
            system, text, temperature=0, max_tokens=200, feature="command"
        )
        if result.ok:
            try:
                raw = result.text.strip()
                start, end = raw.find("{"), raw.rfind("}")
                if start != -1 and end != -1:
                    return json.loads(raw[start:end + 1])
            except (json.JSONDecodeError, ValueError):
                pass

    return _fallback_command(text)


def _fallback_command(text: str) -> dict:
    low = text.lower()
    tabs = {
        "単語": "vocab", "word": "vocab",
        "フレーズ": "phrases", "phrase": "phrases",
        "リーディング": "reading", "読": "reading", "reading": "reading",
        "ライティング": "writing", "書": "writing", "writing": "writing",
        "会話": "conversation", "conversation": "conversation",
        "リスニング": "listening", "listening": "listening",
        "ニュース": "news", "news": "news",
        "文学": "literature",
        "設定": "settings", "settings": "settings",
        "ダッシュ": "dashboard", "ホーム": "dashboard",
    }
    for key, tab in tabs.items():
        if key in text or key in low:
            return {
                "action": "navigate",
                "args": {"tab": tab},
                "say": f"{tab} を開きます",
            }
    if "音声" in text or "voice" in low:
        return {
            "action": "set_input_mode",
            "args": {"mode": "voice"},
            "say": "音声入力に切り替えます",
        }
    if ("文字" in text or "テキスト" in text or "text" in low):
        return {
            "action": "set_input_mode",
            "args": {"mode": "text"},
            "say": "文字入力に切り替えます",
        }
    if "today" in low or "毎日" in text or "デイリー" in text or "始め" in text:
        return {"action": "start_daily", "args": {}, "say": "今日の学習を始めます"}
    return {"action": "none", "args": {}, "say": "うまく聞き取れませんでした"}
