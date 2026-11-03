"""ver1.5.23(概要ページの文言修正=クロスワードのサンプル数の表現 + 手動ブロックのfail2banフィルター修正)の静的検査。
本番にも開発DBにも触れない(ファイルを読むだけ)。使い方: リポジトリ直下で `python3 scripts/check_ver1523.py`(全項目OKなら終了コード0)。

確かめること:
  A. 概要ページ(about.html)に「サンプル全部」の断定が残っていない(ログイン済み無料の上限は20個・公開サンプルが20件を超えると嘘になるため)
  B. 4言語辞書(ja/en/zh-CN/zh-TW)の about.sec.tiers.14 / .30 が新しい表現に揃っている・古い断定が無い
  C. about.html の日本語(HTML直書き)と辞書の日本語(ja)が同じ文言(空白差は無視)
  D. 数字の主張が実際の上限と矛盾しない(ゲスト=5個・ログイン済み無料=20個・games.pyの定数と一致)
  E. 手動ブロックのフィルターのfailregexに<HOST>がある(11/2の導入失敗の再発防止)・実起動の検査スクリプトが存在する
  F. バージョン表記(APP_VERSION・CHANGELOG・release_notes)が揃っている
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
bad = 0
n = 0


def check(name, ok, detail=""):
    global bad, n
    n += 1
    if ok:
        print(f"  OK  {name}")
    else:
        bad += 1
        print(f"  NG  {name} {detail}")


html = (ROOT / "static/about.html").read_text(encoding="utf-8")
dict_src = (ROOT / "static/js/i18n_dict_about.js").read_text(encoding="utf-8")


def norm(s):
    return re.sub(r"\s+", "", s)


# 辞書を言語ごとに分ける(i18n_dict_about.js は "ja" / "en" / "zh-CN" / "zh-TW" の順に同じキーが並ぶ)
def lang_values(key):
    return re.findall(r'"' + re.escape(key) + r'":\s*"((?:[^"\\]|\\.)*)"', dict_src)


print("A. 概要ページの断定")
check("about.html に「サンプル全部」が残っていない", "サンプル全部" not in html)
check("about.html に新しい表現「サンプルがもっと遊べます」が2か所", html.count("サンプルがもっと遊べます") == 2, f"(実際 {html.count('サンプルがもっと遊べます')})")

print("B. 4言語辞書")
for key in ("about.sec.tiers.14", "about.sec.tiers.30"):
    vals = lang_values(key)
    check(f"{key}: 4言語分ある", len(vals) == 4, f"(実際 {len(vals)})")
    if len(vals) != 4:
        continue
    ja, en, zhcn, zhtw = vals
    check(f"{key}[ja]: 新しい表現", "サンプルがもっと遊べます" in ja and "サンプル全部" not in ja)
    check(f"{key}[en]: 新しい表現(more of the sample)", "play more of the sample" in en and "All the sample" not in en)
    check(f"{key}[zh-CN]: 新しい表現(更多的示例)", "更多的示例" in zhcn and "全部" not in zhcn.split("填字游戏")[0][-12:] and "所有示例" not in zhcn)
    check(f"{key}[zh-TW]: 新しい表現(更多的範例)", "更多的範例" in zhtw and "所有範例" not in zhtw)
    check(f"{key}: zh-CNに繁体字が混ざらない(遊/戲/範/開)", not re.search(r"[遊戲範開]", zhcn))
    check(f"{key}: zh-TWに簡体字が混ざらない(游/戏/范/开)", not re.search(r"[游戏范开]", zhtw))

print("C. HTMLの日本語と辞書(ja)の一致")
m14 = re.search(r'data-i18n="about\.sec\.tiers\.14">(.*?)</li>', html, re.S)
ja14 = lang_values("about.sec.tiers.14")[0]
check("tiers.14: HTMLとjaが同じ文言", bool(m14) and norm(m14.group(1)) == norm(ja14), f"(HTML={m14.group(1) if m14 else None!r})")
m30 = re.search(r'data-i18n="about\.sec\.tiers\.30">(.*?)</p>', html, re.S)
ja30 = lang_values("about.sec.tiers.30")[0]
check("tiers.30: HTMLとjaが同じ文言", bool(m30) and norm(m30.group(1)) == norm(ja30))

print("D. 数字の主張と実際の上限")
games = (ROOT / "app/routers/games.py").read_text(encoding="utf-8")
guest = int(re.search(r"^CW_SAMPLE_PLAY_LIMIT_GUEST\s*=\s*(\d+)", games, re.M).group(1))
free = int(re.search(r"^CW_SAMPLE_PLAY_LIMIT_FREE\s*=\s*(\d+)", games, re.M).group(1))
check(f"ゲストの上限(games.py={guest})とabout.htmlの「（{guest}個）」が一致", f"サンプルの一部（{guest}個）" in html)
check("無料登録の上限がゲストより多い(「もっと遊べます」が事実)", free > guest, f"(guest={guest}, free={free})")

print("E. 手動ブロックのfail2banフィルター")
fm = (ROOT / "deploy/fail2ban/filter.d/eigo-manual.conf").read_text(encoding="utf-8")
check("failregexに<HOST>がある", re.search(r"^failregex\s*=.*<HOST>", fm, re.M) is not None)
check("何にもマッチしない文字列(never-matches)のまま", "never-matches" in fm)
check("実起動の検査スクリプト(docker_loadtest.sh)が存在する", (ROOT / "deploy/fail2ban/tools/docker_loadtest.sh").exists())

print("F. バージョン表記")
cfg = (ROOT / "app/config.py").read_text(encoding="utf-8")
ver = re.search(r'^APP_VERSION\s*=\s*"(ver[\d.]+)"', cfg, re.M).group(1)
check("APP_VERSION=ver1.5.23", ver == "ver1.5.23", f"(実際 {ver})")
check("CHANGELOG.mdに見出しがある", f"## {ver}" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
rn = json.loads((ROOT / "release_notes.json").read_text(encoding="utf-8"))["versions"]
check("release_notes.jsonの先頭がAPP_VERSIONと同じ", rn[0]["version"] == ver, f"(実際 {rn[0]['version']})")
check("release_notesのpublicに内部の機能名を書いていない", all(not re.search(r"fail2ban|jail|ブロック|iptables|cron", t, re.I) for t in rn[0]["public"]))

print(f"\n{n - bad}/{n} 項目OK")
sys.exit(1 if bad else 0)
