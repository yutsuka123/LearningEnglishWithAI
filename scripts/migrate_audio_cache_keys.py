# ruff: noqa: E501
"""One-time migration (2026-08-05 incident follow-up): rename existing
audio cache files from the old ID-only naming (``{type}{id}_{kind}_{voice}
.mp3``) to the new content-hash-suffixed naming (``..._{hash}.mp3``) so the
already-generated cache is preserved instead of being thrown away wholesale
by the audio_store.py change that added text_hash to the cache key.

Safe to run on any environment (local or production, via ``docker exec``):
for each word/phrase, computes the CURRENT text's hash and renames the old
file to the new name if the old file exists and the new one doesn't yet.
Old files for ids where the underlying text is no longer trustworthy should
already have been deleted (see the 2026-08-05 incident cleanup) — this
script does not try to detect that itself, it just carries forward whatever
old files still exist under their current text's hash.

Run:  python scripts/migrate_audio_cache_keys.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402
from app.services import audio_store  # noqa: E402

VOICES = ["ash", "nova"]
# (item_type, id_col, table, text_col, kinds) — kinds: (base, speed) pairs.
JOBS = [
    ("word", "words", "english", [("word", "learn")]),
    ("word", "words", "example", [("example", "learn"), ("example", "native")]),
    ("phrase", "phrases", "english", [("phrase", "learn"), ("phrase", "native")]),
]


def migrate(dry_run: bool) -> None:
    audio_dir = audio_store._audio_dir()
    renamed = missing_old = already_new = skipped_no_text = 0
    with db() as conn:
        for item_type, table, text_col, kinds in JOBS:
            rows = conn.execute(f"SELECT id, {text_col} FROM {table}").fetchall()
            for r in rows:
                text = (r[text_col] or "").strip()
                if not text:
                    skipped_no_text += 1
                    continue
                item_id = r["id"]
                thash = audio_store.text_hash(text)
                for base, speed in kinds:
                    skind = audio_store.storage_kind(base, speed)
                    for voice in VOICES:
                        old_fp = audio_dir / (
                            f"{item_type}{item_id}_{skind}_{voice}.mp3"
                        )
                        new_fp = audio_dir / (
                            f"{item_type}{item_id}_{skind}_{voice}_{thash}.mp3"
                        )
                        if new_fp.exists():
                            already_new += 1
                            continue
                        if not old_fp.exists():
                            missing_old += 1
                            continue
                        if dry_run:
                            print(f"would rename {old_fp.name} -> {new_fp.name}")
                        else:
                            old_fp.rename(new_fp)
                        renamed += 1
    print("---")
    print(f"renamed: {renamed}")
    print(f"already on new scheme: {already_new}")
    print(f"no old file to migrate: {missing_old}")
    print(f"skipped (no text): {skipped_no_text}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    migrate(args.dry_run)
