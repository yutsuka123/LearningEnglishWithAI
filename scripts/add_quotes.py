# ruff: noqa: E501
"""Famous quotes: scientists / Shakespeare / quotes cited by Sherlock Holmes /
world-famous "despair" lines. Authored by Claude — no app/OpenAI API calls.
Dedupe on english (lowercased). Public-domain or widely-quoted lines only.

Run: python scripts/add_quotes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "名言・名台詞": [
        # 科学者
        ("Now I am become Death, the destroyer of worlds.", "我は死なり、世界の破壊者なり。（オッペンハイマー／『バガヴァッド・ギーター』）"),
        ("God does not play dice with the universe.", "神は宇宙を相手にサイコロ遊びをなさらない。（アインシュタイン）"),
        ("Imagination is more important than knowledge.", "想像力は知識よりも重要である。（アインシュタイン）"),
        ("I have not failed. I've just found ten thousand ways that won't work.", "私は失敗していない。うまくいかない1万通りの方法を見つけただけだ。（エジソン）"),
        ("Eureka! I have found it!", "わかったぞ、見つけた！（アルキメデス）"),
        ("And yet it moves.", "それでも地球は回っている。（ガリレオ）"),
        # シェイクスピア
        ("Now is the winter of our discontent.", "今や我らの不満の冬。（『リチャード三世』）"),
        ("A horse! A horse! My kingdom for a horse!", "馬を、馬を！ 馬の代わりに我が王国をくれてやる！（『リチャード三世』）"),
        ("To be, or not to be, that is the question.", "生きるべきか、死ぬべきか、それが問題だ。（『ハムレット』）"),
        ("Something is rotten in the state of Denmark.", "デンマークに何か腐ったものがある。（『ハムレット』）"),
        ("The lady doth protest too much, methinks.", "あの女、ちと弁解が過ぎるようだな。（『ハムレット』）"),
        ("All the world's a stage, and all the men and women merely players.", "世界はすべて舞台、人はみな役者にすぎない。（『お気に召すまま』）"),
        ("Et tu, Brute?", "ブルータス、お前もか。（『ジュリアス・シーザー』）"),
        ("Cowards die many times before their deaths.", "臆病者は死ぬ前に何度も死ぬ。（『ジュリアス・シーザー』）"),
        ("What's in a name? That which we call a rose by any other name would smell as sweet.", "名前が何だというの。バラはどんな名で呼んでも甘く香る。（『ロミオとジュリエット』）"),
        ("The course of true love never did run smooth.", "まことの恋の道が平坦だったためしはない。（『夏の夜の夢』）"),
        ("Lord, what fools these mortals be!", "やれやれ、人間とはなんと愚かな！（『夏の夜の夢』）"),
        ("We are such stuff as dreams are made on.", "我らは夢と同じ糸で織られている。（『テンペスト』）"),
        ("All that glitters is not gold.", "光るものすべてが金とは限らない。（『ヴェニスの商人』）"),
        # ホームズが引用・名言
        ("When you have eliminated the impossible, whatever remains, however improbable, must be the truth.", "不可能を除外して残ったものは、いかにありえなくとも真実である。（シャーロック・ホームズ）"),
        ("You see, but you do not observe.", "君は見ているが、観察してはいない。（シャーロック・ホームズ）"),
        ("The game is afoot.", "獲物は動き出した（さあ勝負だ）。（ホームズ／原典は『ヘンリー四世』）"),
        ("There is nothing new under the sun.", "日の下に新しいものは何もない。（ホームズが引用／『伝道の書』）"),
        ("Education never ends, Watson. It is a series of lessons, with the greatest for the last.", "教育に終わりはない、ワトソン。最後に最大の教訓が来るのだ。（シャーロック・ホームズ）"),
        ("Mediocrity knows nothing higher than itself, but talent instantly recognizes genius.", "凡人は己以上のものを知らぬが、才人は天才を即座に見抜く。（ホームズ）"),
    ],
    "絶望・名言": [
        ("Abandon all hope, ye who enter here.", "この門をくぐる者は、一切の希望を捨てよ。（ダンテ『神曲』地獄の門）"),
        ("Life's but a walking shadow, full of sound and fury, signifying nothing.", "人生は歩く影にすぎず、響きと怒りに満ちて、何の意味もない。（『マクベス』）"),
        ("Out, out, brief candle!", "消えろ、消えろ、はかない灯火よ！（『マクベス』）"),
        ("The horror! The horror!", "ああ、地獄だ……地獄だ……。（コンラッド『闇の奥』）"),
        ("Vanity of vanities; all is vanity.", "空の空、すべては空。（『伝道の書』）"),
        ("Nothing to be done.", "もう、為すべきことは何もない。（ベケット『ゴドーを待ちながら』）"),
        ("I can't go on. I'll go on.", "もう続けられない。それでも続けよう。（ベケット『名づけえぬもの』）"),
        ("Man is a useless passion.", "人間とは無益な情熱である。（サルトル）"),
        ("Despair is the price one pays for setting oneself an impossible aim.", "絶望とは、不可能な目標を自らに課した者が払う代償だ。（グレアム・グリーン）"),
        ("I have of late lost all my mirth.", "近ごろ私は、すっかり快活さを失ってしまった。（『ハムレット』）"),
        ("The center cannot hold; things fall apart.", "中心は支えきれず、すべては崩れ落ちる。（W.B.イェイツ『再臨』）"),
        ("Do not go gentle into that good night.", "穏やかにあの良き夜に入っていくな。（ディラン・トマス）"),
    ],
}


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        added = skipped = 0
        per_scene: dict[str, int] = {}
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in existing:
                    skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                existing.add(en.lower())
                added += 1
                per_scene[scene] = per_scene.get(scene, 0) + 1
    print(f"phrases: +{added} (skipped {skipped})  {per_scene}")
    with db() as conn:
        print("フレーズ総数:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
