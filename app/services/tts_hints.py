"""TTS(読み上げ)に渡す綴りの読み替え。

音声は「見出し語・例文・フレーズの綴り」だけをTTSに渡して作るため、発音記号
(detail.pronunciation)が正しくても、綴りが別の英単語と同じ語は英語の読みで
発音されてしまう(2026-09-20発覚: 日本酒の"sake"が"for the sake of"と同じ
「セイク」になっていた。データ側の発音記号は/ˈsɑːki/で正しかった)。
データの照査(訳・例文・IPAの文字列・事実確認)では音声の実際の発音は確認
していないため、この種の誤りは照査を通っても残る。

対策: TTSに渡す直前に、読み間違えやすい語だけを「読み通りの綴り」に置き換える
(例: 日本酒のsake → sah-kee。DBのIPA/ˈsɑːki/と一致させる)。表示・DB・
音声ファイルのキャッシュキーは元の綴りのまま変わらない(置き換えは合成時の
入力だけ)。なお生成TTSは同じ綴りでも文・声によって語尾がkee/kay等に揺れる
ことがある(2026-09-20実測・どちらも辞書にある英語の読み)。

※ instructions(指示文)で「こう読め」と書く方法は効かなかった(2026-09-20
実測: gpt-4o-mini-tts はsakeを指示どおりに読まず、綴り通りのセイクのまま)。
綴りの読み替えは、同じ実測で意図どおり読まれることを確認している。

読み方の補正が要る語は、下の`RULES`に足す。`RULES`は(当てはまるか, 置き換え)
の組で、当てはまらないテキストは一切変わらない(=既存語の合成結果・
tts_cacheキーは不変)。
"""

from __future__ import annotations

import re
from typing import Callable

# --- 日本酒の"sake" -------------------------------------------------------
# "for the sake of / for God's sake / for its own sake / forsake"は英語の
# 慣用でセイク(/seɪk/)が正しいので対象外にし、それ以外の"sake"を日本酒とみなす。
_SAKE = re.compile(r"\bsake\b", re.I)
_SAKE_IDIOM = re.compile(
    r"\bsake\s+of\b"                    # for the sake of ...
    r"|['’]s?\s+sake\b"                 # for God's / old times' sake
    r"|\bown\s+sake\b"                  # for its/their own sake
    r"|\bfor\s+(?:\w+\s+){0,2}sake\b",  # for the sake / for goodness sake
    re.I,
)
_SAKE_SPOKEN = "sah-kee"   # 辞書の第一形 /ˈsɑːki/(DBのIPAと一致・英語話者の読み)


def _is_japanese_sake(text: str) -> bool:
    return bool(_SAKE.search(text)) and not _SAKE_IDIOM.search(text)


def _respell_sake(text: str) -> str:
    return _SAKE.sub(
        lambda m: _SAKE_SPOKEN.capitalize() if m.group(0)[0].isupper()
        else _SAKE_SPOKEN, text)


RULES: list[tuple[Callable[[str], bool], Callable[[str], str]]] = [
    (_is_japanese_sake, _respell_sake),
]


def spoken_text(text: str) -> str:
    """TTSに渡す綴り。読み替えが要る語を含まなければ`text`をそのまま返す。"""
    for match, respell in RULES:
        if match(text):
            text = respell(text)
    return text
