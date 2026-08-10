# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Expand the existing `AI` domain / `AI・機械学習の技術英語` scene into areas
that were previously thin, authored by Claude (2026-08-10・ユーザー要望).

投入前に既存119語(`SELECT english FROM words WHERE domain='AI'`)・既存22
フレーズ(`SELECT japanese FROM phrases WHERE scene='AI・機械学習の技術英語'`)
を確認し、さらに `words` テーブル全体(他ドメイン含む)ともenglish文字列の
重複がないか確認済み。特に以下は既に別ドメインで存在するため今回は含めて
いない: GPU/NPU(`半導体`), matrix/dot product/linear algebra/eigenvalue/
partial derivative/calculus(`数学`), probability distribution/normal
distribution(`統計学`), vector/scalar(`物理`), temperature(`科学`),
alignment(`管理`), singularity(`SF`), token(一般語), tensor(`AI`に既存)。
これらの代わりにTPU/AI accelerator/AI alignment/technological singularity/
output token等の類語・複合語で領域をカバーしている。

対象語彙(手薄だった6分野を補強):
- **ハードウェア**: TPU, VRAM, CUDA core, tensor core, inference chip,
  edge device, AI accelerator, on-device inference。
- **手法(画像・テキストのタスク種別)**: image classification, object
  detection, semantic/instance segmentation, named entity recognition,
  sentiment analysis, anomaly detection。
- **モデル・アーキテクチャの一般名称**(実在の商用モデル名・企業名は一切
  不使用): RNN, LSTM, GAN, diffusion model, autoencoder, encoder-decoder
  model, LLM, foundation model, multimodal model, mixture of experts,
  vision transformer。
- **AIにまつわる数学用語**(既存の行列・線形代数語彙とは非重複の範囲):
  Bayesian, chain rule, likelihood, prior/posterior probability, cosine
  similarity, Euclidean distance, dimensionality reduction, stochastic。
- **LLM特有の用語**: tokenizer, output token, sampling temperature,
  top-p sampling, chain-of-thought, system prompt, RLHF, AI alignment,
  context length。
- **G検定・E資格で問われる概念・歴史・倫理用語**: AI effect, technological
  singularity, Turing test, frame problem, symbol grounding problem,
  explainable AI, AI ethics, algorithmic bias, trolley problem, AI winter。

想定読者はAI学習者・指導者からAI初心者まで幅広いため、level(難易度)は
300番台の平易な概念語(large language model, AI ethics等)から900番台の
専門用語(posterior probability, RLHF, symbol grounding problem等)まで
分布させている。

フレーズはAIの仕組みを初心者に説明する文と、エンジニア同士の技術的な
会話文の両方を含む。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased), checked
against ALL domains, not just `AI`.

Run:  python scripts/add_ai_ml_expanded.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- ハードウェア ---
    ("TPU", "TPU（Google発のAI専用演算チップ）", "名詞", "TPUs are optimized for large-scale machine learning workloads.", "AI", "750"),
    ("VRAM", "VRAM（GPUに搭載されるメモリ）", "名詞", "We ran out of VRAM while training the larger model.", "AI", "700"),
    ("CUDA core", "CUDAコア（GPU内の並列演算ユニット）", "名詞", "This GPU has thousands of CUDA cores for parallel processing.", "AI", "800"),
    ("tensor core", "テンソルコア（行列演算に特化した演算ユニット）", "名詞", "Tensor cores speed up the matrix multiplications used in deep learning.", "AI", "850"),
    ("inference chip", "推論専用チップ", "名詞", "The company designed a dedicated inference chip for its data centers.", "AI", "800"),
    ("edge device", "エッジデバイス（末端の小型機器）", "名詞", "We deployed a compressed model to run on the edge device.", "AI", "600"),
    ("AI accelerator", "AIアクセラレータ（AI処理専用ハードウェア）", "名詞", "An AI accelerator handles neural network math far faster than a general CPU.", "AI", "700"),
    ("on-device inference", "オンデバイス推論（端末上での推論実行）", "名詞", "On-device inference keeps your data private because nothing is sent to a server.", "AI", "750"),
    # --- 手法(タスクの種類) ---
    ("image classification", "画像分類", "名詞", "Image classification assigns a single label to an entire picture.", "AI", "400"),
    ("object detection", "物体検出", "名詞", "Object detection draws a box around every car in the photo.", "AI", "500"),
    ("semantic segmentation", "セマンティックセグメンテーション（画素単位の意味分類）", "名詞", "Semantic segmentation labels every pixel in the image by category.", "AI", "800"),
    ("instance segmentation", "インスタンスセグメンテーション（個体単位の領域分割）", "名詞", "Instance segmentation can tell two overlapping people apart, unlike semantic segmentation.", "AI", "850"),
    ("named entity recognition", "固有表現認識", "名詞", "Named entity recognition pulls out names, places, and dates from a document.", "AI", "750"),
    ("sentiment analysis", "感情分析", "名詞", "Sentiment analysis showed that most reviews were positive.", "AI", "600"),
    ("anomaly detection", "異常検知", "名詞", "Anomaly detection flags transactions that look very different from the usual pattern.", "AI", "650"),
    # --- モデル・アーキテクチャの一般名称 ---
    ("large language model", "大規模言語モデル（LLM）", "名詞", "A large language model is trained on huge amounts of text.", "AI", "350"),
    ("recurrent neural network", "再帰型ニューラルネットワーク（RNN）", "名詞", "A recurrent neural network processes sequences one step at a time.", "AI", "700"),
    ("long short-term memory", "長短期記憶（LSTM）", "名詞", "Long short-term memory networks were designed to remember information over long sequences.", "AI", "850"),
    ("generative adversarial network", "敵対的生成ネットワーク（GAN）", "名詞", "A generative adversarial network pits two models against each other to improve both.", "AI", "800"),
    ("diffusion model", "拡散モデル", "名詞", "A diffusion model gradually turns random noise into a realistic image.", "AI", "600"),
    ("autoencoder", "オートエンコーダ", "名詞", "An autoencoder learns to compress data and then reconstruct it as closely as possible.", "AI", "750"),
    ("encoder-decoder model", "エンコーダ・デコーダモデル", "名詞", "An encoder-decoder model reads the input first and then generates the output.", "AI", "800"),
    ("foundation model", "基盤モデル", "名詞", "A foundation model is pretrained on broad data and then adapted to many tasks.", "AI", "550"),
    ("multimodal model", "マルチモーダルモデル（複数種類のデータを扱うモデル）", "名詞", "A multimodal model can process both images and text at once.", "AI", "500"),
    ("mixture of experts", "専門家混合モデル（MoE）", "名詞", "A mixture of experts only activates a few specialized sub-networks for each input.", "AI", "850"),
    ("vision transformer", "ビジョントランスフォーマー（画像向けTransformer）", "名詞", "A vision transformer applies the transformer architecture directly to image patches.", "AI", "800"),
    # --- AIにまつわる数学用語 ---
    ("Bayesian", "ベイズ的な", "形容詞", "A Bayesian approach updates your belief as new evidence arrives.", "AI", "700"),
    ("chain rule", "連鎖律", "名詞", "Backpropagation relies on the chain rule to compute gradients layer by layer.", "AI", "750"),
    ("likelihood", "尤度", "名詞", "The model chooses parameters that maximize the likelihood of the observed data.", "AI", "800"),
    ("prior probability", "事前確率", "名詞", "The prior probability reflects what we believed before seeing any new data.", "AI", "850"),
    ("posterior probability", "事後確率", "名詞", "The posterior probability is updated after taking the new evidence into account.", "AI", "900"),
    ("cosine similarity", "コサイン類似度", "名詞", "Cosine similarity measures how close two embedding vectors point in the same direction.", "AI", "800"),
    ("Euclidean distance", "ユークリッド距離", "名詞", "Euclidean distance measures the straight-line distance between two points.", "AI", "750"),
    ("dimensionality reduction", "次元削減", "名詞", "Dimensionality reduction makes high-dimensional data easier to visualize.", "AI", "800"),
    ("stochastic", "確率的な", "形容詞", "Stochastic gradient descent updates the weights using small random batches of data.", "AI", "700"),
    # --- LLM特有の用語 ---
    ("tokenizer", "トークナイザー（文章をトークンに分割する仕組み）", "名詞", "The tokenizer splits raw text into tokens the model can understand.", "AI", "600"),
    ("output token", "出力トークン", "名詞", "The model generates one output token at a time.", "AI", "650"),
    ("sampling temperature", "サンプリング温度", "名詞", "Lower the sampling temperature if you want more predictable output.", "AI", "700"),
    ("top-p sampling", "トップpサンプリング（核サンプリング）", "名詞", "Top-p sampling only considers tokens whose combined probability reaches a threshold.", "AI", "850"),
    ("chain-of-thought", "思考の連鎖（段階的な推論プロセス）", "名詞", "Chain-of-thought prompting encourages the model to reason step by step.", "AI", "650"),
    ("system prompt", "システムプロンプト", "名詞", "The system prompt sets the assistant's overall behavior before the conversation starts.", "AI", "500"),
    ("RLHF", "人間のフィードバックによる強化学習（RLHF）", "名詞", "RLHF uses human feedback to shape the model's responses.", "AI", "900"),
    ("AI alignment", "AIアラインメント（AIの目標を人間の意図に合わせること）", "名詞", "AI alignment research tries to make sure a model pursues the goals we actually intend.", "AI", "750"),
    ("context length", "コンテキスト長", "名詞", "The conversation got cut off once we exceeded the context length.", "AI", "550"),
    # --- G検定・E資格で問われる概念・歴史・倫理用語 ---
    ("AI effect", "AI効果（実現すると『これはAIではない』とみなされる現象）", "名詞", "The AI effect explains why solved problems stop being called AI.", "AI", "800"),
    ("technological singularity", "技術的特異点（シンギュラリティ）", "名詞", "Some researchers debate whether a technological singularity will ever happen.", "AI", "700"),
    ("Turing test", "チューリングテスト", "名詞", "The Turing test checks whether a person can tell a machine from a human in conversation.", "AI", "450"),
    ("frame problem", "フレーム問題", "名詞", "The frame problem asks how an AI decides which facts actually matter in a given situation.", "AI", "850"),
    ("symbol grounding problem", "シンボルグラウンディング問題（記号接地問題）", "名詞", "The symbol grounding problem asks how symbols get connected to real-world meaning.", "AI", "900"),
    ("explainable AI", "説明可能なAI（XAI）", "名詞", "Explainable AI tries to make a model's decisions understandable to the people affected by them.", "AI", "700"),
    ("AI ethics", "AI倫理", "名詞", "AI ethics asks how we should build and use these systems responsibly.", "AI", "350"),
    ("algorithmic bias", "アルゴリズムバイアス", "名詞", "Algorithmic bias can creep in when the training data isn't diverse enough.", "AI", "650"),
    ("trolley problem", "トロッコ問題", "名詞", "The trolley problem often comes up when people discuss the ethics of self-driving cars.", "AI", "600"),
    ("AI winter", "AIの冬の時代（研究資金が減退した時期）", "名詞", "Funding dried up during the AI winter of the 1970s and again in the late 1980s.", "AI", "750"),
]

PHRASES: list[tuple[str, str]] = [
    ("A GPU can perform many calculations in parallel, which speeds up training.", "GPUは並列に多くの計算を行えるため、学習が高速化されます。"),
    ("We're evaluating a TPU cluster to cut our training costs.", "学習コストを削減するためTPUクラスターを検討しています。"),
    ("This model runs entirely on-device, so no data ever leaves the phone.", "このモデルは完全にデバイス上で動作するため、データが端末外に出ることはありません。"),
    ("Edge devices don't have much VRAM, so we had to shrink the model first.", "エッジデバイスはVRAMが少ないため、まずモデルを小型化する必要がありました。"),
    ("Object detection draws a box around every item it finds in the image.", "物体検出は画像内で見つけた物体それぞれを四角で囲みます。"),
    ("Semantic segmentation labels every single pixel in the image.", "セマンティックセグメンテーションは画像内のすべてのピクセルにラベルを付けます。"),
    ("Sentiment analysis tells us whether a review is mostly positive or negative.", "感情分析はレビューが主に肯定的か否定的かを判定します。"),
    ("Named entity recognition pulls names, places, and dates out of the text.", "固有表現認識はテキストから人名・地名・日付を抽出します。"),
    ("The system used anomaly detection to flag this transaction automatically.", "このシステムは異常検知を使ってこの取引を自動的にフラグ付けしました。"),
    ("A large language model predicts the next word based on huge amounts of text.", "大規模言語モデルは膨大なテキストをもとに次の単語を予測します。"),
    ("A diffusion model starts from random noise and gradually turns it into an image.", "拡散モデルはランダムなノイズから始めて、徐々に画像へと変えていきます。"),
    ("This is a generative adversarial network, so two models compete to improve each other.", "これは敵対的生成ネットワークで、2つのモデルが互いを高め合うように競います。"),
    ("An autoencoder learns to compress data and then reconstruct it as closely as possible.", "オートエンコーダはデータを圧縮し、できるだけ忠実に再構築することを学習します。"),
    ("Vision transformers apply the transformer architecture directly to image patches.", "Vision Transformerはトランスフォーマーアーキテクチャを画像パッチに直接応用します。"),
    ("A mixture of experts only activates a few sub-networks for each input.", "専門家混合モデルは入力ごとに一部のサブネットワークだけを活性化します。"),
    ("Try lowering the sampling temperature if you want more predictable output.", "より予測しやすい出力にしたいならサンプリング温度を下げてみてください。"),
    ("Top-p sampling only considers the tokens that make up the most likely mass of probability.", "Top-pサンプリングは、確率の大部分を占める最も可能性の高いトークンだけを考慮します。"),
    ("Chain-of-thought prompting helps the model reason through a problem step by step.", "思考の連鎖(Chain-of-thought)プロンプティングは、モデルが問題を段階的に推論するのを助けます。"),
    ("We adjusted the system prompt to make the assistant sound more concise.", "アシスタントをより簡潔にするため、システムプロンプトを調整しました。"),
    ("RLHF uses human feedback to fine-tune how the model behaves.", "RLHFは人間のフィードバックを使ってモデルの振る舞いを微調整します。"),
    ("AI alignment research tries to make sure a model pursues the goals we actually want.", "AIアラインメント研究は、モデルが私たちが本当に望む目標を追求するようにすることを目指しています。"),
    ("We ran out of context length halfway through the document.", "文書の途中でコンテキスト長が足りなくなりました。"),
    ("Can you explain the Turing test in simple terms?", "チューリングテストを簡単な言葉で説明してもらえますか？"),
    ("Some researchers worry about a coming technological singularity.", "一部の研究者は、いずれ訪れる技術的特異点を懸念しています。"),
    ("The frame problem asks how an AI knows which facts are actually relevant.", "フレーム問題は、AIがどの事実が本当に関連するかをどう知るのかを問う問題です。"),
    ("Explainable AI tries to make a model's decisions understandable to the people it affects.", "説明可能なAI(XAI)は、モデルの判断をそれに影響を受ける人々に理解できるようにしようとします。"),
    ("Algorithmic bias can creep in when the training data isn't diverse enough.", "訓練データに十分な多様性がないと、アルゴリズムバイアスが入り込むことがあります。"),
    ("The trolley problem often comes up when people discuss self-driving car ethics.", "トロッコ問題は、自動運転車の倫理について議論する際によく話題になります。"),
    ("Funding dried up during the AI winter of the 1970s.", "1970年代のAIの冬の時代には、資金提供が枯渇しました。"),
    ("Bayesian methods update your belief as new evidence comes in.", "ベイズ的な手法は、新しい証拠が入るたびに信念を更新します。"),
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
                "VALUES (?, ?, 'AI・機械学習の技術英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
