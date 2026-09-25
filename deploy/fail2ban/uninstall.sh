#!/usr/bin/env bash
# eigo用のjailを外す(fail2ban本体・sshd等の他のjail・他プロジェクトの設定は変えない)。VPS上でroot。
#   sudo bash uninstall.sh          # jailを外してreload=BANしていたIPは全て解除される
#   sudo bash uninstall.sh --purge  # さらに配置したfilter/action/スクリプト/cronも削除(監査ログ・許可リストは残す)
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "rootで実行してください(sudo)" >&2; exit 1; }
rm -f /etc/fail2ban/jail.d/eigo.local
fail2ban-client reload >/dev/null
echo "eigoのjailを外しました(BAN中のIPは解除済み)。残るjail: $(fail2ban-client status 2>/dev/null | sed -n 's/.*Jail list:[[:space:]]*//p')"
if [ "${1:-}" = "--purge" ]; then
  rm -f /etc/fail2ban/filter.d/eigo-*.conf /etc/fail2ban/action.d/eigo-audit.conf /usr/local/sbin/eigo-f2b-* /etc/cron.d/eigo-f2b /etc/logrotate.d/eigo-f2b /etc/eigo-f2b.conf
  echo "配置したファイルも削除しました(監査ログ /var/log/eigo-f2b-audit* と /etc/fail2ban/eigo-allowlist.txt は残しています)"
fi
