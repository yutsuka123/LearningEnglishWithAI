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


# --- 日本語由来語(色名・将棋語): 「英語話者が読む音」への読み替え(2026-09-26) ---------------
# 綴りだけを渡すと、声(ash/nova)によって別々に読まれたり誤読される語(sente=「セント」・gote=「ゴート」・
# 色名の`-iro`=「ヘロ」等)がある(既存音声のブラインド判定で確認)。DBのIPA(英語風・
# `scripts/apply_ja_origin_pronunciation_2026_09_26.py`で設定)と音声を一致させるため、読みを固定する
# 読み替えを合成時の入力にだけ適用する(表示・DB・item音声のキャッシュキーは元の綴りのまま)。
# 値は「読み通りの綴り」(sakeの`sah-kee`と同じ型)。追加するときはIPAと矛盾しないこと・実際に合成して
# ブラインド判定で確認すること。
_JA_LOAN_RESPELL: dict[str, str] = {
    "sente": "sen-tay",                    # /ˈsɛnteɪ/
    "gote": "goh-tay",                     # /ˈɡoʊteɪ/
    "kifu": "kee-foo",                     # /ˈkiːfuː/
    "ai-iro": "eye ee-roh",                # /ˈaɪ ˌiːroʊ/
    "moegi-iro": "moh-eh-ghee ee-roh",     # /moʊˈɛɡi ˌiːroʊ/ (綴りのgeeはアルファベットGの「ジー」に読まれるため、硬いgはghee)
    "asagi-iro": "ah-sah-ghee ee-roh",     # /ɑːˈsɑːɡi ˌiːroʊ/
    "shu-iro": "shoo ee-roh",              # /ˈʃuː ˌiːroʊ/
    "uguisu-iro": "oo-gwee-soo ee-roh",    # /uːˈɡwiːsuː ˌiːroʊ/
    "kinari-iro": "kee-nah-ree ee-roh",    # /kiːˈnɑːri ˌiːroʊ/
    "ama-iro": "ah-mah ee-roh",            # /ˈɑːmɑː ˌiːroʊ/
    "fuji-iro": "foo-jee ee-roh",          # /ˈfuːdʒi ˌiːroʊ/
    "kyo-murasaki": "kyoh moo-rah-sah-kee",  # /ˈkjoʊ mʊrɑːˈsɑːki/
    "koki-hi": "koh-kee hee",              # /koʊˈki hi/
}
_JA_LOAN_RE = re.compile(
    r"(?<![\w-])(" + "|".join(
        re.escape(k) for k in sorted(_JA_LOAN_RESPELL, key=len, reverse=True)) + r")(?![\w-])",
    re.I)


def _has_ja_loan(text: str) -> bool:
    return bool(_JA_LOAN_RE.search(text))


def _respell_ja_loan(text: str) -> str:
    def sub(m: re.Match) -> str:
        r = _JA_LOAN_RESPELL[m.group(1).lower()]
        return r[0].upper() + r[1:] if m.group(1)[0].isupper() else r
    return _JA_LOAN_RE.sub(sub, text)


RULES: list[tuple[Callable[[str], bool], Callable[[str], str]]] = [
    (_is_japanese_sake, _respell_sake),
    (_has_ja_loan, _respell_ja_loan),
]


def spoken_text(text: str) -> str:
    """TTSに渡す綴り。読み替えが要る語を含まなければ`text`をそのまま返す。"""
    for match, respell in RULES:
        if match(text):
            text = respell(text)
    return text
