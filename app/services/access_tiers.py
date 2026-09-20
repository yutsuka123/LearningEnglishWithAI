"""B1(ゲスト/無料ユーザー)向けの「無料範囲」判定(2026-08-09、
2026-08-11に方針改訂)。

無料範囲 = レベルの低い順(基礎語優先)で①(未ログイン)単語1,000語・
フレーズ750件、②(ログイン無料)単語2,000語・フレーズ1,500件
（`docs/ACCESS_TIERS.md`参照）。固定フラグ列は持たせず、
`words.level`/`phrases.level`から都度計算する（語彙の追加・レベル
再判定があっても自動的に整合するようにするため）。

**2026-09-20の例外(ショーケース語)**: 上記のレベル昇順の範囲とは別に、
トップの訴求(妖怪・ニッチ分野)を登録なしで体験してもらうための**ごく少数の
紹介用の語**(`SHOWCASE_WORDS`・上限`MAX_SHOWCASE_WORDS`語)だけを、ゲスト・
ログイン無料・課金者のいずれでも無料再生にする。範囲判定
(`free_range_ids`/`is_free_range`/`free_range_id_filter`)がこれらを含めて
返すので、再生課金(`charge_playback_if_needed`)・🆓/🔒表示・「🔊再生できる
ものだけ」・課金別ソートは常に同じ結果になる。範囲の件数(①1,000語・②2,000語)
自体は変えず、ショーケース語は**上乗せ**(範囲内の語を押し出さない)。それ
以外の語の課金・🔒は変わらない。

**2026-08-11の方針転換**: 一覧・検索・詳細は①②とも無料範囲に関わらず
常時無料公開に変更（ニッチ分野の広さを隠さないため）。この無料範囲は
**音声再生の可否のみ**を左右する: 無料範囲内の単語・フレーズは誰でも
(ゲスト相当含め)何度でも無料で再生できるが、範囲外は課金ユーザーの
チャージ残高を消費する（`app/services/ai.py`の
`charge_playback_if_needed`参照）。旧`detail_block_message`(詳細を
無料範囲外でブロックする関数)はこの方針転換により2026-08-11に削除した。
"""

from __future__ import annotations

import logging
import sqlite3

log = logging.getLogger(__name__)

FREE_WORDS_LIMIT = 2000      # ②(ログイン無料)向け
FREE_PHRASES_LIMIT = 1500
GUEST_WORDS_LIMIT = 1000     # ①(未ログイン)向け・②の半分
GUEST_PHRASES_LIMIT = 750

# ショーケース語(2026-09-20・オーナー決定): 無料範囲の外にある語のうち、
# 「妖怪」などトップで訴求する分野を登録なしで聴いてもらうための少数。語は
# IDでなく(英語表記, 分野)で指定し、実行時にDBから解決する(ローカルと本番で
# IDが食い違いうるため)。**この一覧を増やすときは必ずオーナー確認**
# (課金対象を減らす変更のため)。上限は`MAX_SHOWCASE_WORDS`で固定し、
# 超えるとimport時に失敗する(気づいたら増えていた、を防ぐ)。
# 選定(2026-09-20・本番の読み取り調査): ゲスト無料範囲の外・男女の音声が保存済み
# (8KB以上)・detailに語源と豆知識あり・禁止用語でない。Kappa/werewolf/
# goblin/mermaidはログイン無料範囲には既に入っており、実際に増えるのは
# ゲストの再生のみ(ログイン済みの課金への影響はTenguのみ)。
SHOWCASE_WORDS: list[tuple[str, str]] = [
    ("Kappa", "生物(想像上)"),      # 河童
    ("Tengu", "生物(想像上)"),      # 天狗
    ("werewolf", "生物(想像上)"),   # 狼男
    ("goblin", "生物(想像上)"),     # ゴブリン(小鬼)
    ("mermaid", "生物(想像上)"),    # 人魚
]
MAX_SHOWCASE_WORDS = 10
if len(SHOWCASE_WORDS) > MAX_SHOWCASE_WORDS:
    raise RuntimeError(
        f"SHOWCASE_WORDSは{MAX_SHOWCASE_WORDS}語まで(オーナー決定)。"
        "増やす場合はオーナー確認の上でMAX_SHOWCASE_WORDSを見直すこと。")
_BANNED_DOMAIN = "禁止用語"   # app/routers/vocabulary.pyのBANNED_DOMAINと同値
_showcase_warned: set[tuple[str, str]] = set()   # 警告は語ごとに1回だけ

# app/routers/vocabulary.py の LEVEL_ORDER と同一スケール(words/phrases共通)。
# ここで独自に持つのは循環インポート回避のため（vocabulary.py はルーター）。
LEVEL_ORDER = [
    "300-", "300", "350", "400", "450", "500", "550", "600", "650",
    "700", "750", "800", "850", "900", "950", "990", "990+",
]


def _level_rank_case(column: str = "level") -> str:
    """レベル文字列を昇順ソート可能な整数に変換するCASE式（未知の値・
    空欄は最後尾扱い＝無料範囲の優先対象にしない）。"""
    whens = " ".join(
        f"WHEN '{lv}' THEN {i}" for i, lv in enumerate(LEVEL_ORDER)
    )
    return f"(CASE {column} {whens} ELSE {len(LEVEL_ORDER) + 1} END)"


# 一覧ルーターが「無料で聞ける順」ソートのSQLを組むために使う公開名
# （ここ以外で同じCASE式を再実装しない＝無料範囲の判定と並びの基準を
# 一致させるため・2026-09-20）。
level_rank_case = _level_rank_case


def billing_order(
    rows: list, guest_ids: set[int], free_ids: set[int], *, desc: bool = False,
) -> list:
    """一覧を「無料で聞ける順」(課金別ソート・2026-09-20)に並べ替える。

    並び = ①未登録ゲストが無料再生できる範囲(guest_ids) → ②ログイン無料の
    範囲(free_idsのうち①を除く) → ③それ以外(有料範囲)。各グループ内の
    並びは呼び出し側が渡した`rows`の順（レベル昇順→タイブレーク）を保つ
    (sortedは安定ソート)。`desc=True`ならグループ順も含め全体を反転する。
    無料範囲そのもの(どの語が①②か)はレベル昇順の上位N件という既存の
    判定(`free_range_ids`)をそのまま使うので、再生可否の表示(🆓/🔒)と
    必ず一致する。
    """
    def group(r) -> int:
        i = r["id"]
        if i in guest_ids:
            return 0
        return 1 if i in free_ids else 2

    ordered = sorted(rows, key=group)
    return ordered[::-1] if desc else ordered


def _table_and_limit(
    item_type: str, *, guest: bool = False,
) -> tuple[str, int]:
    if item_type == "phrase":
        limit = GUEST_PHRASES_LIMIT if guest else FREE_PHRASES_LIMIT
        return "phrases", limit
    return "words", (GUEST_WORDS_LIMIT if guest else FREE_WORDS_LIMIT)


def showcase_word_ids(conn: sqlite3.Connection) -> set[int]:
    """`SHOWCASE_WORDS`を実行時にword idへ解決して返す。(英語表記,分野)が
    ちょうど1件に決まらない語(未解決=削除・改名／曖昧=同じ組が複数)は
    **黙って飛ばし**、語ごとに1回だけ警告ログを出す。禁止用語ドメインの
    語は対象にしない。"""
    english = sorted({e for e, _ in SHOWCASE_WORDS})
    ph = ",".join("?" * len(english))
    rows = conn.execute(
        f"SELECT id, english, domain FROM words WHERE english IN ({ph}) "
        "AND COALESCE(domain, '') <> ?",
        [*english, _BANNED_DOMAIN],
    ).fetchall()
    found: dict[tuple[str, str], list[int]] = {}
    for r in rows:
        found.setdefault((r["english"], r["domain"]), []).append(r["id"])
    ids: set[int] = set()
    for key in SHOWCASE_WORDS:
        hit = found.get(key, [])
        if len(hit) == 1:
            ids.add(hit[0])
        elif key not in _showcase_warned:
            _showcase_warned.add(key)
            log.warning(
                "ショーケース語を解決できないため無料再生の対象外にします: "
                "%s / %s (該当%d件)", key[0], key[1], len(hit))
    return ids


def _showcase_ids_for(conn: sqlite3.Connection, item_type: str) -> set[int]:
    """無料範囲に上乗せするid(単語のみ。フレーズにショーケース語は無い)。"""
    return showcase_word_ids(conn) if item_type == "word" else set()


def free_range_id_filter(
    conn: sqlite3.Connection, item_type: str, *, guest: bool = False,
) -> tuple[str, list]:
    """一覧クエリに足せる「無料範囲内のみ」のWHERE断片とパラメータを返す
    （🔊再生できるものだけ表示フィルター用・2026-08-11）。ショーケース語
    (単語のみ)は範囲に上乗せして含める(2026-09-20)。"""
    table, limit = _table_and_limit(item_type, guest=guest)
    rank_expr = _level_rank_case()
    clause = (
        "id IN (SELECT id FROM ("
        f"  SELECT id, ROW_NUMBER() OVER (ORDER BY {rank_expr}, id) AS rn "
        f"  FROM {table}"
        ") WHERE rn <= ?)"
    )
    params: list = [limit]
    extra = sorted(_showcase_ids_for(conn, item_type))
    if extra:
        clause = f"({clause} OR id IN ({','.join('?' * len(extra))}))"
        params += extra
    return clause, params


def free_range_ids(
    conn: sqlite3.Connection, item_type: str, *, guest: bool = False,
) -> set[int]:
    """`free_range_id_filter`と同じ判定を、リクエスト単位で1回のSELECTだけ
    実行してidの集合として返す（一覧/quiz応答の各行に`is_free_range`を
    付与する用途。行ごとにランク計算するのを避けるため・2026-08-12）。
    ショーケース語(単語のみ)は範囲に上乗せして含める(2026-09-20)。"""
    table, limit = _table_and_limit(item_type, guest=guest)
    rank_expr = _level_rank_case()
    rows = conn.execute(
        f"SELECT id FROM ("
        f"  SELECT id, ROW_NUMBER() OVER (ORDER BY {rank_expr}, id) AS rn "
        f"  FROM {table}"
        f") WHERE rn <= ?",
        (limit,),
    ).fetchall()
    return {r["id"] for r in rows} | _showcase_ids_for(conn, item_type)


def is_free_range(
    conn: sqlite3.Connection, item_type: str, item_id: int, *,
    guest: bool = False,
) -> bool:
    """指定した単語/フレーズが無料範囲(レベル昇順の上位N件、またはショー
    ケース語)に入っているか。``guest=True``で①(未ログイン)向けのより狭い
    範囲を使う(ショーケース語はゲスト・ログイン共通で無料)。"""
    table, limit = _table_and_limit(item_type, guest=guest)
    rank_expr = _level_rank_case()
    row = conn.execute(
        f"SELECT rn FROM ("
        f"  SELECT id, ROW_NUMBER() OVER (ORDER BY {rank_expr}, id) AS rn "
        f"  FROM {table}"
        f") WHERE id = ?",
        (item_id,),
    ).fetchone()
    if not row:
        return False
    if row["rn"] <= limit:
        return True
    return item_id in _showcase_ids_for(conn, item_type)
