# CLAUDE.md

## ⚠️ .env を読む/確認するときの必須ルール（再発防止）

`.env`には`OPENAI_API_KEY`等の秘密情報に加え、**実ユーザーに紐づく認証
情報**が記載されている場合がある。内容確認のために広いgrepパターンを
使い、意図せず秘密情報の値そのものを会話ログに表示してしまう事故が
過去に起きているため、以下を徹底する（詳細な経緯は非公開の
`docs/TODO.md`参照・`docs/`は`.gitignore`対象）。

- `.env`の中身を確認・grepするときは、**秘密情報を含む行を必ず除外する**。
  - NG: `grep "^OPENAI_" .env`（`OPENAI_API_KEY`行も拾ってしまう）
  - OK: `grep -E "^OPENAI_(MODEL|QUALITY_MODEL|TTS_MODEL)" .env`
    のように**具体的なキー名を列挙**する、または
    `grep -v -iE "key|secret|password|token" .env` のように**危険な
    キーワードを含む行を明示的に除外**してから見る。
- Read ツールで`.env`全体を読むのは避ける。特定の設定値だけ確認したい
  ときは、該当行番号のみを`offset`/`limit`で指定し、秘密情報を含む行の
  範囲は読まないこと。
- 万一秘密情報を表示してしまった場合は、直ちにユーザーに報告し、
  該当する鍵・パスワードの再発行/リセットを推奨すること（内容を自分の
  応答で繰り返さない）。

## 🚫 本番VPSへの rsync で `--delete` を使うときの必須ルール（2026-08-13再発防止）

コード更新のため `/Users/ytsuka/mydata/src/LearningEnglishWithAI/` を
VPS の `~/eigo/` へ `rsync --delete` した際、ソース側に存在しない
`deploy/.env.study`（本番の`OPENAI_API_KEY`/`SESSION_SECRET`等）が
**「余分なファイル」として削除されてしまう事故**が発生した（稼働中
コンテナの環境変数から復元して事なきを得たが、コンテナ再作成のタイミング
次第では本番停止に直結しうる重大インシデントだった）。

- 本番VPSの`~/eigo/`（またはdeployディレクトリ全般）へ`rsync`する際、
  **`--delete`を使うなら`.env.study`・`.env`等の秘密情報ファイルを
  必ず`--exclude`に明示すること**（ローカルに存在しない＝gitignore対象
  だからこそVPS側にしか無く、`--delete`は問答無用で消してしまう）。
  可能なら`--delete`自体を避け、追加のみの同期にする。
- rsyncコマンドを組み立てたら、実行前に**dry-run(`--dry-run`)で
  `deleting`と表示される対象を確認**してから本番に対して実行する。
- 万一削除してしまった場合、まずprivateリポジトリ`business_plan`の
  `products/study_nyangailab/secrets_backup/env.study.backup`
  （2026-08-13〜保管・下記「🔗連携している private リポジトリ」参照）を
  VPSへ配置し直すのが最短の復旧手段。バックアップが古い/無い場合のみ、
  稼働中コンテナが残っていれば`docker inspect <container> --format
  '{{range .Config.Env}}...'`で環境変数を復元できる可能性があるが、
  この種の操作は秘密情報の抜き出しにあたるためClaude Code側の安全装置
  でブロックされうる。その場合は無理に迂回せず、ユーザー自身の
  ターミナルで実行してもらう。**コンテナを再作成する前に**復旧すること
  （再作成時に`.env.study`が読めないと本番が起動しなくなる）。

## 📌 バージョン管理・リリースノート（2026-08-08〜必須ルール）

`app/config.py`の`APP_VERSION`を上げるときは、必ず次をセットで行う
（バージョンだけ上げてコミットしない、を禁止）:

1. [CHANGELOG.md](CHANGELOG.md) に新バージョンの見出しを追加し、
   修正内容・機能追加の概要を箇条書きで記録する。
2. その場で `git add` → `git commit` → `git push` まで行う
   （コミットメッセージにバージョン文字列を含めるか、直後に
   バージョンだけの軽いコミットを作ってもよい）。
3. コミットが完了したら、そのコミットハッシュを分かる範囲で
   CHANGELOG.mdの当該エントリに追記する（次回セッションで参照しやすく
   するため）。

## 🔒 個人情報・インフラ接続情報を公開リポジトリに書かないルール（2026-08-09強化）

`deploy/DEPLOY_RUNBOOK.md`に本番VPSの実IPアドレスが2026-06-16の作成時から
**2ヶ月近く平文のまま公開GitHubリポジトリに残り続けていた**事故が発覚し
（`git-filter-repo`で履歴含め削除・詳細はTODO_OLD.md「公開リポジトリの
機密情報パージ」参照）、既存ルール（README.md・SESSION_HANDOFF.md限定の
記述）では**deployディレクトリ等の新規ファイルを見落とす**ことが判明した
ため、対象を明確化する。

- 個人情報・インフラ接続情報（VPSのIP/ホスト名、SSH鍵のパス、実ユーザー名・
  利用データ、DB接続文字列等）は`docs/`（`.gitignore`対象）または非公開の
  `business_plan`リポジトリにのみ記載し、**git管理下の"全"ファイル**
  （README.md・SESSION_HANDOFF.md・`deploy/`配下含む、特定ファイルに限らず
  新規作成するファイルも同様）には書かない。実IP/実パスが必要な手順書は
  `<VPS_IP>`のようなプレースホルダーで書く。
- **許可される書き方＝参照ポインタのみ**: 「詳細は非公開の`docs/TODO.md`
  （またはprivateな`business_plan`リポジトリ）を参照」という**文言だけ**を
  公開ファイルに残すのはOK（参照先の場所を示す文字列自体には秘密情報が
  含まれないため）。ただしこれは**参照先が実際に非公開である場合のみ有効**
  （`docs/`は`.gitignore`確認済み。`business_plan`等の外部リポジトリを
  参照先にする場合は、都度そのリポジトリが本当にprivateか確認すること）。
- **新しいファイルをgit管理下に追加・コミットする前**（特に`deploy/`・
  運用手順書・READMEなど）は、実IP・実ホスト名・実パス・実名等が紛れ込んで
  いないか一呼吸おいて確認する。「後で直す」を前提にしない（今回のように
  直されないまま長期間残るリスクがある）。
- 万一すでに公開コミットしてしまった場合は、現在のファイル内容をまず
  プレースホルダーに置換して通常コミット→pushし（即時の生の漏洩を止める）、
  その上で履歴からの削除が必要か（`git-filter-repo`等・破壊的操作なので
  必ずユーザー確認の上で）を別途検討する。

## 🔗 連携している private リポジトリ（business_plan・2026-08-09〜）

このプロジェクト（`LearningEnglishWithAI`・public）は、事業戦略・インフラ
バックアップ用に以下のprivateリポジトリと連携している。

- **場所**: ローカル `/Users/ytsuka/mydata/project/private/business_plan`
  ／GitHub `yutsuka123/business_plan`（private確認済み・公開APIで404）。
- **本プロジェクト用フォルダ**: `products/study_nyangailab/`
  - `README.md`: 事業サマリ（詳細はこちら側の`docs/`参照という設計）。
  - `運用リファレンス.md`: 本番VPSのIP/SSH鍵パス/デプロイ手順の**バックアップ
    コピー**（`docs/TODO.md`の「🔧 運用リファレンス」がgit管理外＝
    このマシンにしかバックアップが無いため2026-08-09に開始）。
    **`docs/TODO.md`側を更新したら、このファイルも都度同期すること**。
  - `secrets_backup/`（**2026-08-13〜**）: 本番VPS用SSH鍵ペアと
    `deploy/.env.study`（`OPENAI_API_KEY`/`SESSION_SECRET`等の実値）の
    バックアップ。rsync --deleteがVPS専用の`.env.study`を誤削除する
    事故（下記ルール参照）を機に、VPS/作業機のどちらか一方が失われても
    復旧できるよう追加した。**このリポジトリ側（LearningEnglishWithAI）
    には実値は一切置かない**（本項目の通りbusiness_plan側のみに保管）。
    値を更新したら都度手動で同期すること（詳細・復元手順は
    `products/study_nyangailab/secrets_backup/README.md`参照）。

## その他

- 新しいセッションを始めるときは、まず [docs/DESIGN.md](docs/DESIGN.md)
  と [docs/TODO.md](docs/TODO.md) を読む。
