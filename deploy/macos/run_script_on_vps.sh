#!/usr/bin/env bash
# 本番VPS上でscripts/配下のPythonスクリプトを実行する。【macOS/Linux用】
# コンテンツ反映(add_*.py・import_details.py等)は必ずテーブル単位のSQL
# スクリプト経由で行い、DBファイルそのものを転送しないというルール
# (CLAUDE.md参照)を、実行面から支援するラッパー。
#
# 2026-09-14判明: Dockerfileはscripts/をイメージに焼き込む方式(bind mount
# ではない)ため、稼働中のeigo-appコンテナへ`docker exec`しても、
# sync_code.shで転送しただけの新しいスクリプトは見えない(イメージの
# 再ビルドが必要)。かといって`docker compose up -d --build`は稼働中の
# コンテナを再作成してしまい、予定外のダウンタイム=無告知デプロイに
# なってしまう。
# そこで、**イメージだけ再ビルド(`docker compose build`、稼働中コンテナは
# 無停止・無変更)**した上で、**`docker compose run --rm`で使い捨ての別
# コンテナ**を起動してスクリプトを実行する(同じ/data・.env.studyを見る
# ので本番DBへの反映は正しく行われるが、稼働中コンテナは一切触らない)。
# 実際のコード反映(稼働中コンテナの入れ替え)は、予告済みのメンテ枠で
# scheduled_deploy.shが`up -d --build`することで初めて起こる。
#
# ⚠️2026-09-14 Fable指摘(C2)で修正: 当初`docker compose build`が既定の
# `:latest`タグを上書きしていたため、DB分割等の「移行成功まで:latestは
# 触らない」設計の切替スクリプトと衝突し、失敗時ロールバックが
# 新コード×未移行データで起動する重大な穴があった。
# `EIGO_IMAGE`環境変数(docker-compose.study.ymlが`${EIGO_IMAGE:-eigo-app:latest}`
# を参照)で明示的に別タグを使い、`:latest`には一切触れないようにした。
#
# 前提: 事前に ./deploy/macos/sync_code.sh でコード(scripts/含む)を
# 同期済みであること。
#
# 使い方:
#   ./deploy/macos/run_script_on_vps.sh scripts/add_latin_etymology_2026_09_14.py
#   ./deploy/macos/run_script_on_vps.sh scripts/import_details.py \
#       scripts/add_latin_etymology_2026_09_14_details.json
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TARGET_CONF="$REPO_ROOT/docs/deploy_target.local.sh"

if [ ! -f "$TARGET_CONF" ]; then
  echo "エラー: $TARGET_CONF が見つかりません。" >&2
  exit 1
fi
# shellcheck source=/dev/null
source "$TARGET_CONF"
: "${VPS_SSH_KEY:?VPS_SSH_KEY が未設定です}"
: "${VPS_HOST:?VPS_HOST が未設定です}"
: "${VPS_APP_DIR:?VPS_APP_DIR が未設定です}"

if [ "$#" -lt 1 ]; then
  echo "使い方: $0 <script.py> [args...]" >&2
  exit 1
fi

COMPOSE_FILE="deploy/docker-compose.study.yml"
SERVICE="${SERVICE:-eigo-app}"
RUN_NAME="eigo-app-content-task"
# :latestには絶対に触らない専用タグ(Fable指摘C2)。
TASK_IMAGE="${TASK_IMAGE:-eigo-app:content-task}"

echo "1/2: イメージを再ビルド(タグ=$TASK_IMAGE、:latest・稼働中コンテナは無変更)..."
ssh -i "$VPS_SSH_KEY" "$VPS_HOST" \
  "cd $VPS_APP_DIR && EIGO_IMAGE=$TASK_IMAGE docker compose -f $COMPOSE_FILE build"

echo "2/2: 使い捨てコンテナでスクリプト実行: python3 $*"
ssh -i "$VPS_SSH_KEY" "$VPS_HOST" \
  "cd $VPS_APP_DIR && EIGO_IMAGE=$TASK_IMAGE docker compose -f $COMPOSE_FILE run --rm \
   --name $RUN_NAME $SERVICE python3 $*"
