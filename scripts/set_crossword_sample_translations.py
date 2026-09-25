# ruff: noqa: E501
"""クロスワードのサンプルのタイトル・説明・タグの多言語訳を`crossword_samples.i18n_json`へ
投入する(2026-09-26・多言語化)。

対象は`crossword_samples`テーブルの**`i18n_json`列だけ**。既存の日本語列
(title/description/domains/puzzle_json等)には一切触れない。対象行は**日本語
タイトルの完全一致**で特定する(サンプルのidはローカルと本番で食い違いうるため、idは使わない)。
一致しないタイトル(改名・削除された等)は飛ばして最後に一覧表示する。冪等
(同じ内容なら「変更なし」で何も書かない)。

    i18n_json = {"en": {"title", "description", "tags": [...]},
                 "zh-CN": {...}, "zh-TW": {...}}
    tagsは`domains`(カンマ区切り)と同じ順序・同じ個数(表示用の分野名の訳)。

使い方(リポジトリルートで・**既定はドライラン**=何も書かず、結果だけ表示):

    python scripts/set_crossword_sample_translations.py            # ドライラン
    python scripts/set_crossword_sample_translations.py --apply    # 実際に書く

DATA_DIRは他のスクリプト・アプリと同じ(環境変数`DATA_DIR`。未設定ならリポジトリの
`data/`)。**ローカルDBに対してだけ実行すること。本番への適用は、必ずオーナーが判断・
実行する**(本番のcontent.dbへ触るのはこのスクリプトの`--apply`が唯一で、書くのは
`i18n_json`列のみ)。

【実行前のバックアップ手順(--applyの前に必ず)】
    # ローカル
    sqlite3 data/content.db ".backup 'data/content.pre_cw_i18n_$(date +%Y%m%d).db'"
    # (VPSのコンテナ内で実行する場合は、コンテナのdata/へ同様に .backup してから。
    #  content.dbは音声等も含む大きなファイルなので、ディスクの空きを確認すること)

【実行後の確認】
    sqlite3 data/content.db "SELECT COUNT(*), SUM(i18n_json IS NOT NULL) FROM crossword_samples;"
    # → 件数は実行前と同じ・i18n_jsonが入った行数=一致したタイトルの数
    # users/landing_visits/usage_events等のライブデータのテーブルはこのスクリプトは
    # 一切触らない(core.db/logs.dbは開くだけで書かない)。念のため主要テーブルの件数も
    # 実行前後で比べること(CLAUDE.mdの「本番DBに書き込む操作をしたら件数を確認」)。

アプリ側: `app/database.py`の`_migrate`が`i18n_json`列をNULL許容で追加する(デプロイ後の
最初の起動で自動)。`app/routers/games.py`の`_localize_sample`が、`X-Lang`ヘッダの言語の
訳があればそれを、無ければ日本語を返す(JSONの形は変えず`tags`キーを足すだけ)。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# 分野名(サンプルの`domains`に並ぶ日本語名)→(en, zh-CN, zh-TW)。カンマは含めない
# (domainsがカンマ区切りのため)。
TAGS: dict[str, tuple[str, str, str]] = {
    "基礎語彙": ("Basic vocabulary", "基础词汇", "基礎詞彙"),
    "生活": ("Daily life", "生活", "生活"),
    "身体": ("Body", "身体", "身體"),
    "解剖学": ("Anatomy", "解剖学", "解剖學"),
    "保健": ("Health care", "保健", "保健"),
    "医療(症状)": ("Medical (symptoms)", "医疗(症状)", "醫療(症狀)"),
    "美容": ("Beauty", "美容", "美容"),
    "動物(哺乳類)": ("Animals (mammals)", "动物(哺乳类)", "動物(哺乳類)"),
    "動物(その他)": ("Animals (other)", "动物(其他)", "動物(其他)"),
    "動物(身近な動物)": ("Animals (familiar)", "动物(常见动物)", "動物(常見動物)"),
    "動物(鳥)": ("Animals (birds)", "动物(鸟类)", "動物(鳥類)"),
    "動物(昆虫)": ("Animals (insects)", "动物(昆虫)", "動物(昆蟲)"),
    "動物(魚類)": ("Animals (fish)", "动物(鱼类)", "動物(魚類)"),
    "爬虫類": ("Reptiles", "爬行动物", "爬蟲類"),
    "猫": ("Cats", "猫", "貓"),
    "犬": ("Dogs", "狗", "狗"),
    "動物(絶滅)": ("Animals (extinct)", "动物(灭绝)", "動物(絕種)"),
    "植物(花)": ("Plants (flowers)", "植物(花)", "植物(花)"),
    "植物(樹木)": ("Plants (trees)", "植物(树木)", "植物(樹木)"),
    "植物(身近な)": ("Plants (familiar)", "植物(常见)", "植物(常見)"),
    "植物(他)": ("Plants (other)", "植物(其他)", "植物(其他)"),
    "植物(草)": ("Plants (grasses)", "植物(草)", "植物(草)"),
    "農業・園芸": ("Agriculture and gardening", "农业・园艺", "農業・園藝"),
    "園芸・アクアリウム": ("Gardening and aquariums", "园艺・水族", "園藝・水族"),
    "建築・建物": ("Architecture and buildings", "建筑・建筑物", "建築・建築物"),
    "料理": ("Cooking", "料理", "料理"),
    "物理": ("Physics", "物理", "物理"),
    "化学": ("Chemistry", "化学", "化學"),
    "天文": ("Astronomy", "天文", "天文"),
    "地学": ("Earth science", "地学", "地學"),
    "数学": ("Mathematics", "数学", "數學"),
    "軍事": ("Military", "军事", "軍事"),
    "アマチュア無線・無線通信": ("Amateur radio and wireless communication", "业余无线电・无线通信", "業餘無線電・無線通訊"),
    "電気電子": ("Electrical and electronic", "电气电子", "電氣電子"),
    "電子工作": ("Electronics projects", "电子制作", "電子製作"),
    "アニメ": ("Anime", "动漫", "動漫"),
    "SF": ("Sci-fi", "科幻", "科幻"),
    "生物(想像上)": ("Creatures (imaginary)", "生物(想象中)", "生物(想像中)"),
    "ゲーム・Discordの英語": ("Gaming and Discord English", "游戏・Discord用语", "遊戲・Discord用語"),
    "ビジネス": ("Business", "商务", "商務"),
    "シンガポール英語": ("Singapore English", "新加坡英语", "新加坡英語"),
    "インド英語": ("Indian English", "印度英语", "印度英語"),
    "イギリス英語": ("British English", "英式英语", "英式英語"),
    "オーストラリア英語": ("Australian English", "澳大利亚英语", "澳洲英語"),
    "米英の違い": ("US-UK differences", "美英差异", "美英差異"),
    "和製英語": ("Japanese-made English", "和制英语", "和製英語"),
    "医療(病名)": ("Medical (disease names)", "医疗(病名)", "醫療(病名)"),
    "航空管制": ("Air traffic control", "空中交通管制", "空中交通管制"),
    "航空": ("Aviation", "航空", "航空"),
    "航空・宇宙": ("Aerospace", "航空・航天", "航空・太空"),
}

# 日本語タイトル → {言語: (タイトル, 説明)}。日本語の説明は、対象行のdescriptionが
# 想定と一致するかの確認用(食い違えば警告を出すが、タイトル一致なら投入は行う)。
SAMPLES: dict[str, dict] = {
    "はじめてのクロスワード（やさしい単語）": {
        "ja_desc": "TOEIC400点未満のやさしい基礎単語だけ。はじめての1問に。",
        "en": ("My First Crossword (Easy Words)", "Only easy basic words below TOEIC 400. A perfect first puzzle."),
        "zh-CN": ("第一次填字游戏（简单单词）", "只有TOEIC 400分以下的简单基础单词。最适合作为第一道题。"),
        "zh-TW": ("第一次填字遊戲（簡單單字）", "只有TOEIC 400分以下的簡單基礎單字。最適合作為第一道題。"),
    },
    "暮らしの英語クロスワード": {
        "ja_desc": "毎日の生活で使う、やさしい英語。",
        "en": ("Everyday Life English Crossword", "Easy English you use in daily life."),
        "zh-CN": ("生活英语填字游戏", "日常生活中会用到的简单英语。"),
        "zh-TW": ("生活英語填字遊戲", "日常生活中會用到的簡單英語。"),
    },
    "からだの英語クロスワード": {
        "ja_desc": "体の部位と体調の、やさしい英語。",
        "en": ("Body English Crossword", "Easy English for body parts and how you feel."),
        "zh-CN": ("身体英语填字游戏", "关于身体部位和身体状况的简单英语。"),
        "zh-TW": ("身體英語填字遊戲", "關於身體部位和身體狀況的簡單英語。"),
    },
    "どうぶつ大集合クロスワード": {
        "ja_desc": "ほ乳類から鳥・魚まで、動物の英語ぜんぶ。",
        "en": ("Animal Roundup Crossword", "English for animals of every kind, from mammals to birds and fish."),
        "zh-CN": ("动物大集合填字游戏", "从哺乳动物到鸟类、鱼类，动物的英语全都有。"),
        "zh-TW": ("動物大集合填字遊戲", "從哺乳動物到鳥類、魚類，動物的英語全都有。"),
    },
    "ペットと家畜のクロスワード": {
        "ja_desc": "イヌ・ネコから馬・ヤギまで、身近な動物のやさしい英語。",
        "en": ("Pets and Livestock Crossword", "Easy English for familiar animals, from dogs and cats to horses and goats."),
        "zh-CN": ("宠物与家畜填字游戏", "从狗、猫到马、山羊，身边常见动物的简单英语。"),
        "zh-TW": ("寵物與家畜填字遊戲", "從狗、貓到馬、山羊，身邊常見動物的簡單英語。"),
    },
    "花と緑のクロスワード": {
        "ja_desc": "庭とベランダの英語。バラ・ユリ・マツ。",
        "en": ("Flowers and Greenery Crossword", "English for the garden and balcony: rose, lily, pine."),
        "zh-CN": ("花与绿植填字游戏", "庭院和阳台的英语。玫瑰・百合・松树。"),
        "zh-TW": ("花與綠植填字遊戲", "庭院和陽台的英語。玫瑰・百合・松樹。"),
    },
    "建物と部屋のクロスワード": {
        "ja_desc": "家と町の建物の英語。",
        "en": ("Buildings and Rooms Crossword", "English for homes and the buildings of a town."),
        "zh-CN": ("建筑与房间填字游戏", "家和城镇建筑物的英语。"),
        "zh-TW": ("建築與房間填字遊戲", "家和城鎮建築物的英語。"),
    },
    "やさしい単語10問クロスワード": {
        "ja_desc": "やさしい単語だけ、たっぷり10語の大きめ盤面。",
        "en": ("Easy Words 10-Word Crossword", "A larger grid with a full 10 words, all easy ones."),
        "zh-CN": ("简单单词10题填字游戏", "只用简单单词，共10个词的较大盘面。"),
        "zh-TW": ("簡單單字10題填字遊戲", "只用簡單單字，共10個詞的較大盤面。"),
    },
    "料理の英語クロスワード": {
        "ja_desc": "キッチンと食卓の英語。レシピが読めるようになる語ばかり。",
        "en": ("Cooking English Crossword", "English for the kitchen and the table, with words that help you read recipes."),
        "zh-CN": ("料理英语填字游戏", "厨房和餐桌的英语。都是能帮您读懂食谱的词汇。"),
        "zh-TW": ("料理英語填字遊戲", "廚房和餐桌的英語。都是能幫您讀懂食譜的詞彙。"),
    },
    "理系のことばクロスワード": {
        "ja_desc": "物理・化学・天文・地学・数学のことば。",
        "en": ("Science Terms Crossword", "Terms from physics, chemistry, astronomy, earth science and mathematics."),
        "zh-CN": ("理科词汇填字游戏", "物理・化学・天文・地学・数学的词汇。"),
        "zh-TW": ("理科詞彙填字遊戲", "物理・化學・天文・地學・數學的詞彙。"),
    },
    "ミリタリー英語クロスワード": {
        "ja_desc": "軍事の基本語彙。洋画や海外ニュースで見かける言葉。",
        "en": ("Military English Crossword", "Basic military vocabulary, the kind of words you see in Hollywood films and international news."),
        "zh-CN": ("军事英语填字游戏", "军事基础词汇。在欧美电影和国际新闻中常见的词。"),
        "zh-TW": ("軍事英語填字遊戲", "軍事基礎詞彙。在歐美電影和國際新聞中常見的詞。"),
    },
    "無線とエレクトロニクスのクロスワード": {
        "ja_desc": "無線・電気電子・電子工作の入門語彙。",
        "en": ("Radio and Electronics Crossword", "Introductory vocabulary for radio, electrical and electronic engineering, and electronics hobby projects."),
        "zh-CN": ("无线电与电子学填字游戏", "无线电・电气电子・电子制作的入门词汇。"),
        "zh-TW": ("無線電與電子學填字遊戲", "無線電・電氣電子・電子製作的入門詞彙。"),
    },
    "SF・ゲームのクロスワード": {
        "ja_desc": "SF、アニメ、オンラインゲームで飛びかう英語。",
        "en": ("Sci-Fi and Games Crossword", "English that flies around in sci-fi, anime and online games."),
        "zh-CN": ("科幻・游戏填字游戏", "科幻、动漫、网络游戏中常见的英语。"),
        "zh-TW": ("科幻・遊戲填字遊戲", "科幻、動漫、線上遊戲中常見的英語。"),
    },
    "ビジネス英語クロスワード": {
        "ja_desc": "会議とメールの定番語。TOEIC頻出レンジ。",
        "en": ("Business English Crossword", "Standard words for meetings and emails, in the range that often appears on TOEIC."),
        "zh-CN": ("商务英语填字游戏", "会议和邮件中的常用词。TOEIC高频范围。"),
        "zh-TW": ("商務英語填字遊戲", "會議和郵件中的常用詞。TOEIC高頻範圍。"),
    },
    "TOEIC500点台（目安）の力だめしクロスワード": {
        "ja_desc": "基礎語彙から10語。今の実力をためす1問。",
        "en": ("TOEIC 500s (Approx.) Skills Check Crossword", "Ten words from the basic vocabulary. One puzzle to test your current level."),
        "zh-CN": ("TOEIC 500分段（参考）实力测试填字游戏", "从基础词汇中选出10个词。测试当前实力的一题。"),
        "zh-TW": ("TOEIC 500分段（參考）實力測試填字遊戲", "從基礎詞彙中選出10個詞。測試目前實力的一題。"),
    },
    "世界の英語クロスワード": {
        "ja_desc": "シンガポール英語・インド英語・英豪の言い回し。",
        "en": ("World Englishes Crossword", "Singapore English, Indian English, and British and Australian expressions."),
        "zh-CN": ("世界各地的英语填字游戏", "新加坡英语、印度英语、英国和澳大利亚的说法。"),
        "zh-TW": ("世界各地的英語填字遊戲", "新加坡英語、印度英語、英國和澳洲的說法。"),
    },
    "病名の英語クロスワード（上級）": {
        "ja_desc": "医療英語の中でも手ごわい病名だけを集めた上級編。",
        "en": ("Disease Names Crossword (Advanced)", "An advanced set with only the toughest disease names in medical English."),
        "zh-CN": ("病名英语填字游戏（高级）", "只收集医学英语中最棘手的病名的高级篇。"),
        "zh-TW": ("病名英語填字遊戲（高級）", "只收集醫學英語中最棘手的病名的高級篇。"),
    },
    "空と宇宙のクロスワード（上級）": {
        "ja_desc": "翼と推進、そして宇宙。航空宇宙のことば（上級）。",
        "en": ("Sky and Space Crossword (Advanced)", "Wings, propulsion, and space: aerospace vocabulary (advanced)."),
        "zh-CN": ("天空与宇宙填字游戏（高级）", "机翼与推进，以及宇宙。航空航天词汇（高级）。"),
        "zh-TW": ("天空與宇宙填字遊戲（高級）", "機翼與推進，以及宇宙。航空太空詞彙（高級）。"),
    },
    "ネコ好きの中級クロスワード": {
        "ja_desc": "猫の、日常でよく見聞きする英語。",
        "en": ("Intermediate Crossword for Cat Lovers", "English about cats that you often see and hear in daily life."),
        "zh-CN": ("爱猫人士的中级填字游戏", "日常生活中常见常听的关于猫的英语。"),
        "zh-TW": ("愛貓人士的中級填字遊戲", "日常生活中常見常聽的關於貓的英語。"),
    },
    "上級語彙の腕試しクロスワード（TOEIC600〜750）": {
        "ja_desc": "上級レンジの基礎語彙で腕試し。",
        "en": ("Advanced Vocabulary Challenge Crossword (TOEIC 600–750)", "Test yourself with basic vocabulary from the upper range."),
        "zh-CN": ("高级词汇实力挑战填字游戏（TOEIC 600〜750）", "用高级范围的基础词汇来试试身手。"),
        "zh-TW": ("高級詞彙實力挑戰填字遊戲（TOEIC 600〜750）", "用高級範圍的基礎詞彙來試試身手。"),
    },
    "天文クロスワード（太陽系の星々）": {
        "ja_desc": "惑星と恒星、太陽系の基本の英語。",
        "en": ("Astronomy Crossword (Stars of the Solar System)", "Basic English for planets, stars and the solar system."),
        "zh-CN": ("天文填字游戏（太阳系的星体）", "行星与恒星、太阳系的基础英语。"),
        "zh-TW": ("天文填字遊戲（太陽系的星體）", "行星與恆星、太陽系的基礎英語。"),
    },
    "航空無線・アマチュア無線クロスワード": {
        "ja_desc": "メーデーから月面反射通信まで、無線家の世界をのぞく10語。",
        "en": ("Aviation Radio and Amateur Radio Crossword", "Ten words that peek into the world of radio enthusiasts, from “Mayday” to moonbounce."),
        "zh-CN": ("航空无线电・业余无线电填字游戏", "从“Mayday”到月面反射通信，10个词带您一窥无线电爱好者的世界。"),
        "zh-TW": ("航空無線電・業餘無線電填字遊戲", "從「Mayday」到月面反射通訊，10個詞帶您一窺無線電愛好者的世界。"),
    },
}

LANGS = ("en", "zh-CN", "zh-TW")


def build_payload(title: str, domains: str) -> tuple[dict | None, list[str]]:
    """1件分のi18n_json(dict)を組み立てる。分野名の訳が足りなければNone+理由。"""
    spec = SAMPLES[title]
    tags_ja = [t for t in (domains or "").split(",") if t]
    missing = [t for t in tags_ja if t not in TAGS]
    if missing:
        return None, [f"分野名の訳が未登録: {missing}"]
    payload = {}
    for i, lang in enumerate(LANGS):
        name, desc = spec[lang]
        payload[lang] = {
            "title": name, "description": desc,
            "tags": [TAGS[t][i] for t in tags_ja],
        }
    return payload, []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", action="store_true",
                    help="実際に書き込む(既定はドライラン)")
    args = ap.parse_args()

    updated = unchanged = 0
    warnings: list[str] = []
    with db() as conn:
        cols = {r["name"] for r in conn.execute(
            "PRAGMA table_info(crossword_samples)")}
        if "i18n_json" not in cols:
            print("i18n_json列がまだありません"
                  + ("(--apply時に追加します)" if args.apply
                     else "(--apply時に追加されます・ドライランでは追加しません)"))
            if args.apply:
                conn.execute(
                    "ALTER TABLE crossword_samples ADD COLUMN i18n_json TEXT")
                cols.add("i18n_json")
        rows = conn.execute(
            "SELECT id, title, description, domains"
            + (", i18n_json" if "i18n_json" in cols else ", NULL AS i18n_json")
            + " FROM crossword_samples ORDER BY sort_order, id").fetchall()
        db_titles = {r["title"] for r in rows}
        for r in rows:
            title = r["title"]
            if title not in SAMPLES:
                warnings.append(f"訳が未登録のサンプル(日本語のまま): id={r['id']} {title}")
                continue
            if r["description"] != SAMPLES[title]["ja_desc"]:
                warnings.append(
                    f"日本語の説明が想定と異なります(訳が古い可能性・投入は行う): "
                    f"id={r['id']} {title}")
            payload, problems = build_payload(title, r["domains"])
            if payload is None:
                warnings.extend(f"id={r['id']} {title}: {p}" for p in problems)
                continue
            new_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
            old = r["i18n_json"]
            if old:
                try:
                    if json.dumps(json.loads(old), ensure_ascii=False,
                                  sort_keys=True) == new_json:
                        unchanged += 1
                        continue
                except ValueError:
                    pass
            print(f"{'更新' if args.apply else '更新予定'}: id={r['id']} {title}")
            if args.apply:
                conn.execute(
                    "UPDATE crossword_samples SET i18n_json = ? WHERE id = ?",
                    (new_json, r["id"]))
            updated += 1
        for t in SAMPLES:
            if t not in db_titles:
                warnings.append(f"DBに無いタイトル(改名・未登録?・訳は投入しない): {t}")
    print(f"\n{'書き込み' if args.apply else 'ドライラン'}: 更新{'した' if args.apply else 'される'}={updated} "
          f"変更なし={unchanged} 警告={len(warnings)}")
    for w in warnings:
        print("警告:", w)
    if not args.apply:
        print("(何も書き込んでいません。--applyで実行します)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
