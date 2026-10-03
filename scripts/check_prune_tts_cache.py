# ruff: noqa: E501
"""scripts/prune_tts_cache.py と ai.synthesize_speech(persist_cache=) の検査(2026-09-29)。

「完全に重複したものだけを消す」「それ以外は絶対に消さない」ことと、二重保存を止めるオプションが効くことを、
**使い捨ての一時DB**(DATA_DIRをここで上書きしてからappを読み込む)と偽のTTSクライアントで確かめる。
本番/ローカルの実データ・本物のOpenAIには触れない。

  .venv/bin/python scripts/check_prune_tts_cache.py     # 0=全部OK
"""

from __future__ import annotations

import atexit
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="check_prune_tts_")
atexit.register(shutil.rmtree, _TMP, ignore_errors=True)   # 実行ごとに/tmpへ残さない
os.environ["DATA_DIR"] = _TMP
os.environ["ALLOW_FRESH_DB"] = "1"
os.environ["OPENAI_API_KEY"] = "sk-test-not-a-real-key"
os.environ["MULTIUSER"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import prune_tts_cache as pr  # noqa: E402
from app.config import paths  # noqa: E402
from app.database import db, init_db  # noqa: E402
from app.routers.learn import _item_text  # noqa: E402
from app.services import ai, audio_store  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("  OK   " if cond else "  FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


init_db()
MODEL = ai.load_settings().tts_model
AUDIO = paths.data_dir / "audio"
CACHE = paths.data_dir / "tts_cache"
AUDIO.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
with db() as conn:
    IDS = [r["id"] for r in conn.execute(
        "SELECT id FROM words WHERE COALESCE(english,'') != '' ORDER BY id LIMIT 30")]
OLD = time.time() - 48 * 3600
_next = [0]


def text_of(i: int, kind: str = "word") -> str:
    with db() as conn:
        return _item_text(conn, "word", i, kind, True)


def cache_path(i: int, voice: str = "ash", kind: str = "word") -> Path:
    style = "native" if kind.endswith("_native") else "learn"
    return pr._cache_path_for(MODEL, voice, style, text_of(i, kind.replace("_native", "")))


def audio_path(i: int, voice: str = "ash", kind: str = "word") -> Path:
    t = text_of(i, kind.replace("_native", ""))
    return AUDIO / f"word{i}_{kind}_{voice}_{audio_store.text_hash(t)}.mp3"


def add_audio(i: int, data: bytes, voice: str = "ash", kind: str = "word") -> Path:
    t = text_of(i, kind.replace("_native", ""))
    with db() as conn:
        audio_store.put(conn, "word", i, kind, voice, t, data)
    return audio_path(i, voice, kind)


def add_cache(i: int, data: bytes, voice: str = "ash", kind: str = "word", old: bool = True) -> Path:
    p = cache_path(i, voice, kind)
    p.write_bytes(data)
    if old:
        os.utime(p, (OLD, OLD))
    return p


def take() -> list[int]:
    a = IDS[_next[0]]
    _next[0] += 1
    return a


DATA = b"\xff\xfbAUDIO" * 2000      # 約14KB
DATA2 = b"\xff\xfbOTHER" * 2000     # サイズは同じで中身が違う

print("== 1. 重複の判定(消してよいもの・消してはいけないもの)")
i_dup, i_dupn = take(), take()
p_dup_a = add_audio(i_dup, DATA);            p_dup_c = add_cache(i_dup, DATA)             # 完全重複(learn)
p_dupn_a = add_audio(i_dupn, DATA, kind="word_native"); p_dupn_c = add_cache(i_dupn, DATA, kind="word_native")  # 完全重複(native)
i_diffc, i_diffs, i_nocache, i_noaudio, i_new, i_other_voice = (take() for _ in range(6))
p_diffc_a = add_audio(i_diffc, DATA);        p_diffc_c = add_cache(i_diffc, DATA2)        # 同サイズ・中身違い
p_diffs_a = add_audio(i_diffs, DATA);        p_diffs_c = add_cache(i_diffs, DATA + b"x")  # サイズ違い
p_nocache_a = add_audio(i_nocache, DATA)                                                   # cache無し
p_noaudio_c = add_cache(i_noaudio, DATA)                                                   # audio無し(cacheだけ)
p_new_a = add_audio(i_new, DATA);            p_new_c = add_cache(i_new, DATA, old=False)  # 作成直後(24時間未満)
p_ov_a = add_audio(i_other_voice, DATA, voice="nova"); p_ov_c = add_cache(i_other_voice, DATA, voice="ash")  # 声が違う=別のキー(cacheは対象の別ファイル)
# 古い版の音声(ハッシュがテキストと合わない)とその想定cache
i_stale = take()
p_stale_a = AUDIO / f"word{i_stale}_word_ash_0123456789.mp3"; p_stale_a.write_bytes(DATA)
p_stale_c = add_cache(i_stale, DATA)
# 名前が想定外のファイル(触ってはいけない)
weird1 = CACHE / "notes.txt"; weird1.write_bytes(DATA)
weird2 = CACHE / ("z" * 32 + ".mp3"); weird2.write_bytes(DATA)     # 16進ではない
weird3 = CACHE / (("a" * 32) + ".mp3.lnk"); weird3.write_bytes(DATA)
audio_before = {p.name: p.read_bytes() for p in AUDIO.iterdir()}
cache_before = {p.name: p.read_bytes() for p in CACHE.iterdir()}

s = pr.run(execute=False, quiet=True)
check("dry-run は何も変更しない(audio・cacheとも)", {p.name: p.read_bytes() for p in AUDIO.iterdir()} == audio_before
      and {p.name: p.read_bytes() for p in CACHE.iterdir()} == cache_before)
check("dry-run で完全重複を2件と数える(learnとnative)", s.get("duplicates") == 2, str(s))

s = pr.run(execute=True, mode="delete", quiet=True)
check("delete: 完全重複の2件だけを処理", s.get("processed") == 2 and s.get("duplicates") == 2, str(s))
check("完全重複(learn)のcache側は消えた", not p_dup_c.exists())
check("完全重複(native)のcache側は消えた", not p_dupn_c.exists())
check("audio側は1件も変わっていない(消えていない・中身も同じ)", {p.name: p.read_bytes() for p in AUDIO.iterdir()} == audio_before)
check("同サイズで中身が違うcacheは残る", p_diffc_c.exists() and p_diffc_c.read_bytes() == DATA2)
check("サイズが違うcacheは残る", p_diffs_c.exists())
check("cacheだけ(audio無し)は残る", p_noaudio_c.exists())
check("作成直後(24時間未満)のcacheは残る", p_new_c.exists())
check("声が違う(別キー)cacheは残る", p_ov_c.exists())
check("古い版の音声に対応するcacheは残る(対象外)", p_stale_c.exists())
check("名前が想定外のファイルは全て残る", weird1.exists() and weird2.exists() and weird3.exists())
check("audio側の見送り件数が数えられている(古い版=1)", s.get("skip_audio_not_current") == 1, str(s))
check("見送りの内訳: 新しすぎる1・サイズ違い1・中身違い1", s.get("skip_too_new") == 1 and s.get("skip_different_size") == 1 and s.get("skip_different_content") == 1, str(s))
s2 = pr.run(execute=True, mode="delete", quiet=True)
check("2回目は何も処理しない(冪等)", s2.get("processed", 0) == 0 and s2.get("duplicates", 0) == 0, str(s2))

print("== 2. 作成から時間がたてば対象になる/--limit")
os.utime(p_new_c, (OLD, OLD))
s = pr.run(execute=True, mode="delete", min_age_hours=24, quiet=True)
check("24時間たった作成直後のものも、完全一致なら削除される", s.get("processed") == 1 and not p_new_c.exists(), str(s))
a, b = take(), take()
add_audio(a, DATA); pa = add_cache(a, DATA); add_audio(b, DATA); pb = add_cache(b, DATA)
s = pr.run(execute=True, mode="delete", limit=1, quiet=True)
check("--limit 1 は1件だけ処理して止まる", s.get("processed") == 1 and s.get("stopped_by_limit") == 1 and (pa.exists() != pb.exists()), str(s))
s = pr.run(execute=True, mode="delete", quiet=True)
check("続けて実行すると残りを処理する", not pa.exists() and not pb.exists(), str(s))

print("== 3. ハードリンクモード(削除せず共有)")
h = take()
p_ha = add_audio(h, DATA); p_hc = add_cache(h, DATA)
s = pr.run(execute=True, mode="hardlink", quiet=True)
check("cache側が audio と同じ実体(inode)になり、中身も同じ", os.path.samefile(p_ha, p_hc) and p_hc.read_bytes() == DATA, str(s))
check("共有後もcacheファイルは存在する(何も失っていない)", p_hc.exists() and p_ha.exists())
s = pr.run(execute=True, mode="hardlink", quiet=True)
check("2回目は「共有済み」として数え、何もしない", s.get("already_shared", 0) >= 1 and s.get("processed", 0) == 0, str(s))
check("一時ファイル(.lnk)が残っていない", not list(CACHE.glob("*.lnk.lnk")) and not any(p.name.endswith(".mp3.lnk") and p.name != weird3.name for p in CACHE.iterdir()))

print("== 4. 二重保存を止めるオプション(偽のTTSクライアント)")
calls = [0]


class _Speech:
    def create(self, **kw):
        calls[0] += 1

        class R:
            content = b"\x00" * 20000

            def read(self):
                return self.content
        return R()


class _Client:
    class audio:  # noqa: N801
        speech = _Speech()


ai._client = lambda: (_Client(), ai.load_settings())  # type: ignore[assignment]
t1, t2 = "persist test sentence one", "persist test sentence two"
a1, e1 = ai.synthesize_speech(t1, "nova", rate_limit=False)
c1 = ai._tts_cache_path(MODEL, "nova", t1, ai._tts_instructions("learn"))
check("既定(persist_cache=True)は従来どおりtts_cacheに保存する", e1 is None and a1 and c1.exists())
a2, e2 = ai.synthesize_speech(t2, "nova", rate_limit=False, persist_cache=False)
c2 = ai._tts_cache_path(MODEL, "nova", t2, ai._tts_instructions("learn"))
check("persist_cache=False は音声を返すが tts_cache に保存しない", e2 is None and a2 and not c2.exists())
n = calls[0]
a3, e3 = ai.synthesize_speech(t1, "nova", rate_limit=False, persist_cache=False)
check("保存済みのキャッシュは persist_cache=False でも読み出す(APIを呼ばない)", e3 is None and a3 == a1 and calls[0] == n)

print("== 5. 保存失敗時の受け皿(2026-10-04・独立レビューMEDIUM-1): audio_storeに書けないときだけtts_cacheに残す")
import stat  # noqa: E402
from app.config import paths as _paths  # noqa: E402
from app.services import audio_store as _astore  # noqa: E402
from app.database import db as _db  # noqa: E402

_adir = _paths.data_dir / "audio"
_adir.mkdir(parents=True, exist_ok=True)
t3 = "fallback test sentence three"
with _db() as _conn:
    ok_put = _astore.put(_conn, "word", 999991, "word", "nova", t3, b"\x01" * 20000)
    check("audio_store.put: 書けたらTrue", ok_put is True and (_astore.get(_conn, "word", 999991, "word", "nova", t3) is not None))
    _adir.chmod(stat.S_IRUSR | stat.S_IXUSR)            # 読み取り専用にして保存失敗を再現
    try:
        bad_put = _astore.put(_conn, "word", 999992, "word", "nova", t3, b"\x01" * 20000)
    finally:
        _adir.chmod(stat.S_IRWXU)
    check("audio_store.put: 書けなければFalse(例外にしない・警告ログ)", bad_put is False)
    check("書けなかった音声はaudio_storeに無い", _astore.get(_conn, "word", 999992, "word", "nova", t3) is None)
c3 = ai._tts_cache_path(MODEL, "nova", t3, ai._tts_instructions("learn"))
check("save_tts_cache前はtts_cacheに無い", not c3.exists())
check("save_tts_cache: tts_cacheに保存してTrue", ai.save_tts_cache(t3, "nova", b"\x02" * 20000) is True and c3.exists())
n = calls[0]
a4, e4 = ai.synthesize_speech(t3, "nova", rate_limit=False, persist_cache=False)
check("受け皿に残した音声は次の再生でAPIを呼ばず返る(合成費の再発生なし)", e4 is None and a4 == b"\x02" * 20000 and calls[0] == n)

print()
if FAILS:
    print(f"❌ 失敗 {len(FAILS)} 件: " + ", ".join(FAILS))
    raise SystemExit(1)
print("✅ すべて成功")
