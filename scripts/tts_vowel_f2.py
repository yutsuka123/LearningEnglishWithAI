"""音声の「最初の母音」を音響分析(Praatのフォルマント)で分類する開発用ツール(2026-10-03)。

背景: 「a cappella」を女声(nova)で再生すると「アカペラ」でなく「エイカペラ」になる、と管理者メモ#7で報告された。
LLM(gpt-audio)のブラインド書き起こしでは「a」が曖昧で/ɑː/と/eɪ/を区別できなかったため、母音のF2で客観的に判定する。
  /ɑː/(アー)  : F1が高め(男声~700/女声~900)・F2が低く安定(男声~1100/女声~1300)
  /eɪ/(エイ)  : F1が下がり、F2が約1700→2500〜2900まで上昇(二重母音)
  /ə/(弱いア): F1/F2とも中間(F2 ~1400〜1700)で短い

使い方(dev専用・requirementsには入れない: `.venv/bin/pip install praat-parselmouth numpy`):
  .venv/bin/python scripts/tts_vowel_f2.py <mp3> [<mp3> ...]              # 各ファイルの先頭の母音を分類
  .venv/bin/python scripts/tts_vowel_f2.py --in-sentence a ca <mp3> ...    # 文中の「a ca…」の「a」を取り出して分類(whisperの単語時刻を使う・OpenAIキーが要る)
声の種別はファイル名の`nova`(女声)/`ash`(男声)で判断する(最大フォルマントの設定が変わる)。本番・DBには触れない。
"""

from __future__ import annotations

import re
import subprocess
import unicodedata
import sys
import tempfile
from pathlib import Path

import numpy as np
import parselmouth


def _to_wav(src: Path, dst: Path, start: float | None = None, dur: float | None = None) -> None:
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    if dur is not None:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-i", str(src), "-ar", "22050", "-ac", "1", str(dst)]
    subprocess.run(cmd, check=True)


def classify_first_vowel(wav: Path, female: bool) -> dict:
    """最初の有声区間(最大強度-22dB以上が続く区間)のF1/F2から分類する。
    戻り値: {"label": "ah"|"ay"|"schwa"|"?", "f2_med", "f2_end", "f1_med", "frames", "start"}"""
    snd = parselmouth.Sound(str(wav))
    fm = snd.to_formant_burg(time_step=0.025, max_number_of_formants=5,
                             maximum_formant=5500 if female else 5000, window_length=0.03)
    it = snd.to_intensity(time_step=0.025)
    peak = max(it.values[0]) if it.values.size else 0
    frames = []
    for t in np.arange(0.0, snd.duration, 0.025):
        db = it.get_value(t)
        f1, f2 = fm.get_value_at_time(1, t), fm.get_value_at_time(2, t)
        voiced = db is not None and db >= peak - 22 and f1 == f1 and f2 == f2 and 150 < f1 < 1300
        frames.append((t, voiced, f1, f2))
    run: list = []
    for fr in frames:                      # 最初の連続した有声区間(3フレーム=75ms以上)
        if fr[1]:
            run.append(fr)
        elif len(run) >= 3:
            break
        else:
            run = []
    if len(run) < 3:
        return {"label": "?", "frames": len(run)}
    f1s = [r[2] for r in run]
    f2s = [r[3] for r in run]
    f2_med, f2_end = float(np.median(f2s)), float(np.median(f2s[-3:]))
    f1_med = float(np.median(f1s))
    # 判定: 二重母音/eɪ=F2の中央値が高い、または(F2が中程度かつ終端で大きく上昇)。区間の終端は次の子音(k等)への
    # 遷移でF2が上がることがあるため、終端だけでエイと決めない。ア=F2の中央値が低く、かつF1が高い(口が開く)。
    ay = f2_med > 1700 or (f2_end > 2300 and f2_med > 1500)
    open_vowel = f1_med >= (700 if female else 520)
    ah = f2_med < (1650 if female else 1500) and open_vowel
    label = "ay" if ay else ("ah" if ah else "schwa")
    return {"label": label, "f2_med": round(f2_med), "f2_end": round(f2_end), "f1_med": round(f1_med),
            "frames": len(run), "start": round(run[0][0], 2)}


def first_word_clip(mp3: Path, first: str, nxt: str, out: Path) -> bool:
    """文中で`first`の次が`nxt`で始まる箇所を探し、`first`の語の区間をwavに切り出す(whisper-1の単語時刻)。"""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import tts_blind_judge as j
    client = j._client()
    with open(mp3, "rb") as f:
        tr = client.audio.transcriptions.create(model="whisper-1", file=f, response_format="verbose_json",
                                                timestamp_granularities=["word"], language="en")
    def norm(w: str) -> str:     # アクセント記号を外して小文字化(à→a)
        return re.sub(r"[^a-z']", "", unicodedata.normalize("NFKD", w).encode("ascii", "ignore").decode().lower())
    ws = [(norm(w.word), w.start, w.end) for w in (tr.words or [])]
    for i in range(len(ws) - 1):
        if ws[i][0] == norm(first) and ws[i + 1][0].startswith(norm(nxt)):
            st, en = max(0.0, ws[i][1] - 0.15), ws[i + 1][1] + 0.02   # 語頭の取りこぼしに備え少し前から
            _to_wav(mp3, out, st, en - st)
            return True
    return False


def classify_file(mp3: Path, in_sentence: tuple[str, str] | None = None) -> dict:
    female = "nova" in mp3.name
    with tempfile.TemporaryDirectory() as d:
        wav = Path(d) / "x.wav"
        if in_sentence:
            if not first_word_clip(mp3, in_sentence[0], in_sentence[1], wav):
                return {"label": "?", "note": "文中に見つからない"}
        else:
            _to_wav(mp3, wav)
        return classify_first_vowel(wav, female)


if __name__ == "__main__":
    args = sys.argv[1:]
    ins = None
    if args and args[0] == "--in-sentence":
        ins = (args[1], args[2])
        args = args[3:]
    for p in args:
        r = classify_file(Path(p), ins)
        print(f"{Path(p).name:58s} {r}")
