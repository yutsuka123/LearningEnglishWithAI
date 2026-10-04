#!/usr/bin/env bash
# eigo(study.nyangailab.com)用のfail2banを導入する。VPS上でroot(sudo)で実行する。【何度実行しても安全(冪等)】
#   sudo bash install.sh            # 既定=dryrun(BANはせず「BANしたはず」を監査ログに残すだけ)
#   sudo bash install.sh ban        # 実際にBANする(dryrunで数日様子を見て誤判定が無いと確認してから)
# ・相乗りの他プロジェクトの設定・ログには触れない(追加するのは eigo-* の名前のファイルだけ)。
# ・設定テスト(fail2ban-client -t)に失敗したら、新しいjailを外して中止する(既存のsshd等のjailは影響を受けない)。
# ・実IP・ホスト・パスはこのファイルに書かない(Caddyログの場所はdocker inspectで実行時に取得する)。
set -euo pipefail

MODE="${1:-dryrun}"
case "$MODE" in dryrun|ban) ;; *) echo "使い方: install.sh [dryrun|ban]" >&2; exit 2 ;; esac
[ "$(id -u)" -eq 0 ] || { echo "rootで実行してください(sudo bash install.sh)" >&2; exit 1; }
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CADDY_CONTAINER="${CADDY_CONTAINER:-aipoc-web}"
F2B=/etc/fail2ban

echo "== 0/7 事前確認 (mode=$MODE)"
command -v fail2ban-client >/dev/null || { echo "fail2ban が入っていません(apt install fail2ban)" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 が必要です" >&2; exit 1; }
APP_CONTAINER="${APP_CONTAINER:-eigo-app}"
APPDATA="$(docker inspect "$APP_CONTAINER" --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Source}}{{end}}{{end}}' 2>/dev/null || true)"
[ -n "$APPDATA" ] && [ -f "$APPDATA/core.db" ] && [ -f "$APPDATA/logs.db" ] || { echo "アプリのデータ(core.db/logs.db)が見つかりません(container=$APP_CONTAINER)" >&2; exit 1; }
# 途中で失敗した場合に、置いたjailを外して中止する(jailだけが残って次回のfail2ban再起動で自己テスト無しに有効化されるのを防ぐ)
JAIL_PLACED=0; INSTALL_OK=0
cleanup() {
  if [ "$INSTALL_OK" != 1 ] && [ "$JAIL_PLACED" = 1 ]; then
    rm -f "$F2B/jail.d/eigo.local"
    echo "導入が完了しなかったため、eigoのjailを外しました(既存のjailは変更していません)。原因を確認して再実行してください" >&2
  fi
}
trap cleanup EXIT
LOGDIR="$(docker inspect "$CADDY_CONTAINER" --format '{{range .Mounts}}{{if eq .Destination "/var/log/caddy"}}{{.Source}}{{end}}{{end}}' 2>/dev/null || true)"
[ -n "$LOGDIR" ] && [ -f "$LOGDIR/study.log" ] || { echo "Caddyのstudy.logが見つかりません(container=$CADDY_CONTAINER)" >&2; exit 1; }
if [ "$MODE" = ban ]; then
  iptables -S DOCKER-USER >/dev/null 2>&1 || { echo "DOCKER-USERチェーンがありません。Dockerが動いているか確認してください" >&2; exit 1; }
fi
echo "  fail2ban $(fail2ban-client --version | head -1) / study.log を確認 / 既存jail: $(fail2ban-client status 2>/dev/null | sed -n 's/.*Jail list:[[:space:]]*//p')"

echo "== 1/7 既存のeigo用ファイルをバックアップ"
BK="/var/backups/eigo-f2b/$(date +%Y%m%d_%H%M%S)"; mkdir -p "$BK"
for f in "$F2B"/filter.d/eigo-*.conf "$F2B"/action.d/eigo-*.conf "$F2B"/jail.d/eigo.local "$F2B"/eigo-allowlist.txt \
         /usr/local/sbin/eigo-f2b-* /etc/eigo-f2b.conf /etc/cron.d/eigo-f2b /etc/logrotate.d/eigo-f2b; do
  [ -e "$f" ] && cp -a --parents "$f" "$BK"/ 2>/dev/null || true
done
echo "  バックアップ先: $BK"

echo "== 2/7 ファイルを配置"
install -m 644 "$SRC"/filter.d/*.conf "$F2B"/filter.d/
install -m 644 "$SRC"/action.d/eigo-audit.conf "$F2B"/action.d/
install -m 755 "$SRC"/bin/eigo-f2b-* /usr/local/sbin/
install -d -m 755 /var/lib/eigo-f2b
# 2026-09-29: アプリへの通知(POST /api/system/security-events)用トークンをコンテナのenvから複製する
# (docker inspectで取得=.env.studyの生ファイルは読まない)。未設定なら通知は無効(監査ログのみ継続)。
# ⚠️ .env.studyへトークンを追記しただけでは反映されない: `docker restart`はenv_fileを再読込しない。
#    `docker compose up -d`でコンテナを作り直した後にこのinstall.shを実行すること(2026-09-29 Fable指摘M4)。
NOTIFY_TOKEN="$(docker exec "$APP_CONTAINER" printenv FAIL2BAN_NOTIFY_TOKEN 2>/dev/null || true)"
[ -z "$NOTIFY_TOKEN" ] && echo "  ⚠️ FAIL2BAN_NOTIFY_TOKEN未設定(アプリの.env.studyに追記後、コンテナを再作成したか確認)。管理画面への通知は無効のまま進めます" >&2
APP_PORT="$(docker inspect "$APP_CONTAINER" --format '{{(index (index .NetworkSettings.Ports "8000/tcp") 0).HostPort}}' 2>/dev/null || true)"
# 2026-09-29 Fable指摘L1: ポートが取れないまま既定値(8001)にフォールバックすると、
# 相乗りの他プロジェクトが偶然そのポートを使っていた場合にトークン付きリクエストを誤送信しうる。
# 取れなければ通知を諦める(空URL=eigo-f2b-audit/poller側がAPP_URL未設定として何もしない)。
if [ -z "$APP_PORT" ] && [ -n "$NOTIFY_TOKEN" ]; then
  echo "  ⚠️ アプリのポートをdocker inspectで特定できませんでした。通知は無効のまま進めます" >&2
  NOTIFY_TOKEN=""
fi
APP_URL=""; [ -n "$APP_PORT" ] && APP_URL="http://127.0.0.1:${APP_PORT}"
printf 'CADDY_LOG_DIR=%s\nAPP_DATA_DIR=%s\nAPP_URL=%s\nNOTIFY_TOKEN=%s\n' \
  "$LOGDIR" "$APPDATA" "$APP_URL" "$NOTIFY_TOKEN" > /etc/eigo-f2b.conf
chmod 600 /etc/eigo-f2b.conf  # NOTIFY_TOKEN(秘密情報)を含むためroot専用に(以前は644)
if [ ! -e "$F2B/eigo-allowlist.txt" ]; then
  cat > "$F2B/eigo-allowlist.txt" <<'ALLOW'
# eigo用fail2banの許可リスト(運営者が手で書く)。ここに書いたIP/CIDRはBANされない。1行1件・#でコメント。
# 例) 自宅/職場の固定IP、外部の監視サービスなど。IPを変更したら都度更新すること。
# 203.0.113.10
# 198.51.100.0/24
ALLOW
  chmod 644 "$F2B/eigo-allowlist.txt"
fi
touch /var/log/eigo-f2b-audit.log; chown root:adm /var/log/eigo-f2b-audit.log; chmod 640 /var/log/eigo-f2b-audit.log
install -m 644 "$SRC"/cron.d/eigo-f2b /etc/cron.d/eigo-f2b
install -m 644 "$SRC"/logrotate/eigo-f2b /etc/logrotate.d/eigo-f2b

echo "== 3/7 jailを生成(mode=$MODE・eigo-loginflood/eigo-loginfail/eigo-probe-trustedは常にdryrun=候補のみ・2026-09-29/10-04オーナー方針)"
python3 - "$SRC/jail.d/eigo.local.tmpl" "$F2B/jail.d/eigo.local" "$LOGDIR/study.log" "$MODE" <<'PY'
import sys
tmpl, out, logpath, mode = sys.argv[1:5]


def actions_for(m):
    audit = "eigo-audit[name=%(__name__)s, mode=" + m + "]"
    if m == "ban":
        return ("iptables-multiport[name=%(__name__)s, port=\"http,https\", protocol=tcp, chain=DOCKER-USER]\n"
                 "         " + audit)
    return audit


actions_enforce = actions_for(mode)     # eigo-probe/eigo-ratelimited: install.shの引数どおり
actions_candidate = actions_for("dryrun")  # eigo-loginflood/eigo-loginfail: 常にdryrun(様子見・2026-09-29)
lines = []
for line in open(tmpl, encoding="utf-8").read().splitlines():
    if not line.lstrip().startswith("#"):  # コメント行は置換しない(複数行の値が混ざって設定が壊れるのを防ぐ)
        line = (line.replace("__LOGPATH__", logpath)
                .replace("__ACTIONS_ENFORCE__", actions_enforce)
                .replace("__ACTIONS_CANDIDATE__", actions_candidate))
    lines.append(line)
open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
PY
chmod 644 "$F2B/jail.d/eigo.local"
JAIL_PLACED=1

echo "== 4/7 信頼IP(アカウント作成から2日以上のユーザーが直近30日にログイン成功したIP)を初回更新"
/usr/local/sbin/eigo-f2b-trusted-refresh || { echo "信頼IPの更新に失敗しました(監査ログを確認: /var/log/eigo-f2b-audit.log)" >&2; exit 1; }
echo "  信頼IP: $(grep -vc '^#' /var/lib/eigo-f2b/trusted.txt || true) 件"

echo "== 5/7 設定テスト(fail2ban-client -t)"
if ! fail2ban-client -t >/tmp/eigo-f2b-configtest.log 2>&1; then
  tail -15 /tmp/eigo-f2b-configtest.log >&2
  rm -f "$F2B/jail.d/eigo.local"
  echo "設定テストに失敗したため、eigoのjailを外して中止しました(既存のjailは変更していません)" >&2
  exit 1
fi
echo "  OK"

echo "== 6/7 フィルターが実ログに何行マッチするか(fail2ban-regex・読み取りのみ)"
for f in probe loginflood loginfail ratelimited; do
  printf '  eigo-%-12s ' "$f"
  out="$(fail2ban-regex "$LOGDIR/study.log" "$F2B/filter.d/eigo-$f.conf" 2>&1 || true)"
  { echo "$out" | grep -E '^Lines:' | sed 's/^Lines: //' | tr -d '\n'; } || true
  # 日時("ts":{EPOCH})を全行で解釈できているか(0だと、判定が時間窓に入らず何も検知しない)
  echo "  / 日時の解釈: $({ echo "$out" | grep -E '"ts":\{EPOCH\}' | grep -oE '\[[0-9]+\]' | head -1 | tr -d '[]'; } || true)行"
done
echo "  ※日時の解釈が0行なら、fail2banがCaddyの\"ts\"を読めていません(その場合は導入を中止してください)"

echo "== 7/7 fail2banに反映(サービス再起動)"
# 2026-09-29判明: `fail2ban-client reload`だと、あるjailのaction一覧に新しいアクションが
# 増える変更(dryrun→banでiptables-multiportが追加される等)が反映されないバグがある
# (fail2ban 1.0.2で確認・configファイルは正しいのに`fail2ban-client get <jail> actions`が
# 新アクションを含まないまま・エラーログも一切出ずサイレント)。`systemctl restart fail2ban`
# なら確実に反映される(検証済み: 再起動後は正しく2アクションとも登録され、実際にBANできた)。
# 再起動は数秒未満で完了し、他プロジェクトのjail(sshd等)もすぐ復帰する。
systemctl restart fail2ban
sleep 2
systemctl is-active --quiet fail2ban || { echo "fail2banサービスの再起動に失敗しました" >&2; exit 1; }
INSTALL_OK=1   # 再起動まで通った(以降の自己テストの失敗ではjailを外さない)
sleep 4
for j in eigo-probe eigo-probe-trusted eigo-loginflood eigo-loginfail eigo-ratelimited; do
  printf '  %-19s ' "$j"; { fail2ban-client status "$j" 2>&1 | grep -E 'Currently (failed|banned)' | tr -s ' \t\n' ' '; } || true; echo
done

if [ "$MODE" = ban ]; then
  # 2026-09-29判明: 固定IP(192.0.2.123)を使い回すと、過去の導入試行(dryrun<->banの
  # 切り替えを繰り返した際の同IPでのban/unban)でfail2ban内部の台帳が汚れ、新しいbanipが
  # 実際にはファイアウォールへ再投入されない(=誤ってこの自己テストが失敗する)ことがある。
  # 毎回TEST-NET-1(192.0.2.0/24)内でランダムな末尾を使い、汚れを避ける。
  TESTIP="192.0.2.$((RANDOM % 254 + 1))"
  echo "== BAN経路の自己テスト(TEST-NET-1の$TESTIPを仮BAN→DOCKER-USERを確認→解除。実在のIPには影響しない)"
  fail2ban-client set eigo-probe banip "$TESTIP" >/dev/null || echo "  ❌ fail2ban-clientのbanipに失敗(要調査)" >&2
  # 2026-09-29判明: サービス再起動直後の初回actionban(actionstart_on_demandでのチェーン作成込み)は、
  # `fail2ban-client status`がjailを「稼働中」と報告した後もしばらく(実測で6秒待っても間に合わず、
  # 10秒強で反映された)ファイアウォールへ反映されないことがある(2回目以降のbanは1秒未満で反映される)。
  # 固定sleepで賭けるのではなく、最大15秒ポーリングして確認する。
  FOUND=0
  for _ in $(seq 1 15); do
    if grep -q -- "-s $TESTIP/" <<<"$(iptables -S 2>/dev/null || true)"; then FOUND=1; break; fi
    sleep 1
  done
  if [ "$FOUND" = 1 ]; then echo "  ✅ ファイアウォールにBANルールが入った"; else echo "  ❌ BANルールが見つからない(要調査)" >&2; fi
  iptables -S DOCKER-USER | sed 's/^/  DOCKER-USER: /'
  fail2ban-client set eigo-probe unbanip "$TESTIP" >/dev/null
  if grep -q -- "-s $TESTIP/" <<<"$(iptables -S 2>/dev/null || true)"; then echo "  ❌ 解除後もルールが残っている(要調査)" >&2; else echo "  ✅ 解除でルールが消えた"; fi
fi

# 2026-10-04: 信頼IPの扱いの自己テスト(ignorecommandの向き=eigo-probeは信頼IPを免除し、eigo-probe-trustedは信頼IPだけを数える)と、
# 記録専用jailが実際にはBANしないこと(dryrunの記録だけが残り、DOCKER-USERにルールが入らない)の確認。TEST-NET-1の仮IPを使い、実在のIPには影響しない。
echo "== 信頼IPの扱いの自己テスト(終了コード: 0=無視 / 1=数える)"
TEST_T="$(mktemp)"; TEST_A="$(mktemp)"; echo "192.0.2.77" > "$TEST_T"; : > "$TEST_A"
ign() { local rc=0; EIGO_F2B_TRUSTED="$TEST_T" EIGO_F2B_ALLOW="$TEST_A" /usr/local/sbin/eigo-f2b-ignore "$@" >/dev/null 2>&1 || rc=$?; echo "$rc"; }
R1="$(ign 192.0.2.77)"; R2="$(ign 192.0.2.88)"; R3="$(ign --only-exempt 192.0.2.77)"; R4="$(ign --only-exempt 192.0.2.88)"
rm -f "$TEST_T" "$TEST_A"
[ "$R1" = 0 ] && [ "$R2" = 1 ] && [ "$R3" = 1 ] && [ "$R4" = 0 ] \
  && echo "  ✅ eigo-probe: 信頼IPは無視(0)・他は数える(1) / eigo-probe-trusted: 信頼IPだけ数える(1)・他は無視(0)" \
  || echo "  ❌ ignorecommandの向きが想定と違う(信頼IP=${R1}/他=${R2}/記録専用の信頼IP=${R3}/他=${R4}・要調査)" >&2
echo "  fail2banに登録されたignorecommand: eigo-probe=$(fail2ban-client get eigo-probe ignorecommand 2>&1 | tr -d '\n') / eigo-probe-trusted=$(fail2ban-client get eigo-probe-trusted ignorecommand 2>&1 | tr -d '\n')"
echo "== 記録専用jail(eigo-probe-trusted)の自己テスト(TEST-NET-1の仮IPで判定の記録だけが残り、実BANされないこと)"
TESTIP2="192.0.2.$((RANDOM % 254 + 1))"
# 監査ログは過去の自己テストの行も残るので、banip前の行数を控え、新しく増えた行だけを見る(前方一致・古い行での誤判定を避ける・独立照査M2)
AUD=/var/log/eigo-f2b-audit.log; BEFORE_LINES="$(wc -l < "$AUD" 2>/dev/null || echo 0)"
fail2ban-client set eigo-probe-trusted banip "$TESTIP2" >/dev/null || echo "  ❌ fail2ban-clientのbanipに失敗(jailが動いていない?・要調査)" >&2
FOUND2=0
for _ in $(seq 1 10); do
  if tail -n +"$((BEFORE_LINES + 1))" "$AUD" 2>/dev/null | grep -qF "eigo-probe-trusted ip=$TESTIP2 "; then FOUND2=1; break; fi
  sleep 1
done
[ "$FOUND2" = 1 ] && echo "  ✅ 監査ログに記録された(DRYRUN BAN eigo-probe-trusted)" || echo "  ❌ 監査ログに記録が無い(要調査)" >&2
RULES2="$(iptables -S 2>/dev/null || true)"   # here-stringで判定(grep -qとのパイプはpipefail+SIGPIPEで誤判定しうる・独立照査L1)
if grep -q -- "-s $TESTIP2/" <<<"$RULES2"; then echo "  ❌ 記録専用なのにファイアウォールにルールが入った(要調査)" >&2; else echo "  ✅ ファイアウォールにルールは入っていない(実BANしない)"; fi
fail2ban-client set eigo-probe-trusted unbanip "$TESTIP2" >/dev/null || true

echo
echo "完了(mode=$MODE)。監査ログ: /var/log/eigo-f2b-audit.log / 判定の確認: sudo bash $SRC/review.sh"
[ "$MODE" = dryrun ] && echo "※dryrunは実際にはBANしません。数日後にreview.shで内容を確認し、問題なければ install.sh ban で実BANに切り替えます。"
exit 0
