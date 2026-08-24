"""Gmail SMTP経由のメール送信（フルフィルメントPhase C・2026-08-25）。

`docs/TODO.md`「🏪 BASEショップ開設・フルフィルメント」で決定済みの方針
（送信元は`nyangai.lab@gmail.com`のアプリパスワードでGmail SMTP経由）に
従う。VPS自身のIPから直接SMTP送信すると迷惑メール判定されやすいため、
Gmailのサブミッションサーバー(smtp.gmail.com:465, SSL)を使う。

呼び出し側(fulfillment.py)の同期処理を止めないよう、常にbest-effortで
例外を握りつぶす（送信失敗はapp.logに記録するのみ）。
"""

from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText

from ..config import log

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def is_configured() -> bool:
    return bool(
        os.getenv("GMAIL_ADDRESS", "").strip()
        and os.getenv("GMAIL_APP_PASSWORD", "").strip()
    )


def send_email(subject: str, body: str, *, to: str = "") -> bool:
    """メールを1通送る。未設定/失敗時はFalseを返すのみ(例外は投げない)。"""
    address = os.getenv("GMAIL_ADDRESS", "").strip()
    app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    if not address or not app_password:
        log.info("mailer: GMAIL_ADDRESS/GMAIL_APP_PASSWORD未設定のため送信スキップ")
        return False
    recipient = to.strip() or os.getenv(
        "FULFILLMENT_NOTIFY_EMAIL", "").strip() or address

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = address
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as smtp:
            smtp.login(address, app_password)
            smtp.sendmail(address, [recipient], msg.as_string())
        log.info("mailer: sent subject=%r to=%s", subject, recipient)
        return True
    except Exception:
        log.warning("mailer: send failed subject=%r", subject, exc_info=True)
        return False
