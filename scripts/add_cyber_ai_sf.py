# ruff: noqa: E501
"""サイバー/セキュリティ/IT/AI/SF 系の語彙を追加する。

セキュリティ用語(malware/ransomware/phishing/firewall/vulnerability ...)、
サイバー・電脳系(cyberspace/cyberattack/blockchain ...)、AI 系
(neural/inference/hallucinate ...)、SF 系(metaverse/hologram/cyborg ...)を
学習用に登録する。domain は既存の IT / AI / SF を使う。english で重複判定し、
既存語は例文だけ補充する。著者は Claude(app/OpenAI API は呼ばない)。

Run: python scripts/add_cyber_ai_sf.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, japanese, part_of_speech, example, domain, level)
ITEMS: list[tuple[str, str, str, str, str, str]] = [
    # ===== セキュリティ (domain=IT) =====
    ("malware", "マルウェア・悪意あるソフト", "名詞", "The malware spread across the network.", "IT", "700"),
    ("ransomware", "ランサムウェア(身代金要求型ウイルス)", "名詞", "Ransomware locked all the company files.", "IT", "800"),
    ("phishing", "フィッシング詐欺", "名詞", "He fell for a phishing email.", "IT", "700"),
    ("firewall", "ファイアウォール", "名詞", "The firewall blocked the attack.", "IT", "600"),
    ("vulnerability", "脆弱性・弱点", "名詞", "They found a vulnerability in the software.", "IT", "700"),
    ("exploit", "(脆弱性を突く)攻撃コード・悪用する", "名詞", "Hackers exploited the security flaw.", "IT", "800"),
    ("patch", "修正プログラム・修正する", "名詞", "Install the latest security patch.", "IT", "600"),
    ("backdoor", "バックドア(不正な裏口)", "名詞", "The virus opened a backdoor on the PC.", "IT", "800"),
    ("spyware", "スパイウェア", "名詞", "Spyware tracked his every keystroke.", "IT", "700"),
    ("trojan", "トロイの木馬(偽装型ウイルス)", "名詞", "The trojan disguised itself as a game.", "IT", "800"),
    ("botnet", "ボットネット(乗っ取り端末の群れ)", "名詞", "The botnet sent millions of spam emails.", "IT", "900"),
    ("malicious", "悪意のある", "形容詞", "He clicked a malicious link.", "IT", "700"),
    ("hacker", "ハッカー", "名詞", "A hacker broke into the database.", "IT", "600"),
    ("intrusion", "侵入・不正アクセス", "名詞", "The system detected an intrusion.", "IT", "800"),
    ("antivirus", "ウイルス対策ソフト", "名詞", "Keep your antivirus up to date.", "IT", "600"),
    ("biometric", "生体認証の", "形容詞", "The phone uses biometric authentication.", "IT", "800"),
    ("authorization", "認可・権限付与", "名詞", "You need authorization to access this.", "IT", "700"),
    ("credential", "認証情報・資格情報", "名詞", "Never share your login credentials.", "IT", "700"),
    ("decryption", "復号", "名詞", "Decryption requires the secret key.", "IT", "800"),
    ("cipher", "暗号・暗号方式", "名詞", "The message was written in a cipher.", "IT", "800"),
    ("spoofing", "なりすまし・偽装", "名詞", "Email spoofing fakes the sender address.", "IT", "900"),
    ("keylogger", "キーロガー(入力盗聴ソフト)", "名詞", "A keylogger captured his password.", "IT", "900"),
    ("payload", "ペイロード(攻撃の中身)", "名詞", "The virus delivered its payload at midnight.", "IT", "900"),
    ("sandbox", "サンドボックス(隔離実行環境)", "名詞", "Run the file in a sandbox first.", "IT", "800"),
    ("quarantine", "隔離する・検疫", "動詞", "The antivirus quarantined the infected file.", "IT", "700"),
    ("penetration", "侵入・(侵入)テスト", "名詞", "They ran a penetration test on the server.", "IT", "800"),
    ("cybersecurity", "サイバーセキュリティ", "名詞", "Cybersecurity is a top priority for banks.", "IT", "700"),

    # ===== サイバー・電脳/IT (domain=IT) =====
    ("cyber", "サイバーの・電脳の", "形容詞", "Cyber threats are growing every year.", "IT", "600"),
    ("cyberspace", "サイバー空間", "名詞", "They met in cyberspace before meeting in person.", "IT", "700"),
    ("cyberattack", "サイバー攻撃", "名詞", "The power grid suffered a cyberattack.", "IT", "700"),
    ("cybercrime", "サイバー犯罪", "名詞", "Cybercrime costs billions every year.", "IT", "700"),
    ("blockchain", "ブロックチェーン", "名詞", "Bitcoin runs on a blockchain.", "IT", "800"),
    ("cryptocurrency", "暗号資産・仮想通貨", "名詞", "He invested in cryptocurrency.", "IT", "800"),
    ("bandwidth", "帯域幅・通信容量", "名詞", "Video streaming uses a lot of bandwidth.", "IT", "700"),
    ("latency", "遅延・応答の遅れ", "名詞", "Online games need low latency.", "IT", "800"),
    ("protocol", "プロトコル・通信規約", "名詞", "HTTPS is a secure protocol.", "IT", "700"),
    ("packet", "パケット(分割データ)", "名詞", "Data travels across the net in packets.", "IT", "700"),
    ("router", "ルーター", "名詞", "Restart the router to fix the connection.", "IT", "600"),
    ("server", "サーバー", "名詞", "The website runs on a cloud server.", "IT", "600"),
    ("database", "データベース", "名詞", "The customer data is stored in a database.", "IT", "600"),
    ("cache", "キャッシュ・一時保存する", "名詞", "Clear the browser cache to fix the error.", "IT", "700"),
    ("debug", "デバッグする・不具合を直す", "動詞", "She spent hours debugging the code.", "IT", "700"),
    ("compile", "コンパイルする", "動詞", "The compiler compiles the source code.", "IT", "700"),
    ("interface", "インターフェース・接点", "名詞", "The app has a simple user interface.", "IT", "600"),
    ("middleware", "ミドルウェア", "名詞", "Middleware connects the app and the database.", "IT", "900"),

    # ===== AI (domain=AI) =====
    ("neural", "ニューラルの・神経の", "形容詞", "A neural network powers the model.", "AI", "800"),
    ("inference", "推論", "名詞", "The model makes an inference from the data.", "AI", "800"),
    ("dataset", "データセット", "名詞", "The model was trained on a huge dataset.", "AI", "700"),
    ("hallucinate", "(AIが)もっともらしい誤りを生成する", "動詞", "Language models sometimes hallucinate facts.", "AI", "900"),
    ("overfitting", "過学習・過剰適合", "名詞", "Overfitting makes the model fail on new data.", "AI", "900"),
    ("embedding", "埋め込み(ベクトル表現)", "名詞", "Words are turned into embeddings.", "AI", "900"),
    ("transformer", "トランスフォーマー(AIモデル構造)", "名詞", "The transformer architecture changed AI.", "AI", "900"),
    ("generative", "生成的な・生成AIの", "形容詞", "Generative AI can write text and images.", "AI", "800"),
    ("autonomous", "自律的な・自動運転の", "形容詞", "Autonomous cars drive without a human.", "AI", "800"),
    ("chatbot", "チャットボット", "名詞", "A chatbot answers customer questions.", "AI", "700"),
    ("reinforcement", "強化・強化学習の強化", "名詞", "The robot learns by reinforcement learning.", "AI", "800"),
    ("classifier", "分類器", "名詞", "The classifier sorts emails as spam or not.", "AI", "900"),
    ("annotation", "アノテーション・注釈付け", "名詞", "Data annotation is slow but important.", "AI", "800"),
    ("token", "トークン(処理の最小単位)・しるし", "名詞", "The model is billed per token.", "AI", "800"),
    ("prompt", "プロンプト・(行動を)促す", "名詞", "A good prompt gives a better answer.", "AI", "700"),
    ("fine-tune", "微調整する・ファインチューニングする", "動詞", "We fine-tuned the model on legal texts.", "AI", "900"),

    # ===== SF (domain=SF) =====
    ("humanoid", "ヒューマノイド・人型の", "名詞", "The lab built a humanoid robot.", "SF", "800"),
    ("virtual", "仮想の・バーチャルの", "形容詞", "She explored a virtual world with a headset.", "SF", "600"),
    ("augmented", "拡張された(拡張現実の)", "形容詞", "Augmented reality overlays data on the world.", "SF", "800"),
    ("hologram", "ホログラム・立体映像", "名詞", "A hologram of the captain appeared.", "SF", "800"),
    ("holographic", "ホログラフィの・立体映像の", "形容詞", "The room had a holographic display.", "SF", "900"),
    ("avatar", "アバター(分身キャラ)", "名詞", "He designed a custom avatar for the game.", "SF", "700"),
    ("metaverse", "メタバース", "名詞", "They held a concert in the metaverse.", "SF", "800"),
    ("simulation", "シミュレーション・模擬", "名詞", "Maybe we live inside a simulation.", "SF", "700"),
    ("simulate", "シミュレートする・模擬する", "動詞", "The program simulates a black hole.", "SF", "700"),
    ("teleportation", "テレポーテーション・瞬間移動", "名詞", "Teleportation is still science fiction.", "SF", "900"),
    ("cyberpunk", "サイバーパンク", "名詞", "The movie has a dark cyberpunk setting.", "SF", "900"),
    ("utopia", "ユートピア・理想郷", "名詞", "The story imagines a perfect utopia.", "SF", "800"),
    ("nanotechnology", "ナノテクノロジー", "名詞", "Nanotechnology builds machines atom by atom.", "SF", "900"),
    ("nanobot", "ナノボット(極小ロボット)", "名詞", "Nanobots repaired the damaged cells.", "SF", "990"),
    ("warp", "ワープする・歪める", "動詞", "The ship warped across the galaxy.", "SF", "800"),
    ("drone", "ドローン・無人機", "名詞", "A drone delivered the package.", "SF", "600"),
    ("exoskeleton", "外骨格・パワードスーツ", "名詞", "The soldier wore a powered exoskeleton.", "SF", "900"),
    ("terraform", "テラフォーミングする・惑星改造する", "動詞", "They plan to terraform Mars.", "SF", "990"),
    ("starship", "宇宙船", "名詞", "The starship left for a distant star.", "SF", "700"),
    ("wormhole", "ワームホール(時空のトンネル)", "名詞", "They traveled through a wormhole.", "SF", "900"),
    ("antimatter", "反物質", "名詞", "The engine is powered by antimatter.", "SF", "900"),
    ("replicant", "レプリカント(人造人間)", "名詞", "A replicant looks exactly like a human.", "SF", "990"),
    ("sentient", "知覚力のある・意識を持つ", "形容詞", "The AI became sentient overnight.", "SF", "900"),
    ("mutant", "突然変異体・ミュータント", "名詞", "The hero is a mutant with strange powers.", "SF", "800"),
    ("genome", "ゲノム・全遺伝情報", "名詞", "Scientists mapped the human genome.", "SF", "800"),
    ("biohacking", "バイオハッキング・身体の自己改造", "名詞", "Biohacking blurs the line between man and machine.", "SF", "990"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = filled = skipped = 0
        for en, ja, pos, ex, domain, level in ITEMS:
            if en.lower() in existing:
                conn.execute(
                    "UPDATE words SET example = ? WHERE "
                    "LOWER(english)=LOWER(?) AND COALESCE(example,'')=''",
                    (ex, en),
                )
                filled += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing.add(en.lower())
            added += 1
    print(f"cyber/AI/SF words: +{added} (例文補充 {filled})")
    with db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        for dom in ("IT", "AI", "SF"):
            n = conn.execute(
                "SELECT COUNT(*) FROM words WHERE domain=?", (dom,)
            ).fetchone()[0]
            print(f"  domain={dom}: {n}")
    print(f"単語総数: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
