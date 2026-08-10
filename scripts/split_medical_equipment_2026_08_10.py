# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Carve a new "医療(機器・器具)" domain out of `医療(治療)`, and add newly
requested medical-equipment vocabulary, authored by Claude (2026-08-10・
ユーザー要望: メス/心電図/血圧計/MRI/CT/マンモグラフィー/診察台 他)。

背景: 2026-08-10のsplit_medical_2026_08_10.pyで`医療`を症状/治療/専門・
学問/その他の4分類に再編した際、`crutches`/`defibrillator`/`forceps`/
`gurney`/`scalpel`/`stethoscope`/`ventilator`/`wheelchair`の8語(いずれも
「治療行為」ではなく「医療機器・器具」)が便宜上`医療(治療)`に入っていた。
ユーザーが機器・器具を独立分類にしたいと提起したため、この8語を新設の
`医療(機器・器具)`へ移し、新規語(心電図/血圧計/MRI/CT/マンモグラフィー/
診察台等)もあわせて追加する。

事前にDB全体を確認し、`IV drip`/`pulse oximeter`は既存`看護学`ドメインに
既にあるため対象外(そのまま)。`thermometer`は`化学`ドメイン(実験用)、
`x-ray`は`物理`ドメイン(X線という物理現象)で別語義のためそのままでは
衝突する。`thermometer`は今回見送り、`x-ray`は`X-ray machine`という
複合見出しで医療機器としての意味に絞って追加した。

新規追加語: electrocardiogram(心電図)、blood pressure monitor(血圧計)、
MRI machine、CT scanner、mammography(マンモグラフィー)、examination
table(診察台)、ultrasound machine(超音波診断装置)、X-ray machine、
syringe(注射器)、endoscope(内視鏡)、dialysis machine(人工透析装置)、
operating table(手術台)、hospital bed(病院のベッド)。

No app / OpenAI API calls — everything is hand-written and inserted/updated
directly in the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/split_medical_equipment_2026_08_10.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

OLD_DOMAIN = "医療(治療)"
NEW_DOMAIN = "医療(機器・器具)"

# 既存 医療(治療) から機器・器具として移す語(英語見出しで一致判定)。
EQUIPMENT_WORDS_TO_MOVE = {
    "crutches", "defibrillator", "forceps", "gurney", "scalpel",
    "stethoscope", "ventilator", "wheelchair",
}

NEW_WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("electrocardiogram", "心電図(ECG)", "名詞", "The nurse attached electrodes to take an electrocardiogram.", NEW_DOMAIN, "700"),
    ("blood pressure monitor", "血圧計", "名詞", "The blood pressure monitor showed a reading of 120 over 80.", NEW_DOMAIN, "550"),
    ("MRI machine", "MRI装置", "名詞", "The MRI machine takes detailed images of soft tissue.", NEW_DOMAIN, "650"),
    ("CT scanner", "CTスキャナー", "名詞", "The CT scanner produces cross-sectional images of the body.", NEW_DOMAIN, "650"),
    ("mammography", "マンモグラフィー(乳房X線検査)", "名詞", "She goes in for a mammography screening every year.", NEW_DOMAIN, "750"),
    ("examination table", "診察台", "名詞", "Please lie down on the examination table.", NEW_DOMAIN, "450"),
    ("ultrasound machine", "超音波診断装置(エコー)", "名詞", "The doctor used an ultrasound machine to check the baby's heartbeat.", NEW_DOMAIN, "600"),
    ("X-ray machine", "レントゲン(X線)撮影装置", "名詞", "Stand still while the X-ray machine takes the picture.", NEW_DOMAIN, "500"),
    ("syringe", "注射器", "名詞", "The nurse filled the syringe with the vaccine.", NEW_DOMAIN, "500"),
    ("endoscope", "内視鏡", "名詞", "The doctor used an endoscope to examine the patient's stomach.", NEW_DOMAIN, "700"),
    ("dialysis machine", "人工透析装置", "名詞", "He spends four hours on the dialysis machine three times a week.", NEW_DOMAIN, "750"),
    ("operating table", "手術台", "名詞", "The patient was moved onto the operating table.", NEW_DOMAIN, "550"),
    ("hospital bed", "病院用ベッド", "名詞", "The hospital bed can be raised and lowered electronically.", NEW_DOMAIN, "400"),
]

PHRASES: list[tuple[str, str]] = [
    ("Please lie down on the examination table.", "診察台に横になってください。"),
    ("We need to run an MRI to see what's going on.", "何が起きているか確認するためMRIを撮る必要があります。"),
    ("The doctor ordered a CT scan just to be safe.", "念のため医師がCTスキャンを指示しました。"),
    ("Roll up your sleeve so I can check your blood pressure.", "血圧を測るので袖をまくってください。"),
    ("Try to hold still for the X-ray.", "レントゲンの間はじっとしていてください。"),
    ("The nurse is going to draw some blood with a syringe.", "看護師が注射器で採血します。"),
    ("We'll do an ultrasound to get a better look.", "もっとよく見るために超音波検査をします。"),
    ("The surgeon asked for the scalpel.", "外科医がメスを求めました。"),
    ("Can you pass me the forceps?", "鉗子を取ってもらえますか？"),
    ("He's still hooked up to the ventilator.", "彼はまだ人工呼吸器につながれています。"),
    ("She needs crutches for the next few weeks.", "彼女はこれから数週間、松葉杖が必要です。"),
    ("The paramedics brought the patient in on a gurney.", "救急隊員が患者をストレッチャーで運び込みました。"),
    ("Please schedule your mammography for next month.", "来月にマンモグラフィーの予約を入れてください。"),
    ("The endoscope lets the doctor see inside without surgery.", "内視鏡を使えば手術せずに内部を見ることができます。"),
    ("He goes to the clinic for dialysis three times a week.", "彼は週3回、透析のためにクリニックに通っています。"),
]


def main() -> int:
    with db() as conn:
        rows = conn.execute(
            "SELECT id, english FROM words WHERE domain=?", (OLD_DOMAIN,)
        ).fetchall()
        moved = 0
        for r in rows:
            if r["english"].lower() in {
                w.lower() for w in EQUIPMENT_WORDS_TO_MOVE
            }:
                conn.execute(
                    "UPDATE words SET domain=? WHERE id=?",
                    (NEW_DOMAIN, r["id"]),
                )
                moved += 1
    print(f"moved from {OLD_DOMAIN} -> {NEW_DOMAIN}: {moved}")

    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in NEW_WORDS:
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
    print(f"words added: +{added} (skipped {skipped})")

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
                "VALUES (?, ?, '医療機器の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
