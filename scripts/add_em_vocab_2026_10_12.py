# ruff: noqa: E501
"""電磁気・電力(science-lab連動)の語彙とフレーズを追加する(2026-10-12・B28)。

別プロジェクト`science-lab`(電磁気の教材サイト)の教材ページに出てくる概念
(ベクトル解析のgrad/div/rot/ラプラシアン・マクスウェル・電気力線/等電位線・発電機/三相/
変圧器/モーター・送電線路・アンテナ・雷/避雷針・半導体 等)を英語語彙・フレーズにする。
本文(語144語・フレーズ40件)は`scripts/add_em_vocab_2026_10_12.json`に置く
(`words`: english/japanese/part_of_speech/domain/level/example/detail、
 `phrases`: english/japanese/scene/level/detail)。

- 分野は既存の`数学`/`物理`/`電気電子`/`半導体`、フレーズ場面は`物理学の英語`/`電気・電子`に入れる(新設しない)。
- `words.japanese`は短い訳語(説明文は`detail`)。
- 重複判定: 語は英語綴り(小文字)の完全一致、フレーズは英文(小文字・前後空白除去)の完全一致でスキップ。
- DB安全装置(2026-09-26・CLAUDE.md「本番DBの主データベース」ルール): dry-runが既定・`--apply`で書き込み・
  書き込み前にcontent DBをSQLiteバックアップAPIで複製・前後で主要テーブルの件数を比較・
  `--rollback <inserted_ids JSON>`で今回挿入した行だけ削除できる。**ファイル単位で本番DBを上書きしない**
  (このスクリプトは`INSERT`のみ。本番ではコンテナ内で実行する)。

使い方:
  python scripts/add_em_vocab_2026_10_12.py              # dry-run(何も書かない)
  python scripts/add_em_vocab_2026_10_12.py --apply
  python scripts/add_em_vocab_2026_10_12.py --data /tmp/em/add_em_vocab_2026_10_12.json   # 本番: 稼働中コンテナへ一時コピーしたJSONを使う
  python scripts/add_em_vocab_2026_10_12.py --rollback <data/script_backups/..._inserted_ids.json>

仕上げ(別手順): 音声は`scripts/build_audio.py`(新規分だけが未生成として拾われる)。
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _db_safety import default_backup_dir, key_counts, print_counts, same_counts  # noqa: E402
from app.config import paths  # noqa: E402
from app.database import db  # noqa: E402

DATA_JSON = Path(__file__).resolve().parent / "add_em_vocab_2026_10_12.json"
ALLOWED_DOMAINS = {"数学", "物理", "電気電子", "半導体"}
ALLOWED_SCENES = {"物理学の英語", "電気・電子"}


def _load(path: Path = DATA_JSON) -> tuple[list[dict], list[dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    words, phrases = data["words"], data["phrases"]
    for w in words:
        assert w["domain"] in ALLOWED_DOMAINS, w["english"]
        assert w["japanese"] and "。" not in w["japanese"], w["english"]
        assert isinstance(w["detail"], dict), w["english"]
    for p in phrases:
        assert p["scene"] in ALLOWED_SCENES, p["english"]
        assert isinstance(p["detail"], dict), p["english"]
    return words, phrases


def _backup_content_db(backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    dst = backup_dir / f"content_before_em_vocab_{time.strftime('%Y%m%d_%H%M%S')}.db"
    src = sqlite3.connect(f"file:{paths.content_db_file}?mode=ro", uri=True)
    out = sqlite3.connect(dst)
    with out:
        src.backup(out)
    out.close()
    src.close()
    return dst


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="実際に書き込む(既定はdry-run)")
    ap.add_argument("--rollback", metavar="INSERTED_IDS_JSON")
    ap.add_argument("--backup-dir", default=None, help="既定 DATA_DIR/script_backups")
    ap.add_argument("--data", default=str(DATA_JSON), help="本文JSON(既定=このスクリプトの隣)。本番で一時コピーを使うとき用")
    args = ap.parse_args()
    backup_dir = Path(args.backup_dir) if args.backup_dir else default_backup_dir()

    if args.rollback:
        ids = json.loads(Path(args.rollback).read_text(encoding="utf-8"))
        with db() as conn:
            before = key_counts(conn)
            for wid, eng in ids["words"]:
                conn.execute("DELETE FROM words WHERE id = ? AND english = ?", (wid, eng))
            for pid, eng in ids["phrases"]:
                conn.execute("DELETE FROM phrases WHERE id = ? AND english = ?", (pid, eng))
            conn.commit()
            print_counts("before", before)
            print_counts("after", key_counts(conn))
        return 0

    words, phrases = _load(Path(args.data))
    with db() as conn:
        before = key_counts(conn)
        print_counts("before", before)
        ex_w = {r["english"].lower() for r in conn.execute("SELECT english FROM words").fetchall()}
        ex_p = {r["english"].lower().strip() for r in conn.execute("SELECT english FROM phrases").fetchall()}
        new_w = [w for w in words if w["english"].lower() not in ex_w]
        new_p = [p for p in phrases if p["english"].lower().strip() not in ex_p]
        print(f"words: 追加予定 {len(new_w)} / 重複スキップ {len(words) - len(new_w)} / 原稿 {len(words)}")
        print(f"phrases: 追加予定 {len(new_p)} / 重複スキップ {len(phrases) - len(new_p)} / 原稿 {len(phrases)}")
        if not args.apply:
            print("dry-run のため書き込みません。--apply で実行。")
            return 0

        bk = _backup_content_db(backup_dir)
        print(f"content DB バックアップ: {bk}")
        ins_w: list[list] = []
        ins_p: list[list] = []
        for w in new_w:
            cur = conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, example, domain, level, detail) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (w["english"], w["japanese"], w["part_of_speech"], w["example"], w["domain"], w["level"],
                 json.dumps(w["detail"], ensure_ascii=False)),
            )
            ins_w.append([cur.lastrowid, w["english"]])
        for p in new_p:
            cur = conn.execute(
                "INSERT INTO phrases (english, japanese, scene, level, detail) VALUES (?, ?, ?, ?, ?)",
                (p["english"], p["japanese"], p["scene"], str(p["level"]),
                 json.dumps(p["detail"], ensure_ascii=False)),
            )
            ins_p.append([cur.lastrowid, p["english"]])
        conn.commit()
        after = key_counts(conn)
        print_counts("after", after)
        exp = dict(before)
        exp["words"] += len(ins_w)
        exp["phrases"] += len(ins_p)
        ok = same_counts(exp, after)
        ids_file = backup_dir / f"em_vocab_inserted_ids_{time.strftime('%Y%m%d_%H%M%S')}.json"
        ids_file.write_text(json.dumps({"words": ins_w, "phrases": ins_p}, ensure_ascii=False), encoding="utf-8")
        print(f"挿入した行のID: {ids_file}  (ロールバック: --rollback {ids_file})")
        print("件数チェック:", "OK(words/phrasesだけが増え、他の表は不変)" if ok else "NG ← 想定外。直ちに調査")
        return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
