#!/usr/bin/env bash
# 予告した時刻に自動でデプロイする（VPS上で cron から実行する・2026-08-22）。
#
# ■ なぜ必要か
#   「メンテナンス予定を予告して、その時刻に更新する」を人手でやると、深夜の
#   作業に張り付く必要がある。予告時刻に自動で反映されるようにして、
#   停止を伴う更新を定期メンテナンス枠（既定: 毎週月曜 03:00-03:30 JST）に
#   まとめられるようにする。
#
# ■ 動き
#   cron が数分おきにこのスクリプトを呼ぶ。
#     1. $APP_DIR/data/deploy_request.json が無ければ何もしない（即終了）。
#     2. run_at（JST）がまだ先なら何もしない。
#     3. 時刻が来ていたら:
#        a. vocabulary.db をバックアップ
#        b. 現在のイメージを eigo-app:prev としてタグ付け（ロールバック用）
#        c. docker compose up -d --build
#        d. ヘルスチェック（/api/health）が通るまで最大60秒待つ
#        e. 通らなければ eigo-app:prev に戻して起動し直す（自動ロールバック）
#        f. 結果を data/deploy_log.jsonl に追記し、リクエストファイルを消す
#
# ■ 前提（重要）
#   **コードは事前に作業機から rsync 済みであること。** このスクリプトは
#   「置いてあるコードを、予告した時刻に反映する」だけで、コードを取りに
#   行かない（本リポジトリはVPS上ではgit管理外のrsync配置のため）。
#   手順: 作業機で sync_code.ps1 / sync_code.sh → 予約を入れる → 待つ。
#
# ■ 予約の入れ方（どちらでもよい）
#   - 管理画面の「バージョン情報」→ メンテナンス予定 → 臨時メンテナンスで
#     「この時刻に自動デプロイする」にチェックして保存
#   - VPSで直接:
#       echo '{"run_at":"2026-08-25 03:00","note":"ver1.2.10"}' \
#         > ~/eigo/data/deploy_request.json
#
# ■ cron への登録（VPS上で crontab -e）
#     */5 * * * * /home/<user>/eigo/deploy/scheduled_deploy.sh \
#        >> /home/<user>/eigo/data/scheduled_deploy_cron.log 2>&1
#   ※ 5分刻みなので、予告時刻から最大5分遅れて実行される。
#
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
DATA_DIR="${DATA_DIR:-$APP_DIR/data}"
COMPOSE_FILE="${COMPOSE_FILE:-$APP_DIR/deploy/docker-compose.study.yml}"
CONTAINER="${CONTAINER:-eigo-app}"
IMAGE="${IMAGE:-eigo-app:latest}"
PREV_IMAGE="${PREV_IMAGE:-eigo-app:prev}"
# ヘルスチェックはホストの 127.0.0.1:8001（compose で公開している検証用ポート）
# を使う。コンテナ内は 8000 だが、ホストからは 8001 にマップされている点に注意。
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8001/api/health}"
REQUEST="$DATA_DIR/deploy_request.json"
LOG="$DATA_DIR/deploy_log.jsonl"

log_json() {   # log_json <status> <message>
  printf '{"at":"%s","status":"%s","message":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$(echo "$2" | tr -d '"\n')" \
    >> "$LOG"
}

# ヘルスチェック。ホストに curl が無い環境もあるので、コンテナ内から
# Python で叩く経路もフォールバックとして用意しておく（イメージには curl が
# 入っていないので docker exec で curl は使えない）。
health_ok() {
  if command -v curl >/dev/null 2>&1 &&
     curl -fsS --max-time 5 "$HEALTH_URL" >/dev/null 2>&1; then
    return 0
  fi
  docker exec -i "$CONTAINER" python - >/dev/null 2>&1 <<'PYHEALTH'
import sys
import urllib.request
r = urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=5)
sys.exit(0 if r.status == 200 else 1)
PYHEALTH
}

[ -f "$REQUEST" ] || exit 0

# run_at を取り出す（jq が無い環境でも動くよう sed で拾う）。
RUN_AT="$(sed -n 's/.*"run_at"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
  "$REQUEST" | head -1)"
if [ -z "$RUN_AT" ]; then
  log_json error "deploy_request.json に run_at がありません"
  mv "$REQUEST" "$REQUEST.invalid"
  exit 1
fi

# JSTで比較する（VPSのタイムゾーンに依存しないよう TZ を明示）。
NOW_EPOCH="$(date +%s)"
RUN_EPOCH="$(TZ=Asia/Tokyo date -d "$RUN_AT" +%s 2>/dev/null || echo 0)"
if [ "$RUN_EPOCH" -eq 0 ]; then
  log_json error "run_at を日時として解釈できません: $RUN_AT"
  mv "$REQUEST" "$REQUEST.invalid"
  exit 1
fi
[ "$NOW_EPOCH" -ge "$RUN_EPOCH" ] || exit 0   # まだ時刻前 → 何もしない

echo "=== scheduled deploy start ($(date)) run_at=$RUN_AT ==="
log_json start "run_at=$RUN_AT"

# --- a. DBバックアップ（sqliteのbackup APIで安全にコピー）------------------
STAMP="$(date +%Y%m%d_%H%M%S)"
if docker exec -i "$CONTAINER" python - <<PY
import sqlite3
src = sqlite3.connect('/data/vocabulary.db')
dst = sqlite3.connect('/data/backup_vocabulary_${STAMP}.db')
src.backup(dst); dst.close(); src.close()
print('backup ok')
PY
then
  log_json backup "backup_vocabulary_${STAMP}.db"
else
  log_json warn "DBバックアップに失敗（デプロイは続行）"
fi

# --- b. ロールバック用に現在のイメージを退避 -------------------------------
if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker tag "$IMAGE" "$PREV_IMAGE"
  log_json tag "$IMAGE -> $PREV_IMAGE"
fi

# --- c. ビルドして入れ替え ---------------------------------------------------
if ! docker compose -f "$COMPOSE_FILE" up -d --build; then
  log_json error "build/up に失敗"
  # ビルド失敗なら古いコンテナがそのまま動いている可能性が高いので、
  # 無理にロールバックせず、状態だけ残して人が見に来られるようにする。
  mv "$REQUEST" "$REQUEST.failed"
  exit 1
fi

# --- d. ヘルスチェック -------------------------------------------------------
OK=0
for _ in $(seq 1 12); do
  sleep 5
  if health_ok; then
    OK=1
    break
  fi
done

if [ "$OK" -eq 1 ]; then
  log_json success "deploy ok (run_at=$RUN_AT)"
  rm -f "$REQUEST"
  echo "=== scheduled deploy success ==="
  exit 0
fi

# --- e. 自動ロールバック -----------------------------------------------------
log_json error "ヘルスチェックが通らないためロールバックします"
if docker image inspect "$PREV_IMAGE" >/dev/null 2>&1; then
  docker tag "$PREV_IMAGE" "$IMAGE"
  docker compose -f "$COMPOSE_FILE" up -d --no-build || true
  sleep 10
  if health_ok; then
    log_json rolled_back "前のイメージに戻して復旧しました"
  else
    log_json fatal "ロールバックしても復旧しません。手動対応が必要です"
  fi
else
  log_json fatal "$PREV_IMAGE が無くロールバックできません"
fi
mv "$REQUEST" "$REQUEST.failed"
exit 1
