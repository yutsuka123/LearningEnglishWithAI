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
echo "CADDY_LOG_DIR=$LOGDIR" > /etc/eigo-f2b.conf; chmod 644 /etc/eigo-f2b.conf
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

echo "== 3/7 jailを生成(mode=$MODE)"
python3 - "$SRC/jail.d/eigo.local.tmpl" "$F2B/jail.d/eigo.local" "$LOGDIR/study.log" "$MODE" <<'PY'
import sys
tmpl, out, logpath, mode = sys.argv[1:5]
audit = "eigo-audit[name=%(__name__)s, mode=" + mode + "]"
if mode == "ban":
    actions = ("iptables-multiport[name=%(__name__)s, port=\"http,https\", protocol=tcp, chain=DOCKER-USER]\n"
               "         " + audit)
else:
    actions = audit
lines = []
for line in open(tmpl, encoding="utf-8").read().splitlines():
    if not line.lstrip().startswith("#"):  # コメント行は置換しない(複数行の値が混ざって設定が壊れるのを防ぐ)
        line = line.replace("__LOGPATH__", logpath).replace("__ACTIONS__", actions)
    lines.append(line)
open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
PY
chmod 644 "$F2B/jail.d/eigo.local"

echo "== 4/7 信頼IP(直近30日にログイン成功したIP)を初回更新"
/usr/local/sbin/eigo-f2b-trusted-refresh
echo "  信頼IP: $(grep -vc '^#' /var/lib/eigo-f2b/trusted.txt) 件"

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
  echo "$out" | grep -E '^Lines:' | sed 's/^Lines: //' | tr -d '\n'
  # 日時("ts":{EPOCH})を全行で解釈できているか(0だと、判定が時間窓に入らず何も検知しない)
  echo "  / 日時の解釈: $(echo "$out" | grep -E '"ts":\{EPOCH\}' | grep -oE '\[[0-9]+\]' | head -1 | tr -d '[]')行"
done
echo "  ※日時の解釈が0行なら、fail2banがCaddyの\"ts\"を読めていません(その場合は導入を中止してください)"

echo "== 7/7 fail2banに反映(reload)"
fail2ban-client reload >/dev/null
sleep 4
for j in eigo-probe eigo-loginflood eigo-loginfail eigo-ratelimited; do
  printf '  %-17s ' "$j"; fail2ban-client status "$j" 2>&1 | grep -E 'Currently (failed|banned)' | tr -s ' \t\n' ' '; echo
done

if [ "$MODE" = ban ]; then
  echo "== BAN経路の自己テスト(TEST-NET-1の192.0.2.123を仮BAN→DOCKER-USERを確認→解除。実在のIPには影響しない)"
  fail2ban-client set eigo-probe banip 192.0.2.123 >/dev/null
  sleep 1
  if iptables -S | grep -q -- '-s 192.0.2.123'; then echo "  ✅ ファイアウォールにBANルールが入った"; else echo "  ❌ BANルールが見つからない(要調査)" >&2; fi
  iptables -S DOCKER-USER | sed 's/^/  DOCKER-USER: /'
  fail2ban-client set eigo-probe unbanip 192.0.2.123 >/dev/null
  iptables -S | grep -q -- '-s 192.0.2.123' && echo "  ❌ 解除後もルールが残っている(要調査)" >&2 || echo "  ✅ 解除でルールが消えた"
fi

echo
echo "完了(mode=$MODE)。監査ログ: /var/log/eigo-f2b-audit.log / 判定の確認: sudo bash $SRC/review.sh"
[ "$MODE" = dryrun ] && echo "※dryrunは実際にはBANしません。数日後にreview.shで内容を確認し、問題なければ install.sh ban で実BANに切り替えます。"
exit 0
