"""OpenAI integration with graceful no-key fallback + usage/cost tracking.

The whole app must run without an API key (per the requirements: "キーはまだ
無くてもOK"). Every AI call therefore returns a structured result that either
contains the model output or an ``ai_enabled=False`` marker, so the UI can show
a friendly "set your API key" message instead of crashing.

Token usage and an estimated USD cost are recorded for every successful call so
the UI can display API consumption (ユーザー要望: API使用量・費用の表示).
"""

from __future__ import annotations

import sqlite3
import time
from collections import deque
from dataclasses import dataclass
from typing import Iterator

from ..config import load_settings, log
from ..database import db
from .errors import ERROR_CODES

# ---------------------------------------------------------------------------
# Cost / rate guards — prevent runaway spend if something loops or misbehaves.
# Two independent limits, both configurable via .env:
#   * AI_DAILY_COST_CAP_USD — refuse once today's spend reaches the cap.
#   * AI_MAX_CALLS_PER_MIN  — refuse if calls arrive too fast (loop guard).
# Refusals are returned as a normal "AI unavailable" result so the UI shows a
# friendly message and (for TTS) falls back to the free browser voice.
# ---------------------------------------------------------------------------

# ユーザーID別の直近呼び出し時刻（§D5: 以前はグローバル単一カウンタだった
# ため、1ユーザーの連続呼び出しが他の全ユーザーのAI機能を止めてしまう
# 問題があった。ユーザーごとに独立させ、他ユーザーへの影響を無くす）。
_call_times: dict[int, deque[float]] = {}


def _today_cost_usd() -> float:
    with db() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) AS c FROM ai_usage "
            "WHERE date(created_at, 'localtime') = date('now', 'localtime')"
        ).fetchone()
    return float(row["c"] or 0.0)


def _user_cost_usd(user_id: int, period: str) -> float:
    """Sum of a single user's AI cost over 'day' (local day) or 'month'."""
    if period == "month":
        clause = ("strftime('%Y-%m', created_at, 'localtime') = "
                  "strftime('%Y-%m', 'now', 'localtime')")
    else:
        clause = ("date(created_at, 'localtime') = "
                  "date('now', 'localtime')")
    with db() as conn:
        row = conn.execute(
            f"SELECT COALESCE(SUM(cost_usd), 0) AS c FROM ai_usage "
            f"WHERE user_id = ? AND {clause}", (user_id,)
        ).fetchone()
    return float(row["c"] or 0.0)


def _default_daily_cap_usd(u: dict, s) -> float:
    """個別上限が未設定のユーザーの既定無料枠(USD/日)。
    2026-08-12決定: 無料枠は**旧ユーザー（テスター）＝管理者が直接作成した
    アカウント（email未設定）のみ**。自己サインアップ（emailを設定して
    登録した全ユーザー）は課金の有無を問わず**0円**（無料枠なし・残高が
    無ければAI機能を一切使えない・購入したptで利用する）。

    2026-08-26: 上記の無料枠を「100pt/日(通常)・1000pt/日(admin)」という
    キリのよい値に統一（ユーザー指示）。従来はrole="admin"かどうかを見ずに
    一律`ai_daily_free_jpy`だったが、admin(オーナー自身のテスト利用等)は
    より広い枠が要るため新たにrole分岐を追加した。この変更に合わせ、
    既存の個別上限(`users.daily_cost_cap_usd`)を持っていた対象ユーザーは
    移行時に一括でNULLへ戻し、この既定値に統一する
    （`scripts/reset_daily_cap_overrides.py`参照）。

    「特別ユーザー」に無料枠を与えたい場合は、この既定値ではなく
    `users.daily_cost_cap_usd`(個別上限)を管理者が直接設定する
    （このオーバーライドは`_effective_caps`側で既にこの既定値より優先
    されている＝新規スキーマ不要）。

    旧実装は`user_tier()`の"legacy"/"charged"判定（＝emailの有無に加え
    残高/チャージ履歴も見る）を使っていたが、「一度でも課金した旧
    ユーザー」は"charged"と判定され、結果的に大半の自己サインアップ課金
    ユーザーにも恒久的な無料枠を与えてしまっていた
    （docs/TODO.md「¥150/日無料枠の抜け穴」参照・2026-08-12修正）。
    emailの有無だけを見ることで、課金履歴に関係なく「旧ユーザーか
    どうか」を安定して判定する。"""
    if (u.get("email") or "").strip():
        return 0.0
    from .auth import GUEST_USERNAME
    if u.get("username") == GUEST_USERNAME:
        return 0.0  # 2026-08-12: ゲスト疑似ユーザーは常に無料枠0円
    if u.get("role") == "admin":
        return s.ai_daily_free_jpy_admin / s.usd_jpy_rate
    return s.ai_daily_free_jpy / s.usd_jpy_rate


def _effective_caps(u: dict, s) -> tuple[float, float]:
    """ユーザーの実効 日次/月次 上限(USD)。個別設定があればそれを優先
    （0円の明示指定も尊重）、無ければ既定値（旧ユーザーのみ¥150/日相当・
    それ以外は0円）を使う。月次は個別未設定なら日次既定の30日分を上限
    とする（従来は無制限だったギャップの修正）。"""
    dcap = u.get("daily_cost_cap_usd")
    dcap = float(dcap) if dcap is not None else _default_daily_cap_usd(u, s)
    mcap = u.get("monthly_cost_cap_usd")
    mcap = float(mcap) if mcap is not None else dcap * 30
    return dcap, mcap


def _user_guard(s) -> str | None:
    """課金モデル: 日次/月次の上限は「無料枠」。枠に到達したら**前払いチャージ
    残高**を消費して継続（残高は枠とは別管理）。残高が無ければ停止。
    無料枠は0円もありえる（emailを設定した自己サインアップユーザーは
    全員これ・§`_default_daily_cap_usd`）＝その場合は初回から残高必須。

    CLIスクリプト実行時（Webリクエスト経由でない場合）はこの個別枠
    チェックを丸ごとスキップする。`current_user_id()`はリクエスト文脈が
    無い場合ownerにフォールバックするため、CLIバッチ実行がオーナー個人の
    日次/月次無料枠を消費して停止してしまう問題への対応
    （docs/TODO.md「CLIスクリプトのAI無料枠問題」参照）。サイト全体の合計
    支出上限（`_guard()`内のsite_cap）はCLI実行でも引き続き有効。"""
    from .auth import current_user_id, get_user, is_web_request

    if not is_web_request():
        return None

    uid = current_user_id()
    with db() as conn:
        u = get_user(conn, uid)
    if not u:
        return None
    dcap, mcap = _effective_caps(u, s)
    over_daily = _user_cost_usd(uid, "day") >= dcap
    over_monthly = _user_cost_usd(uid, "month") >= mcap
    if over_daily or over_monthly:
        bal = u.get("balance_jpy")
        if bal is not None and float(bal) > 0:
            return None  # 枠到達だがチャージ残高で継続（_record_usageで消費）
        which = "本日" if over_daily else "今月"
        return (f"{which}の無料利用枠の上限に達しました。設定画面でチャージ"
                "キーを登録すると、残高で引き続きご利用いただけます。")
    return None


def budget_status() -> dict:
    """Today's spend vs. the configured cap (for the UI / settings display)."""
    s = load_settings()
    spent = _today_cost_usd()
    cap = s.ai_daily_cost_cap_usd
    return {
        "today_cost_usd": round(spent, 4),
        "cap_usd": cap,
        "remaining_usd": round(max(0.0, cap - spent), 4),
        "blocked": cap > 0 and spent >= cap,
        "calls_per_min_cap": s.ai_max_calls_per_min,
    }


def _guard(
    feature: str, *, rate_limit: bool = True, skip_user_cap: bool = False,
) -> str | None:
    """Return a refusal message if a guard trips, else None. The daily cost
    cap is ALWAYS enforced. The per-minute rate limit can be skipped for an
    explicit, user-authorized batch (``rate_limit=False``) — the cap still
    stops it once the day's budget is spent, so it resumes next run.

    ``skip_user_cap``: ユーザー別の日次/月次無料枠チェックだけを飛ばす
    （サイト全体の合計支出上限・分間レート制限は引き続き有効）。単語/
    フレーズの「無料範囲」音声(`synthesize_speech`の`free_range`引数)専用
    — `access_tiers`のとおり件数上限があるためコストは有界で、既に
    `charge_playback_if_needed`で無料と判定済みの再生をここで再度
    ブロックしない（2026-08-12: ゲスト無料枠を0円にした際、この二重
    チェックのせいで無料範囲内でも未キャッシュの語は合成できず、フロント
    側がブラウザ音声にフォールバックしてしまう不具合が発覚したため）。"""
    s = load_settings()
    # サイト全体の合計支出に対する保険（個別/tier別の枠とは独立の最終防衛線）。
    # 2026-08-08: 以前はこの`AI_DAILY_COST_CAP_USD`がユーザー個別枠の
    # フォールバックとしても使われ実質有名無実だったため、tier別無料枠の
    # 導入と合わせて「サイト全体の1日合計」チェックとして再定義した。
    site_cap = s.ai_daily_cost_cap_usd
    if site_cap > 0 and _today_cost_usd() >= site_cap:
        return ("本日のAI利用がサイト全体の上限に達しました。"
                "時間をおいて再試行してください。")
    # ユーザー別ガード（tierごとの日次/月次無料枠・前払い残高）。
    if not skip_user_cap:
        refusal = _user_guard(s)
        if refusal:
            return refusal
    if rate_limit:
        from .auth import current_user_id

        uid = current_user_id()
        now = time.monotonic()
        times = _call_times.setdefault(uid, deque(maxlen=240))
        window = [t for t in times if now - t < 60.0]
        if len(window) >= s.ai_max_calls_per_min:
            return (
                f"AI呼び出しが短時間に集中しています（上限 "
                f"{s.ai_max_calls_per_min}回/分）。少し待ってから再試行して"
                "ください。"
            )
        times.append(now)
    return None


# Approx. USD price per 1M tokens (input, output). Update as needed.
# Source: OpenAI public pricing. Unknown models fall back to gpt-4o-mini.
PRICING = {
    # 既定(標準ティア)。4o/4o-mini を使っていた箇所はこれに統一。
    "gpt-5.4-mini": (0.75, 4.50),
    # 高品質ティア(gpt-5.4 フル)。<272K context の標準レート。
    "gpt-5.4": (2.50, 15.00),
    # 2026-07リリースの最安ティア(品質/速度テスト後に既定切替を検討中)。
    "gpt-5.6-luna": (0.20, 1.20),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
}


def _price_for(model: str) -> tuple[float, float]:
    return PRICING.get(model, PRICING["gpt-5.4-mini"])


def _token_kwarg(model: str, n: int) -> dict:
    """新しめのモデル(gpt-5系 / o系)は max_tokens 非対応で
    max_completion_tokens を使う。旧モデル(4o/4.1)は従来どおり max_tokens。"""
    m = (model or "").lower()
    if m.startswith("gpt-5") or m.startswith(("o1", "o3", "o4")):
        return {"max_completion_tokens": n}
    return {"max_tokens": n}


# temperature のカスタム値を受け付けないモデル（既定値1のみ対応）。
# 2026-08-08: gpt-5.6-luna採用時に temperature=0.7 で400エラーになることを
# 確認して追加。同日、gpt-5.6-terra でも同じ制約を確認したため gpt-5.6系
# 全体に広げた（sol は未確認だが同一世代のため予防的に含める）。o系
# (推論系)モデルも同様の制約を持つことが多いため含める。
_NO_CUSTOM_TEMPERATURE_PREFIXES = ("gpt-5.6", "o1", "o3", "o4")


def _temperature_kwarg(model: str, temperature: float) -> dict:
    m = (model or "").lower()
    if m.startswith(_NO_CUSTOM_TEMPERATURE_PREFIXES):
        return {}
    return {"temperature": temperature}


def estimate_cost(model: str, prompt_tokens: int, output_tokens: int) -> float:
    pin, pout = _price_for(model)
    return prompt_tokens / 1_000_000 * pin + output_tokens / 1_000_000 * pout


@dataclass
class AIResult:
    ok: bool
    text: str
    error: str | None = None
    cost_usd: float = 0.0
    prompt_tokens: int = 0
    output_tokens: int = 0


# 機能(feature)別の動的課金倍率(2026-08-12・ユーザー決定)。無料枠(日次/月次
# 上限)を使い切った後の利用でのみ、この式でチャージ残高から控除する
# （枠内の利用・枠の判定基準そのものは実測原価のまま・変更なし）。
# 式: 残高から引く額 = ceil_to_0.5円(実測原価(¥) × 倍率 [+ 上乗せ額]) 。
# 一覧に無いfeatureは既定の"other"倍率(×2.0)を使う（判定・翻訳・要約・
# 音声操作・単語/フレーズ詳細生成・呼び出し元不明のTTS/STT等）。
#
# reading_tts/listening_tts: 教材の読み上げ(TTS)呼び出し元が判明している
# 場合のみ使う専用倍率（`static/js/views.js`のリーディング/リスニング画面
# からのみクライアントが`feature`を明示指定・`app/routers/learn.py`の
# `TtsIn`でホワイトリスト検証済み。会話中の読み上げ等、呼び出し元不明な
# TTS/STTは"tts"/"stt"のまま＝"other"倍率にフォールバックする）。
CATEGORY_MULTIPLIER = {
    "conversation": 2.5,
    "reading": 1.5,
    "writing": 2.0,
    "reading_tts": 1.7,
    "listening_tts": 1.7,
    "other": 2.0,
}

CHARGE_SURCHARGE_JPY = 0.5
CHARGE_ROUND_STEP_JPY = 0.5

# 会話1往復は「チャット」「TTS」「STT」が別々のAPI呼び出しとして課金される
# ため、全部に+50銭を乗せると1往復で最大3回分の上乗せになってしまう
# （2026-08-12ユーザー指摘・「50銭は一回だけ」に修正）。TTS/STTは倍率のみ
# （丸めによる実質下限0.5円は残る）が原則で、+50銭が乗るのはテキスト生成
# (chat)、および呼び出し元が判明しているreading_tts/listening_tts
# （教材読み上げ。ユーザー指示により明示的に+50銭を付ける）のみ。判定は
# 除外リスト方式にする（許可リスト方式だと、"listening"等chat()経由の
# 「その他」カテゴリ機能に+50銭が乗り忘れるバグがあったため2026-08-12修正）。
_NO_SURCHARGE_FEATURES = {"tts", "stt"}

# crossword_hint（クロスワードのヒント生成）は2026-09-05〜、呼び出し
# ごとの自動課金(_record_usage → _maybe_deduct_balance)からは外し、
# 1ゲーム分の原価合計をまとめて1回だけ課金する方式に変更した
# (下記 charge_crossword_game 参照。docs/COST_ESTIMATE.md §1.5
# 「新課金式案」)。キャッシュ済みでAI呼び出しが0回のゲームでも
# 必ず最低0.25pt課金することで、キャッシュヒット率が上がるほど
# 平均収益が¥0に近づいていた旧方式(呼び出し毎課金・§1.5旧版)の
# 弱点を解消する狙い。ai_usageへのINSERT自体(原価の記録)は従来通り
# 続ける（_record_usage参照・profitability分析に必要なため）。
_LUMP_SUM_FEATURES = {"crossword_hint"}


def _compute_charge_jpy(cost_usd: float, rate: float, feature: str) -> float:
    import math

    mult = CATEGORY_MULTIPLIER.get(feature, CATEGORY_MULTIPLIER["other"])
    surcharge = 0.0 if feature in _NO_SURCHARGE_FEATURES else CHARGE_SURCHARGE_JPY
    raw = cost_usd * rate * mult + surcharge
    steps = math.ceil(raw / CHARGE_ROUND_STEP_JPY - 1e-9)
    return steps * CHARGE_ROUND_STEP_JPY


def _maybe_deduct_balance(
    conn, uid: int, cost_usd: float, feature: str, s,
) -> None:
    """チャージ残高は「無料枠（日次/月次上限）に到達した後の利用」でのみ消費
    する（枠とは別管理）。枠内の利用では残高を減らさない。呼び出し元が同じ
    接続内で対象のai_usage行を既にINSERTしている前提
    （`_user_cost_usd`はコミット済み分を見るため、直前＝このコール分を
    除いた累計になる）。"""
    from .auth import add_balance, get_user

    u = get_user(conn, uid)
    if not u or u.get("balance_jpy") is None:
        return
    dcap, mcap = _effective_caps(u, s)
    prior_day = _user_cost_usd(uid, "day")
    prior_mon = _user_cost_usd(uid, "month")
    over = prior_day >= dcap or prior_mon >= mcap
    if not over:
        return
    charge = _compute_charge_jpy(cost_usd, s.usd_jpy_rate, feature)
    # 0円未満にはしない(旧UPDATE文のMAX(0,...)相当)。add_balance()は単純な
    # 加減算のみ行うため、ここで下限をクランプしてから渡す。
    cur = float(u.get("balance_jpy") or 0)
    delta = -min(charge, cur)
    if delta != 0:
        add_balance(
            conn, uid, delta, reason="ai_usage",
            note=f"{feature} (${cost_usd:.5f})",
        )


# クロスワード1ゲーム分の課金式(2026-09-05ユーザー提案・
# docs/COST_ESTIMATE.md §1.5「新課金式案」)。既存のCATEGORY_MULTIPLIER
# 方式(呼び出し毎・0.5円単位)とは別枠の独自の式・単位(pt・0.25刻み)。
CROSSWORD_GAME_BASE_PT = 0.25
CROSSWORD_GAME_SURCHARGE_JPY = 0.5
CROSSWORD_GAME_MULT = 2.0
CROSSWORD_GAME_ROUND_STEP_PT = 0.25


def _compute_crossword_game_charge_pt(cost_usd_total: float, rate: float) -> float:
    """1ゲームぶんのAI原価合計(USD)から課金額(pt)を計算する。
    AI呼び出しが0回(全語キャッシュ済み/AI不要モード)なら基本額のみ、
    それ以外は「基本額 + (原価(円) + 50銭) × 2」を0.25pt単位で切り上げる。"""
    import math

    if cost_usd_total <= 0:
        return CROSSWORD_GAME_BASE_PT
    cost_jpy = cost_usd_total * rate
    raw = (CROSSWORD_GAME_BASE_PT
           + (cost_jpy + CROSSWORD_GAME_SURCHARGE_JPY) * CROSSWORD_GAME_MULT)
    steps = math.ceil(raw / CROSSWORD_GAME_ROUND_STEP_PT - 1e-9)
    return steps * CROSSWORD_GAME_ROUND_STEP_PT


def charge_crossword_game(conn, uid: int, cost_usd_total: float) -> float:
    """クロスワード1ゲーム作成(新規/再生成)ごとに、そのゲームで実際に
    発生したAI原価合計をまとめて1回だけ課金する(_LUMP_SUM_FEATURES参照
    ・呼び出し毎の自動課金はこのfeatureでは行わない)。保存(ピン留め)の
    有無に関わらず毎回課金する。無料枠(日次/月次上限)の判定とは独立
    （crossword自体がテスト/招待ユーザー限定の別機能であり、キャッシュ
    済みでも必ず最低額を課金することが本方式の狙いのため）。
    残高が課金額に満たない場合は残高を使い切るだけに留め、0円未満には
    しない(ゲーム自体は既に生成済みでAI原価も既に発生済みのため、
    再生課金(charge_playback_if_needed)と違って事前に拒否できない)。
    戻り値: 実際に控除した額(pt)。"""
    from .auth import add_balance, get_user

    u = get_user(conn, uid)
    if not u or u.get("balance_jpy") is None:
        return 0.0
    s = load_settings()
    charge = _compute_crossword_game_charge_pt(cost_usd_total, s.usd_jpy_rate)
    cur = float(u.get("balance_jpy") or 0)
    delta = -min(charge, cur)
    if delta != 0:
        add_balance(
            conn, uid, delta, reason="crossword_game",
            note=f"ai_cost=${cost_usd_total:.5f}",
        )
    return -delta


_USAGE_WRITE_RETRIES = 3  # database is locked時の再試行回数(2026-09-06)


def _record_usage(
    model: str,
    prompt_tokens: int,
    output_tokens: int,
    feature: str,
) -> float:
    from .auth import current_ip, current_user_id

    cost = estimate_cost(model, prompt_tokens, output_tokens)
    uid = current_user_id()
    ip = current_ip()
    s = load_settings()
    # クロスワードのAIヒント生成(_ensure_ai_hints)のように、1リクエスト内で
    # 複数語のバッチをThreadPoolExecutorで並列にai.chat()する機能があり、
    # 各バッチが独立したDB接続でここへ書き込みに来る。busy_timeout(15秒)
    # 内でも競合が解消しないことがあり、"database is locked"のまま例外に
    # なると、実際には成功していたAI応答ごと「chat失敗」として捨てられて
    # しまっていた(2026-09-06ユーザー報告: 有料会員なのにヒントが
    # 「準備中」のまま・日本語ヒントがAI生成されず訳語のみにフォール
    # バックした事例)。まずは短い間隔で数回リトライして解消を試みる。
    for attempt in range(_USAGE_WRITE_RETRIES):
        try:
            with db() as conn:
                conn.execute(
                    "INSERT INTO ai_usage "
                    "(model, prompt_tokens, output_tokens, cost_usd, "
                    " feature, user_id, ip) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (model, prompt_tokens, output_tokens, cost, feature,
                     uid, ip),
                )
                if feature not in _LUMP_SUM_FEATURES:
                    _maybe_deduct_balance(conn, uid, cost, feature, s)
            return cost
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower() or (
                attempt == _USAGE_WRITE_RETRIES - 1):
                raise
            time.sleep(0.2 * (attempt + 1))
    return cost  # pragma: no cover - ループは必ずreturn/raiseで抜ける


# OpenAI SDKの既定(timeout未指定=10分・max_retries=2)のままだと、接続
# トラブル時に「失敗はするが数分待たされる」状態になり得る(2026-09-05
# ユーザー報告: ローカルでcrossword_hint生成中に1分以上固まって見えた。
# app.logのchat失敗ログ自体はConnection errorとして残っていたため、
# 機能面のフォールバック(AI失敗時は非AIヒントへ切替)は効いていたが、
# 応答が返るまでの体感速度が悪かった)。接続系はすぐに諦めさせ、
# リトライも1回だけにして「待たされる」ワースト値を短くする。
_OPENAI_TIMEOUT_SEC = 20.0
_OPENAI_CONNECT_TIMEOUT_SEC = 5.0
_OPENAI_MAX_RETRIES = 1
# この秒数以上かかった呼び出しは、成功していてもapp.logにWARNINGを残す
# (2026-09-05・「各処理の時間で課題なところをあぶりだしたい」対応)。
_SLOW_CALL_SEC = 8.0


def _client():
    """Create an OpenAI client from current settings, or return None."""
    settings = load_settings()
    if not settings.ai_enabled:
        return None, settings
    try:
        import httpx
        from openai import OpenAI

        return OpenAI(
            api_key=settings.openai_api_key,
            timeout=httpx.Timeout(
                _OPENAI_TIMEOUT_SEC, connect=_OPENAI_CONNECT_TIMEOUT_SEC),
            max_retries=_OPENAI_MAX_RETRIES,
        ), settings
    except Exception:  # pragma: no cover - import/runtime guard
        log.exception("OpenAI クライアントの初期化に失敗")
        return None, settings


def is_enabled() -> bool:
    return load_settings().ai_enabled


def chat(
    system: str,
    user: str,
    *,
    temperature: float = 0.7,
    max_tokens: int = 1200,
    feature: str = "",
    model: str | None = None,
    rate_limit: bool = True,
) -> AIResult:
    """Single-turn chat completion. Stateless by design — we never rely on
    server-side chat history; all context is passed in explicitly.

    ``model`` overrides the configured chat model (used for判定/教材生成).
    ``rate_limit=False`` skips the per-minute cap for an explicit, authorized
    batch (the daily cost cap still applies and will stop it once spent)."""
    client, settings = _client()
    if client is None:
        if not settings.ai_enabled:
            return AIResult(
                ok=False,
                text="",
                error="OPENAI_API_KEY が未設定です。設定で登録してください。",
            )
        return AIResult(
            ok=False, text="", error="OpenAI クライアントを初期化できませんでした。"
        )

    refusal = _guard(feature, rate_limit=rate_limit)
    if refusal:
        return AIResult(ok=False, text="", error=refusal)

    use_model = model or settings.openai_model
    capped = min(max_tokens, settings.ai_max_output_tokens)
    # 呼び出しの所要時間を計測(2026-09-05・ユーザー報告「クロスワード生成が
    # 1分以上固まって見えた」の再発防止)。成功時も遅い呼び出しは警告ログを
    # 残し、「AI呼び出しのどこが遅いか」を事後にapp.logから追えるようにする
    # (失敗時は原因調査のため常にelapsedを記録)。
    t0 = time.monotonic()
    try:
        resp = client.chat.completions.create(
            model=use_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **_temperature_kwarg(use_model, temperature),
            **_token_kwarg(use_model, capped),
        )
    except Exception as exc:
        elapsed = time.monotonic() - t0
        log.error("chat 失敗 (feature=%s model=%s elapsed=%.1fs): %s",
                   feature, use_model, elapsed, exc)
        # 2026-08-29修正: synthesize_speech()と同じ問題(生の例外文字列を
        # そのままユーザーへ返していた)。errors.pyの定型文(4005)を返す。
        return AIResult(ok=False, text="", error=ERROR_CODES["4005"][0])

    elapsed = time.monotonic() - t0
    if elapsed >= _SLOW_CALL_SEC:
        log.warning(
            "chat 低速 (feature=%s model=%s elapsed=%.1fs)",
            feature, use_model, elapsed)
    usage = resp.usage
    ptok = getattr(usage, "prompt_tokens", 0) or 0
    otok = getattr(usage, "completion_tokens", 0) or 0
    try:
        cost = _record_usage(use_model, ptok, otok, feature)
    except Exception:
        # 2026-09-06: API呼び出し自体は既に成功しているため、利用量記録
        # (DB書き込み)がdatabase is locked等で失敗しても応答は握り
        # つぶさない(ユーザー報告: クロスワードのAIヒント並列生成で
        # DB競合が起きると、成功していたAI応答ごと「chat失敗」扱いに
        # なり、有料会員でもヒントが「準備中」のまま/日本語ヒントが
        # 訳語のみにフォールバックしていた)。費用はDBが無くても概算
        # できるのでログだけ残して処理を続ける(_record_usage側で3回
        # リトライ済みのため、ここに来るのは稀)。
        log.exception(
            "chat: usage記録に失敗(API呼び出し自体は成功・feature=%s)",
            feature)
        cost = estimate_cost(use_model, ptok, otok)
    return AIResult(
        ok=True,
        text=resp.choices[0].message.content or "",
        cost_usd=cost,
        prompt_tokens=ptok,
        output_tokens=otok,
    )


def chat_stream(
    system: str,
    user: str,
    *,
    temperature: float = 0.7,
    max_tokens: int = 800,
    feature: str = "",
    model: str | None = None,
) -> Iterator[str]:
    """Yield text chunks as they arrive (improves perceived responsiveness).

    Yields plain text deltas. The final usage/cost is recorded at the end and
    is NOT yielded as text; callers stream text and can fetch usage separately.
    ``model`` overrides the configured chat model (2026-08-22: 会話の
    「応答速度優先」チェックボックス用に追加。未指定時は従来通り
    ``settings.openai_model``)。"""
    client, settings = _client()
    if client is None:
        yield "[AI未設定] OPENAI_API_KEY を設定すると会話できます。"
        return

    refusal = _guard(feature)
    if refusal:
        yield f"[停止] {refusal}"
        return

    use_model = model or settings.openai_model
    t0 = time.monotonic()
    try:
        stream = client.chat.completions.create(
            model=use_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **_temperature_kwarg(use_model, temperature),
            **_token_kwarg(
                use_model,
                min(max_tokens, settings.ai_max_output_tokens),
            ),
            stream=True,
            stream_options={"include_usage": True},
        )
        ptok = otok = 0
        for chunk in stream:
            if chunk.usage is not None:
                ptok = chunk.usage.prompt_tokens or 0
                otok = chunk.usage.completion_tokens or 0
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
        if ptok or otok:
            _record_usage(use_model, ptok, otok, feature)
        elapsed = time.monotonic() - t0
        if elapsed >= _SLOW_CALL_SEC:
            log.warning(
                "chat_stream 低速 (feature=%s model=%s elapsed=%.1fs)",
                feature, use_model, elapsed)
    except Exception as exc:
        elapsed = time.monotonic() - t0
        log.error("chat_stream 失敗 (feature=%s model=%s elapsed=%.1fs): %s",
                   feature, use_model, elapsed, exc)
        yield f"\n[エラー] {exc}"


# OpenAI TTS voices (ChatGPT-quality, natural). Names shown in the UI.
TTS_VOICES = [
    "alloy", "ash", "ballad", "coral", "echo",
    "fable", "nova", "onyx", "sage", "shimmer",
]

# Rough TTS cost estimate (USD per 1000 characters). gpt-4o-mini-tts is
# billed by tokens; we approximate from text length for the usage display.
_TTS_USD_PER_1K_CHARS = 0.015


# 読み上げの話し方プリセット（gpt-4o-mini-tts の品質を安定させる）。
#   learn  … 学習用。落ち着いた一定ペース・やや遅め・明瞭（指示なしだと文の
#            抑揚が過剰・不自然になるのを防ぐ）。
#   native … ネイティブの自然な速さ・リズム・リンキング（少し速い）。
TTS_STYLES = {
    "learn": (
        "You are a clear, friendly English teacher reading for a learner. "
        "Speak in natural, standard English with calm, even intonation and a "
        "steady, slightly slower pace. Pronounce every word clearly and "
        "distinctly. Do not rush, do not add emotion, drama, whispering, or "
        "any accent."
    ),
    "native": (
        "Speak in natural, native English at a normal conversational pace "
        "and rhythm, with the natural linking, stress, and flow a native "
        "speaker uses in everyday speech. Keep it clear and easy to follow. "
        "Neutral, friendly tone; no exaggeration, drama, or strong accent."
    ),
}
TTS_STYLE_DEFAULT = "learn"


def _tts_instructions(style: str = TTS_STYLE_DEFAULT) -> str:
    import os
    if style == "learn":
        env = os.getenv("OPENAI_TTS_INSTRUCTIONS", "").strip()
        if env:
            return env
    return TTS_STYLES.get(style, TTS_STYLES["learn"])


def _tts_cache_path(model: str, voice: str, text: str, instr: str = ""):
    import hashlib

    from ..config import paths

    key = f"{model}|{voice}|{instr}|{text}".encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()[:32]
    cache_dir = paths.data_dir / "tts_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{digest}.mp3"


def synthesize_speech(
    text: str, voice: str = "alloy", *,
    style: str = TTS_STYLE_DEFAULT, rate_limit: bool = True,
    feature: str = "tts", free_range: bool = False,
) -> tuple[bytes | None, str | None]:
    """Return (audio_mp3_bytes, error). Uses OpenAI's natural TTS voices.

    Audio is cached on disk by (model, voice, instructions, text); a cache hit
    costs nothing and makes repeated playback free。``style`` で読み上げの
    話し方を選ぶ（'learn'=学習用ゆっくり明瞭 / 'native'=ネイティブの自然な速さ）。
    ``feature`` は課金カテゴリのヒント（呼び出し元が判明している場合のみ
    "reading_tts"/"listening_tts" 等・呼び出し側でホワイトリスト検証済みの
    前提。既定"tts"は呼び出し元不明＝"other"倍率にフォールバック）。
    ``free_range``: 呼び出し元(`charge_playback_if_needed`)が単語/フレーズの
    「無料範囲」内と判定済み（＝件数上限があり総コストが有界）の場合に
    True。ユーザー別の日次/月次無料枠チェックだけを免除する
    （サイト全体の上限・レート制限は引き続き有効）。
    """
    client, settings = _client()
    if client is None:
        if not settings.ai_enabled:
            return None, "OPENAI_API_KEY が未設定です。"
        return None, "OpenAI クライアントを初期化できませんでした。"
    if voice not in TTS_VOICES:
        voice = "alloy"

    instr = _tts_instructions(style)
    cache = _tts_cache_path(settings.tts_model, voice, text[:4000], instr)
    if cache.exists():
        return cache.read_bytes(), None  # cache hit → no API call, no cost

    # only a real (paid) synthesis hits the guard
    refusal = _guard(feature, rate_limit=rate_limit, skip_user_cap=free_range)
    if refusal:
        return None, refusal

    # instructions は gpt-4o-mini-tts 系のみ対応（tts-1系は非対応なので付けない）
    extra = {}
    if instr and "gpt-4o" in settings.tts_model:
        extra["instructions"] = instr
    t0 = time.monotonic()
    try:
        resp = client.audio.speech.create(
            model=settings.tts_model,
            voice=voice,
            input=text[:4000],
            response_format="mp3",
            **extra,
        )
        audio = resp.read() if hasattr(resp, "read") else resp.content
        elapsed = time.monotonic() - t0
        if elapsed >= _SLOW_CALL_SEC:
            log.warning("TTS 低速 (voice=%s model=%s elapsed=%.1fs)",
                        voice, settings.tts_model, elapsed)
        try:
            cache.write_bytes(audio)
        except Exception:  # caching is best-effort
            pass
        cost = len(text) / 1000 * _TTS_USD_PER_1K_CHARS
        from .auth import current_ip, current_user_id
        uid = current_user_id()
        with db() as conn:
            conn.execute(
                "INSERT INTO ai_usage "
                "(model, prompt_tokens, output_tokens, cost_usd, feature, "
                " user_id, ip) VALUES (?, 0, 0, ?, ?, ?, ?)",
                (settings.tts_model, cost, feature, uid, current_ip()),
            )
            # 2026-08-12修正: 以前はここでチャージ残高を消費しておらず、
            # 無料枠を使い切った後もTTSだけ無制限に無料で使えてしまう
            # 抜け穴があった。
            # 2026-08-13修正: 上記の巻き戻し防止だけを見ていたため、
            # free_range=True(無料範囲の単語/フレーズ・公開サンプル教材)
            # でも、無料枠¥0のユーザー(ゲスト/自己サインアップ)は
            # _maybe_deduct_balance内の「上限超過」判定が常にTrueになり、
            # 未キャッシュの初回合成でチャージ残高が課金されてしまう抜け穴が
            # あった。free_rangeはガード免除だけでなく課金免除も意味する
            # べきなのでスキップする(単語/フレーズ・公開サンプルいずれも
            # 「課金ユーザーでも無料」という設計のため)。
            if not free_range:
                _maybe_deduct_balance(conn, uid, cost, feature, settings)
        return audio, None
    except Exception as exc:
        elapsed = time.monotonic() - t0
        log.error("TTS 失敗 (voice=%s, model=%s, elapsed=%.1fs): %s",
                  voice, settings.tts_model, elapsed, exc)
        # 2026-08-29修正: 以前はexcの文字列をそのままユーザーに返しており、
        # OpenAI側の生エラー(レート制限のJSON等)がトースト表示に漏れていた
        # (実機フィードバックで発覚)。詳細はログのみに留め、画面には
        # errors.py(4桁エラーコードの単一ソース)の定型文を返す。
        return None, ERROR_CODES["8001"][0]


# 単語/フレーズ音声「再生」課金の下限(円)。1回あたりの課金額がこれ未満に
# なる場合はこの額に切り上げる（ユーザー指示・2026-08-09）。
PLAYBACK_MIN_CHARGE_JPY = 0.5
# 再生時に課金する額 = 生成コスト(USD換算前)の何分の1にするか。
PLAYBACK_CHARGE_DIVISOR = 10

# --- 短時間の重複課金防止(2026-08-13〜) -------------------------------------
# 同じユーザーが同じコンテンツを誤連打・二重送信しても、直近5分以内に
# 既に課金済みなら再課金しない。プロセス内メモリのみ（デプロイでの
# 再起動時にはクリアされるが、5分という短命さから実用上は問題ない）。
_RECENT_CHARGE_TTL_SEC = 300  # 5分
_recent_charges: dict[tuple, float] = {}  # (uid, key) -> 課金時刻(epoch秒)


def _recent_charge_hit(uid: int, key: str) -> bool:
    """直近5分以内に同一(uid, key)へ課金済みならTrue（かつ期限切れ掃除）。"""
    import time

    now = time.time()
    expired = [k for k, ts in _recent_charges.items()
               if now - ts > _RECENT_CHARGE_TTL_SEC]
    for k in expired:
        _recent_charges.pop(k, None)
    return (uid, key) in _recent_charges


def _recent_charge_mark(uid: int, key: str) -> None:
    import time

    _recent_charges[(uid, key)] = time.time()


def charge_playback_if_needed(
    item_type: str, item_id: int, kind: str, text: str,
) -> str | None:
    """単語/フレーズ音声「再生」の課金ガード（2026-08-09〜）。

    `access_tiers`の無料範囲(レベル昇順・②ログイン無料=単語2,000/
    フレーズ1,500、①未ログイン=単語1,000/フレーズ750)に入っている語は
    誰でも無料で再生できる（B1方針・公平性の原則）。②③④は範囲外だと
    再生ごとに「音声生成コストの1/10」(下限0.5円)をチャージ残高から
    控除する。①(ゲスト)は残高という概念自体が無いため、範囲外は
    ログインを促すメッセージで拒否する（課金消費フローには乗せない）。
    管理者は課金対象外（動作確認用）。キャッシュ済み音声の再生でも、
    再生自体は毎回この課金対象になる（＝「生成は1回・再生は課金」という
    APIコストとは別軸の収益化）。ただし2026-08-13〜: 同一ユーザーが
    同一(item_type, item_id, kind)を直近5分以内に既に課金済みなら、
    誤連打・確認のための聞き直し等では再課金しない（ユーザー指示）。
    `kind`は"word"/"example"/"phrase"のいずれか(同じitem_idでも単語音声と
    例文音声は別コンテンツなのでキーに含める)。

    戻り値: 課金不要/成功なら None、拒否する場合はユーザー向けエラー文言。
    """
    from . import access_tiers
    from .auth import add_balance, current_user_id, get_user, is_guest_user_id

    with db() as conn:
        uid = current_user_id()
        is_guest = is_guest_user_id(conn, uid)
        if access_tiers.is_free_range(
            conn, item_type, item_id, guest=is_guest,
        ):
            return None
        if is_guest:
            # 「ログインすると聴けます」は、ログイン後の無料範囲(②)にも
            # 入っている語だけに限定して案内する。②の範囲外まで一律で
            # この文言を出すと、ログインしても実際はチャージが必要な
            # 語なのに「ログインだけで無料になる」と誤解させてしまい、
            # 苦情の原因になるため区別する(2026-08-11ユーザー指摘)。
            if access_tiers.is_free_range(conn, item_type, item_id):
                return (
                    "この単語・フレーズの音声はログインすると聴けます"
                    "（無料の会員登録のみで再生できる範囲が広がります）。"
                )
            return (
                "この単語・フレーズの音声は無料の範囲外です。ログイン"
                "（無料の会員登録）だけでは聴けず、少額のチャージが必要に"
                "なります。"
            )
        u = get_user(conn, uid)
        if u and u.get("role") == "admin":
            return None
        recent_key = f"{item_type}:{item_id}:{kind}"
        if _recent_charge_hit(uid, recent_key):
            return None
        settings = load_settings()
        gen_cost_usd = len(text) / 1000 * _TTS_USD_PER_1K_CHARS
        charge_jpy = max(
            PLAYBACK_MIN_CHARGE_JPY,
            gen_cost_usd / PLAYBACK_CHARGE_DIVISOR
            * settings.usd_jpy_rate * settings.balance_markup,
        )
        balance = float((u or {}).get("balance_jpy") or 0)
        if balance < charge_jpy:
            return (
                "この単語・フレーズの再生には少額のチャージ消費が必要です"
                f"（必要額: 約¥{charge_jpy:.1f}・残高: ¥{balance:.1f}）。"
                "設定画面からチャージしてください。"
            )
        delta = -min(charge_jpy, balance)
        if delta != 0:
            add_balance(
                conn, uid, delta, reason="tts_playback",
                note=f"{item_type}:{item_id}:{kind}",
            )
        _recent_charge_mark(uid, recent_key)
        return None


# 認識言語ヒント: ISO-639-1 コード → Whisper が verbose_json で返す言語名。
_LANG_NAMES = {
    "en": "english", "ja": "japanese", "zh": "chinese", "ko": "korean",
}


def transcribe(
    audio_bytes: bytes, filename: str = "audio.webm", language: str = "",
) -> tuple[str | None, str | None]:
    """Speech-to-text via OpenAI Whisper. Returns (text, error).

    ``language`` は認識言語のヒント(誤認識対策):
    * ""            … 完全自動判定(従来動作)
    * "en"          … その言語に固定(例: 英語以外に化けるのを防ぐ)
    * "en,ja" など  … 候補を限定。自動判定し、候補外(例:韓国語)に化けたら
                       先頭の言語で取り直す。
    """
    import io

    client, settings = _client()
    if client is None:
        if not settings.ai_enabled:
            return None, "OPENAI_API_KEY が未設定です。"
        return None, "OpenAI クライアントを初期化できませんでした。"
    refusal = _guard("stt")
    if refusal:
        return None, refusal
    allowed = [c.strip().lower() for c in (language or "").split(",")
               if c.strip()]

    def _call(lang: str | None):
        # verbose_json を常時使い、実際の音声長(resp.duration)をコスト計算に
        # 使う（§D4: 以前はバイト数からの逆算のみで、圧縮音声だと過小評価
        # しがちだった）。text/languageは verbose_json でも変わらず取得可能。
        f = io.BytesIO(audio_bytes)
        f.name = filename
        kw: dict = {
            "model": settings.stt_model, "file": f,
            "response_format": "verbose_json",
        }
        if lang:
            kw["language"] = lang
        return client.audio.transcriptions.create(**kw)

    t0 = time.monotonic()
    try:
        calls = 1
        if len(allowed) == 1:
            resp = _call(allowed[0])
            text = resp.text
        elif len(allowed) >= 2:
            # 候補が複数: 自動判定し、候補外に化けたら先頭言語で取り直す。
            resp = _call(None)
            detected = (getattr(resp, "language", "") or "").lower()
            names = {_LANG_NAMES.get(c, c) for c in allowed} | set(allowed)
            if detected and detected not in names:
                resp = _call(allowed[0])
                calls = 2
            text = resp.text
        else:
            resp = _call(None)
            text = resp.text
        # whisper-1 ≈ $0.006/分。実際の音声長(duration)が取れればそれを使い、
        # 取れない場合のみバイト数からの概算にフォールバックする。
        duration_sec = getattr(resp, "duration", None)
        if duration_sec:
            minutes = max(float(duration_sec) / 60.0, 0.01)
        else:
            minutes = max(len(audio_bytes) / (16000 * 60), 0.05)
        cost = minutes * 0.006 * calls
        from .auth import current_ip, current_user_id
        uid = current_user_id()
        with db() as conn:
            conn.execute(
                "INSERT INTO ai_usage "
                "(model, prompt_tokens, output_tokens, cost_usd, feature, "
                " user_id, ip) VALUES (?, 0, 0, ?, 'stt', ?, ?)",
                (settings.stt_model, cost, uid, current_ip()),
            )
            # 2026-08-12修正: TTSと同じ抜け穴（残高が一切減らない）がSTTにも
            # あったため同様に修正。
            _maybe_deduct_balance(conn, uid, cost, "stt", settings)
        elapsed = time.monotonic() - t0
        if elapsed >= _SLOW_CALL_SEC:
            log.warning("STT 低速 (model=%s calls=%d elapsed=%.1fs)",
                        settings.stt_model, calls, elapsed)
        return text, None
    except Exception as exc:
        elapsed = time.monotonic() - t0
        log.error("STT 失敗 (elapsed=%.1fs): %s", elapsed, exc)
        return None, f"文字起こしに失敗しました: {exc}"


def usage_summary() -> dict:
    """Return total + recent API usage and estimated cost for the UI."""
    with db() as conn:
        total = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) AS cost, "
            "COALESCE(SUM(prompt_tokens), 0) AS ptok, "
            "COALESCE(SUM(output_tokens), 0) AS otok, "
            "COUNT(*) AS calls FROM ai_usage"
        ).fetchone()
        today = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) AS cost FROM ai_usage "
            "WHERE date(created_at, 'localtime') = date('now', 'localtime')"
        ).fetchone()
        recent = conn.execute(
            "SELECT model, prompt_tokens, output_tokens, cost_usd, "
            "feature, created_at FROM ai_usage ORDER BY id DESC LIMIT 10"
        ).fetchall()
    s = load_settings()
    rate = s.usd_jpy_rate
    return {
        "total_cost_usd": round(total["cost"], 4),
        "today_cost_usd": round(today["cost"], 4),
        "total_cost_jpy": round(total["cost"] * rate, 1),
        "today_cost_jpy": round(today["cost"] * rate, 1),
        "jpy_rate": rate,
        "jpy_as_of": s.usd_jpy_as_of,
        "prompt_tokens": total["ptok"],
        "output_tokens": total["otok"],
        "calls": total["calls"],
        "recent": [dict(r) for r in recent],
        "daily_cap_usd": s.ai_daily_cost_cap_usd,
        "daily_cap_jpy": round(s.ai_daily_cost_cap_usd * rate, 1),
        "cap_blocked": (
            s.ai_daily_cost_cap_usd > 0
            and today["cost"] >= s.ai_daily_cost_cap_usd
        ),
    }
