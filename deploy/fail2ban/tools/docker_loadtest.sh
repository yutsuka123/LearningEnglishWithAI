#!/usr/bin/env bash
# fail2ban(eigo用)の設定が「実際に起動できるか」を、使い捨てのDockerコンテナ(Ubuntu 24.04=本番VPSと同じfail2ban 1.0.2)で確認する。
# 本番には一切触れない(ネットワークもファイルも隔離されたコンテナの中だけ)。2026-11-03追加。
#
# 背景: 2026-11-02 03:02、手動ブロック用フィルター(eigo-manual)の failregex に <HOST> が無く、
#   fail2ban 1.0.2 が "No failure-id group" で起動に失敗した(`fail2ban-client -t` の設定テストは通ってしまう)。
#   → 設定テストだけでは見つからない種類の不具合なので、jailを実際に読み込んで起動し、BAN/解除まで通す。
#
# 使い方(Macなど、Dockerが動く作業機で): bash deploy/fail2ban/tools/docker_loadtest.sh
#   確認すること: ①全jail(eigo-* 10本)が起動する ②eigo-manual-* の5本でbanip→DOCKER-USERにルールが入り、unbanipで消える
#                ③永久ブロック(eigo-manual-perm)のbantimeが-1 ④fail2ban.logにERRORが無い
#   対照実験(わざと旧い壊れた設定で起動に失敗することを確認=この検査が不具合を検出できる証拠):
#     OLD_FILTER=/path/to/old/eigo-manual.conf bash deploy/fail2ban/tools/docker_loadtest.sh --expect-fail
#   終了コード: 0=期待どおり(通常=すべて合格 / --expect-fail=起動に失敗した)、1=期待と違う
set -euo pipefail

if [ "${1:-}" != "--inner" ]; then
  HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  EXTRA=()
  if [ -n "${OLD_FILTER:-}" ]; then EXTRA+=(-v "$OLD_FILTER:/oldfilter.conf:ro" -e USE_OLD_FILTER=1); fi
  docker run --rm --cap-add NET_ADMIN --cap-add NET_RAW ${EXTRA[@]+"${EXTRA[@]}"} \
    -e EXPECT_FAIL="$([ "${1:-}" = "--expect-fail" ] && echo 1 || echo 0)" \
    -v "$HERE:/src:ro" ubuntu:24.04 bash /src/tools/docker_loadtest.sh --inner
  exit $?
fi

# ---- ここから使い捨てコンテナの中 ----
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq >/dev/null 2>&1
apt-get install -y -qq fail2ban iptables python3 >/dev/null 2>&1
update-alternatives --set iptables /usr/sbin/iptables-legacy >/dev/null 2>&1 || true   # コンテナでnftが使えない環境のため(判定内容には影響しない)
echo "fail2ban: $(fail2ban-client --version | head -1)"
SRC=/src; F2B=/etc/fail2ban
FAIL=0; ok() { echo "  ✅ $*"; }; ng() { echo "  ❌ $*"; FAIL=1; }

# install.sh の「2/7 ファイルを配置」「3/7 jailを生成」と同じ手順(MODE=ban)
install -m 644 "$SRC"/filter.d/*.conf "$F2B"/filter.d/
install -m 644 "$SRC"/action.d/eigo-audit.conf "$F2B"/action.d/
install -m 755 "$SRC"/bin/eigo-f2b-* /usr/local/sbin/
if [ "${USE_OLD_FILTER:-0}" = 1 ]; then install -m 644 /oldfilter.conf "$F2B"/filter.d/eigo-manual.conf; echo "  (対照実験: 旧フィルターを使用)"; fi
install -d -m 755 /var/lib/eigo-f2b
: > /var/lib/eigo-f2b/manual.log; : > /var/lib/eigo-f2b/trusted.txt
touch /var/log/eigo-f2b-audit.log
printf '# test\n' > "$F2B/eigo-allowlist.txt"
printf 'CADDY_LOG_DIR=/var/log/caddy\nAPP_DATA_DIR=/data\nAPP_URL=\nNOTIFY_TOKEN=\n' > /etc/eigo-f2b.conf
mkdir -p /var/log/caddy
for i in $(seq 1 5); do printf '{"ts":%s.0,"request":{"host":"study.nyangailab.com","uri":"/","remote_ip":"198.51.100.%s"},"status":200}\n' "$(date +%s)" "$i"; done > /var/log/caddy/study.log
iptables -N DOCKER-USER   # 本番のDockerが作るチェーンの代わり

python3 - "$SRC/jail.d/eigo.local.tmpl" "$F2B/jail.d/eigo.local" /var/log/caddy/study.log ban <<'PY'
import sys
tmpl, out, logpath, mode = sys.argv[1:5]
def actions_for(m):
    audit = "eigo-audit[name=%(__name__)s, mode=" + m + "]"
    if m == "ban":
        return ("iptables-multiport[name=%(__name__)s, port=\"http,https\", protocol=tcp, chain=DOCKER-USER]\n         " + audit)
    return audit
actions_enforce = actions_for(mode); actions_candidate = actions_for("dryrun")
actions_manual = "iptables-multiport[name=%(__name__)s, port=\"http,https\", protocol=tcp, chain=DOCKER-USER]"
lines = []
for line in open(tmpl, encoding="utf-8").read().splitlines():
    if not line.lstrip().startswith("#"):
        line = (line.replace("__LOGPATH__", logpath).replace("__ACTIONS_ENFORCE__", actions_enforce)
                .replace("__ACTIONS_CANDIDATE__", actions_candidate).replace("__ACTIONS_MANUAL__", actions_manual))
    lines.append(line)
open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
PY
# コンテナにはsshdのログが無いので、既定のsshd jailだけ無効にする(eigo用の判定とは無関係)
printf '[sshd]\nenabled = false\n' > "$F2B/jail.d/zz-disable-sshd.local"

echo "== 設定テスト(fail2ban-client -t・本番の導入手順の5/7と同じ)"
if fail2ban-client -t >/tmp/cfgtest.log 2>&1; then ok "設定テストOK(※これは今回の不具合を検出できない)"; else ng "設定テスト失敗"; tail -5 /tmp/cfgtest.log; fi

echo "== 実際に起動(本番の導入手順の7/7と同じ=サービス起動)"
START_OK=1
fail2ban-client -x start >/tmp/start.log 2>&1 || START_OK=0
sleep 4
JAILS="$(fail2ban-client status 2>/dev/null | sed -n 's/.*Jail list:[[:space:]]*//p' || true)"
echo "  起動したjail: ${JAILS:-なし}"
WANT="eigo-probe eigo-probe-trusted eigo-loginflood eigo-loginfail eigo-ratelimited eigo-manual-1h eigo-manual-24h eigo-manual-7d eigo-manual-30d eigo-manual-perm"
MISS=""; for j in $WANT; do fail2ban-client status "$j" >/dev/null 2>&1 || MISS="$MISS $j"; done

if [ "${EXPECT_FAIL:-0}" = 1 ]; then
  echo "== 対照実験の判定(起動に失敗するのが期待)"
  grep -h -E "ERROR" /var/log/fail2ban.log 2>/dev/null | head -3 | cut -c1-200 || true
  if [ "$START_OK" = 0 ] || [ -n "$MISS" ]; then echo "  ✅ 期待どおり、壊れた設定では起動に失敗した(この検査は不具合を検出できる)"; exit 0; fi
  echo "  ❌ 壊れた設定のはずが全jailが起動した(検査が不具合を検出できていない)"; exit 1
fi

[ "$START_OK" = 1 ] && [ -z "$MISS" ] && ok "10本すべて起動" || ng "起動していないjail:${MISS:- (全体の起動に失敗)}"
grep -h -E " ERROR " /var/log/fail2ban.log 2>/dev/null | head -5 | cut -c1-220 || true
ERRN="$(grep -c -E " ERROR " /var/log/fail2ban.log 2>/dev/null || true)"
[ "${ERRN:-0}" -eq 0 ] && ok "fail2ban.log にERRORなし" || ng "fail2ban.log にERROR ${ERRN}件"

echo "== 手動ブロック5本: banip→DOCKER-USERにルール→unbanipで消える(TEST-NET-1の仮IP)"
n=0
for j in 1h 24h 7d 30d perm; do
  n=$((n + 1)); TIP="192.0.2.$((10 + n))"
  fail2ban-client set "eigo-manual-$j" banip "$TIP" >/dev/null 2>&1 || ng "eigo-manual-$j: banipに失敗"
  FOUND=0; for _ in $(seq 1 10); do iptables -S 2>/dev/null | grep -q -- "-s $TIP/" && { FOUND=1; break; }; sleep 1; done
  [ "$FOUND" = 1 ] && ok "eigo-manual-$j: ルールが入った" || ng "eigo-manual-$j: ルールが入らない"
  fail2ban-client set "eigo-manual-$j" unbanip "$TIP" >/dev/null 2>&1 || true
  sleep 1
  iptables -S 2>/dev/null | grep -q -- "-s $TIP/" && ng "eigo-manual-$j: 解除後もルールが残る" || ok "eigo-manual-$j: 解除でルールが消えた"
done
echo "== bantime(1h=3600 / 24h=86400 / 7d=604800 / 30d=2592000 / perm=-1)"
for pair in 1h:3600 24h:86400 7d:604800 30d:2592000 perm:-1; do
  j="${pair%%:*}"; want="${pair##*:}"; got="$(fail2ban-client get "eigo-manual-$j" bantime 2>/dev/null | tr -d '[:space:]')"
  [ "$got" = "$want" ] && ok "eigo-manual-$j bantime=$got" || ng "eigo-manual-$j bantime=$got (期待 $want)"
done
echo
[ "$FAIL" = 0 ] && { echo "✅ 全項目合格"; exit 0; } || { echo "❌ 不合格あり"; exit 1; }
