# ruff: noqa: E501
"""Assign a difficulty level to every phrase (scene-based + length nudge).
Authored by Claude — no app/OpenAI API calls. Idempotent. Mirrors the word
level scale (300-/300/.../990+/範囲外). Run: python scripts/relevel_phrases.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db, init_db  # noqa: E402

ORDER = ["300-", "300", "400", "500", "600", "700", "800", "900", "990", "990+"]


def base_level(scene: str) -> str:
    s = scene or ""
    if s.startswith("禁止"):
        return "範囲外"
    for k in ("名言", "哲学", "宗教", "キリスト", "仏教", "ユダヤ", "イスラム",
              "古典", "絶望"):
        if k in s:
            return "800"
    if "ニュース" in s:
        return "800"
    for k in ("ビジネス", "IT", "管理", "AI", "会議", "開発"):
        if k in s:
            return "700"
    for k in ("慣用", "誤用", "和製"):
        if k in s:
            return "700"
    for k in ("病院", "病状", "症状", "軍事", "銃器", "警察", "犯罪", "護身",
              "緊急", "鉄道", "観光客", "両替", "AI指示"):
        if k in s:
            return "600"
    for k in ("生活", "日常", "友人", "家庭", "趣味", "ホテル", "レストラン",
              "買い物", "道案内", "観光", "出入国", "税関", "電話", "外国人",
              "スーパー", "ご近所"):
        if k in s:
            return "500"
    return "600"


def bump(level: str, steps: int) -> str:
    if level not in ORDER:
        return level
    i = min(len(ORDER) - 1, max(0, ORDER.index(level) + steps))
    return ORDER[i]


def main() -> int:
    init_db()  # ensure phrases.level column exists
    with db() as conn:
        rows = conn.execute(
            "SELECT id, english, scene FROM phrases"
        ).fetchall()
        dist: dict[str, int] = {}
        for r in rows:
            lv = base_level(r["scene"])
            # 長い文(語数多)は一段難しめに（範囲外は据え置き）。
            words = len((r["english"] or "").split())
            if lv != "範囲外" and words >= 14:
                lv = bump(lv, 1)
            conn.execute(
                "UPDATE phrases SET level = ? WHERE id = ?", (lv, r["id"])
            )
            dist[lv] = dist.get(lv, 0) + 1
    print("フレーズ難易度の分布:",
          dict(sorted(dist.items(), key=lambda x: (x[0] == "範囲外", x[0]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
