from __future__ import annotations

"""
Alert notifier with real delivery channels.

Supported channels:
  - file       JSONL outbox (always works, the fallback)
  - dingtalk   DingTalk / WeChat Work webhook
  - email      SMTP email
  - stdout     Print to stdout (for container log aggregation)

Configure webhooks in configs/app.yaml or via environment variables:
  DINGTALK_WEBHOOK_URL
  SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS / SMTP_FROM / SMTP_TO
"""

from __future__ import annotations

import json
import os
import smtplib
import ssl
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any


class Notifier:
    """Send alerts through one or more channels."""

    def __init__(self, outbox: str | Path = "data/alerts/outbox.jsonl") -> None:
        self.outbox = Path(outbox)
        self.outbox.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, channel: str, target: str, title: str, body: str) -> Path:
        """Send alert to a channel. Always writes to the outbox as audit trail.

        channel: 'file' | 'dingtalk' | 'email' | 'stdout'
        """
        self._write_outbox(channel, target, title, body)

        if channel == "dingtalk":
            self._send_dingtalk(title, body)
        elif channel == "email":
            self._send_email(target, title, body)
        elif channel == "stdout":
            print(f"[ALERT] [{channel}] {title}: {body}")

        return self.outbox

    # ------------------------------------------------------------------
    # Outbox (audit trail)
    # ------------------------------------------------------------------

    def _write_outbox(self, channel: str, target: str, title: str, body: str) -> None:
        payload = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "channel": channel,
            "target": target,
            "title": title,
            "body": body,
        }
        with self.outbox.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            fp.write("\n")

    # ------------------------------------------------------------------
    # DingTalk / WeChat Work webhook
    # ------------------------------------------------------------------

    def _send_dingtalk(self, title: str, body: str) -> None:
        webhook_url = os.environ.get("DINGTALK_WEBHOOK_URL", "")
        if not webhook_url:
            self._write_outbox("stderr", "", "dingtalk: no webhook url configured",
                               f"DINGTALK_WEBHOOK_URL env var not set. Skipping alert: {title}")
            return

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": f"## {title}\n\n{body}\n\n> CDC Warehouse Platform @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            },
        }
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(webhook_url, data=data,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = resp.read().decode("utf-8")
                print(f"[notifier] dingtalk response: {result}")
        except Exception as exc:
            print(f"[notifier] dingtalk send failed: {exc}")

    # ------------------------------------------------------------------
    # SMTP email
    # ------------------------------------------------------------------

    def _send_email(self, to_address: str, subject: str, body: str) -> None:
        smtp_host = os.environ.get("SMTP_HOST", "")
        if not smtp_host:
            self._write_outbox("stderr", "", "email: no SMTP configured",
                               f"SMTP_HOST env var not set. Skipping email alert: {subject}")
            return

        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER", "")
        smtp_pass = os.environ.get("SMTP_PASS", "")
        from_addr = os.environ.get("SMTP_FROM", smtp_user or "cdc-warehouse@example.com")

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_address

        try:
            ctx = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.starttls(context=ctx)
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.sendmail(from_addr, [to_address], msg.as_string())
        except Exception as exc:
            print(f"[notifier] email send failed: {exc}")
