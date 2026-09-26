"""原語(日本語)の音声(VOICEVOX生成・「詳細plus」の中身)の照合と場所(2026-09-26・docs/DESIGN.md §9.8)。

## 置き場所・形式
- `data/audio_native/` に `w{語ID}_{male|female}_{原語表記のハッシュ10桁}.mp3` と `manifest.json`。
  **`data/audio/`(AI音声のキャッシュ)とは別のディレクトリ**にしてある。`audio_store`の経路は、キャッシュに無いと
  OpenAIで合成し直す作りなので、原語音声をそこに置くと「有料の中身が課金なしで合成される/配られる」穴になりうる。
- 生成は`scripts/gen_native_audio_voicevox.py`(開発機でVOICEVOXを使う・費用0)。**VOICEVOX本体・モデルは再配布禁止**なので、
  サーバーへ置くのは生成したmp3とmanifestだけ。クレジット「VOICEVOX:キャラ名」は必須(manifestの`credit`を画面に出す)。

## 誤配信の防止(音声誤配信事故の再発防止・audio_storeと同じ考え方)
- manifestは語のIDごとに`english`と`text`(原語表記)を持つ。**DB側の現在の値(englishとdetail.native.text)と一致したときだけ**
  音声を出す。IDが指す語が変わっていたら(=ローカルと本番でID採番が分岐した等)一致せず、音声は出ない(欄も「音声なし」になるだけ)。
- ファイル名はmanifestの`file`を信用せず、IDと性別と原語表記のハッシュから**自分で組み立てる**(パス操作の余地なし)。
- 課金の門番は`word_plus`側(開いた記録がある/管理者のときだけ`GET /api/words/{id}/plus/audio/{sex}`が返す)。
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Optional

from ..config import paths

SEXES = ("male", "female")
_CREDIT_RE = re.compile(r"^VOICEVOX:[^\s<>&\"'/\\]{1,30}$")
_cache: dict = {"mtime": None, "words": {}}


def _dir() -> Path:
    return paths.data_dir / "audio_native"


def text_hash(text: str) -> str:
    """`audio_store.text_hash`と同じ(原語表記→10桁)。生成スクリプトも同じ式でファイル名を作る。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]


def _manifest() -> dict:
    """{語ID(文字列): {english, text, male:{credit}, female:{credit}, ...}}。ファイルの更新時刻が変わったときだけ読み直す。
    無い/壊れているときは空(=原語音声なし)で、例外は出さない。"""
    p = _dir() / "manifest.json"
    try:
        mtime = p.stat().st_mtime_ns
    except OSError:
        _cache.update(mtime=None, words={})
        return {}
    if _cache["mtime"] != mtime:
        words: dict = {}
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("words"), dict):
                words = data["words"]
        except (OSError, ValueError):
            words = {}
        _cache.update(mtime=mtime, words=words)
    return _cache["words"]


def _entry(word_id: int, english: str, text: str) -> Optional[dict]:
    if not text or not english:
        return None
    e = _manifest().get(str(word_id))
    if not isinstance(e, dict) or e.get("english") != english or e.get("text") != text:
        return None   # IDが指す語が変わった(または別の語)=出さない
    return e


def file_path(word_id: int, sex: str, english: str, text: str) -> Optional[Path]:
    """配る音声ファイル(語のenglish・原語表記がmanifestと一致し、ファイルが実在するときだけ)。"""
    if sex not in SEXES or _entry(word_id, english, text) is None:
        return None
    p = _dir() / f"w{int(word_id)}_{sex}_{text_hash(text)}.mp3"
    return p if p.is_file() else None


def info(word_id: int, english: str, text: str) -> Optional[dict]:
    """画面用の情報`{"male": {"credit": ..}, "female": {"credit": ..}}`(男女の両方が実在するときだけ・無ければNone)。
    音声そのもののURLは返さない(配信は課金の門番を通る専用エンドポイントだけ)。"""
    e = _entry(word_id, english, text)
    if e is None:
        return None
    out: dict = {}
    for sex in SEXES:
        s = e.get(sex)
        if not isinstance(s, dict) or file_path(word_id, sex, english, text) is None:
            return None
        credit = str(s.get("credit") or "")
        out[sex] = {"credit": credit if _CREDIT_RE.match(credit) else "VOICEVOX"}
    return out
