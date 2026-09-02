# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""フィジカルAI分野の語彙拡充、authored by Claude(2026-09-02・ユーザー要望
「全分野の語彙拡充、特にフィジカルAI関連の語彙拡充を先に行うこと」に対応。
犬猫/スポーツ等の宣伝アプローチ検討の前提条件として、本番DB調査で
フィジカルAI分野がわずか15語(全13,432語中)と手薄だったことが判明した
ため着手)。

投入前に本番の既存15語を確認した上で、機械工学(actuator/sensor/servo/
encoder/gyroscope/lidar/gripper/end effector/PID control等)・AI
(reinforcement learning等)・SF(robot/exoskeleton)・製造(industrial
robot)・スポーツ科学(proprioception)に既に収録済みの基礎的な部品名/
制御理論用語とは重複しないよう、より高度な「身体性AI・ロボット学習」
寄りの39語を選定した(学習パラダイム/モデル・アーキテクチャ/知覚/
操作/移動/システム基盤の6グループ)。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table.

Run:  python scripts/add_physical_ai_2026_09_02.py
仕上げ: 投入後に通常のセッション内カデンスで`scripts/build_details.py`/
        `scripts/build_audio.py`を回してdetail/音声を埋める。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "フィジカルAI"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # === 学習パラダイム ===
    ("imitation learning", "模倣学習(人間や熟練者の実演からロボットが行動を学ぶ手法)", "名詞", "Imitation learning lets the robot learn a task by watching a human demonstrate it.", DOMAIN, "850"),
    ("behavior cloning", "行動クローニング(実演データをそのまま模倣して方策を学習する手法)", "名詞", "Behavior cloning trains the robot to copy the exact actions recorded during teleoperation.", DOMAIN, "900"),
    ("domain randomization", "ドメインランダム化(シミュレーションの見た目や物理条件をランダムに変えて実機への転移を高める手法)", "名詞", "Domain randomization varies the simulated lighting and textures so the policy generalizes to the real world.", DOMAIN, "900"),
    ("reality gap", "リアリティギャップ(シミュレーションと実世界の性能差)", "名詞", "Domain randomization is one way to narrow the reality gap between simulation and the real robot.", DOMAIN, "900"),
    ("cross-embodiment learning", "クロスエンボディメント学習(異なる形状・構造のロボット間で学習を転用すること)", "名詞", "Cross-embodiment learning lets a policy trained on one robot arm transfer to a different robot design.", DOMAIN, "950"),
    ("sample efficiency", "サンプル効率(少ないデータ・試行回数で学習できる度合い)", "名詞", "Improving sample efficiency means the robot needs fewer trials to learn a new skill.", DOMAIN, "900"),
    ("offline reinforcement learning", "オフライン強化学習(収集済みデータのみを使い追加の試行なしで方策を学習する強化学習)", "名詞", "Offline reinforcement learning trains the policy purely from a fixed dataset of past interactions.", DOMAIN, "950"),
    ("online reinforcement learning", "オンライン強化学習(エージェントが環境と実際に相互作用しながら方策を学習する強化学習)", "名詞", "Online reinforcement learning lets the robot keep improving its policy through continued trial and error.", DOMAIN, "900"),
    ("kinesthetic teaching", "運動感覚教示(人がロボットの腕を直接動かして動作を教える教示法)", "名詞", "In kinesthetic teaching, the trainer physically guides the robot arm through the motion.", DOMAIN, "950"),
    ("demonstration data", "デモンストレーションデータ(模倣学習に使う、人間の実演を記録したデータ)", "名詞", "The team collected demonstration data by teleoperating the robot through the folding task.", DOMAIN, "850"),

    # === モデル・アーキテクチャ ===
    ("vision-language-action model", "Vision-Language-Actionモデル(視覚・言語・行動を統合したロボット向け基盤モデル、VLA)", "名詞", "A vision-language-action model can follow a spoken instruction and directly output robot actions.", DOMAIN, "950"),
    ("robot foundation model", "ロボット基盤モデル(多様なタスク・環境に汎用的に対応できるよう大量データで事前学習したモデル)", "名詞", "A robot foundation model can be fine-tuned for many different manipulation tasks.", DOMAIN, "950"),
    ("diffusion policy", "拡散モデル方策(拡散モデルを用いてロボットの行動を生成する手法)", "名詞", "A diffusion policy can generate smooth, multimodal robot actions from demonstrations.", DOMAIN, "950"),
    ("policy network", "方策ネットワーク(エージェントの行動を出力するニューラルネットワーク)", "名詞", "The policy network takes the camera image and outputs the next joint angles.", DOMAIN, "900"),
    ("reward model", "報酬モデル(強化学習でエージェントの行動の良さを評価するモデル)", "名詞", "The reward model scores each action based on how close the robot gets to the goal.", DOMAIN, "900"),
    ("large-scale robot dataset", "大規模ロボットデータセット", "名詞", "Researchers trained the policy on a large-scale robot dataset collected from many different tasks.", DOMAIN, "900"),

    # === 知覚 ===
    ("point cloud", "点群(3次元空間内の点の集合として物体や環境の形状を表すデータ)", "名詞", "The robot builds a 3D map from a point cloud captured by its sensors.", DOMAIN, "850"),
    ("depth camera", "デプスカメラ(奥行き情報を取得できるカメラ)", "名詞", "The depth camera measures how far each object is from the robot.", DOMAIN, "750"),
    ("occupancy grid map", "占有格子地図(空間を格子状に区切り各セルの占有状態を表す地図表現)", "名詞", "The robot updates its occupancy grid map as it explores the room.", DOMAIN, "900"),
    ("object pose estimation", "物体姿勢推定(物体の位置と向きを推定すること)", "名詞", "Object pose estimation tells the robot the exact position and orientation of the cup before grasping it.", DOMAIN, "900"),
    ("scene understanding", "シーン理解(周囲の状況を認識・解釈すること)", "名詞", "Scene understanding helps the robot tell the difference between a chair and an obstacle.", DOMAIN, "850"),
    ("multimodal perception", "マルチモーダル知覚(視覚・触覚・音声など複数の感覚情報を統合する知覚)", "名詞", "Multimodal perception combines camera and touch sensor data to recognize the object more reliably.", DOMAIN, "900"),
    ("tactile sensing", "触覚センシング(触覚情報を検知する技術)", "名詞", "Tactile sensing in the fingertips helps the robot adjust its grip without dropping the egg.", DOMAIN, "850"),
    ("proprioceptive sensing", "固有受容感覚センシング(関節角度や力など、ロボット自身の内部状態を検知するセンシング)", "名詞", "Proprioceptive sensing tells the robot the current angle of each joint even without looking at it.", DOMAIN, "900"),
    ("affordance", "アフォーダンス(物体や環境が持つ、行動を誘発する特徴)", "名詞", "The handle's shape gives a strong affordance for grasping.", DOMAIN, "900"),

    # === 操作・移動 ===
    ("grasp planning", "把持計画(ロボットが物体をどのように掴むかを計画すること)", "名詞", "Grasp planning helps the robotic arm pick up objects of different shapes.", DOMAIN, "900"),
    ("compliant control", "コンプライアント制御(力加減を柔軟に調整する制御方式)", "名詞", "Compliant control lets the robot arm yield slightly when it bumps into something instead of pushing hard.", DOMAIN, "900"),
    ("whole-body control", "全身協調制御(ロボットの全身の関節を協調させて制御すること)", "名詞", "Whole-body control coordinates the robot's arms, legs, and torso to keep it balanced while reaching.", DOMAIN, "950"),
    ("underactuated system", "劣駆動系(関節数よりアクチュエータの数が少ないシステム)", "名詞", "A walking robot is often modeled as an underactuated system because it has fewer actuators than degrees of freedom.", DOMAIN, "950"),
    ("quadruped robot", "四足歩行ロボット", "名詞", "The quadruped robot climbed the stairs without losing its balance.", DOMAIN, "800"),
    ("legged locomotion", "脚式移動(脚を使った移動方式)", "名詞", "Legged locomotion allows the robot to cross rough terrain that wheels cannot handle.", DOMAIN, "850"),
    ("gait generation", "歩容生成(歩き方のパターンを生成すること)", "名詞", "Gait generation adjusts the robot's stride length depending on the terrain.", DOMAIN, "900"),
    ("central pattern generator", "中枢パターン生成器(周期的な運動パターンを生み出す神経回路モデル、CPG)", "名詞", "A central pattern generator produces the rhythmic signals that drive the robot's walking gait.", DOMAIN, "950"),
    ("zero moment point", "ゼロモーメント点(二足歩行ロボットの安定性を判定する指標、ZMP)", "名詞", "The humanoid robot keeps the zero moment point inside its foot to avoid falling over.", DOMAIN, "950"),
    ("collision avoidance", "衝突回避", "名詞", "The mobile robot's collision avoidance system stopped it before it hit the wall.", DOMAIN, "750"),

    # === システム・基盤 ===
    ("physics simulator", "物理シミュレータ", "名詞", "The team trains the policy in a physics simulator before testing it on the real robot.", DOMAIN, "800"),
    ("shared autonomy", "共有自律(人とロボットが操作を分担する仕組み)", "名詞", "Shared autonomy lets the operator guide the robot arm while the system handles fine adjustments.", DOMAIN, "900"),
    ("human-robot interaction", "ヒューマンロボットインタラクション(人とロボットの相互作用に関する研究分野)", "名詞", "Human-robot interaction research studies how people communicate naturally with robots.", DOMAIN, "850"),
    ("physical AI", "フィジカルAI(現実世界で身体を通じて知覚・行動するAIの総称)", "名詞", "Physical AI combines perception, reasoning, and control so a robot can act safely in the real world.", DOMAIN, "750"),
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
                print(f"  [skip: 既存] {en}")
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing.add(en.lower())
            added += 1

    print(f"\nwords: +{added} (skipped {skipped}) in domain={DOMAIN}")
    with db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM words WHERE domain = ?", (DOMAIN,)
        ).fetchone()[0]
        print(f"{DOMAIN} total now: {total}")
        grand_total = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        print("total words:", grand_total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
