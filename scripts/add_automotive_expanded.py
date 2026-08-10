# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Expand the existing "自動車産業"/"自動車工学" domains with additional
vocabulary and dealer/mechanic-facing phrases, authored by Claude
(2026-08-10・ユーザー要望).

対象語彙: 電気自動車・自動運転の深掘り(BEV、急速充電、充電ケーブル、運転支
援システム)、燃料・燃料系統(ガソリン各種、ディーゼル、吸気/排気バルブ)、
駆動・変速系統(CVT、四輪駆動、FF/FR、ドライブベルト/シャフト、エンジンシ
リンダー)、車種・ボディタイプ(ピックアップトラック、軽自動車、クーペ、セ
ダン、ハッチバック、ステーションワゴン)。加えて、フレーズが使うディーラー
商談・車検/整備の場面をカバーするための関連語(試乗、月々の支払い、延長保
証、認定中古車、代車など)も補った。

**ドメインの振り分け方針**: ビジネス・消費者向け(車種/ボディタイプ、購入・
契約・充電インフラに関わる語)は既存の`自動車産業`へ、メカ・技術寄り(燃料
の種類、バルブ、駆動系の部品・方式)は既存の`自動車工学`へ、内容に応じて
行ごとに割り振った。

**既存語との衝突回避(複合見出し化)**: 事前に`自動車産業`/`自動車工学`の
既存55語、および全ドメイン横断でのユニーク語を確認したところ、以下が判明
したため、単独形ではなく自動車文脈の複合見出しにした、または追加を見送っ
た。
- `belt`は`武道・格闘技`(柔道帯)で既存 → `drive belt`という複合見出しで追加。
- `cylinder`は`機械工学`(一般機械)で既存 → `engine cylinder`という複合見出
  しで追加。
- `shaft`は`機械工学`で既存 → `drive shaft`という複合見出しで追加。
- `valve`は`機械工学`で既存 → `intake valve` / `exhaust valve`という複合見
  出しで追加。
- `internal combustion engine`は`機械工学`に既存 → 今回は追加しない。
- `regenerative braking`は既に`自動車工学`に存在 → 追加しない(要求トピック
  だが既存語のため見送り)。
- `fuel tank`は`航空・宇宙`ドメインに既存 → 追加しない(要求トピックだが既
  存語のため見送り)。
- `down payment`は`不動産`ドメインに既存 → 代わりに整備の文脈で使う
  `loaner car`(代車)を追加した。
- `manual transmission`は既に`自動車工学`に存在するため、口語的な同義語
  `stick shift`のみを新規追加した(`manual transmission mode`という新語は
  追加しなかった)。

フレーズはディーラーで車を選ぶ・商談する場面、整備士とのやり取りの場面で
実際に使う自然な表現。scene は既存の`自動車産業の英語`(ディーラー商談の
フレーズが既にあるシーン)を再利用した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_automotive_expanded.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 自動車産業: 電気自動車・自動運転の深掘り ---
    ("battery electric vehicle (BEV)", "バッテリー電気自動車(BEV)", "名詞", "A battery electric vehicle (BEV) runs entirely on electricity stored in its battery.", "自動車産業", "500"),
    ("fast charging", "急速充電", "名詞", "Fast charging can restore most of the battery in about thirty minutes.", "自動車産業", "500"),
    ("charging cable", "充電ケーブル", "名詞", "Make sure the charging cable is fully connected before you leave the car.", "自動車産業", "500"),
    ("driving assistance system", "運転支援システム", "名詞", "The driving assistance system can keep the car centered in its lane.", "自動車産業", "600"),
    # --- 自動車産業: 車種・ボディタイプ ---
    ("kei car", "軽自動車", "名詞", "A kei car is a small, fuel-efficient vehicle popular in Japan for city driving.", "自動車産業", "550"),
    ("pickup truck", "ピックアップトラック", "名詞", "He uses a pickup truck to haul equipment for his business.", "自動車産業", "450"),
    ("coupe", "クーペ", "名詞", "The coupe has only two doors but a sportier roofline than the sedan.", "自動車産業", "450"),
    ("sedan", "セダン", "名詞", "A sedan usually has four doors and a separate trunk.", "自動車産業", "450"),
    ("hatchback", "ハッチバック", "名詞", "The hatchback's rear door opens upward, giving easy access to cargo space.", "自動車産業", "450"),
    ("station wagon", "ステーションワゴン", "名詞", "A station wagon offers more cargo space than a sedan of the same length.", "自動車産業", "500"),
    # --- 自動車産業: ディーラー商談・購入関連 ---
    ("test drive", "試乗", "名詞", "Would you like to schedule a test drive this weekend?", "自動車産業", "450"),
    ("loaner car", "代車", "名詞", "The dealership gave us a loaner car while ours was being repaired.", "自動車産業", "550"),
    ("monthly payment", "月々の支払い", "名詞", "The monthly payment depends on the loan term you choose.", "自動車産業", "500"),
    ("extended warranty", "延長保証", "名詞", "We recommend adding an extended warranty for extra peace of mind.", "自動車産業", "600"),
    ("certified pre-owned", "認定中古車(の)", "形容詞", "Certified pre-owned vehicles go through a strict inspection before resale.", "自動車産業", "650"),
    ("options package", "オプションパッケージ", "名詞", "The options package adds leather seats and a premium sound system.", "自動車産業", "550"),
    ("vehicle registration", "車両登録", "名詞", "You'll need your vehicle registration to renew your insurance.", "自動車産業", "600"),
    ("fuel efficiency rating", "燃費評価", "名詞", "This model has one of the best fuel efficiency ratings in its class.", "自動車産業", "600"),
    ("safety rating", "安全性能評価", "名詞", "The car earned a five-star safety rating in independent testing.", "自動車産業", "550"),
    ("sticker price", "(車両の)表示価格", "名詞", "The sticker price doesn't include tax, title, or registration fees.", "自動車産業", "550"),
    # --- 自動車工学: 燃料・燃料系統 ---
    ("gasoline", "ガソリン", "名詞", "This car runs on gasoline, not diesel.", "自動車工学", "400"),
    ("unleaded gasoline", "無鉛ガソリン", "名詞", "Modern engines are designed to run on unleaded gasoline.", "自動車工学", "550"),
    ("diesel engine", "ディーゼルエンジン", "名詞", "A diesel engine typically produces more torque at low speeds than a gasoline engine.", "自動車工学", "500"),
    ("diesel fuel", "軽油・ディーゼル燃料", "名詞", "Make sure you fill the tank with diesel fuel, not gasoline.", "自動車工学", "500"),
    ("premium gasoline", "ハイオクガソリン", "名詞", "High-performance engines often require premium gasoline.", "自動車工学", "550"),
    ("regular gasoline", "レギュラーガソリン", "名詞", "Most everyday cars run fine on regular gasoline.", "自動車工学", "550"),
    ("intake valve", "吸気バルブ", "名詞", "The intake valve opens to let the air-fuel mixture into the cylinder.", "自動車工学", "650"),
    ("exhaust valve", "排気バルブ", "名詞", "The exhaust valve releases burned gases out of the cylinder.", "自動車工学", "650"),
    # --- 自動車工学: 駆動・変速系統 ---
    ("stick shift", "マニュアル車・スティックシフト(口語)", "名詞", "He prefers driving a stick shift over an automatic.", "自動車工学", "550"),
    ("continuously variable transmission (CVT)", "無段変速機(CVT)", "名詞", "A continuously variable transmission (CVT) changes gear ratios smoothly instead of shifting between fixed gears.", "自動車工学", "700"),
    ("drive belt", "ドライブベルト", "名詞", "A worn drive belt can start to squeal when the engine is cold.", "自動車工学", "600"),
    ("drive shaft", "ドライブシャフト・推進軸", "名詞", "The drive shaft transfers power from the transmission to the wheels.", "自動車工学", "650"),
    ("four-wheel drive (4WD)", "四輪駆動(4WD)", "名詞", "Four-wheel drive (4WD) gives extra traction on rough or slippery terrain.", "自動車工学", "550"),
    ("front-engine front-wheel drive (FF)", "フロントエンジン・前輪駆動(FF)", "名詞", "Most compact cars use a front-engine front-wheel drive (FF) layout.", "自動車工学", "700"),
    ("front-engine rear-wheel drive (FR)", "フロントエンジン・後輪駆動(FR)", "名詞", "Many sports cars use a front-engine rear-wheel drive (FR) layout for better balance.", "自動車工学", "700"),
    ("engine cylinder", "エンジンシリンダー", "名詞", "Each engine cylinder houses a piston that moves up and down.", "自動車工学", "600"),
    # --- 自動車工学: 車体スペック(フレーズ理解を補強する関連語) ---
    ("curb weight", "車両重量", "名詞", "A lighter curb weight usually improves fuel efficiency.", "自動車工学", "650"),
    ("wheelbase", "ホイールベース", "名詞", "A longer wheelbase generally means more legroom in the back seat.", "自動車工学", "700"),
    ("ground clearance", "最低地上高", "名詞", "The SUV's higher ground clearance makes it better suited for rough roads.", "自動車工学", "650"),
]

PHRASES: list[tuple[str, str]] = [
    ("Can I take this car for a test drive?", "この車を試乗させてもらえますか。"),
    ("What's included in the options package?", "オプションパッケージには何が含まれていますか。"),
    ("Is this a certified pre-owned vehicle?", "これは認定中古車ですか。"),
    ("How much would the monthly payment be?", "月々の支払いはいくらになりますか。"),
    ("Does the price include the extended warranty?", "この価格には延長保証も含まれていますか。"),
    ("The sticker price is a bit higher than I expected.", "表示価格は思ったより高いですね。"),
    ("Can you walk me through the safety rating?", "安全性能評価について説明してもらえますか。"),
    ("What's the fuel efficiency rating on the sedan?", "このセダンの燃費評価はどのくらいですか。"),
    ("I'd like to compare the sedan and the hatchback.", "セダンとハッチバックを比較したいのですが。"),
    ("Do you have any pickup trucks in stock?", "ピックアップトラックの在庫はありますか。"),
    ("Is four-wheel drive available on this trim?", "このグレードには四輪駆動(4WD)は付いていますか。"),
    ("This model comes with a driving assistance system as standard.", "このモデルには運転支援システムが標準装備されています。"),
    ("How fast can this car charge with fast charging?", "この車は急速充電でどのくらい速く充電できますか。"),
    ("Did you bring the charging cable with the car?", "車に充電ケーブルは付属していましたか。"),
    ("I need a mechanic to check the drive belt.", "整備士にドライブベルトを点検してもらう必要があります。"),
    ("The mechanic said the drive shaft needs replacing.", "整備士はドライブシャフトの交換が必要だと言いました。"),
    ("Should I use regular gasoline or premium gasoline?", "レギュラーガソリンとハイオクガソリン、どちらを使うべきですか。"),
    ("This engine only takes unleaded gasoline.", "このエンジンは無鉛ガソリンしか使えません。"),
    ("Can you check the intake valve while it's in the shop?", "入庫している間に吸気バルブを点検してもらえますか。"),
    ("The exhaust valve was making a strange noise.", "排気バルブから変な音がしていました。"),
    ("Would you prefer a stick shift or an automatic?", "マニュアル(スティックシフト)とオートマ、どちらがいいですか。"),
    ("This car has a continuously variable transmission.", "この車は無段変速機(CVT)を搭載しています。"),
    ("Can I get a loaner car while mine is in the shop?", "整備中は代車を借りられますか。"),
    ("I still need to finish the vehicle registration paperwork.", "まだ車両登録の書類を仕上げないといけません。"),
    ("A kei car might be a better fit for city driving.", "街乗りには軽自動車の方が向いているかもしれません。"),
    ("We also carry a few station wagons if you need more cargo space.", "もっと荷室が必要でしたらステーションワゴンも扱っています。"),
    ("Is this coupe available with all-wheel drive?", "このクーペは四輪駆動(AWD)仕様もありますか。"),
]


def main() -> int:
    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing_words:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing_words.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")

    with db() as conn:
        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in existing_phrases:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '自動車産業の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
