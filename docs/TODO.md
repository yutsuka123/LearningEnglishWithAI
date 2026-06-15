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
- [x] 英会話: シーン/自由会話モード、ストリーミング、🔁声変更、💡返答例、
      🌐日本語訳ボタン、英語のみ読み上げ、コーチ【例】＋添削例の読み上げ
- [x] 自由会話チューター（日本語OK・なんでも対応）＋会話ログを判定に反映
- [x] 音声入力: ON/OFFトグル録音、強制中止、Whisper自動文字起こし(言語自動判定)
- [x] クイズ: 正解/うろ覚え/不正解/ノーカウント/わからない、和英・英和を分離
- [x] 判定・教材タブ（AI判定＋単語/フレーズ生成）／品質モデル設定
      (OPENAI_QUALITY_MODEL)
- [x] 費用の日本円換算（USD_JPY_RATE, 週1見直し）
- [x] 単語の一括インポート（AIで訳精査＋例文生成・重複スキップ）
- [x] 単語 約100→約1108語に拡充（TOEIC 600/700/800 + 各分野）
- [x] 単語に level / domain 列＋一覧表示、🔊再生ボタン、TTSディスクキャッシュ
- [x] 既存全語の domain/level をAI自動分類（/api/words/retag）

## コンテンツ現状サマリ（2026-06-14 時点）

- 単語 **2332** / フレーズ **1056**。すべて例文付き（例文なし=0）。
- レベル: 300/400/500/600/700/800/900/990/990+/範囲外（細スケール）。
  範囲外=禁止用語44のみ。990+=専門ジャーゴン。詳細は §5h。
- 分野(domain)・シーン(scene)で大量に分類。禁止用語は既定で非表示・非出題
  （設定の🔞トグルで表示/出題可。§5）。
- **データ追加は全て本チャットのAI(私)が作成し、アプリのOpenAI APIは未使用。**
  投入は `scripts/add_*.py`（DB直接INSERT・重複はenglish小文字でスキップ）。
  再レベリングは `scripts/relevel.py`（冪等）。DB(`data/`)はgit管理外のため
  各セッションでローカル保持される（コードのみコミット）。
- 追加スクリプト一覧（実行順の目安）: add_phrases → add_banned → add_danger
  → add_technical → add_examples_rail → add_genres → add_more → add_names
  → add_mst → add_genres2 → relevel → add_fixes。

## 実装済み拡張（2026-06-14・ユーザー依頼分）

### 1. 単語一覧の分野別ソート・フィルタ ✅
- [x] 分野(domain)・レベル(level)でフィルタ、並び替えセレクト（UI）
      ＋キーワード検索（英語/日本語）
- [x] バックエンド `/api/words` に `domain`/`level`/`sort` クエリ追加、
      `/api/words/facets`（分野・レベル一覧）を追加
- [x] フレーズ集にもフィルタ(シーン)・並び替え・検索を実装、
      `/api/phrases` に `sort` 追加

### 1b. 2声(男声ash=青 / 女声nova=赤)の再生ボタン ✅
- [x] 単語・フレーズ一覧の再生を**男声(ash・青)/女声(nova・赤)**の2ボタンに
- [x] `speech.sayWithVoice(text, voice)` を追加（既存TTSキャッシュを利用、
      自然な声OFF/失敗時はブラウザ音声にフォールバック）
- 備考: 事前MP3バッチ生成・番号付きファイル管理（#3）は未着手。今回は
  再生時に声を指定する方式（キャッシュ済みなら2回目以降は無料）。

### 2. 例文ポップアップ＋再生 ✅ 2026-06-15
- [x] 単語一覧に「📄 例文」ボタン → モーダル(ポップアップ)で
      英語・日本語訳・例文・🔊再生(男声ash/女声nova)。例文が無ければ
      「📝 例文を作る(AI)」で生成（コストガード下）。`showWordExample()`。

### 3. 音声のMP3化（番号管理・2声）✅ 2026-06-15（オンデマンド方式）
- [x] **番号(ID)＋声で一元管理**。エンドポイント
      `GET /api/learn/tts/item?item_type=word|phrase&item_id=&kind=word|
      example|phrase&voice=ash|nova`。保存済みなら即返す(=無料)、無ければ
      合成して保存し**次回からトークン不要**（ユーザー要望の「再生のたびに
      保存→以後無料」をそのまま実装。一括事前生成はコスト面で見送り）。
- [x] 保存層を抽象化 `app/services/audio_store.py`（`AUDIO_STORAGE`=
      file|db|hybrid、既定 file）。file は `data/audio/{type}{id}_{kind}_
      {voice}.mp3`、db は `audio_blobs` テーブル(BLOB)。番号＋声で一元管理。
- [x] 単語/フレーズ一覧・例文ポップアップの再生をこのID方式に切替。
      フロントは `speech.sayItem(type,id,kind,voice,fallback)`。
- [ ] （任意）一括MP3生成バッチ＝意図的に未実装。暴走・高額化を避けるため
      「再生時にだけ生成・保存」する遅延方式を採用。

### 6. 習熟度の「覚えた」＋コスト暴走ガード ✅ 2026-06-15
- [x] mastery 上限を **0..200** に拡張。「✅覚えた」ボタンで満点200に
      （`POST /api/{words|phrases}/{id}/known`）。クイズ判定・一覧・各行に設置。
      mastery>=100 を「覚えた」とみなし、一覧で **覚えた: 含む/隠す/のみ**
      フィルタ（`mastered` クエリ）。出題重みは `100 - mastery`（覚えた=最小1）。
- [x] 忘却曲線の減衰を **週 -1**（旧: 月-5）に変更。`apply_weekly_decay`
      （経過週数ぶんまとめて減算・端数日保持、`last_decay_date`管理）。
      覚えた(200)は約100週で100を割るまで保持。
- [x] **AIコスト暴走ガード**（`app/services/ai.py` `_guard`）: 1日の費用上限
      `AI_DAILY_COST_CAP_USD`(既定$1.0)超過で停止、`AI_MAX_CALLS_PER_MIN`
      (既定20)で短時間集中を遮断、`AI_MAX_OUTPUT_TOKENS`(既定1500)で
      max_tokens を上限クランプ。chat/stream/TTS/STT すべてに適用。TTSは
      キャッシュ命中なら無課金で素通り。費用は**ローカル日**基準で集計し、
      topbar の 💰 バッジに上限・停止状態を表示。

### 9. 音声DBを少しずつ拡充（継続タスク）🔁 2026-06-15〜
`scripts/build_audio.py`（番号+声で `audio_store` に事前生成・保存。保存済みは
スキップし「次の未生成分」だけ作るので何度でも安全に再実行できる。再生時の
オンデマンド保存とも共存）。
- 既定は **単語+50 / フレーズ+50**（2声 ash+nova）。**毎セッション続きを実行**:
  `python scripts/build_audio.py`（声を絞るなら `--voices ash`）。
- 1日コスト上限(AI_DAILY_COST_CAP_USD)は常に有効。上限到達で中断し次回に継続。
- 例文の音声化が必要になったら kind=example 対応を足す（現状は単語見出し/
  フレーズのみ）。**例文テキストは全単語に付与済み（例文作成は不要）。**
- 初回(2026-06-15): 単語音声 +300語 / フレーズ音声 +300件（2声）を生成。

### 8. 米英の生活サバイバル英語 +100/+100 ✅ 2026-06-15
`scripts/add_living_us_uk.py`（チャットAI作成・API不使用・全語に例文）。
「とりあえず米英で生活できる」レベル。フレーズ **+102**（scene 生活・住まい14
/ 生活・銀行郵便14 / 生活・医療11 / 生活・買い物13 / 生活・交通11 /
生活・手続き会話39）、単語 **+109**（domain「生活」: 賃貸/銀行/医療/買い物/
交通/手続き＋US/UK差 petrol/gas・tap/faucet・trolley/cart・pavement/sidewalk・
postcode/zip code・chemist/drugstore 等）。合計 フレーズ **1283** / 単語
**2464**（例文なし=0）。新scene/domainはフィルタにも反映。

### 7. ニュース/慣用/電話/日常/名言フレーズ拡充 ✅ 2026-06-15
`scripts/add_news_quotes.py`（チャットAI作成・OpenAI API不使用、英語で重複
スキップ）。ニュース報道30 / ニュース定型10 / 慣用句・イディオム(新規16) /
電話10 / 日常会話(新規29) / 哲学・名言(新規29)。関連語(ニュース/哲学)も+追加。
合計フレーズ **1056→1181**（+125）/ 単語 **2332→2355**（全語に例文）。
- 備考: 慣用句・名言はDBに既存が多く、重複は自動スキップしたため一部の
  目標件数に届かず（既存と合わせれば十分な網羅）。

### 4. フレーズ集の大幅拡充（合計 約500）✅ 2026-06-14
- [x] 以下カテゴリで作成＋精査して追加（scene でタグ）。**生成はチャットAI**で
      行い、アプリのOpenAI APIは未使用。`scripts/add_phrases.py` でDB直接INSERT
      （重複は english 小文字でスキップ）。フレーズ +526（合計578）:
  - 日常会話40 / ニュース30 / 出入国・税関28 / ホテル33 /
    レストラン・カフェ33 / 両替・買い物28 / 道案内・観光30 /
    病院・病状35 / 警察・トラブル25 / 観光客対応25 / 慣用句・引用34 /
    宗教・古典20 / ビジネス37 / 家庭の会話30 / 友人の会話29 / 趣味35 /
    禁止用語（注意喚起・露骨回避）15 / その他25
- [x] 追加フレーズ中の**未登録単語を単語集へ追加**（手作りの訳・例文・
      domain・level、重複スキップ）。単語 +96（合計1204）。
      `scripts/add_phrases.py --missing-words` で未カバー語を確認可能。
- 備考: 禁止用語は scene で分離済み。テスト/表示のON/OFFトグル（#5）は未実装。

### 5. 禁止用語の扱い ✅ 2026-06-14
- [x] 単語に domain="禁止用語"、フレーズに scene="禁止用語（注意喚起）" を付与。
      `scripts/add_banned.py` で投入（罵り・スラング・差別語は伏字＋強い警告）。
      禁止フレーズ48 / 禁止単語26。差別語は伏字(n*****等)で理解・回避のみ目的。
- [x] 設定で「表示する/しない」「テスト(出題)に含める/含めない」の2トグル
      （既定: 両方OFF＝除外）。一覧・単語/フレーズのクイズ・デイリーすべてに反映。
      バックエンドは `include_banned` クエリ、フロントは localStorage
      (showBanned/testBanned)。単語/フレーズ一覧には「🔞 禁止用語も表示」も設置。
- [x] facets(分野候補)・scenes(シーン候補)からは既定で禁止を除外。
- [x] 「和製英語・誤用注意」(発音トラップ・false friend) を安全な通常シーンで
      常時表示（25件）。日本人が使いがちで危険な英語の注意喚起。
- 備考: 教育/注意喚起目的。意味＋注意〔...〕中心。

### 5b. 護身・危険英語の拡充＋名言+100 ✅ 2026-06-14
`scripts/add_danger.py`（チャットAI作成・OpenAI API不使用）。
- [x] 差別語・強い罵りを**伏字をやめ明示**（トグルOFF既定で保護）。映画把握・
      言われた時の理解・護身が目的。各エントリは警告のみ・使用例なし。
- [x] **通常表示の安全シーン**（護身のため常時表示・出題可）:
  - 緊急・護身（警察/脅し）35: Freeze! / Hands up! / Get down! / Drop the
    weapon! / This is a robbery. / Or else. など
  - 銃器・軍事25: Open fire! / Cease fire! / Take cover! / Fall back! など
  - 犯罪・事件15: robbery/ransom/hostage/bail/指名手配 等の文
  - 単語: rifle/pistol/ammunition/hostage/ransom/smuggle/ambush/casualty
    など30語（domain 軍事/法律/医療）
- [x] **非表示（禁止トグル裏）**: 薬物スラング(scene 禁止用語（薬物）10件＋
      単語) と 差別語・最強の罵り(domain 禁止用語)。明示・警告付き。
- [x] **名言・名台詞 +106**（scene 名言・名台詞）: シェイクスピア/ディケンズ/
      カエサル/リンカーン/チャーチル/アインシュタイン/孫子/映画名台詞 ほか。
- 現状計: フレーズ824 / 単語1278（禁止単語44は既定で非表示・非出題）。

### 5c. 医療(部位別症状)＋専門用語の拡充 ✅ 2026-06-14
`scripts/add_technical.py`（チャットAI作成・OpenAI API不使用）。
- [x] 病院・部位別症状フレーズ +41（scene 病院・部位別症状）:
      「この辺が痛い」「右胸/心臓のあたり/肘が痛い」「頭の前がずきずき」
      「頭全体が痛い」「もうろうとする」「胃/腸が痛い」「かゆい」「ぎっくり腰」
      「押すと痛い」「痛みが腕に広がる」など。
- [x] 臓器・部位・症状の単語（domain 医療）: heart/lung/liver/kidney/
      spleen/pancreas/gallbladder/bladder/elbow/spine/artery/numbness 等。
- [x] 化学(domain 化学)31: 硫酸/硝酸/塩酸/クエン酸/酸/アルカリ/
      水酸化ナトリウム/触媒/中和/腐食性 など。
- [x] 物理(domain 物理)32: 力学/動力学/相対性理論/核物質/核分裂/
      放射線/慣性/運動量/同位体 など。
- [x] 機械(domain 機械)31: 流体力学/フランジ/モータ/アクチュエータ/
      ソレノイド/板金/表面処理/公差/トルク/油圧/めっき など。
- [x] 電気電子(domain 電気電子)29: 基板/はんだ/抵抗器/コンデンサ/
      半導体/端子/変圧器/短絡/プリント基板 など。
- 現状計: フレーズ865 / 単語1449。分野フィルタに 化学/物理/機械/電気電子 追加。

### 5d. 技術用語に例文付与＋鉄道用語 ✅ 2026-06-14
`scripts/add_examples_rail.py`（チャットAI作成・OpenAI API不使用）。
- [x] 医療/化学/物理/機械/電気電子の単語に**自然な英語例文を付与**（空欄のみ
      補充、既存例文は保持）。171件補充＋元seedの残り2件も補い、
      **例文なしの単語=0** に。
- [x] 鉄道(domain 鉄道)語 +29: railway/track/platform/locomotive/freight/
      改札(ticket gate)/踏切(level crossing)/特急(limited express)/新幹線
      (bullet train)/車掌(conductor)/パンタグラフ/連結器/定期券 など。
- [x] 鉄道・駅フレーズ +22（scene 鉄道・駅）: 「どのホームから出ますか」
      「乗り換えはどこ」「直通電車はありますか」「ドアが閉まります」
      「優先席」など。
- 現状計: フレーズ887 / 単語1478。全単語に例文あり。

### 5e. ジャンル別用語の大量追加 ✅ 2026-06-14
`scripts/add_genres.py`（チャットAI作成・OpenAI API不使用）。全語に例文付き。
- [x] 単語 +287（10分野）: SF30 / サスペンス29 / 恋愛28 / 世界史25 /
      日本史30 / 遊び30 / 動物28 / 植物30 / 料理28 / 数学29。
  - SF: starship/alien/hyperspace/wormhole/singularity 等
  - サスペンス: alibi/motive/red herring/forensics/plot twist 等
  - 恋愛: crush/soulmate/propose/honeymoon/breakup 等
  - 世界史: empire/dynasty/renaissance/crusade/armistice 等
  - 日本史: samurai/shogun/daimyo/national isolation/restoration 等
  - 遊び: hide-and-seek/hopscotch/rock-paper-scissors/dodgeball 等
  - 動物: mammal/predator/herbivore/hibernate/venom 等
  - 植物: stem/petal/photosynthesis/deciduous/germinate 等
  - 料理: recipe/simmer/marinate/knead/garnish 等
  - 数学: equation/fraction/prime number/calculus/probability 等
- [x] 会話フレーズ +30: 恋愛15（Will you go out with me? 等）/
      料理15（Let it simmer for ten minutes. 等）。
- 現状計: フレーズ917 / 単語1765。分野フィルタに10分野を追加。

### 5f. 宗教/哲学/IT/AI指示/管理＋具体名 ✅ 2026-06-14
`scripts/add_more.py` ＋ `scripts/add_names.py`（チャットAI作成・API不使用）。
全単語に例文。宗教・哲学フレーズは引用付き。
- [x] 宗教(domain 宗教)語を大幅増（計69）: キリスト教/ユダヤ教/イスラム教/
      仏教の用語。引用フレーズを宗教別シーンで追加: キリスト教14/ユダヤ教12/
      イスラム教12/仏教12（聖書・タルムード・ハディース・法句経 等の引用）。
- [x] 哲学(domain 哲学)29語＋哲学フレーズ14（デカルト/ニーチェ/サルトル/
      ソクラテス 等の名言）。
- [x] IT(domain IT)を充実（計117）: compile/dependency/frontend/backend/
      embedded/kernel/baud rate 等。**ビルド/エラーのよくある表現35件**を
      scene「IT・ビルド/エラー」で追加（The build failed. / Null pointer
      exception. / Merge conflict / 404 / It works on my machine. 等）。
- [x] AI指示フレーズ+14（計18・scene AI指示）: 「3点で要約」「5歳児にも
      分かるように」「校正して」「順を追って」など。
- [x] 管理(domain 管理)19語＋scene「管理・進行」20: reschedule(リスケ)/
      milestone/backlog/escalate/「締め切りを延ばせますか」など。
- [x] 動物・植物の**具体名**を追加（動物83/植物73）: cat/dog/lion/bear/
      cherry blossom(サクラ)/beech(ブナ)/dandelion(タンポポ) 等。
- [x] ホテルフレーズ追加: 「トイレットペーパーを補充してください」ほか。
- 現状計: フレーズ1056 / 単語2010。

### 5g. 軍事(具体)＋船舶＋交通 ✅ 2026-06-14
`scripts/add_mst.py`（チャットAI作成・API不使用）。全語に例文。
意味衝突は別表記で回避（army division=師団／prow=船首／bow=弓）。
- [x] 軍事(domain 軍事・計70): 戦車/戦艦/駆逐艦/潜水艦/空母/巡洋艦/各種ミサイル
      (弾道・巡航)/核弾頭/自走砲/戦闘機/攻撃機/爆撃機/レーダー/ソナー/大隊/師団/
      連隊/旅団/小隊/分隊/階級(将軍・提督・大佐・少佐・大尉・中尉・軍曹)/司令室/
      戦略/戦術/特殊部隊/強襲揚陸艦/投石機/弩/弓/ガレー船/歩兵/騎兵 等。
- [x] 船舶(domain 船舶・43): ship/vessel/ferry/tanker/コンテナ船/船体/甲板/船首/
      船尾/左舷/右舷/舵/錨/帆柱/竜骨/スクリュー/灯台/救命胴衣/航海/転覆 等。
- [x] 交通(domain 交通・41): 信号機/交差点/横断歩道/歩行者/車線/ロータリー/
      陸橋/渋滞/制限速度/一方通行/Uターン/通行料/ウインカー/追い越す/譲る/
      ガードレール/中央分離帯/歩道橋/通勤 等。
- 現状計: 単語2148（全語に例文）。分野フィルタに 船舶/交通 を追加。

### 5h. レベルを細スケールへ再設定 ✅ 2026-06-14（更新）
`scripts/relevel.py`（冪等・チャットAI作成・API不使用）。
スケール: 300- / 300 / 400 / 500 / 600 / 700 / 800 / 900 / 990 / 990+ / 範囲外。
- [x] 分野ごとの基準バンド(DOMAIN_BASE)＋基礎語の下げ(LOW)＋専門語の
      900/990/990+ 振り分け。**範囲外は禁止用語44語のみ**(乱用しない)。
- [x] 例: cat=300 / lion=400 / oxygen・addition・gravity=500 / cancer=700 /
      aerodynamics=900 / calculus=990 / titration・trebuchet=990+ /
      nigger=範囲外。
- 分布: 300:2 / 400:209 / 500:179 / 600:931 / 700:516 / 800:155 / 900:56 /
      990:74 / 990+:123 / 範囲外:44。フィルタ選択肢も全バンドに対応。
- level は文字列扱いで既存処理(ソート/フィルタ/facets)は無傷。

### 5i. 新分野（航空宇宙/スポーツ/音楽/病名/法律手続き）✅ 2026-06-14
`scripts/add_genres2.py`（API不使用・全語に例文、レベルは 5h で確定）。
- [x] 航空・宇宙30: altitude/cockpit/fuselage/thrust/orbit/astronaut/reentry 等
- [x] スポーツ29: referee/coach/tournament/marathon/penalty/podium/doping 等
- [x] 音楽28: rhythm/harmony/chord/symphony/concerto/octave/ensemble 等
- [x] 病名28: cancer/diabetes/pneumonia/stroke/hypertension/dementia 等
- [x] 法律手続き26: lawsuit/plaintiff/verdict/jury/subpoena/injunction 等
- 現状計: 単語2289。分野フィルタに5分野を追加。

### 5j. 訳語見直し＋米英の違い ✅ 2026-06-14
`scripts/add_fixes.py`（API不使用）。
- [x] 多義語の訳を補完・修正（43語）: decimal=小数・10進数 / solution=溶液・
      解決(策) / current=電流(現在の・海流) / trunk=幹・(車の)トランク・(象の)鼻 /
      sentence=判決・刑／(文法の)文 / galley=ガレー船・(船内の)調理室 ほか。
- [x] 米英で異なる語を分野「米英の違い」に+43: elevator/lift・apartment/flat・
      truck/lorry・gasoline/petrol・subway/underground・fall/autumn・
      pants/trousers・check/bill・color/colour 等（つづりの違い含む・例文付き）。
- 現状計: 単語2332（全語に例文）。

## 既知の制約 / 次に検討

- [ ] ブラウザでの実機UI確認（本環境にJS実行系が無いため未確認。Chrome推奨）
- [ ] リーディングの設問採点をより丁寧に（現状はAI生成教材の表示＋読み上げ）
- [ ] Win/Mac 実機での `python run.py` 起動確認

## 🔜 マルチユーザー化 ＋ サクラVPS限定公開（次の大仕事・2026-06-15起票）

目的: 複数ユーザー対応（ユーザー別に進捗管理）。サクラVPSに限定公開
（無料版・ユーザー名＋パスワードでログイン）。

リリース方針（2026-06-15）:
- まず **α版を無料公開・知人のみ**（クローズド）。バージョン **ver.1.1.0-alpha01**。
- 将来 **有料化／事業化も検討中**（課金ガード・ユーザー別進捗が布石）。
- **ブラウザ → Android アプリ化** を検討（最短は PWA 化＝下のバックログと接続）。

### A. データ設計（DBは分けず「共有1DB＋user_id」推奨）
- [ ] **コンテンツ（共有）と進捗（ユーザー別）を分離する** のが要点。
      現状は mastery/review_level/next_review/times_* が words・phrases の
      列に直付け＝単一ユーザー設計。これを per-user テーブルへ移す:
      `user_word_progress(user_id, word_id, mastery, review_level,
      next_review, times_asked, ok_en2ja, ...)` / 同様に
      `user_phrase_progress`。words/phrases 本体は語彙・例文・音声＝全員共有
      （2,400語×人数ぶん複製しない）。attempts/study_sessions/ai_usage/
      conversation_log にも user_id を付与。
- [ ] DBを「ユーザーごとに別ファイル」にする案は非推奨: 大きなコンテンツ
      と音声を人数ぶん複製、更新の伝播も面倒。共有1DB（将来 Postgres 移行可）
      が素直。SQLite は少人数・低同時実行なら十分。
- [ ] 音声(audio_store)は id+声で共有のまま（ユーザー非依存）。

### B. 認証（無料版・ユーザー名＋パスワード）
- [ ] `users(id, username, password_hash, created_at)`。ハッシュは
      passlib/bcrypt。ログインフォーム→署名付きセッションCookie→FastAPI
      依存性で user_id を注入。限定公開なので登録は招待制 or 管理者作成。
- [ ] 簡易版なら「リバプロのBasic認証（共有1組）」で即・限定公開できるが、
      それだと進捗をユーザー別に分けられない→本格運用はアプリ内認証必須。

### C. サクラVPSデプロイ（既存 n8n+Docker と相乗り）
現状: Ubuntu 24.04 / 2GB RAM・3vCore・SSD100GB / n8n は
https://ailab.nyangailab.com/ で稼働中。
- [ ] **相乗りは可能**。本アプリは uvicorn+SQLite で軽量（~150MB）。AI処理は
      OpenAI APIに外出し＝ローカル重処理なし。2GB RAM は n8n(+Postgres)と
      合算で要注意だが小規模限定公開なら可。逼迫時は swap 追加。音声0.5GBも
      100GB SSD で余裕。Docker コンテナ化して n8n と並走が清潔。
- [ ] **ページ名の分割＝サブドメイン**が定石。例: `eigo.nyangailab.com`
      →本アプリ / `n8n.nyangailab.com`→n8n。DNSにA(orCNAME)追加＋既存の
      リバプロ（n8nの前段。nginx/Caddy/Traefik のどれか要確認）に vhost
      追加、TLSは Let's Encrypt（Caddy/Traefik は自動）。パス分割
      (`/eigo`)も可だがアプリ側で base path 対応が要りサブドメインより面倒。
- [ ] **ailab の改名**: 新サブドメイン名を決め DNS＋リバプロの server_name
      を変更。**注意**: n8n は WEBHOOK_URL / N8N_HOST / N8N_EDITOR_BASE_URL に
      ホスト名を焼き込むため、外部サービスに登録済みの Webhook URL が壊れる。
      改名時は n8n 環境変数も更新し、旧名はしばらくリダイレクト維持が安全。
- [ ] まず「リバプロが何か」を確認: `docker ps` / 80,443 を握る
      コンテナ・プロセス（traefik/caddy/nginx/nginx-proxy 等）を見て、その
      流儀で vhost を足す。
- [ ] コスト面: 音声生成をVPS側でやるとOpenAI課金もVPS側に出る。AI_DAILY_
      COST_CAP_USD 等のガードはそのまま有効活用。

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
