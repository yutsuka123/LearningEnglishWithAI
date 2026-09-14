#!/usr/bin/env bash
# 本番VPS上のeigo-appコンテナ内でscripts/配下のPythonスクリプトを実行する。
# 【macOS/Linux用】コンテンツ反映(add_*.py・import_details.py等)は必ず
# テーブル単位のSQLスクリプト経由で行い、DBファイルそのものを転送しない
# というルール(CLAUDE.md参照)を、実行面から支援するラッパー。
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

CONTAINER="${CONTAINER:-eigo-app}"
echo "実行: docker exec $CONTAINER python3 $*"
ssh -i "$VPS_SSH_KEY" "$VPS_HOST" \
  "cd $VPS_APP_DIR && docker exec -i $CONTAINER python3 $*"
