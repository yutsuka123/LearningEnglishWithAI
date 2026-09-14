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
# ⚠️ 実行はtmux/screenの中で行うこと。ビルド等に数分かかるため、
#   SSHセッションが切れるとスクリプトごと中断する(Fable指摘M1)。
#   途中で切れても、移行スクリプト自身のトランザクション保護
#   (scripts/migrate_split_db_2026_09_14.py)により中途半端なデータが
#   コミットされることは無いが、後片付け(新3ファイルの削除確認)が
#   手動になる場合がある。
#
# ■ 安全設計のポイント(2026-09-14 Fableレビューで4件の重大指摘を受け
#   全面的に修正済み)
# - `:latest`タグは移行成功を確認するまで一切書き換えない。新イメージは
#   別タグ(`eigo-app:split-candidate`)でビルドし、稼働中コンテナには
#   何の影響も与えない。ロールバック用の`:prev`は`:latest`タグからでは
#   なく、**稼働中コンテナが実際に使っているイメージID**から作る
#   (Fable指摘C2: `:latest`が他の作業で先に上書きされていても安全)。
# - 移行は`docker compose run --rm`(EIGO_IMAGE=候補タグ)で実行し、
#   本番サービス定義(user/env_file/network/volumes)をそのまま継承する
#   (Fable指摘H1: 素の`docker run`だと権限不一致で失敗し得た)。
# - 旧コンテナの停止後、実際に停止したことを`docker ps`で確認する
#   (Fable指摘H4: 停止失敗を握りつぶすと稼働中に移行してしまう)。
# - 移行スクリプト自身が件数一致・FK整合性・重複名なし・金額合計一致等を
#   検証し、1つでも失敗すれば新3ファイルを自動削除して非ゼロ終了する
#   (scripts/migrate_split_db_2026_09_14.py参照)。既存の出力ファイルが
#   あれば無条件に上書きせず拒否する(Fable指摘C1)。
# - 移行が失敗した場合、`:latest`は触っていないため
#   `docker compose up -d`だけで即座に旧構成のまま復旧する。
# - 移行成功後に`:latest`を新イメージへ切替→起動→ヘルスチェック+
#   件数サニティチェック(Fable指摘M4)。失敗時は`:prev`へ戻す。
#
# ■ 使い方(VPS上、tmux/screen内で・事前にコード同期済みであること)
#   cd $VPS_APP_DIR
#   tmux new -s dbsplit
#   ./deploy/migrate_and_cutover_db_split.sh
#
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
DATA_DIR="${DATA_DIR:-$APP_DIR/data}"
COMPOSE_FILE="${COMPOSE_FILE:-deploy/docker-compose.study.yml}"
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

container_running() {
  [ -n "$(docker ps -q -f "name=^${CONTAINER}\$")" ]
}

confirm() {
  read -r -p "$1 [y/N]: " ans
  [ "$ans" = "y" ] || [ "$ans" = "Y" ]
}

cd "$APP_DIR"
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
  echo "  前回の移行が中断した残骸、または既に切替済みの可能性があります。" >&2
  echo "  内容を確認の上、本当に作り直してよい場合のみ手動で削除してから" >&2
  echo "  再実行してください(このスクリプトは既存ファイルを自動削除しません)。" >&2
  exit 1
fi
confirm "旧vocabulary.db($(du -h "$DATA_DIR/vocabulary.db" | cut -f1))を3分割へ移行します。よろしいですか?" \
  || { echo "中断しました。"; exit 1; }

# 切替後の件数サニティチェック用に、移行前のusers/words件数を控えておく
# (Fable指摘M4: ヘルスチェックはDBの中身を見ないため、別途実データで
# 検証する)。
PRE_USERS="$(docker exec -i "$CONTAINER" python3 -c "
import sqlite3
c = sqlite3.connect('/data/vocabulary.db')
print(c.execute('SELECT COUNT(*) FROM users').fetchone()[0])
")"
PRE_WORDS="$(docker exec -i "$CONTAINER" python3 -c "
import sqlite3
c = sqlite3.connect('/data/vocabulary.db')
print(c.execute('SELECT COUNT(*) FROM words').fetchone()[0])
")"
log_json pre_counts ok "users=$PRE_USERS words=$PRE_WORDS"

# --- 1. ロールバック用に、稼働中コンテナが実際に使っているイメージIDを
#        控える(:latestタグからではない。Fable指摘C2: :latestが他の
#        作業で先に上書きされていても安全にするため)。 --------------------
RUNNING_IMAGE_ID="$(docker inspect "$CONTAINER" --format '{{.Image}}' 2>/dev/null || true)"
if [ -n "$RUNNING_IMAGE_ID" ]; then
  docker tag "$RUNNING_IMAGE_ID" "$PREV_IMAGE"
  log_json tag_prev ok "running($RUNNING_IMAGE_ID) -> $PREV_IMAGE"
else
  echo "警告: 稼働中コンテナのイメージIDが取得できませんでした。" >&2
  confirm "このまま続行しますか(失敗時のロールバックができない可能性があります)?" \
    || { echo "中断しました。"; exit 1; }
fi

# --- 2. 新イメージを候補タグでビルド(稼働中コンテナは無停止・無変更) -------
echo "--- 新イメージをビルド中(候補タグ、稼働中コンテナには影響しません) ---"
EIGO_IMAGE="$CANDIDATE_IMAGE" docker compose -f "$COMPOSE_FILE" build
log_json build ok "$CANDIDATE_IMAGE"

# --- 3. デプロイ直前バックアップ(念のため、フェーズ0のスナップショットと別) -
STAMP="$(date +%Y%m%d_%H%M%S)"
docker exec -i "$CONTAINER" python3 -c "
import sqlite3
src = sqlite3.connect('/data/vocabulary.db')
dst = sqlite3.connect('/data/vocabulary.predeploy-dbsplit-${STAMP}.db')
src.backup(dst); dst.close(); src.close()
"
log_json backup ok "vocabulary.predeploy-dbsplit-${STAMP}.db"

confirm "旧コンテナを停止して移行を実行します(ここからダウンタイム開始)。よろしいですか?" \
  || { echo "中断しました(バックアップ・候補イメージはそのまま残します)。"; exit 1; }

# --- 4. 旧コンテナを停止(処理中リクエストに猶予・グレースフル) -------------
echo "--- 旧コンテナを停止中(最大30秒の猶予) ---"
docker compose -f "$COMPOSE_FILE" stop -t 30 "$CONTAINER" || true
if container_running; then
  # 停止失敗を握りつぶすと、稼働中の旧コンテナが書き込みを続けたまま
  # 移行(読み取り専用スナップショット)を実行してしまい、直近の書き込みが
  # 失われる恐れがある(Fable指摘H4)。
  log_json stop_old fatal "旧コンテナの停止に失敗しました。手動確認が必要です"
  echo "エラー: 旧コンテナ($CONTAINER)がまだ稼働中です。手動で確認・停止してから" >&2
  echo "  再実行してください。" >&2
  exit 1
fi
log_json stop_old ok "graceful stop confirmed (timeout 30s)"

# --- 5. 移行スクリプトを候補イメージの使い捨てコンテナで実行 ---------------
# docker compose run(EIGO_IMAGE=候補タグ)で実行することで、本番サービス
# 定義のuser(1000:1000)・env_file(.env.study)・network・volumesを
# そのまま継承する(Fable指摘H1: 素のdocker runだと権限/ネットワークが
# 本番と食い違い、失敗したり誤った所有権でファイルが作られたりし得た)。
echo "--- 移行スクリプトを実行中 ---"
if EIGO_IMAGE="$CANDIDATE_IMAGE" docker compose -f "$COMPOSE_FILE" run --rm \
  --no-deps --name eigo-app-migrate "$CONTAINER" \
  python3 scripts/migrate_split_db_2026_09_14.py --source /data/vocabulary.db
then
  log_json migrate ok "検証OK"
else
  log_json migrate error "移行スクリプトが失敗しました"
  echo "--- 移行失敗。旧コンテナを再起動して復旧します ---"
  echo "  ※失敗時は移行スクリプトが新3ファイルを自動削除しますが、" >&2
  echo "    強制終了等の異常終了の場合は $DATA_DIR に残骸が残ることが" >&2
  echo "    あります。復旧後に確認してください。" >&2
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
  # ヘルスチェックはDBの中身を見ないため、実データの件数も突合する
  # (Fable指摘M4)。
  POST_USERS="$(docker exec -i "$CONTAINER" python3 -c "
import sqlite3
c = sqlite3.connect('/data/core.db')
print(c.execute('SELECT COUNT(*) FROM users').fetchone()[0])
" 2>/dev/null || echo "ERR")"
  POST_WORDS="$(docker exec -i "$CONTAINER" python3 -c "
import sqlite3
c = sqlite3.connect('file:/data/content.db?mode=ro', uri=True)
print(c.execute('SELECT COUNT(*) FROM words').fetchone()[0])
" 2>/dev/null || echo "ERR")"
  if [ "$POST_USERS" = "$PRE_USERS" ] && [ "$POST_WORDS" = "$PRE_WORDS" ]; then
    log_json success ok "DB分割切替完了 (users=$POST_USERS words=$POST_WORDS)"
    echo "=== 完了 ==="
    echo "旧vocabulary.dbはロールバック用にそのまま残しています。"
    echo "本番で十分な期間問題なく稼働したことを確認できたら削除してください。"
    exit 0
  fi
  log_json mismatch error \
    "件数不一致 users(pre=$PRE_USERS,post=$POST_USERS) words(pre=$PRE_WORDS,post=$POST_WORDS)"
  echo "エラー: 切替後の件数が移行前と一致しません。ロールバックします。" >&2
  OK=0
fi

# --- 8. ヘルスチェック失敗 or 件数不一致 → 旧イメージへロールバック ---------
log_json error error "ヘルスチェック/件数検証に失敗したためロールバックします"
docker tag "$PREV_IMAGE" "$IMAGE"
docker compose -f "$COMPOSE_FILE" up -d
sleep 10
if health_ok; then
  log_json rolled_back ok "旧イメージ+旧vocabulary.dbで復旧しました"
  echo "警告: 新3ファイル(core.db/content.db/logs.db)は残っています。原因調査後、" >&2
  echo "  問題なければ削除するか、再度このスクリプトを実行してください。" >&2
  exit 1
else
  log_json fatal fatal "ロールバックしても復旧しません。手動対応が必要です"
  exit 1
fi
