#!/usr/bin/env python3
"""機能紹介動画とポスターを1コマンドで作り直す。

  ①一時DATA_DIR+アプリ起動 ②撮影(Playwright・CDPスクリーンキャスト)
  ③音の合成とエンコード ④ポスター生成 ⑤検証(ffprobe・音量・容量)

使い方(リポジトリのルートから):
  .venv/bin/python scripts/videos/build.py                 # 全本
  .venv/bin/python scripts/videos/build.py --only phrase_polite
  .venv/bin/python scripts/videos/build.py --list
  .venv/bin/python scripts/videos/build.py --only phrase_polite --frames-dir /tmp/frames

出力: static/video/<name>.mp4 / static/video/posters/<name>.jpg
本番・本体のdata/には触れない(一時ディレクトリで完結)。
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import shutil
import signal
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib import encode as enc            # noqa: E402
from lib import poster as post           # noqa: E402
from lib import verify as ver            # noqa: E402
from lib.appserver import REPO_ROOT, AppServer   # noqa: E402
from lib.stage import Stage              # noqa: E402

# 作成順(ここに足す)。各モジュールは NAME/TITLE/DURATION と
# prepare()/perform()/poster_body() を持つ(scenarios/phrase_polite.py 参照)。
SCENARIOS = ["flash_word", "phrase_polite", "crossword"]

VIDEO_DIR = REPO_ROOT / "static" / "video"
POSTER_DIR = VIDEO_DIR / "posters"


async def build_one(mod, app: AppServer, args) -> dict:
    name = mod.NAME
    print(f"\n=== {name}: {mod.TITLE} ===", flush=True)
    ctx = {"data_dir": app.data_dir}
    stage = Stage(app.url, hide=getattr(mod, "HIDE", None),
                  extra_css=getattr(mod, "EXTRA_CSS", ""))
    if args.poster_only:   # 撮影・エンコードを省き、ポスターだけ作り直す
        try:
            await stage.open()
            await mod.prepare(stage, ctx)
        finally:
            await stage.close()
        poster_path = POSTER_DIR / f"{name}.jpg"
        r = await post.render_poster(
            mod.poster_body(ctx), poster_path, css=getattr(mod, "POSTER_CSS", ""))
        print(f"  ポスター: {r['bytes']:,} bytes (q={r['quality']}) {r['path']}")
        return {"name": name, "ok": True, "result": r}
    try:
        await stage.open()
        await mod.prepare(stage, ctx)
        print("  撮影中…", flush=True)
        await stage.start_recording()
        await mod.perform(stage, ctx)
        rec = await stage.finish(mod.DURATION)
    finally:
        await stage.close()
    print(f"  フレーム{len(rec.frames)}枚・タップ{rec.taps}"
          f"・音声再生{sum(1 for e in rec.audio_events if e.ev == 'playing')}回",
          flush=True)

    out_mp4 = VIDEO_DIR / f"{name}.mp4"
    work = Path(tempfile.mkdtemp(prefix=f"vid_{name}_"))
    print("  エンコード中…", flush=True)
    try:
        info = enc.encode(rec, out_mp4, work / "enc", width=args.width,
                          height=args.height, fps=args.fps, crf=args.crf)
    finally:
        if not args.keep_temp:
            shutil.rmtree(work, ignore_errors=True)

    poster_path = POSTER_DIR / f"{name}.jpg"
    if not args.no_poster:
        print("  ポスター生成中…", flush=True)
        css = getattr(mod, "POSTER_CSS", "")
        await post.render_poster(mod.poster_body(ctx), poster_path, css=css)

    result, problems = ver.check(
        out_mp4, poster_path if not args.no_poster else None)
    result["plays"] = info["plays"]
    result["taps"] = info["taps"]
    if args.frames_dir:
        d = Path(args.frames_dir) / name
        n = len(ver.dump_frames(out_mp4, d, every=1.0))
        sheet = ver.contact_sheet(d, d / "sheet.png")
        print(f"  確認用フレーム{n}枚 -> {d}(一覧: {sheet})")
    _report(name, result, problems)
    return {"name": name, "ok": not problems, "result": result}


def _report(name: str, r: dict, problems: list[str]) -> None:
    print(f"  動画: {r['bytes']:,} bytes / {r['duration']:.2f}s / {r['size']} "
          f"/ {r['vcodec']}({r['profile']},{r['pix_fmt']}) {r['fps']}fps "
          f"/ 音声={r['acodec']}({r['sample_rate']}Hz,{r['channels']}ch) "
          f"/ faststart={r['faststart']}")
    ld = r.get("loudness")
    if ld:
        print(f"  音量: {ld['lufs']} LUFS / LRA {ld['lra']} / "
              f"TP {ld['true_peak_dbfs']} dBFS")
    if "poster_bytes" in r:
        print(f"  ポスター: {r['poster_bytes']:,} bytes")
    for p in r.get("plays", []):
        print(f"  再生: t={p['t']:.2f}s rate={p['rate']:.2f} dur={p['dur']:.2f}s"
              f" trunc={p['pos']}")
    taps = r.get("taps", [])
    plays = r.get("plays", [])
    if taps and plays:
        for pl in plays:   # 直前のタップからの遅れ = 音と操作のずれ
            prev = [t for t in taps if t <= pl["t"] + 0.01]
            if prev:
                print(f"  音のずれ: タップ{prev[-1]:.2f}s -> 音{pl['t']:.2f}s "
                      f"(遅れ {pl['t'] - prev[-1]:.3f}s)")
    silent = ver.silences(VIDEO_DIR / f"{name}.mp4") if r["acodec"] else []
    if silent:
        print("  無音区間(参考): " + ", ".join(
            f"{a:.1f}-{('%.1f' % b) if b else '末'}s" for a, b in silent))
    print("  検証: " + ("OK" if not problems else "NG"))
    for p in problems:
        print("   - " + p)


async def amain(args) -> int:
    names = args.only or SCENARIOS
    unknown = [n for n in names if n not in SCENARIOS]
    if unknown:
        print(f"未知の動画名: {unknown}(--list で一覧)")
        return 2
    mods = [importlib.import_module(f"scenarios.{n}") for n in names]
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    POSTER_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    with AppServer(keep=args.keep_temp) as app:
        print(f"アプリ起動: {app.url}(一時DATA_DIR={app.data_dir})", flush=True)
        for mod in mods:
            results.append(await build_one(mod, app, args))
    bad = [r["name"] for r in results if not r["ok"]]
    print("\n完了: " + ", ".join(r["name"] for r in results)
          + (f"  / 要確認: {bad}" if bad else "  / すべて検証OK"))
    return 1 if bad else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--only", nargs="+", metavar="NAME", help="この動画だけ作る")
    ap.add_argument("--list", action="store_true", help="動画名の一覧")
    ap.add_argument("--keep-temp", action="store_true",
                    help="一時DATA_DIRを削除しない(デバッグ用)")
    ap.add_argument("--no-poster", action="store_true")
    ap.add_argument("--poster-only", action="store_true",
                    help="ポスターだけ作り直す(撮影・エンコードを省略)")
    ap.add_argument("--frames-dir", help="確認用に1秒おきのPNGを書き出す先")
    ap.add_argument("--width", type=int, default=720)
    ap.add_argument("--height", type=int, default=1280)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--crf", type=int, default=20)
    args = ap.parse_args()
    if args.list:
        for n in SCENARIOS:
            m = importlib.import_module(f"scenarios.{n}")
            print(f"{n}\t{m.TITLE}\t{m.DURATION}s")
        return
    # kill/Ctrl-C されても with 句の後始末(uvicorn停止・一時dir削除)を走らせる
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    sys.exit(asyncio.run(amain(args)))


if __name__ == "__main__":
    main()
