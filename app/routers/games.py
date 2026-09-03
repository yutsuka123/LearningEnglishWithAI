"""ゲーム機能のAPI(2026-09-03・第一弾はクロスワード)。

テストユーザー+管理者限定公開(`app/services/games_access.py`)。ログイン
ユーザーのみ(ゲスト不可・auth依存のcurrent_user_idが未ログインでは
使えないため自然に弾かれる)。設計の詳細・スコア/ヒント仕様は
docs/TODO.md および実装時のプランドキュメント参照。
"""

from __future__ import annotations

import json
import random
import re

from fastapi import APIRouter
from pydantic import BaseModel

from ..database import db
from ..services import crossword_gen, errors, games_access
from ..services.auth import current_user_id, get_user
from ..services.spaced_repetition import banned_filter

router = APIRouter(prefix="/api/games", tags=["games"])

_WORD_RE = re.compile(r"^[A-Za-z]+$")
MIN_WORD_LEN, MAX_WORD_LEN = 3, 10
MIN_PLACED_WORDS = 6
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


# ヒント1つ使うごとに基礎点の10%を減点する(2026-09-03ユーザー指示)。
# 「全オープン」は特別枠で、率ではなく即「加点なしで解けた」扱いにする
# (crossword_hint内で直接solved=Trueにする・下記HINT_TYPES参照)。
HINT_PCT = 0.10
HINT_TYPES = {"audio", "first_letter", "last_letter", "japanese", "english",
              "reveal"}

# クリューモード(2026-09-03ユーザー指示で3種→4種に拡張)。「無料で常時
# 開示するヒント種別」をモードごとに選べる。「本当のクロスワードに近い」
# 英英モード(例文ヒントを常時)・「ヒアリングで埋める」音声モード
# (発音再生だけ無料)・従来の日本語常時表示・何も無料開示しない
# ヒント制、の4種。無料開示された種別は、あらためて/hintで要求しても
# 減点しない(既に見えているため)。
CLUE_MODES = ("always_ja", "always_english", "always_audio", "hints_only")
FREE_HINT_BY_MODE = {
    "always_ja": "japanese",
    "always_english": "english",
    "always_audio": "audio",
    "hints_only": None,
}

# 部分正解の開示(2026-09-03ユーザー提起)。当てずっぽう連打で少しずつ
# 正解を割り出す抜け道を防ぐため、外れた回答ごとに試行回数を記録し、
# 上限を超えたら0点でギブアップ扱いにする(先頭文字だけ合わせ続ける
# ような単純な当てずっぽうを封じる狙い)。
PARTIAL_MATCH_THRESHOLD = 0.8   # 位置一致率がこれ以上なら一致箇所を全開示
MAX_WRONG_ATTEMPTS = 5          # 1クリューあたりの不正解許容回数


def _guard_games_access(conn, uid: int) -> None:
    """管理者 or ゲームのテスト許可リストに載っているユーザーのみ通す。
    それ以外は機能自体が存在しないかのような汎用メッセージ(3020)で403。"""
    me = get_user(conn, uid)
    is_admin = bool(me and me.get("role") == "admin")
    is_test_allowed = bool(
        me and games_access.is_test_allowed(me.get("username", "")))
    if not (is_admin or is_test_allowed):
        raise errors.http_error("3020")


def _owned_session(conn, session_id: int, uid: int) -> dict:
    row = conn.execute(
        "SELECT * FROM crossword_sessions WHERE id = ? AND user_id = ?",
        (session_id, uid),
    ).fetchone()
    if not row:
        raise errors.http_error("7001")
    return dict(row)


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


def _leaks_answer(text: str, english: str, japanese: str = "") -> bool:
    """ヒント文が答えをそのまま含んでいないか調べる(2026-09-03ユーザー
    指摘: lidarの説明文に「lidar は」、motorの訳語「モーター」がそのまま
    出ていた等、複数件報告された)。2種類を見る:
    (1) 英語の綴りがそのまま含まれていないか(大小文字問わず)。
    (2) 単語の日本語訳の中心語(カタカナ読み等、_ja_core_term参照)が
    そのまま含まれていないか——ユーザー指摘の通り「単なるカタカナの
    置き換えも答えが入っているものとする」ため、英語綴りの一致だけでは
    不十分。"""
    if not text:
        return False
    if english and english.lower() in text.lower():
        return True
    core = _ja_core_term(japanese) if japanese else ""
    if core and len(core) >= 2 and core in text:
        return True
    return False


def _fetch_candidate_words(
    conn, source_type: str, domains: list[str] | None, deck_id: int | None,
) -> list[dict]:
    """クロスワードの候補語(id/english/japanese/example/synonyms)を
    取得する。禁止用語は常に除外する(V1の簡略化・ユーザーのallow_banned
    に関わらず)。"""
    if source_type == "domain":
        if not domains:
            raise errors.http_error("7002", "分野を1つ以上選んでください。")
        from .vocabulary import _word_filter
        where, params = _word_filter(
            ",".join(domains), None, None, None, False, False, None)
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
        english = (r["english"] or "").strip()
        if not _WORD_RE.match(english):
            continue
        if not (MIN_WORD_LEN <= len(english) <= MAX_WORD_LEN):
            continue
        key = english.upper()
        if key in seen:
            continue
        seen.add(key)
        detail = _parse_detail(r["detail"])
        japanese = r["japanese"] or ""
        out.append({
            "id": r["id"], "english": english.upper(),
            "japanese": japanese, "example": r["example"] or "",
            "synonyms": _extract_synonyms(r["detail"]),
            "explanation": _extract_explanation(r["detail"]),
            "crossword_hint_en": detail.get("crossword_hint_en", "") or "",
            "crossword_hint_ja": detail.get("crossword_hint_ja", "") or "",
            "blank_ja": _masked_example_ja(
                detail.get("example_ja", "") or "", japanese),
            "_detail": detail,
        })
    return out


def _json_array(text: str) -> list:
    raw = text.strip()
    a, b = raw.find("["), raw.rfind("]")
    if a == -1 or b == -1:
        return []
    try:
        data = json.loads(raw[a:b + 1])
        return data if isinstance(data, list) else []
    except (ValueError, TypeError):
        return []


def _ensure_ai_hints(
    conn, pool: list[dict], cache_key: str, system: str,
) -> None:
    """クロスワードのヒント文を、未生成の語のみAIでバッチ生成しwords.
    detail[cache_key]にキャッシュする共通処理(2026-09-03)。一度生成した
    語は以降AIを呼び直さない(コスト削減・既存のdetail生成と同じ再利用
    方針)。英語ヒント(crossword_hint_en)・日本語ヒント(crossword_hint_ja)
    の両方で使う。AI無効時/失敗時は呼び出し元が別のフィールドへ
    フォールバックする。"""
    from concurrent.futures import ThreadPoolExecutor
    from ..services import ai
    if not ai.is_enabled():
        return
    missing = [c for c in pool if not c.get(cache_key)]
    if not missing:
        return
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

    for r in results:
        if not r.ok:
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


def _ensure_english_ai_hints(conn, pool: list[dict]) -> None:
    _ensure_ai_hints(conn, pool, "crossword_hint_en", _EN_HINT_SYSTEM)


def _ensure_japanese_ai_hints(conn, pool: list[dict]) -> None:
    _ensure_ai_hints(conn, pool, "crossword_hint_ja", _JA_HINT_SYSTEM)


ENGLISH_STYLES = ("fill_blank", "definition", "hybrid")
JAPANESE_STYLES = ("simple", "explanation", "hybrid")


class NewGamePayload(BaseModel):
    source_type: str  # 'domain' | 'deck'
    domains: list[str] | None = None
    deck_id: int | None = None
    word_count: int = DEFAULT_WORD_COUNT
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


# 安全なヒント文が1つも用意できなかった語用の汎用表示(2026-09-03)。
# 訳語(japanese)へフォールバックすると、訳語自体がカタカナ読みで
# 答えを割ってしまう語がある(例: motor→モーター)ため、explanation/
# hybridスタイルでは訳語へフォールバックしない方針にした代わりに使う。
_HINT_UNAVAILABLE_JA = "(この語のヒント文を準備中です。他のヒントもお試しください)"


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
        if style == "explanation":
            return explanation or _HINT_UNAVAILABLE_JA
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
        return src["japanese"]
    if clue_mode == "always_english":
        blank = ""
        if src["example"]:
            blank = _masked_example(src["example"], english)
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
        if style == "hybrid":
            # 日本語版hybridと同じ理由(上記コメント参照)で、1文に結合
            # せずクリューごとにどちらか一方をランダムに選ぶ。
            use_definition = random.random() < 0.5
            if use_definition and definition:
                return definition
            return blank or definition
        return blank  # fill_blank
    return ""


@router.post("/crossword/new")
def crossword_new(payload: NewGamePayload):
    uid = current_user_id()
    if payload.clue_mode not in CLUE_MODES:
        raise errors.http_error("7002", "clue_modeが不正です。")
    if payload.english_style not in ENGLISH_STYLES:
        raise errors.http_error("7002", "english_styleが不正です。")
    if payload.japanese_style not in JAPANESE_STYLES:
        raise errors.http_error("7002", "japanese_styleが不正です。")
    with db() as conn:
        _guard_games_access(conn, uid)
        candidates = _fetch_candidate_words(
            conn, payload.source_type, payload.domains, payload.deck_id)
        # 選んだモード/スタイルの無料ヒントに必要なデータが無い語は
        # あらかじめ除外する(全クリューに無料ヒントが表示できるように)。
        # AI有効時は「語の説明」をその場で生成できるため、既存synonyms
        # の有無では絞り込まない(2026-09-03: synonymsだけに頼ると多義語
        # で意味がズレたヒントになる問題があったため、AIヒントを優先する
        # ようにした・_ensure_english_ai_hints参照)。
        from ..services import ai
        ai_can_define = ai.is_enabled()
        if payload.clue_mode == "always_ja":
            if payload.japanese_style == "explanation" and not ai_can_define:
                candidates = [c for c in candidates if c["explanation"]]
            elif payload.japanese_style == "hybrid" and not ai_can_define:
                # hybrid: 穴埋め文・説明のどちらか一方でもあれば可
                candidates = [
                    c for c in candidates
                    if c["blank_ja"] or c["explanation"]]
        elif payload.clue_mode == "always_english":
            if payload.english_style == "definition" and not ai_can_define:
                candidates = [c for c in candidates if c["synonyms"]]
            elif payload.english_style == "fill_blank":
                candidates = [c for c in candidates if c["example"]]
            elif payload.english_style == "hybrid" and not ai_can_define:
                # hybrid: 例文・類義語のどちらか一方でもあれば可
                candidates = [
                    c for c in candidates if c["example"] or c["synonyms"]]
        if len(candidates) < MIN_PLACED_WORDS:
            raise errors.http_error("7005")
        word_count = min(
            max(payload.word_count, MIN_PLACED_WORDS), MAX_WORD_COUNT)
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
            max_grid=crossword_gen.grid_size_for(word_count))
        if puzzle is None or len(puzzle.clues) < MIN_PLACED_WORDS:
            raise errors.http_error("7005")

        # AI代の節約のため、実際にパズルへ配置された語だけにヒント生成を
        # 絞る(オーバーサンプルした候補全体ではなく)。
        placed_ids = {cl.word_id for cl in puzzle.clues}
        used_pool = [c for c in pool if c["id"] in placed_ids]
        if (payload.clue_mode == "always_english"
                and payload.english_style in ("definition", "hybrid")):
            _ensure_english_ai_hints(conn, used_pool)
        elif (payload.clue_mode == "always_ja"
                and payload.japanese_style in ("explanation", "hybrid")):
            _ensure_japanese_ai_hints(conn, used_pool)

        by_id = {c["id"]: c for c in used_pool}
        clues_full = []
        for cl in puzzle.clues:
            entry = {
                "number": cl.number, "direction": cl.direction,
                "row": cl.row, "col": cl.col, "length": cl.length,
                "word_id": cl.word_id, "english": cl.english,
            }
            if payload.clue_mode in ("always_ja", "always_english"):
                src = by_id[cl.word_id]
                style = (payload.japanese_style if payload.clue_mode ==
                         "always_ja" else payload.english_style)
                entry["free_clue"] = _free_clue_text(
                    payload.clue_mode, style, src, cl.english)
            clues_full.append(entry)
        puzzle_json = json.dumps({
            "rows": puzzle.rows, "cols": puzzle.cols,
            "cells": sorted(list(puzzle.cells)),
            "clues": clues_full,
        })
        source_ref = (
            ",".join(payload.domains or []) if payload.source_type == "domain"
            else str(payload.deck_id)
        )
        cur = conn.execute(
            "INSERT INTO crossword_sessions "
            "(user_id, source_type, source_ref, clue_mode, puzzle_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (uid, payload.source_type, source_ref, payload.clue_mode,
             puzzle_json),
        )
        session_id = cur.lastrowid
        state = _session_state(
            conn, session_id, uid, by_id, payload.clue_mode)
        # 希望語数より少なく配置された場合、原因と対策(分野を増やす等)を
        # 案内する(2026-09-03ユーザー指示「うまく作れない場合は分野を
        # 増やしてくださいとアドバイスする」)。候補語同士が交差しにくい
        # 組み合わせだと、6語以上(MIN_PLACED_WORDS)は満たしていても
        # 希望語数を下回ることがあるため。
        if len(puzzle.clues) < word_count:
            state["notice"] = (
                f"{word_count}語を希望しましたが、単語同士がうまく交差"
                f"できず{len(puzzle.clues)}語だけ配置しました。分野を"
                f"複数選ぶ・単語帳を変える、または語数を減らすと、"
                f"希望語数に近づきやすくなります。"
            )
        return state


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

    free_hint = FREE_HINT_BY_MODE.get(clue_mode)
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
        if free_hint in ("japanese", "english"):
            # 生成時に選ばれたモード+スタイル(日本語訳/説明・穴埋め文/
            # 類義語説明/ハイブリッド)のテキストをそのまま使う
            # (puzzle_json内にfree_clueとして保存済み・crossword_new
            # の_free_clue_text参照)。
            clue_out["free_clue"] = c.get("free_clue", "")
        if c["word_id"] in word_info:
            clue_out["word_id"] = c["word_id"]
            clue_out["english"] = c["english"]
            clue_out["word_info"] = word_info[c["word_id"]]
        clues_out.append(clue_out)
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
        "clue_mode": clue_mode,
        "status": row["status"],
        "score": row["score"],
        "grid": {"rows": puzzle["rows"], "cols": puzzle["cols"],
                 "cells": puzzle["cells"]},
        "clues": clues_out,
        "revealed_cells": revealed_cells,
    }


@router.get("/crossword/sessions")
def crossword_sessions():
    uid = current_user_id()
    with db() as conn:
        _guard_games_access(conn, uid)
        rows = conn.execute(
            "SELECT id, source_type, source_ref, status, score, created_at "
            "FROM crossword_sessions WHERE user_id = ? "
            "ORDER BY created_at DESC LIMIT 20",
            (uid,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.get("/crossword/{session_id}")
def crossword_get(session_id: int):
    uid = current_user_id()
    with db() as conn:
        _guard_games_access(conn, uid)
        return _session_state(conn, session_id, uid)


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
        _guard_games_access(conn, uid)
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
        answer = payload.answer.strip().upper()
        target = clue["english"]
        correct = answer == target
        result = {"correct": correct, "match_ratio": None,
                   "attempts_left": None, "forced_reveal": False}

        if correct and not p["solved"]:
            p["solved"] = True
            wrow = conn.execute(
                "SELECT level FROM words WHERE id = ?", (clue["word_id"],),
            ).fetchone()
            base = _score_for_level(wrow["level"] if wrow else None)
            # 「音声モード」の発音ヒントはこのモードでは常時無料なので、
            # 減点対象から除く(日本語/英語ヒントは常時表示型なので
            # そもそもhints_usedに入らない。上のcrossword_hintガード参照)。
            free_hint = FREE_HINT_BY_MODE.get(row["clue_mode"])
            paid_hints = [
                h for h in p["hints_used"]
                if h != "reveal" and h != free_hint
            ]
            gained = base * (1 - HINT_PCT * len(paid_hints))
            p["score"] = max(round(gained), 0)
            row["score"] += p["score"]
        elif not correct and not p["solved"] and not p["given_up"]:
            # 部分正解の開示(2026-09-03ユーザー提起): 位置一致率が高い
            # (PARTIAL_MATCH_THRESHOLD以上)なら一致した文字を全部、
            # そうでなくても先頭文字だけ合っていればそこだけ開示する。
            # ただし当てずっぽう連打(先頭文字だけ合わせ続ける等)を防ぐ
            # ため、不正解のたびに試行回数を数え、上限(MAX_WRONG_ATTEMPTS)
            # に達したら0点でギブアップ扱いにして答えを開示する。
            matches = sum(
                1 for i in range(len(target))
                if i < len(answer) and answer[i] == target[i])
            ratio = matches / len(target) if target else 0
            result["match_ratio"] = round(ratio, 2)
            revealed = set(p.get("revealed_positions", []))
            if ratio >= PARTIAL_MATCH_THRESHOLD:
                for i in range(len(target)):
                    if i < len(answer) and answer[i] == target[i]:
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
        _guard_games_access(conn, uid)
        row = _owned_session(conn, session_id, uid)
        puzzle = json.loads(row["puzzle_json"])
        progress = json.loads(row["progress_json"])
        clue = _find_clue(puzzle, payload.clue_number, payload.direction)
        if clue is None:
            raise errors.http_error("7002", "存在しないクリューです。")
        free_hint = FREE_HINT_BY_MODE.get(row["clue_mode"])
        if payload.hint_type == free_hint and free_hint in ("japanese",
                                                              "english"):
            # 文章系(日本語・英語ヒント)は既にクリューとして常時表示
            # されているため、あらためて要求する意味が無い。音声だけは
            # 「常時無料だが表示ではなく再生」なので、このガード対象外
            # (下のコスト計算で0円扱いにする)。
            raise errors.http_error(
                "7002", "このモードでは既に表示されているヒントです。")
        key = f"{clue['number']}-{clue['direction']}"
        p = progress.setdefault(key, {"solved": False, "given_up": False,
                                       "hints_used": []})
        if payload.hint_type not in p["hints_used"]:
            p["hints_used"].append(payload.hint_type)
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
        _guard_games_access(conn, uid)
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
        _guard_games_access(conn, uid)
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
