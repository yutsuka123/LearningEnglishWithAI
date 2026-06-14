"""AI-powered learning endpoints: material generation (news/reading/literature),
conversation role-play, writing feedback, and session start/end (§8-§14)."""

from __future__ import annotations

import json
from datetime import date

from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..database import db
from ..schemas import (
    ConversationIn,
    GenerateIn,
    SessionEndIn,
    WritingFeedbackIn,
)
from ..services import ai, persistence
from ..services.context_builder import build_context
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

    system = (
        "あなたは英語学習教材を作る講師です。" + _LEVEL_NOTE +
        " 出力はMarkdownで、英文・日本語訳・重要語彙(3〜6語、英語/日本語)・"
        "簡単な内容理解問題(2問)を含めてください。"
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
def list_materials(area: str | None = None, limit: int = 20):
    with db() as conn:
        if area:
            rows = conn.execute(
                "SELECT * FROM materials WHERE area = ? ORDER BY id DESC LIMIT ?",
                (area, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM materials ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


def _conversation_prompts(payload: ConversationIn) -> tuple[str, str]:
    system = (
        "あなたは親切な英会話パートナー兼コーチです。" + _LEVEL_NOTE +
        f" シーン: {payload.grp} / {payload.topic}。"
        " 自然な英語で短めに返答し、最後に【コーチ】として、学習者の文の"
        "良い点と直すべき点を日本語で1〜2行添えてください。"
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


@router.post("/conversation")
def conversation(payload: ConversationIn):
    """Non-streaming conversation turn (used as a fallback)."""
    system, user = _conversation_prompts(payload)
    result = ai.chat(
        system, user, temperature=0.8, max_tokens=600, feature="conversation"
    )
    return {"ok": result.ok, "reply": result.text, "error": result.error}


@router.post("/conversation/stream")
def conversation_stream(payload: ConversationIn):
    """Streamed conversation turn for responsiveness (text/plain chunks)."""
    system, user = _conversation_prompts(payload)

    def gen():
        yield from ai.chat_stream(
            system, user, temperature=0.8,
            max_tokens=600, feature="conversation",
        )

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")


class TtsIn(BaseModel):
    text: str
    voice: str = "alloy"


@router.post("/tts")
def tts(payload: TtsIn):
    """Return natural-voice MP3 audio for the given text (OpenAI TTS)."""
    audio, error = ai.synthesize_speech(payload.text, payload.voice)
    if error:
        # 422 lets the frontend fall back to the browser voice.
        return Response(content=error, status_code=422, media_type="text/plain")
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
def daily_session(words: int = 10, phrases: int = 10):
    """Build a ~10-minute daily plan: vocab + mini-phrases + reading + writing.

    Up to 10 words and 10 phrases per session (learner's cap). Items are
    chosen by the forgetting-curve scheduler (due items first). Returns the
    concrete items so the client can run the fast part without AI calls."""
    n_words = max(1, min(words, 10))
    n_phrases = max(1, min(phrases, 10))

    with db() as conn:
        words_list = [
            {
                "id": r["id"],
                "english": r["english"],
                "japanese": r["japanese"],
                "example": r["example"],
                "mastery": r["mastery"],
            }
            for r in select_for_review(conn, table="words", limit=n_words)
        ]
        phrase_rows = select_for_review(
            conn, table="phrases", limit=n_phrases
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
