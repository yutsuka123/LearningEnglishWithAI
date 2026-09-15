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
# ⚠️ このスクリプトの実行中は、scheduled_deploy.sh用の
#   data/deploy_request.json を予約しないこと(下記手順0で自動チェック
#   する)。cronがこの操作の途中で`docker compose up -d --build`を
#   実行すると、まだ移行していないデータに対して分割対応コードで
#   コンテナが再作成されてしまう(2回目Fableレビュー指摘M-2)。
#
# ■ 安全設計のポイント(2026-09-14 Fableレビュー2回・重大4件+高4件+中5件の
#   指摘を全面的に反映済み)
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
# - **件数サニティチェック用のPRE件数は、旧コンテナを完全に停止した後の
#   静的な状態から取得する**(2回目レビュー指摘M-1: 以前は確認プロンプト・
#   ビルド・バックアップを挟んだ数分前の「稼働中の」値を使っていたため、
#   その間に実際にあった新規登録等が誤って「件数不一致」と判定され、
#   届いたばかりのデータを持つ新環境を巻き戻してしまう恐れがあった)。
# - 移行スクリプト自身が件数一致・FK整合性・重複名なし・金額合計一致等を
#   検証し、1つでも失敗すれば新3ファイルを自動削除して非ゼロ終了する
#   (scripts/migrate_split_db_2026_09_14.py参照)。既存の出力ファイルが
#   あれば無条件に上書きせず拒否する(Fable指摘C1)。
# - 移行が失敗した場合、`:prev`(稼働中コンテナの元イメージ)へ明示的に
#   再タグしてから`docker compose up -d`する(2回目レビュー指摘M-2:
#   以前は「:latestは触っていないはず」という前提で無条件`up -d`
#   していたが、外部要因(他の作業からの`docker compose build`等)で
#   :latestが書き換わっていた場合に備え、明示的に安全な方へ寄せる)。
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

# 移行前スナップショットからusers/words件数を読む共通ヘルパ。候補
# イメージの使い捨てコンテナ経由で読む(旧コンテナは既に停止済みの
# 前提のため`docker exec`は使えない)。
count_users_words() {
  local db_path="$1"
  EIGO_IMAGE="$CANDIDATE_IMAGE" docker compose -f "$COMPOSE_FILE" run --rm \
    --no-deps -T --name eigo-app-count "$CONTAINER" python3 -c "
import sqlite3
c = sqlite3.connect('file:${db_path}?mode=ro', uri=True)
print(c.execute('SELECT COUNT(*) FROM users').fetchone()[0])
print(c.execute('SELECT COUNT(*) FROM words').fetchone()[0])
"
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
if [ -f "$DATA_DIR/deploy_request.json" ]; then
  echo "エラー: $DATA_DIR/deploy_request.json が存在します" >&2
  echo "  (scheduled_deploy.shの自動デプロイが予約されています)。" >&2
  echo "  この操作の途中でcronによる自動デプロイが割り込むと危険なため、" >&2
  echo "  予約を解除するか完了するまで待ってから再実行してください。" >&2
  exit 1
fi
confirm "旧vocabulary.db($(du -h "$DATA_DIR/vocabulary.db" | cut -f1))を3分割へ移行します。よろしいですか?" \
  || { echo "中断しました。"; exit 1; }

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
# 2026-09-15 本番投入時に判明した事象への対応: このVPS環境の
# docker compose(v5.1.4)では、`EIGO_IMAGE=$CANDIDATE_IMAGE docker compose
# build`が候補タグではなく`$IMAGE`(:latest)に直接書き込むことが実際に
# 起きた(ローカルの新しいdocker compose(v5.5.1)では再現せず、バージョン
# 依存の挙動と推測されるが未解明)。実害は無かった(手順1の`:prev`は
# `:latest`ではなく稼働中コンテナの実IDから取るため無事だった)が、
# 「検証が通るまで:latestを一切変更しない」という設計上の安全マージンが
# 失われるため、ビルド前後で:latestが意図せず変化していないかを検証し、
# 変化していれば候補タグを明示的に貼り直した上で:latestを復元する。
PRE_BUILD_LATEST_ID="$(docker image inspect "$IMAGE" --format '{{.Id}}' 2>/dev/null || true)"
echo "--- 新イメージをビルド中(候補タグ、稼働中コンテナには影響しません) ---"
EIGO_IMAGE="$CANDIDATE_IMAGE" docker compose -f "$COMPOSE_FILE" build
POST_BUILD_LATEST_ID="$(docker image inspect "$IMAGE" --format '{{.Id}}' 2>/dev/null || true)"
if [ -n "$PRE_BUILD_LATEST_ID" ] \
   && [ "$POST_BUILD_LATEST_ID" != "$PRE_BUILD_LATEST_ID" ]; then
  echo "警告: ビルドで候補タグではなく$IMAGEが直接書き換えられました。" >&2
  echo "  候補タグへ明示的に貼り直し、$IMAGEを復元します。" >&2
  docker tag "$POST_BUILD_LATEST_ID" "$CANDIDATE_IMAGE"
  docker tag "$PRE_BUILD_LATEST_ID" "$IMAGE"
  log_json build warn \
    "EIGO_IMAGEが$IMAGEに直接反映されたため候補タグへ手動で分離・復元"
elif ! docker image inspect "$CANDIDATE_IMAGE" >/dev/null 2>&1; then
  # 上記のIDずれでは検知できないが候補タグ自体が存在しないケースの保険。
  echo "警告: ビルド後に$CANDIDATE_IMAGEが見つかりません。" >&2
  exit 1
fi
log_json build ok "$CANDIDATE_IMAGE"

confirm "旧コンテナを停止して移行を実行します(ここからダウンタイム開始)。よろしいですか?" \
  || { echo "中断しました(候補イメージはそのまま残します)。"; exit 1; }

# --- 3. 旧コンテナを停止(処理中リクエストに猶予・グレースフル) -------------
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

# --- 4. デプロイ直前バックアップ + 件数サニティチェック用の基準値取得 ------
# 2回目レビュー指摘M-1: 旧コンテナを完全に停止した「今」の静的な状態から
# 取得する(確認プロンプト・ビルドを挟んだ数分前の値だと、その間の実際の
# 新規登録等が「不一致」と誤判定され、届いたばかりのデータを持つ新環境を
# 誤ってロールバックしてしまう恐れがあった)。旧コンテナは既に停止済みの
# ため、候補イメージの使い捨てコンテナ経由で読む。
STAMP="$(date +%Y%m%d_%H%M%S)"
# 2026-09-15 4回目Fableレビュー(試験仕様書v2レビュー中に確定)指摘の
# 重大-1: `set -euo pipefail`下では `VAR="$(cmd)"` の代入文自体がcmdの
# 非ゼロ終了で即座にスクリプトを終了させ、直後のif分岐(復旧処理)へは
# 到達しない(bashの既知の挙動・実機再現済み)。`if ! VAR="$(cmd)"; then`
# の形にすることで、失敗をset -eに奪われず自前の分岐で拾えるようにする。
if ! BACKUP_OUT="$(EIGO_IMAGE="$CANDIDATE_IMAGE" docker compose -f "$COMPOSE_FILE" \
  run --rm --no-deps -T --name eigo-app-backup "$CONTAINER" python3 -c "
import sqlite3
src = sqlite3.connect('file:/data/vocabulary.db?mode=ro', uri=True)
dst = sqlite3.connect('/data/vocabulary.predeploy-dbsplit-${STAMP}.db')
src.backup(dst); dst.close(); src.close()
print('ok')
")" || [ "$BACKUP_OUT" != "ok" ]; then
  log_json backup fatal "バックアップに失敗しました。旧コンテナを再起動します"
  # 3回目レビュー指摘M-5: 他の復旧パス(移行失敗時・ヘルスチェック失敗時)
  # と同様、":latestは触っていないはず"に頼らず明示的にprevへ再タグして
  # から起動する。ただしPREV_IMAGEが存在しない場合(手順1で取得失敗し
  # confirmで続行した場合)はdocker tag自体がset -eで即死し、この復旧
  # ブロックにすら入れなくなるため、存在確認してから行う(高-1対応)。
  if docker image inspect "$PREV_IMAGE" >/dev/null 2>&1; then
    docker tag "$PREV_IMAGE" "$IMAGE"
  else
    log_json backup fatal "$PREV_IMAGE が存在しないため再タグをスキップします(手動確認要)"
  fi
  docker compose -f "$COMPOSE_FILE" up -d
  exit 1
fi
log_json backup ok "vocabulary.predeploy-dbsplit-${STAMP}.db"

# 同じ理由(重大-1)で、件数取得の失敗も明示的に拾って復旧する
# (旧実装はここに復旧処理自体が無く、失敗時は旧コンテナ停止のまま
# 無人ダウンタイムになっていた)。
if ! PRE_COUNTS="$(count_users_words "/data/vocabulary.db")"; then
  log_json pre_counts fatal "件数取得に失敗しました。旧コンテナを再起動します"
  if docker image inspect "$PREV_IMAGE" >/dev/null 2>&1; then
    docker tag "$PREV_IMAGE" "$IMAGE"
  else
    log_json pre_counts fatal "$PREV_IMAGE が存在しないため再タグをスキップします(手動確認要)"
  fi
  docker compose -f "$COMPOSE_FILE" up -d
  exit 1
fi
PRE_USERS="$(echo "$PRE_COUNTS" | sed -n 1p)"
PRE_WORDS="$(echo "$PRE_COUNTS" | sed -n 2p)"
if [ -z "$PRE_USERS" ] || [ -z "$PRE_WORDS" ]; then
  log_json pre_counts fatal "件数の解析に失敗しました(出力形式不正)。旧コンテナを再起動します"
  if docker image inspect "$PREV_IMAGE" >/dev/null 2>&1; then
    docker tag "$PREV_IMAGE" "$IMAGE"
  else
    log_json pre_counts fatal "$PREV_IMAGE が存在しないため再タグをスキップします(手動確認要)"
  fi
  docker compose -f "$COMPOSE_FILE" up -d
  exit 1
fi
log_json pre_counts ok "users=$PRE_USERS words=$PRE_WORDS"

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
  echo "--- 移行失敗。旧イメージ・旧コンテナで復旧します ---"
  echo "  ※失敗時は移行スクリプトが新3ファイルを自動削除しますが、" >&2
  echo "    強制終了等の異常終了の場合は $DATA_DIR に残骸が残ることが" >&2
  echo "    あります。復旧後に確認してください。" >&2
  # 2回目レビュー指摘M-2: ":latestは触っていないはず"という前提に頼らず、
  # 明示的にprevへ再タグしてから起動する(他プロセスによる:latest書き換え
  # に対する防御)。PREV_IMAGE不在時はdocker tag自体がset -eで即死し復旧
  # 不能になるため、存在確認してから行う(4回目レビュー指摘 高-1対応)。
  if docker image inspect "$PREV_IMAGE" >/dev/null 2>&1; then
    docker tag "$PREV_IMAGE" "$IMAGE"
  else
    log_json recover fatal "$PREV_IMAGE が存在しないため再タグをスキップします(手動確認要)"
  fi
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
  # (Fable指摘M4)。PREは手順4で旧コンテナ停止後の静的な状態から取得済み
  # なので、ここでの比較は本来の移行が正しいかだけを見る(M-1対応)。
  POST_USERS="$(docker exec -i "$CONTAINER" python3 -c "
import sqlite3
c = sqlite3.connect('file:/data/core.db?mode=ro', uri=True)
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
# PREV_IMAGE不在時はdocker tag自体がset -eで即死し、docker compose up -d
# すら試みられず完全停止のまま終わる恐れがあるため、存在確認してから行う
# (4回目レビュー指摘 高-1対応)。不在でもup -dは試みる(現IMAGEでの
# 再起動を最後の望みとする)。
if docker image inspect "$PREV_IMAGE" >/dev/null 2>&1; then
  docker tag "$PREV_IMAGE" "$IMAGE"
else
  log_json error fatal "$PREV_IMAGE が存在しないため再タグをスキップします(手動確認要)"
fi
docker compose -f "$COMPOSE_FILE" up -d
sleep 10
if health_ok; then
  log_json rolled_back ok "旧イメージ+旧vocabulary.dbで復旧しました"
  echo "警告: 新3ファイル(core.db/content.db/logs.db)は残っています。原因調査後、" >&2
  echo "  問題なければ削除するか、再度このスクリプトを実行してください。" >&2
  echo "警告: 停止後に届いた分の書き込みはこの新3ファイル側にしか無い" >&2
  echo "  可能性があります(ロールバック=データ損失になり得る)。手動での" >&2
  echo "  マージを検討してください。" >&2
  exit 1
else
  log_json fatal fatal "ロールバックしても復旧しません。手動対応が必要です"
  exit 1
fi
