"""Pydantic request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# --- Vocabulary ---------------------------------------------------------------

class WordCreate(BaseModel):
    english: str = Field(min_length=1)
    japanese: str = Field(min_length=1)
    part_of_speech: str = ""
    example: str = ""


class WordUpdate(BaseModel):
    english: str | None = None
    japanese: str | None = None
    part_of_speech: str | None = None
    example: str | None = None


class AttemptIn(BaseModel):
    word_id: int
    direction: str  # 'ja2en' | 'en2ja'
    correct: bool


# --- Categories (conversation / reading / writing / literature) --------------

class CategoryStudyIn(BaseModel):
    category_id: int
    mastery_delta: int = 5


class ListeningStudyIn(BaseModel):
    topic_id: int
    comprehension: int | None = None
    weak_areas: str | None = None


# --- AI / sessions -----------------------------------------------------------

class GenerateIn(BaseModel):
    area: str  # news / reading / literature / conversation / writing / listening
    field: str = ""
    instruction: str = ""


class WritingFeedbackIn(BaseModel):
    category: str = ""
    prompt: str = ""
    text: str


class ConversationIn(BaseModel):
    grp: str = ""
    topic: str = ""
    message: str
    history: list[dict] = []  # [{role, content}] kept client-side only


class SessionEndIn(BaseModel):
    content: str = ""
    accuracy: int | None = None
    weak_points: str = ""
    next_topic: str = ""
    new_words: str = ""


class MemoryUpdateIn(BaseModel):
    content: str


class SettingsIn(BaseModel):
    openai_api_key: str | None = None
    openai_model: str | None = None
