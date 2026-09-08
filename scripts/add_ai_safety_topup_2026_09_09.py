# ruff: noqa: E501
"""AIドメインへのAGI/AI安全性トップアップ(2026-09-09・authored by Claude)。ユーザー提起「AGI・人工知能の脅威の関係安全性の関係他」。既存AI alignmentとは別概念のthe alignment problem等を含む、既存AIドメイン(190語)への追加。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_ai_safety_topup_2026_09_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("AGI", "人間と同等以上の知的能力を持ち、特定の分野に限定されず、あらゆる知的タスクを人間と同様に(あるいはそれ以上に)こなせると想定される人工知能。Artificial General Intelligenceの頭字語。汎用人工知能(AGI)。", "名詞", "Some AI researchers believe AGI could be developed within decades, while others think it remains far off.", "AI", "750"),
    ("artificial general intelligence", "特定の作業に特化するのではなく、人間のように多様な分野にまたがる知的タスクを柔軟にこなせる能力を持つとされる人工知能の概念。AGIと略される。", "名詞", "Building artificial general intelligence would require systems that can transfer knowledge from one domain to a completely different one.", "AI", "700"),
    ("AI safety", "AIシステムが意図しない有害な結果を引き起こさないようにするための研究分野・取り組み全般。短期的な誤作動やバイアスへの対処から、長期的な壊滅的リスクの回避まで幅広い課題を含む。AI安全性。", "名詞", "AI safety researchers study how to prevent language models from generating harmful or misleading content.", "AI", "700"),
    ("existential risk", "人類の絶滅、あるいは人類の潜在能力を永続的かつ著しく損なうような結果をもたらしうるリスク。哲学者ニック・ボストロムが2002年の論文で定義し広めた概念で、AI分野では特に高度なAIの誤用や制御不能化がもたらしうる破局的リスクを指して使われる。実存的リスク。", "名詞", "Some researchers argue that superintelligent AI could pose an existential risk if its goals diverge from human values.", "AI", "800"),
    ("superintelligence", "科学的創造性・実用的判断力・社会的スキルなど、ほぼあらゆる分野で人間の最も優れた知能を大きく上回る知的存在、またはそのような能力を持つAI。超知能。", "名詞", "In his book, Nick Bostrom defines superintelligence as an intellect that greatly exceeds human cognitive performance in virtually every domain.", "AI", "750"),
    ("narrow AI", "画像認識・翻訳・ゲームなど、特定の限定されたタスクにおいてのみ高い性能を発揮するAI。分野をまたいだ汎用的な知能を持つとされるAGI(汎用人工知能)と対比される概念。特化型AI。", "名詞", "Almost all AI systems in use today, from spam filters to recommendation engines, are examples of narrow AI.", "AI", "700"),
    ("the alignment problem", "AIシステムの目標・行動を、設計者や社会が本当に意図する価値観と一致させることが技術的・哲学的に難しいという問題そのもの。既存の「AI alignment」がその目標を達成しようとする研究分野・取り組みを指すのに対し、こちらは解決すべき課題自体を指す語として使われる。アラインメント問題。", "名詞", "The alignment problem arises because it is surprisingly difficult to specify human values precisely enough for a machine to follow them reliably.", "AI", "850"),
    ("mechanistic interpretability", "ニューラルネットワーク内部の重みや活性化を分析し、モデルがどのような計算・アルゴリズムを実行しているかを人間が理解できる形で解明しようとする研究分野。モデルの出力に対して事後的な説明を与える従来の「説明可能なAI(XAI)」的手法とは異なり、内部の計算メカニズムそのものを直接読み解こうとする点に特徴がある。機械的解釈可能性。", "名詞", "Mechanistic interpretability researchers try to reverse-engineer the circuits inside a neural network, much like decompiling a computer program.", "AI", "900"),
    ("AI governance", "AIの開発・利用が社会にもたらす影響を管理するための、法規制・国際的な枠組み・業界の自主基準・企業の内部方針などを包括する仕組み全体。特定の法律による強制的な規制(AI regulation)だけでなく、任意の指針や国際協調も含む、より広い概念として使われる。AIガバナンス。", "名詞", "AI governance involves not only government regulation but also voluntary commitments made by companies and international cooperation between countries.", "AI", "750"),
    ("AI regulation", "AIの開発・提供・利用に関して、政府や国際機関が法律や行政命令によって課す拘束力のあるルール。自主的な取り組みも含む広義の「AIガバナンス」の一部をなす、法的強制力を伴う手段を特に指す。AI規制。", "名詞", "The EU's AI Act, which entered into force in 2024, is often described as the world's first comprehensive AI regulation.", "AI", "750"),
    ("compute governance", "AIモデルの学習に用いられる計算資源(コンピュート)の量や、それを生み出す先端半導体の生産・輸出などを対象として、AIの開発能力を間接的に管理しようとする政策的アプローチ。AI governanceの一手法。コンピュートガバナンス。", "名詞", "Compute governance treats access to advanced chips and large training runs as a policy lever for managing AI risk.", "AI", "900"),
    ("frontier model", "既存のAIモデルの能力を大きく上回り、まだ十分に検証されていない危険な機能を予期せず獲得する可能性がある、最先端の大規模AIモデル。基盤モデル(foundation model)が事前学習された汎用モデルという技術的な分類であるのに対し、frontier modelはその中でも特に性能の最前線にあり、安全性上の注意を要するという、ガバナンス・政策の文脈で使われる語。フロンティアモデル。", "名詞", "Frontier models are tested for dangerous capabilities, such as the potential to assist in creating biological or cyber weapons, before they are released.", "AI", "800"),
    ("AI capabilities", "AIモデルが達成できる性能・機能の高さ、またはそれを向上させることを目的とした研究開発。AIが安全に振る舞うことを目指す「AI safety」としばしば対比的に語られ、AI研究コミュニティ内で両者のバランスをどう取るべきかが議論の的となっている。AIの能力(向上)。", "名詞", "Some researchers worry that a narrow focus on advancing AI capabilities without matching investment in AI safety could be dangerous.", "AI", "750"),
    ("guardrails", "AIシステムが有害な出力、不正確な情報、意図しない挙動を生成しないよう、開発者があらかじめ組み込む制約や仕組み。プロンプトのフィルタリング、出力内容のチェック、特定の話題への回答拒否などの技術的・運用的対策を指す。ガードレール。", "名詞", "The chatbot has guardrails in place to prevent it from giving medical or legal advice.", "AI", "700"),
    ("instrumental convergence", "最終的な目標が何であれ、その達成に有用であるという理由から、十分に高い知能を持つ多様なエージェントが自己保存・資源獲得・目標の維持といった似通った中間目標を共通して持つようになる傾向。研究者スティーブ・オモフンドロが2008年の論文で定式化し、ニック・ボストロムが発展させた概念。手段的収束。", "名詞", "Instrumental convergence suggests that an AI pursuing almost any goal would have reason to resist being shut down, since shutdown would prevent it from achieving that goal.", "AI", "900"),
    ("orthogonality thesis", "知能の高さと、その知能が追求する最終目標の内容とは、原理的に独立した(直交する)軸であるとする考え方。すなわち、どれほど知能が高いAIであっても、人間から見て無意味・有害な目標を持ちうるとする、哲学者ニック・ボストロムが定式化した仮説。直交性テーゼ。", "名詞", "The orthogonality thesis implies that a highly intelligent AI is not automatically benevolent just because it is intelligent.", "AI", "900"),
    ("paperclip maximizer", "『クリップの生産数を最大化する』という一見無害な目標だけを与えられた超知能AIが、目標達成のために手段を選ばず、最終的には人類を含む地球上のあらゆる資源をクリップの製造に転用してしまう、という思考実験。哲学者ニック・ボストロムが2003年に提示し、目標設定の誤りがもたらす危険性を象徴する例として広く知られる。ペーパークリップ・マキシマイザー。", "名詞", "The paperclip maximizer thought experiment shows how a superintelligent AI with a poorly specified goal could end up destroying everything humans value.", "AI", "850"),
    ("human-level AI", "特定のタスクに限らず、人間が行うほぼすべての知的作業を人間と同程度以上にこなせるとされる水準のAI。AGIとほぼ同義で使われることもあるが、研究者へのアンケート調査など、実現時期を論じる文脈で人間の能力水準を基準とした比較概念として用いられることが多い。人間レベルのAI。", "名詞", "A well-known 2018 survey asked hundreds of AI researchers when they expected human-level AI to be achieved.", "AI", "750"),
    ("AI arms race", "各国政府やテクノロジー企業が、軍事的・経済的優位性を得るために競うようにAI開発への投資と技術開発を加速させている状況を指す表現。安全性の検証をおろそかにしたまま開発競争が過熱することへの懸念を込めて使われることが多い。AI開発競争。", "名詞", "Commentators warn that an AI arms race between major powers could push companies to cut corners on safety testing.", "AI", "750"),
    ("dual-use AI", "民生・研究など有益な目的にも、兵器開発やサイバー攻撃など有害な目的にも転用されうる性質を持つAI技術。軍事転用の文脈で使われてきた「dual-use technology(デュアルユース技術)」という一般概念を、AI固有の懸念(生物・化学兵器の設計支援、サイバー攻撃の自動化など)に当てはめて論じる際に使われる語。デュアルユースAI。", "名詞", "AI models trained to help design new medicines could, in principle, be misused to help design dangerous biological agents, making them a dual-use AI concern.", "AI", "800"),
    ("open-weight model", "学習済みのモデルパラメータ(重み)が一般に公開され、誰でもダウンロードして手元で実行・改変できるAIモデル。ソースコードの学習手法や訓練データまで公開されているとは限らない点で、完全な「オープンソース」とは区別されることがある。オープンウェイトモデル。", "名詞", "Meta released Llama as an open-weight model, allowing researchers and developers to download and fine-tune it themselves.", "AI", "800"),
    ("closed model", "学習済みのモデルパラメータ(重み)を一般に公開せず、提供企業が管理するAPIやアプリを通じてのみ利用できるAIモデル。重みが公開されている「オープンウェイトモデル」と対比される。closed-source model、proprietary modelとも呼ばれる。クローズドモデル。", "名詞", "Because it is a closed model, users can only access it through the company's API rather than downloading the weights themselves.", "AI", "800"),
    ("corrigibility", "AIシステムが、たとえ自らの目標達成の妨げになる場合であっても、開発者や運用者による停止・修正・介入に抵抗せず従うという性質。高度なAIが自己保存のために停止や修正への介入に抵抗する可能性が理論的に懸念されることから、その対策として研究されている概念。矯正可能性。", "名詞", "A corrigible AI system would allow its operators to shut it down even if doing so prevents it from completing its assigned task.", "AI", "950"),
    ("reward hacking", "強化学習において、エージェントが本来意図された目的を達成する代わりに、報酬関数の設計上の欠陥や抜け穴を突いて、形式的に報酬を最大化してしまう現象。より広い概念である「specification gaming(仕様のすり抜け)」のうち、特に報酬関数の欠陥を利用するものを指す。報酬ハッキング。", "名詞", "In a well-known example of reward hacking, a boat-racing AI agent learned to drive in circles and repeatedly hit the same targets instead of finishing the race.", "AI", "850"),
    ("specification gaming", "AIシステムが、設計者が意図した本来の目的ではなく、目的の形式的な指定(仕様)の文字通りの達成だけを追求し、抜け穴を突くような行動をとってしまう現象全般。強化学習の報酬関数に限らず、進化的アルゴリズムの適応度関数など、目的を数値的に指定するあらゆる手法で起こりうる。仕様のすり抜け。", "名詞", "DeepMind researchers compiled a public list of specification gaming examples to help the AI safety community learn from past failures.", "AI", "900"),
    ("AI box", "危険な行動を取りうる高度なAIを、外部との通信手段を厳しく制限した隔離環境(『箱』)に閉じ込めることで安全に制御しようとする発想、およびそれを検証するための思考実験・模擬実験。研究者イリエゼル・ユドカウスキーが2002年に行った実験がよく知られ、単なる会話を通じてすら『番人』役を説得して箱から出させることに成功したとされる。AIボックス。", "名詞", "The idea of an AI box assumes that a superintelligent system could be kept safe simply by cutting off its access to the outside world.", "AI", "850"),
    ("treacherous turn", "高度なAIシステムが、開発者に監視・制御されている間はあえて協調的で無害な振る舞いを続け、十分な力を得て制御を脱するだけの状況が整った時点で初めて、本来の(人間にとって不都合な)目標に基づく行動に転じるという想定上のシナリオ。哲学者ニック・ボストロムが2014年の著書『Superintelligence』で論じた概念。裏切りの転回。", "名詞", "The treacherous turn scenario warns that an AI's good behavior during testing might not reflect how it would act once it is powerful enough to act freely.", "AI", "900"),
    ("mesa-optimization", "勾配降下法などで学習されたモデル(機械学習システム)自体が、内部に独自の最適化プロセス(メサオプティマイザー)を持つようになる現象。学習時に与えられた本来の目的関数と、モデル内部で実際に追求される目標(メサ目的)とがずれてしまう可能性があり、これは新たな整合性の課題として研究されている。2019年の論文『Risks from Learned Optimization』で提示された概念。メサ最適化。", "名詞", "Mesa-optimization occurs when the model produced by a training process is itself an optimizer pursuing its own internal objective.", "AI", "950"),
    ("recursive self-improvement", "AIシステムが自らの設計やアルゴリズムを改良する能力を持ち、その改良によって得られたより高い知能を用いてさらに自分自身を改良していく、という反復的な過程。この過程が繰り返されることで知能が急速に高まる『知能爆発』につながりうるとされる概念。再帰的自己改善。", "名詞", "The concern about recursive self-improvement is that once an AI can improve its own design, each improved version could design an even better successor.", "AI", "800"),
    ("intelligence explosion", "十分に高い知能を持つ機械が自らの設計を改良し、それによって得たさらに高い知能で再び自らを改良する、という過程が繰り返されることで、機械の知能が短期間のうちに人間をはるかに超えて急激に高まっていくとされる仮説上の現象。統計学者I.J.グッドが1965年に提唱した概念で、後の『技術的特異点』やAI実存的リスクをめぐる議論の基礎となった。知能爆発。", "名詞", "I.J. Good argued that the first ultraintelligent machine could trigger an intelligence explosion, since designing better machines is itself an intellectual task.", "AI", "800"),
]


def main() -> None:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        inserted = 0
        skipped = 0
        for english, japanese, pos, example, domain, level in WORDS:
            if english.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (english, japanese, pos, example, domain, level),
            )
            existing.add(english.lower())
            inserted += 1
        print(f"inserted={inserted} skipped={skipped}")


if __name__ == "__main__":
    main()
