"""録画結果(フレーム列+音声イベント)を mp4(H.264 + AAC)に組む。

  1. フレーム(JPEG+タイムスタンプ)→ 一定fps・yuv420p の H.264
     (concat demuxer で「各フレームをその秒数だけ表示」→ fpsフィルタで一定化)
  2. 音声イベント(実際に鳴ったmp3・開始時刻・再生速度・停止位置)→ 映像の
     時刻に adelay で置いて amix → loudnorm(2パス・-16 LUFS前後)
  3. 映像 + 音声を mux(-movflags +faststart・AAC 44.1kHz)

iPhone Safari で再生できる設定: -profile:v high -pix_fmt yuv420p
+ AAC-LC(-ar 44100)+ faststart。
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from .stage import AudioEvent, Recording

MIN_AUDIO_BYTES = 8 * 1024   # これ未満の音声は不良(0.36秒の無内容音)の疑い


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if p.returncode != 0:
        raise RuntimeError(
            f"コマンド失敗: {' '.join(cmd[:6])} ...\n{p.stderr[-1500:]}")
    return p


def _build_video(rec: Recording, work: Path, out: Path, *, width: int,
                 height: int, fps: int, crf: int, preset: str) -> None:
    frames = sorted(rec.frames, key=lambda f: f.ts)
    t0, t_end = rec.t0, rec.t0 + rec.duration
    before = [f for f in frames if f.ts <= t0]
    seq = []   # (開始時刻, frame)
    seq.append((t0, before[-1] if before else frames[0]))
    for f in frames:
        if t0 < f.ts < t_end:
            seq.append((f.ts, f))
    fdir = work / "frames"
    fdir.mkdir(parents=True, exist_ok=True)
    lines = ["ffconcat version 1.0"]
    for i, (ts, f) in enumerate(seq):
        nxt = seq[i + 1][0] if i + 1 < len(seq) else t_end
        d = max(0.001, nxt - ts)
        name = f"f{i:05d}.jpg"
        (fdir / name).write_bytes(f.data)
        lines.append(f"file 'frames/{name}'")
        lines.append(f"duration {d:.4f}")
    lines.append(f"file 'frames/f{len(seq) - 1:05d}.jpg'")   # 最終行の重複(仕様)
    (work / "frames.ffconcat").write_text("\n".join(lines) + "\n")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(work / "frames.ffconcat"),
         # スクリーンキャストのJPEGは full range(yuvj) なので、iPhone等が
         # 期待する limited range・BT.709 の yuv420p に明示変換する。
         "-vf", (f"fps={fps},scale={width}:{height}:flags=lanczos:"
                 "in_range=pc:in_color_matrix=bt601:"
                 "out_range=tv:out_color_matrix=bt709,format=yuv420p"),
         "-t", f"{rec.duration:.3f}",
         "-color_range", "tv", "-colorspace", "bt709",
         "-color_primaries", "bt709", "-color_trc", "bt709",
         "-c:v", "libx264", "-profile:v", "high", "-level", "4.0",
         "-preset", preset, "-crf", str(crf), "-r", str(fps),
         "-movflags", "+faststart", "-an", str(out)])


def _plays(rec: Recording) -> list[dict]:
    """音声イベントを「1回の再生」ごとにまとめる。"""
    evs = sorted(rec.audio_events, key=lambda e: e.t)
    plays = []
    for i, e in enumerate(evs):
        if e.ev != "playing":
            continue
        if e.src not in rec.audio_blobs:
            raise RuntimeError("再生された音声のバイト列を取得できていません")
        end = next((x for x in evs[i + 1:]
                    if x.src == e.src and x.ev in ("pause", "ended")), None)
        pos = end.pos if end else e.dur
        natural = (not end) or (e.dur and pos >= e.dur - 0.05)
        plays.append({
            "src": e.src, "t": e.t - rec.t0, "rate": e.rate or 1.0,
            "dur": e.dur, "pos": None if natural else pos,
        })
    return plays


def _build_audio(rec: Recording, work: Path, out_wav: Path,
                 target_lufs: float) -> list[dict]:
    plays = _plays(rec)
    if not plays:
        return []
    files: dict[str, Path] = {}
    for src, blob in rec.audio_blobs.items():
        if len(blob) < MIN_AUDIO_BYTES:
            raise RuntimeError(
                f"音声が小さすぎます({len(blob)}バイト<8KB)。不良の疑い")
        p = work / f"a{len(files)}.mp3"
        p.write_bytes(blob)
        files[src] = p
    cmd = ["ffmpeg", "-y", "-v", "error"]
    used = []
    for pl in plays:
        cmd += ["-i", str(files[pl["src"]])]
        used.append(pl)
    parts, labels = [], []
    for i, pl in enumerate(used):
        ms = max(0, round(pl["t"] * 1000))
        chain = f"[{i}:a]"
        if pl["pos"] is not None:
            chain += f"atrim=end={pl['pos']:.3f},asetpts=PTS-STARTPTS,"
        chain += (f"aformat=sample_rates=44100:channel_layouts=mono,"
                  f"atempo={pl['rate']:.4f},adelay={ms}|{ms}[a{i}]")
        parts.append(chain)
        labels.append(f"[a{i}]")
    mix = "".join(labels) + (
        f"amix=inputs={len(used)}:duration=longest:normalize=0,"
        f"apad=whole_dur={rec.duration:.3f}[mix]")
    raw = work / "audio_raw.wav"
    # (apad の後ろに atrim を置くと出力が壊れるので、長さは -t で切る)
    run(cmd + ["-filter_complex", ";".join(parts + [mix]), "-map", "[mix]",
               "-t", f"{rec.duration:.3f}", "-ar", "44100", "-ac", "1",
               str(raw)])
    # loudnorm 2パス(測定→線形適用)
    tp = -1.5
    m = run(["ffmpeg", "-y", "-v", "info", "-i", str(raw), "-af",
             f"loudnorm=I={target_lufs}:TP={tp}:LRA=11:print_format=json",
             "-f", "null", "-"]).stderr
    js = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", m, re.S).group(0))
    af = (f"loudnorm=I={target_lufs}:TP={tp}:LRA=11:"
          f"measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:"
          f"offset={js['target_offset']}:linear=true")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af", af,
         "-ar", "44100", "-ac", "1", str(out_wav)])
    return used


def encode(rec: Recording, out_mp4: Path, work: Path, *, width: int = 720,
           height: int = 1280, fps: int = 30, crf: int = 20,
           preset: str = "slow", target_lufs: float = -16.0) -> dict:
    """Recording → out_mp4。戻り値は検証・報告用の情報。"""
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    vid = work / "video_only.mp4"
    _build_video(rec, work, vid, width=width, height=height, fps=fps,
                 crf=crf, preset=preset)
    wav = work / "audio_norm.wav"
    plays = _build_audio(rec, work, wav, target_lufs)
    if plays:
        run(["ffmpeg", "-y", "-v", "error", "-i", str(vid), "-i", str(wav),
             "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-ar", "44100",
             "-ac", "1", "-movflags", "+faststart",
             "-t", f"{rec.duration:.3f}", str(out_mp4)])
    else:
        shutil.copy(vid, out_mp4)
    return {"plays": plays, "taps": rec.taps, "frames": len(rec.frames)}
