#!/usr/bin/env python3
"""分野(単語のdomain)・シーン(フレーズのscene)・大分類の「表示名」の翻訳
(static/js/i18n_dict_taxonomy.js)の取りこぼし検査。

使い方(リポジトリルートで):
    .venv/bin/python scripts/check_taxonomy_i18n.py [content.dbのパス]
パスを省略すると DATA_DIR(未指定なら ./data)の content.db を**読み取り専用**で開く
(書き込みはしない・本番DBを直接指す場合も読み取りのみ)。

検査内容:
 1. DBに実在する全ての words.domain / phrases.scene(空を除く)と、
    app/services/taxonomy.py の WORD_CATEGORIES/PHRASE_CATEGORIES に載っている
    全ての大分類名・分野名・シーン名が、en/zh-CN/zh-TW の4言語(ja=恒等を含む)
    そろって辞書に登録されているか(取りこぼし=日本語のまま表示されてしまう名前)
 2. 4言語のキー集合が一致するか・同一ブロック内のキー重複が無いか
 3. en/zh-CN/zh-TW の値にかな(日本語)が混入していないか
 4. 同じ絞り込み一覧に並ぶ名前(分野同士・シーン同士・大分類同士)の訳が
    言語内で衝突していないか(同じ訳の項目が2つあると区別できない)
 5. OpenCCが入っていれば、zh-CNに繁体字・zh-TWに簡体字が混ざっていないか
    (OpenCCの字形表は厳しめで、判定は「要確認リスト」として表示する・終了コードには影響しない)

終了コード 0=問題なし・1=問題あり。
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.services import taxonomy  # noqa: E402

DICT_JS = os.path.join(ROOT, "static", "js", "i18n_dict_taxonomy.js")
KANA = re.compile("[぀-ヺー-ヿ]")
BLOCK_RE = re.compile(
    r'^  Object\.assign\(D(?:\.(ja|en)|\["(zh-CN|zh-TW)"\]), \{$')
ENTRY_RE = re.compile(r'^    "(tax\.[^"]+)": (".*"),$')
LANGS = ["ja", "en", "zh-CN", "zh-TW"]


def load_dict() -> tuple[dict[str, dict[str, str]], list[str]]:
    """i18n_dict_taxonomy.js を行ベースで読む(値はJSON文字列リテラルとして解釈)。
    戻り値=({lang: {key: value}}, 問題のリスト)。"""
    problems: list[str] = []
    out: dict[str, dict[str, str]] = {lang: {} for lang in LANGS}
    cur: str | None = None
    with open(DICT_JS, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.rstrip("\n")
            m = BLOCK_RE.match(line)
            if m:
                cur = m.group(1) or m.group(2)
                continue
            if line.startswith("  });"):
                cur = None
                continue
            m = ENTRY_RE.match(line)
            if m and cur:
                key, raw = m.group(1), m.group(2)
                try:
                    val = json.loads(raw)
                except ValueError:
                    problems.append(f"{DICT_JS}:{lineno}: 値がJSON文字列として読めない")
                    continue
                if key in out[cur]:
                    problems.append(f"重複キー({cur}): {key} (line {lineno})")
                out[cur][key] = val
            elif cur and line.strip() and not line.strip().startswith("//"):
                problems.append(f"{DICT_JS}:{lineno}: 読めない行: {line[:60]}")
    return out, problems


def db_values(db_path: str) -> tuple[list[str], list[str]]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        doms = [r[0] for r in con.execute(
            "SELECT DISTINCT domain FROM words "
            "WHERE domain IS NOT NULL AND domain != ''")]
        scs = [r[0] for r in con.execute(
            "SELECT DISTINCT scene FROM phrases "
            "WHERE scene IS NOT NULL AND scene != ''")]
    finally:
        con.close()
    return doms, scs


def main() -> int:
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        data_dir = os.environ.get("DATA_DIR") or os.path.join(ROOT, "data")
        db_path = os.path.join(data_dir, "content.db")
    if not os.path.exists(db_path):
        print(f"content.db が見つからない: {db_path}")
        return 1

    d, problems = load_dict()
    doms, scs = db_values(db_path)
    tax_doms = [x for v in taxonomy.WORD_CATEGORIES.values() for x in v]
    tax_scs = [x for v in taxonomy.PHRASE_CATEGORIES.values() for x in v]
    cats = list(dict.fromkeys(
        list(taxonomy.WORD_CATEGORIES) + list(taxonomy.PHRASE_CATEGORIES)
        + [taxonomy.OTHER_CATEGORY]))
    groups = {
        "分野": list(dict.fromkeys(doms + tax_doms)),
        "シーン": list(dict.fromkeys(scs + tax_scs)),
        "大分類": cats,
    }
    all_names = list(dict.fromkeys(sum(groups.values(), [])))

    # 1. 取りこぼし
    for lang in LANGS:
        miss = [n for n in all_names if "tax." + n not in d[lang]]
        if miss:
            problems.append(f"[{lang}] 訳が無い名前 {len(miss)}件: " + " / ".join(miss[:20])
                            + (" ..." if len(miss) > 20 else ""))
    # 2. キー集合の一致
    base = set(d["ja"])
    for lang in LANGS[1:]:
        extra = set(d[lang]) - base
        lack = base - set(d[lang])
        if extra or lack:
            problems.append(f"[{lang}] jaとキー集合が不一致: 余分{len(extra)}件・不足{len(lack)}件")
    # ja=恒等
    for k, v in d["ja"].items():
        if v != k[len("tax."):]:
            problems.append(f"[ja] 恒等でない: {k} -> {v}")
    # 3. かな混入
    for lang in ("en", "zh-CN", "zh-TW"):
        for k, v in d[lang].items():
            if KANA.search(v):
                problems.append(f"[{lang}] かな混入: {k} -> {v}")
    # 4. 一覧内の衝突
    for lang in ("en", "zh-CN", "zh-TW"):
        for gname, names in groups.items():
            seen: dict[str, str] = {}
            for n in names:
                v = d[lang].get("tax." + n)
                if v is None:
                    continue
                if v in seen and seen[v] != n:
                    problems.append(f"[{lang}] {gname}で訳が衝突: 「{seen[v]}」と「{n}」がどちらも {v}")
                seen.setdefault(v, n)

    # 5. 簡繁混在(OpenCCがあれば・参考表示)
    try:
        import opencc  # type: ignore
        t2s = opencc.OpenCC("t2s")
        s2t = opencc.OpenCC("s2t")
        warn = []
        for k, v in d["zh-CN"].items():
            body = re.sub(r"[^㐀-鿿]", "", v)
            if t2s.convert(body) != body:
                warn.append(f"[zh-CN] 繁体字混入の疑い: {k} -> {v}")
        for k, v in d["zh-TW"].items():
            body = re.sub(r"[^㐀-鿿]", "", v)
            if s2t.convert(body) != body:
                warn.append(f"[zh-TW] 簡体字混入の疑い: {k} -> {v}")
        for w in warn:
            print("要確認(OpenCC):", w)
        print(f"OpenCC簡繁チェック: 要確認 {len(warn)}件")
    except ImportError:
        print("(OpenCC未導入のため簡繁チェックは省略)")

    print(f"DB: 分野{len(doms)}種・シーン{len(scs)}種 / taxonomy.py: 大分類{len(cats)}・分野{len(set(tax_doms))}・シーン{len(set(tax_scs))}"
          f" / 検査対象の名前 {len(all_names)}件 / 辞書 {len(d['ja'])}キー×4言語")
    if problems:
        print("\n問題あり:")
        for p in problems:
            print(" -", p)
        return 1
    print("OK: 取りこぼし0・キー集合一致・かな混入なし・訳の衝突なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
