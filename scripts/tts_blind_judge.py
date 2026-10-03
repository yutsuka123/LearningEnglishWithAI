"""TTS音声のブラインド判定器(2026-10-03・方式は docs/AUDIO_IPA_SCAN_2026-09-20.md と
memory `reference-tts-blind-judge-gotchas` の実運用メモに基づく)。

綴りもIPAも見せず、聞こえた音だけを英語風のrespellingで書き起こさせる(gpt-audio系)。
語を明かすと先入観で偏るため、プロンプトは中立のまま(文脈の説明を足すと全拒否になった)。
有効票だけを数える(拒否・JSON・「音声を下さい」等の返答は除外して最大14回まで呼ぶ)。

  .venv/bin/python scripts/tts_blind_judge.py <mp3> [<mp3> ...]     # 各ファイルの書き起こし(3票)を表示
  .venv/bin/python scripts/tts_blind_judge.py --vowel <mp3> ...     # 第1音節の母音を選択式で3票(ay/ah等を区別)

他のスクリプトからは `judge(path, votes=3)` を使う。本番・DBには一切触れない(ローカルのファイルを読むだけ)。
費用の目安: 1票あたり約$0.003〜0.007。
"""

from __future__ import annotations

import base64
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PROMPT = ("Listen to this audio clip. Do not guess the spelling. Write what you hear: "
          "each word as hyphen-separated syllables in an English-style respelling, with stressed "
          "syllables in CAPITALS, all on one line. Output only that line.")
_MODELS = ("gpt-audio-1.5", "gpt-audio")
_REFUSAL = re.compile(
    r"sorry|can't help|cannot help|unable to|json|provide (the |an )?audio|audio clip|"
    r"replying to|i can.t (hear|listen|process)|don.t have (the )?(ability|access)", re.I)


def _padded_wav_b64(mp3: Path, head: float = 0.6, tail: float = 0.6, tail_only: float | None = None) -> str:
    """前後に無音を足した16kHzのwavをbase64で返す(`tail_only`=秒を指定すると末尾だけを切り出す)。"""
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "x.wav"
        cmd = ["ffmpeg", "-v", "error", "-y"]
        if tail_only:
            cmd += ["-sseof", f"-{tail_only}"]
        cmd += ["-i", str(mp3), "-af", f"adelay={int(head * 1000)}:all=1,apad=pad_dur={tail}",
                "-ar", "16000", "-ac", "1", str(out)]
        subprocess.run(cmd, check=True)
        return base64.b64encode(out.read_bytes()).decode()


def _client():
    from app.services import ai
    client, _ = ai._client()
    if client is None:
        raise SystemExit("OpenAIクライアントを作れません(キー未設定)")
    return client


def one_vote(client, b64: str) -> str | None:
    """1票。拒否・無効な返答はNone。"""
    for model in _MODELS:
        try:
            r = client.chat.completions.create(
                model=model, modalities=["text"],
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "input_audio", "input_audio": {"data": b64, "format": "wav"}}]}])
        except Exception as e:  # noqa: BLE001 — モデル名違い等は次の候補へ
            err = str(e)
            if "model" in err.lower() and ("not found" in err.lower() or "does not exist" in err.lower()):
                continue
            return None
        txt = (r.choices[0].message.content or "").strip().splitlines()
        line = txt[0].strip().strip("`\"' ") if txt else ""
        if not line or _REFUSAL.search(line) or len(line) > 160:
            return None
        return line
    return None


VOWEL_PROMPT = ("Listen to this audio clip. Focus only on the very first syllable. Which vowel sound does it have? "
                "A) like 'ay' in 'say'  B) like 'ah' in 'father'  C) like 'a' in 'cat'  D) like 'uh' in 'about'  "
                "E) something else. Answer with a single capital letter only.")


def vowel_vote(client, b64: str) -> str | None:
    """第1音節の母音の選択式1票(A=ay B=ah C=cat D=schwa E=other)。拒否はNone。"""
    for model in _MODELS:
        try:
            r = client.chat.completions.create(
                model=model, modalities=["text"],
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": VOWEL_PROMPT},
                    {"type": "input_audio", "input_audio": {"data": b64, "format": "wav"}}]}])
        except Exception as e:  # noqa: BLE001
            err = str(e).lower()
            if "model" in err and ("not found" in err or "does not exist" in err):
                continue
            return None
        m = re.match(r"\s*([A-E])\b", (r.choices[0].message.content or "").strip())
        return m.group(1) if m else None
    return None


def vowel_judge(mp3: str | Path, votes: int = 3, max_calls: int = 12, client=None) -> list[str]:
    client = client or _client()
    b64 = _padded_wav_b64(Path(mp3))
    got: list[str] = []
    for _ in range(max_calls):
        v = vowel_vote(client, b64)
        if v:
            got.append(v)
            if len(got) >= votes:
                break
    return got


def clip_target(client, mp3: str | Path, pattern: str, out: Path, lead: float = 0.04, trail: float = 0.05) -> bool:
    """単語タイムスタンプ付きの文字起こし(whisper-1)で、パターン(例 r"a cappella")に当たる区間だけを
    切り出して `out`(wav)に書く。見つからなければFalse。長い例文の中の特定の語だけを判定するために使う。"""
    with open(mp3, "rb") as f:
        tr = client.audio.transcriptions.create(
            model="whisper-1", file=f, response_format="verbose_json",
            timestamp_granularities=["word"], language="en")
    words = [(re.sub(r"[^\w']", "", w.word).lower(), w.start, w.end) for w in (tr.words or [])]
    toks = pattern.lower().split()
    for i in range(len(words) - len(toks) + 1):
        if all(words[i + k][0] == toks[k] for k in range(len(toks))):
            st = max(0.0, words[i][1] - lead)
            en = words[i + len(toks) - 1][2] + trail
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{st:.3f}", "-t", f"{en - st:.3f}", "-i", str(mp3),
                            "-af", "adelay=600:all=1,apad=pad_dur=0.6", "-ar", "16000", "-ac", "1", str(out)], check=True)
            return True
    return False


def vowel_judge_in_context(mp3: str | Path, pattern: str, votes: int = 3, client=None) -> list[str] | None:
    """文中の特定の語句の第1音節の母音を判定する(語句が文字起こしで見つからなければNone)。"""
    client = client or _client()
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "clip.wav"
        if not clip_target(client, mp3, pattern, out):
            return None
        b64 = base64.b64encode(out.read_bytes()).decode()
        got: list[str] = []
        for _ in range(12):
            v = vowel_vote(client, b64)
            if v:
                got.append(v)
                if len(got) >= votes:
                    break
        return got


def synth(text: str, voice: str, style: str = "learn", client=None, respell: bool = True) -> bytes:
    """本番と同じ入力で1回合成する(読み替え`tts_hints.spoken_text`・指示文・モデルも本番と同じ)。
    ローカルのDB・キャッシュには書かず、バイト列を返すだけ。"""
    from app.config import load_settings
    from app.services import ai, tts_hints
    client = client or _client()
    speak = tts_hints.spoken_text(text) if respell else text
    extra = {"instructions": ai._tts_instructions(style)}
    resp = client.audio.speech.create(model=load_settings().tts_model, voice=voice, input=speak,
                                      response_format="mp3", **extra)
    return resp.read() if hasattr(resp, "read") else resp.content


def judge(mp3: str | Path, votes: int = 3, max_calls: int = 14, client=None) -> list[str]:
    """有効票(書き起こし)を最大votes個集めて返す。足りなければ少ないまま返す。"""
    client = client or _client()
    mp3 = Path(mp3)
    full = _padded_wav_b64(mp3)
    tail = None
    got: list[str] = []
    for i in range(max_calls):
        # 3回続けて無効なら、末尾だけを切り出して聞かせる(長い例文が拒否されるときの回避)
        b64 = full if (i < 3 or got) else (tail or (tail := _padded_wav_b64(mp3, tail_only=1.8)))
        v = one_vote(client, b64)
        if v:
            got.append(v)
            if len(got) >= votes:
                break
    return got


if __name__ == "__main__":
    c = _client()
    args = sys.argv[1:]
    vowel = bool(args) and args[0] == "--vowel"
    for p in (args[1:] if vowel else args):
        print(Path(p).name)
        if vowel:
            print("   ", vowel_judge(p, client=c))
        else:
            for v in judge(p, client=c):
                print("   ", v)
