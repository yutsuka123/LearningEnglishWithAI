# 英語学習支援システム 設計書

> このドキュメントは「セッション（会話）が変わっても開発を再開できる」ことを
> 目的に、要件・設計・進捗を1か所にまとめたものです。新しいセッションを始める
> ときは、まずこのファイルと [TODO.md](TODO.md) を読んでください。

最終更新: 2026-06-14

---

## 1. 目的

英語学習を**長期間継続**できる仕組みを作る。OpenAI API（ChatGPT）を使うが、
学習履歴・進捗・習熟度は**自作システム側で永続化**し、チャット履歴に依存せず
いつでも学習状態を再現できるようにする。

## 2. 学習者プロフィール

- 現在レベル: TOEIC 550〜600
- 短期目標: TOEIC 700
- 最終目標: TOEIC 800 以上
- 学習スタイル: 単語 / 会話 / リスニング / リーディング / ライティングを総合的に

## 3. 技術スタック（決定事項）

| 項目 | 採用 | 理由 |
|------|------|------|
| 言語/実行 | Python 3.11+（本機は 3.14） | 追加環境が最小。Win/Mac 両対応 |
| バックエンド | FastAPI + Uvicorn | 軽量・高速・型安全 |
| DB | SQLite（標準ライブラリ sqlite3） | ネイティブビルド不要で両OS同一動作 |
| フロント | 素の HTML/CSS/JS（SPA） | 依存最小・起動が速い |
| 音声入力 | ブラウザ Web Speech API（SpeechRecognition） | 無料・OS非依存 |
| 音声出力 | ブラウザ SpeechSynthesis（TTS） | 無料・OS非依存 |
| AI | OpenAI Python SDK（任意・キー未設定でも起動） | 要件どおり |

**クロスプラットフォーム方針**: パスは必ず `pathlib` 経由（`app/config.py` の
`paths`）。OS依存のコマンドやパス区切りを直書きしない。`python run.py` で起動し
ブラウザが自動で開く。

## 4. アーキテクチャ

```
run.py                      # 起動ランチャ（サーバ起動＋ブラウザを開く）
app/
  config.py                 # 設定・パス（DATA_DIR, .env 読み込み）
  database.py               # SQLite スキーマ・接続・シード
  seed_data.py              # 初期コンテンツ（単語 約100 / フレーズ 約50）
  schemas.py                # Pydantic 入出力モデル
  main.py                   # FastAPI 本体（ルータ登録・起動処理・静的配信）
  routers/
    vocabulary.py           # 単語 CRUD / クイズ / 採点 / 統計
    phrases.py              # フレーズ CRUD / クイズ / 採点
    categories.py           # 会話・読・書・文学カテゴリ + リスニング
    learn.py                # AI教材生成 / 会話(ストリーム) / 添削 /
                            #   デイリー / セッション要約・保存 / 音声コマンド
    system.py               # 設定 / APIキー / 使用量・費用 / memory / 履歴 / 分類
  services/
    spaced_repetition.py    # 習熟度・両方向採点・忘却曲線(SRS)・月次減衰
    persistence.py          # memory.md / study_log.md 読み書き
    ai.py                   # OpenAI ラッパ + 使用量/費用記録（キー無しは安全に失敗）
    context_builder.py      # AIへ渡す最小コンテキスト生成
static/                     # フロント（index.html, css, js）
data/                       # 実行時データ（gitignore）: vocabulary.db, memory.md,
                            #   study_log.md
docs/                       # 本設計書・TODO
```

## 5. データモデル（SQLite）

- `words` — 単語。`english, japanese, part_of_speech, example, mastery(0-100),`
  `times_asked, times_correct,` 方向別カウンタ `ask_/ok_ (en2ja, ja2en),`
  `review_level, next_review, last_studied`
- `word_attempts` — 1回ごとの解答ログ（両方向ボーナス判定用）
- `phrases` — フレーズ。words と同じ列構成（両方向・忘却曲線対応）
- `phrase_attempts` — フレーズの解答ログ
- `categories` — 会話/読/書/文学のカテゴリ別習熟度（area, grp, name, mastery）
- `listening_topics` — ソース×アクセント別の理解度・苦手
- `materials` — AI生成教材（news/reading/literature 等）
- `study_sessions` — 1セッション=1行の学習履歴
- `ai_usage` — API呼び出しごとのトークン数と推定費用（USD）
- `app_state` — 月次減衰の記録・両方向ボーナス済みフラグ等

## 6. 学習ロジック（要件の数式を実装）

- 習熟度は 0〜100、初期 0。
- **両方向（日→英 / 英→日）正解**でその日に **+5**（上限100）。1日1回まで。
- 出題優先度 = `100 - 習熟度`（低いほど出やすい）。
- **忘却曲線（SRS, Leitner式）**: 正解で次回間隔を延長、不正解で初期化。
  間隔 `REVIEW_INTERVALS = [1,2,4,8,16,35,70,150]` 日。`next_review` が
  期限到来した項目を優先出題 → 覚えた語も**時々復習**として再登場。
- **月次減衰**: 月が変わると全単語・全フレーズの習熟度 -5（下限0）。起動時に判定。
- 単語・フレーズとも **習熟度・正答率を方向別に管理**。
- デイリーは **1回あたり単語10・フレーズ10まで**（約10分想定）。

## 7. AIへの入力（§13）

毎回チャット履歴全体は渡さず、`context_builder.build_context()` が以下を生成:
現在レベル・目標・苦手（memory.md）／今日の復習対象（低習熟度語）／最近の学習履歴
（study_sessions 数件）。

## 8. 学習終了時（§14）

AIが「学習結果 / 新出単語 / 苦手ポイント / 次回課題 / memory更新案 /
study_log更新案」を Markdown 出力。`/api/learn/session/save` で
`study_sessions` に保存し、`study_log.md` に追記。

## 9. ユーザー要望（この設計に反映済み / 反映予定）

- 入力方式トグル: クイズ/リーディング/ライティングで**音声 or 文字**を選択。
- **API使用量・費用の表示**（`ai_usage` 集計 → `/api/system/usage`）。
- 応答性向上: 会話はストリーミング（`/api/learn/conversation/stream`）。
  既定モデルは高速な `gpt-4o-mini`。
- **会話駆動の操作**: 学習だけでなく設定保存・画面移動なども音声/自然言語で。
  `/api/learn/command` が意図(JSON)に変換（キー無し時はキーワード判定で代替）。
- 毎回 約10分: 単語 / ミニフレーズ / リーディング / ライティング(音声応答可)。
- **AIの読み上げ声**: 学習回ごとにランダムで変化し、声の名前を画面表示。
  設定画面で使う声を個別にON/OFF（有効な声からランダム選択）。実装は
  `static/js/speech.js`（localStorage に有効な声名を保存）。
- 幅広いトピック: 日常 / 映画 / ニュース(政治・経済・エンタメ・軍事・各国…) /
  米英アクセント / 歴史 / 外国人対応(道案内・聞き返し等) / IT・開発 / 機械 /
  AI用語 / AIへの指示 / 出入国 / レストラン / ホテル / スーパー / ご近所 /
  TOEIC 500-800 / 留学 など。会話カテゴリとフレーズ集に反映。

## 9.5 プライバシー方針（重要）

- **個人名・個人情報・機密情報を git 管理ファイルに書かない**。
- 個人情報（APIキー、ニックネーム等）は `.env` のみに置く（git管理外）。
  - `USER_NICKNAME` … AIの呼びかけ名。未設定なら匿名。
  - `OPENAI_API_KEY` … APIキー。
- 学習データ（`data/` の DB・memory.md・study_log.md）も git 管理外。
- 新しいシード文・サンプルに実在の個人名を入れない（プレースホルダを使う）。

## 9.7 音声・番号管理 / 禁止用語（次セッション実装の設計メモ）

**番号(ID)管理**: 単語=`words.id`、フレーズ=`phrases.id`（既存のautoincrement）
を正準IDとし、UI表示・音声ファイル名に使う。例文は親(単語/フレーズ)IDに紐づく。

**MP3化（2声・番号＋声で命名）**: 既存のTTSディスクキャッシュ
（`data/tts_cache/`、内容ハッシュ名）に加え、決定的な名前で `data/audio/` に保存:
- 単語: `w{id}_ash.mp3` / `w{id}_nova.mp3`
- 単語の例文: `wex{id}_ash.mp3` / `wex{id}_nova.mp3`
- フレーズ: `p{id}_ash.mp3` / `p{id}_nova.mp3`
- 声は **ash(男性)** と **nova(女性)** の2種を保存。
- 生成は `ai.synthesize_speech(text, voice)`（キャッシュ済み）を流用し、
  生成済みをID命名でコピー/保存するバッチ（スクリプト or `/api/...`）。
- 再生は保存済みMP3を返す静的配信にすれば**API課金ゼロ**（将来オフライン化）。

**例文ポップアップ**: 一覧の「例文」ボタン→モーダルで 例文/訳/🔊再生。

**分野フィルタ/ソート**: `/api/words?domain=&level=&sort=` を追加。

**禁止用語**: `words`/`phrases` に `banned INTEGER DEFAULT 0`（または
`domain='禁止用語'`）。`app_state` か設定で次のトグル（既定OFF）:
- `banned_test`（クイズ・デイリーに含めるか）
- `banned_show`（一覧に表示するか）
選択肢で抽出/表示から除外。目的は**映画理解・注意喚起・誤用防止**であり、
露骨すぎる例文は避け、意味と「使ってはいけない理由」を中心に扱う。

## 10. 将来拡張（要件§15）

Google Drive 連携 / GitHub 連携 / スマホ対応 / TOEIC 模擬試験生成 /
ロールプレイ強化。memory.md・study_log.md は Markdown なので同期しやすい。

## 11. 起動方法

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   /  macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # OPENAI_API_KEY を入れる（無くても起動可）
python run.py               # http://127.0.0.1:8000 が自動で開く
```
