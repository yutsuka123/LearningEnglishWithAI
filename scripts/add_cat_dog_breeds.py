# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Top up the 動物(animal) domain with common cat/dog BREED names, authored
by Claude (2026-08-04・ユーザー要望: 「猫犬は種類も入れましょう」).

既存の動物語彙は cat/dog のような種としての基本語のみで、品種名が一切
なかった。よく知られた犬種・猫種を追加する。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_cat_dog_breeds.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 犬種 ---
    ("Labrador Retriever", "ラブラドール・レトリバー", "名詞", "Labrador Retrievers are known for being friendly and easy to train.", "動物", "500"),
    ("Golden Retriever", "ゴールデン・レトリバー", "名詞", "The Golden Retriever is one of the most popular family dogs.", "動物", "500"),
    ("Poodle", "プードル", "名詞", "Poodles come in toy, miniature, and standard sizes.", "動物", "450"),
    ("Bulldog", "ブルドッグ", "名詞", "The bulldog has a distinctive wrinkled face.", "動物", "450"),
    ("Beagle", "ビーグル", "名詞", "Beagles have an excellent sense of smell.", "動物", "500"),
    ("Chihuahua", "チワワ", "名詞", "The Chihuahua is one of the smallest dog breeds in the world.", "動物", "500"),
    ("Dachshund", "ダックスフンド", "名詞", "The dachshund is known for its long body and short legs.", "動物", "600"),
    ("German Shepherd", "ジャーマン・シェパード", "名詞", "German Shepherds are often trained as police or service dogs.", "動物", "550"),
    ("Siberian Husky", "シベリアン・ハスキー", "名詞", "Siberian Huskies were originally bred to pull sleds.", "動物", "600"),
    ("Corgi", "コーギー", "名詞", "Corgis have short legs but were originally bred to herd cattle.", "動物", "550"),
    ("Shiba Inu", "柴犬", "名詞", "The Shiba Inu is a small breed originally from Japan.", "動物", "500"),
    ("Border Collie", "ボーダー・コリー", "名詞", "Border Collies are considered one of the most intelligent dog breeds.", "動物", "650"),
    ("Pomeranian", "ポメラニアン", "名詞", "Pomeranians are small dogs known for their fluffy coats.", "動物", "600"),
    ("Yorkshire Terrier", "ヨークシャー・テリア", "名詞", "Yorkshire Terriers are a small breed with long, silky fur.", "動物", "700"),
    ("Great Dane", "グレート・デーン", "名詞", "The Great Dane is one of the tallest dog breeds.", "動物", "650"),
    ("Rottweiler", "ロットワイラー", "名詞", "Rottweilers are large, powerful dogs often used for guarding.", "動物", "700"),
    ("Boxer", "ボクサー(犬種)", "名詞", "Boxers are energetic dogs known for their playful nature.", "動物", "650"),
    ("Doberman", "ドーベルマン", "名詞", "Dobermans are known for their loyalty and alertness.", "動物", "700"),
    ("Pug", "パグ", "名詞", "Pugs have a flat face and a curled tail.", "動物", "500"),
    ("Shih Tzu", "シーズー", "名詞", "The Shih Tzu was originally bred as a companion dog in China.", "動物", "700"),
    ("mixed breed", "雑種・ミックス犬", "名詞", "Many rescue dogs are a mixed breed.", "動物", "600"),
    ("purebred", "純血種の", "形容詞", "This dog is a purebred with official papers.", "動物", "700"),
    # --- 猫種 ---
    ("Siamese cat", "シャム猫", "名詞", "Siamese cats are known for their blue eyes and vocal personality.", "動物", "600"),
    ("Persian cat", "ペルシャ猫", "名詞", "Persian cats have long, thick fur that needs regular grooming.", "動物", "600"),
    ("Maine Coon", "メインクーン", "名詞", "The Maine Coon is one of the largest domestic cat breeds.", "動物", "700"),
    ("Ragdoll", "ラグドール", "名詞", "Ragdolls tend to go limp when you pick them up, hence the name.", "動物", "750"),
    ("Scottish Fold", "スコティッシュフォールド", "名詞", "The Scottish Fold is known for its folded ears.", "動物", "750"),
    ("Sphynx cat", "スフィンクス(猫)", "名詞", "The Sphynx cat is famous for having almost no fur.", "動物", "750"),
    ("Bengal cat", "ベンガル猫", "名詞", "The Bengal cat has a spotted coat that resembles a wild leopard.", "動物", "750"),
    ("British Shorthair", "ブリティッシュショートヘア", "名詞", "The British Shorthair has a round face and a dense coat.", "動物", "800"),
    ("tabby", "トラ猫・キジトラ", "名詞", "My cat is a tabby with orange and white stripes.", "動物", "600"),
    ("calico", "三毛猫", "名詞", "Calico cats almost always turn out to be female.", "動物", "650"),
    ("tortoiseshell", "べっ甲柄(猫)", "名詞", "Her cat has a beautiful tortoiseshell coat.", "動物", "750"),
    ("stray cat", "野良猫", "名詞", "We started feeding a stray cat that showed up in our yard.", "動物", "500"),
    ("feral cat", "野生化した猫", "名詞", "Feral cats are much harder to tame than strays.", "動物", "700"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
