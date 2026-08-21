#!/usr/bin/env bash
# 本番VPS(study.nyangailab.com)へアプリのコードだけを同期する。【macOS/Linux用】
#
# Windows作業機からは deploy/windows/sync_code.ps1 を使うこと
# （同じ同期対象・同じ --delete 挙動を WSL の rsync 経由で再現している）。
#
# 2026-08-13: リポジトリ全体を rsync --delete で丸ごとミラーしていたため、
# ローカルに存在しない(=gitignore対象で意図的にVPSにしか無い)
# deploy/.env.study が「余分なファイル」として削除される事故が起きた。
# 再発防止のため、同期対象を明示的に列挙する(allowlist)方式に変更した。
# deploy/ ディレクトリ自体を同期対象に含めないので、deploy/.env.study
# には構造的に触れられない。
#
# 使い方:
#   1. deploy/macos/deploy_target.example.sh を docs/deploy_target.local.sh に
#      コピーして実値を埋める（docs/ は .gitignore 対象＝コミットされない）。
#   2. ./deploy/macos/sync_code.sh を実行する（コード同期のみ。反映には別途
#      VPS側で docker compose -f deploy/docker-compose.study.yml up -d
#      --build が必要）。
#
# deploy/docker-compose.study.yml や Caddyfile.study.snippet 等
# deploy 配下の設定ファイルを更新したい場合は、このスクリプトでは
# 同期せず、個別に1ファイルずつ rsync すること（--delete はディレクトリ
# 丸ごとには絶対に使わない）。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_CONF="$REPO_ROOT/docs/deploy_target.local.sh"

if [ ! -f "$TARGET_CONF" ]; then
  echo "エラー: $TARGET_CONF が見つかりません。" >&2
  echo "deploy/deploy_target.example.sh を参考に作成してください。" >&2
  exit 1
fi
# shellcheck source=/dev/null
source "$TARGET_CONF"
: "${VPS_SSH_KEY:?VPS_SSH_KEY が未設定です（docs/deploy_target.local.sh を確認）}"
: "${VPS_HOST:?VPS_HOST が未設定です（docs/deploy_target.local.sh を確認）}"
: "${VPS_APP_DIR:?VPS_APP_DIR が未設定です（docs/deploy_target.local.sh を確認）}"

# 同期対象は明示的に列挙(allowlist)。deploy/・docs/・data/・.env 等は
# 意図的に対象外（deploy/.env.study を守るため。Dockerfileが実際に
# COPYしている範囲に合わせてある）。
SYNC_ITEMS=(app static templates scripts run.py requirements.txt Dockerfile CHANGELOG.md)

echo "同期先: ${VPS_HOST}:${VPS_APP_DIR}/"
for item in "${SYNC_ITEMS[@]}"; do
  if [ ! -e "$REPO_ROOT/$item" ]; then
    echo "警告: $item が見つからないためスキップします" >&2
    continue
  fi
  echo "→ 同期中: $item"
  rsync -avz --delete \
    --exclude='__pycache__/' --exclude='*.pyc' \
    -e "ssh -i $VPS_SSH_KEY" \
    "$REPO_ROOT/$item" "$VPS_HOST:$VPS_APP_DIR/"
done

echo ""
echo "コード同期完了。反映するには VPS 上で以下を実行してください:"
echo "  cd $VPS_APP_DIR && docker compose -f deploy/docker-compose.study.yml up -d --build"
