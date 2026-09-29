"""tts_cache のうち、audio(audio_store)に保存済みの音声と**完全に同じ内容**の重複だけを整理する
(2026-09-29 オーナー決定・ver1.5.8)。

背景: 単語/フレーズ/例文の音声は `data/audio/`(audio_store)に永続保存される。ところが音声を作る関数
(`ai.synthesize_speech`)は同じ音声を `data/tts_cache/` にも書いていたため、二重に保存されていた
(実測 2026-09-29: tts_cache 81,668件5.73GBのうち35,068件2.78GBが audio と完全重複・作成後に再利用された
実績は1%未満)。二重保存は ver1.5.8 で止めた(`persist_cache=False`)。このスクリプトは、すでにある重複を消す。

**「確信が持てたものだけ」削除する条件(すべて満たしたものだけ)**:
  1. audio の1ファイルごとに、対応する tts_cache のファイル名を**計算で**求める(キーの決まり方はアプリと同じ
     `ai._tts_cache_path`。モデル・声・話し方・読み上げテキストのハッシュ)。
  2. その audio ファイルが**現行のテキストに対する有効な音声**である(IDが指す語/例文のテキストのハッシュと一致)。
  3. tts_cache 側のファイルが存在し、**サイズが同じで、中身がバイト単位で完全に一致**する。
  4. tts_cache 側の更新から `--min-age-hours`(既定24時間)以上たっている(書き込み直後のものを触らない)。
  → 1つでも欠けたら何もしない。audio 側は一切変更しない。tts_cache の名前が「32桁の16進.mp3」以外のファイルも触らない。

モード(既定は dry-run=件数の確認だけで何も変更しない。`--execute` を付けたときだけ実行):
  --mode delete    tts_cache 側の重複ファイルを削除する(既定・オーナー決定)
  --mode hardlink  削除せず、audio と同じ実体を共有(ハードリンク)にする(同じ容量の節約・何も失わない)

使い方(VPS上、eigo-appコンテナの中で・低優先度で):
  docker exec eigo-app nice -n 19 python3 scripts/prune_tts_cache.py                    # 件数と容量の確認のみ
  docker exec eigo-app nice -n 19 python3 scripts/prune_tts_cache.py --execute --limit 5000   # 削除(1回最大5000件・繰り返し実行できる)
"""

from __future__ import annotations

import argparse
import collections
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_settings, paths  # noqa: E402
from app.database import db, init_db  # noqa: E402
from app.services import ai, audio_store, tts_hints  # noqa: E402

# audio_store のファイル名: {type}{id}_{kind}[_native]_{voice}_{hash10}.mp3
_AUDIO_RE = re.compile(
    r"^(word|phrase)(\d+)_(word|example|phrase)(_native)?_([A-Za-z]+)_([0-9a-f]{10})\.mp3$")
# tts_cache のファイル名: sha256の先頭32桁.mp3(これ以外は触らない)
_CACHE_RE = re.compile(r"^[0-9a-f]{32}\.mp3$")
_CHUNK = 1 << 20


def same_bytes(a: Path, b: Path) -> bool:
    """2つのファイルがバイト単位で完全に同じか(サイズ→中身の順に比較)。"""
    if a.stat().st_size != b.stat().st_size:
        return False
    with open(a, "rb") as fa, open(b, "rb") as fb:
        while True:
            x, y = fa.read(_CHUNK), fb.read(_CHUNK)
            if x != y:
                return False
            if not x:
                return True


def _cache_path_for(model: str, voice: str, style: str, text: str) -> Path:
    """アプリ(`ai.synthesize_speech`)と同じ規則で tts_cache のパスを求める。"""
    speak = tts_hints.spoken_text(text[:4000])
    return ai._tts_cache_path(model, voice, speak, ai._tts_instructions(style))


def run(execute: bool = False, mode: str = "delete", min_age_hours: float = 24.0,
        limit: int = 0, quiet: bool = False) -> dict:
    """走査して集計を返す(execute=Trueなら実際に削除/共有化する)。"""
    from app.routers.learn import _item_text  # 重い読み込みなので使うときだけ

    if mode not in ("delete", "hardlink"):
        raise ValueError("mode は delete か hardlink")
    model = load_settings().tts_model
    audio_dir = paths.data_dir / "audio"
    cache_dir = paths.data_dir / "tts_cache"
    stats: collections.Counter = collections.Counter()
    now = time.time()
    if not audio_dir.is_dir() or not cache_dir.is_dir():
        return dict(stats)
    with db() as conn:
        for e in os.scandir(audio_dir):
            m = _AUDIO_RE.match(e.name)
            if not e.is_file() or not m:
                continue
            stats["audio_files"] += 1
            typ, iid, base, native, voice, thash = m.groups()
            text = _item_text(conn, typ, int(iid), base, True)
            if not text or audio_store.text_hash(text) != thash:
                stats["skip_audio_not_current"] += 1      # 古い版/元が無い音声は対象外
                continue
            cp = _cache_path_for(model, voice, "native" if native else "learn", text)
            if cp.parent != cache_dir or not _CACHE_RE.match(cp.name):
                stats["skip_unexpected_path"] += 1
                continue
            try:
                cst = cp.stat()
            except FileNotFoundError:
                stats["no_cache_twin"] += 1
                continue
            ap = Path(e.path)
            if os.path.samestat(cst, e.stat()):
                stats["already_shared"] += 1              # 既にハードリンクで共有済み
                continue
            if (now - cst.st_mtime) < min_age_hours * 3600:
                stats["skip_too_new"] += 1
                continue
            if cst.st_size != e.stat().st_size:
                stats["skip_different_size"] += 1
                continue
            try:
                same = same_bytes(cp, ap)
            except OSError:
                stats["skip_read_error"] += 1
                continue
            if not same:
                stats["skip_different_content"] += 1
                continue
            # ここまで来たものだけが「完全重複」
            stats["duplicates"] += 1
            stats["duplicate_bytes"] += cst.st_size
            if not execute:
                continue
            try:
                if mode == "delete":
                    os.unlink(cp)
                else:  # hardlink: 一時名で作ってから置き換える(途中で失敗しても元のファイルは残る)
                    tmp = cp.with_name(cp.name + ".lnk")
                    if tmp.exists():
                        tmp.unlink()
                    os.link(ap, tmp)
                    os.replace(tmp, cp)
                stats["processed"] += 1
                stats["processed_bytes"] += cst.st_size
            except OSError as ex:
                stats["errors"] += 1
                if not quiet:
                    print(f"  失敗: {type(ex).__name__}")
            if limit and stats["processed"] >= limit:
                stats["stopped_by_limit"] = 1
                break
    return dict(stats)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--execute", action="store_true", help="指定しない場合は件数の確認だけ(dry-run)")
    p.add_argument("--mode", choices=("delete", "hardlink"), default="delete")
    p.add_argument("--min-age-hours", type=float, default=24.0,
                   help="tts_cache側の更新からこの時間以上たったものだけ対象(既定24)")
    p.add_argument("--limit", type=int, default=0, help="1回に処理する最大件数(0=無制限)")
    a = p.parse_args()
    init_db()
    s = run(execute=a.execute, mode=a.mode, min_age_hours=a.min_age_hours, limit=a.limit)
    gb = lambda b: f"{b / 1e9:.2f}GB"  # noqa: E731
    print(f"audio の音声ファイル: {s.get('audio_files', 0)}件")
    print(f"  うち現行でない(古い版・元なし): {s.get('skip_audio_not_current', 0)}件(対象外)")
    print(f"  tts_cache に対応なし: {s.get('no_cache_twin', 0)}件 / 既に共有済み: {s.get('already_shared', 0)}件")
    print(f"  見送り: 新しすぎる {s.get('skip_too_new', 0)} / サイズ違い {s.get('skip_different_size', 0)}"
          f" / 中身が違う {s.get('skip_different_content', 0)} / 読めない {s.get('skip_read_error', 0)}")
    print(f"完全重複(サイズ・中身が完全一致): {s.get('duplicates', 0)}件 {gb(s.get('duplicate_bytes', 0))}")
    if not a.execute:
        print("dry-run です。何も変更していません。実行するには --execute を付けてください。")
        return 0
    verb = "削除" if a.mode == "delete" else "ハードリンク化"
    print(f"{verb}: {s.get('processed', 0)}件 {gb(s.get('processed_bytes', 0))}"
          f" / 失敗 {s.get('errors', 0)}件" + (" / 上限で中断(再実行で続きを処理)" if s.get("stopped_by_limit") else ""))
    return 1 if s.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
