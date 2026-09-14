#!/usr/bin/env bash
# DB分割(vocabulary.db → content.db/core.db/logs.db)の本番一回限りの
# 移行+切替を行う(2026-09-14・フェーズ3準備)。VPS上で実行する想定。
#
# 通常の scheduled_deploy.sh (cronによる自動デプロイ)とは別枠。理由:
# - 一回限りの構造移行であり、繰り返し実行されるものではない。
# - 移行スクリプト自体が「その時点のスナップショット」を作る性質上、
#   アプリを止めた状態で実行する必要がある(ローカル検証で確認済み・
#   docs/TODO.md「DB分割の検討」参照)。scheduled_deploy.shのような
#   無告知の自動実行には向かない。
# - 初回の切替は人間が各ステップの出力を確認しながら進めるべき
#   （ユーザー指示「急がないで着実に」）。
#
# ■ 安全設計のポイント
# - `:latest`タグは移行成功を確認するまで一切書き換えない。新イメージは
#   別タグ(`eigo-app:split-candidate`)でビルドし、稼働中コンテナには
#   何の影響も与えない。
# - 移行は`docker run`の使い捨てコンテナで実行し、稼働中コンテナは
#   旧コンテナを明示的に停止するまで触らない。
# - 移行スクリプト自身が件数一致・FK整合性・重複名なしを検証し、
#   1つでも失敗すれば新3ファイルを自動削除して非ゼロ終了する
#   (scripts/migrate_split_db_2026_09_14.py参照)。
# - 移行が失敗した場合、`:latest`は触っていないため
#   `docker compose up -d`だけで即座に旧構成のまま復旧する。
# - 移行成功後に`:latest`を新イメージへ切替→起動→ヘルスチェック。
#   ヘルスチェックが失敗した場合は`:prev`(旧イメージ)へ戻す。
#
# ■ 使い方(VPS上、事前にコード同期済みであること)
#   cd $VPS_APP_DIR
#   ./deploy/migrate_and_cutover_db_split.sh
#
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
DATA_DIR="${DATA_DIR:-$APP_DIR/data}"
COMPOSE_FILE="${COMPOSE_FILE:-$APP_DIR/deploy/docker-compose.study.yml}"
CONTAINER="${CONTAINER:-eigo-app}"
IMAGE="${IMAGE:-eigo-app:latest}"
PREV_IMAGE="${PREV_IMAGE:-eigo-app:prev}"
CANDIDATE_IMAGE="${CANDIDATE_IMAGE:-eigo-app:split-candidate}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8001/api/health}"
LOG="$DATA_DIR/db_split_cutover_log.jsonl"

log_json() {
  printf '{"at":"%s","step":"%s","status":"%s","message":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$2" "$(echo "$3" | tr -d '"\n')" \
    | tee -a "$LOG"
}

health_ok() {
  curl -fsS --max-time 5 "$HEALTH_URL" >/dev/null 2>&1
}

confirm() {
  read -r -p "$1 [y/N]: " ans
  [ "$ans" = "y" ] || [ "$ans" = "Y" ]
}

echo "=== DB分割 移行+切替スクリプト ==="
echo "対象: $DATA_DIR/vocabulary.db → content.db/core.db/logs.db"
echo ""

# --- 0. 事前確認 -------------------------------------------------------------
if [ ! -f "$DATA_DIR/vocabulary.db" ]; then
  echo "エラー: $DATA_DIR/vocabulary.db が見つかりません。" >&2
  exit 1
fi
if [ -f "$DATA_DIR/core.db" ] || [ -f "$DATA_DIR/content.db" ] || \
   [ -f "$DATA_DIR/logs.db" ]; then
  echo "エラー: core.db/content.db/logs.db が既に存在します。" >&2
  echo "  前回の移行が中断した残骸の可能性があります。内容を確認の上、" >&2
  echo "  問題なければ削除してから再実行してください。" >&2
  exit 1
fi
confirm "旧vocabulary.db($(du -h "$DATA_DIR/vocabulary.db" | cut -f1))を3分割へ移行します。よろしいですか?" \
  || { echo "中断しました。"; exit 1; }

# --- 1. 現在のイメージをprevとして保存(:latestはまだ触らない) --------------
if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker tag "$IMAGE" "$PREV_IMAGE"
  log_json tag_prev ok "$IMAGE -> $PREV_IMAGE"
fi

# --- 2. 新イメージを候補タグでビルド(稼働中コンテナは無停止・無変更) -------
echo "--- 新イメージをビルド中(候補タグ、稼働中コンテナには影響しません) ---"
docker build -t "$CANDIDATE_IMAGE" "$APP_DIR"
log_json build ok "$CANDIDATE_IMAGE"

# --- 3. デプロイ直前バックアップ(念のため、フェーズ0のスナップショットと別) -
STAMP="$(date +%Y%m%d_%H%M%S)"
python3 -c "
import sqlite3
src = sqlite3.connect('$DATA_DIR/vocabulary.db')
dst = sqlite3.connect('$DATA_DIR/vocabulary.predeploy-dbsplit-${STAMP}.db')
src.backup(dst); dst.close(); src.close()
"
log_json backup ok "vocabulary.predeploy-dbsplit-${STAMP}.db"

confirm "旧コンテナを停止して移行を実行します(ここからダウンタイム開始)。よろしいですか?" \
  || { echo "中断しました(バックアップ・候補イメージはそのまま残します)。"; exit 1; }

# --- 4. 旧コンテナを停止(処理中リクエストに猶予・グレースフル) -------------
echo "--- 旧コンテナを停止中(最大30秒の猶予) ---"
docker compose -f "$COMPOSE_FILE" stop -t 30 "$CONTAINER" || true
log_json stop_old ok "graceful stop (timeout 30s)"

# --- 5. 移行スクリプトを候補イメージの使い捨てコンテナで実行 ---------------
echo "--- 移行スクリプトを実行中 ---"
if docker run --rm \
  --env-file "$APP_DIR/deploy/.env.study" \
  -e DATA_DIR=/data \
  -v "$DATA_DIR:/data" \
  "$CANDIDATE_IMAGE" \
  python3 scripts/migrate_split_db_2026_09_14.py --source /data/vocabulary.db
then
  log_json migrate ok "検証OK"
else
  log_json migrate error "移行スクリプトが失敗(新3ファイルは自動削除済み)"
  echo "--- 移行失敗。旧コンテナを再起動して復旧します ---"
  docker compose -f "$COMPOSE_FILE" up -d
  for _ in $(seq 1 12); do sleep 5; health_ok && break; done
  if health_ok; then
    log_json recover ok "旧コンテナで復旧しました"
  else
    log_json recover fatal "旧コンテナの復旧にも失敗。手動対応が必要です"
  fi
  exit 1
fi

# --- 6. ここで初めて:latestを新イメージへ切替 ------------------------------
docker tag "$CANDIDATE_IMAGE" "$IMAGE"
log_json tag_latest ok "$CANDIDATE_IMAGE -> $IMAGE"

# --- 7. 新コンテナを起動 -----------------------------------------------------
echo "--- 新コンテナを起動中 ---"
docker compose -f "$COMPOSE_FILE" up -d

OK=0
for _ in $(seq 1 12); do
  sleep 5
  if health_ok; then OK=1; break; fi
done

if [ "$OK" -eq 1 ]; then
  log_json success ok "DB分割切替完了"
  echo "=== 完了 ==="
  echo "旧vocabulary.dbはロールバック用にそのまま残しています。"
  echo "本番で十分な期間問題なく稼働したことを確認できたら削除してください。"
  exit 0
fi

# --- 8. ヘルスチェック失敗 → 旧イメージへロールバック -----------------------
log_json error error "ヘルスチェックが通らないためロールバックします"
docker tag "$PREV_IMAGE" "$IMAGE"
docker compose -f "$COMPOSE_FILE" up -d
sleep 10
if health_ok; then
  log_json rolled_back ok "旧イメージ+旧vocabulary.dbで復旧しました"
  echo "警告: 新3ファイル(core.db/content.db/logs.db)は残っています。原因調査後、" >&2
  echo "  問題なければ削除するか、再度このスクリプトを実行してください。" >&2
else
  log_json fatal fatal "ロールバックしても復旧しません。手動対応が必要です"
  exit 1
fi
