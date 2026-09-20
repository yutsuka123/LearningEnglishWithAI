"""撮影対象の語・フレーズが「ゲストの無料範囲にあり、音声が保存済み」であることの
事前確認(preflight)。

動画で映した操作(🆓を押して音が鳴る)を、実際のゲストも同じように体験できる
ことを担保するための確認。語彙が更新されて範囲から外れたり音声が消えたり
した場合は、撮影前にここで失敗させる(誤った動画を作らない)。

判定は `app/services/access_tiers.py` の関数をそのまま使う。ただし
`app` パッケージ経由で import すると app.config が(あれば)`.env` を
読み込んでしまうため、ファイルパスから単体でロードする(access_tiers は
sqlite3 以外に依存しない)。
"""

from __future__ import annotations

import hashlib
import importlib.util
import sqlite3
from pathlib import Path

from .appserver import REPO_ROOT

MIN_AUDIO_BYTES = 8 * 1024


def _load_access_tiers():
    path = REPO_ROOT / "app" / "services" / "access_tiers.py"
    spec = importlib.util.spec_from_file_location("_at_standalone", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


access_tiers = _load_access_tiers()


def open_content(data_dir: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{data_dir / 'content.db'}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]


def audio_sizes(audio_dir: Path, item_type: str, item_id: int, text: str,
                kinds=("phrase",), voices=("ash", "nova")) -> dict:
    """{'phrase_ash': bytes, ...}(無ければ0)。"""
    h = _hash(text)
    out = {}
    for k in kinds:
        for v in voices:
            p = audio_dir / f"{item_type}{item_id}_{k}_{v}_{h}.mp3"
            out[f"{k}_{v}"] = p.stat().st_size if p.exists() else 0
    return out


def require_guest_playable_phrase(data_dir: Path, english: str) -> dict:
    """フレーズ(英文一致)が ①ゲスト無料範囲内 ②詳細あり ③男声/女声の
    保存音声が8KB以上 を満たすか確認し、情報を返す。満たさなければ例外。"""
    conn = open_content(data_dir)
    try:
        row = conn.execute(
            "SELECT id, english, japanese, level, scene, detail "
            "FROM phrases WHERE english = ?", (english,)).fetchone()
        if row is None:
            raise RuntimeError(f"フレーズが見つかりません: {english}")
        free = access_tiers.is_free_range(
            conn, "phrase", row["id"], guest=True)
    finally:
        conn.close()
    if not free:
        raise RuntimeError(
            f"ゲストの無料範囲外です(🔒になる): id={row['id']} {english}")
    if not (row["detail"] or "").strip():
        raise RuntimeError(f"詳細が未作成です: id={row['id']} {english}")
    sizes = audio_sizes(data_dir / "audio", "phrase", row["id"], english)
    bad = {k: v for k, v in sizes.items()
           if k.startswith("phrase_") and v < MIN_AUDIO_BYTES}
    if bad:
        raise RuntimeError(f"音声が無い/8KB未満です: id={row['id']} {bad}")
    return {"id": row["id"], "english": row["english"],
            "japanese": row["japanese"], "level": row["level"],
            "scene": row["scene"], "audio": sizes}
