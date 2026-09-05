"""ゲーム機能のAPI(2026-09-03・第一弾はクロスワード)。

2026-09-05〜一般公開。サンプルクロスワード(source_type='sample')は
ゲスト含め誰でも遊べる(_guard_session_access参照)。自分で作る方
(分野/単語帳から選ぶカスタムゲーム)はログイン済みユーザーなら誰でも
使える(_guard_games_access参照。ゲストは単語帳が使えないことと、
生成のたびに実際のAI原価が発生し得ることから、まずはサンプルのみで
体験してもらう)。設計の詳細・スコア/ヒント仕様はdocs/TODO.md および
実装時のプランドキュメント参照。
"""

from __future__ import annotations

import difflib
import json
import random
import re

from fastapi import APIRouter
from pydantic import BaseModel

from ..config import log
from ..database import db
from ..services import crossword_gen, errors
from ..services.auth import current_user_id
from ..services.spaced_repetition import banned_filter

router = APIRouter(prefix="/api/games", tags=["games"])

_WORD_RE = re.compile(r"^[A-Za-z]+$")
MIN_WORD_LEN, MAX_WORD_LEN = 3, 10
# 冠詞落とし+複合語のスペースを"_"に変換(2026-09-05ユーザー指示)。
# 「the Sun」「the Moon」のように冠詞+1語、「litter box」「Siamese cat」
# のように複数語で登録されている語は、そのままだと_WORD_RE(1単語限定)に
# 弾かれてクロスワードに出題できなかった。
#   1. 先頭の冠詞(the/a/an)は答えから完全に落とす(「the Sun」→「SUN」。
#      冠詞自体は意味を持たないため)。
#   2. 冠詞を落とした後もなお複数語（スペース区切り）が残る場合は、
#      スペースを"_"に変換して1つの答えにする(「the Milky Way」→
#      冠詞落とし→「Milky Way」→「MILKY_WAY」)。この"_"のマスは常時
#      開示する(未解答でも見える。答え合わせ・部分一致判定はプレイヤー
#      入力側のスペースを"_"に正規化してから比較する。_session_state・
#      crossword_answer参照)。
# 語義・例文は元の語(冠詞/スペースありの原文)のものをそのまま使う。
# _masked_exampleは答え文字列の部分一致でマスクするため、例文中に元の
# 表記(スペースあり)が含まれていても問題なくマスクできる。
_ARTICLE_RE = re.compile(r"^(?:the|a|an)\s+(.+)$", re.IGNORECASE)
_MULTI_WORD_RE = re.compile(r"^[A-Za-z]+(?: [A-Za-z]+)+$")
# 複合語("_"を含む)は素の単語より長くなりがちなため上限を緩める。
MAX_WORD_LEN_COMPOUND = 18


def _normalize_crossword_answer(raw: str) -> tuple[str, bool] | None:
    """words.englishをクロスワードの答え用に正規化する。
    戻り値は(答え文字列, 冠詞を落としたか)。出題不可なら None。"""
    text = (raw or "").strip()
    if _WORD_RE.match(text):
        if not (MIN_WORD_LEN <= len(text) <= MAX_WORD_LEN):
            return None
        return text.upper(), False
    article_dropped = False
    m = _ARTICLE_RE.match(text)
    if m:
        text = m.group(1).strip()
        article_dropped = True
    if _WORD_RE.match(text):
        if not (MIN_WORD_LEN <= len(text) <= MAX_WORD_LEN):
            return None
        return text.upper(), article_dropped
    if _MULTI_WORD_RE.match(text):
        joined = text.replace(" ", "_")
        if not (MIN_WORD_LEN <= len(joined) <= MAX_WORD_LEN_COMPOUND):
            return None
        return joined.upper(), article_dropped
    return None
# 性器・生殖器等のセンシティブな語(2026-09-05ユーザー指示「センシティブ
# な内容・性器などの単語等はクロスワード出題から外しましょう」)。
# words.domain='身体'には解剖学の一環としてurethra〜pubic hairの一連の
# 生殖器名(id 10900,10902〜10911,10914)が含まれるが、これらは「禁止用語」
# ドメインには入れない(通常の単語学習・医療英語としては引き続き必要な
# 語のため、一覧/クイズ等では従来通り表示する)。クロスワードの出題
# (ゲーム機能)からだけ、この語IDを明示的に除外する。前立腺がん・経腟
# 分娩・子宮のような病名/専門医学用語(身体ドメイン以外)は対象外
# (性的に露骨な語というより一般的な医学・健康トピックのため)。
CROSSWORD_SENSITIVE_WORD_IDS = frozenset({
    10900,  # urethra 尿道
    10902, 10903,  # testicle(s) 精巣
    10904, 10905,  # ovary/ovaries 卵巣
    10906,  # penis 陰茎
    10907,  # vagina 腟
    10908,  # scrotum 陰嚢
    10909,  # vulva 外陰部
    10910,  # prostate 前立腺
    10911,  # genitals 性器・陰部(総称)
    10914,  # pubic hair 陰毛
    # 2026-09-05発覚: 宣伝用クロスワードを試作中、犬,猫ドメインから
    # 避妊・去勢手術等の語が出題されてしまった(id26のネコ好きサンプル
    # 作り直しで個別除外していたのと同じ語だが、ドメイン全体からの
    # 自動出題では防げていなかった)。動物の繁殖・去勢に関する手術用語
    # も同様にクロスワード出題から除外する(通常の単語学習では引き続き
    # 表示する)。
    12424,  # whelping 出産する(犬が子犬を産むこと)
    12430,  # spay 避妊手術をする(メスの生殖器を摘出する手術)
    12431,  # neuter 去勢手術をする(オスの生殖器を摘出する手術)
    12375,  # declawing 抜爪(爪の末節骨ごとの切除手術)
})
# UIの語数選択肢(views.js WORD_COUNT_OPTS)の最小値と揃える
# (2026-09-05ユーザー指摘: 以前は6だったため「3」「5」を選んでも実際は
# 6語にクランプされてしまっていた。生成に失敗した場合は7005のメッセージ
# で語数/フィルターの調整を案内する)。
MIN_PLACED_WORDS = 3
DEFAULT_WORD_COUNT = 10
MAX_WORD_COUNT = 50  # 2026-09-03ユーザー指示(従来20→50に拡大)

# 難易度連動スコア(2026-09-03ユーザー指示)。基礎点はTOEICレベル
# (words.level、app/routers/vocabulary.pyのLEVEL_ORDER参照)の1/10。
# TOEIC範囲を超える難易度(990+)は100点固定、範囲未満(300-)は10点固定、
# レベル未設定(範囲外)も含め、どのケースでも最低MIN_CORRECT_SCORE点は
# 保証する。
LEVEL_FIXED_SCORES = {"300-": 10, "990+": 100}
MIN_CORRECT_SCORE = 10


def _score_for_level(level: str | None) -> int:
    level = (level or "").strip()
    if level in LEVEL_FIXED_SCORES:
        return LEVEL_FIXED_SCORES[level]
    try:
        return max(int(level) // 10, MIN_CORRECT_SCORE)
    except ValueError:
        return MIN_CORRECT_SCORE  # レベル未設定(範囲外)は最低点


# 2026-09-05ユーザー指示: ヒントは使用回数によらず自由に使ってよい
# (使用ごとの減点は廃止)。「答えを見る」だけは特別枠で、率ではなく
# 即「加点なしで解けた」扱いにする(crossword_hint内で直接solved=True
# にする・下記HINT_TYPES参照)。
HINT_TYPES = {"audio", "first_letter", "last_letter", "japanese", "english",
              "reveal"}

# クリューモード(2026-09-03ユーザー指示で3種→4種、2026-09-05に
# always_both追加で5種、その後「ヒント制」廃止で4種に整理)。「無料で
# 常時開示するヒント種別」をモードごとに選べる。「本当のクロスワードに
# 近い」英英モード(例文ヒントを常時)・「ヒアリングで埋める」音声モード
# (発音再生だけ無料)・従来の日本語常時表示・両方常時表示してプレイ中に
# 切り替えられる両方モード、の4種(2026-09-05ユーザー指示: 「ヒント制」
# は先頭文字/末尾文字/発音等のヒントボタンが全モード共通で既にあるため
# 選択肢として不要、として削除)。無料開示された種別は、あらためて
# /hintで要求しても減点しない(既に見えているため)。
CLUE_MODES = ("always_ja", "always_english", "always_audio", "always_both")
# 値は常にタプル(1モードで複数種類が無料になるalways_bothに対応するため
# 2026-09-05に単一値からタプルへ変更)。
FREE_HINT_BY_MODE = {
    "always_ja": ("japanese",),
    "always_english": ("english",),
    "always_audio": ("audio",),
    "always_both": ("japanese", "english"),
}

# クリューモードごとの最終スコア倍率(2026-09-05ユーザー指示)。「ヒントの
# 難易度」は独立した設定ではなく、クリューモード=最初から無料で見える
# ヒントの手厚さそのものを指す、との整理に基づく。日本語訳が常に見える
# always_jaが最も易しいため減点(0.8倍)、英英/音声は等倍。
# always_bothは日本語訳・英語ヒントの両方が常に見え、always_ja単体より
# さらに手厚いため、ユーザー指示の「点数は-10%」に基づき0.9倍にする
# (0.8倍のalways_jaより甘い設定に見えるが、これはユーザーの明示的な
# 指示値をそのまま採用したもの)。ヒント自体(先頭文字/末尾文字/発音/
# 答えを見る等)は何回使ってもこの倍率自体は変わらない
# (使用回数による追加減点は廃止済み)。
CLUE_MODE_SCORE_MULTIPLIER = {
    "always_ja": 0.8,
    "always_english": 1.0,
    "always_audio": 1.0,
    "always_both": 0.9,
}

# 部分正解の開示(2026-09-03ユーザー提起)。当てずっぽう連打で少しずつ
# 正解を割り出す抜け道を防ぐため、外れた回答ごとに試行回数を記録し、
# 上限を超えたら0点でギブアップ扱いにする(先頭文字だけ合わせ続ける
# ような単純な当てずっぽうを封じる狙い)。
# 2026-09-05ユーザー要望「難易度低なら50%一致で開示」→同日さらに
# 「低40%・中60%」に調整。旧来は全員一律0.8だったが、下記の一致率
# 算出をdifflibベースの整列判定に変更した(1文字抜け/余分で全体が
# ズレても一致した部分は一致とみなせるようになった)ため、閾値も
# あわせて下げた。「高」は1.0のまま(=完全一致でない限り全開示は
# 起きない・実質先頭文字の開示のみに縮小)。
PARTIAL_MATCH_THRESHOLD_BY_DIFFICULTY = {
    "easy": 0.4, "normal": 0.6, "hard": 1.0,
}
ANSWER_DIFFICULTIES = tuple(PARTIAL_MATCH_THRESHOLD_BY_DIFFICULTY)
MAX_WRONG_ATTEMPTS = 5          # 1クリューあたりの不正解許容回数


def _guard_games_access(conn, uid: int) -> None:
    """カスタムクロスワード(分野/単語帳から選ぶ方)はログイン済みユーザー
    なら誰でも使える(2026-09-05〜一般公開。従来のテスト許可リスト/
    招待ユーザー限定`games_access.can_access`は廃止)。ゲストのみ拒否
    する(単語帳が使えないこと、生成のたびにAI原価が実際に発生し得る
    ことから、まずはサンプルのみで体験してもらう方針)。"""
    from ..services.auth import is_guest_user_id
    if is_guest_user_id(conn, uid):
        raise errors.http_error("3020")


def _owned_session(conn, session_id: int, uid: int) -> dict:
    row = conn.execute(
        "SELECT * FROM crossword_sessions WHERE id = ? AND user_id = ?",
        (session_id, uid),
    ).fetchone()
    if not row:
        raise errors.http_error("7001")
    row = dict(row)
    # ゲスト(__guest__)は全員user_idを共有するため、user_id一致だけでは
    # 別のゲストのセッションも「自分のもの」として通ってしまう
    # (2026-09-05サンプルクロスワードをゲストにも公開したことで表面化。
    # app/main.pyのミドルウェアが発行するguest_sid Cookieで個別に区別
    # する。ログイン済みユーザーはこのチェック自体をスキップ)。
    from ..services.auth import is_guest_user_id, current_guest_sid
    if is_guest_user_id(conn, uid):
        gsid = current_guest_sid()
        if not gsid or row.get("guest_sid") != gsid:
            raise errors.http_error("7001")
    return row


def _guard_session_access(conn, uid: int, session_id: int) -> None:
    """既存の_guard_games_access相当だが、対象セッションがサンプル
    (source_type='sample')の場合は誰でも(ゲスト含む)通す(2026-09-05・
    サンプルクロスワードは集客用に一般公開するため)。それ以外(分野/
    単語帳のカスタムゲーム)は従来通りテスト/招待/管理者限定のまま。"""
    row = conn.execute(
        "SELECT source_type FROM crossword_sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    if row and row["source_type"] == "sample":
        return
    _guard_games_access(conn, uid)


def _parse_detail(detail_json: str | None) -> dict:
    if not detail_json:
        return {}
    try:
        return json.loads(detail_json)
    except (ValueError, TypeError):
        return {}


def _extract_synonyms(detail_json: str | None) -> str:
    """words.detail(JSON文字列)から類義語(英単語)を取り出し、
    "obtainable, suitable"のようなカンマ区切り文字列にする。英英モード
    「語の説明」スタイル用(2026-09-03ユーザー指示: 「文章の穴埋め」
    (例文マスク)だけでなく、語の説明も選べるようにしたい)。新しい
    AI生成を追加せず、既存のdetail列(単語追加時にAIが生成し裏取り済み
    のデータ)を再利用する。synonymsの要素は基本{"word":..}形式だが、
    単語によっては単純な文字列のまま保存されているものもあり
    (2026-09-03発覚・AttributeErrorでクロスワード生成が500エラーに
    なっていた)、両方に対応する。"""
    raw = _parse_detail(detail_json).get("synonyms") or []
    words = [s.get("word", "") if isinstance(s, dict) else str(s)
             for s in raw]
    words = [w for w in words if w]
    return ", ".join(words[:3])


def _extract_explanation(detail_json: str | None) -> str:
    """words.detail(JSON文字列)から日本語の説明文を取り出す。日本語訳
    モードの「説明」スタイル用(2026-09-03ユーザー指示: 日本語訳だけで
    なく、説明になっているものも選べるといい)。"""
    return _parse_detail(detail_json).get("explanation", "") or ""


def _ja_core_term(japanese: str) -> str:
    """words.japanese(例: "フォノン(格子振動の量子)")から、括弧の注記や
    「・」区切りの別訳を除いた中心語(例: "フォノン")を取り出す。
    日本語穴埋め文のマスク対象を探すのに使う。"""
    core = re.split(r"[（(・/]", japanese or "")[0].strip()
    return core


def _masked_example_ja(example_ja: str, japanese: str) -> str:
    """日本語の例文中に単語の日本語訳(中心語)が含まれていれば、それを
    伏せ字にする(2026-09-03: 英語穴埋め(_masked_example)の日本語版)。
    見つからなければ空文字を返す(呼び出し側でフォールバック)。"""
    core = _ja_core_term(japanese)
    if not core or not example_ja or core not in example_ja:
        return ""
    return example_ja.replace(core, "○" * len(core))


_EN_TOKEN_RE = re.compile(r"[A-Za-z]{2,}")
# クリュー本文中のカタカナの連なり(2文字以上)を抜き出す用(2026-09-05・
# サンプルクロスワード作成時の照査で発覚: LEADの説明文「…動詞「導く」は
# /liːd/(リード)。」のように、訳語(japanese)側ではなく**クリュー本文
# そのもの**にカタカナ読みが混じって答えを割るケースがあった)。
_KATA_RUN_RE = re.compile(r"[ァ-ヴー]{2,}")


def _leaks_answer(text: str, english: str, japanese: str = "") -> bool:
    """ヒント文が答えをそのまま含んでいないか調べる(2026-09-03ユーザー
    指摘: lidarの説明文に「lidar は」、motorの訳語「モーター」がそのまま
    出ていた等、複数件報告された。2026-09-05サンプルクロスワード作成時の
    照査でさらに2パターン追加)。見るのは4種類:
    (1) 英語の綴りがそのまま含まれていないか(大小文字問わず)。
    (2) 単語の日本語訳の中心語(カタカナ読み等、_ja_core_term参照)が
    そのまま含まれていないか——ユーザー指摘の通り「単なるカタカナの
    置き換えも答えが入っているものとする」ため、英語綴りの一致だけでは
    不十分。
    (3) クリュー中の英単語(2文字以上)の一部が答えと重なっていないか
    (例: STOCKPOTの説明文に"(stock)"が混じっていたケース。答え全体の
    一致だけを見る(1)では素通りしてしまう)。
    (4) クリュー本文中のカタカナの連なりが答えの読みそのものになって
    いないか(訳語(japanese)フィールドではなく地の文にあるケース)。"""
    if not text:
        return False
    if english and english.lower() in text.lower():
        return True
    core = _ja_core_term(japanese) if japanese else ""
    if core and len(core) >= 2 and core in text:
        return True
    en_lower = english.lower() if english else ""
    if en_lower:
        for tok in _EN_TOKEN_RE.findall(text):
            t = tok.lower()
            if len(t) >= 4 and (t in en_lower or en_lower in t):
                return True
        for run in _KATA_RUN_RE.findall(text):
            if _is_transliteration_of(run, english):
                return True
    return False


def _fetch_candidate_words(
    conn, source_type: str, domains: list[str] | None, deck_id: int | None,
    level_min: str | None = None, level_max: str | None = None,
) -> list[dict]:
    """クロスワードの候補語(id/english/japanese/example/synonyms)を
    取得する。禁止用語は常に除外する(V1の簡略化・ユーザーのallow_banned
    に関わらず)。level_min/level_max はTOEIC目安の難易度絞り込み
    (2026-09-05ユーザー要望・分野選択時のみ有効、単語帳選択時は単語帳の
    中身をそのまま使うため無視する)。"""
    if source_type == "domain":
        if not domains:
            raise errors.http_error("7002", "分野を1つ以上選んでください。")
        from .vocabulary import BANNED_DOMAIN, _word_filter
        # _word_filterはdomain<>'禁止用語'を必ず付けるが、多義語の
        # word_domain_tags経由で禁止用語がタグ付けされているケースの
        # 防御線として、リクエスト自体からも明示的に除く(2026-09-05
        # fable監査指摘の念のための多重防御)。
        domains = [d for d in domains if d != BANNED_DOMAIN]
        if not domains:
            raise errors.http_error("7002", "分野を1つ以上選んでください。")
        where, params = _word_filter(
            ",".join(domains), None, level_min, level_max, False, False,
            None)
        clause = " WHERE " + " AND ".join(where)
    elif source_type == "deck":
        if not deck_id:
            raise errors.http_error("7002", "単語帳を選んでください。")
        owned = conn.execute(
            "SELECT 1 FROM decks WHERE id = ? AND user_id = ?",
            (deck_id, current_user_id()),
        ).fetchone()
        if not owned:
            raise errors.http_error("7001", "単語帳が見つかりません。")
        where = [
            "words.id IN (SELECT word_id FROM deck_words WHERE deck_id = ?)",
            banned_filter("words"),
        ]
        params = [deck_id]
        clause = " WHERE " + " AND ".join(where)
    else:
        raise errors.http_error("7002", "source_typeはdomainかdeckを指定してください。")

    rows = conn.execute(
        f"SELECT id, english, japanese, example, detail FROM words{clause}",
        params,
    ).fetchall()

    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        if r["id"] in CROSSWORD_SENSITIVE_WORD_IDS:
            continue
        normalized = _normalize_crossword_answer(r["english"])
        if normalized is None:
            continue
        english, article_dropped = normalized
        key = english
        if key in seen:
            continue
        seen.add(key)
        detail = _parse_detail(r["detail"])
        japanese = r["japanese"] or ""
        out.append({
            "id": r["id"], "english": english,
            "article_dropped": article_dropped,
            "japanese": japanese, "example": r["example"] or "",
            "synonyms": _extract_synonyms(r["detail"]),
            "explanation": _extract_explanation(r["detail"]),
            "crossword_hint_en": detail.get("crossword_hint_en", "") or "",
            "crossword_hint_ja": detail.get("crossword_hint_ja", "") or "",
            "crossword_fillblank_en": (
                detail.get("crossword_fillblank_en", "") or ""),
            "blank_ja": _masked_example_ja(
                detail.get("example_ja", "") or "", japanese),
            "_detail": detail,
        })
    return out


def _json_array(text: str) -> list:
    raw = text.strip()
    a, b = raw.find("["), raw.rfind("]")
    if a == -1 or b == -1:
        log.warning("crossword AI response had no JSON array: %.200s", raw)
        return []
    try:
        data = json.loads(raw[a:b + 1])
        if not isinstance(data, list):
            log.warning(
                "crossword AI response JSON was not a list: %.200s", raw)
            return []
        return data
    except (ValueError, TypeError):
        log.warning(
            "crossword AI response JSON parse failed: %.200s", raw,
            exc_info=True)
        return []


def _ensure_ai_hints(
    conn, pool: list[dict], cache_key: str, system: str,
) -> float:
    """クロスワードのヒント文を、未生成の語のみAIでバッチ生成しwords.
    detail[cache_key]にキャッシュする共通処理(2026-09-03)。一度生成した
    語は以降AIを呼び直さない(コスト削減・既存のdetail生成と同じ再利用
    方針)。英語ヒント(crossword_hint_en)・日本語ヒント(crossword_hint_ja)
    の両方で使う。AI無効時/失敗時は呼び出し元が別のフィールドへ
    フォールバックする。戻り値: 実際に発生したAI原価合計(USD、失敗した
    呼び出し分は0)。2026-09-05新課金式(1ゲームまとめて課金)の原価
    集計に使う(呼び出し元の_create_crossword_session参照)。"""
    from concurrent.futures import ThreadPoolExecutor
    from ..services import ai
    if not ai.is_enabled():
        return 0.0
    missing = [c for c in pool if not c.get(cache_key)]
    if not missing:
        return 0.0
    # 1回のAI呼び出しでmax_tokensを使い切って途中の語のヒントが欠ける
    # (JSON配列が閉じずに切れる)ことがあったため(2026-09-03ユーザー
    # 報告: 英英ハイブリッドで穴埋めのみになる語があった)、8語ずつの
    # チャンクに分けて呼ぶ(1語あたりのトークン余裕を確保)。
    # チャンクは並列で呼ぶ(2026-09-03発覚: 語数上限を50まで拡大した
    # ことで、順番に呼ぶと7チャンク×数秒=最大45秒もかかり、その間
    # DBの書き込みトランザクションを開いたままになる問題があったため。
    # DBへの書き込み(UPDATE)は全チャンクのAI応答が揃ってから、まとめて
    # 素早く行う=トランザクションを長く保持しない)。
    CHUNK = 8
    by_en = {c["english"]: c for c in missing}
    batches = [missing[i:i + CHUNK] for i in range(0, len(missing), CHUNK)]

    def _call(batch: list[dict]):
        listing = "\n".join(f"{c['english']} | {c['japanese']}" for c in batch)
        return ai.chat(
            system, f"単語(英語 | 日本語訳):\n{listing}",
            temperature=0.4, max_tokens=1200, feature="crossword_hint",
        )

    with ThreadPoolExecutor(max_workers=min(8, len(batches))) as pool_exec:
        results = list(pool_exec.map(_call, batches))

    total_cost = sum(r.cost_usd for r in results)
    for r in results:
        if not r.ok:
            # 2026-09-05: 失敗を握りつぶすとAI不調に誰も気づけないため、
            # 一般公開に伴いログに残す(該当語は_free_clue_text側の
            # フォールバックで引き続き別のヒントを表示する)。
            log.warning(
                "crossword AI hint batch failed (cache_key=%s): %s",
                cache_key, r.error)
            continue
        for item in _json_array(r.text):
            en = str(item.get("english", "")).strip().upper()
            hint = str(item.get("hint", "")).strip()
            c = by_en.get(en)
            if not c or not hint:
                continue
            c[cache_key] = hint
            detail = c.get("_detail") or {}
            detail[cache_key] = hint
            conn.execute(
                "UPDATE words SET detail = ? WHERE id = ?",
                (json.dumps(detail, ensure_ascii=False), c["id"]),
            )
    return total_cost


# 2026-09-03ユーザー指摘: gravity(物理)にseriousness(比喩義の類義語)が出る
# など、既存detail.synonyms/explanationの単純な再利用だと多義語で意味が
# ズレたり(英語)、専門語で説明文が単語自体の綴りを含んでしまったり
# (日本語、例: phononの説明文が「phononとは...」と書いてしまう)する
# 問題があった。日本語訳が示す意味に忠実で、単語自身(英語綴り・カタカナ
# 読みとも)を含まない、クロスワードのヒントとして適切な短文をAIに
# 作らせ、words.detailにキャッシュする。
_EN_HINT_SYSTEM = (
    "クロスワードパズルの英語ヒントを作ります。各単語について、"
    "その単語自身や単純な語形変化を使わずに、意味を的確に説明する"
    "短い英語の定義文(フレーズ可、1文以内)を作ってください。"
    "与えられた日本語訳が表す意味に忠実に(多義語でも他の意味を"
    "使わない)。平易な英単語を使うこと。"
    'JSON配列のみ出力: [{"english":"GRAVITY","hint":"the force that '
    'pulls objects toward the earth"}]'
)
_JA_HINT_SYSTEM = (
    "クロスワードパズルの日本語ヒントを作ります。各単語について、"
    "その単語自身の英語綴りや、それをそのままカタカナ読みしたものを"
    "使わずに、意味が分かる日本語の説明文を1文程度で作ってください。"
    "専門用語は身近な言葉に言い換えること。"
    'JSON配列のみ出力: [{"english":"PHONON","hint":"結晶がわずかに'
    '振動するときの、その振動エネルギーの最小単位を表す物理の言葉。"}]'
)


def _ensure_english_ai_hints(conn, pool: list[dict]) -> float:
    return _ensure_ai_hints(conn, pool, "crossword_hint_en", _EN_HINT_SYSTEM)


def _ensure_japanese_ai_hints(conn, pool: list[dict]) -> float:
    return _ensure_ai_hints(conn, pool, "crossword_hint_ja", _JA_HINT_SYSTEM)


# 穴埋め(fill_blank)用の専用例文(2026-09-05ユーザー指示「サンプルに
# 限らず、ヒントの穴埋め文はクロスワード用に動的に作っていい」)。
# 従来fill_blankはwords.example(語一覧・クイズ等でも共用する既存の
# 例文)が無い語を候補から除外するだけだったが、この専用例文を
# AI生成してキャッシュすることで、例文が無い語もfill_blankモードの
# 対象にできるようにする(words.exampleそのものは変更しない=他機能に
# 影響しない)。
_EN_FILLBLANK_SYSTEM = (
    "クロスワードパズルの穴埋めヒント用の英語例文を作ります。各単語に"
    "ついて、与えられた綴りと完全に同じ形(大文字/小文字の違いのみ許容。"
    "語形変化や活用・複数形化は不可)でその単語を1回だけ含む、短く"
    "自然な英語の例文を1文作ってください。与えられた日本語訳が表す"
    "意味に忠実に(多義語でも他の意味を使わない)。平易な単語・構文を"
    "使うこと。"
    'JSON配列のみ出力: [{"english":"GRAVITY","hint":"Gravity pulls '
    'objects toward the ground."}]'
)


def _ensure_english_fillblank_examples(conn, pool: list[dict]) -> float:
    return _ensure_ai_hints(
        conn, pool, "crossword_fillblank_en", _EN_FILLBLANK_SYSTEM)


ENGLISH_STYLES = ("fill_blank", "definition", "hybrid", "rich")
JAPANESE_STYLES = ("simple", "explanation", "hybrid", "rich")


class NewGamePayload(BaseModel):
    source_type: str  # 'domain' | 'deck'
    domains: list[str] | None = None
    deck_id: int | None = None
    # TOEIC目安の難易度絞り込み(2026-09-05・分野選択時のみ有効。
    # 値はapp/routers/vocabulary.pyのLEVEL_ORDERに従う文字列)。
    level_min: str | None = None
    level_max: str | None = None
    word_count: int = DEFAULT_WORD_COUNT
    # 「ヒントの難易度」はこのclue_mode自体が兼ねる(2026-09-05ユーザー
    # 指示・CLUE_MODE_SCORE_MULTIPLIER参照)。独立したhint_difficulty
    # フィールドは廃止した。
    clue_mode: str = "always_ja"
    # 英英モード(clue_mode='always_english')限定のサブ設定。
    # 'fill_blank'=例文の対象単語をマスクした穴埋め文/'definition'=
    # 類義語による語の説明/'hybrid'=両方(2026-09-03ユーザー指示
    # 「文章の穴埋めと説明のハイブリッドでもいい、それが本当の
    # クロスワードかも」)。他モードでは無視される。
    english_style: str = "fill_blank"
    # 日本語訳モード(clue_mode='always_ja')限定のサブ設定。
    # 'simple'=単語の日本語訳のみ/'explanation'=より詳しい日本語の説明文
    # (2026-09-03ユーザー指示「日本語訳だけでなく説明になっているものも
    # 選べるといい」)。他モードでは無視される。
    japanese_style: str = "simple"
    # パズルの詰め方(2026-09-05ユーザー要望「選択できるだけ面積減らして
    # クロスを多くするモード・普通モード選択できる」)。Trueで
    # crossword_gen.generate()のcompact=Trueを使い、交差数よりも面積の
    # 小ささを優先する。既定Falseは従来通り交差数優先。
    compact: bool = False
    # 不正解時の部分一致開示の甘さ(2026-09-05ユーザー要望)。
    # PARTIAL_MATCH_THRESHOLD_BY_DIFFICULTY参照。"normal"が既存動作
    # (旧・全員一律0.8)のまま。
    answer_difficulty: str = "normal"


# 安全なヒント文が1つも用意できなかった語用の汎用表示(2026-09-03)。
# 訳語(japanese)へフォールバックすると、訳語自体がカタカナ読みで
# 答えを割ってしまう語がある(例: motor→モーター)ため、explanation/
# hybridスタイルでは訳語へフォールバックしない方針にした代わりに使う。
_HINT_UNAVAILABLE_JA = "(この語のヒント文を準備中です。他のヒントもお試しください)"


# カタカナ→ローマ字の簡易対応表(2026-09-05ユーザー指摘: 「インスリン」
# のように、単語の日本語訳が英語の発音をそのままカタカナ化しただけの
# 外来語だと、訳語を見せるだけで答え(英語綴り)がバレてしまう。
# _leaks_answerの中心語チェックは「ヒント文に訳語が紛れ込んでいないか」
# 用で、訳語そのものが答えを割っているかの判定はできないため、
# 簡易的な音韻類似度で判定する新しいチェックを追加する。完全な変換
# ルールではなく、比較用の大まかなローマ字化で十分(2文字の拗音・外来
# 音を先にマッチさせるため、キーの長い順に並べてある)。
_KATAKANA_ROMAJI = {
    "キャ": "kya", "キュ": "kyu", "キョ": "kyo",
    "ギャ": "gya", "ギュ": "gyu", "ギョ": "gyo",
    "シャ": "sha", "シュ": "shu", "ショ": "sho", "シェ": "she",
    "ジャ": "ja", "ジュ": "ju", "ジョ": "jo", "ジェ": "je",
    "チャ": "cha", "チュ": "chu", "チョ": "cho", "チェ": "che",
    "ニャ": "nya", "ニュ": "nyu", "ニョ": "nyo",
    "ヒャ": "hya", "ヒュ": "hyu", "ヒョ": "hyo",
    "ビャ": "bya", "ビュ": "byu", "ビョ": "byo",
    "ピャ": "pya", "ピュ": "pyu", "ピョ": "pyo",
    "ミャ": "mya", "ミュ": "myu", "ミョ": "myo",
    "リャ": "rya", "リュ": "ryu", "リョ": "ryo",
    "ティ": "ti", "ディ": "di", "デュ": "dyu", "トゥ": "tu", "ドゥ": "du",
    "ファ": "fa", "フィ": "fi", "フェ": "fe", "フォ": "fo", "フュ": "fyu",
    "ウィ": "wi", "ウェ": "we", "ウォ": "wo",
    "ヴァ": "va", "ヴィ": "vi", "ヴェ": "ve", "ヴォ": "vo",
    "ツァ": "tsa", "ツィ": "tsi", "ツェ": "tse", "ツォ": "tso",
    "ア": "a", "イ": "i", "ウ": "u", "エ": "e", "オ": "o",
    "カ": "ka", "キ": "ki", "ク": "ku", "ケ": "ke", "コ": "ko",
    "ガ": "ga", "ギ": "gi", "グ": "gu", "ゲ": "ge", "ゴ": "go",
    "サ": "sa", "シ": "shi", "ス": "su", "セ": "se", "ソ": "so",
    "ザ": "za", "ジ": "ji", "ズ": "zu", "ゼ": "ze", "ゾ": "zo",
    "タ": "ta", "チ": "chi", "ツ": "tsu", "テ": "te", "ト": "to",
    "ダ": "da", "ヂ": "ji", "ヅ": "zu", "デ": "de", "ド": "do",
    "ナ": "na", "ニ": "ni", "ヌ": "nu", "ネ": "ne", "ノ": "no",
    "ハ": "ha", "ヒ": "hi", "フ": "fu", "ヘ": "he", "ホ": "ho",
    "バ": "ba", "ビ": "bi", "ブ": "bu", "ベ": "be", "ボ": "bo",
    "パ": "pa", "ピ": "pi", "プ": "pu", "ペ": "pe", "ポ": "po",
    "マ": "ma", "ミ": "mi", "ム": "mu", "メ": "me", "モ": "mo",
    "ヤ": "ya", "ユ": "yu", "ヨ": "yo",
    "ラ": "ra", "リ": "ri", "ル": "ru", "レ": "re", "ロ": "ro",
    "ワ": "wa", "ヲ": "wo", "ン": "n", "ヴ": "vu",
    "ー": "", "ッ": "",  # 長音符・促音は比較用に単純化のため落とす
}
_KATAKANA_KEYS = sorted(_KATAKANA_ROMAJI, key=len, reverse=True)


def _katakana_to_romaji(text: str, long_vowel: str = "") -> str:
    """カタカナ文字列を比較用の大まかなローマ字に変換する(正確な発音
    規則ではなく、英単語との類似度判定に足りる程度の簡易変換)。
    ``long_vowel``: 長音符「ー」の変換先(既定は空=無視)。英語のr音消失
    (car→カー、door→ドア)により、英語のrが日本語では長音符になっている
    ことが多いため、long_vowel="r"で変換した版も別途比較に使う
    (2026-09-05サンプルクロスワード作成時の照査で追加。
    ショッピングカート→CARTのような一部一致の検出に必要だった)。"""
    table = _KATAKANA_ROMAJI if not long_vowel else {
        **_KATAKANA_ROMAJI, "ー": long_vowel}
    keys = _KATAKANA_KEYS if not long_vowel else sorted(
        table, key=len, reverse=True)
    out = []
    i = 0
    while i < len(text):
        for k in keys:
            if text.startswith(k, i):
                out.append(table[k])
                i += len(k)
                break
        else:
            i += 1  # カタカナ以外の文字はスキップ
    return "".join(out)


# 2026-09-05サンプルクロスワード作成時の照査で判明: 単純なローマ字の
# 文字列類似度(SequenceMatcher)だけでは「クロック→CLOCK(0.55)」
# 「リレー→RELAY(0.44)」のような明白なカタカナ読みを閾値0.6で取り
# こぼす。母音を落とした子音だけの「骨格」で比べると両方1.00で一致する
# ため、骨格比較を追加する。l/r・v/b・c/q/k・j/z・f/h・w/b・z/sは
# 日本語のカタカナ化で同じ音になりやすい組。
_CONS_MAP = str.maketrans({"l": "r", "v": "b", "c": "k", "q": "k",
                           "j": "z", "f": "h", "w": "b", "z": "s"})


def _normalize_en(s: str) -> str:
    """英語綴りをカタカナ読みに寄せる前処理。軟音のc(ce/ci/cy)はs音
    (concert→konsert≒コンサート)、xはks 2音(boxer→bokser≒ボクサー)。
    どちらも_CONS_MAPだけでは取りこぼす。"""
    s = s.lower()
    out = []
    for i, ch in enumerate(s):
        nxt = s[i + 1] if i + 1 < len(s) else ""
        if ch == "c" and nxt in "eiy":
            out.append("s")
        elif ch == "x":
            out.append("ks")
        else:
            out.append(ch)
    return "".join(out)


def _skeleton(s: str) -> str:
    """母音を落とした子音の骨格。重複除去は母音を落とす前に行う(後に
    すると「リレー」のrireがrr→rまで潰れてRELAYのrrと長さが合わなくなり
    検出漏れになる)。"""
    s = _normalize_en(s).translate(_CONS_MAP)
    dedup = []
    for ch in s:
        if dedup and dedup[-1] == ch:
            continue
        dedup.append(ch)
    return "".join(ch for ch in dedup if ch not in "aiueoy-'. ")


def _ja_segments(japanese: str) -> list[str]:
    """訳語を「・」「/」「、」「(…)」等で分割した全断片を返す。
    _ja_core_term は先頭の断片(中心語)しか見ないため、「中継局・
    レピータ」のように**2番目以降の断片が答えのカタカナ読み**になって
    いるケースを検出できない(2026-09-05サンプルクロスワード作成時の
    照査で発覚)。答えバレ判定はこちらで全断片を見る。"""
    parts = re.split(r"[（()）・/、,，\s]+", japanese or "")
    return [p.strip() for p in parts if p and p.strip()]


_TRANSLITERATION_RATIO_THRESHOLD = 0.50


def _seg_matches(romaji: str, target: str, ratio: float) -> bool:
    if not romaji or not target:
        return False
    if difflib.SequenceMatcher(None, romaji, target.lower()).ratio() >= ratio:
        return True
    ja_sk, en_sk = _skeleton(romaji), _skeleton(target)
    if not ja_sk or not en_sk:
        return False
    if len(ja_sk) >= 3 and len(en_sk) >= 3:
        return difflib.SequenceMatcher(None, ja_sk, en_sk).ratio() >= 0.75
    # 骨格が短い語は完全一致のみ認める(先頭一致まで認めると「カリッと
    # (kr) vs CRISPY(krsp)」のような誤検出が出る)。
    return len(ja_sk) >= 2 and ja_sk == en_sk


def _is_transliteration_of(japanese: str, english: str) -> bool:
    """単語の日本語訳(のいずれかの断片)が、英語の発音をそのままカタカナ
    化したもの(＝答えを直接バラす訳語)かどうかを判定する。2026-09-05
    サンプルクロスワード作成時の照査で、単純なローマ字類似度(閾値0.6)
    だけでは複数の実例(クロック→CLOCK、リレー→RELAY、コンサート→
    CONCERT、ボクサー→BOXER、ヒューズ→FUSE等)を取りこぼすことが判明
    したため、(a)ローマ字そのままの類似度(閾値を0.6→0.50に強化)、
    (b)母音を落とした子音骨格の一致、の2段構えに強化した。中継局・
    レピータのように2番目以降の断片が答えを割るケースに対応するため、
    訳語は_ja_segmentsで全断片に分けて見る。"""
    if not japanese or not english:
        return False
    prefixes = [english[:n] for n in range(4, len(english))]
    en_sk = _skeleton(english)
    for seg in _ja_segments(japanese):
        if len(seg) < 2:
            continue
        romaji = _katakana_to_romaji(seg)
        if not romaji:
            continue
        if _seg_matches(romaji, english, _TRANSLITERATION_RATIO_THRESHOLD):
            return True
        # 英語のr音消失(car→カー等)により、日本語では長音符になって
        # いることが多いパターン。骨格の完全一致だけを見る(緩めると
        # 「筐体・ケース→ENCLOSURE」のような誤検出が出る)。
        romaji_r = _katakana_to_romaji(seg, long_vowel="r")
        if len(en_sk) >= 3 and (en_sk in _skeleton(romaji_r)
                                 or en_sk in _skeleton(romaji)):
            # 「ショッピングカート」のように、長いカタカナ語の一部が
            # 答えそのものになっているケース(CART)。
            return True
        if _skeleton(romaji_r) == en_sk:
            return True
        # 答えの先頭部分(4文字以上)がそのままカタカナ化されているケース
        # (例: テキスト(和製英語)/教科書 → TEXTBOOK)。先頭一致は
        # ほぼ完全一致のみ認める(緩めるとサメ/SHARK、シマリス/
        # CHIPMUNKのような誤検出が大量に出る)。
        for p in prefixes:
            if _skeleton(romaji) == _skeleton(p):
                return True
            if difflib.SequenceMatcher(
                    None, romaji, p.lower()).ratio() >= 0.8:
                return True
    return False


_ARTICLE_NOTE = {"ja": "（回答は冠詞なしで）", "en": " (answer without the article)"}


def _with_article_note(text: str, src: dict, lang: str) -> str:
    """冠詞落とし(2026-09-05ユーザー指示)した語には、ヒント文に
    「回答は冠詞なしで」の注記を付ける(答えが冠詞抜きの綴りになって
    いることをプレイヤーに伝えるため)。"""
    if not src.get("article_dropped") or not text:
        return text
    return text + _ARTICLE_NOTE[lang]


def _free_clue_text(
    clue_mode: str, style: str, src: dict, english: str,
) -> str:
    """クリューモード+スタイルに応じた無料ヒント本文を組み立てる。"""
    if clue_mode == "always_ja":
        # crossword_hint_ja(AIが作成しキャッシュした、単語自身の英語綴り・
        # カタカナ読みを含まない説明文)を優先し、無ければ従来のexplanation
        # にフォールバックする(2026-09-03ユーザー指摘: 専門語で従来の
        # explanationが単語自体を含んでしまう(例: phononの説明文に
        # 「phononとは」)ことがあり、ヒントとして不適切だったため。
        # _ensure_japanese_ai_hints参照)。crossword_hint_jaが未生成の語
        # (AIの応答から漏れた等)でexplanationへフォールバックする際も、
        # answer(英語綴り)がそのまま含まれていれば使わない(2026-09-03
        # 追加報告: lidarの説明文に「lidar は」とそのまま書かれていた
        # ケースがあったため、安全側のフィルタを機械的にもかける)。
        hint_ja = src.get("crossword_hint_ja") or ""
        if _leaks_answer(hint_ja, english, src["japanese"]):
            hint_ja = ""
        old_explanation = src["explanation"] or ""
        if _leaks_answer(old_explanation, english, src["japanese"]):
            old_explanation = ""
        explanation = hint_ja or old_explanation
        # 2026-09-03追加報告: motorの訳語「モーター・原動機」のように、
        # 訳語自体が答えのカタカナ読みで答えを割ってしまう語がある
        # (_leaks_answerは英語綴りの直接一致しか検知できないため、
        # explanation/hybridの最終フォールバックとして訳語(japanese)を
        # 使うのはそもそも危険。安全なヒントが無い場合は訳語を出さず、
        # 汎用の準備中メッセージにする)。
        # 2026-09-05ユーザー指摘: 「インスリン」のように訳語自体が英語の
        # 発音をそのままカタカナ化した外来語だと、rich/simpleで訳語を
        # そのまま見せるだけで答え(英語綴り)がバレてしまう。上記の
        # motor(モーター)対策(_leaks_answer)は完全一致の文字列検索
        # だったが、こちらは音韻の類似度で判定する(_is_transliteration_of)。
        # 該当する場合は訳語を出さず、explanationへフォールバックする。
        # _is_transliteration_ofには訳語全体を渡す(内部で_ja_segmentsに
        # より「中継局・レピータ」のような2番目以降の断片も含めて全断片
        # をチェックする・サンプルクロスワード作成時の照査で発覚した
        # 見逃しパターンへの対応)。
        safe_japanese = (
            "" if _is_transliteration_of(src["japanese"], english)
            else src["japanese"]
        )
        if style == "explanation":
            return explanation or _HINT_UNAVAILABLE_JA
        if style == "rich":
            # 2026-09-05ユーザー要望「簡単なヒントは複数のヒントの組み
            # 合わせ」への対応。hybridと違いランダムに1つ選ぶのではなく、
            # 訳語+説明文を両方まとめて出す(いちばん手厚い=易しい表示)。
            if safe_japanese and explanation:
                return f"{safe_japanese}（{explanation}）"
            return safe_japanese or explanation or _HINT_UNAVAILABLE_JA
        if style == "hybrid":
            # 2026-09-03ユーザー指摘(実際の新聞クロスワードの例を提示):
            # 本物のクロスワードは「1つのクリューに穴埋め+意味の両方」
            # ではなく、クリューごとに「穴埋め派」と「意味・連想派」が
            # 混在する(例:「グリーンランドは世界最大の○○。」(穴埋め)と
            # 「アンマンを首都とする中東の国。」(説明のみ、穴埋めなし)が
            # 同じ盤面に混じる)。そのためhybridは両方を1文に結合するの
            # ではなく、クリューごとにどちらか一方をランダムに選ぶ
            # (以前の"／意味:"併記方式から変更)。選んだ方にデータが
            # 無ければもう一方にフォールバックし、両方無ければ準備中
            # メッセージにする(訳語へはフォールバックしない・上記理由)。
            use_explanation = random.random() < 0.5
            if use_explanation and explanation:
                return explanation
            return src["blank_ja"] or explanation or _HINT_UNAVAILABLE_JA
        # style == "simple"。訳語がそのまま答えのカタカナ化(上記参照)の
        # 場合は、explanationへフォールバックする(それも無ければ準備中
        # メッセージ・訳語のみモードでも答えを直接見せるよりはまし)。
        return safe_japanese or explanation or _HINT_UNAVAILABLE_JA
    if clue_mode == "always_english":
        blank = ""
        if src["example"]:
            blank = _masked_example(src["example"], english)
        elif src.get("crossword_fillblank_en"):
            # words.exampleが無い語向けの、クロスワード専用に動的生成
            # した例文(2026-09-05ユーザー指示・_ensure_english_
            # fillblank_examples参照)。AIが単語をそのままの形で含め
            # 忘れた場合、_masked_exampleは無置換のまま返す=答えが
            # そのまま見えてしまうため、置換できた(=マスクされた)場合
            # のみ採用する(念のための安全策)。
            fillblank_ex = src["crossword_fillblank_en"]
            masked = _masked_example(fillblank_ex, english)
            if masked != fillblank_ex:
                blank = masked
        # crossword_hint_en(AIが作成しキャッシュした、日本語訳の意味に
        # 忠実な短い定義文)を優先し、無ければ従来のsynonymsに
        # フォールバックする(2026-09-03ユーザー指摘: synonymsそのまま
        # だと多義語で意味がズレることがあるため。_ensure_english_ai_
        # hints参照)。念のため、どちらもanswer自体を含んでいれば使わない
        # (日本語版と同じ安全フィルタ)。
        hint_en = src.get("crossword_hint_en") or ""
        if _leaks_answer(hint_en, english):
            hint_en = ""
        synonyms = src["synonyms"] or ""
        if _leaks_answer(synonyms, english):
            synonyms = ""
        definition = hint_en or synonyms
        if style == "definition":
            return definition
        if style == "rich":
            # 日本語版rich(上記コメント参照)と同じ考え方で、穴埋め文+
            # 語の説明を両方まとめて出す(いちばん手厚い=易しい表示)。
            if blank and definition:
                return f"{blank} （{definition}）"
            return blank or definition
        if style == "hybrid":
            # 日本語版hybridと同じ理由(上記コメント参照)で、1文に結合
            # せずクリューごとにどちらか一方をランダムに選ぶ。
            use_definition = random.random() < 0.5
            if use_definition and definition:
                return definition
            return blank or definition
        return blank  # fill_blank
    return ""


def _create_crossword_session(
    conn, uid: int, source_type: str, domains: list[str] | None,
    deck_id: int | None, level_min: str | None, level_max: str | None,
    word_count: int, clue_mode: str, english_style: str,
    japanese_style: str, compact: bool = False,
    answer_difficulty: str = "normal",
) -> dict:
    """クロスワードセッションを1つ生成してDBへ保存し、フロント表示用の
    状態を返す共通処理(2026-09-05・従来crossword_new直書きだった処理を
    /restart(同じ設定で最初から作り直す)と共有できるよう切り出した)。"""
    candidates = _fetch_candidate_words(
        conn, source_type, domains, deck_id, level_min, level_max)
    # 選んだモード/スタイルの無料ヒントに必要なデータが無い語は
    # あらかじめ除外する(全クリューに無料ヒントが表示できるように)。
    # AI有効時は「語の説明」をその場で生成できるため、既存synonyms
    # の有無では絞り込まない(2026-09-03: synonymsだけに頼ると多義語
    # で意味がズレたヒントになる問題があったため、AIヒントを優先する
    # ようにした・_ensure_english_ai_hints参照)。
    from ..services import ai
    ai_can_define = ai.is_enabled()
    # 2026-09-05ユーザー要望「両方モード追加・ゲーム中に切替」対応。
    # always_bothは日本語訳/英語ヒントの両方を必要とするため、両方の
    # フィルタを順に適用する(=どちらの条件も満たす語だけが残る)。
    wants_ja = clue_mode in ("always_ja", "always_both")
    wants_en = clue_mode in ("always_english", "always_both")
    if wants_ja:
        if japanese_style == "explanation" and not ai_can_define:
            candidates = [c for c in candidates if c["explanation"]]
        elif japanese_style in ("hybrid", "rich") and not ai_can_define:
            # hybrid/rich: 穴埋め文・説明のどちらか一方でもあれば可
            # (richは訳語と組み合わせるだけなので、無くても訳語単体に
            # 自然にフォールバックできる・_free_clue_text参照)。
            candidates = [
                c for c in candidates
                if c["blank_ja"] or c["explanation"]]
    if wants_en:
        if english_style == "definition" and not ai_can_define:
            candidates = [c for c in candidates if c["synonyms"]]
        elif english_style == "fill_blank" and not ai_can_define:
            # AI無効時のみexample必須(2026-09-05ユーザー指示「穴埋め文は
            # クロスワード用に動的に作っていい」に伴い、AI有効時は
            # crossword_fillblank_enを動的生成して補うため、ここでは
            # 除外しない・下記_ensure_english_fillblank_examples参照)。
            candidates = [c for c in candidates if c["example"]]
        elif english_style in ("hybrid", "rich") and not ai_can_define:
            # hybrid/rich: 例文・類義語のどちらか一方でもあれば可
            candidates = [
                c for c in candidates if c["example"] or c["synonyms"]]
    if len(candidates) < MIN_PLACED_WORDS:
        raise errors.http_error(
            "7005",
            f"選んだ範囲に単語が{MIN_PLACED_WORDS}語未満しかありません。"
            "分野を増やす・単語帳を変える、またはレベル範囲を広げて"
            "ください。",
        )
    word_count = min(max(word_count, MIN_PLACED_WORDS), MAX_WORD_COUNT)
    random.shuffle(candidates)
    # 2026-09-03ユーザー指示「平均2以上、できれば3以上」への対応:
    # 目標語数ちょうどの候補ではなく、その3倍まで(上限は候補の全数)
    # をgenerate()に渡し、試行ごとに異なる組み合わせで交差数を探索
    # させる(crossword_gen.generate()のtarget_count参照)。
    oversample_n = min(len(candidates), word_count * 3)
    pool = candidates[:oversample_n]

    word_pairs = [(c["id"], c["english"]) for c in pool]
    puzzle = crossword_gen.generate(
        word_pairs, attempts=40, target_count=word_count,
        max_grid=crossword_gen.grid_size_for(word_count), compact=compact)
    if puzzle is None or len(puzzle.clues) < MIN_PLACED_WORDS:
        raise errors.http_error(
            "7005",
            "この単語の組み合わせではクロスワードを作れませんでした。"
            "語数を増やす(候補が増えて交差しやすくなります)・分野を"
            "増やす、またはレベル範囲を広げてみてください。",
        )

    # AI代の節約のため、実際にパズルへ配置された語だけにヒント生成を
    # 絞る(オーバーサンプルした候補全体ではなく)。
    placed_ids = {cl.word_id for cl in puzzle.clues}
    used_pool = [c for c in pool if c["id"] in placed_ids]
    ai_cost_total = 0.0
    if wants_en and english_style in ("definition", "hybrid", "rich"):
        ai_cost_total += _ensure_english_ai_hints(conn, used_pool)
    if wants_en and english_style == "fill_blank":
        # words.exampleが既にある語はAIを呼ばず流用する(コスト削減・
        # 2026-09-05ユーザー指示「穴埋め文はクロスワード用に動的に
        # 作っていい」の対象はexampleが無い語のみ)。
        needs_fillblank = [c for c in used_pool if not c["example"]]
        if needs_fillblank:
            ai_cost_total += _ensure_english_fillblank_examples(
                conn, needs_fillblank)
    if wants_ja and japanese_style in ("explanation", "hybrid", "rich"):
        ai_cost_total += _ensure_japanese_ai_hints(conn, used_pool)

    by_id = {c["id"]: c for c in used_pool}
    clues_full = []
    for cl in puzzle.clues:
        entry = {
            "number": cl.number, "direction": cl.direction,
            "row": cl.row, "col": cl.col, "length": cl.length,
            "word_id": cl.word_id, "english": cl.english,
        }
        if wants_ja or wants_en:
            src = by_id[cl.word_id]
            # always_bothは両方保存しておき、プレイ中にどちらを表示する
            # かはフロント側のトグルで切り替える(2026-09-05)。
            if wants_ja:
                entry["free_clue_ja"] = _with_article_note(
                    _free_clue_text(
                        "always_ja", japanese_style, src, cl.english),
                    src, "ja")
            if wants_en:
                entry["free_clue_en"] = _with_article_note(
                    _free_clue_text(
                        "always_english", english_style, src, cl.english),
                    src, "en")
        clues_full.append(entry)
    puzzle_json = json.dumps({
        "rows": puzzle.rows, "cols": puzzle.cols,
        "cells": sorted(list(puzzle.cells)),
        "clues": clues_full,
    })
    source_ref = (
        ",".join(domains or []) if source_type == "domain"
        else str(deck_id)
    )
    cur = conn.execute(
        "INSERT INTO crossword_sessions "
        "(user_id, source_type, source_ref, clue_mode, score_multiplier, "
        "word_count, english_style, japanese_style, level_min, level_max, "
        "compact, answer_difficulty, puzzle_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (uid, source_type, source_ref, clue_mode,
         CLUE_MODE_SCORE_MULTIPLIER[clue_mode], word_count, english_style,
         japanese_style, level_min, level_max, compact, answer_difficulty,
         puzzle_json),
    )
    session_id = cur.lastrowid
    _enforce_session_cap(conn, uid)
    # 2026-09-05新課金式: 呼び出し毎の自動課金(ai.py `_LUMP_SUM_FEATURES`
    # によりcrossword_hintは自動課金対象外)ではなく、このゲーム1回分の
    # AI原価合計(ai_cost_total、キャッシュ済みのみなら0)をまとめて課金
    # する。保存(ピン留め)の有無に関わらず、ゲームを作るたびに毎回課金
    # する(docs/COST_ESTIMATE.md §1.5「新課金式案」)。
    ai.charge_crossword_game(conn, uid, ai_cost_total)
    state = _session_state(conn, session_id, uid, by_id, clue_mode)
    # 希望語数より少なく配置された場合、原因と対策(分野を増やす等)を
    # 案内する(2026-09-03ユーザー指示「うまく作れない場合は分野を
    # 増やしてくださいとアドバイスする」)。候補語同士が交差しにくい
    # 組み合わせだと、MIN_PLACED_WORDS語以上は満たしていても希望語数を
    # 下回ることがあるため。
    if len(puzzle.clues) < word_count:
        state["notice"] = (
            f"{word_count}語を希望しましたが、単語同士がうまく交差"
            f"できず{len(puzzle.clues)}語だけ配置しました。分野を"
            f"複数選ぶ・単語帳を変える、または語数を減らすと、"
            f"希望語数に近づきやすくなります。"
        )
    return state


# 保存できるセッション数の上限(2026-09-05ユーザー要望)。課金ユーザー・
# 管理者は10件、それ以外(無料ユーザー)は直近1件のみ(=新しく作ると
# 前のものは消える)。ピン留め(pinned=1)したセッションは、課金ユーザーで
# ある間だけ上限のカウント対象・削除対象から除外する。
CW_SESSION_CAP_CHARGED = 10
CW_SESSION_CAP_FREE = 1


def _enforce_session_cap(conn, uid: int) -> None:
    """新規作成のたびに呼ぶ、保存件数の上限維持(2026-09-05)。
    fable監査で指摘の2点に対応:
    (1) 無料ユーザー(元課金ユーザーがダウングレードした場合を含む)は
        pinned状態に関わらず直近1件のみ残す(ピン留めは課金ユーザー限定
        機能のため、非課金になった時点で無制限保持の抜け道にしない)。
    (2) ピン留めできる件数自体もCW_SESSION_CAP_CHARGED件までに制限する
        (crossword_pinのガード参照。ここでは既存データの後始末として、
        万一上限を超えたピン留めが残っていても直近優先で切り詰める)。
    """
    from ..services.auth import is_charged_or_admin
    charged = is_charged_or_admin(conn, uid)
    # created_atが秒精度のため同時刻の同着がありうる。id DESCを副次
    # キーにして、作成直後の行を確実に「最新」扱いにする。
    order = "ORDER BY created_at DESC, id DESC"
    # サンプルクロスワード(source_type='sample')は別枠の上限・保持ルール
    # (CW_SAMPLE_PLAY_LIMIT_*/CW_SAMPLE_PIN_LIMIT_*)で管理するため、この
    # 関数(カスタムゲーム用)の対象からは常に除外する(2026-09-05・サンプル
    # 公開時に追加。除外しないと、この関数がuser_id一致だけで削除対象を
    # 選ぶため、カスタムゲームを作るたびに同じユーザーのサンプル履歴まで
    # 巻き込んで削除してしまう)。
    not_sample = "AND source_type != 'sample'"
    if not charged:
        rows = conn.execute(
            f"SELECT id FROM crossword_sessions WHERE user_id = ? "
            f"{not_sample} {order}",
            (uid,),
        ).fetchall()
        excess_ids = [r["id"] for r in rows[CW_SESSION_CAP_FREE:]]
    else:
        pinned_rows = conn.execute(
            f"SELECT id FROM crossword_sessions WHERE user_id = ? "
            f"AND pinned = 1 {not_sample} {order}", (uid,),
        ).fetchall()
        # ピン留め自体が上限を超えている分は、古い方から通常の削除対象
        # (pinned=0)に戻す(ピン留めは「消えない」約束なのでいきなり
        # 削除はせず、まず上限内の通常セッション扱いに落とす)。
        pinned_excess_ids = [r["id"] for r in pinned_rows[CW_SESSION_CAP_CHARGED:]]
        if pinned_excess_ids:
            ph = ",".join("?" * len(pinned_excess_ids))
            conn.execute(
                f"UPDATE crossword_sessions SET pinned = 0 "
                f"WHERE id IN ({ph})", pinned_excess_ids,
            )
        rows = conn.execute(
            f"SELECT id FROM crossword_sessions WHERE user_id = ? "
            f"AND pinned = 0 {not_sample} {order}", (uid,),
        ).fetchall()
        excess_ids = [r["id"] for r in rows[CW_SESSION_CAP_CHARGED:]]
    if excess_ids:
        ph = ",".join("?" * len(excess_ids))
        conn.execute(
            f"DELETE FROM crossword_sessions WHERE id IN ({ph})",
            excess_ids,
        )


# ============================================================
# サンプルクロスワード(2026-09-05・集客用の一般公開機能)
#
# 通常のクロスワード(分野/単語帳を自分で選ぶ)はテスト/招待/管理者限定の
# ままだが、こちらは事前に作り込んだ固定のパズル(crossword_samples)を
# 誰でも(ゲスト含む)遊べるようにする。パズル内容は全ユーザー共通の
# ため、AI代は初回作成時のみ(全ユーザー共有のsunkコスト)・都度課金は
# 発生しない。
#
# 階層別の制限(2026-09-05ユーザー指示):
#   ゲスト(未ログイン)   : 5個まで(異なるサンプル)プレイ可・保存不可
#   ログイン済み(無料)   : 20個までプレイ可・保存(ピン留め)5件まで
#   課金ユーザー・管理者 : プレイ数無制限・保存10件まで
# 「プレイ数」は異なるサンプルを試した数(=crossword_sample_playsの
# DISTINCT sample_id)。同じサンプルの再プレイ・作り直しは消費しない。
# ============================================================

CW_SAMPLE_PLAY_LIMIT_GUEST = 5
CW_SAMPLE_PLAY_LIMIT_FREE = 20
CW_SAMPLE_PIN_LIMIT_FREE = 5
CW_SAMPLE_PIN_LIMIT_CHARGED = CW_SESSION_CAP_CHARGED  # 10・既存の値を流用


def _sample_identity(conn, uid: int) -> tuple[bool, str]:
    """(is_guest, guest_sid)を返す。ゲストはuser_idを共有するため、
    プレイ数のカウントはguest_sidで行う(現在ログイン中ならguest_sidは
    常に空文字)。"""
    from ..services.auth import is_guest_user_id, current_guest_sid
    is_guest = is_guest_user_id(conn, uid)
    return is_guest, (current_guest_sid() if is_guest else "")


def _sample_play_count(conn, uid: int, is_guest: bool, gsid: str) -> int:
    if is_guest:
        if not gsid:
            return 0
        return conn.execute(
            "SELECT COUNT(DISTINCT sample_id) c FROM crossword_sample_plays "
            "WHERE guest_sid = ?", (gsid,),
        ).fetchone()["c"]
    return conn.execute(
        "SELECT COUNT(DISTINCT sample_id) c FROM crossword_sample_plays "
        "WHERE user_id = ? AND guest_sid = ''", (uid,),
    ).fetchone()["c"]


def _sample_already_played(
    conn, uid: int, is_guest: bool, gsid: str, sample_id: int,
) -> bool:
    if is_guest:
        if not gsid:
            return False
        return conn.execute(
            "SELECT 1 FROM crossword_sample_plays WHERE guest_sid = ? "
            "AND sample_id = ? LIMIT 1", (gsid, sample_id),
        ).fetchone() is not None
    return conn.execute(
        "SELECT 1 FROM crossword_sample_plays WHERE user_id = ? "
        "AND guest_sid = '' AND sample_id = ? LIMIT 1", (uid, sample_id),
    ).fetchone() is not None


def _start_sample_session(conn, uid: int, sample: dict) -> dict:
    """sample(crossword_samplesの1行)からセッションを1つ作る。プレイ数の
    上限判定込み(既にプレイ済みのサンプルなら無制限に作り直せる)。"""
    from ..services.auth import is_charged_or_admin

    is_guest, gsid = _sample_identity(conn, uid)
    charged = is_charged_or_admin(conn, uid)
    # 登録者限定サンプルはゲストに一覧までは見せるが、プレイは拒否する
    # (2026-09-05ユーザー指示「未登録でも一覧は見えるがプレイは登録者
    # 限定」)。crossword_samples.guest_playable=0のものが対象。
    if is_guest and not sample["guest_playable"]:
        raise errors.http_error("7006")
    already = _sample_already_played(conn, uid, is_guest, gsid, sample["id"])
    if not already and not charged:
        limit = (CW_SAMPLE_PLAY_LIMIT_GUEST if is_guest
                 else CW_SAMPLE_PLAY_LIMIT_FREE)
        if _sample_play_count(conn, uid, is_guest, gsid) >= limit:
            if is_guest:
                msg = (f"ゲストで試せるサンプルは{limit}個までです。"
                       "ログイン(無料)すると20個まで遊べるようになります。")
            else:
                msg = (f"無料で遊べるサンプルは{limit}個までです。"
                       "チャージすると無制限に遊べるようになります。")
            raise errors.http_error("7002", msg)
    cur = conn.execute(
        "INSERT INTO crossword_sessions "
        "(user_id, guest_sid, source_type, source_ref, clue_mode, "
        "score_multiplier, word_count, english_style, japanese_style, "
        "level_min, level_max, compact, answer_difficulty, puzzle_json) "
        "VALUES (?, ?, 'sample', ?, ?, 1.0, ?, ?, ?, ?, ?, ?, 'normal', ?)",
        (uid, gsid, str(sample["id"]), sample["clue_mode"],
         sample["word_count"], sample["english_style"],
         sample["japanese_style"], sample["level_min"], sample["level_max"],
         sample["compact"], sample["puzzle_json"]),
    )
    session_id = cur.lastrowid
    conn.execute(
        "INSERT INTO crossword_sample_plays "
        "(user_id, guest_sid, sample_id, session_id) VALUES (?, ?, ?, ?)",
        (uid, gsid, sample["id"], session_id),
    )
    return _session_state(conn, session_id, uid)


def _restart_sample_session(conn, uid: int, old: dict) -> dict:
    """サンプルは固定パズルなので「最初から」は同じ内容で進捗だけ
    リセットする(新しい配置を作り直すカスタムゲームとは異なる)。"""
    sample = conn.execute(
        "SELECT * FROM crossword_samples WHERE id = ? AND is_active = 1",
        (old["source_ref"],),
    ).fetchone()
    if not sample:
        raise errors.http_error("7001")
    return _start_sample_session(conn, uid, dict(sample))


@router.get("/crossword/samples")
def crossword_sample_list():
    """サンプル一覧+現在のユーザーのプレイ上限・消費状況(2026-09-05)。
    ゲスト含め誰でも呼べる(ガード無し)。"""
    uid = current_user_id()
    with db() as conn:
        from ..services.auth import is_charged_or_admin
        is_guest, gsid = _sample_identity(conn, uid)
        charged = is_charged_or_admin(conn, uid)
        play_limit = (
            None if charged
            else CW_SAMPLE_PLAY_LIMIT_GUEST if is_guest
            else CW_SAMPLE_PLAY_LIMIT_FREE
        )
        played = _sample_play_count(conn, uid, is_guest, gsid)
        rows = conn.execute(
            "SELECT id, title, description, domains, level_min, level_max, "
            "word_count, guest_playable FROM crossword_samples "
            "WHERE is_active = 1 ORDER BY sort_order, id",
        ).fetchall()
        samples = []
        for r in rows:
            d = dict(r)
            d["already_played"] = _sample_already_played(
                conn, uid, is_guest, gsid, r["id"])
            # ゲストには「登録者限定」であることを一覧の時点で伝える
            # (2026-09-05ユーザー指示「未登録でも一覧は見えるがプレイは
            # 登録者限定」)。ログイン済みユーザーには常にfalse(区別不要)。
            d["guest_locked"] = is_guest and not d["guest_playable"]
            samples.append(d)
        return {
            "samples": samples,
            "play_limit": play_limit,
            "played_count": played,
            "can_play_more": play_limit is None or played < play_limit,
            "tier": "charged" if charged else "guest" if is_guest else "free",
        }


@router.post("/crossword/samples/{sample_id}/start")
def crossword_sample_start(sample_id: int):
    uid = current_user_id()
    with db() as conn:
        sample = conn.execute(
            "SELECT * FROM crossword_samples WHERE id = ? AND is_active = 1",
            (sample_id,),
        ).fetchone()
        if not sample:
            raise errors.http_error("7001")
        return _start_sample_session(conn, uid, dict(sample))


@router.post("/crossword/new")
def crossword_new(payload: NewGamePayload):
    uid = current_user_id()
    if payload.clue_mode not in CLUE_MODES:
        raise errors.http_error("7002", "clue_modeが不正です。")
    if payload.english_style not in ENGLISH_STYLES:
        raise errors.http_error("7002", "english_styleが不正です。")
    if payload.japanese_style not in JAPANESE_STYLES:
        raise errors.http_error("7002", "japanese_styleが不正です。")
    if payload.answer_difficulty not in ANSWER_DIFFICULTIES:
        raise errors.http_error("7002", "answer_difficultyが不正です。")
    with db() as conn:
        _guard_games_access(conn, uid)
        return _create_crossword_session(
            conn, uid, payload.source_type, payload.domains,
            payload.deck_id, payload.level_min, payload.level_max,
            payload.word_count, payload.clue_mode, payload.english_style,
            payload.japanese_style, payload.compact,
            payload.answer_difficulty)


@router.post("/crossword/{session_id}/restart")
def crossword_restart(session_id: int):
    """既存(完了・進行中問わず)セッションと同じ設定で、新しいパズルを
    作り直す「最初から」用(2026-09-05ユーザー要望「クリアしたものも
    再開可能・最初からと、途中かを選べる」の「最初から」側)。"""
    uid = current_user_id()
    with db() as conn:
        _guard_session_access(conn, uid, session_id)
        old = _owned_session(conn, session_id, uid)
        if old["source_type"] == "sample":
            return _restart_sample_session(conn, uid, old)
        domains = (old["source_ref"].split(",") if old["source_ref"]
                   and old["source_type"] == "domain" else None)
        deck_id = (int(old["source_ref"])
                   if old["source_type"] == "deck" and old["source_ref"]
                   else None)
        return _create_crossword_session(
            conn, uid, old["source_type"], domains, deck_id,
            old["level_min"], old["level_max"], old["word_count"],
            old["clue_mode"], old["english_style"], old["japanese_style"],
            bool(old["compact"]),
            old["answer_difficulty"] or "normal")


class PinPayload(BaseModel):
    pinned: bool


@router.post("/crossword/{session_id}/pin")
def crossword_pin(session_id: int, payload: PinPayload):
    """セッションの保存(ピン留め)切り替え(2026-09-05ユーザー要望
    「課金ユーザーのみほぞんできる・チェックすると消去されないように
    する」)。カスタムゲームのピン留めは課金ユーザー・管理者限定(無料
    ユーザーは上限1件のため実質「保存」の意味を成さない・
    _enforce_session_cap参照)。サンプルクロスワード(2026-09-05)は
    別枠の緩い上限(ゲスト不可・無料ログイン5件・課金10件)。"""
    uid = current_user_id()
    with db() as conn:
        _guard_session_access(conn, uid, session_id)
        row = _owned_session(conn, session_id, uid)
        is_sample = row["source_type"] == "sample"
        from ..services.auth import is_charged_or_admin, is_guest_user_id
        charged = is_charged_or_admin(conn, uid)
        if payload.pinned:
            if is_sample:
                if is_guest_user_id(conn, uid):
                    raise errors.http_error(
                        "3016", "サンプルクロスワードの保存にはログイン"
                        "(無料の会員登録)が必要です。")
                cap = (CW_SAMPLE_PIN_LIMIT_CHARGED if charged
                       else CW_SAMPLE_PIN_LIMIT_FREE)
            else:
                if not charged:
                    raise errors.http_error(
                        "3016", "クロスワードの保存(ピン留め)は課金ユーザー"
                        "限定です。設定画面からチャージすると使えるように"
                        "なります。")
                cap = CW_SESSION_CAP_CHARGED
            # ピン留め自体の件数も上限までにする(2026-09-05fable監査
            # 指摘: 上限なしに保存できてしまう抜け穴の防止。サンプルと
            # カスタムゲームは別枠で数える)。
            source_filter = (
                "source_type = 'sample'" if is_sample
                else "source_type != 'sample'")
            pinned_count = conn.execute(
                "SELECT COUNT(*) c FROM crossword_sessions "
                f"WHERE user_id = ? AND pinned = 1 AND {source_filter}",
                (uid,),
            ).fetchone()["c"]
            if pinned_count >= cap:
                raise errors.http_error(
                    "7002", f"保存できるのは{cap}件までです。他の保存を"
                    "解除してからお試しください。")
        conn.execute(
            "UPDATE crossword_sessions SET pinned = ? WHERE id = ? "
            "AND user_id = ?",
            (1 if payload.pinned else 0, session_id, uid),
        )
        return {"ok": True, "pinned": payload.pinned}


def _session_state(
    conn, session_id: int, uid: int,
    by_id: dict[int, dict] | None = None, clue_mode: str | None = None,
) -> dict:
    """回答(answer)を含まない、フロント表示用のセッション状態を作る。"""
    row = _owned_session(conn, session_id, uid)
    puzzle = json.loads(row["puzzle_json"])
    progress = json.loads(row["progress_json"])
    clue_mode = clue_mode or row["clue_mode"]

    if by_id is None:
        ids = [c["word_id"] for c in puzzle["clues"]]
        ph = ",".join("?" * len(ids))
        wrows = conn.execute(
            f"SELECT id, japanese FROM words WHERE id IN ({ph})", ids,
        ).fetchall()
        by_id = {r["id"]: {"japanese": r["japanese"] or ""} for r in wrows}

    free_hint = FREE_HINT_BY_MODE.get(clue_mode, ())
    # 正解/ギブアップ済みの語は、タップで単語詳細(既存のshowWordDetail
    # モーダル)を開けるようにする(2026-09-03ユーザー要望「答えたら、
    # 答えた単語触ると詳細画面が出るといい」)。未正解の語の情報は
    # 一切含めない(答えを先に知られてしまうため)。
    done_ids = sorted({
        c["word_id"] for c in puzzle["clues"]
        if progress.get(f"{c['number']}-{c['direction']}", {}).get("solved")
        or progress.get(f"{c['number']}-{c['direction']}", {})
        .get("given_up")
    })
    word_info: dict[int, dict] = {}
    if done_ids:
        ph = ",".join("?" * len(done_ids))
        rows = conn.execute(
            f"SELECT id, japanese, level, example, detail FROM words "
            f"WHERE id IN ({ph})", done_ids,
        ).fetchall()
        for r in rows:
            word_info[r["id"]] = {
                "japanese": r["japanese"] or "", "level": r["level"] or "",
                "example": r["example"] or "",
                "has_detail": bool(r["detail"]),
            }

    revealed_cells: dict[str, str] = {}
    clues_out = []
    for c in puzzle["clues"]:
        key = f"{c['number']}-{c['direction']}"
        p = progress.get(key, {})
        clue_out = {
            "number": c["number"], "direction": c["direction"],
            "row": c["row"], "col": c["col"], "length": c["length"],
            "solved": bool(p.get("solved")),
            "given_up": bool(p.get("given_up")),
            "hints_used": p.get("hints_used", []),
            "wrong_attempts": p.get("wrong_attempts", 0),
        }
        # 生成時に選ばれたモード+スタイルのテキストをそのまま使う
        # (puzzle_json内にfree_clue_ja/enとして保存済み・crossword_new
        # の_free_clue_text参照。always_bothは両方入っており、フロント側
        # のトグルでどちらを表示するか選ぶ)。
        if "japanese" in free_hint:
            clue_out["free_clue_ja"] = c.get("free_clue_ja", "")
        if "english" in free_hint:
            clue_out["free_clue_en"] = c.get("free_clue_en", "")
        if c["word_id"] in word_info:
            clue_out["word_id"] = c["word_id"]
            clue_out["english"] = c["english"]
            clue_out["word_info"] = word_info[c["word_id"]]
        clues_out.append(clue_out)
        # 複合語の区切り"_"(2026-09-05ユーザー指示)は答えではなく構造上の
        # 区切りなので、未解答でも常に開示する(cwCatImageFor等と同様、
        # 答えを含まない情報のため安全)。
        for i, ch in enumerate(c["english"]):
            if ch == "_":
                r = c["row"] + (i if c["direction"] == "down" else 0)
                col = c["col"] + (i if c["direction"] == "across" else 0)
                revealed_cells[f"{r},{col}"] = "_"
        if p.get("solved") or p.get("given_up"):
            for i, ch in enumerate(c["english"]):
                r = c["row"] + (i if c["direction"] == "down" else 0)
                col = c["col"] + (i if c["direction"] == "across" else 0)
                revealed_cells[f"{r},{col}"] = ch
        else:
            # 部分正解の当てずっぽう連打対策(2026-09-03): 一度でも
            # 位置一致した文字は、以後の試行結果に関わらず開示済みの
            # ままにする(戻ることはない)。
            for i in p.get("revealed_positions", []):
                if i >= len(c["english"]):
                    continue
                r = c["row"] + (i if c["direction"] == "down" else 0)
                col = c["col"] + (i if c["direction"] == "across" else 0)
                revealed_cells[f"{r},{col}"] = c["english"][i]

    return {
        "session_id": session_id,
        "source_type": row["source_type"],
        "clue_mode": clue_mode,
        "score_multiplier": row["score_multiplier"],
        "status": row["status"],
        "score": row["score"],
        "grid": {"rows": puzzle["rows"], "cols": puzzle["cols"],
                 "cells": puzzle["cells"]},
        "clues": clues_out,
        "revealed_cells": revealed_cells,
    }


@router.get("/crossword/sessions")
def crossword_sessions():
    """カスタムゲーム(分野/単語帳)の再開一覧。サンプル(source_type=
    'sample')はここには含めない(2026-09-05・専用のGET /crossword/samples
    に「プレイ済み」表示+再プレイ導線があるため。混ぜると保存件数の
    説明文(カスタムゲーム用)と噛み合わなくなる)。"""
    uid = current_user_id()
    with db() as conn:
        _guard_games_access(conn, uid)
        rows = conn.execute(
            "SELECT id, source_type, source_ref, status, score, created_at, "
            "word_count, pinned FROM crossword_sessions WHERE user_id = ? "
            "AND source_type != 'sample' ORDER BY created_at DESC LIMIT 30",
            (uid,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.get("/crossword/{session_id}")
def crossword_get(session_id: int):
    uid = current_user_id()
    with db() as conn:
        _guard_session_access(conn, uid, session_id)
        return _session_state(conn, session_id, uid)



# 複合語の区切り判定用(2026-09-05ユーザー指示「半角/全角スペース・
# 半角/全角アンダースコア・区切りなし、どれでも一致するように」)。
_WORD_SEPARATOR_TRANS = str.maketrans("", "", " 　_＿")


def _strip_word_separators(text: str) -> str:
    return text.translate(_WORD_SEPARATOR_TRANS)


def _masked_example(example: str, english: str) -> str:
    """例文中の対象単語をアンダースコアでマスクする(英語ヒント用)。"""
    return re.sub(
        re.escape(english), "_" * len(english), example, flags=re.IGNORECASE)


def _find_clue(puzzle: dict, number: int, direction: str) -> dict | None:
    for c in puzzle["clues"]:
        if c["number"] == number and c["direction"] == direction:
            return c
    return None


class AnswerPayload(BaseModel):
    clue_number: int
    direction: str
    answer: str


@router.post("/crossword/{session_id}/answer")
def crossword_answer(session_id: int, payload: AnswerPayload):
    uid = current_user_id()
    with db() as conn:
        _guard_session_access(conn, uid, session_id)
        row = _owned_session(conn, session_id, uid)
        puzzle = json.loads(row["puzzle_json"])
        progress = json.loads(row["progress_json"])
        clue = _find_clue(puzzle, payload.clue_number, payload.direction)
        if clue is None:
            raise errors.http_error("7002", "存在しないクリューです。")
        key = f"{clue['number']}-{clue['direction']}"
        p = progress.setdefault(key, {
            "solved": False, "given_up": False, "hints_used": [],
            "revealed_positions": [], "wrong_attempts": 0,
        })
        # 複合語("_"区切り、2026-09-05)の正誤判定は、区切り文字の
        # 種類・有無を問わない(2026-09-05ユーザー指示「半角/全角の
        # スペース・アンダースコア、区切りなし、どれでも一致するように」)。
        # 部分一致(difflib)側は従来通りtarget(アンダースコア入り)を
        # そのまま使う("_"のマスは常時開示済みのため、そこが一致しなく
        # ても実害が無い)。
        answer = payload.answer.strip().upper()
        target = clue["english"]
        correct = _strip_word_separators(answer) == _strip_word_separators(
            target)
        result = {"correct": correct, "match_ratio": None,
                   "attempts_left": None, "forced_reveal": False}

        if correct and not p["solved"]:
            p["solved"] = True
            wrow = conn.execute(
                "SELECT level FROM words WHERE id = ?", (clue["word_id"],),
            ).fetchone()
            base = _score_for_level(wrow["level"] if wrow else None)
            # 2026-09-05ユーザー指示でヒント使用ごとの減点は廃止し、
            # クリューモード(=最初から出るヒントの手厚さ)で決まる倍率を
            # 最終スコアにかける方式に一本化(row["score_multiplier"]は
            # crossword_new作成時にCLUE_MODE_SCORE_MULTIPLIERから設定)。
            # ヒント自体は自由に使えるが、「答えを見る」だけは特別枠で
            # 加点なし(下のreveal分岐でp["solved"]=Trueかつscore未設定の
            # ままここへは来ないため、常に0点のまま)。
            gained = base * row["score_multiplier"]
            p["score"] = max(round(gained), 0)
            row["score"] += p["score"]
        elif not correct and not p["solved"] and not p["given_up"]:
            # 部分正解の開示(2026-09-03ユーザー提起): 一致率が高い
            # (PARTIAL_MATCH_THRESHOLD_BY_DIFFICULTY以上)なら一致した
            # 文字を全部、そうでなくても先頭文字だけ合っていればそこだけ
            # 開示する。ただし当てずっぽう連打(先頭文字だけ合わせ続ける等)
            # を防ぐため、不正解のたびに試行回数を数え、上限
            # (MAX_WRONG_ATTEMPTS)に達したら0点でギブアップ扱いにして
            # 答えを開示する。
            # 2026-09-05ユーザー指示: 単純な位置一致(answer[i]==target[i])
            # だと、1文字抜け/余分があるだけで以降の文字が全部ズレて
            # 「ほぼ合っているのに一致率が低く出る」問題があったため、
            # difflib(Ratcliff/Obershelp法)で整列した一致率に変更。
            # ずれを吸収しつつ、実際に一致したtarget側の位置だけを
            # 正確に特定できる(get_matching_blocksの.b/.sizeがtarget側の
            # 一致区間)。
            sm = difflib.SequenceMatcher(None, answer, target)
            ratio = sm.ratio()
            result["match_ratio"] = round(ratio, 2)
            revealed = set(p.get("revealed_positions", []))
            threshold = PARTIAL_MATCH_THRESHOLD_BY_DIFFICULTY.get(
                row["answer_difficulty"] or "normal", 0.8)
            if ratio >= threshold:
                for block in sm.get_matching_blocks():
                    for i in range(block.b, block.b + block.size):
                        revealed.add(i)
            elif answer and answer[0] == target[0]:
                revealed.add(0)
            p["revealed_positions"] = sorted(revealed)

            p["wrong_attempts"] = p.get("wrong_attempts", 0) + 1
            attempts_left = MAX_WRONG_ATTEMPTS - p["wrong_attempts"]
            result["attempts_left"] = max(attempts_left, 0)
            if p["wrong_attempts"] >= MAX_WRONG_ATTEMPTS:
                p["given_up"] = True
                result["forced_reveal"] = True

        conn.execute(
            "UPDATE crossword_sessions SET score = ?, progress_json = ? "
            "WHERE id = ?",
            (row["score"], json.dumps(progress), session_id),
        )
        if p.get("solved") or p.get("given_up"):
            _maybe_complete(conn, session_id, puzzle, progress, row["score"])

        state = _session_state(conn, session_id, uid)
        state.update(result)
        return state


class HintPayload(BaseModel):
    clue_number: int
    direction: str
    hint_type: str


@router.post("/crossword/{session_id}/hint")
def crossword_hint(session_id: int, payload: HintPayload):
    uid = current_user_id()
    if payload.hint_type not in HINT_TYPES:
        raise errors.http_error("7002", "hint_typeが不正です。")
    with db() as conn:
        _guard_session_access(conn, uid, session_id)
        row = _owned_session(conn, session_id, uid)
        puzzle = json.loads(row["puzzle_json"])
        progress = json.loads(row["progress_json"])
        clue = _find_clue(puzzle, payload.clue_number, payload.direction)
        if clue is None:
            raise errors.http_error("7002", "存在しないクリューです。")
        free_hint = FREE_HINT_BY_MODE.get(row["clue_mode"], ())
        if (payload.hint_type in free_hint
                and payload.hint_type in ("japanese", "english")):
            # 文章系(日本語・英語ヒント)は既にクリューとして常時表示
            # されているため、あらためて要求する意味が無い(always_bothは
            # 両方が対象)。音声だけは「常時無料だが表示ではなく再生」
            # なので、このガード対象外(下のコスト計算で0円扱いにする)。
            raise errors.http_error(
                "7002", "このモードでは既に表示されているヒントです。")
        key = f"{clue['number']}-{clue['direction']}"
        p = progress.setdefault(key, {"solved": False, "given_up": False,
                                       "hints_used": []})
        if payload.hint_type not in p["hints_used"]:
            p["hints_used"].append(payload.hint_type)
        # 先頭文字/末尾文字ヒントは、マス目にもそのまま反映する
        # (2026-09-05ユーザー要望「先頭文字を押下したらクロスワードの
        # 先頭を空けてしまっていい」)。不正解時の部分正解開示
        # (revealed_positions・crossword_answer参照)と同じ仕組みを流用し、
        # 一度開示した位置は答え直しても戻らない。
        if payload.hint_type in ("first_letter", "last_letter"):
            revealed = set(p.get("revealed_positions", []))
            revealed.add(0 if payload.hint_type == "first_letter"
                         else len(clue["english"]) - 1)
            p["revealed_positions"] = sorted(revealed)
        if payload.hint_type == "reveal" and not p["solved"]:
            # 全オープンは加点なしで即「解けた」扱いにする(ギブアップとは
            # 違い正答として記録・答えを開示する)。
            p["solved"] = True
            conn.execute(
                "UPDATE crossword_sessions SET progress_json = ? WHERE id = ?",
                (json.dumps(progress), session_id),
            )
            _maybe_complete(conn, session_id, puzzle, progress, row["score"])
        else:
            conn.execute(
                "UPDATE crossword_sessions SET progress_json = ? WHERE id = ?",
                (json.dumps(progress), session_id),
            )

        wrow = conn.execute(
            "SELECT japanese, example FROM words WHERE id = ?",
            (clue["word_id"],),
        ).fetchone()
        content: dict = {}
        if payload.hint_type == "audio":
            content = {"word_id": clue["word_id"]}
        elif payload.hint_type == "first_letter":
            content = {"letter": clue["english"][0]}
        elif payload.hint_type == "last_letter":
            content = {"letter": clue["english"][-1]}
        elif payload.hint_type == "japanese":
            content = {"japanese": wrow["japanese"] if wrow else ""}
        elif payload.hint_type == "english":
            example = (wrow["example"] if wrow else "") or ""
            if not example:
                raise errors.http_error("7001", "この語には例文がありません。")
            content = {"example": _masked_example(example, clue["english"])}
        elif payload.hint_type == "reveal":
            content = {"answer": clue["english"]}

        return {"hint_type": payload.hint_type, **content,
                "session": _session_state(conn, session_id, uid)}


class GiveUpPayload(BaseModel):
    clue_number: int
    direction: str


@router.post("/crossword/{session_id}/giveup")
def crossword_giveup(session_id: int, payload: GiveUpPayload):
    uid = current_user_id()
    with db() as conn:
        _guard_session_access(conn, uid, session_id)
        row = _owned_session(conn, session_id, uid)
        puzzle = json.loads(row["puzzle_json"])
        progress = json.loads(row["progress_json"])
        clue = _find_clue(puzzle, payload.clue_number, payload.direction)
        if clue is None:
            raise errors.http_error("7002", "存在しないクリューです。")
        key = f"{clue['number']}-{clue['direction']}"
        p = progress.setdefault(key, {"solved": False, "given_up": False,
                                       "hints_used": []})
        if not p["solved"]:
            p["given_up"] = True
            conn.execute(
                "UPDATE crossword_sessions SET progress_json = ? WHERE id = ?",
                (json.dumps(progress), session_id),
            )
            _maybe_complete(conn, session_id, puzzle, progress, row["score"])
        return _session_state(conn, session_id, uid)


@router.post("/crossword/{session_id}/giveup-all")
def crossword_giveup_all(session_id: int):
    """全クリューを一括ギブアップする(2026-09-03ユーザー要望「全部答え
    オープンボタン」)。テスト中の便利機能として、1クリューずつ
    ギブアップを繰り返す手間を省く(未正解の全クリューを1回のDB更新で
    given_up扱いにする・スコアは変えない=既存の単一ギブアップと同じ
    仕様)。"""
    uid = current_user_id()
    with db() as conn:
        _guard_session_access(conn, uid, session_id)
        row = _owned_session(conn, session_id, uid)
        puzzle = json.loads(row["puzzle_json"])
        progress = json.loads(row["progress_json"])
        for clue in puzzle["clues"]:
            key = f"{clue['number']}-{clue['direction']}"
            p = progress.setdefault(
                key, {"solved": False, "given_up": False, "hints_used": []})
            if not p["solved"]:
                p["given_up"] = True
        conn.execute(
            "UPDATE crossword_sessions SET progress_json = ? WHERE id = ?",
            (json.dumps(progress), session_id),
        )
        _maybe_complete(conn, session_id, puzzle, progress, row["score"])
        return _session_state(conn, session_id, uid)


def _maybe_complete(conn, session_id: int, puzzle: dict, progress: dict,
                     score: int) -> None:
    all_done = all(
        progress.get(f"{c['number']}-{c['direction']}", {}).get("solved")
        or progress.get(f"{c['number']}-{c['direction']}", {}).get("given_up")
        for c in puzzle["clues"]
    )
    if all_done:
        conn.execute(
            "UPDATE crossword_sessions SET status = 'completed', "
            "completed_at = datetime('now') WHERE id = ?",
            (session_id,),
        )
