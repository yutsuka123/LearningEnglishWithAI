#!/usr/bin/env bash
# eigo用fail2banの判定内容を確認する(読み取り専用・VPS上でroot)。
#   sudo bash review.sh          # IPは短縮ハッシュで表示(会話ログ・画面共有に生IPを出さない)
#   sudo bash review.sh --raw    # 生IPで表示(運営者本人が確認する用)
# 見るポイント: ①BAN(したはず)のIPに、実ユーザー・運営者・テスト・検索/広告のクローラーが混ざっていないか
#               ②根拠のリクエストが本当にスキャン/攻撃らしいか ③実BANに切り替える前後で件数が想定内か
set -euo pipefail
RAW=0; [ "${1:-}" = "--raw" ] && RAW=1
AUDIT=/var/log/eigo-f2b-audit.log
[ -f "$AUDIT" ] || { echo "監査ログがありません(導入前?)"; exit 1; }
echo "== 現在のjail状態"
for j in eigo-probe eigo-loginflood eigo-loginfail eigo-ratelimited; do
  printf '  %-17s ' "$j"; { fail2ban-client status "$j" 2>&1 | grep -E 'Currently (failed|banned)|Total (failed|banned)' | tr -s ' \t\n' ' '; } || true; echo
done
echo "== 信頼IP/許可リスト"
echo "  信頼IP(アカウント2日以上のユーザーが直近30日にログイン成功): $(grep -vc '^#' /var/lib/eigo-f2b/trusted.txt 2>/dev/null || true) 件 / 許可リスト: $(grep -vc '^\s*#\|^\s*$' /etc/fail2ban/eigo-allowlist.txt 2>/dev/null || true) 件"
LAST_OK="$(grep 'TRUSTED-REFRESH n=' "$AUDIT" | tail -1 || true)"
echo "  最後の信頼IP更新(成功): ${LAST_OK:-なし}"
LAST_FAIL="$(grep 'TRUSTED-REFRESH FAILED' "$AUDIT" | tail -1 || true)"
[ -n "$LAST_FAIL" ] && echo "  ⚠️ 直近の失敗: $LAST_FAIL"
# 成功記録が30分以上前なら警告(cronが止まっている・DBが読めない)
python3 - "$AUDIT" <<'PY' || true
import re, sys, time
last = None
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    m = re.match(r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) TRUSTED-REFRESH n=", line)
    if m: last = m.group(1)
if last and time.time() - time.mktime(time.strptime(last, "%Y-%m-%d %H:%M:%S")) > 1800:
    print("  ⚠️ 信頼IPの更新が30分以上止まっています(cron/DBの読み取りを確認)")
PY
echo "== 判定(BAN/BANしたはず)の集計と根拠"
python3 - "$AUDIT" "$RAW" <<'PY'
import hashlib, re, sys
from collections import defaultdict, Counter
path, raw = sys.argv[1], sys.argv[2] == "1"
def show(ip): return ip if raw else hashlib.sha256(("f2b-" + ip).encode()).hexdigest()[:8]
ev = defaultdict(list); cur = None; per_jail = Counter(); modes = Counter()
for line in open(path, encoding="utf-8", errors="replace"):
    m = re.match(r"(\S+ \S+) (DRYRUN|BAN-ON)\s+BAN\s+(\S+) ip=(\S+) failures=(\S+) bantime=(\S+)s", line)
    if m:
        cur = (m.group(1), m.group(3), m.group(4)); per_jail[m.group(3)] += 1; modes[m.group(2)] += 1
        ev[m.group(4)].append([m.group(1), m.group(3), m.group(5), []]); continue
    if line.startswith("    根拠: ") and cur and ev[cur[2]]:
        ev[cur[2]][-1][3].append(line.strip()[3:])
print("  判定件数(jail別):", dict(per_jail), " / mode別:", dict(modes), " / distinct IP:", len(ev))
for ip, lst in sorted(ev.items(), key=lambda kv: kv[1][-1][0], reverse=True)[:25]:
    t, jail, fails, evid = lst[-1]
    print(f"\n  [{show(ip)}] 最終判定 {t} {jail} (この期間の判定{len(lst)}回)")
    for e in evid[:6]: print("      " + e)
if not ev: print("  (まだ判定はありません=誤検知も無し)")
PY
echo
echo "== 直近のfail2ban本体ログ(eigo関連のBan/Ignore・最新15行)"
grep -E "eigo-(probe|loginflood|loginfail|ratelimited)" /var/log/fail2ban.log 2>/dev/null | grep -E " (Ban|Unban|Ignore) " | tail -15 | \
  { if [ "$RAW" = 1 ]; then cat; else sed -E 's/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/<ip>/g'; fi; } || true
