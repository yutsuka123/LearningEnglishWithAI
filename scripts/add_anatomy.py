# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "解剖学" domain/scene: vocabulary and phrases for anatomy
terminology, authored by Claude (2026-08-10・ユーザー要望).

対象語彙: 骨格系(体軸骨格/体肢骨格、大腿骨・上腕骨・鎖骨等の個別の骨)、関節
の分類(球関節、蝶番関節、車軸関節、鞍関節)、結合組織(靭帯、腱、軟骨、筋膜、
結合組織一般)、体腔(胸腔、腹腔、骨盤腔)、解剖学的方向用語(前部/後部/内側/
外側/上方/下方/近位/遠位、解剖学的正位)、解剖学的平面(矢状面、前額面、水平
面)、その他(器官系、脳神経)。既存`医療`ドメインの基礎的な体の部位語彙
(abdomen/ankle/artery/bladder/chest/joint/muscle/nerve/spine/skull等)とは
重複しない、より学術的な解剖学用語のみを扱う。

フレーズは解剖学を学ぶ医学生・トレーナーが使うような説明的な文を中心に
構成する("The femur is the longest bone in the human body." など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_anatomy.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 骨格系(全体) ---
    ("skeletal system", "骨格系", "名詞", "The skeletal system supports the body and protects internal organs.", "解剖学", "700"),
    ("musculoskeletal system", "筋骨格系", "名詞", "The musculoskeletal system allows the body to move and maintain posture.", "解剖学", "800"),
    ("axial skeleton", "体軸骨格", "名詞", "The axial skeleton includes the skull, spine, and rib cage.", "解剖学", "850"),
    ("appendicular skeleton", "体肢骨格", "名詞", "The appendicular skeleton consists of the limbs and their girdles.", "解剖学", "850"),
    # --- 個別の骨 ---
    ("femur", "大腿骨", "名詞", "The femur is the longest and strongest bone in the human body.", "解剖学", "650"),
    ("humerus", "上腕骨", "名詞", "The humerus connects the shoulder to the elbow.", "解剖学", "700"),
    ("clavicle", "鎖骨", "名詞", "The clavicle is one of the most commonly fractured bones.", "解剖学", "700"),
    ("scapula", "肩甲骨", "名詞", "The scapula anchors many of the muscles that move the arm.", "解剖学", "750"),
    ("sternum", "胸骨", "名詞", "The sternum sits at the center of the chest and protects the heart.", "解剖学", "700"),
    ("patella", "膝蓋骨", "名詞", "The patella, or kneecap, protects the front of the knee joint.", "解剖学", "700"),
    ("mandible", "下顎骨", "名詞", "The mandible is the only movable bone in the skull.", "解剖学", "700"),
    ("cranium", "頭蓋骨(脳を包む部分)", "名詞", "The cranium encloses and protects the brain.", "解剖学", "700"),
    # --- 関節の分類 ---
    ("ball-and-socket joint", "球関節", "名詞", "The shoulder is a ball-and-socket joint, allowing a wide range of motion.", "解剖学", "800"),
    ("hinge joint", "蝶番関節", "名詞", "The elbow is a hinge joint that mainly bends and straightens.", "解剖学", "800"),
    ("pivot joint", "車軸関節", "名詞", "A pivot joint in the neck lets you rotate your head from side to side.", "解剖学", "850"),
    ("saddle joint", "鞍関節", "名詞", "The saddle joint at the base of the thumb allows for a wide range of movement.", "解剖学", "850"),
    # --- 結合組織 ---
    ("ligament", "靭帯", "名詞", "Ligaments connect bone to bone and stabilize the joints.", "解剖学", "700"),
    ("tendon", "腱", "名詞", "Tendons connect muscle to bone, transmitting the force of contraction.", "解剖学", "700"),
    ("cartilage", "軟骨", "名詞", "Cartilage cushions the joints and reduces friction between bones.", "解剖学", "700"),
    ("fascia", "筋膜", "名詞", "Fascia is a thin layer of connective tissue that wraps around muscles and organs.", "解剖学", "800"),
    ("connective tissue", "結合組織", "名詞", "Ligaments, tendons, and cartilage are all types of connective tissue.", "解剖学", "800"),
    # --- 体腔 ---
    ("thoracic cavity", "胸腔", "名詞", "The heart and lungs are located in the thoracic cavity.", "解剖学", "800"),
    ("abdominal cavity", "腹腔", "名詞", "The stomach, liver, and intestines lie within the abdominal cavity.", "解剖学", "800"),
    ("pelvic cavity", "骨盤腔", "名詞", "The bladder and reproductive organs are found in the pelvic cavity.", "解剖学", "850"),
    # --- 解剖学的方向用語 ---
    ("anatomical position", "解剖学的正位", "名詞", "Please stand in anatomical position for the physical examination.", "解剖学", "800"),
    ("anterior", "前部の・前方の", "形容詞", "Anterior means toward the front of the body.", "解剖学", "750"),
    ("posterior", "後部の・後方の", "形容詞", "The spine runs along the posterior side of the trunk.", "解剖学", "750"),
    ("medial", "内側の", "形容詞", "Medial means closer to the midline of the body.", "解剖学", "800"),
    ("lateral", "外側の", "形容詞", "Lateral structures are farther from the body's midline.", "解剖学", "800"),
    ("superior", "上方の", "形容詞", "In anatomy, superior means located above another structure.", "解剖学", "800"),
    ("inferior", "下方の", "形容詞", "The feet are inferior to the knees.", "解剖学", "800"),
    ("proximal", "近位の(体幹に近い側)", "形容詞", "The elbow is proximal to the wrist.", "解剖学", "850"),
    ("distal", "遠位の(体幹から遠い側)", "形容詞", "The fingers are distal to the elbow.", "解剖学", "850"),
    # --- 解剖学的平面 ---
    ("sagittal plane", "矢状面", "名詞", "The sagittal plane divides the body into left and right halves.", "解剖学", "900"),
    ("coronal plane", "前額面(冠状面)", "名詞", "The coronal plane divides the body into front and back sections.", "解剖学", "900"),
    ("transverse plane", "水平面", "名詞", "The transverse plane separates the upper and lower body.", "解剖学", "900"),
    # --- その他 ---
    ("organ system", "器官系", "名詞", "The circulatory system is one of the body's major organ systems.", "解剖学", "700"),
    ("cranial nerve", "脳神経", "名詞", "Twelve pairs of cranial nerves emerge directly from the brain.", "解剖学", "850"),
]

PHRASES: list[tuple[str, str]] = [
    ("The femur is the longest bone in the human body.", "大腿骨は人体で最も長い骨です。"),
    ("The heart is located in the thoracic cavity.", "心臓は胸腔内に位置しています。"),
    ("Anterior means toward the front of the body.", "前部(anterior)とは体の前方を指します。"),
    ("The elbow is a hinge joint.", "肘は蝶番関節です。"),
    ("The shoulder is a ball-and-socket joint, which allows a wide range of motion.", "肩は球関節で、広い可動域を持ちます。"),
    ("Tendons connect muscle to bone, while ligaments connect bone to bone.", "腱は筋肉を骨に結びつけ、靭帯は骨と骨を結びつけます。"),
    ("The skull protects the brain within the cranial cavity.", "頭蓋骨は頭蓋腔内で脳を保護します。"),
    ("Cartilage cushions the joints and reduces friction.", "軟骨は関節を保護し、摩擦を減らします。"),
    ("The spine is also called the vertebral column.", "脊椎は脊柱とも呼ばれます。"),
    ("The stomach lies within the abdominal cavity.", "胃は腹腔内にあります。"),
    ("Medial means closer to the midline of the body.", "内側(medial)とは体の正中線に近い方を指します。"),
    ("Lateral structures are farther from the midline.", "外側(lateral)の構造は正中線から遠い位置にあります。"),
    ("Please stand in anatomical position for the examination.", "診察のために解剖学的正位で立ってください。"),
    ("The sagittal plane divides the body into left and right halves.", "矢状面は体を左右に分けます。"),
    ("The coronal plane divides the body into front and back sections.", "前額面は体を前後に分けます。"),
    ("The transverse plane separates the upper and lower body.", "水平面は体を上下に分けます。"),
    ("Fascia is a thin layer of connective tissue that wraps around the muscles.", "筋膜は筋肉を包む薄い結合組織の層です。"),
    ("The axial skeleton includes the skull, spine, and rib cage.", "体軸骨格には頭蓋骨・脊椎・肋骨が含まれます。"),
    ("The appendicular skeleton consists of the limbs and their girdles.", "体肢骨格は四肢とその帯からなります。"),
    ("Twelve pairs of cranial nerves emerge directly from the brain.", "12対の脳神経は脳から直接出ています。"),
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
                "VALUES (?, ?, '解剖学の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
