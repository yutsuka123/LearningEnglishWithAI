# English Learning with AI

TOEIC 向けの英語学習支援アプリ。**Windows / macOS 両対応**。
単語・フレーズ・会話・リスニング・リーディング・ライティング・ニュース・文学を
総合的に学習し、習熟度・忘却曲線・学習履歴を**自作システム側で永続化**します。
ChatGPT（OpenAI API）は教材生成・添削・会話に使いますが、**APIキーが無くても
起動・ローカル学習は可能**です。

> 設計・要件・進捗は [docs/DESIGN.md](docs/DESIGN.md) と
> [docs/TODO.md](docs/TODO.md) にまとまっています（セッションをまたいで再開可能）。

## 主な機能

- 単語 / ミニフレーズを **両方向（英→日・日→英）** で出題、習熟度・正答率を管理
- **忘却曲線（SRS）** で復習タイミングを自動調整（覚えた語も時々再登場）
- 1回 **約10分**のデイリーセッション（単語10・フレーズ10・読・書）
- 音声入力（読み上げ認識）／音声出力（読み上げ）— 入力は**音声/文字をトグル**
- 会話はストリーミング応答。**音声コマンドで操作**（画面移動・設定保存など）
- **API使用量・推定費用**を表示
- `memory.md` / `study_log.md` / `vocabulary.db` に学習状態を永続化

## セットアップ

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS:   source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env     # 任意: OPENAI_API_KEY を設定（無くても可）

python run.py            # http://127.0.0.1:8000 が自動で開きます
```

停止は `Ctrl+C`。データは `data/` 配下に保存されます（git管理外）。

## 注意

- 音声認識はブラウザの Web Speech API を使用します（Chrome 推奨、要ネット接続）。
- APIキーは設定画面または `.env` で後から登録できます。
