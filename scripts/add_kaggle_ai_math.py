# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated words & phrases for KAGGLE / ML-COMPETITION / AI・DATA
SCIENCE / MATH vocabulary, authored by Claude.

Focus (フレーズ集・単語集の手薄な領域を補強): Kaggle等の機械学習コンペで
実際に飛び交う専門語彙（リーダーボード、CV、特徴量エンジニアリング、
アンサンブル、data leakage等）、論文・GitHubリポジトリを読むエンジニアが
出会う AI/ML の技術英語（ニューラルネット構成要素、Transformer、LLM用語）、
ML/データ実務に関わるソフトウェア工学語彙（コンテナ化、再現性、ETL等）、
そして線形代数・統計の実務数学語彙（行列、勾配、分散、固有値等）。

対象読者: Kaggleコンペを追いかけ、論文やGitHubリポジトリを読み、AI/データ
サイエンスの現場で働くエンジニア。

既存の `AI` ドメイン（thinking/processing の比喩語彙が中心）、`IT` ドメイン
（一般的なソフトウェア工学語彙）、`数学` ドメイン（四則演算・基礎幾何・
基礎微積分等）とは重複しないよう、投入前に確認済み。より専門的・実務的な
語彙を追加する。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_kaggle_ai_math.py
      python scripts/add_kaggle_ai_math.py --missing-words   # report only

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "Kaggle・機械学習コンペ": [
        ("What's your CV score?", "CVスコア（交差検証のスコア）はどれくらい？"),
        ("My local CV doesn't match the public leaderboard.", "ローカルのCVがパブリックリーダーボードと一致しません。"),
        ("This feature is leaking information from the target.", "この特徴量はターゲットの情報がリークしています。"),
        ("Let's blend our models before the deadline.", "締め切り前にモデルをブレンドしましょう。"),
        ("There was a huge shake-up on the leaderboard.", "リーダーボードで大きなシェイクアップ（順位変動）がありました。"),
        ("I trust my CV more than the public LB.", "パブリックLBよりも自分のCVを信頼しています。"),
        ("We should submit a simple baseline first.", "まずはシンプルなベースラインを提出すべきです。"),
        ("How many folds are you using for cross-validation?", "交差検証は何foldでやっていますか？"),
        ("This model is clearly overfitting to the training set.", "このモデルは明らかに訓練データに過学習しています。"),
        ("Try stacking the outputs of these three models.", "この3つのモデルの出力をスタッキングしてみてください。"),
        ("We ran out of submissions for today.", "今日の提出回数を使い切りました。"),
        ("Did you check the discussion forum for leaks?", "ディスカッションフォーラムでリーク情報を確認しましたか？"),
        ("Our private LB score dropped a lot from the public one.", "プライベートLBのスコアがパブリックから大きく下がりました。"),
        ("Let's do an ablation study to see which feature matters most.", "どの特徴量が効いているか、アブレーションスタディをやりましょう。"),
        ("I'm doing a grid search over these hyperparameters.", "このハイパーパラメータについてグリッドサーチをしています。"),
        ("Early stopping kicked in after 20 rounds.", "20ラウンド後にアーリーストッピングが発動しました。"),
        ("This kernel shares a nice EDA of the dataset.", "このカーネルはデータセットのいいEDAを共有しています。"),
        ("We need a proper held-out set to evaluate this.", "これを評価するにはちゃんとしたホールドアウトセットが必要です。"),
        ("Their solution reached near-SOTA performance.", "彼らの解法はほぼSOTAの性能に達しました。"),
        ("Feature importance shows this column barely matters.", "特徴量重要度を見ると、この列はほとんど効いていません。"),
        ("Let's freeze the pipeline before the final submission.", "最終提出の前にパイプラインを固定しましょう。"),
        ("The gold medal solutions are usually huge ensembles.", "金メダルの解法は大抵巨大なアンサンブルです。"),
        ("Watch out for train/test split contamination.", "訓練・テスト分割の汚染に気をつけてください。"),
        ("Our gradient boosting model beat the neural net baseline.", "勾配ブースティングのモデルがニューラルネットのベースラインを上回りました。"),
    ],
    "AI・機械学習の技術英語": [
        ("The model failed to converge during training.", "モデルは訓練中に収束しませんでした。"),
        ("We fine-tuned a pretrained model on our own dataset.", "事前学習済みモデルを自前のデータセットでファインチューニングしました。"),
        ("The attention mechanism lets the model focus on relevant tokens.", "アテンション機構はモデルが関連するトークンに注目できるようにします。"),
        ("This LLM is hallucinating facts that aren't in the source.", "このLLMは元の資料にない事実を幻覚（ハルシネーション）で作り出しています。"),
        ("We're running low on context window for this prompt.", "このプロンプトはコンテキストウィンドウが足りなくなってきています。"),
        ("Prompt engineering made a huge difference in output quality.", "プロンプトエンジニアリングで出力品質が大きく変わりました。"),
        ("RAG lets the model retrieve documents before answering.", "RAGはモデルが回答前に文書を検索できるようにします。"),
        ("Should we fine-tune the model or just improve the prompt?", "モデルをファインチューニングすべきか、それともプロンプトを改善すべきか？"),
        ("The confusion matrix shows a lot of false positives.", "混同行列を見ると偽陽性が多いです。"),
        ("Precision is high but recall is really low.", "適合率は高いですが、再現率がかなり低いです。"),
        ("The F1 score improved after we balanced the dataset.", "データセットのバランスを取った後、F1スコアが改善しました。"),
        ("Check the AUC-ROC before deciding on a threshold.", "閾値を決める前にAUC-ROCを確認してください。"),
        ("Add dropout to reduce overfitting.", "過学習を減らすためにドロップアウトを加えてください。"),
        ("Batch normalization stabilized the training.", "バッチ正規化で訓練が安定しました。"),
        ("The loss isn't going down after a few epochs.", "数エポック経っても損失が下がっていません。"),
        ("We need to increase the batch size to speed things up.", "処理を速くするためにバッチサイズを増やす必要があります。"),
        ("The embedding space captures semantic similarity well.", "この埋め込み空間は意味的な類似性をよく捉えています。"),
        ("Backpropagation updates the weights layer by layer.", "誤差逆伝播は層ごとに重みを更新します。"),
        ("This is a classic case of vanishing gradients.", "これは勾配消失の典型例です。"),
        ("The generative model produces surprisingly realistic images.", "この生成モデルは驚くほどリアルな画像を生成します。"),
        ("We saved a checkpoint every 1,000 steps.", "1,000ステップごとにチェックポイントを保存しました。"),
        ("The learning rate schedule decays after each epoch.", "学習率スケジュールは各エポック後に減衰します。"),
    ],
    "データサイエンス実務": [
        ("Can you reproduce this result on a fresh environment?", "この結果、まっさらな環境で再現できますか？"),
        ("We should move this notebook logic into a proper script.", "このノートブックのロジックをちゃんとしたスクリプトに移すべきです。"),
        ("Set up a virtual environment before installing dependencies.", "依存関係をインストールする前に仮想環境を作ってください。"),
        ("We hit the API rate limit again.", "またAPIのレート制限に引っかかりました。"),
        ("The data pipeline broke because of a schema change.", "スキーマの変更でデータパイプラインが壊れました。"),
        ("There are too many missing values in this column.", "この列は欠損値が多すぎます。"),
        ("Let's remove that outlier before computing the average.", "平均を計算する前にその外れ値を除いてください。"),
        ("Did you normalize the features before training?", "訓練前に特徴量を正規化しましたか？"),
        ("The ETL job failed overnight.", "夜間のETLジョブが失敗しました。"),
        ("Let's containerize this so it runs the same everywhere.", "どこでも同じように動くようコンテナ化しましょう。"),
        ("This dependency conflicts with the one we already use.", "この依存関係は既存のものと衝突します。"),
        ("What's the correlation between these two variables?", "この2つの変数の相関はどのくらいですか？"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- Kaggle / ML competition vocabulary ---
    ("leaderboard", "リーダーボード（順位表）", "名詞", "Check the public leaderboard for your rank.", "AI", "650"),
    ("submission", "提出（結果の投稿）", "名詞", "We have one submission left for today.", "AI", "600"),
    ("baseline model", "ベースラインモデル", "名詞", "Always start with a simple baseline model.", "AI", "700"),
    ("cross-validation", "交差検証", "名詞", "Cross-validation gives a more reliable score.", "AI", "800"),
    ("K-fold", "K分割（交差検証の分割数）", "名詞", "We used five-fold, that is K-fold, cross-validation.", "AI", "850"),
    ("underfitting", "未学習・当てはまり不足", "名詞", "Underfitting means the model is too simple.", "AI", "800"),
    ("feature engineering", "特徴量エンジニアリング", "名詞", "Feature engineering often matters more than the model.", "AI", "800"),
    ("feature importance", "特徴量重要度", "名詞", "Feature importance ranks which columns matter most.", "AI", "800"),
    ("ensemble method", "アンサンブル手法（複数モデルの組み合わせ）", "名詞", "An ensemble method combines several models into one.", "AI", "800"),
    ("stacking", "スタッキング（モデルを重ねる手法）", "名詞", "Stacking combines predictions from several models.", "AI", "900"),
    ("blending", "ブレンディング（予測の混合）", "名詞", "We used blending instead of full stacking.", "AI", "900"),
    ("ablation study", "アブレーションスタディ（要素除去実験）", "名詞", "The ablation study showed which module helped most.", "AI", "950"),
    ("hyperparameter tuning", "ハイパーパラメータ調整", "名詞", "Hyperparameter tuning took most of our compute budget.", "AI", "850"),
    ("grid search", "グリッドサーチ", "名詞", "We ran a grid search over the learning rate.", "AI", "850"),
    ("early stopping", "アーリーストッピング（早期終了）", "名詞", "Early stopping prevents the model from overfitting.", "AI", "800"),
    ("data leakage", "データリーク（情報漏洩）", "名詞", "Data leakage inflated our validation score.", "AI", "900"),
    ("held-out set", "ホールドアウトセット（保留データ）", "名詞", "We evaluated the final model on a held-out set.", "AI", "850"),
    ("exploratory data analysis", "探索的データ分析", "名詞", "Exploratory data analysis comes before modeling.", "AI", "850"),
    ("pipeline", "パイプライン（処理の一連の流れ）", "名詞", "The whole pipeline runs in under an hour.", "IT", "700"),
    ("state of the art", "最先端の（技術水準）", "形容詞", "This model achieves state of the art accuracy.", "AI", "900"),
    ("inference time", "推論時間", "名詞", "Inference time matters for real-time applications.", "AI", "800"),
    ("checkpoint", "チェックポイント（学習途中の保存点）", "名詞", "We restored training from the last checkpoint.", "AI", "750"),
    ("learning rate schedule", "学習率スケジュール", "名詞", "The learning rate schedule decays over time.", "AI", "900"),
    ("gradient boosting", "勾配ブースティング", "名詞", "Gradient boosting is popular for tabular data.", "AI", "900"),
    ("shake-up", "シェイクアップ（順位の大変動）", "名詞", "There was a massive shake-up after the private LB reveal.", "AI", "990+"),
    ("public leaderboard", "パブリックリーダーボード", "名詞", "Don't overfit to the public leaderboard.", "AI", "850"),
    ("private leaderboard", "プライベートリーダーボード", "名詞", "The private leaderboard decides the final ranking.", "AI", "850"),
    ("out-of-fold prediction", "アウトオブフォールド予測（OOF）", "名詞", "We generated out-of-fold predictions for stacking.", "AI", "950"),
    ("test-time augmentation", "テスト時データ拡張（TTA）", "名詞", "Test-time augmentation gave us a small score boost.", "AI", "950"),
    ("pseudo-labeling", "疑似ラベリング", "名詞", "Pseudo-labeling adds confident predictions as new labels.", "AI", "950"),
    ("target encoding", "ターゲットエンコーディング", "名詞", "Target encoding replaces categories with target statistics.", "AI", "900"),
    ("one-hot encoding", "ワンホットエンコーディング", "名詞", "One-hot encoding turns categories into binary columns.", "AI", "800"),
    ("label encoding", "ラベルエンコーディング", "名詞", "Label encoding maps each category to an integer.", "AI", "800"),
    ("feature selection", "特徴量選択", "名詞", "Feature selection removes columns that don't help.", "AI", "800"),
    ("class imbalance", "クラス不均衡", "名詞", "Class imbalance makes accuracy a misleading metric.", "AI", "850"),
    ("root mean squared error", "二乗平均平方根誤差（RMSE）", "名詞", "The competition is scored by root mean squared error.", "AI", "850"),
    ("log loss", "対数損失", "名詞", "Log loss punishes confident wrong predictions heavily.", "AI", "900"),
    # --- AI / ML general technical vocabulary ---
    ("hidden layer", "隠れ層（ニューラルネットの中間層）", "名詞", "The hidden layer transforms the input representation.", "AI", "750"),
    ("validation set", "検証データセット", "名詞", "We tuned hyperparameters using the validation set.", "AI", "750"),
    ("weight", "重み（パラメータ）", "名詞", "The optimizer updates the weights each step.", "AI", "650"),
    ("gradient clipping", "勾配クリッピング", "名詞", "Gradient clipping prevents exploding gradients.", "AI", "950"),
    ("training iteration", "訓練の反復（1回分の更新）", "名詞", "The loss dropped steadily over many training iterations.", "AI", "700"),
    ("batch size", "バッチサイズ", "名詞", "A larger batch size can speed up training.", "AI", "700"),
    ("logits", "ロジット（活性化前の生の出力値）", "名詞", "The model outputs raw logits before the softmax.", "AI", "950"),
    ("word embedding", "単語埋め込み（ベクトル表現）", "名詞", "Word embeddings capture semantic meaning.", "AI", "800"),
    ("attention mechanism", "アテンション機構", "名詞", "The attention mechanism weighs each input token.", "AI", "900"),
    ("transformer architecture", "トランスフォーマーアーキテクチャ", "名詞", "Most modern language models use a transformer architecture.", "AI", "850"),
    ("instruction tuning", "指示チューニング", "名詞", "Instruction tuning teaches the model to follow commands.", "AI", "950"),
    ("pretraining", "事前学習", "名詞", "Pretraining uses a huge amount of unlabeled text.", "AI", "850"),
    ("test set", "テストデータセット", "名詞", "We evaluate final performance on the test set.", "AI", "700"),
    ("training set", "訓練データセット", "名詞", "The model learns patterns from the training set.", "AI", "650"),
    ("label", "ラベル（正解データ）", "名詞", "Each image comes with a label.", "AI", "600"),
    ("ground truth", "正解データ", "名詞", "We compared predictions against the ground truth.", "AI", "800"),
    ("confusion matrix", "混同行列", "名詞", "The confusion matrix shows where the model fails.", "AI", "850"),
    ("precision", "適合率（精度指標）", "名詞", "High precision means few false positives.", "AI", "800"),
    ("sensitivity", "感度（再現率と同義で使われる統計指標）", "名詞", "Sensitivity measures how many true positives we catch.", "AI", "850"),
    ("F1 score", "F1スコア", "名詞", "The F1 score balances precision and recall.", "AI", "850"),
    ("AUC-ROC", "AUC-ROC（分類性能指標）", "名詞", "AUC-ROC summarizes performance across thresholds.", "AI", "950"),
    ("weight decay", "重み減衰（正則化手法の一種）", "名詞", "Weight decay shrinks the model's weights during training.", "AI", "900"),
    ("batch normalization", "バッチ正規化", "名詞", "Batch normalization keeps activations stable.", "AI", "900"),
    ("convolutional neural network", "畳み込みニューラルネットワーク", "名詞", "A convolutional neural network processes images well.", "AI", "850"),
    ("latent space", "潜在空間", "名詞", "Similar images cluster together in latent space.", "AI", "950"),
    ("generative model", "生成モデル", "名詞", "A generative model can create new images.", "AI", "800"),
    ("hallucination", "幻覚（LLMの事実誤認生成）", "名詞", "Hallucination is a known problem with LLMs.", "AI", "850"),
    ("input token", "入力トークン（テキストの最小処理単位）", "名詞", "The tokenizer splits text into input tokens.", "AI", "800"),
    ("context window", "コンテキストウィンドウ", "名詞", "Long documents can exceed the context window.", "AI", "850"),
    ("prompt engineering", "プロンプトエンジニアリング", "名詞", "Prompt engineering can improve output without retraining.", "AI", "800"),
    ("retrieval-augmented generation", "検索拡張生成", "名詞", "Retrieval-augmented generation reduces hallucination.", "AI", "950"),
    ("vanishing gradient", "勾配消失", "名詞", "This is a classic case of the vanishing gradient problem.", "AI", "900"),
    ("self-attention", "自己注意機構", "名詞", "Self-attention lets each token attend to every other token.", "AI", "900"),
    ("positional encoding", "位置エンコーディング", "名詞", "Positional encoding tells the model the order of tokens.", "AI", "950"),
    ("zero-shot", "ゼロショット（例示なしでの推論）", "形容詞", "The model handled the task in a zero-shot setting.", "AI", "850"),
    ("few-shot learning", "少数例学習", "名詞", "Few-shot learning works with just a handful of examples.", "AI", "850"),
    ("in-context learning", "文脈内学習", "名詞", "In-context learning happens without updating any weights.", "AI", "900"),
    ("knowledge distillation", "知識蒸留", "名詞", "Knowledge distillation trains a small model to mimic a big one.", "AI", "950"),
    ("quantization", "量子化（モデル軽量化手法）", "名詞", "Quantization shrinks the model to run faster on edge devices.", "AI", "900"),
    ("model compression", "モデル圧縮", "名詞", "Model compression makes the model easier to deploy.", "AI", "900"),
    ("batch inference", "バッチ推論", "名詞", "We run batch inference overnight instead of in real time.", "AI", "850"),
    ("softmax", "ソフトマックス関数", "名詞", "Softmax turns logits into a probability distribution.", "AI", "900"),
    ("sigmoid function", "シグモイド関数", "名詞", "The sigmoid function squashes values between zero and one.", "AI", "850"),
    ("semi-supervised learning", "半教師あり学習", "名詞", "Semi-supervised learning uses both labeled and unlabeled data.", "AI", "850"),
    # --- Software engineering vocabulary for ML/data work ---
    ("containerization", "コンテナ化", "名詞", "Containerization makes deployment consistent.", "IT", "850"),
    ("random seed", "乱数シード", "名詞", "Setting a random seed makes results reproducible.", "AI", "800"),
    ("notebook", "ノートブック（対話型実行環境）", "名詞", "We prototyped the model in a notebook.", "IT", "600"),
    ("virtual environment", "仮想環境", "名詞", "Always work inside a virtual environment.", "IT", "700"),
    ("dependency management", "依存関係管理", "名詞", "Dependency management gets messy in large projects.", "IT", "800"),
    ("rate limit", "レート制限", "名詞", "We hit the API rate limit twice today.", "IT", "700"),
    ("data pipeline", "データパイプライン", "名詞", "The data pipeline runs every night at midnight.", "IT", "750"),
    ("ETL", "ETL（抽出・変換・格納）", "名詞", "The ETL job extracts data from three sources.", "IT", "850"),
    ("null value", "null値（欠損値）", "名詞", "Handle null values before running the model.", "IT", "650"),
    ("missing value", "欠損値", "名詞", "Missing values need to be imputed or dropped.", "AI", "700"),
    ("outlier", "外れ値", "名詞", "One outlier skewed the entire average.", "数学", "750"),
    ("normalization", "正規化", "名詞", "Normalization scales features to a common range.", "数学", "800"),
    ("standardization", "標準化", "名詞", "Standardization gives features a mean of zero.", "数学", "800"),
    ("experiment tracking", "実験管理・実験トラッキング", "名詞", "Experiment tracking logs every run's parameters and metrics.", "IT", "850"),
    ("model registry", "モデルレジストリ", "名詞", "We store every trained model in the model registry.", "IT", "900"),
    ("feature store", "フィーチャーストア", "名詞", "The feature store keeps features consistent across teams.", "IT", "900"),
    ("data versioning", "データバージョン管理", "名詞", "Data versioning lets us reproduce old experiments exactly.", "IT", "850"),
    ("container image", "コンテナイメージ", "名詞", "We built a container image with all the dependencies.", "IT", "750"),
    ("unit test", "単体テスト", "名詞", "Every data transformation should have a unit test.", "IT", "700"),
    ("environment variable", "環境変数", "名詞", "The API key is stored as an environment variable.", "IT", "700"),
    ("staging environment", "ステージング環境", "名詞", "We test the pipeline in a staging environment first.", "IT", "800"),
    # --- Math vocabulary ---
    ("matrix", "行列", "名詞", "We multiplied two matrices together.", "数学", "750"),
    ("feature vector", "特徴ベクトル", "名詞", "Each sample is represented as a feature vector.", "数学", "800"),
    ("dot product", "内積", "名詞", "The dot product measures how aligned two vectors are.", "数学", "850"),
    ("linear algebra", "線形代数", "名詞", "Linear algebra underlies most machine learning.", "数学", "800"),
    ("optimizer", "オプティマイザ（最適化アルゴリズム）", "名詞", "We used Adam as the optimizer for this model.", "AI", "800"),
    ("convex function", "凸関数", "名詞", "A convex function has a single global minimum.", "数学", "950"),
    ("distribution", "分布（統計）", "名詞", "The data follows a normal distribution.", "数学", "750"),
    ("variance", "分散", "名詞", "High variance means the model is unstable.", "数学", "800"),
    ("standard deviation", "標準偏差", "名詞", "The standard deviation shows how spread out the data is.", "数学", "750"),
    ("skewness", "歪度（分布の非対称性）", "名詞", "Positive skewness means a long tail to the right.", "数学", "950"),
    ("covariance", "共分散", "名詞", "Covariance shows how two variables move together.", "数学", "900"),
    ("eigenvalue", "固有値", "名詞", "We computed the eigenvalues of the matrix.", "数学", "990"),
    ("dimensionality", "次元数", "名詞", "High dimensionality makes the data harder to visualize.", "数学", "900"),
    ("sparse matrix", "疎行列", "名詞", "A sparse matrix has mostly zero entries.", "数学", "900"),
    ("dense matrix", "密行列", "名詞", "A dense matrix stores every entry explicitly.", "数学", "900"),
    ("matrix multiplication", "行列積", "名詞", "Matrix multiplication is at the core of neural network layers.", "数学", "800"),
    ("identity matrix", "単位行列", "名詞", "Multiplying by the identity matrix changes nothing.", "数学", "900"),
    ("matrix transpose", "行列の転置", "名詞", "The matrix transpose swaps rows and columns.", "数学", "900"),
    ("vector norm", "ベクトルのノルム", "名詞", "The vector norm measures its length.", "数学", "950"),
    ("orthogonal", "直交する", "形容詞", "These two vectors are orthogonal to each other.", "数学", "900"),
    ("linear regression", "線形回帰", "名詞", "Linear regression fits a straight line to the data.", "数学", "800"),
    ("logistic regression", "ロジスティック回帰", "名詞", "Logistic regression is a common baseline for classification.", "数学", "850"),
    ("differentiation", "微分", "名詞", "Differentiation gives us the slope of the function.", "数学", "850"),
    ("partial derivative", "偏微分", "名詞", "We take the partial derivative with respect to each weight.", "数学", "950"),
    ("local minimum", "局所最小値", "名詞", "The optimizer got stuck at a local minimum.", "数学", "900"),
    ("global minimum", "大域最小値", "名詞", "A convex function has only one global minimum.", "数学", "900"),
]


# --- insertion --------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_STOP = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "for", "with", "from", "by", "as", "is", "are", "was", "were", "be", "been",
    "do", "does", "did", "have", "has", "had", "will", "would", "can", "could",
    "should", "may", "might", "must", "i", "you", "he", "she", "it", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our",
    "their", "this", "that", "these", "those", "here", "there", "what", "when",
    "where", "who", "how", "why", "not", "no", "yes", "so", "up", "out", "off",
    "down", "let", "lets", "please", "thanks", "thank", "ok", "okay", "im",
    "ill", "id", "ive", "dont", "cant", "wont", "isnt", "thats", "whats",
    "very", "just", "too", "more", "some", "any", "all", "one", "two", "get",
    "got", "go", "going", "like", "want", "need", "make", "made", "take",
    "see", "now", "today", "tonight", "good", "well", "back", "about", "over",
    "into", "than", "then", "again", "really", "much", "many", "wish", "mind",
    "before", "later", "earlier", "second", "point", "way", "say",
    "saying", "sure", "understand", "following", "pick", "leave", "there",
    "left", "run", "runs", "running", "clearly", "reached", "shows", "show",
    "used", "using", "came", "comes", "means", "matter", "matters", "beat",
    "check", "checked", "did", "watch", "kicked", "trust", "freeze",
    "ran", "hit", "hits", "twice", "three", "does", "same", "everywhere",
    "night", "midnight", "nightly", "one's", "always", "start", "started",
}


def _content_words(phrases: list[tuple[str, str]]) -> set[str]:
    out: set[str] = set()
    for en, _ in phrases:
        for tok in _WORD_RE.findall(en.lower()):
            w = tok.strip("'-")
            if len(w) >= 4 and w not in _STOP:
                out.add(w)
    return out


def report_missing() -> None:
    """Print content words used in the new phrases that are not yet in `words`
    and not covered by the WORDS list above (authoring aid)."""
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
    covered = {w[0].lower() for w in WORDS}
    all_phrases = [p for lst in PHRASES_BY_SCENE.values() for p in lst]
    missing = sorted(
        w for w in _content_words(all_phrases)
        if w not in existing and w not in covered
    )
    print(f"missing content words ({len(missing)}):")
    print(", ".join(missing))


def main() -> int:
    if "--missing-words" in sys.argv:
        report_missing()
        return 0

    with db() as conn:
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }

        ph_added = ph_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1

        w_added = w_skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in w_existing:
                w_skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            w_existing.add(en.lower())
            w_added += 1

    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("totals -> phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
              "words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
