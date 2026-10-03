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
import unicodedata
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


# --- 外来表現の "a" / "à"(イタリア語・フランス語の前置詞): 冠詞の読みにしない(2026-10-03) ----------------
# 管理者メモ#7: 「a cappella」を女声(nova)で再生すると「アカペラ」でなく「エイカペラ」になっていた(男声は正しい)。
# 綴りだけを渡すと、先頭の"a"を英語の冠詞(/eɪ/や弱い/ə/)に読んでしまう。音響分析(F2の上昇=二重母音/eɪ/)で
# 本番の音声を測り、見出し語の女声と、フレーズ「Could I order à la carte instead?」の女声・"à la carte"例文の
# ネイティブ速度(女声)で同じ誤読を確認した。辞書の読みは/ɑː/(アー)なので、"ah"に置き換えて固定する。
# 対象は「冠詞と紛れる前置詞のa/à」を持つ外来表現だけ(下の正規表現に当たらない文は一切変わらない)。
_FOREIGN_A = re.compile(
    r"(?<![\w-])(?P<a>[aà])(?P<sp>\s+)(?P<rest>(?:cappella|capella|la\s+(?:carte|mode)))\b",
    re.I)
# "roman à clef"(実話小説): "clef"は音楽用語のクレフ(/klɛf/)と同じ綴りだが、ここはフランス語で/kleɪ/(クレー)。
# 男女どちらの声も「klef」と読んでいた(2026-10-03・ブラインド判定の3票とも)。
_ROMAN_A_CLEF = re.compile(r"(?<![\w-])(?P<roman>roman)(?P<pl>s?)[\s-]+[aà][\s-]+clefs?(?![\w-])", re.I)


def _has_foreign_a(text: str) -> bool:
    return bool(_FOREIGN_A.search(text) or _ROMAN_A_CLEF.search(text))


def _respell_foreign_a(text: str) -> str:
    def sub_a(m: re.Match) -> str:
        ah = "Ah" if m.group("a") in "AÀ" else "ah"
        rest = m.group("rest")
        if rest[:2].lower() == "la":          # "la carte" → "lah carte"(辞書 /lɑː/)
            rest = rest[:2] + ("H" if rest[:2].isupper() else "h") + rest[2:]
        return ah + m.group("sp") + rest

    def sub_roman(m: re.Match) -> str:
        head = "Roh-mahn" if m.group("roman")[0].isupper() else "roh-mahn"
        return head + ("z" if m.group("pl") else "") + " ah klay"

    return _ROMAN_A_CLEF.sub(sub_roman, _FOREIGN_A.sub(sub_a, text))


# --- 見出し語そのものの読み替え(2026-10-04・ver1.5.11) ---------------------------------------------------------
# 9/20の音声⇔IPA調査(`docs/AUDIO_IPA_SCAN_2026-09-20.md`)で読み替え案が合格した47語を、2026-10-04に現行の本番音声と
# 同じ基準で再判定した(ブラインド書き起こし3票+独立の再確認3票・複数テイク・必要な語は読み替え案を比較)。その結果、
# **現行の音声が実際に誤読していて、読み替えで直せると確認できた語だけ**を下の表に入れた(他の語は9/26の日本語由来語の
# 差し替え等で既に正しく読めており、規則を足す必要がない=足さない)。lead(鉛)=「リード」→「レッド」、bow(弓)=
# 「バウ」→「ボウ」、geisha=「デイシャ」→「ゲイシャ」、ema=「エマ」→「エイマ」 等。
# ★適用は「テキスト全体がその語と一致するとき」だけ(大小文字・前後の空白は無視)。例文・フレーズの中の同じ綴りは一切変えない
#   (lead=「鉛」は/lɛd/だが"lead the team"は/liːd/・"bow"は「弓/お辞儀」で読みが違うなど、綴り単位の置換は文中で誤爆する。
#    検証した条件=見出し語単独の音声、とも一致させる)。
# 除外(判断の記録): sake・sake brewer=日本酒の規則で適用済み / 人種差別語1語=音声を作り直す対象にしない(オーナー判断待ち) /
#   bear=現行が合格で、読み替え"bayr"は男声が「ベイ」になる / live load(/laɪv/)=読み替えでも自動判定で「give」と「five」を
#   区別できず検証できなかった(現行は誤読の疑い・オーナーの耳で確認する) / 他は現行が合格のため不要。
# 値は「読み通りの綴り」(sakeの`sah-kee`と同じ型)。大文字は強勢の位置。追加するときはIPAと矛盾しないこと・
# 実際に合成してブラインド判定で確認すること(`scripts/tts_blind_judge.py`)。
_HEADWORD_RESPELL: dict[str, str] = {
    "bow":                "boh",                          # /boʊ/
    "lead":               "led",                          # /lɛd/
    "lead-acid battery":  "led-ass-id bat-uh-ree",        # /lɛd ˈæsɪd ˈbætəri/
    "geisha":             "gay-shuh",                     # /ˈɡeɪʃə/
    "poka-yoke":          "poh-kuh yoh-kay-ee",           # /ˌpoʊkəˈjoʊkeɪ/
    "neta":               "neh-tah",                      # /ˈnɛtɑː/
    "ho-o":               "hoh-oh",                       # /ˈhoʊ oʊ/
    "ema":                "ay-mah",                       # /ˈeɪmɑː/
    "chawan":             "chah-wahn",                    # /ˈtʃɑːwɑːn/
    "moe":                "moh-ay",                       # /ˈmoʊeɪ/
    "seinen":             "say-nen",                      # /ˈseɪnɛn/
    "jamon":              "hah-mohn",                     # /hɑːˈmoʊn/
    "tostones":           "tah-stoh-nayz",                # /tɒˈstoʊneɪz/
    "patina":             "pat-in-uh",                    # /ˈpætɪnə/
    "crema":              "kray-muh",                     # /ˈkreɪmə/
    "en passant":         "ahn pah-sahn",                 # /ɒ̃ pæˈsɒ̃/
    "levain":             "luh-van(g)",                   # /ləˈvæ̃/
    "rnav":               "ar-navv",                      # /ˈɑːrnæv/
}


def _headword_key(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split()).casefold()


def _is_headword(text: str) -> bool:
    return _headword_key(text) in _HEADWORD_RESPELL


def _respell_headword(text: str) -> str:
    return _HEADWORD_RESPELL[_headword_key(text)]


RULES: list[tuple[Callable[[str], bool], Callable[[str], str]]] = [
    (_is_japanese_sake, _respell_sake),
    (_has_ja_loan, _respell_ja_loan),
    (_has_foreign_a, _respell_foreign_a),
]   # 見出し語の規則は`spoken_text`の先頭で別に判定する


def spoken_text(text: str) -> str:
    """TTSに渡す綴り。読み替えが要る語を含まなければ`text`をそのまま返す。

    見出し語そのもの(テキスト全体が表の語と一致)は、他の規則で書き換えられる前の綴りで先に判定する
    (将来`sente`等を表に足しても先行規則に食われないように・2026-10-04独立レビューLOW-3)。
    なお`/api/learn/tts`(自由テキストの読み上げ)にも同じ規則が効く: 利用者が1語だけ(例: "bow")を
    読ませたときは、表の読みになる(文・フレーズの中の同じ綴りは変わらない)。"""
    if _is_headword(text):
        return _respell_headword(text)
    for match, respell in RULES:
        if match(text):
            text = respell(text)
    return text
