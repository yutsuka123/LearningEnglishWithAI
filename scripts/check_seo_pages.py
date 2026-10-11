"""公開SEOページ(用語集・フレーズ集・サイトマップ)の検査(2026-10-12・ver1.5.14)。

  .venv/bin/python scripts/check_seo_pages.py     # 0=全部OK(本番・外部には触れない・.envの無い環境で実行)

隔離したDATA_DIR・MULTIUSER=1・FastAPIのTestClientで、次を確かめる:
 - 件数の上限(150)・「他N語」の案内・発音記号/例文訳/ニュアンスの表示
 - 例文と訳が食い違う語は訳を出さない(`_resolve_example_ja`の再利用)
 - XSS: DB由来の文字列は全てエスケープ・JSON-LDは`</script>`で抜けられない・JSON-LDが正しいJSON
 - 禁止用語: 分野/シーンページは404・一覧/サイトマップ/関連リンク/件数に一切出ない
 - detailが空/壊れた語でも落ちない・関連リンクは同じ大分類で最大12件・相互リンク(単語↔フレーズ)
 - サイトマップのlastmod・URL数・タイトル/説明文の長さ
"""

from __future__ import annotations

import atexit
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
_TMP = tempfile.mkdtemp(prefix="check_seo_")
atexit.register(shutil.rmtree, _TMP, ignore_errors=True)
os.environ.update({
    "DATA_DIR": _TMP, "ALLOW_FRESH_DB": "1", "MULTIUSER": "1", "SESSION_SECRET": "check-secret",
    "OPENAI_API_KEY": "sk-test-not-a-real-key",
})
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.database import db, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.routers import seo_pages  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("  OK   " if cond else "  FAIL ") + name + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


XSS = '<script>alert(1)</script>"\'&'
BIG = "検査大分野"          # 200語(上限150を超える)
SMALL = "検査小分野"         # 3語+壊れたdetail+訳が食い違う語+XSS
BANNED = ["禁止用語", "禁止用語（薬物）"]
SCENE_SAME = BIG             # 単語分野と同名のシーン(相互リンクの検査)
SCENE_B = "検査シーンB"
BANNED_SCENE = "禁止用語（注意喚起）"
NOIPA = "検査句動詞分野"        # 発音記号が無い分野(「発音記号つき」と書かない)
SLASH = "検査/スラッシュ名"       # 名前に/を含む(本番に3シーン実在: 例 IT・ビルド/エラー)


def seed() -> None:
    init_db()
    with db() as conn:
        for i in range(200):
            det = {"pronunciation": f"/ˈtɛst{i}/", "example_ja": f"検査の例文の訳{i}",
                   "example_ja_src": f"This is test sentence {i}.", "meanings": ["x"]}
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, example, domain, detail) VALUES (?,?,?,?,?,?)",
                (f"testword{i}", f"検査語{i}、別の意味", "名詞", f"This is test sentence {i}.", BIG, json.dumps(det, ensure_ascii=False)))
        # 小分野: 正常・訳が食い違う・detail空・detail壊れ・XSS
        good = {"pronunciation": "/ɡʊd/", "example_ja": "良い例文の訳", "example_ja_src": "A good example."}
        mism = {"pronunciation": "/mɪs/", "example_ja": "食い違う訳(出してはいけない)", "example_ja_src": "Some OTHER sentence."}
        xss_d = {"pronunciation": XSS, "example_ja": XSS, "example_ja_src": XSS}
        for eng, ja, ex, det in (
            ("good", "良い", "A good example.", json.dumps(good, ensure_ascii=False)),
            ("mismatch", "食い違い", "This sentence differs.", json.dumps(mism, ensure_ascii=False)),
            ("nodetail", "詳細なし", "No detail here.", ""),
            ("brokenjson", "壊れ", "Broken json.", "{not json"),
            (XSS, XSS, XSS, json.dumps(xss_d, ensure_ascii=False)),
        ):
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, example, domain, detail) VALUES (?,?,?,?,?,?)",
                (eng, ja, XSS if eng == XSS else "名詞", ex, SMALL, det))
        for dom in BANNED:
            for i in range(3):
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, example, domain, detail) VALUES (?,?,?,?,?,?)",
                    (f"bannedword{i}", f"禁止の語{i}", "名詞", f"Banned example {i}.", dom, "{}"))
        # フレーズ
        for i in range(160):
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene, detail) VALUES (?,?,?,?)",
                (f"Test phrase {i}.", f"検査フレーズ{i}", SCENE_SAME, json.dumps({"nuance": f"ニュアンス{i}"}, ensure_ascii=False)))
        for eng, ja, det in (("Phrase <b>x</b>", XSS, json.dumps({"nuance": XSS}, ensure_ascii=False)),
                             ("No detail phrase.", "詳細なしフレーズ", ""),
                             ("Broken phrase.", "壊れ", "{oops")):
            conn.execute("INSERT INTO phrases (english, japanese, scene, detail) VALUES (?,?,?,?)", (eng, ja, SCENE_B, det))
        for i in range(4):
            conn.execute("INSERT INTO words (english, japanese, part_of_speech, example, domain, detail) VALUES (?,?,?,?,?,?)",
                         (f"get over {i}", f"乗り越える{i}", "句動詞", f"I got over it {i}.", NOIPA, json.dumps({"example_ja": "x", "example_ja_src": f"I got over it {i}."}, ensure_ascii=False)))
        conn.execute("INSERT INTO phrases (english, japanese, scene, detail) VALUES (?,?,?,?)", ("Slash scene phrase.", "スラッシュ", SLASH, "{}"))
        conn.execute("INSERT INTO words (english, japanese, part_of_speech, example, domain, detail) VALUES (?,?,?,?,?,?)", ("slashword", "スラッシュ語", "名詞", "A slash example.", SLASH, "{}"))
        for i in range(2):
            conn.execute("INSERT INTO phrases (english, japanese, scene, detail) VALUES (?,?,?,?)",
                         (f"Banned phrase {i}", f"禁止フレーズ{i}", BANNED_SCENE, "{}"))


def ld_blocks(html: str) -> list[dict]:
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        out.append(json.loads(m.group(1)))
    return out


def main() -> int:
    seed()
    c = TestClient(app)

    # ---- 大きい分野: 上限150・案内・表示項目 ----
    t0 = time.time()
    r = c.get(f"/glossary/{quote(BIG)}")
    dt = time.time() - t0
    h = r.text
    check("大分野: 200", r.status_code == 200)
    check("大分野: 項目は150件(上限)", h.count('<li class="glossary-item">') == seo_pages.MAX_WORDS_PER_PAGE == 150)
    check("大分野: <li>と</li>が対応", h.count('<li class="glossary-item">') == h.count("</li>"))
    check("大分野: 「他50語」の案内", "他50語はアプリ内" in h)
    check("大分野: 件数の説明(全200語・先頭の150語)", "全200語" in h and "先頭の150語" in h)
    check("大分野: 発音記号が出る", '<span class="gl-ipa">/ˈtɛst0/</span>' in h)
    check("大分野: 例文の訳が出る(対応する訳)", "検査の例文の訳0" in h)
    check("大分野: 151番目以降は出ない", "testword150" not in h and "testword149" in h)
    check("大分野: 描画が1秒以内", dt < 1.0, f"{dt:.2f}s")
    m = re.search(r"<title>(.*?)</title>", h)
    check("大分野: titleに件数と特徴", m and "（200語）" in m.group(1) and "発音記号" in m.group(1), m.group(1) if m else "")
    d = re.search(r'<meta name="description" content="(.*?)" />', h)
    check("大分野: descriptionは150字以内で実際の語を含む", d and len(d.group(1)) <= 150 and "testword0" in d.group(1), d.group(1) if d else "")
    check("大分野: canonical", f'rel="canonical" href="https://study.nyangailab.com/glossary/{quote(BIG)}"' in h)
    lds = ld_blocks(h)
    bc = [x for x in lds if x.get("@type") == "BreadcrumbList"]
    check("大分野: JSON-LD(パンくず)が正しいJSONで3階層", len(bc) == 1 and len(bc[0]["itemListElement"]) == 3
          and bc[0]["itemListElement"][2]["item"].endswith("/glossary/" + quote(BIG)))
    check("大分野: 見えるパンくず", 'class="gl-bc"' in h and 'aria-current="page"' in h)
    check("大分野: 同名シーンへの相互リンク", f'href="/phrasebook/{quote(BIG)}"' in h)
    check("大分野: 関連リンクは自分自身を含まず最大12件", h.count('class="glossary-links gl-related"') <= 1
          and f'href="/glossary/{quote(BIG)}"' not in re.sub(r'<link[^>]*>', "", h))
    rel = re.findall(r'<a href="/glossary/[^"]*">', re.search(r'<p class="glossary-links gl-related">(.*?)</p>', h, re.S).group(1)) \
        if 'gl-related' in h else []
    check("大分野: 関連リンクは12件以下", len(rel) <= 12, str(len(rel)))

    # ---- 小分野: エスケープ・訳の食い違い・壊れたdetail ----
    r = c.get(f"/glossary/{quote(SMALL)}")
    h = r.text
    check("小分野: 200", r.status_code == 200)
    check("小分野: 全5語が出る(壊れたdetailでも落ちない)", h.count('<li class="glossary-item">') == 5)
    check("小分野: 対応する訳は出る", "良い例文の訳" in h)
    check("小分野: 食い違う訳は出さない", "食い違う訳(出してはいけない)" not in h)
    check("小分野: 全語表示なので「他N語」は出ない", "アプリ内でフラッシュカード" not in h and "全5語です" in h and "全語を" in h)
    body = h.split("</script>\n</head>")[-1] if "</script>\n</head>" in h else h
    check("小分野: XSS文字列は本文でエスケープ", "<script>alert(1)" not in re.sub(r'<script type="application/ld\+json">.*?</script>', "", h, flags=re.S)
          and "&lt;script&gt;alert(1)&lt;/script&gt;" in h)
    for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        check("小分野: JSON-LD内に生の<や>が無い", "<" not in blk and ">" not in blk)
    r2 = c.get(f"/phrasebook/{quote(SCENE_B)}")
    h2 = r2.text
    check("シーンB: 200・3件・壊れたdetailでも落ちない", r2.status_code == 200 and h2.count('<li class="glossary-item">') == 3)
    check("シーンB: XSS(英語/訳/ニュアンス)はエスケープ", "<b>x</b>" not in h2 and "&lt;b&gt;x&lt;/b&gt;" in h2
          and "<script>alert(1)" not in re.sub(r'<script type="application/ld\+json">.*?</script>', "", h2, flags=re.S))

    # ---- フレーズ ----
    r = c.get(f"/phrasebook/{quote(SCENE_SAME)}")
    h = r.text
    check("フレーズ大: 200・150件", r.status_code == 200 and h.count('<li class="glossary-item">') == 150)
    check("フレーズ大: 「他10件」", "他10件はアプリ内" in h)
    check("フレーズ大: ニュアンスが出る", "ニュアンス: ニュアンス0" in h)
    check("フレーズ大: 同名の単語分野への相互リンク", f'href="/glossary/{quote(SCENE_SAME)}"' in h)
    t = re.search(r"<title>(.*?)</title>", h).group(1)
    check("フレーズ大: titleに件数", "（160件）" in t, t)
    check("フレーズ大: JSON-LD(パンくず)", any(x.get("@type") == "BreadcrumbList" for x in ld_blocks(h)))

    # ---- 禁止用語は一切出ない ----
    for dom in BANNED:
        check(f"禁止: /glossary/{dom} は404", c.get(f"/glossary/{quote(dom)}").status_code == 404)
    check("禁止: /phrasebook/禁止用語（注意喚起） は404", c.get(f"/phrasebook/{quote(BANNED_SCENE)}").status_code == 404)
    leaks = []
    pages = ["/glossary", "/phrasebook", f"/glossary/{quote(BIG)}", f"/glossary/{quote(SMALL)}",
             f"/phrasebook/{quote(SCENE_SAME)}", f"/phrasebook/{quote(SCENE_B)}", "/sitemap.xml", "/crossword"]
    for p in pages:
        t = c.get(p).text
        for needle in ("禁止用語", quote("禁止用語"), "bannedword", "禁止の語", "Banned phrase", "禁止フレーズ"):
            if needle in t:
                leaks.append((p, needle))
    check("禁止: 一覧・分野・シーン・サイトマップのどこにも出ない", not leaks, str(leaks))
    idx = c.get("/glossary").text
    with db() as conn:
        pub = seo_pages.public_word_domains(conn)
        pubs = seo_pages.public_phrase_scenes(conn)
    check("索引: 件数は公開分のみ(禁止を含まない)", f"{sum(pub.values()):,}語" in idx and not any("禁止用語" in k for k in pub))
    pidx = c.get("/phrasebook").text
    check("索引(フレーズ): 件数は公開分のみ", f"{sum(pubs.values()):,}フレーズ" in pidx)
    check("索引: JSON-LD(パンくず)", any(x.get("@type") == "BreadcrumbList" for x in ld_blocks(idx)) and any(x.get("@type") == "BreadcrumbList" for x in ld_blocks(pidx)))

    # ---- サイトマップ ----
    sm = c.get("/sitemap.xml").text
    check("サイトマップ: lastmodは更新済み(2026-10-19)で古い9/7は残らない", "<lastmod>2026-10-19</lastmod>" in sm and "2026-09-07" not in sm)
    check("サイトマップ: 検査分野が入る", quote(BIG) in sm and quote(SCENE_B) in sm)
    check("サイトマップ: 全URLが絶対URL", all(u.startswith("https://study.nyangailab.com/") for u in re.findall(r"<loc>(.*?)</loc>", sm)))

    # ---- 発音記号が無い分野では「発音記号」と書かない ----
    hn = c.get(f"/glossary/{quote(NOIPA)}").text
    tn = re.search(r"<title>(.*?)</title>", hn).group(1)
    dn = re.search(r'<meta name="description" content="(.*?)" />', hn).group(1)
    check("発音記号なし分野: title/description/本文に「発音記号」を書かない", "発音記号" not in tn and "発音記号" not in dn
          and "発音記号" not in re.sub(r"<[^>]+>", "", hn.split('<h1>')[1].split('<ul')[0]), f"{tn} / {dn}")
    check("発音記号なし分野: 例文つきと書く", "例文つき" in tn)
    check("発音記号あり分野(大)は「発音記号・例文つき」", "発音記号・例文つき" in re.search(r"<title>(.*?)</title>", c.get(f"/glossary/{quote(BIG)}").text).group(1))

    # ---- 名前に/を含む分野/シーン・末尾スラッシュ ----
    check("スラッシュ入りシーン: 200", c.get(f"/phrasebook/{quote(SLASH)}").status_code == 200)
    check("スラッシュ入り分野: 200", c.get(f"/glossary/{quote(SLASH)}").status_code == 200)
    check("スラッシュ入り: エンコード(%2F)でも200", c.get(f"/phrasebook/{quote(SLASH, safe='')}").status_code == 200)
    check("サイトマップ/索引のスラッシュ入りURLが実際に200", all(
        c.get(u).status_code == 200 for u in re.findall(r"<loc>https://study\.nyangailab\.com(/(?:glossary|phrasebook)/[^<]*)</loc>", sm)))
    for base, name in (("glossary", BIG), ("phrasebook", SCENE_B)):
        rr = c.get(f"/{base}/{quote(name)}/", follow_redirects=False)
        check(f"末尾スラッシュ /{base}/…/ は正規URLへ301", rr.status_code == 301 and rr.headers["location"] == f"/{base}/{quote(name)}", str(rr.status_code))
    for base in ("glossary", "phrasebook"):
        rr = c.get(f"/{base}/", follow_redirects=False)
        check(f"/{base}/ は索引へ301", rr.status_code == 301 and rr.headers["location"] == f"/{base}")
    check("存在しないスラッシュ入りは404", c.get("/glossary/存在しない/名前").status_code == 404)

    # ---- 404ページ・crossword(従来どおり) ----
    check("存在しない分野は404", c.get("/glossary/存在しない分野").status_code == 404)
    check("crosswordは200", c.get("/crossword").status_code == 200)

    print()
    if FAILS:
        print(f"FAILED {len(FAILS)}: {FAILS}")
        return 1
    print("ALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
