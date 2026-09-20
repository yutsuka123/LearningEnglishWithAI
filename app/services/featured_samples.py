"""未登録・未課金向けの「まずはここから」厳選語と、トップの「1語サンプル」
(2026-09-20)。

**語はIDでなく(英語表記, 分野)で指定し、実行時にDBから解決する**。
ローカルと本番でIDが食い違いうるため(過去にIDだけで紐付けて誤配信した
事故あり・`audio_store`参照)。解決できなかった語(削除・改名・無料範囲外へ
移動)は黙って飛ばすだけで、一覧やトップが壊れることはない。

選定の方針: ①**未登録ゲストが無料で再生できる語だけ**(GUEST無料範囲＋
`access_tiers.SHOWCASE_WORDS`のショーケース語。ここで新たに無料にする語は
無く、無料かどうかは`access_tiers`の判定に従うだけ)、②音声が保存済みで
追加コスト0、③禁止用語ドメインは除外、④分野が散って「基礎語彙から
専門用語・ニッチ分野まで」が伝わる顔ぶれ。2026-09-20時点の本番で
候補すべてが(英語, 分野)一意・ゲスト無料範囲内・音声(男女)保存済み・
語源つきであることを読み取り専用で確認済み。
"""

from __future__ import annotations

import json
import sqlite3

# 一覧の先頭に固定する厳選語(この順に並べる・上限20語)。基礎英語とニッチ分野を
# 交互に混ぜ、先頭数語だけ見ても幅が伝わるようにしている。**妖怪の語**
# (Kappa/Tengu=ショーケース語・無料再生の例外。access_tiers.SHOWCASE_WORDS
# 参照)と西洋の怪物(werewolf/goblin/mermaid=同じくショーケース語、
# vampire=元からゲスト範囲内)を上位にまとめて見せる。ショーケース語5語は
# 必ずここに含める(単体テストで検証)。
MAX_FEATURED_WORDS = 20
FEATURED_WORDS: list[tuple[str, str]] = [
    ("sad", "基礎語彙"),                              # 基礎: 語源が意外
    ("Kappa", "生物(想像上)"),                        # 妖怪(河童)
    ("roger", "アマチュア無線・無線通信"),             # 無線
    ("Tengu", "生物(想像上)"),                        # 妖怪(天狗)
    ("lasagna", "イタリア料理"),                       # 料理
    ("werewolf", "生物(想像上)"),                     # 西洋の怪物
    ("vampire", "生物(想像上)"),                       # 西洋の怪物
    ("GPU", "半導体"),                                 # 専門用語
    ("goblin", "生物(想像上)"),                       # 西洋の怪物(小鬼)
    ("elevator / lift", "米英の違い"),                 # 基礎: 米英差
    ("mermaid", "生物(想像上)"),                      # 幻想生物
    ("shooting star", "天文"),                         # 天文
    ("stapler", "和製英語"),                           # 和製英語
    ("Zen", "宗教（日本）"),                           # 日本文化
    ("barbecue", "アメリカ料理"),                      # 料理
    ("magnet", "物理"),                                # 理科
    ("Tanabata", "お祭り"),                            # 日本の行事
    ("ukulele", "音楽(楽器)"),                         # 楽器
    ("dojo", "武道・格闘技"),                          # 武道
    ("dinosaur", "動物(絶滅)"),                        # 絶滅種
]
if len(FEATURED_WORDS) > MAX_FEATURED_WORDS:
    raise RuntimeError(f"FEATURED_WORDSは{MAX_FEATURED_WORDS}語まで")

# トップの「1語サンプル」の候補(先頭から順に、解決でき・語源の1行が
# 作れ・音声が保存済みの最初の語を使う)。ニッチな分野と語源が一度に
# 伝わる語を優先し、万一解決できなくても次の候補に落ちる。
HERO_CANDIDATES: list[tuple[str, str]] = [
    ("roger", "アマチュア無線・無線通信"),
    ("sad", "基礎語彙"),
    ("lasagna", "イタリア料理"),
    ("dojo", "武道・格闘技"),
]

# 1行表示にできる長さの上限(超える説明は出さない＝途中で切って意味を
# 変えたり捏造したりしない)。
_LINE_MAX = 90
_BANNED_DOMAIN = "禁止用語"   # app/routers/vocabulary.pyのBANNED_DOMAINと同値


def resolve_featured_word_ids(
    conn: sqlite3.Connection, allowed_ids: set[int],
) -> list[int]:
    """`FEATURED_WORDS`を実行時にword idへ解決して(指定順のまま)返す。
    `allowed_ids`(=ゲスト無料範囲のid集合)に入らない語は除外する。"""
    english = sorted({e for e, _ in FEATURED_WORDS})
    ph = ",".join("?" * len(english))
    rows = conn.execute(
        f"SELECT id, english, domain FROM words WHERE english IN ({ph}) "
        "AND COALESCE(domain, '') <> ? ORDER BY id",
        [*english, _BANNED_DOMAIN],
    ).fetchall()
    found: dict[tuple[str, str], int] = {}
    for r in rows:
        if r["id"] in allowed_ids:
            found.setdefault((r["english"], r["domain"]), r["id"])
    return [found[k] for k in FEATURED_WORDS if k in found]


def resolve_featured_phrase_ids(
    conn: sqlite3.Connection, allowed_ids: set[int],
) -> list[int]:
    """ミニフレーズ一覧の先頭に固定するフレーズ(=ショーケース・フレーズ)を
    実行時にidへ解決して(指定順のまま)返す。`allowed_ids`(ゲスト無料再生できる
    id集合)に入らないものは除外する。無料かどうかは`access_tiers`の判定に従う
    だけで、ここで新たに無料にするフレーズは無い。"""
    from . import access_tiers
    return [i for i in access_tiers.showcase_phrase_id_list(conn)
            if i in allowed_ids]


def _text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _first_sentence(text: str) -> str:
    """最初の一文(「。」まで)。無ければ全文。"""
    i = text.find("。")
    return text[: i + 1] if i >= 0 else text


def one_line_note(detail_json: str | None) -> tuple[str, str] | None:
    """`words.detail`(JSON)から1行の(見出し, 本文)を作る。語源(origin)の
    最初の一文を優先し、長すぎる/無い場合は豆知識(trivia)の最初の一文。
    どちらも無ければNone(=行を出さない)。既存の文の**一部をそのまま**
    使うだけで、言い換え・要約・生成はしない。"""
    try:
        d = json.loads(detail_json) if detail_json else None
    except ValueError:
        return None
    if not isinstance(d, dict):
        return None
    for label, key in (("語源", "origin"), ("豆知識", "trivia")):
        line = _first_sentence(_text(d.get(key)))
        if line and len(line) <= _LINE_MAX:
            return label, line
    return None


def resolve_hero_word(
    conn: sqlite3.Connection, guest_ids: set[int],
) -> dict | None:
    """トップの1語サンプルを実行時に解決する。条件: ゲスト無料範囲内・
    禁止用語でない・男女の音声が保存済み。語源/豆知識の1行が作れない
    候補は飛ばす(=常に「本物の解説つき」の語だけを見せる)。"""
    from . import audio_store  # 遅延import(起動時の依存を増やさない)
    for english, domain in HERO_CANDIDATES:
        rows = conn.execute(
            "SELECT id, english, japanese, domain, level, detail FROM words "
            "WHERE english = ? AND domain = ? AND domain <> ? ORDER BY id",
            (english, domain, _BANNED_DOMAIN),
        ).fetchall()
        for r in rows:
            if r["id"] not in guest_ids:
                continue
            note = one_line_note(r["detail"])
            if not note:
                continue
            if not all(
                audio_store.has(conn, "word", r["id"], "word", voice,
                                r["english"].strip())
                for voice in ("ash", "nova")
            ):
                continue
            return {
                "id": r["id"], "english": r["english"],
                "japanese": r["japanese"], "domain": r["domain"],
                "note_label": note[0], "note": note[1],
            }
    return None
