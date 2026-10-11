"""公開用の用語集・フレーズ集・クロスワード紹介ページ（2026-09-07新設）。

SPA本体は語彙・例文がJS描画の内側にあり、JavaScriptを実行しない
クローラー（多くの生成AIクローラーを含む）には本文がほぼ見えていない
という課題（docs/SEO_LLMO_STRATEGY.md参照）への対応。既存DBの内容を
そのままSSRして、ログイン不要・クロール可能な静的ページとして外に出す。

[重要] `禁止用語`(words.domain)・`禁止用語（注意喚起）`(phrases.scene)は
過去の禁止用語漏洩事故(2026-08-17)の教訓により、このページ群には
一切出さない。個別ページのURLを直接指定されても404になるよう、
「実際にDBから除外済みの一覧に含まれるか」で検証する（ドメイン名の
文字列比較だけに頼らない）。
"""

from __future__ import annotations

import html as html_lib
import json
import re
from urllib.parse import quote

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

from ..database import db
from .vocabulary import _resolve_example_ja

router = APIRouter()

BASE_URL = "https://study.nyangailab.com"

# 1ページに載せる件数の上限(2026-10-12: 40→150。検索の受け皿として中身を
# 厚くする。全分野の約8割(234分野中の約200)はこの上限に収まる)。
# 超える分はアプリ内で学べる旨を案内する。
MAX_WORDS_PER_PAGE = 150
MAX_PHRASES_PER_PAGE = 150
# 「関連する分野/シーン」リンクの最大数(内部リンク・同じ大分類から)。
MAX_RELATED_LINKS = 12

# 公開してはいけないドメイン/シーン。「禁止用語」を含むものは全て除外
# する（部分一致・2026-09-07修正: 完全一致だけだと`禁止用語（薬物）`の
# ような亜種を見落とすことが判明したため。words.domain/phrases.sceneに
# 今後同様の亜種が増えても自動的に拾えるよう、接頭辞ではなく部分一致で
# 判定する）。

# data/domain_audit/domain_reference.md の大分類（ナビゲーション用の
# 手作業マッピング）。新しいdomainがDBに増えた場合は_categorize_word()の
# フォールバック規則で拾われるので、ここへの追記は必須ではない。
_WORD_CATEGORY_MAP: dict[str, str] = {}
_WORD_CATEGORIES_SOURCE: dict[str, list[str]] = {
    "理学": ["物理", "化学", "生物学", "生化学", "地学", "数学", "統計学", "天文", "科学"],
    "工学": [
        "ソフトウェア工学", "機械工学", "電気電子", "音響工学", "土木工学",
        "都市工学", "防災工学", "経営工学", "生物工学", "車載組込み開発",
        "組み込み開発", "組み込み（ソフト）", "組み込み（エレキ）",  # 2026-09-09新設
        "品質工学", "半導体", "航空・宇宙", "海洋工学", "製造", "自動車工学",
        "醸造工学", "建築・建物", "自動車産業", "電池", "エネルギー",
        "人工衛星", "航空", "航空管制",
    ],
    "医療・健康": [
        "医療", "看護学", "保健", "美容", "解剖学", "助産学",
    ],
    "人文・社会": [
        "文学", "哲学", "宗教", "政治", "法律", "経済学", "歴史", "地理",
        "教養", "論文・学術", "階級社会", "職業", "軍事", "ニュース",
        "外交", "国際情勢", "法律(生活)", "認証・規制",
        "知的財産（一般）", "知的財産（著作権）", "知的財産（特許）",
        "知的財産（米国）", "知的財産（デザイン）", "知的財産（商標）",  # 2026-09-09新設
        "金融",  # 2026-09-13新設
    ],
    "芸術・文化": [
        "美術・博物館", "音楽", "芸術", "大衆文化", "デザイン用語",
        "話芸・コメディ", "日本文化", "米国文化", "中国文化", "欧州文化",
        "アジア文化", "文化(その他の国)", "陶芸",  # 2026-09-09新設
        "服飾", "ファッション", "色彩",  # 2026-09-13新設
    ],
    "自然": [
        "動物(身近な動物)", "動物(哺乳類)", "動物(鳥)", "動物(魚類)",
        "爬虫類", "両生類", "甲殻類", "軟体動物", "動物(昆虫)",
        "動物(絶滅)", "動物(その他)", "植物(身近な)", "植物(樹木)",
        "植物(花)", "植物(草)", "植物(絶滅)", "植物(他)", "生物(その他)",
        "生物(想像上)", "農業・園芸", "動物園・植物園", "犬", "猫",
        "漁業", "林業", "動物(類人猿)", "動物(旧人類)",  # 2026-09-09新設
    ],
    "料理・グルメ": [
        "料理", "和食", "アメリカ料理", "イギリス料理", "イタリア料理",
        "インド料理", "スペイン料理", "タイ料理", "ドイツ料理",
        "フランス料理", "ベトナム料理", "中東・ギリシャ料理", "中華料理",
        "韓国・メキシコ料理", "その他世界の料理", "コーヒー", "製菓・製パン",
    ],
    "趣味・エンタメ": [
        "スポーツ", "サッカー", "バスケットボール", "野球", "モータースポーツ",
        "ゲーム・Discordの英語", "TRPG・ボードゲーム", "アニメ", "SF",
        "サスペンス", "遊び", "コレクター", "DIY・工具", "手芸",
        "アマチュア無線・無線通信", "趣味・ガジェット", "電子工作",
        "アウトドア・レジャー", "園芸・アクアリウム", "多趣味・その他",
        "ダンス・大道芸", "球技・アウトドアスポーツ", "スポーツ科学",
        "将棋", "囲碁", "チェス", "オセロ", "パズル",
        "オリンピック・パラリンピック", "縫製機器",  # 2026-09-13新設
    ],
    "生活・実務": [
        "生活", "ビジネス", "不動産", "交通", "旅行", "冠婚葬祭", "管理",
        "タクシー", "米英の違い", "口語", "Web・SEO・LLMO", "恋愛", "鉄道",
        "船舶", "プレゼン・教える技術", "家電", "和製英語", "インバウンド",
        "お祭り", "経営学", "アパレル産業", "交通(古来)", "バス", "路面電車",
        "災害", "災害(種類)", "生地",  # 2026-09-13新設
    ],
    "IT・情報": ["IT", "AI", "IT(産業)", "フィジカルAI", "VR・AR"],
    "語学・試験": ["英検", "試験・資格"],
    "新語・流行": ["流行（2025）", "新語（2025）", "流行（2026）", "新語（2026）"],  # 2026-09-09新設
}
for _cat, _domains in _WORD_CATEGORIES_SOURCE.items():
    for _d in _domains:
        _WORD_CATEGORY_MAP[_d] = _cat

_WORD_CATEGORY_ORDER = list(_WORD_CATEGORIES_SOURCE.keys()) + ["その他"]

# フレーズの`scene`は話題ドメインだけでなく「言い回し・マナー」系も
# 多いため、単語とは別に会話機能カテゴリを設ける。
_PHRASE_FUNCTION_KEYWORDS = (
    "やんわり", "婉曲", "クッション言葉", "相槌", "つなぎ言葉", "依頼",
    "お願い", "許可を求める", "断る", "反論", "皮肉", "仮定法", "申し出",
    "もてなし", "近隣", "抗議", "クレーム", "ほめる", "注意する", "叱る",
    "お悔やみ", "直訳で失礼",
)


def _categorize_word(domain: str) -> str:
    if domain in _WORD_CATEGORY_MAP:
        return _WORD_CATEGORY_MAP[domain]
    prefixes = {
        "医療": "医療・健康", "薬学": "医療・健康",
        "動物": "自然", "植物": "自然", "生物": "自然",
        "音楽": "芸術・文化", "文学": "人文・社会", "歴史": "人文・社会",
        "宗教": "人文・社会", "IT": "IT・情報",
    }
    for prefix, cat in prefixes.items():
        if domain.startswith(prefix):
            return cat
    if "史" in domain:
        return "人文・社会"
    if domain.endswith("英語") or domain.endswith("英語の言い回し"):
        return "語学・試験"
    if "文化" in domain:
        return "芸術・文化"
    if "スポーツ" in domain:
        return "趣味・エンタメ"
    return "その他"


def _categorize_phrase(scene: str) -> str:
    if any(k in scene for k in _PHRASE_FUNCTION_KEYWORDS):
        return "会話の言い回し・マナー"
    # 「〇〇の英語」「〇〇英語」のような接尾辞を外して単語側の分類に寄せる。
    base = scene
    for suffix in ("の英語", "英語", "の交信", "の言い回し"):
        if base.endswith(suffix) and len(base) > len(suffix):
            base = base[: -len(suffix)]
            break
    return _categorize_word(base)


def public_word_domains(conn) -> dict[str, int]:
    rows = conn.execute(
        "SELECT domain, COUNT(*) c FROM words "
        "WHERE domain IS NOT NULL AND domain != '' "
        "GROUP BY domain",
    ).fetchall()
    return {
        r["domain"]: r["c"] for r in rows if "禁止用語" not in r["domain"]
    }


def public_phrase_scenes(conn) -> dict[str, int]:
    rows = conn.execute(
        "SELECT scene, COUNT(*) c FROM phrases "
        "WHERE scene IS NOT NULL AND scene != '' "
        "GROUP BY scene",
    ).fetchall()
    return {
        r["scene"]: r["c"] for r in rows if "禁止用語" not in r["scene"]
    }


# JS到達ビーコン(2026-09-19・計測設計3-B・Fable敵対的レビューS4)。SEO/LLM
# 経由の着地(/glossary等)にもindex.htmlと同じインラインbootを置き、「JSが
# 実行された人間訪問」を数えられるようにする(無いと、これらの着地は構造的に
# 人間訪問・JS到達が0になり、検索/LLM経由の効果測定が成立しない)。label='seo'。
# 失敗しても表示には影響させない。
_BOOT_BEACON = """<script>
(function () {
  try {
    var body = JSON.stringify({ kind: 'boot', category: 'html', label: 'seo',
      value: Math.round(performance.now()) });
    var ok = false;
    if (navigator.sendBeacon) {
      ok = navigator.sendBeacon('/api/system/track',
        new Blob([body], { type: 'application/json' }));
    }
    if (!ok && window.fetch) {
      fetch('/api/system/track', { method: 'POST', body: body, keepalive: true,
        headers: { 'Content-Type': 'application/json' } });
    }
  } catch (e) { /* 計測の失敗は無視 */ }
})();
</script>"""


def _json_ld(obj: dict) -> str:
    """構造化データ(JSON-LD)の`<script>`。`</script>`で抜けられないよう
    `<`・`>`・`&`をJSONのエスケープに置き換える(値は全てDB由来のため)。"""
    raw = json.dumps(obj, ensure_ascii=False)
    raw = raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f'<script type="application/ld+json">{raw}</script>'


def _breadcrumbs(items: list[tuple[str, str]]) -> tuple[str, str]:
    """パンくず。[(表示名, 絶対URL), ...]（最後が現在のページ）→
    (見えるナビのHTML, JSON-LDのscript)。"""
    links = []
    for i, (name, url) in enumerate(items):
        n = html_lib.escape(name)
        if i < len(items) - 1:
            links.append(f'<a href="{html_lib.escape(url)}">{n}</a>')
        else:
            links.append(f'<span aria-current="page">{n}</span>')
    nav = '<nav class="gl-bc" aria-label="パンくず">' + " › ".join(links) + "</nav>"
    ld = _json_ld({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": url}
            for i, (name, url) in enumerate(items)
        ],
    })
    return nav, ld


def _gloss(text: str, limit: int = 14) -> str:
    """説明文用に、日本語訳の最初の意味だけを短く取り出す。"""
    first = re.split(r"[、，,;；(（]", text or "")[0].strip()
    return first[:limit]


def _title(core: str, extra: str, brand: str = "｜nyangailab", limit: int = 60) -> str:
    """検索結果で切れにくいタイトル。長い分野名のときは補足(件数・特徴)を落とす。"""
    full = f"{core}｜{extra}{brand}" if extra else f"{core}{brand}"
    return full if len(full) <= limit else f"{core}{brand}"


def _short(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _load_detail(raw: str | None) -> dict:
    try:
        d = json.loads(raw) if raw else {}
    except (ValueError, TypeError):
        return {}
    return d if isinstance(d, dict) else {}


def _related_links(items: list[tuple[str, int]], base: str, unit: str) -> str:
    """同じ大分類の他の分野/シーンへの内部リンク(件数の多い順)。"""
    if not items:
        return ""
    links = "".join(
        f'<a href="{base}/{quote(name)}">{html_lib.escape(name)}（{count}{unit}）</a>'
        for name, count in items[:MAX_RELATED_LINKS])
    return f'<p class="glossary-links gl-related">{links}</p>'


def _page(title: str, description: str, canonical: str, body: str,
          jsonld: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html_lib.escape(title)}</title>
<meta name="description" content="{html_lib.escape(description)}" />
<meta name="robots" content="index, follow" />
<link rel="canonical" href="{html_lib.escape(canonical)}" />
<meta property="og:type" content="website" />
<meta property="og:title" content="{html_lib.escape(title)}" />
<meta property="og:description" content="{html_lib.escape(description)}" />
<meta property="og:url" content="{html_lib.escape(canonical)}" />
<meta property="og:site_name" content="nyangailab（にゃんがいらぼ）" />
<link rel="stylesheet" href="/static/css/page.css" />
<style>
.glossary-list{{list-style:none;padding:0;margin:0}}
.glossary-item{{padding:.6em 0;border-bottom:1px solid rgba(128,128,128,.25)}}
.glossary-cat{{margin:1.5em 0 .5em}}
.glossary-links a{{display:inline-block;margin:.2em .6em .2em 0}}
.glossary-bridge{{margin-top:2em;padding:1em;border-radius:8px;
  background:rgba(128,128,128,.08)}}
.gl-ipa{{opacity:.75;white-space:nowrap}}
.gl-ex,.gl-note{{margin-top:.25em;font-size:.95em}}
.gl-exja,.gl-note{{opacity:.8}}
.gl-bc{{font-size:.9em;margin-bottom:.8em;opacity:.85}}
.gl-related a{{margin:.25em .7em .25em 0}}
</style>
{jsonld}
</head>
<body>
{_BOOT_BEACON}
<div class="wrap">
<div class="card">
{body}
</div>
</div>
</body>
</html>"""


_BRIDGE_CTA = """
<div class="glossary-bridge">
  <p>このアプリは特定分野の単語だけのアプリではありません。日常会話・
  TOEIC対策の基礎語彙から、月額サブスクなしで前払い制（使った分だけ）で
  学べるAI英語学習アプリ<b>nyangailab</b>の一部です。</p>
  <p><a href="/">→ トップページでアプリを見る</a> ／
  <a href="/static/about.html">→ 使い方・料金の説明</a></p>
</div>
"""


@router.get("/glossary", response_class=HTMLResponse)
def glossary_index():
    with db() as conn:
        domains = public_word_domains(conn)
    by_cat: dict[str, list[tuple[str, int]]] = {}
    for domain, count in domains.items():
        by_cat.setdefault(_categorize_word(domain), []).append((domain, count))
    total_words = sum(domains.values())
    nav, ld = _breadcrumbs([
        ("nyangailab", f"{BASE_URL}/"),
        ("英単語 分野別用語集", f"{BASE_URL}/glossary"),
    ])
    parts = [
        nav,
        "<h1>英単語 分野別用語集</h1>",
        "<p>nyangailabに収録されている英単語を分野別に一覧できます。"
        "日常会話やTOEIC対策の基礎語彙に加え、専門用語やアマチュア無線・"
        "アニメ・世界各国の料理などニッチな分野まで、"
        f"{len(domains)}分野・{total_words:,}語を掲載しています。"
        "各語に日本語訳と例文があり、ほとんどの語に発音記号もついています。</p>",
    ]
    for cat in _WORD_CATEGORY_ORDER:
        items = sorted(by_cat.get(cat, []), key=lambda x: -x[1])
        if not items:
            continue
        parts.append(f'<h2 class="glossary-cat">{html_lib.escape(cat)}</h2>')
        parts.append('<p class="glossary-links">')
        for domain, count in items:
            href = f"/glossary/{quote(domain)}"
            parts.append(
                f'<a href="{href}">{html_lib.escape(domain)}'
                f'（{count}語）</a>')
        parts.append("</p>")
    parts.append(_BRIDGE_CTA)
    body = "\n".join(parts)
    return HTMLResponse(_page(
        f"英単語 分野別用語集（{len(domains)}分野・{total_words:,}語）｜日本語訳・例文つき｜nyangailab",
        "専門用語・アマチュア無線・航空・アニメ・世界各国の料理まで、"
        f"{len(domains)}分野{total_words:,}語の英単語を、日本語訳・例文・"
        "発音記号つきで無料で閲覧できる分野別用語集です。",
        f"{BASE_URL}/glossary",
        body,
        ld,
    ))


@router.get("/glossary/{domain:path}", response_class=HTMLResponse)
def glossary_domain(domain: str):
    with db() as conn:
        domains = public_word_domains(conn)
        if not domain.strip("/"):
            return RedirectResponse("/glossary", status_code=301)
        if domain not in domains and domain.rstrip("/") in domains:
            # 末尾スラッシュ付きは正規のURLへ(パス型にしたため従来の自動補正が効かない)
            return RedirectResponse(
                f"/glossary/{quote(domain.rstrip('/'))}", status_code=301)
        if domain not in domains:
            not_found_body = (
                "<h1>ページが見つかりません</h1>"
                '<p><a href="/glossary">→ 用語集トップへ戻る</a></p>'
            )
            return HTMLResponse(
                _page("見つかりませんでした｜nyangailab", "", "", not_found_body),
                status_code=404,
            )
        rows = conn.execute(
            "SELECT english, japanese, part_of_speech, example, detail "
            "FROM words WHERE domain = ? ORDER BY id LIMIT ?",
            (domain, MAX_WORDS_PER_PAGE),
        ).fetchall()
        scenes = public_phrase_scenes(conn)
    total = domains[domain]
    esc = html_lib.escape
    cat = _categorize_word(domain)
    related = sorted(
        ((d, c) for d, c in domains.items()
         if d != domain and _categorize_word(d) == cat),
        key=lambda x: -x[1])
    nav, ld = _breadcrumbs([
        ("nyangailab", f"{BASE_URL}/"),
        ("英単語 分野別用語集", f"{BASE_URL}/glossary"),
        (f"「{domain}」の英単語一覧", f"{BASE_URL}/glossary/{quote(domain)}"),
    ])
    shown = len(rows)
    items: list[str] = []
    samples = []
    ipa_count = 0
    for r in rows:
        detail = _resolve_example_ja(_load_detail(r["detail"]), r["example"] or "")
        ipa = detail.get("pronunciation")
        has_ipa_word = isinstance(ipa, str) and bool(ipa.strip())
        ipa_count += has_ipa_word
        ipa_html = (
            f' <span class="gl-ipa">{esc(_short(ipa, 60))}</span>'
            if has_ipa_word else "")
        pos_raw = r["part_of_speech"]
        pos = f"（{esc(pos_raw)}）" if pos_raw else ""
        example = esc(r["example"] or "")
        ex_ja = detail.get("example_ja")
        ex_html = ""
        if example:
            ex_html = f'<div class="gl-ex">例文: {example}'
            if isinstance(ex_ja, str) and ex_ja.strip():
                ex_html += f'<br><span class="gl-exja">{esc(ex_ja.strip())}</span>'
            ex_html += "</div>"
        items.append(
            '<li class="glossary-item">'
            f"<b>{esc(r['japanese'])}</b>は英語で"
            f"<b>{esc(r['english'])}</b>{ipa_html}{pos}。"
            f"{ex_html}</li>"
        )
        if len(samples) < 3:
            samples.append(f"{r['english']}（{_gloss(r['japanese'])}）")
    # 発音記号が付いているのが半数未満の分野(句動詞など)では「発音記号つき」と書かない
    feat = "発音記号・例文つき" if ipa_count * 2 >= shown else "例文つき"
    parts = [
        nav,
        f"<h1>「{esc(domain)}」の英単語一覧</h1>",
        f"<p>nyangailabに収録されている「{esc(domain)}」分野の"
        f"英単語は全{total}語です。"
        + (f"このページでは先頭の{shown}語を" if total > shown else "全語を")
        + f"日本語訳・{feat}で紹介します。</p>",
        '<ul class="glossary-list">',
        *items,
        "</ul>",
    ]
    if total > shown:
        parts.append(
            f"<p>他{total - shown}語はアプリ内でフラッシュカード・"
            "音声つきで学べます。</p>")
    if domain in scenes:
        parts.append(
            f'<p>この分野の会話フレーズ: <a href="/phrasebook/{quote(domain)}">'
            f"「{esc(domain)}」の英語フレーズ（{scenes[domain]}フレーズ）</a></p>")
    if related:
        parts.append(f"<h2 class=\"glossary-cat\">「{esc(cat)}」の他の分野</h2>")
        parts.append(_related_links(related, "/glossary", "語"))
    parts.append(_BRIDGE_CTA)
    parts.append('<p><a href="/glossary">→ 用語集トップ（他の分野を見る）</a></p>')
    body = "\n".join(parts)
    title = _title(f"「{domain}」の英単語一覧（{total}語）", feat)
    description = _short(
        f"「{domain}」の英単語{total}語を日本語訳・{feat}で一覧。"
        + ("、".join(samples) + "など。" if samples else "")
        + "ログイン不要で無料で閲覧できます。", 150)
    return HTMLResponse(_page(
        title, description, f"{BASE_URL}/glossary/{quote(domain)}", body, ld))


@router.get("/phrasebook", response_class=HTMLResponse)
def phrasebook_index():
    with db() as conn:
        scenes = public_phrase_scenes(conn)
    by_cat: dict[str, list[tuple[str, int]]] = {}
    for scene, count in scenes.items():
        by_cat.setdefault(_categorize_phrase(scene), []).append((scene, count))
    order = _WORD_CATEGORY_ORDER[:-1] + ["会話の言い回し・マナー", "その他"]
    total_phrases = sum(scenes.values())
    nav, ld = _breadcrumbs([
        ("nyangailab", f"{BASE_URL}/"),
        ("英語フレーズ集（シーン別）", f"{BASE_URL}/phrasebook"),
    ])
    parts = [
        nav,
        "<h1>英語フレーズ集（シーン別）</h1>",
        "<p>nyangailabに収録されている英語フレーズをシーン別に一覧できます。"
        f"{len(scenes)}シーン・{total_phrases:,}フレーズを掲載し、"
        "各フレーズに日本語訳とニュアンスの説明がついています。</p>",
    ]
    for cat in order:
        items = sorted(by_cat.get(cat, []), key=lambda x: -x[1])
        if not items:
            continue
        parts.append(f'<h2 class="glossary-cat">{html_lib.escape(cat)}</h2>')
        parts.append('<p class="glossary-links">')
        for scene, count in items:
            href = f"/phrasebook/{quote(scene)}"
            parts.append(
                f'<a href="{href}">{html_lib.escape(scene)}'
                f'（{count}フレーズ）</a>')
        parts.append("</p>")
    parts.append(_BRIDGE_CTA)
    body = "\n".join(parts)
    return HTMLResponse(_page(
        f"英語フレーズ集（{len(scenes)}シーン・{total_phrases:,}フレーズ）｜日本語訳つき｜nyangailab",
        "日常会話・ビジネス・旅行からアマチュア無線の交信、妖怪・伝承の話まで、"
        f"{len(scenes)}シーン{total_phrases:,}フレーズの英語表現を日本語訳と"
        "ニュアンスの説明つきで無料で閲覧できます。",
        f"{BASE_URL}/phrasebook",
        body,
        ld,
    ))


@router.get("/phrasebook/{scene:path}", response_class=HTMLResponse)
def phrasebook_scene(scene: str):
    with db() as conn:
        scenes = public_phrase_scenes(conn)
        if not scene.strip("/"):
            return RedirectResponse("/phrasebook", status_code=301)
        if scene not in scenes and scene.rstrip("/") in scenes:
            return RedirectResponse(
                f"/phrasebook/{quote(scene.rstrip('/'))}", status_code=301)
        if scene not in scenes:
            not_found_body = (
                "<h1>ページが見つかりません</h1>"
                '<p><a href="/phrasebook">→ フレーズ集トップへ戻る</a></p>'
            )
            return HTMLResponse(
                _page("見つかりませんでした｜nyangailab", "", "", not_found_body),
                status_code=404,
            )
        rows = conn.execute(
            "SELECT english, japanese, detail FROM phrases "
            "WHERE scene = ? ORDER BY id LIMIT ?",
            (scene, MAX_PHRASES_PER_PAGE),
        ).fetchall()
        domains = public_word_domains(conn)
    total = scenes[scene]
    esc = html_lib.escape
    cat = _categorize_phrase(scene)
    related = sorted(
        ((sc, c) for sc, c in scenes.items()
         if sc != scene and _categorize_phrase(sc) == cat),
        key=lambda x: -x[1])
    nav, ld = _breadcrumbs([
        ("nyangailab", f"{BASE_URL}/"),
        ("英語フレーズ集（シーン別）", f"{BASE_URL}/phrasebook"),
        (f"「{scene}」の英語フレーズ", f"{BASE_URL}/phrasebook/{quote(scene)}"),
    ])
    shown = len(rows)
    parts = [
        nav,
        f"<h1>「{esc(scene)}」の英語フレーズ</h1>",
        f"<p>nyangailabに収録されている「{esc(scene)}」の"
        f"英語フレーズは全{total}件です。"
        + (f"このページでは先頭の{shown}件を" if total > shown else "全件を")
        + "日本語訳とニュアンスの説明つきで紹介します。</p>",
        '<ul class="glossary-list">',
    ]
    samples = []
    for r in rows:
        nuance = _load_detail(r["detail"]).get("nuance")
        note = (
            f'<div class="gl-note">ニュアンス: {esc(_short(nuance, 200))}</div>'
            if isinstance(nuance, str) and nuance.strip() else "")
        parts.append(
            '<li class="glossary-item">'
            f"<b>{esc(r['english'])}</b><br>"
            f"{esc(r['japanese'])}{note}</li>"
        )
        if len(samples) < 2:
            samples.append(f"「{_short(r['english'], 40)}」")
    parts.append("</ul>")
    if total > shown:
        parts.append(
            f"<p>他{total - shown}件はアプリ内で音声つきで学べます。</p>")
    if scene in domains:
        parts.append(
            f'<p>この分野の英単語: <a href="/glossary/{quote(scene)}">'
            f"「{esc(scene)}」の英単語一覧（{domains[scene]}語）</a></p>")
    if related:
        parts.append(f"<h2 class=\"glossary-cat\">「{esc(cat)}」の他のシーン</h2>")
        parts.append(_related_links(related, "/phrasebook", "フレーズ"))
    parts.append(_BRIDGE_CTA)
    parts.append('<p><a href="/phrasebook">→ フレーズ集トップ（他のシーンを見る）</a></p>')
    body = "\n".join(parts)
    title = _title(f"「{scene}」の英語フレーズ・例文集（{total}件）", "日本語訳つき")
    description = _short(
        f"「{scene}」で使う英語フレーズ{total}件を日本語訳・ニュアンスの説明つきで紹介。"
        + ("、".join(samples) + "など。" if samples else "")
        + "ログイン不要で無料で閲覧できます。", 150)
    return HTMLResponse(_page(
        title, description, f"{BASE_URL}/phrasebook/{quote(scene)}", body, ld))


@router.get("/crossword", response_class=HTMLResponse)
def crossword_landing():
    with db() as conn:
        rows = conn.execute(
            "SELECT title, word_count, guest_playable FROM crossword_samples "
            "WHERE is_active = 1 ORDER BY sort_order LIMIT 12",
        ).fetchall()
    parts = [
        "<h1>英語クロスワードパズル（無料・ログイン不要で一部プレイ可）</h1>",
        "<p>nyangailabのクロスワードは、収録している英単語からその場で"
        "自動生成できる英語学習ゲームです。分野を選んで作成すると、"
        "その分野の語彙で復習になるクロスワードが作られます。"
        "登録不要のゲストでも、一部のサンプルパズルをそのままプレイ"
        "できます。</p>",
        "<h2>サンプルパズル</h2>",
        '<ul class="glossary-list">',
    ]
    for r in rows:
        badge = "🆓 ゲストでもプレイ可" if r["guest_playable"] else "要登録"
        parts.append(
            '<li class="glossary-item">'
            f"{html_lib.escape(r['title'])}"
            f"（{r['word_count']}問・{badge}）</li>"
        )
    parts.append("</ul>")
    parts.append(
        "<p>自分で分野を選んでクロスワードを自動生成する機能は、"
        "登録および課金ユーザー向けです。</p>")
    parts.append(_BRIDGE_CTA)
    parts.append(
        '<p><a href="/">→ トップページから「🎮 ゲーム」を開いてプレイする</a></p>')
    body = "\n".join(parts)
    return HTMLResponse(_page(
        "英語クロスワードパズル｜無料プレイあり｜nyangailab",
        "英単語から自動生成できる英語学習クロスワード。ログイン不要の"
        "ゲストでも一部サンプルを無料でプレイできます。",
        f"{BASE_URL}/crossword",
        body,
    ))
