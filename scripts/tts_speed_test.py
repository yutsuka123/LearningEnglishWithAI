# ruff: noqa: E501
"""ネイティブ速度(speed=native)の読み上げが本当に「ネイティブの速さ」か検証する。

背景（2026-08-22ユーザー指摘）:
  「フレーズ・英単語のネイティブ速度が普通速度とあまり変わらない。ゆっくりは
  ゆっくりだが、ネイティブ速度がネイティブ速度になっていない（遅い）」。
  ただし単に早送りにすればよいのではなく、**ネイティブらしい自然な音声**で
  ある必要がある。

やること:
  DBから単語/フレーズ/例文をランダムに取り（日本語が混ざる行は除外）、
  現行の learn / native 指示文・**候補の新しい native 指示文**・
  **APIのspeedパラメータ**でそれぞれ合成し、

    - 実測の再生時間（秒）
    - words per minute (WPM)
    - learn に対する速さの比

  を表で出す。音声は data/tts_speed_test/ に .wav で保存するので、
  そのまま**耳で聴いて**「早送りっぽくないか」「ネイティブらしいか」を
  確認できる。

目安（英語の話速の一般的な基準）:
    ゆっくり(学習者向け)   ≒ 100〜130 WPM
    通常の会話           ≒ 140〜170 WPM
    速いニュース/雑談      ≒ 180 WPM 以上
  ※単語1語だけの音声はWPMが意味を持たないので、単語は「秒数」で比べる。

注意:
  - **実際にOpenAI APIを叩くので費用が発生する**（件数 × スタイル数）。
    gpt-4o-mini-tts は概ね $0.015/1k文字。数十回でも数円程度。
  - 計測のため wav で取得している。**OpenAIのwavはヘッダのフレーム数が
    プレースホルダ(0xFFFFFFFF)**なので `wave.getnframes()` は使えない
    （2026-08-22に実測で判明。全部 89478.49秒 と出た）。dataチャンクの
    実バイト数から計算すること。
  - このスクリプトは **DBを一切変更しない**（読み取りのみ）。

使い方（VPSのコンテナ内で実行する想定）:
    docker cp scripts/tts_speed_test.py eigo-app:/app/scripts/
    docker exec -i eigo-app python scripts/tts_speed_test.py
    docker cp eigo-app:/app/data/tts_speed_test ./tts_speed_test

オプション:
    --n 12            サンプル件数
    --seed 42         乱数シード
    --voice ash       声
    --styles learn,native,native_v3,native_x115
    --list-styles     候補の指示文を表示して終了
    --measure-only    合成せず、保存済みwavの長さだけ測り直す
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_settings, paths  # noqa: E402
from app.database import db  # noqa: E402
from app.services.ai import TTS_STYLES  # noqa: E402

OUT_DIR = paths.data_dir / "tts_speed_test"

# --- 比較する条件（現行 + 候補）---------------------------------------------
# instructions … 読み方の指示文（None なら現行の TTS_STYLES を使う）
# api_speed    … OpenAI TTS の speed パラメータ（None なら送らない）
CANDIDATES: dict[str, dict] = {
    "learn": {"instructions": TTS_STYLES["learn"]},
    "native": {"instructions": TTS_STYLES["native"]},
    # v1: 目標WPMを数値で明示した版。
    # → 2026-08-22の実測で **単語1語のときに0.3秒＝ほぼ無音になる事故**が
    #   2/3件で発生した。採用してはいけない見本として残す。
    "native_v1": {"instructions": (
        "Speak as a native English speaker talking casually to another native "
        "speaker. Use a brisk, everyday conversational tempo of about 160 "
        "words per minute — noticeably faster than a teacher reading for a "
        "learner. Use natural linking, contractions, reduced function words, "
        "and normal sentence stress. Do not over-enunciate and do not pause "
        "between words. Keep it relaxed and natural, never rushed or robotic."
    )},
    # v3: 短い語句でも会話調で言い切らせる版（指示文だけで速くする試み）。
    "native_v3": {"instructions": (
        "Speak as a native English speaker in relaxed everyday conversation, "
        "at about 165 words per minute. Use natural linking, contractions and "
        "reductions, and normal stress. Start immediately, do not leave a "
        "pause before or after, and do not over-enunciate. Even for a single "
        "word or a short phrase, say it the quick, offhand way a native "
        "speaker would in conversation — not the careful way a teacher would "
        "pronounce it for a student. Natural and easy to follow, never rushed."
    )},
    # 現行のnative指示文のまま、APIのspeedで確実に速くする案。
    "native_x115": {"instructions": TTS_STYLES["native"], "api_speed": 1.15},
    "native_x125": {"instructions": TTS_STYLES["native"], "api_speed": 1.25},
}

_JA = re.compile(r"[぀-ゟ゠-ヿ一-鿿]")


def wav_seconds(data: bytes) -> float:
    """wav の実バイト数から再生時間（秒）を求める。

    OpenAI が返す wav はヘッダのサイズ欄がプレースホルダなので、
    `wave` モジュールの getnframes() を信用してはいけない。
    """
    if data[:4] != b"RIFF":
        return 0.0
    i = 12
    rate = ch = width = 0
    dlen = 0
    while i + 8 <= len(data):
        cid = data[i:i + 4]
        size = struct.unpack("<I", data[i + 4:i + 8])[0]
        i += 8
        if cid == b"fmt ":
            ch, rate = struct.unpack("<HI", data[i + 2:i + 8])
            width = struct.unpack("<H", data[i + 14:i + 16])[0] // 8
        elif cid == b"data":
            over = (size in (0xFFFFFFFF, 0)) or (i + size > len(data))
            dlen = (len(data) - i) if over else size
            break
        i += size + (size & 1)
    if not (rate and ch and width):
        return 0.0
    return dlen / float(rate * ch * width)


def _samples(n: int, seed: int) -> list[tuple[str, str]]:
    """(種別, テキスト) をDBからランダムに n 件。

    日本語が混ざる行（禁止用語の注記付き例文など）は読み上げ時間が
    比較にならないので除外する（2026-08-22の実測で判明）。
    """
    import random
    rnd = random.Random(seed)
    pool: list[tuple[str, str]] = []
    try:
        with db() as conn:
            words = conn.execute(
                "SELECT english, example FROM words "
                "WHERE TRIM(COALESCE(english,'')) <> '' "
                "ORDER BY RANDOM() LIMIT 300"
            ).fetchall()
            phrases = conn.execute(
                "SELECT english FROM phrases "
                "WHERE TRIM(COALESCE(english,'')) <> '' "
                "ORDER BY RANDOM() LIMIT 300"
            ).fetchall()
        for r in words:
            if not _JA.search(r["english"] or ""):
                pool.append(("単語", r["english"]))
            ex = (r["example"] or "").strip()
            if ex and not _JA.search(ex):
                pool.append(("例文", ex))
        for r in phrases:
            if not _JA.search(r["english"] or ""):
                pool.append(("フレーズ", r["english"]))
    except Exception as e:
        print(f"（DBを読めなかったので内蔵サンプルを使います: {e}）")
    if not pool:
        pool = [
            ("単語", "abandon"), ("単語", "reluctant"),
            ("フレーズ", "Let me get back to you on that."),
            ("フレーズ", "That makes sense."),
            ("例文", "She reluctantly agreed to postpone the meeting."),
            ("例文", "The team abandoned the plan after the budget was cut."),
        ]
    by_kind: dict[str, list[str]] = {}
    for kind, text in pool:
        by_kind.setdefault(kind, []).append(text)
    picked: list[tuple[str, str]] = []
    kinds = [k for k in ("単語", "フレーズ", "例文") if by_kind.get(k)]
    i = 0
    while len(picked) < n and kinds:
        k = kinds[i % len(kinds)]
        lst = by_kind[k]
        if not lst:
            kinds.remove(k)
            continue
        picked.append((k, lst.pop(rnd.randrange(len(lst)))))
        i += 1
    return picked


def _synth(text: str, voice: str, cfg: dict) -> bytes:
    """指定条件で wav を合成（app.services.ai を経由せず直接叩く。
    本番のキャッシュ・課金記録を汚さないため）。"""
    from openai import OpenAI

    settings = load_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    extra = {}
    instr = cfg.get("instructions")
    if instr and "gpt-4o" in settings.tts_model:
        extra["instructions"] = instr
    if cfg.get("api_speed"):
        extra["speed"] = float(cfg["api_speed"])
    resp = client.audio.speech.create(
        model=settings.tts_model, voice=voice, input=text[:4000],
        response_format="wav", **extra,
    )
    return resp.read() if hasattr(resp, "read") else resp.content


def _measure_only(styles: list[str]) -> int:
    rows: dict[str, dict[str, float]] = {}
    for p in sorted(OUT_DIR.glob("*.wav")):
        m = re.match(r"(\d+)_(.+)_[a-z]+\.wav$", p.name)
        if not m:
            continue
        rows.setdefault(m.group(1), {})[m.group(2)] = \
            wav_seconds(p.read_bytes())
    if not rows:
        print(f"{OUT_DIR} に wav がありません。")
        return 1
    ratios: dict[str, list[float]] = {s: [] for s in styles}
    print("  # " + "".join(f"{s:>13}" for s in styles))
    for idx in sorted(rows):
        r = rows[idx]
        print(f"{idx:>3} " + "".join(f"{r.get(s, 0):>12.2f}s" for s in styles))
        base = r.get("learn") or 0
        for s in styles:
            if base and r.get(s):
                ratios[s].append(base / r[s])
    print()
    for s in styles:
        if ratios[s]:
            print(f"  {s:<12} learn比 平均 "
                  f"{sum(ratios[s]) / len(ratios[s]):.3f} 倍")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--voice", default="ash")
    ap.add_argument("--styles",
                    default="learn,native,native_v3,native_x115,native_x125")
    ap.add_argument("--list-styles", action="store_true")
    ap.add_argument("--measure-only", action="store_true")
    args = ap.parse_args()

    if args.list_styles:
        for k, v in CANDIDATES.items():
            print(f"--- {k} --- speed={v.get('api_speed')}\n"
                  f"{v.get('instructions')}\n")
        return 0

    styles = [s.strip() for s in args.styles.split(",") if s.strip()]
    unknown = [s for s in styles if s not in CANDIDATES]
    if unknown:
        print(f"未知のスタイル: {unknown}（--list-styles で一覧）")
        return 1
    if args.measure_only:
        return _measure_only(styles)

    settings = load_settings()
    if not settings.ai_enabled:
        print("OPENAI_API_KEY が未設定です。")
        return 1

    samples = _samples(args.n, args.seed)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"サンプル {len(samples)} 件 × 条件 {len(styles)} 種 = "
          f"{len(samples) * len(styles)} 回合成します（費用が出ます）。")
    print(f"音声の保存先: {OUT_DIR}\n")

    results: dict[str, list[tuple[float, float]]] = {s: [] for s in styles}
    for i, (kind, text) in enumerate(samples, 1):
        words = max(1, len(text.split()))
        print(f"[{i}/{len(samples)}] {kind}({words}語): {text}")
        for st in styles:
            try:
                audio = _synth(text, args.voice, CANDIDATES[st])
            except Exception as e:
                print(f"    {st:<12} 合成失敗: {e}")
                results[st].append((0.0, 0.0))
                continue
            sec = wav_seconds(audio)
            wpm = words / sec * 60 if sec else 0.0
            results[st].append((sec, wpm))
            (OUT_DIR / f"{i:02d}_{st}_{args.voice}.wav").write_bytes(audio)
            warn = "  ⚠️短すぎ(合成失敗の疑い)" if sec < 0.5 else ""
            print(f"    {st:<12} {sec:5.2f}秒  {wpm:6.1f} WPM{warn}")
        print()

    print("=" * 68)
    print("まとめ（learn を 1.00 とした速さの比。大きいほど速い）")
    print("=" * 68)
    multi = [i for i, (_, t) in enumerate(samples) if len(t.split()) > 2]
    base = results.get("learn")
    for st in styles:
        wpms = [results[st][i][1] for i in multi if results[st][i][1]]
        avg_wpm = sum(wpms) / len(wpms) if wpms else 0.0
        ratio = ""
        if base:
            pairs = [(base[i][0], results[st][i][0]) for i in multi
                     if base[i][0] and results[st][i][0]]
            if pairs:
                r = sum(b / n for b, n in pairs) / len(pairs)
                ratio = f"  learn比 {r:.2f}倍"
        print(f"  {st:<12} 平均 {avg_wpm:6.1f} WPM（3語以上 {len(wpms)}件）"
              f"{ratio}")
    print()
    print("目安: 学習者向け 100〜130 / 自然な会話 140〜170 / 速い 180〜 WPM")
    print(f"耳で確認: {OUT_DIR} の wav を聴き比べ、"
          "「早送りっぽくないか」「不自然に詰まっていないか」を見てください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
