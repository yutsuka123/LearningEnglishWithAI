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

コード更新のため作業機のリポジトリルート（`<REPO_ROOT>/`）を
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

## 🚨 本番`vocabulary.db`をローカルのファイルで丸ごと上書きしてはいけない（2026-09-13再発防止・重大インシデント）

語彙・フレーズ追加作業の一環で、ローカルの`data/vocabulary.db`を
`rsync`で本番VPSの`~/eigo/data/vocabulary.db`へ**ファイル単位で上書き**
した。`vocabulary.db`は単語・フレーズだけでなく**本番の実ユーザー
アカウント・PayPay決済履歴・アクセスログ(landing_visits/usage_events)
等、アプリの全データを1ファイルに同居させている**設計だったため、
本番の実データがローカル開発機の(古い・テスト用の)データで丸ごと
消えてしまう事故になった(`users`が実16件→ダミー15件、
`landing_visits`が2,345件→1件、等)。ユーザーが管理画面で「ログが
リセットされたような挙動」に気づき発覚。

**復旧できた経緯**: `deploy/scheduled_deploy.sh`が直近デプロイ
(2026-09-12 17:51 JST・ver1.4.2)の直前に自動取得していたバックアップ
(`backup_vocabulary_20260912_175110.db`)がVPSに残っていたため、
これを復元した上で、上書き前のDB(退避済み)から**語彙関連テーブル
(words/phrases)のみをid突き合わせでマージ**し直して復旧した。
自動バックアップの仕組みが無ければ復旧不可能だった重大インシデント。

- **`vocabulary.db`（またはアプリの主データベースファイル）を本番へ
  `rsync`・`scp`・`docker cp`等で転送するときは、ファイル単位の上書きを
  絶対にしないこと。** 語彙・フレーズ等の「コンテンツ」だけを反映したい
  場合は、必ず対象テーブル(`words`/`phrases`等)だけを対象にした
  SQL(`ATTACH DATABASE`でのINSERT/UPDATE等、`scripts/import_details.py`
  のようなテーブル単位の投入スクリプト)で反映し、`users`/`landing_visits`
  /`usage_events`/`paypay_payments`等のライブデータを含むファイル全体を
  ローカルの値で置き換えないこと。
- **本番の主データベースファイルを書き換える操作をする前には、必ず
  その場で現在の本番ファイルを別名でバックアップしてから行うこと**
  （`scheduled_deploy.sh`経由の自動デプロイ以外の、手動でのDB操作は
  この自動バックアップの対象外なので、都度自分でバックアップを取る
  習慣が必須）。
- **本番DBに書き込む操作をしたら、直後に主要テーブルの件数
  (`users`/`landing_visits`/`usage_events`等)を必ず確認し、想定外に
  減っていないかその場でチェックすること**（今回はユーザーが気づく
  まで発覚しなかった。自分で確認していれば即座に検知できた）。
- **この事故の根本原因＝コンテンツDBとアプリ/ユーザーDBが同一ファイルに
  同居している設計そのもの**。DB分割(語彙・フレーズ等のコンテンツと、
  users/決済/ログ等のライブデータを別ファイルに分ける)を今後検討する
  こと（2026-09-13ユーザー提起・`docs/TODO.md`参照・未着手）。

## 📌 バージョン管理・リリースノート（2026-08-08〜必須ルール）

**採番は `RV.L` 形式（2026-08-21ユーザー指示で明文化）**:
- 例 `ver1.2.9` なら `R=1` `V=2` `L=9`。
- **アップのたびに末尾の `L` を +1 する。桁上がりはしない**
  （`1.2.9` の次は `1.3.0` ではなく **`1.2.10`**）。
- **`R`・`V`（上位2桁）を上げるのはユーザーから指示があったときだけ。**
  自己判断で上げない。

**`L`を上げるタイミング＝「本番デプロイ済みの状態から新たに変更するとき」
が基本（2026-08-31ユーザー指示）**:
- あるバージョンをcommit&pushしても、**まだ本番デプロイしていない間**に
  さらに修正を加える場合は、`L`を上げず**同じバージョン番号のまま**
  CHANGELOG.md/release_notes.jsonの該当バージョンのエントリに追記する
  （`app/config.py`の`APP_VERSION`も変更しない）。
- 本番デプロイが完了して初めて、次の変更で`L`を+1する。
- **例外＝大規模な変更**（大きな新機能・大規模リファクタ等）は、
  未デプロイでもバージョンを分けてよい。迷ったらユーザーに確認する。
- 目的: 「commitしたが本番には一度も出ていない番号」が乱立するのを防ぎ、
  バージョン番号とアプリ内「バージョン情報」画面が実際のデプロイ状況と
  対応するようにするため。

`app/config.py`の`APP_VERSION`を上げるときは、必ず次をセットで行う
（バージョンだけ上げてコミットしない、を禁止）:

1. [CHANGELOG.md](CHANGELOG.md) に新バージョンの見出しを追加し、
   修正内容・機能追加の概要を箇条書きで記録する。
2. [release_notes.json](release_notes.json)にも同じバージョンのエントリを
   先頭に追加する（**2026-08-26再発防止**: この手順がCLAUDE.mdに
   明記されておらず、`release_notes.json`自身の`_readme`にしか
   「CHANGELOG.mdとセットで追記」と書かれていなかったため、4バージョン
   連続(ver1.2.16〜1.2.19)で更新が漏れ、アプリ内「バージョン情報」画面の
   見出し(`APP_VERSION`)と本文(release_notes.jsonの内容)が食い違う
   不具合になっていた)。`title`は簡潔な要約、`public`は一般ユーザー
   にも見せてよい当たり障りのない内容(不具合解消・機能追加など)、
   `admin`は管理者向けの詳細(件数・原因・ファイル名等)に分けて書く
   （既存エントリの書式を踏襲すること）。
3. その場で `git add` → `git commit` → `git push` まで行う
   （コミットメッセージにバージョン文字列を含めるか、直後に
   バージョンだけの軽いコミットを作ってもよい）。
4. コミットが完了したら、そのコミットハッシュを分かる範囲で
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

- **場所**: GitHub `yutsuka123/business_plan`（private確認済み・公開APIで404）。
  ローカルの clone 先は作業機ごとに異なる（上記「💻 作業機が macOS /
  Windows の2系統になった」参照）。実パスは公開リポジトリに書かない。
- **本プロジェクト用フォルダ**: `products/study_nyangailab/`
  - `README.md`: 事業サマリ（詳細はこちら側の`docs/`参照という設計）。
  - `docs/`（**2026-09-15〜・`docs/`全体のgitバックアップ本体**）:
    このリポジトリ（LearningEnglishWithAI）の`docs/`ディレクトリ全体を
    `rsync -a --exclude='.DS_Store'`でそのままミラーしたもの
    （`DESIGN.md`/`TODO.md`/`TODO_OLD.md`等ファイル名もそのまま）。
    `docs/`はこのリポジトリでは`.gitignore`対象＝このマシンにしか
    存在せずgit管理外だったため、**business_plan側でgit管理下に置く
    ことで初めてバックアップ・履歴管理される**（2026-08-09〜あった
    `運用リファレンス.md`という単一ファイルの手動バックアップ方式を
    `docs/`全体のミラーに統合・発展させたもの）。
    **`docs/`配下を更新した回のセッションでは、このミラーも
    `rsync -a --exclude='.DS_Store' --exclude='TODO_20260915_pre_reorg_backup.md'
    docs/ <business_plan clone先>/products/study_nyangailab/docs/`で
    都度同期し、business_plan側でgit commitすること**（pushは
    [[feedback-business-plan-local-commit-only]]の通り明示的に頼まれた
    時のみ）。
  - `運用リファレンス.md`・`プロジェクトTODOバックアップ.md`等の日本語名
    ファイル（2026-08-09〜2026-09-09頃に作られた手動バックアップの名残）:
    **2026-09-15以降は更新対象外**。内容は上記`docs/`ミラー（特に
    `docs/TODO.md`）に完全に含まれるため、今後参照する場合は`docs/`
    ミラー側を見ること。削除はせず当面残置（要否は別途ユーザー判断）。
  - `secrets_backup/`（**2026-08-13〜**）: 本番VPS用SSH鍵ペアと
    `deploy/.env.study`（`OPENAI_API_KEY`/`SESSION_SECRET`等の実値）の
    バックアップ。rsync --deleteがVPS専用の`.env.study`を誤削除する
    事故（下記ルール参照）を機に、VPS/作業機のどちらか一方が失われても
    復旧できるよう追加した。**このリポジトリ側（LearningEnglishWithAI）
    には実値は一切置かない**（本項目の通りbusiness_plan側のみに保管）。
    値を更新したら都度手動で同期すること（詳細・復元手順は
    `products/study_nyangailab/secrets_backup/README.md`参照）。
- **関連する別プロダクト**: `nyangai.lab`宣伝アカウント（Instagram/X）は
  元々このアプリ用ではなく、別のAndroidアプリ紹介サイト
  （`nyangailab.com`）の宣伝用に作られたものを流用している。そちらの
  サイト・関連リポジトリ名・構成の詳細は`business_plan`の
  `products/nyangailab_android/README.md`を参照。

## 💻 作業機が macOS / Windows の2系統になった（2026-08-21〜）

従来は macOS 1台のみで作業していたが、Windows 機でも作業するようになった。
**プラットフォーム依存のファイルは必ず OS ごとにディレクトリを分けて
git 管理する**（片方だけ直して他方が壊れる事故を防ぐため）。

### ディレクトリ分割のルール
- 実行系（シェルスクリプト等）で OS 依存するものは
  `deploy/macos/` と `deploy/windows/` に分ける。
  新しくスクリプトを追加するときも同じ方針に従うこと。
  - macOS/Linux: `deploy/macos/sync_code.sh` ＋
    `deploy/macos/deploy_target.example.sh`
  - Windows: `deploy/windows/sync_code.ps1` ＋
    `deploy/windows/deploy_target.example.ps1`
- OS に依存しないもの（`docker-compose.study.yml`・`Caddyfile.study.snippet`・
  `.env.study.example`・`DEPLOY_RUNBOOK.md` 等）は `deploy/` 直下に据え置く。
  VPS 上で動くもの＝Linux前提なので分割不要。
- **片方を変更したらもう片方も必ず同じ内容に揃える**（同期対象の allowlist、
  `--delete` の扱い等がズレると本番事故に直結する）。

### 改行コード（CRLF）事故に注意
Windows の git は既定で `core.autocrlf=true` のため、チェックアウト時に
LF → CRLF へ勝手に変換される。**シェルスクリプト・SSH秘密鍵・Dockerfile が
CRLF になると Linux/OpenSSH 側で動かない**（秘密鍵は `invalid format` で拒否）。
- 本リポジトリは [.gitattributes](.gitattributes) で拡張子ごとに改行コードを
  固定済み。新しい種類のファイルを追加するときは必要に応じて追記すること。
- private リポジトリ `business_plan` の `secrets_backup/` も同様に
  `.gitattributes` で保護してある（詳細は下記「🔗連携している private
  リポジトリ」参照）。

### Windows 固有の事情
- **rsync が無い**（Git Bash にも同梱されていない）。WSL(Ubuntu) の rsync を
  呼び出すラッパー方式にしてある。scp/tar では `--delete` 相当の差分削除が
  できず Mac 版と挙動が変わってしまうため。
- `deploy/windows/sync_code.ps1` は上記「rsync `--delete` の必須ルール」を
  構造的に強制するため **既定が dry-run**。実行するには `-Execute` を明示する。
  （Mac 版は従来どおり即実行なので挙動が異なる）
- 本番VPSへは `ssh eigo-vps` で入れる（`~/.ssh/config` にエイリアス設定済み。
  実IPを打たずに済むので、コマンド履歴や会話ログへのIP露出を防げる）。
  rsync も `eigo-vps:/home/<user>/eigo/` の形で書けば実IPを書かずに済む。

### 環境ごとに異なるパス（手順書に実パスを書かない理由）
- 本リポジトリの clone 先も、連携先 `business_plan` の clone 先も、**作業機
  ごとにパスが異なる**（`business_plan` は Mac と Windows で階層自体が違う）。
  そのため手順書・スクリプトに実パスを直書きせず、スクリプト自身の位置から
  相対で解決するか、gitignore 対象の設定ファイルに逃がすこと。
  実パスが必要なメモは `docs/`（git管理外）か `business_plan` 側に置く。
- `docs/` は `.gitignore` 対象＝**git経由では他マシンに来ない**。新しい作業機
  では `docs/DESIGN.md` `docs/TODO.md` が存在しないので、手動コピーが必要。
  代替として `business_plan` 側の `運用リファレンス.md` を参照する。

## その他

- 新しいセッションを始めるときは、まず [docs/DESIGN.md](docs/DESIGN.md)
  と [docs/TODO.md](docs/TODO.md) を読む。
  **ただし `docs/` は git 管理外**なので、作業機によっては存在しない。
  無い場合は `business_plan` の `products/study_nyangailab/運用リファレンス.md`
  を代わりに読む。
