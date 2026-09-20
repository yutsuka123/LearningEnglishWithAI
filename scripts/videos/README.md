# 機能紹介動画・ポスターの生成パイプライン

未登録トップページの「機能紹介動画ギャラリー」用の **動画(mp4)とポスター画像(jpg)** を、
実際のアプリを撮影して作る。**アプリの見た目が変わったら、1コマンドで撮り直せる**ことが目的。
本番・本体の `data/` には一切触れない(一時ディレクトリで完結)。

```
static/video/<name>.mp4               # 動画(H.264 + AAC・faststart・≦2.5MB・15〜20秒・縦9:16 720x1280)
                                      #   現在: flash_word(フラッシュ単語)/ phrase_polite(そっけない“No.”を上品に)/ crossword(クロスワード)
static/video/posters/<name>.jpg       # ポスター(≦60KB・縦9:16 540x960)
scripts/videos/storyboards/<name>.md  # 台本(秒単位の流れ・字幕全文・事実の裏付け)
```

## 使い方(リポジトリのルートから)

```bash
.venv/bin/python scripts/videos/build.py --list                  # 動画の一覧
.venv/bin/python scripts/videos/build.py                         # 全本を作り直す
.venv/bin/python scripts/videos/build.py --only phrase_polite    # 1本だけ
.venv/bin/python scripts/videos/build.py --only phrase_polite --poster-only   # ポスターだけ(数十秒)
.venv/bin/python scripts/videos/build.py --only phrase_polite --frames-dir /tmp/frames
    # ↑ 完成mp4から1秒おきのPNGを書き出す(目視確認用)
```

1コマンドの中身: ①一時DATA_DIR+アプリ起動 ②撮影 ③音の合成とエンコード ④ポスター生成
⑤検証(ffprobeで尺・サイズ・コーデック・faststart、ラウドネス、ポスター容量)。
検証に落ちると終了コード1と理由を表示する。所要は1本あたり1分弱。

### 前提

- `.venv` に `playwright`(+ `playwright install chromium`)と `fastapi`/`uvicorn` などアプリの依存
  (`requirements.txt` には入れていない=本番イメージに不要な開発用ツールのため)。
- `ffmpeg`(libx264・aac が使えるもの。drawtext/libass/libwebp は不要)。
- 本体のローカルDB `data/content.db`(語彙・フレーズ)と実音声 `data/audio/*.mp3`
  (`AppServer` が親ディレクトリをたどって探す。場所が違えば環境変数
  `VIDEO_SRC_DATA_DIR`。仮想環境のPythonは `VIDEO_PYTHON` で指定可)。いずれも **読み取り専用**。
- 実IP・鍵・個人情報・`.env` は使わない/書かない(公開リポジトリに入るため)。

## 仕組み

| 部品 | 役割 |
|---|---|
| `lib/appserver.py` | 一時DATA_DIR(`content.db`はsqlite backup APIで読み取り複製、`audio`は本体へのsymlink、`core.db`/`logs.db`は空=ユーザー0人)で `uvicorn` を空きポート(8790〜)に起動。`MULTIUSER=1`・`ALLOW_FRESH_DB=1`・ダミーのAPIキー・外部通信遮断。 |
| `lib/stage.py` | 撮影用ステージ。アプリを **iframe(390x585)** に入れ、下に字幕帯(108px)を確保。字幕・タップ表示(円)・「🔊 AI音声」バッジ・エンドカードを **DOMオーバーレイ** として描画して一緒に録画(ffmpegに drawtext が無いため)。録画は CDP `Page.startScreencast`(JPEG・DSF=2)。 |
| `lib/encode.py` | フレーム列(タイムスタンプ付き)→ 30fps・yuv420p(limited/BT.709)・H.264 High。音声イベント→ ffmpeg で `adelay`/`amix`→ `loudnorm` 2パス(-16 LUFS)→ AAC 44.1kHz モノラル。 |
| `lib/poster.py` | HTMLテンプレを Playwright でスクリーンショット→ JPEG。上限(56KB)に収まる最大品質を探索。 |
| `lib/verify.py` | ffprobe・faststart(moov位置)・ラウドネス(ebur128)・無音検出・フレーム書き出し。 |
| `lib/content.py` | 撮影対象が **ゲスト無料範囲内**(`app/services/access_tiers.py` の関数をそのまま使用)・詳細あり・男声/女声の保存音声が8KB以上、であることの事前確認。外れていれば撮影前に失敗する。 |
| `scenarios/<name>.py` | 1本ごとの台本コード: `NAME`/`TITLE`/`DURATION`、`prepare()`(画面を撮影開始の状態へ・ポスター用の実画面クロップ)、`perform()`(録画中のタイムライン)、`poster_body()`/`POSTER_CSS`。任意で `HIDE`(隠す要素の一覧。既定は `DEFAULT_HIDE`)と `EXTRA_CSS`(撮影側で足す余白調整などのCSS)。 |

`Stage`(`lib/stage.py`)の操作: `tap(selector)`(円を出してから本物のタッチタップ)/ `swipe(selector, dx, dy)`
(CDPのタッチイベントで指を動かす・指の円が付いて動く)/ `type_text(selector, text)`(1文字ずつ入力)/
`scroll(top, ms, selector)`(easeInOutでゆっくり)/ `caption(html, t_in, t_out)` / `end_card(html, t_in)` /
`mark(js, name)`(要素に `data-vid` を付けて後で指す)/ `at(t)`(動画のt秒まで待つ)。

### 音と映像の同期

Playwright は音を録れない。ページ内で `HTMLMediaElement.play` をフックし、**アプリが実際に取得して鳴らした
mp3のバイト列・開始時刻(`playing`イベント)・再生速度・停止位置**を記録して、後から映像の時刻に置く
(声・速度の取り違えが起きない。男声は本番と同じく1.15倍速で再生される)。
スクリーンキャストのフレームのタイムスタンプとページの `Date.now()` は同じ壁時計なので、
1フレーム(33ms)以内で合う(赤/緑/青の全画面を1/2/3秒に出す実測: 検出時刻 1.00/2.00/3.00秒)。
「タップ→音」の遅れはビルドのログに出る(0.15秒以内が目標)。

### 音量

`loudnorm` の2パス(-16 LUFS・TP -1.5)。単語1語だけの短い音声などピークが高くて目標に届かない
ときは、軽いコンプレッサ+ゲイン+リミッタで合わせ直す(`lib/encode.py`)。結果は
ビルドのログと `lib/verify.py`(許容 -19〜-13 LUFS・True Peak -0.5dBFS以下)で確認する。

### 撮影側で隠しているもの(アプリ本体は変更しない)

iframe内にCSSを足して次を隠している(`lib/stage.py` の `DEFAULT_HIDE`): 「残り0pt」・ⓘ・「AI未設定」・
バージョン表記・文字サイズ選択・入力モード・メンテナンス予告・トースト。動画ごとに `HIDE` で
上書きできる(例: クロスワードは「正解！」トーストを映すため `#toast` を外し、錠前に見える
「🔓 答えを見る」系を足して隠している)。
`OPENAI_API_KEY` は空だと画面に「⚠️ AI未設定」が出て、しかも音がブラウザ合成音になり本番と食い違うため、
**本物ではないダミー値**を渡している(保存済みmp3を返すだけで、外部通信は遮断・実キーは使わない)。

## ギャラリーへの登録

トップページの動画ギャラリーは `static/js/video-gallery.js` の `VIDEOS` 配列を読む(表示順=配列順)。
動画を足す・撮り直したら、`src` と `poster` の `?v=` を上げる(`/static/video/` は1年キャッシュ・immutable)。
`sound` は、動画に音が入っている(=「🔊 音が流れます」を出す)ときだけ `true`。

## 新しい動画を足す

1. `scenarios/<name>.py` を `phrase_polite.py` にならって作る(`prepare`/`perform`/`poster_body`)。
   語やフレーズは `lib/content.py` の関数で「ゲスト無料範囲内+音声保存済み」を確認する。
2. `build.py` の `SCENARIOS` に名前を足す。
3. `storyboards/<name>.md` に秒単位の台本・字幕全文・事実の裏付けを書く。
4. `build.py --only <name> --frames-dir <dir>` でビルドし、**書き出したPNGを目で見て**確認する
   (字幕が読める・崩れていない・点滅/急な動きがない・🔒や開発用警告が映っていない)。

## 字幕・表記のルール

- 事実に裏付けがあるものだけ書く。「AIの自然な英語音声」と書き、「ネイティブ音声」とは書かない。
- 料金・無料範囲を断定するなら実装で確認する(`app/services/access_tiers.py`)。
- 点滅・急なズーム・高速カットをしない。字幕とエンドカードはゆっくりフェード。
- BGM・効果音は入れない(権利と好みの面)。
