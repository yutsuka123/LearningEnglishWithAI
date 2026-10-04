"""fail2banの「信頼IPはBANしないが探索は記録する」+「探索でBANされたIPは人間に数えない」の検査(2026-10-04)。

  .venv/bin/python scripts/check_f2b_trusted_probe.py     # 0=全部OK(本番・外部には触れない・.envの無い環境推奨)

1. bin/eigo-f2b-ignore の向き: 通常モード=許可リスト/信頼IPを無視(0)・他は数える(1)、
   --only-exempt(記録専用jail用)=逆(信頼IP/許可リストだけを数える=1・他は無視=0)。解釈できないIP・ファイル欠落は無視(0)。
2. jail.d/eigo.local.tmpl: eigo-probeは信頼IPを免除(--allow-onlyではない)、eigo-probe-trustedは同じフィルター・
   --only-exempt・常にdryrun(__ACTIONS_CANDIDATE__)、4種の既存jailの設定は変わっていない。
3. アプリ: 通知の受け口がeigo-probe-trustedを受け付ける・eigo-probeのban通知でそのIPの訪問記録にbot印(MARK_SCANNER_IP)が付く
   (登録試行・自分の端末・他のIP・印済みの行は対象外)・eigo-probe-trustedでは付かない・unbanでは付かない・BAN後に戻ってきた
   同じIPの訪問(is_scanner_ip)にも付く・未知のjailは拒否。
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_TMP = tempfile.mkdtemp(prefix="check_f2b_trusted_")
import atexit  # noqa: E402
import shutil  # noqa: E402

atexit.register(shutil.rmtree, _TMP, ignore_errors=True)
os.environ["DATA_DIR"] = _TMP
os.environ["ALLOW_FRESH_DB"] = "1"
os.environ["OPENAI_API_KEY"] = "sk-test-not-a-real-key"
os.environ["MULTIUSER"] = "0"
sys.path.insert(0, str(ROOT))

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("  OK   " if cond else "  FAIL ") + name + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


print("== 1. eigo-f2b-ignore の向き(終了コード 0=無視 / 1=数える)")
ALLOW, TRUSTED = Path(_TMP) / "allow.txt", Path(_TMP) / "trusted.txt"
ALLOW.write_text("# 運営者\n198.51.100.0/24  # オフィス\n", encoding="utf-8")
TRUSTED.write_text("# 信頼IP\n203.0.113.5\n", encoding="utf-8")
SCRIPT = ROOT / "deploy" / "fail2ban" / "bin" / "eigo-f2b-ignore"


def ign(*args: str, allow: Path = ALLOW, trusted: Path = TRUSTED) -> int:
    env = {**os.environ, "EIGO_F2B_ALLOW": str(allow), "EIGO_F2B_TRUSTED": str(trusted)}
    return subprocess.run([sys.executable, str(SCRIPT), *args], env=env).returncode


CASES = [
    # (引数, 期待, 説明)
    (("203.0.113.5",), 0, "通常: 信頼IPは無視"),
    (("198.51.100.77",), 0, "通常: 許可リスト(CIDR)は無視"),
    (("192.0.2.9",), 1, "通常: それ以外は数える"),
    (("--allow-only", "203.0.113.5"), 1, "通常(--allow-only): 信頼IPは数える(互換)"),
    (("--allow-only", "198.51.100.77"), 0, "通常(--allow-only): 許可リストは無視(互換)"),
    (("--only-exempt", "203.0.113.5"), 1, "記録専用: 信頼IPを数える"),
    (("--only-exempt", "198.51.100.77"), 1, "記録専用: 許可リストのIPを数える"),
    (("--only-exempt", "192.0.2.9"), 0, "記録専用: それ以外は無視"),
    (("not-an-ip",), 0, "通常: 解釈できないIPは無視"),
    (("--only-exempt", "not-an-ip"), 0, "記録専用: 解釈できないIPは無視"),
    (("--only-exempt",), 0, "記録専用: IP引数なしは無視"),
]
for args, want, desc in CASES:
    got = ign(*args)
    check(f"{desc}  {' '.join(args)} → {got}", got == want, f"want {want}")
missing = Path(_TMP) / "nothing.txt"
# 信頼IPは単一アドレスの完全一致のみ(自動生成ファイルに広い範囲が紛れても全員を免除しない)
BROAD = Path(_TMP) / "trusted_broad.txt"
BROAD.write_text("0.0.0.0/0\n198.18.0.0/16\n203.0.113.5\n", encoding="utf-8")
check("信頼IPファイルのCIDR(0.0.0.0/0)は無効=他のIPは数える", ign("192.0.2.9", trusted=BROAD) == 1)
check("信頼IPファイルの単一アドレスは有効", ign("203.0.113.5", trusted=BROAD) == 0)
check("許可リストのCIDRは有効(運営者が手で書く)", ign("198.51.100.200") == 0)
# 想定外の失敗(信頼IPファイルがディレクトリ等で読めない)=無視(0)+監査ログに痕跡
AUD = Path(_TMP) / "audit.log"
bad = Path(_TMP) / "trusted_dir"; bad.mkdir()
rc = subprocess.run([sys.executable, str(SCRIPT), "203.0.113.5"], env={**os.environ, "EIGO_F2B_ALLOW": str(ALLOW), "EIGO_F2B_TRUSTED": str(bad), "EIGO_F2B_AUDIT": str(AUD)}).returncode
check("想定外の失敗は無視(0)=BANしない側", rc == 0, str(rc))
check("想定外の失敗は監査ログに痕跡が残る(IGNORE-CMD-ERROR)", AUD.exists() and "IGNORE-CMD-ERROR" in AUD.read_text(encoding="utf-8"))
check("ファイルが無いとき: 通常は数える(1)", ign("203.0.113.5", allow=missing, trusted=missing) == 1)
check("ファイルが無いとき: 記録専用は無視(0)", ign("--only-exempt", "203.0.113.5", allow=missing, trusted=missing) == 0)

print("== 2. jail設定テンプレート")
tmpl = (ROOT / "deploy" / "fail2ban" / "jail.d" / "eigo.local.tmpl").read_text(encoding="utf-8")
sections: dict[str, dict[str, str]] = {}
cur = None
for line in tmpl.splitlines():
    if line.lstrip().startswith("#") or not line.strip():
        continue
    if line.startswith("["):
        cur = line.strip("[] ")
        sections[cur] = {}
    elif cur and "=" in line:
        k, v = line.split("=", 1)
        sections[cur][k.strip()] = v.strip()
check("jailは5種", set(sections) == {"eigo-probe", "eigo-probe-trusted", "eigo-loginflood", "eigo-loginfail", "eigo-ratelimited"}, str(sorted(sections)))
p, t = sections["eigo-probe"], sections["eigo-probe-trusted"]
check("eigo-probe: 信頼IPも免除(通常モード・--allow-onlyではない)", p["ignorecommand"].endswith("eigo-f2b-ignore <ip>"), p["ignorecommand"])
check("eigo-probe: 実BANの種別(ENFORCE)のまま", p["action"] == "__ACTIONS_ENFORCE__")
check("eigo-probe-trusted: 同じフィルター", t["filter"] == p["filter"] == "eigo-probe")
check("eigo-probe-trusted: --only-exempt", t["ignorecommand"].endswith("eigo-f2b-ignore --only-exempt <ip>"), t["ignorecommand"])
check("eigo-probe-trusted: 常にdryrun(CANDIDATE)=BANしない", t["action"] == "__ACTIONS_CANDIDATE__")
check("eigo-probe-trusted: しきい値はeigo-probeと同じ", (t["maxretry"], t["findtime"]) == (p["maxretry"], p["findtime"]) == ("3", "10m"))
check("eigo-probe-trusted: ignoreip(ローカル/Docker/プライベート)も同じ", t["ignoreip"] == p["ignoreip"])
check("他のjailの設定は不変(loginflood=60/5m・CANDIDATE)", sections["eigo-loginflood"]["maxretry"] == "60" and sections["eigo-loginflood"]["action"] == "__ACTIONS_CANDIDATE__")
check("他のjailの設定は不変(ratelimited=60/10m・ENFORCE)", sections["eigo-ratelimited"]["maxretry"] == "60" and sections["eigo-ratelimited"]["action"] == "__ACTIONS_ENFORCE__")
install = (ROOT / "deploy" / "fail2ban" / "install.sh").read_text(encoding="utf-8")
check("install.shの状態表示に記録専用jailが含まれる", "eigo-probe eigo-probe-trusted eigo-loginflood" in install)

print("== 3. アプリ: 通知の受け口と探索IPの印")
from app.database import db, init_db  # noqa: E402
from app.routers import system  # noqa: E402
from app.services import visitor_kind as vk  # noqa: E402
from fastapi import HTTPException  # noqa: E402

init_db()
SCAN, TRUST, OTHER = "198.18.0.10", "198.18.0.20", "198.18.0.30"
with db() as conn:
    def visit(ip, *, kind=None, internal=0, mark=0):
        conn.execute(
            "INSERT INTO landing_visits (ip, path, user_agent, guest_sid, is_internal, bot_mark, kind) "
            "VALUES (?, '/', 'Mozilla/5.0 (Windows NT 10.0) Chrome/120', 'g', ?, ?, ?)",
            (ip, internal, mark, kind or "visit"))
    visit(SCAN); visit(SCAN); visit(SCAN, internal=1); visit(SCAN, kind="signup"); visit(SCAN, mark=vk.MARK_OTHER_BOT)
    visit(TRUST); visit(OTHER)


def ev(ip, jail, action="ban", mode="ban", failures=3):
    return system.ingest_security_event(system.SecurityEventIn(
        ip=ip, jail=jail, action=action, mode=mode, failures=failures, bantime_seconds=43200, evidence="x"))


def marks(ip):
    with db() as conn:
        return [(r["kind"] or "visit", r["is_internal"], r["bot_mark"]) for r in conn.execute(
            "SELECT kind, is_internal, bot_mark FROM landing_visits WHERE ip = ? ORDER BY id", (ip,))]


r = ev(TRUST, "eigo-probe-trusted", mode="dryrun")
check("eigo-probe-trusted の通知を受け付ける(印は付けない)", r.get("ok") is True and r.get("marked_visits") == 0, str(r))
check("信頼IPの探索検知では訪問記録に印が付かない", all(m[2] == 0 for m in marks(TRUST)), str(marks(TRUST)))
with db() as conn:
    check("is_scanner_ip: 信頼IPの検知(eigo-probe-trusted)だけでは偽", vk.is_scanner_ip(conn, TRUST) is False)
    check("is_scanner_ip: 記録の無いIPは偽", vk.is_scanner_ip(conn, OTHER) is False)
r = ev(SCAN, "eigo-probe", "unban")
check("eigo-probe の unban では印を付けない", r.get("marked_visits") == 0 and all(m[2] in (0, vk.MARK_OTHER_BOT) for m in marks(SCAN)), str(marks(SCAN)))
r = ev(SCAN, "eigo-probe", "ban")
m = marks(SCAN)
check("eigo-probe の ban で、まだ印の無い通常の訪問2件に印(6)が付く", r.get("marked_visits") == 2 and sum(1 for x in m if x[2] == vk.MARK_SCANNER_IP) == 2, f"{r} {m}")
check("自分の端末の行・登録試行の行・既に別の印がある行は変えない",
      (("visit", 1, 0) in m) and (("signup", 0, 0) in m) and (("visit", 0, vk.MARK_OTHER_BOT) in m), str(m))
check("他のIPの訪問は変えない", all(x[2] == 0 for x in marks(OTHER)) and all(x[2] == 0 for x in marks(TRUST)))
with db() as conn:
    check("is_scanner_ip: eigo-probeでBANされたIPは真", vk.is_scanner_ip(conn, SCAN) is True)
r = ev(SCAN, "eigo-probe", "ban")
check("同じ通知を55秒以内に再送しても重複しない(既存の挙動)", r.get("deduped") is True, str(r))
try:
    ev(OTHER, "sshd")
    check("未知のjail(sshd)は拒否", False)
except HTTPException:
    check("未知のjail(sshd)は拒否", True)
with db() as conn:
    n = conn.execute("SELECT COUNT(*) FROM security_events WHERE jail = 'eigo-probe-trusted'").fetchone()[0]
check("security_eventsにeigo-probe-trustedが記録される(mode=ban拒否分は除く)", n == 1, str(n))
# 手動のbanip(failures=0・自己テスト/運営者の確認手順)は探索の検知ではない=印を付けない(携帯回線等の共有IPの巻き込み防止)
MANUAL = "198.18.0.40"
with db() as conn:
    conn.execute("INSERT INTO landing_visits (ip, path, user_agent, guest_sid, is_internal, bot_mark) VALUES (?, '/', 'Mozilla/5.0 Chrome/120', 'g', 0, 0)", (MANUAL,))
r = ev(MANUAL, "eigo-probe", "ban", failures=0)
check("手動BAN(failures=0)では印を付けない・is_scanner_ipも偽", r.get("marked_visits") == 0 and marks(MANUAL) == [("visit", 0, 0)], f"{r} {marks(MANUAL)}")
with db() as conn:
    check("is_scanner_ip: 手動BAN(failures=0)だけでは偽", vk.is_scanner_ip(conn, MANUAL) is False)
# 30日より前のBANは対象外(動的IP・携帯回線の持ち主が変わっている可能性)
OLD = "198.18.0.50"
with db() as conn:
    conn.execute("INSERT INTO security_events (ip, jail, action, mode, failures, bantime_seconds, evidence, created_at) VALUES (?, 'eigo-probe', 'ban', 'ban', 5, 43200, 'x', datetime('now', '-40 days'))", (OLD,))
    check("is_scanner_ip: 40日前のBANは偽(期限30日)", vk.is_scanner_ip(conn, OLD) is False)
    conn.execute("INSERT INTO security_events (ip, jail, action, mode, failures, bantime_seconds, evidence, created_at) VALUES (?, 'eigo-probe', 'ban', 'ban', 5, 43200, 'x', datetime('now', '-10 days'))", (OLD,))
    check("is_scanner_ip: 10日前の実検知のBANは真", vk.is_scanner_ip(conn, OLD) is True)
# 記録専用jailはdryrunのみ受け付ける(実BAN扱いの行を作らない)
try:
    ev(TRUST, "eigo-probe-trusted", "ban", "ban")
    check("eigo-probe-trusted を mode=ban で送っても拒否", False)
except HTTPException:
    check("eigo-probe-trusted を mode=ban で送っても拒否", True)
# 印付けが失敗しても、BANの記録(INSERT)は消さない
_orig = vk.mark_scanner_ip
vk.mark_scanner_ip = lambda conn, ip: (_ for _ in ()).throw(RuntimeError("boom"))
try:
    r = ev("198.18.0.60", "eigo-probe", "ban")
    with db() as conn:
        kept = conn.execute("SELECT COUNT(*) FROM security_events WHERE ip = '198.18.0.60'").fetchone()[0]
    check("印付けが例外でも、通知(BANの記録)は保存される", r.get("ok") is True and kept == 1, f"{r} kept={kept}")
finally:
    vk.mark_scanner_ip = _orig
main_src = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
check("訪問の記録時にis_scanner_ipで印を付けている(main.py)", "visitor_kind.is_scanner_ip(conn, client_ip)" in main_src and "MARK_SCANNER_IP" in main_src)

print()
if FAILS:
    print(f"❌ 失敗 {len(FAILS)} 件: " + ", ".join(FAILS))
    raise SystemExit(1)
print("✅ すべて成功")
