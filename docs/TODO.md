# 開発 TODO / 進捗

> 新しいセッションを始めたら、まず [DESIGN.md](DESIGN.md) と本ファイルを読む。
> 完了したら `[x]` に更新する。最終更新: 2026-06-14

## 完了 ✅

- [x] プロジェクト雛形（requirements / .gitignore / .env.example / config / run.py）
- [x] SQLite スキーマ・接続・シード（categories / listening / words / phrases）
- [x] 習熟度ロジック（両方向 +5・出題優先度 100-習熟度）
- [x] 忘却曲線 SRS（review_level / next_review / due 優先選択）
- [x] 月次減衰（単語・フレーズ -5）
- [x] memory.md / study_log.md の読み書き
- [x] AI ラッパ（キー未設定でも起動）＋ ストリーミング会話
- [x] API 使用量・費用の記録と集計（ai_usage / /api/system/usage）
- [x] AIコンテキスト生成（最小情報のみ）
- [x] ルータ: vocabulary / phrases / categories / listening / learn / system
- [x] デイリーセッション（単語10・フレーズ10）API
- [x] 音声/自然言語コマンド解釈 API（/api/learn/command）
- [x] 初期コンテンツ: 単語 約100 / フレーズ 約50（seed_data.py）
- [x] 設計書・TODO（docs/）
- [x] プライバシー方針（個人情報は .env のみ / git管理ファイルに書かない）
- [x] **フロントエンド** static/index.html, css/style.css, js/{api,speech,quiz,
      app,views}.js
  - [x] タブUI: ダッシュボード / デイリー / 単語 / フレーズ / 読 / 書 / 会話 /
        リスニング / ニュース / 文学 / 学習履歴 / 設定
  - [x] **音声/文字 入力トグル**（クイズ・読・書・会話）
  - [x] 単語・フレーズの**両方向クイズ**（英→日 / 日→英）＋自動判定＋手動修正
  - [x] **デイリー10分セッション**（単語→フレーズ→読→書）ウィザード
  - [x] 音声入力(SpeechRecognition)・音声出力(SpeechSynthesis)
  - [x] **API使用量・費用**の常時表示（topbar + 設定 + ダッシュボード）
  - [x] **会話駆動操作**（🎙️操作ボタンで画面移動・入力モード・モデル変更等）
  - [x] セッション終了→AI要約→memory/study_log 更新案の保存
  - [x] **AIの声**: 学習回ごとにランダム、声名を表示、設定で声をON/OFF
- [x] 動作確認（起動・全エンドポイントのスモークテスト）
- [x] README に使い方を記載

## 既知の制約 / 次に検討

- [ ] ブラウザでの実機UI確認（本環境にJS実行系が無いため未確認。Chrome推奨）
- [ ] リーディングの設問採点をより丁寧に（現状はAI生成教材の表示＋読み上げ）
- [ ] Win/Mac 実機での `python run.py` 起動確認

## バックログ（将来拡張・要件§15）

- [ ] Google Drive 連携（memory.md / study_log.md / DB の同期）
- [ ] GitHub 連携
- [ ] スマホ対応（レスポンシブ / PWA）
- [ ] TOEIC 模擬試験生成
- [ ] 英会話ロールプレイ強化（シナリオ・採点）
- [ ] リスニング素材の自動取得（YouTube/ニュース）
- [ ] 単語・フレーズの自動追加（学習者レベルに応じてAIが補充）

## メモ / 設計判断

- 行長 79 文字制限の linter が有効（IDE）。新規コードはなるべく短く。
  プロジェクト方針は 88 文字（pyproject.toml）。
- AIキー無しでも全機能の「ローカル部分」は動く。AI部分は明示メッセージで代替。
- 既定モデル `gpt-4o-mini`（高速・安価）。設定で変更可。費用表は ai.py の PRICING。
