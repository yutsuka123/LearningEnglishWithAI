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

### 2. 例文ポップアップ＋再生
- [ ] 単語一覧に「例文表示」ボタン → モーダル(ポップアップ)で
      例文・日本語訳・🔊再生（例文の再生対応）

### 3. 音声のMP3化（番号管理・2声）
- [ ] 単語/フレーズ/例文を **ash(男性)** と **nova(女性)** の2声でMP3生成・保存
- [ ] ファイル名は**番号＋声**で管理（DESIGN参照）:
      `w{word_id}_{voice}.mp3` / `wex{word_id}_{voice}.mp3` /
      `p{phrase_id}_{voice}.mp3`
- [ ] 単語・フレーズ・例文を **番号(ID)で管理**（DBのidを採用、UI/ファイル名に使用）
- [ ] 一括MP3生成バッチ（既存TTSキャッシュを土台に。スクリプト or エンドポイント）
- [ ] 音声保存先の方式決定: ファイル / DB(BLOB) / 折衷（DESIGN §9.7 参照）。
      DB保存も選べるよう保存層を抽象化（番号＋声で一元管理）

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
