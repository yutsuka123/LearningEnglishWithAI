"""完成した mp4 / ポスターの検証(ffprobe・ラウドネス・無音・faststart)と、
目視確認用のフレーム書き出し。"""

from __future__ import annotations

import json
import re
import struct
import subprocess
from pathlib import Path

LIMITS = {
    "max_video_bytes": 2_500_000,
    "min_duration": 15.0,
    "max_duration": 20.0,
    "max_poster_bytes": 60_000,
    "lufs_range": (-19.0, -13.0),
}


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def faststart(path: Path) -> bool:
    """moov が mdat より前にあるか(先頭からのボックス走査)。"""
    with open(path, "rb") as f:
        while True:
            head = f.read(8)
            if len(head) < 8:
                return False
            size, typ = struct.unpack(">I4s", head)
            if typ == b"moov":
                return True
            if typ == b"mdat":
                return False
            if size == 1:
                size = struct.unpack(">Q", f.read(8))[0]
                f.seek(size - 16, 1)
            elif size == 0:
                return False
            else:
                f.seek(size - 8, 1)


def probe(path: Path) -> dict:
    p = _run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format",
              "-show_streams", str(path)])
    j = json.loads(p.stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    num, den = (v.get("avg_frame_rate", "0/1").split("/") + ["1"])[:2]
    return {
        "bytes": int(j["format"]["size"]),
        "duration": float(j["format"]["duration"]),
        "vcodec": v.get("codec_name"), "profile": v.get("profile"),
        "pix_fmt": v.get("pix_fmt"), "size": f"{v.get('width')}x{v.get('height')}",
        "fps": round(int(num) / max(1, int(den)), 2),
        "acodec": a.get("codec_name") if a else None,
        "sample_rate": a.get("sample_rate") if a else None,
        "channels": a.get("channels") if a else None,
        "faststart": faststart(path),
    }


def loudness(path: Path) -> dict | None:
    """EBU R128 の統合ラウドネス(LUFS)・LRA・True Peak。"""
    p = _run(["ffmpeg", "-nostats", "-i", str(path), "-af",
              "ebur128=peak=true", "-f", "null", "-"])
    txt = p.stderr
    m = txt.rfind("Summary:")
    if m < 0:
        return None
    s = txt[m:]
    def grab(pat):
        r = re.search(pat, s)
        return float(r.group(1)) if r else None
    return {"lufs": grab(r"I:\s+(-?[\d.]+) LUFS"),
            "lra": grab(r"LRA:\s+(-?[\d.]+) LU"),
            "true_peak_dbfs": grab(r"Peak:\s+(-?[\d.]+) dBFS")}


def silences(path: Path, noise_db: int = -45, min_len: float = 0.6) -> list:
    """無音区間 [(開始, 終了)]。"""
    p = _run(["ffmpeg", "-nostats", "-i", str(path), "-af",
              f"silencedetect=noise={noise_db}dB:d={min_len}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", p.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", p.stderr)]
    out = []
    for i, s in enumerate(starts):
        out.append((s, ends[i] if i < len(ends) else None))
    return out


def dump_frames(path: Path, outdir: Path, every: float = 1.0,
                scale_w: int = 360) -> list[Path]:
    """目視確認用に every 秒ごとにPNGを書き出す(縮小)。"""
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("*.png"):
        old.unlink()
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-vf",
          f"fps=1/{every},scale={scale_w}:-1", str(outdir / "f_%03d.png")])
    return sorted(outdir.glob("f_*.png"))


def contact_sheet(frames_dir: Path, out: Path, cols: int = 7,
                  thumb_w: int = 270) -> Path:
    """dump_frames の出力を1枚のタイル画像にまとめる(目視確認用)。"""
    n = len(list(frames_dir.glob("f_*.png")))
    rows = max(1, -(-n // cols))
    _run(["ffmpeg", "-y", "-v", "error", "-framerate", "1", "-i",
          str(frames_dir / "f_%03d.png"), "-vf",
          f"scale={thumb_w}:-1,tile={cols}x{rows}", "-frames:v", "1", str(out)])
    return out


def check(video: Path, poster: Path | None) -> tuple[dict, list[str]]:
    """(情報, 問題点リスト)。問題点が空なら合格。"""
    L = LIMITS
    info = probe(video)
    info["loudness"] = loudness(video) if info["acodec"] else None
    problems = []
    if info["bytes"] > L["max_video_bytes"]:
        problems.append(f"動画が大きすぎ: {info['bytes']} > {L['max_video_bytes']}")
    if not (L["min_duration"] <= info["duration"] <= L["max_duration"]):
        problems.append(f"尺が範囲外: {info['duration']:.2f}s")
    if info["vcodec"] != "h264" or info["pix_fmt"] != "yuv420p":
        problems.append(f"映像形式が想定外: {info['vcodec']}/{info['pix_fmt']}")
    if info["profile"] not in ("High", "Main"):
        problems.append(f"プロファイル: {info['profile']}")
    if not info["faststart"]:
        problems.append("faststart(moov先頭)になっていません")
    if info["acodec"] and info["acodec"] != "aac":
        problems.append(f"音声コーデック: {info['acodec']}")
    ld = info["loudness"]
    if ld and ld["lufs"] is not None:
        lo, hi = L["lufs_range"]
        if not (lo <= ld["lufs"] <= hi):
            problems.append(f"音量が範囲外: {ld['lufs']} LUFS")
        if ld["true_peak_dbfs"] is not None and ld["true_peak_dbfs"] > -0.5:
            problems.append(f"ピークが高すぎ(音割れ注意): {ld['true_peak_dbfs']} dBFS")
    if poster is not None:
        pb = poster.stat().st_size
        info["poster_bytes"] = pb
        if pb > L["max_poster_bytes"]:
            problems.append(f"ポスターが大きすぎ: {pb}")
    return info, problems
