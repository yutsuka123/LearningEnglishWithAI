#!/usr/bin/env python3
"""バックエンドの利用者向けメッセージの多言語化(app/services/messages.py)の整合性検査。

使い方(リポジトリルートで): .venv/bin/python scripts/check_message_i18n.py

検査内容:
 1. errors.ERROR_CODESの各コードに訳(en/zh-CN/zh-TW)があるか(管理者・運用者向けで
    意図的に日本語のままにするコードは除く)
 2. messages.MESSAGESの全キーが4言語そろい、プレースホルダー({name})が言語間で一致し、
    en/zh-CN/zh-TWにかな(日本語)が混入していないか
 3. コード中の messages.tr()/tr_ja()/tr_lang() のキー(文字列リテラル)が全て登録済みか
 4. errors.http_error()/error_response()に**日本語の文言リテラル**を直接渡している
    箇所が、登録済みの定型文か(または管理者向けとして許可済みか)

終了コード 0=問題なし・1=問題あり。
"""
from __future__ import annotations

import ast
import glob
import os
import re
import string
import sys

os.environ.setdefault("DATA_DIR", os.path.join(
    os.environ.get("TMPDIR", "/tmp"), "check_message_i18n_data"))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.services import errors, messages  # noqa: E402

KANA = re.compile("[぀-ヺー-ヿ]")
JA = re.compile("[぀-ヺー-ヿ㐀-鿿]")

# 意図的に日本語のままにするエラーコード(管理者・運用者向け)。
ADMIN_ONLY_CODES = {"3005", "3006", "3010", "3011", "3012", "3013", "3014",
                    "3015", "3017"}
# 管理画面・運用者向けのため、文言を直接渡していても翻訳しないファイル。
ADMIN_ONLY_FILES = {
    "app/routers/admin_memos.py", "app/routers/fulfillment.py",
    "app/routers/base_oauth.py", "app/routers/paypay_test.py",
    "app/routers/system.py",   # 管理者向けエンドポイントが中心(ユーザー向けの文言は無い)
}
# それ以外のファイルで日本語のまま残す文言(管理者専用操作・開発者向けの引数
# 不正メッセージ)。増やすときは「利用者に画面で見える文言か」を確認すること。
ALLOWED_UNTRANSLATED = {
    "管理者のみ閲覧できます。", "教材の削除は管理者のみ行えます。",
    "単語/フレーズの自動生成は管理者のみ行えます。",
    "フレーズの追加は管理者のみ行えます。", "フレーズの削除は管理者のみ行えます。",
    "単語の追加・変更は管理者のみ行えます。", "単語の削除は管理者のみ行えます。",
    "この単語には学習記録があるため削除できません。一覧から除外したい場合は、分野を「禁止用語」に変更してください。",
    "このフレーズには学習記録があるため削除できません。一覧から除外したい場合は、シーンを「禁止」で始まる名前に変更してください。",
    "更新する項目がありません", "domainを指定してください。",
    "既に主分類として設定されている分野です。",
    "source_typeはdomainかdeckを指定してください。", "clue_modeが不正です。",
    "english_styleが不正です。", "japanese_styleが不正です。",
    "answer_difficultyが不正です。", "periodはmonthかtotalを指定してください。",
    "hint_typeが不正です。",
}


def fields(text: str) -> set[str]:
    return {n for _, n, _, _ in string.Formatter().parse(text) if n}


def main() -> int:
    problems: list[str] = []
    # 1. エラーコード
    for code, (ja, _st) in errors.ERROR_CODES.items():
        if code in ADMIN_ONLY_CODES:
            continue
        tr = messages.ERROR_TRANSLATIONS.get(code)
        if not tr or len(tr) != 3 or not all(t.strip() for t in tr):
            problems.append(f"エラーコード{code}に訳(en/zh-CN/zh-TW)がありません: {ja[:40]}")
            continue
        for lang, t in zip(("en", "zh-CN", "zh-TW"), tr):
            if KANA.search(t.replace("・", "")):
                problems.append(f"エラーコード{code}の{lang}にかなが混入: {t[:40]}")
    for code in messages.ERROR_TRANSLATIONS:
        if code not in errors.ERROR_CODES:
            problems.append(f"ERROR_TRANSLATIONSに未定義のコード: {code}")
    # 2. MESSAGES
    for key, d in messages.MESSAGES.items():
        for lang in messages.SUPPORTED:
            if not d.get(lang, "").strip():
                problems.append(f"{key}: {lang}が空")
        base = fields(d["ja"])
        for lang in ("en", "zh-CN", "zh-TW"):
            if fields(d.get(lang, "")) != base:
                problems.append(f"{key}: {lang}のプレースホルダーがjaと不一致 {fields(d.get(lang, ''))} != {base}")
            if KANA.search(d.get(lang, "").replace("・", "")):
                problems.append(f"{key}: {lang}にかなが混入")
    # 3/4. コード走査
    keys = set(messages.MESSAGES)
    for path in sorted(glob.glob(os.path.join(ROOT, "app", "**", "*.py"), recursive=True)):
        rel = os.path.relpath(path, ROOT)
        tree = ast.parse(open(path, encoding="utf-8").read())
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            fn = n.func
            name = fn.attr if isinstance(fn, ast.Attribute) else (fn.id if isinstance(fn, ast.Name) else "")
            if name in ("tr", "tr_ja", "tr_lang") and isinstance(fn, ast.Attribute):
                idx = 1 if name == "tr_lang" else 0
                if len(n.args) > idx and isinstance(n.args[idx], ast.Constant) \
                        and isinstance(n.args[idx].value, str):
                    k = n.args[idx].value
                    if k not in keys:
                        problems.append(f"{rel}:{n.lineno}: 未登録の翻訳キー {k!r}")
                        continue
                    need = fields(messages.MESSAGES[k]["ja"])
                    got = {kw.arg for kw in n.keywords if kw.arg}
                    if got != need:
                        problems.append(f"{rel}:{n.lineno}: {k}のパラメータ不一致 need={sorted(need)} got={sorted(got)}")
            if name in ("http_error", "error_response") and len(n.args) >= 2:
                a = n.args[1]
                if isinstance(a, ast.Constant) and isinstance(a.value, str) and JA.search(a.value):
                    t = a.value
                    ok = (t in messages._JA_INDEX or t in messages._JA_TO_CODE
                          or t in ALLOWED_UNTRANSLATED or rel in ADMIN_ONLY_FILES)
                    if not ok:
                        problems.append(f"{rel}:{n.lineno}: 日本語の文言を直接渡していますが訳が未登録です: {t[:50]!r}")
                elif isinstance(a, ast.JoinedStr) and JA.search(ast.unparse(a)) and rel not in ADMIN_ONLY_FILES:
                    problems.append(f"{rel}:{n.lineno}: f文字列の日本語文言(messages.tr()に置き換えてください): {ast.unparse(a)[:50]}")
    # ja文の重複(逆引きの曖昧さ)
    seen: dict[str, str] = {}
    for k, d in messages.MESSAGES.items():
        if d["ja"] in seen:
            problems.append(f"日本語文が重複: {k} と {seen[d['ja']]}")
        seen[d["ja"]] = k
    print(f"エラーコード {len(errors.ERROR_CODES)} 件(うち翻訳 {len(messages.ERROR_TRANSLATIONS)}) / "
          f"個別メッセージ {len(messages.MESSAGES)} 件")
    for p in problems:
        print("NG:", p)
    print("問題なし" if not problems else f"問題 {len(problems)} 件")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
