"""ログインの追加確認(app/services/login_stepup.py)の検査用の「偽の確認サービス」(2026-10-20・ver1.5.19)。

本物の確認サービスは別リポジトリ(非公開)にある。ここにあるのは、アプリ側が相手に求める**内部APIの形だけ**
を同じ形で返す検査専用のスタブ(何も聞かない・何も採点しない)。検査(check_login_stepup.py / check_login_stepup_ui.py)
がimportして使う。共有キーは検査のたびに作る使い捨てのダミーで、本物のキーではない。
"""
from __future__ import annotations

import json
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class Gate:
    """偽の確認サービスの状態。tickets[t] = {ip, host, bind, mode, outcome}。"""

    def __init__(self) -> None:
        self.key = "dummy-" + secrets.token_hex(24)
        self.tickets: dict[str, dict] = {}
        self.log: list[dict] = []          # 受けた要求(path/headers/body)
        self.override: str | None = None   # 相手の誤動作を真似る(下の各値)
        self.valid_cookie = "gatetest=OK"  # このCookieがあるとbeginはskipを返す
        self.last_accepted: bool | None = None
        # 本物は常にSecure。ブラウザ検査(http://127.0.0.1)でWebKitがSecureのCookieを保存しない都合で、
        # その検査だけFalseにする(アプリは相手の値をそのまま使うので、検査の意味は変わらない)。
        self.cookie_secure = True

    # --- 検査側の操作 ---
    def ticket_from_src(self, src: str) -> str:
        return parse_qs(urlparse(src).query).get("c", [""])[0]

    def complete(self, ticket: str, ok: bool) -> None:
        """iframeの画面を終えたことにする(合否を決める)。"""
        self.tickets[ticket]["outcome"] = bool(ok)

    def calls(self, path: str) -> list[dict]:
        return [x for x in self.log if x["path"] == path]


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):            # 標準出力を汚さない
        pass

    def _send(self, status: int, obj) -> None:
        raw = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):                    # noqa: N802
        gate: Gate = self.server.gate     # type: ignore[attr-defined]
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            body = {}
        headers = {k.lower(): v for k, v in self.headers.items()}
        gate.log.append({"path": self.path, "headers": headers, "body": body})
        # 本物と同じ: キー無し/違い/X-Forwarded-For付きは存在しないパスと同じ404
        if ("x-forwarded-for" in headers
                or headers.get("authorization") != "Bearer " + gate.key):
            return self._send(404, {"detail": "Not Found"})
        if gate.override == "http500":
            return self._send(500, {"error": "boom"})
        if gate.override == "slow":
            time.sleep(3.0)
        if self.path == "/internal/begin":
            return self._begin(gate, body)
        if self.path == "/internal/redeem":
            return self._redeem(gate, body)
        return self._send(404, {"detail": "Not Found"})

    def _begin(self, gate: Gate, body: dict) -> None:
        for k in ("ip", "host", "bind", "cookie"):
            if not isinstance(body.get(k), str) or (k != "cookie" and not body[k]):
                return self._send(400, {"error": "bad_request"})
        skip = gate.valid_cookie in body["cookie"]
        t = secrets.token_urlsafe(16)
        gate.tickets[t] = {
            "ip": body["ip"], "host": body["host"], "bind": body["bind"],
            "mode": "skip" if skip else "ask", "outcome": True if skip else None}
        o = gate.override
        if o == "no_mode":
            return self._send(200, {})
        if o == "bad_ticket_chars":
            return self._send(200, {"mode": "skip", "ticket": "a b;c"})
        if skip:
            return self._send(200, {"mode": "skip", "ticket": t})
        src = {"bad_src_slashes": "//evil.example/x",
               "bad_src_absolute": "https://evil.example/x",
               "bad_src_backslash": "/ok\\evil",
               }.get(o or "", f"/g-stub/e?c={t}")
        bind = {"name": "gbstub", "value": secrets.token_urlsafe(16), "max_age": 300, "path": "/g-stub",
                "httponly": True, "samesite": "lax", "secure": gate.cookie_secure}
        if o == "no_bind_cookie":
            return self._send(200, {"mode": "ask", "src": src})
        if o == "bad_bind_cookie":
            bind["value"] = "bad;value"
        elif o == "reserved_bind_cookie":
            bind["name"] = "ela_session"
        return self._send(200, {"mode": "ask", "src": src, "bind_cookie": bind})

    def _redeem(self, gate: Gate, body: dict) -> None:
        t = gate.tickets.pop(body.get("ticket"), None)    # 成否にかかわらず1回で消える
        gate.last_accepted = body.get("accepted")
        if (not t or t["ip"] != body.get("ip") or t["host"] != body.get("host")
                or t["bind"] != body.get("bind")):
            return self._send(200, {"ok": False})
        ok = t["outcome"] is True
        if not ok:
            return self._send(200, {"ok": False})
        if t["mode"] == "skip":
            return self._send(200, {"ok": True, "cookie": None})
        cookie = {"name": "gtest", "value": "signed" + secrets.token_hex(8),
                  "max_age": 2592000, "path": "/", "httponly": True,
                  "samesite": "lax", "secure": gate.cookie_secure}
        if gate.override == "bad_cookie_value":
            cookie["value"] = "va;lue"
        elif gate.override == "bad_cookie_missing":
            del cookie["samesite"]
        elif gate.override == "bad_cookie_name":
            cookie["name"] = "bad name"
        elif gate.override == "bad_cookie_age":
            cookie["max_age"] = -1
        elif gate.override == "reserved_cookie_name":
            cookie["name"] = "ela_session"
        return self._send(200, {"ok": True, "cookie": cookie})


def serve(gate: Gate | None = None, port: int = 0):
    """スタブを別スレッドで起動する。戻り値=(gate, url, server)。止めるときは server.shutdown()。"""
    gate = gate or Gate()
    srv = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    srv.gate = gate                       # type: ignore[attr-defined]
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return gate, f"http://127.0.0.1:{srv.server_address[1]}", srv
