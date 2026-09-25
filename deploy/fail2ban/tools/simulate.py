#!/usr/bin/env python3
"""fail2banの各jailを過去のCaddyログに当てて、「誰がBANされたか」を再現する(読み取り専用・BANは実行しない)。

使い方: simulate.py <Caddyのstudyログ(.log/.gz)を含むディレクトリ or ファイル...>
- filter.d/*.conf の failregex を読み、fail2banと同じく「findtime内にmaxretry回」で判定。
- ログイン成功(POST /api/auth/login 200)のあるIPを「実ユーザー」とみなす。BAN時点の直前30日にログイン成功が
  あるIPは信頼IPとして無視される(bin/eigo-f2b-ignore)ので、BANされない側に数える。
  **信頼IPで守られずにBANされた実ユーザー(=誤BAN)が0件か**を最重要の指標として出す。
  BAN前・BAN後のどちらにログイン成功があっても数える(BAN後にログインできたなら、BAN前は同じ人だった可能性が高い)。
- IPは短縮ハッシュで出力する(生IPを画面/ログに出さない)。
しきい値は jail.d/eigo.local.tmpl と揃えること(下のJAILS)。
"""
import configparser, glob, gzip, hashlib, json, os, re, sys
from collections import defaultdict

JAILS = {  # name: (filter, maxretry, findtime秒, bantime秒)  ← jail.d/eigo.local.tmpl と同じ値
    "eigo-probe":       ("eigo-probe", 3, 600, 12 * 3600),
    "eigo-loginflood":  ("eigo-loginflood", 40, 300, 6 * 3600),
    "eigo-loginfail":   ("eigo-loginfail", 12, 600, 3600),
    "eigo-ratelimited": ("eigo-ratelimited", 60, 600, 3600),
}
HERE = os.path.dirname(os.path.abspath(__file__))
FILTER_DIR = os.path.join(HERE, "..", "filter.d")


def h(ip):
    return hashlib.sha256(("f2b-" + ip).encode()).hexdigest()[:8]


def load_filter(name):
    txt = open(os.path.join(FILTER_DIR, name + ".conf"), encoding="utf-8").read()
    common = open(os.path.join(FILTER_DIR, "eigo-common.conf"), encoding="utf-8").read()
    bot_ua = re.search(r"^_bot_ua = (.+)$", common, re.M).group(1)
    fr = re.search(r"^failregex = (.+)$", txt, re.M).group(1)
    fr = fr.replace('<HOST>', r'(?P<host>[0-9a-fA-F.:]+)')
    ign = r'"User-Agent":\["[^"]*' + bot_ua
    return re.compile(fr), re.compile(ign)


def read_lines(paths):
    files = []
    for p in paths:
        files += sorted(glob.glob(os.path.join(p, "study*"))) if os.path.isdir(p) else [p]
    for f in files:
        op = gzip.open if f.endswith(".gz") else open
        with op(f, "rt", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                yield line


TRUST_DAYS = 30  # bin/eigo-f2b-trusted-refresh の集計期間と同じ


def protected(login_times, ip, ts):
    """BAN時点の直前TRUST_DAYS日以内にログイン成功があれば、信頼IPとして無視される(=BANされない)。"""
    return any(ts - TRUST_DAYS * 86400 <= t <= ts for t in login_times.get(ip, ()))


def main(paths):
    lines = list(read_lines(paths))
    events = []  # (ts, ip, method, uri, status, raw)
    logged_in = set()
    login_times = defaultdict(list)  # ip -> ログイン成功のts
    for line in lines:
        try:
            d = json.loads(line)
        except Exception:
            continue
        r = d.get("request", {})
        if r.get("host") != "study.nyangailab.com":
            continue
        ip = r.get("remote_ip")
        if r.get("method") == "POST" and r.get("uri", "").split("?")[0] == "/api/auth/login" and d.get("status") == 200:
            logged_in.add(ip)
            login_times[ip].append(d.get("ts", 0))
    print(f"読み込み {len(lines)}行 / ログイン成功のあるIP={len(logged_in)}")
    lines.sort(key=lambda l: float(re.search(r'"ts":([0-9.]+)', l).group(1)) if re.search(r'"ts":([0-9.]+)', l) else 0)
    for name, (flt, maxretry, findtime, bantime) in JAILS.items():
        fre, ignre = load_filter(flt)
        hits = defaultdict(list)
        banned_until = {}
        bans = []  # (ts, ip)
        prot_skipped = set()
        for line in lines:
            m = fre.search(line)
            if not m or ignre.search(line):
                continue
            ts = float(re.search(r'"ts":([0-9.]+)', line).group(1))
            ip = m.group("host")
            if banned_until.get(ip, 0) > ts:
                continue  # BAN中は(実際にはファイアウォールで遮断され)ログに現れない
            if protected(login_times, ip, ts):
                prot_skipped.add(ip)
                continue  # 信頼IP(直近にログイン成功): ignorecommandで無視される
            q = hits[ip]
            q.append(ts)
            while q and ts - q[0] > findtime:
                q.pop(0)
            if len(q) >= maxretry:
                bans.append((ts, ip))
                banned_until[ip] = ts + bantime
                hits[ip] = []
        ips = {ip for _, ip in bans}
        fp = sorted(ip for ip in ips if ip in logged_in)  # 保護されなかったのに実ユーザー=誤BAN
        print(f"\n■ {name}  (maxretry={maxretry}/{findtime}s → ban {bantime // 3600}h)")
        print(f"   BANイベント={len(bans)}  distinct IP={len(ips)}  信頼IPとして守られた実ユーザー={len(prot_skipped)}件 {[h(i) for i in sorted(prot_skipped)]}")
        print(f"   誤BAN(守られなかった実ユーザー)={len(fp)}件 {[h(i) for i in fp]}")
    print("\n※ 誤BANが1件でもあるjailは、しきい値を上げるか、そのjailを見送ること。")


if __name__ == "__main__":
    main(sys.argv[1:] or ["."])
