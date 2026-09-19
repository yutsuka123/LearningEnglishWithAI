"""日次スナップショット(成長ログ)の集計と保存（2026-09-20・計測設計
フェーズ2 3-F）。

usage_events等の生ログは保持期間(usage_eventsは90日)を過ぎると
scripts/prune_usage_events.pyが消すため、**人間(自分・ボットを除く)の
日次集計値を`logs.growth_daily`/`logs.growth_cohort_daily`に恒久保存**し、
生ログをpruneしても過去の推移が変わらないようにする。集計値(人数・件数)
だけを保存し、IP・guest_sid・user_id等の個人を特定できる値は残さない。

## 日付
JST暦日(`substr(datetime(created_at,'+9 hours'),1,10)`と同じ切り方・
管理画面の他の集計と同じ)。「その日」は JST 00:00〜24:00。

## 「人間」の定義(既存の集計と同じ材料を再利用)
- 訪問者キー: `guest_sid`。guest_sidが空の古い行(2026-08-30より前)は
  一時的に`ip:<IP>`をキーにする(メモリ上のみ・保存しない)。
- 除外(ボット): その日のそのキーの行のいずれかが、`visitor_kind.classify`
  (UA判定＋接続元がデータセンターかの判定。`admin_visit_trend`と同じ基準)
  で機械的アクセスと判定、または記録時の`bot_mark`が立っている。
- 除外(自分): その日のそのキーに`is_internal=1`の行がある、管理者/テスト
  アカウントでログインしたことのある端末(`own_device_sids`)、
  ADMIN_KNOWN_IPSのIP(ログイン中の一般ユーザーの行は対象外)。
- 管理者/テストアカウント(role=admin / is_test=1)の行は、利用回数・
  アクティブ人数・エラー数のいずれにも入れない。

## 指標(segment='all')
訪問系(landing_visits・kind='visit'):
  visits=延べ閲覧数 / visitors=ユニーク訪問(キー) / visitors_gclid=広告
  クリックID付きの初回訪問 / visitors_bot_excluded・visitors_internal_
  excluded=除外した件数(除外が効いているかの確認用)
JS到達・操作系(usage_events・訪問したキーに限る。2026-08-17以降のみ):
  visitors_js=boot/html到達 / visitors_ready=boot/app_ready到達 /
  visitors_human=人間訪問(基準・JS到達またはその日2回以上閲覧) /
  visitors_engaged=意図的な操作あり(click/play/分野・シーン選択/ようこそ
  等以外の画面遷移。boot/leave/welcome表示は含めない) /
  visitors_viewed_word=英単語ページ閲覧 / visitors_tried_audio=音声再生
登録系: signup_started=登録開始(login_page/via_signup_hash または
  signup_form/opened) / signup_attempted・signup_done=登録試行・完了
  (landing_visits・kind='signup')。
アカウント系(core): new_users=その日に登録した人数(管理者/テスト/ゲスト
  除く) / logins・login_users=ログイン成功数・人数 / active_users=その日に
  活動した登録ユーザー数(usage_events・単語/フレーズ試行・AI利用・ログイン
  のいずれか) / revenue_jpy・payments=入金額・件数(admin_pl_reportと同じ
  定義: BASE注文(cancelled以外)＋PayPay COMPLETED) / chargers=その日に
  課金した人数。
品質: client_errors=フロントのエラー記録数 / play_errors=再生失敗数。

## セグメント
channel:<ad|llm|search|sns|internal|direct|other|unknown|unattributed>
  (その日の初回訪問のreferrer/utm/gclidから`traffic_source.classify_channel`。
  unattributed=その日の訪問行が無いのに登録系イベントがあったもの)
device:<iPhone等>, page:<着地ページ大分類>, referrer:<ホスト>,
utm_source:<値>(いずれも上位のみ。訪問系と登録系の指標を持つ),
feature:page:<画面>・feature:play:<種別>等・feature:click・
feature:ai:<機能>(events=回数・actors=人数)。

## 生ログが消えた日は上書きしない
`is_raw_complete`: 日の開始がprune境界(now-90日)より新しい日だけ集計して
書く。境界より古い日は既存の行を一切触らない(生ログが欠けた状態で
再集計すると0で上書きしてしまうため)。
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime, timedelta, timezone

from ..config import load_admin_known_ips
from ..database import db
from . import auth, traffic_source, ua_parse, visitor_kind

log = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))

# usage_eventsの保持日数(scripts/prune_usage_events.pyと共通・プライバシー
# ポリシーの「閲覧・操作の記録: 約90日」と一致させること)。
USAGE_KEEP_DAYS = 90

# usage_eventsの計測が始まった日(本番の最古行・JST)。これより前の日は
# 操作系の指標を「未計測」として書かない(0と区別する)。
USAGE_MEASURE_START = "2026-08-17"

FEATURE_TOP_N = 40           # 1日あたり保存するfeature:page/play/…の上位数
FEATURE_AI_TOP_N = 30
DIM_TOP_N = {"device": 10, "page": 10, "referrer": 30, "utm_source": 20}
COHORT_MAX_OFFSET = 60       # コホートの日別経過日の上限
COHORT_WEEKS = (1, 2, 3, 4)  # W1〜W4(登録から7n〜7n+6日目)
STATUS_KEY = "growth_snapshot_status"   # app_stateに置く最終実行の状態

_NON_ACTION_KINDS = ("boot", "leave")
_ENGAGED_KINDS = ("click", "play", "word_domain", "phrase_scene")
_NON_ENGAGED_PAGE_CATS = ("welcome", "login_page", "about_page")
_FEATURE_KINDS = ("page", "play", "play_error", "word_domain", "phrase_scene")
_DATE_SQL = "substr(datetime(created_at, '+9 hours'), 1, 10)"
_CTRL_RE = re.compile(r"[\x00-\x1f\x7f]")

Row = tuple  # (segment, metric, value)


# ---------------------------------------------------------------------------
# 日付ユーティリティ(JST暦日 ↔ UTC文字列)
# ---------------------------------------------------------------------------

def _utc_str(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def day_bounds_utc(d: str) -> tuple[str, str]:
    """JST暦日dの[開始, 終了)をDBのcreated_at(UTC・'YYYY-MM-DD HH:MM:SS')
    と比較できる文字列で返す。"""
    start = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=JST)
    return _utc_str(start), _utc_str(start + timedelta(days=1))


def add_days(d: str, n: int) -> str:
    return (date.fromisoformat(d) + timedelta(days=n)).isoformat()


def date_range(start: str, end: str) -> list[str]:
    out, cur = [], start
    while cur <= end:
        out.append(cur)
        cur = add_days(cur, 1)
    return out


def jst_today(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).astimezone(JST).date().isoformat()


def jst_yesterday(now: datetime | None = None) -> str:
    return add_days(jst_today(now), -1)


def is_raw_complete(d: str, now: datetime | None = None) -> bool:
    """日dの生ログ(usage_events)が保持期間内に丸ごと残っているか。
    pruneは`created_at < now-90日`を消すので、日の開始がそれ以降なら完全。"""
    now = now or datetime.now(timezone.utc)
    start = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=JST)
    return start >= now - timedelta(days=USAGE_KEEP_DAYS)


def _seg(name: str, limit: int = 60) -> str:
    """セグメント名に入れる値(クライアントが自由に送れる文字列を含む)を
    保存・表示してよい形に整える。"""
    return _CTRL_RE.sub("", name or "").strip()[:limit] or "(空)"


# ---------------------------------------------------------------------------
# 「自分の端末」「実ユーザー」の判定材料
# ---------------------------------------------------------------------------

def own_device_sids(conn) -> dict[str, dict[str, bool]]:
    """管理者/テストアカウントでログインしたことのある端末(guest_sid
    Cookie)の一覧を返す: {guest_sid: {"admin": bool, "test": bool}}
    （2026-09-19ユーザー要望「お得意様・ゲストIP別の分析から、自分の
    テストアカウントと管理者を分離したい」対応。2026-09-20に
    app/routers/system.pyからここへ移動: 日次集計スクリプトからも
    同じ判定を使うため。system.pyの`_own_device_sids`は本関数の別名）。

    guest_sid Cookieはログイン中の操作にも同じ値で記録される
    (app/main.py・tracking.log_event)ため、同じブラウザで管理者/
    テストアカウントとして操作した記録があれば「自分の端末」と分かる。
    これで、その端末で**ログアウト状態のまま**確認した操作(=ゲスト扱いで
    IPも一般ゲストと区別できない)も分析から分離できる。IPが変わりやすい
    モバイル回線でも効く点が、既知IP(ADMIN_KNOWN_IPS)判定との違い。
    限界: 一度もログインしていない端末・Cookieを消した直後の操作は
    判別できない(その端末でログインした時点から遡って効く)。"""
    rows = conn.execute(
        "SELECT ue.guest_sid AS sid, "
        " MAX(CASE WHEN u.role = 'admin' THEN 1 ELSE 0 END) AS is_admin, "
        " MAX(u.is_test) AS is_test "
        "FROM usage_events ue JOIN users u ON u.id = ue.user_id "
        "WHERE ue.guest_sid != '' AND (u.role = 'admin' OR u.is_test = 1) "
        "GROUP BY ue.guest_sid"
    ).fetchall()
    out = {
        r["sid"]: {"admin": bool(r["is_admin"]), "test": bool(r["is_test"])}
        for r in rows
    }
    # ログインしただけで他の操作が無い端末も自分の端末に含める
    # (login_log.guest_sid・2026-09-19 Fable敵対的レビューS7)。
    try:
        for r in conn.execute(
            "SELECT l.guest_sid AS sid, "
            " MAX(CASE WHEN u.role = 'admin' THEN 1 ELSE 0 END) AS is_admin, "
            " MAX(u.is_test) AS is_test "
            "FROM login_log l JOIN users u ON u.username = l.username "
            "WHERE l.guest_sid != '' AND l.success = 1 "
            "AND (u.role = 'admin' OR u.is_test = 1) "
            "GROUP BY l.guest_sid"
        ):
            cur = out.setdefault(r["sid"], {"admin": False, "test": False})
            cur["admin"] = cur["admin"] or bool(r["is_admin"])
            cur["test"] = cur["test"] or bool(r["is_test"])
    except Exception:
        log.warning("login_logからの自分の端末判定に失敗", exc_info=True)
    return out


class _Ctx:
    """集計に共通の材料(ユーザー区分・自分の端末・管理者IP・IP接続元)。"""

    def __init__(self, conn) -> None:
        self.own = set(own_device_sids(conn))
        try:
            self.admin_ips = load_admin_known_ips()
        except Exception:
            log.warning("ADMIN_KNOWN_IPSの読み込みに失敗", exc_info=True)
            self.admin_ips = set()
        self.geo = {
            r["ip"]: (r["org"] or "", r["hostname"] or "")
            for r in conn.execute("SELECT ip, org, hostname FROM ip_geo_cache")
        }
        self.real_ids: set[int] = set()      # 一般の登録ユーザー
        self.nonreal_ids: set[int] = set()   # 管理者/テスト
        self.uid_by_name: dict[str, int] = {}
        self.reg_date: dict[int, str] = {}   # 実ユーザーの登録日(JST)
        for r in conn.execute(
            "SELECT id, username, role, is_test, "
            "substr(datetime(created_at, '+9 hours'), 1, 10) AS d "
            "FROM users"
        ):
            self.uid_by_name[r["username"]] = r["id"]
            if r["username"] == auth.GUEST_USERNAME:
                continue   # ゲスト疑似ユーザーは人ではない(どちらにも入れない)
            if r["role"] == "admin" or r["is_test"]:
                self.nonreal_ids.add(r["id"])
            else:
                self.real_ids.add(r["id"])
                self.reg_date[r["id"]] = r["d"]
        self._mark_cache: dict[tuple[str, str], int] = {}

    def bot_mark(self, ip: str, ua: str, recorded_mark: int) -> int:
        """1行が機械的アクセスなら0以外。記録時のbot_markと、UA+接続元の
        判定(admin_visit_trendと同じ基準)のどちらか。"""
        if recorded_mark:
            return recorded_mark
        k = (ip or "", ua or "")
        if k not in self._mark_cache:
            org, host = self.geo.get(ip or "", ("", ""))
            self._mark_cache[k] = visitor_kind.classify(
                [ua or ""], org, host, False)[0]
        return self._mark_cache[k]


def _key_of(guest_sid: str, ip: str) -> str:
    """訪問者キー。guest_sidが無い古い行だけIPで代用する(保存しない)。"""
    if guest_sid:
        return guest_sid
    return f"ip:{ip}" if ip else ""


# ---------------------------------------------------------------------------
# 日次の集計
# ---------------------------------------------------------------------------

def _load_user_activity(conn, ctx: _Ctx, lo: str, hi: str,
                        ) -> dict[str, set[int]]:
    """{JST日: その日に活動した実ユーザーid}。usage_events(操作)・単語/
    フレーズ試行・AI利用・ログイン成功のいずれか。"""
    out: dict[str, set[int]] = {}
    where = "created_at >= ? AND created_at < ?"

    def add(rows) -> None:
        for r in rows:
            if r["uid"] in ctx.real_ids:
                out.setdefault(r["d"], set()).add(r["uid"])

    add(conn.execute(
        f"SELECT DISTINCT user_id AS uid, {_DATE_SQL} AS d FROM usage_events "
        f"WHERE {where} AND kind NOT IN ('boot','leave') AND is_internal = 0",
        (lo, hi)))
    for tbl in ("word_attempts", "phrase_attempts", "ai_usage"):
        add(conn.execute(
            f"SELECT DISTINCT user_id AS uid, {_DATE_SQL} AS d FROM {tbl} "
            f"WHERE {where}", (lo, hi)))
    for r in conn.execute(
        f"SELECT DISTINCT username, {_DATE_SQL} AS d FROM login_log "
        f"WHERE {where} AND success = 1", (lo, hi)):
        uid = ctx.uid_by_name.get(r["username"])
        if uid in ctx.real_ids:
            out.setdefault(r["d"], set()).add(uid)
    return out


def _group_by_day(rows) -> dict[str, list]:
    out: dict[str, list] = {}
    for r in rows:
        out.setdefault(r["d"], []).append(r)
    return out


def compute_days(conn, start: str, end: str) -> dict[str, list[Row]]:
    """JST暦日start〜end(両端含む)を集計し、{日付: [(segment, metric,
    value), ...]}を返す(DBには書かない・読み取りだけ)。"""
    lo, _ = day_bounds_utc(start)
    _, hi = day_bounds_utc(end)
    ctx = _Ctx(conn)
    cond = "created_at >= ? AND created_at < ?"

    lv_by_day = _group_by_day(conn.execute(
        "SELECT guest_sid, ip, user_agent, kind, success, referrer_host, "
        "utm_source, utm_medium, has_gclid, landing_path, path, bot_mark, "
        f"is_internal, {_DATE_SQL} AS d FROM landing_visits "
        f"WHERE {cond} ORDER BY id", (lo, hi)))
    ue_by_day = _group_by_day(conn.execute(
        "SELECT user_id, guest_sid, ip, kind, category, label, is_internal, "
        f"{_DATE_SQL} AS d FROM usage_events WHERE {cond} ORDER BY id",
        (lo, hi)))
    ce_by_day = _group_by_day(conn.execute(
        "SELECT user_id, guest_sid, ip, is_internal, "
        f"{_DATE_SQL} AS d FROM client_errors WHERE {cond}", (lo, hi)))
    ai_by_day = _group_by_day(
        r for r in conn.execute(
            f"SELECT user_id, feature, {_DATE_SQL} AS d FROM ai_usage "
            f"WHERE {cond}", (lo, hi))
        if r["user_id"] in ctx.real_ids)

    activity = _load_user_activity(conn, ctx, lo, hi)
    login_rows: dict[str, list[int]] = {}
    for r in conn.execute(
        f"SELECT username, {_DATE_SQL} AS d FROM login_log "
        f"WHERE {cond} AND success = 1", (lo, hi)):
        uid = ctx.uid_by_name.get(r["username"])
        if uid in ctx.real_ids:
            login_rows.setdefault(r["d"], []).append(uid)
    new_users: dict[str, int] = {}
    for d in ctx.reg_date.values():
        if start <= d <= end:
            new_users[d] = new_users.get(d, 0) + 1
    revenue: dict[str, list[float]] = {}   # 日 -> [円, 件数]
    for r in conn.execute(
        "SELECT substr(datetime(detected_at, '+9 hours'), 1, 10) AS d, "
        "amount_jpy AS a FROM base_orders WHERE status != 'cancelled' "
        "AND detected_at >= ? AND detected_at < ?", (lo, hi)):
        cur = revenue.setdefault(r["d"], [0.0, 0])
        cur[0] += r["a"] or 0
        cur[1] += 1
    for r in conn.execute(
        f"SELECT {_DATE_SQL} AS d, amount_jpy AS a FROM paypay_payments "
        f"WHERE status = 'COMPLETED' AND {cond}", (lo, hi)):
        cur = revenue.setdefault(r["d"], [0.0, 0])
        cur[0] += r["a"] or 0
        cur[1] += 1
    chargers: dict[str, set[int]] = {}
    for r in conn.execute(
        f"SELECT user_id, {_DATE_SQL} AS d FROM balance_ledger "
        "WHERE reason IN ('charge_key_redeem', 'paypay_charge') "
        f"AND delta_jpy > 0 AND {cond}", (lo, hi)):
        if r["user_id"] in ctx.real_ids:
            chargers.setdefault(r["d"], set()).add(r["user_id"])

    return {
        d: _compute_one_day(
            d, ctx, lv_by_day.get(d, []), ue_by_day.get(d, []),
            ce_by_day.get(d, []), ai_by_day.get(d, []),
            activity.get(d, set()), login_rows.get(d, []),
            new_users.get(d, 0), revenue.get(d, [0.0, 0]),
            chargers.get(d, set()))
        for d in date_range(start, end)
    }


def _compute_one_day(d, ctx: _Ctx, lv, ue, ce, ai, active, logins,
                     n_new_users, rev, charger_ids) -> list[Row]:
    m: dict[tuple[str, str], float] = {}

    def bump(segment: str, metric: str, n: float = 1) -> None:
        m[(segment, metric)] = m.get((segment, metric), 0) + n

    # --- 除外するキー(ボット・自分) ---
    bot_keys: set[str] = set()
    internal_keys: set[str] = set()
    for r in lv:
        key = _key_of(r["guest_sid"], r["ip"])
        if not key:
            continue
        if ctx.bot_mark(r["ip"], r["user_agent"], r["bot_mark"]):
            bot_keys.add(key)
        if (r["is_internal"] or key in ctx.own
                or (r["ip"] and r["ip"] in ctx.admin_ips)):
            internal_keys.add(key)
    for r in ue:
        key = _key_of(r["guest_sid"], r["ip"])
        if key and r["is_internal"]:
            internal_keys.add(key)
    excluded = bot_keys | internal_keys

    def ue_ok(r) -> tuple[bool, str]:
        """人間の操作として数えてよい行か(と、その訪問者キー)。"""
        key = _key_of(r["guest_sid"], r["ip"])
        uid = r["user_id"]
        if r["is_internal"] or uid in ctx.nonreal_ids:
            return False, key
        if key and key in excluded:
            return False, key
        # 管理者の既知IPは、ログイン中の一般ユーザーの行には適用しない。
        if uid not in ctx.real_ids and r["ip"] and r["ip"] in ctx.admin_ips:
            return False, key
        return True, key

    # --- 訪問(landing_visits・kind='visit') ---
    first_visit: dict[str, object] = {}
    visit_counts: dict[str, int] = {}
    for r in lv:
        if r["kind"] != "visit":
            continue
        key = _key_of(r["guest_sid"], r["ip"])
        if not key or key in excluded:
            continue
        first_visit.setdefault(key, r)
        visit_counts[key] = visit_counts.get(key, 0) + 1
    visitors = set(first_visit)

    # 各訪問者が属するセグメント(その日の初回訪問で決める)。端末・着地・
    # referrer・utm_sourceは上位だけを保存対象にする。
    channel_of: dict[str, str] = {}
    dim_vals: dict[str, dict[str, str]] = {}
    dim_counts: dict[str, dict[str, int]] = {n: {} for n in DIM_TOP_N}
    for k, fv in first_visit.items():
        if not fv["landing_path"]:
            channel_of[k] = "channel:unknown"   # 流入元の記録を始める前の行
        else:
            channel_of[k] = "channel:" + traffic_source.classify_channel(
                fv["referrer_host"], fv["utm_source"], fv["utm_medium"],
                fv["has_gclid"])
        vals = {
            "device": ua_parse.parse_ua(fv["user_agent"])[0],
            "page": traffic_source.landing_group(fv["path"]),
            "referrer": fv["referrer_host"],
            "utm_source": fv["utm_source"],
        }
        dim_vals[k] = {n: _seg(v) for n, v in vals.items() if v}
        for n, v in dim_vals[k].items():
            dim_counts[n][v] = dim_counts[n].get(v, 0) + 1
    keep_dim = {
        n: {v for v, _ in sorted(c.items(), key=lambda x: -x[1])[:DIM_TOP_N[n]]}
        for n, c in dim_counts.items()
    }
    segs_cache: dict[str, list[str]] = {}

    def segs(key: str) -> list[str]:
        """このキーの指標を足すセグメント(チャネル＋端末/着地/…)。
        その日の訪問行が無いキーは channel:unattributed のみ。"""
        if key not in segs_cache:
            if key not in channel_of:
                segs_cache[key] = ["channel:unattributed"]
            else:
                segs_cache[key] = [channel_of[key]] + [
                    f"{n}:{v}" for n, v in dim_vals[key].items()
                    if v in keep_dim[n]]
        return segs_cache[key]

    m[("all", "visits")] = sum(visit_counts.values())
    m[("all", "visitors")] = len(visitors)
    m[("all", "visitors_bot_excluded")] = len(bot_keys)
    m[("all", "visitors_internal_excluded")] = len(internal_keys - bot_keys)
    m[("all", "visitors_gclid")] = sum(
        1 for k in visitors if first_visit[k]["has_gclid"])
    for k in visitors:
        for s in segs(k):
            bump(s, "visitors")
            bump(s, "visits", visit_counts[k])

    # --- 登録系(landing_visits・kind='signup') ---
    attempted: set[str] = set()
    done: set[str] = set()
    for r in lv:
        if r["kind"] != "signup":
            continue
        key = _key_of(r["guest_sid"], r["ip"])
        if not key or key in excluded:
            continue
        attempted.add(key)
        if r["success"] == 1:
            done.add(key)
    m[("all", "signup_attempted")] = len(attempted)
    m[("all", "signup_done")] = len(done)
    for k in attempted:
        for s in segs(k):
            bump(s, "signup_attempted")
    for k in done:
        for s in segs(k):
            bump(s, "signup_done")

    # --- 操作系(usage_events・計測開始日以降のみ) ---
    if d >= USAGE_MEASURE_START:
        boot: set[str] = set()
        ready: set[str] = set()
        engaged: set[str] = set()
        vword: set[str] = set()
        vaudio: set[str] = set()
        started: set[str] = set()
        events: dict[tuple[str, str], list] = {}   # (kind, cat) -> [回数, 人]
        click_n, click_actors, play_errors = 0, set(), 0
        for r in ue:
            kind, cat, label = r["kind"], r["category"], r["label"]
            ok, key = ue_ok(r)
            if not ok:
                continue
            if kind == "boot":
                if key and cat == "html":
                    boot.add(key)
                elif key and cat == "app_ready":
                    ready.add(key)
                continue
            if kind in _NON_ACTION_KINDS:
                continue
            if key:
                if kind in _ENGAGED_KINDS or (
                        kind == "page" and cat not in _NON_ENGAGED_PAGE_CATS):
                    engaged.add(key)
                if kind == "page" and cat == "word_detail":
                    vword.add(key)
                if kind == "play" and cat == "word":
                    vaudio.add(key)
                if ((kind == "page" and cat == "login_page"
                     and label == "via_signup_hash")
                        or (kind == "click" and cat == "signup_form"
                            and label == "opened")):
                    started.add(key)
            actor = f"u{r['user_id']}" if r["user_id"] in ctx.real_ids else key
            if kind == "play_error":
                play_errors += 1
            if kind == "click":
                # 登録フォームの欄別イベント(category='signup_form')は
                # ボタン押下ではなくフォームの計測なので、機能別の利用回数
                # には入れない(登録開始/離脱は専用の指標・画面で見る)。
                if cat != "signup_form":
                    click_n += 1
                    if actor:
                        click_actors.add(actor)
            elif kind in _FEATURE_KINDS:
                ev = events.setdefault((kind, cat), [0, set()])
                ev[0] += 1
                if actor:
                    ev[1].add(actor)
        human = visitors & (
            boot | {k for k, c in visit_counts.items() if c >= 2})
        m[("all", "visitors_js")] = len(boot & visitors)
        m[("all", "visitors_ready")] = len(ready & visitors)
        m[("all", "visitors_human")] = len(human)
        m[("all", "visitors_engaged")] = len(engaged & visitors)
        m[("all", "visitors_viewed_word")] = len(vword & visitors)
        m[("all", "visitors_tried_audio")] = len(vaudio & visitors)
        m[("all", "signup_started")] = len(started)
        m[("all", "play_errors")] = play_errors
        for k in visitors:
            for s in segs(k):
                if k in boot:
                    bump(s, "visitors_js")
                if k in human:
                    bump(s, "visitors_human")
                if k in engaged:
                    bump(s, "visitors_engaged")
        for k in started:
            for s in segs(k):
                bump(s, "signup_started")
        for (kind, cat), (n, actors) in sorted(
                events.items(), key=lambda x: -x[1][0])[:FEATURE_TOP_N]:
            name = f"feature:{kind}:{_seg(cat, 40)}"
            m[(name, "events")] = n
            m[(name, "actors")] = len(actors)
        if click_n:
            m[("feature:click", "events")] = click_n
            m[("feature:click", "actors")] = len(click_actors)
        m[("all", "active_users")] = len(active)
        n_err = 0
        for r in ce:
            key = _key_of(r["guest_sid"], r["ip"])
            if (r["is_internal"] or r["user_id"] in ctx.nonreal_ids
                    or (key and key in excluded)):
                continue
            n_err += 1
        m[("all", "client_errors")] = n_err

    # --- アカウント・課金(core・pruneされない) ---
    m[("all", "new_users")] = n_new_users
    m[("all", "logins")] = len(logins)
    m[("all", "login_users")] = len(set(logins))
    m[("all", "revenue_jpy")] = rev[0]
    m[("all", "payments")] = rev[1]
    m[("all", "chargers")] = len(charger_ids)
    ai_c: dict[str, list] = {}
    for r in ai:
        cur = ai_c.setdefault(_seg(r["feature"] or "(none)", 40), [0, set()])
        cur[0] += 1
        cur[1].add(r["user_id"])
    for name, (n, users) in sorted(
            ai_c.items(), key=lambda x: -x[1][0])[:FEATURE_AI_TOP_N]:
        m[(f"feature:ai:{name}", "events")] = n
        m[(f"feature:ai:{name}", "actors")] = len(users)

    return [(seg, metric, float(v)) for (seg, metric), v in m.items()]


def compute_cohorts(conn, now: datetime | None = None) -> list[tuple]:
    """登録日コホート×経過日のアクティブ人数を計算する(DBには書かない)。
    戻り値: [(cohort_date, offset_days, span_days, cohort_size, active), ...]。
    生ログが保持期間内に残っている日の分だけ計算する(それより古い日の
    セルは既存の行を触らない)。"""
    now = now or datetime.now(timezone.utc)
    ctx = _Ctx(conn)
    yday = jst_yesterday(now)
    cohorts: dict[str, list[int]] = {}
    for uid, d in ctx.reg_date.items():
        if USAGE_MEASURE_START <= d <= yday:
            cohorts.setdefault(d, []).append(uid)
    if not cohorts:
        return []
    # 生ログが完全に残っている最初の日(保持境界より新しい日)。
    act_lo = jst_today(now - timedelta(days=USAGE_KEEP_DAYS))
    while not is_raw_complete(act_lo, now):
        act_lo = add_days(act_lo, 1)
    act_lo = max(act_lo, min(cohorts))
    if act_lo > yday:
        return []
    lo, _ = day_bounds_utc(act_lo)
    _, hi = day_bounds_utc(yday)
    days_of: dict[int, set[str]] = {}
    for d, uids in _load_user_activity(conn, ctx, lo, hi).items():
        for u in uids:
            days_of.setdefault(u, set()).add(d)

    rows: list[tuple] = []
    for c, uids in sorted(cohorts.items()):
        size = len(uids)
        for k in range(0, COHORT_MAX_OFFSET + 1):
            a = add_days(c, k)
            if a > yday:
                break
            if a < act_lo:
                continue
            rows.append((c, k, 1, size, sum(
                1 for u in uids if a in days_of.get(u, ()))))
        for w in COHORT_WEEKS:
            first, last = add_days(c, 7 * w), add_days(c, 7 * w + 6)
            if last > yday or first < act_lo:
                continue   # 窓が未完了、または生ログが欠けている窓は書かない
            win = set(date_range(first, last))
            rows.append((c, 7 * w, 7, size, sum(
                1 for u in uids if win & days_of.get(u, set()))))
    return rows


# ---------------------------------------------------------------------------
# 保存・実行
# ---------------------------------------------------------------------------

def first_data_date(conn) -> str | None:
    """集計元(landing_visits・usage_events)の最古のJST日。"""
    cands = []
    for tbl in ("landing_visits", "usage_events"):
        r = conn.execute(
            f"SELECT MIN(created_at) AS m FROM {tbl}").fetchone()
        if r and r["m"]:
            cands.append(conn.execute(
                "SELECT substr(datetime(?, '+9 hours'), 1, 10)",
                (r["m"],)).fetchone()[0])
    return min(cands) if cands else None


def snapshotted_dates(conn) -> set[str]:
    return {r["date"] for r in conn.execute(
        "SELECT DISTINCT date FROM growth_daily "
        "WHERE segment = 'all' AND metric = 'visits'")}


def store_days(conn, days: dict[str, list[Row]]) -> int:
    """日ごとにまるごと入れ替えて保存する(冪等)。書いた行数を返す。"""
    n = 0
    for d, rows in days.items():
        conn.execute("DELETE FROM growth_daily WHERE date = ?", (d,))
        conn.executemany(
            "INSERT OR REPLACE INTO growth_daily "
            "(date, segment, metric, value) VALUES (?, ?, ?, ?)",
            [(d, seg, metric, val) for seg, metric, val in rows])
        n += len(rows)
    return n


def store_cohorts(conn, rows: list[tuple]) -> int:
    conn.executemany(
        "INSERT OR REPLACE INTO growth_cohort_daily "
        "(cohort_date, offset_days, span_days, cohort_size, active_users) "
        "VALUES (?, ?, ?, ?, ?)", rows)
    return len(rows)


def plan_days(conn, start: str | None, end: str | None,
              now: datetime | None = None, *, only_missing: bool = False,
              lookback: int = 0) -> tuple[list[str], list[str]]:
    """集計する日(生ログが完全な日)と、保持期間切れで触らない日を返す。
    start/end省略時は 最古の生ログ日〜昨日。only_missing=Trueなら未保存の日
    ＋直近lookback日だけに絞る。"""
    now = now or datetime.now(timezone.utc)
    yday = jst_yesterday(now)
    end = min(end or yday, yday)
    start = start or first_data_date(conn)
    if not start or start > end:
        return [], []
    want = date_range(start, end)
    if only_missing:
        have = snapshotted_dates(conn)
        recent = (set(date_range(max(start, add_days(end, -(lookback - 1))),
                                 end)) if lookback > 0 else set())
        want = [d for d in want if d not in have or d in recent]
    do = [d for d in want if is_raw_complete(d, now)]
    skipped = [d for d in want if not is_raw_complete(d, now)]
    return do, skipped


def run_snapshot(conn, start: str | None = None, end: str | None = None,
                 now: datetime | None = None, *, only_missing: bool = False,
                 lookback: int = 0, dry_run: bool = False) -> dict:
    """集計→保存を実行する(呼び出し側がdb()でコミットする)。"""
    now = now or datetime.now(timezone.utc)
    do, skipped = plan_days(conn, start, end, now, only_missing=only_missing,
                            lookback=lookback)
    result = {"days": len(do), "skipped_old": len(skipped), "rows": 0,
              "cohort_rows": 0, "first": do[0] if do else None,
              "last": do[-1] if do else None}
    if do:
        # 連続範囲でまとめて読み、必要な日だけ保存する。
        computed = compute_days(conn, do[0], do[-1])
        picked = {d: computed[d] for d in do}
        result["rows"] = (sum(len(v) for v in picked.values()) if dry_run
                          else store_days(conn, picked))
    cohorts = compute_cohorts(conn, now)
    result["cohort_rows"] = (len(cohorts) if dry_run
                             else store_cohorts(conn, cohorts))
    return result


def unsnapshotted_usage_days(conn, cutoff_utc: str) -> list[str]:
    """これから消す(created_at < cutoff_utc)usage_eventsを持つ日のうち、
    growth_dailyに未保存の日。空でなければpruneを止める判断材料。"""
    have = snapshotted_dates(conn)
    days = [r["d"] for r in conn.execute(
        f"SELECT DISTINCT {_DATE_SQL} AS d FROM usage_events "
        "WHERE created_at < ?", (cutoff_utc,))]
    return sorted(d for d in days if d >= USAGE_MEASURE_START and d not in have)


def write_status(conn, ok: bool, detail: dict, error: str = "") -> None:
    payload = {
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ok": bool(ok), "error": error[:300], **detail,
    }
    conn.execute(
        "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
        (STATUS_KEY, json.dumps(payload, ensure_ascii=False)))


def read_status(conn) -> dict | None:
    r = conn.execute(
        "SELECT value FROM app_state WHERE key = ?", (STATUS_KEY,)).fetchone()
    if not r or not r["value"]:
        return None
    try:
        return json.loads(r["value"])
    except ValueError:
        return None


def run_daily(lookback: int = 7, now: datetime | None = None,
              dry_run: bool = False) -> dict:
    """cron用の日次実行: 未保存の日と直近lookback日(既定7日・遅れて届いた
    記録や接続元の判定更新を取り込む)を冪等に再集計して保存し、結果を
    app_stateに残す。失敗したら例外を投げる(状態には失敗を記録する)。
    scripts/snapshot_growth_daily.pyと、pruneの直前に呼ぶ
    scripts/prune_usage_events.pyの両方から使う。"""
    try:
        with db() as conn:
            result = run_snapshot(
                conn, now=now, only_missing=True, lookback=lookback,
                dry_run=dry_run)
            if not dry_run:
                write_status(conn, True, {**result, "lookback": lookback})
        return result
    except Exception as e:
        if not dry_run:
            try:
                with db() as conn:
                    write_status(conn, False, {},
                                 error=f"{type(e).__name__}: {e}")
            except Exception:
                log.warning("日次集計の失敗状態の保存にも失敗", exc_info=True)
        raise
