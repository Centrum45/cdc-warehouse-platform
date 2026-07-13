from __future__ import annotations

"""
Alert notifier with production-oriented delivery channels.

Supported channels:
  - file       JSONL outbox, always safe as audit trail
  - stdout     container / systemd log aggregation
  - email      SMTP email
  - dingtalk   DingTalk webhook
  - wechat     WeChat Work webhook
  - feishu     Feishu webhook
"""

import json
import os
import smtplib
import ssl
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Iterable, Optional, Union

WEBHOOK_CHANNELS = {"dingtalk", "wechat", "feishu"}


class Notifier:
    """Send alerts through one or more configured channels."""

    def __init__(self, outbox: Optional[Union[str, Path]] = None) -> None:
        config = self._alert_config()
        outbox_path = outbox or os.environ.get("ALERT_OUTBOX") or config.get("outbox") or "data/alerts/outbox.jsonl"
        self.outbox = Path(outbox_path)
        self.outbox.parent.mkdir(parents=True, exist_ok=True)

    def send(self, channel: str, target: str, title: str, body: str) -> Path:
        """Send one alert. Delivery failure never hides the outbox record."""
        channel = (channel or "file").strip().lower()
        target = self._default_target(channel, target)
        self._write_outbox(channel, target, title, body)

        if channel in WEBHOOK_CHANNELS:
            self._send_webhook(channel, title, body)
        elif channel == "email":
            self._send_email(target, title, body)
        elif channel == "stdout":
            print(f"[ALERT] [{channel}] {title}: {body}")

        return self.outbox

    def send_default(self, title: str, body: str, target: str = "") -> Path:
        """Send alert to ALERT_CHANNELS/configured channels."""
        for channel in self.default_channels():
            self.send(channel, target, title, body)
        return self.outbox

    def default_channels(self) -> list[str]:
        config = self._alert_config()
        raw = os.environ.get("ALERT_CHANNELS") or config.get("channels") or "file"
        if isinstance(raw, str):
            channels = [item.strip().lower() for item in raw.split(",") if item.strip()]
        elif isinstance(raw, Iterable):
            channels = [str(item).strip().lower() for item in raw if str(item).strip()]
        else:
            channels = ["file"]
        if "file" not in channels:
            channels.insert(0, "file")
        return channels

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

    def _send_webhook(self, channel: str, title: str, body: str) -> None:
        webhook_url = self._webhook_url(channel)
        if not webhook_url:
            self._write_outbox("stderr", channel, f"{channel}: no webhook url configured",
                               f"webhook env var not set. Skipping alert: {title}")
            return

        payload = self._webhook_payload(channel, title, body)
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = resp.read().decode("utf-8")
                print(f"[notifier] {channel} response: {result}")
        except Exception as exc:
            self._write_outbox("stderr", channel, f"{channel}: send failed", str(exc))
            print(f"[notifier] {channel} send failed: {exc}")

    def _webhook_url(self, channel: str) -> str:
        if channel == "dingtalk":
            return os.environ.get("DINGTALK_WEBHOOK_URL", "")
        if channel == "wechat":
            return os.environ.get("WECHAT_WORK_WEBHOOK_URL", "")
        if channel == "feishu":
            return os.environ.get("FEISHU_WEBHOOK_URL", "")
        return ""

    def _webhook_payload(self, channel: str, title: str, body: str) -> dict[str, Any]:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        markdown = f"## {title}\n\n{body}\n\n> CDC Warehouse Platform @ {now}"
        if channel == "wechat":
            return {"msgtype": "markdown", "markdown": {"content": markdown}}
        if channel == "feishu":
            return {"msg_type": "text", "content": {"text": f"{title}\n\n{body}\n\nCDC Warehouse Platform @ {now}"}}
        return {"msgtype": "markdown", "markdown": {"title": title, "text": markdown}}

    def _send_email(self, to_address: str, subject: str, body: str) -> None:
        smtp_host = os.environ.get("SMTP_HOST", "")
        if not smtp_host:
            self._write_outbox("stderr", "", "email: no SMTP configured",
                               f"SMTP_HOST env var not set. Skipping email alert: {subject}")
            return

        to_address = to_address or os.environ.get("SMTP_TO", "")
        if not to_address:
            self._write_outbox("stderr", "", "email: no target configured",
                               f"SMTP_TO env var not set. Skipping email alert: {subject}")
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
            self._write_outbox("stderr", to_address, "email: send failed", str(exc))
            print(f"[notifier] email send failed: {exc}")

    def _default_target(self, channel: str, target: str) -> str:
        if target:
            return target
        config = self._alert_config()
        if channel == "email":
            return os.environ.get("SMTP_TO") or config.get("email_to") or os.environ.get("ALERT_TARGET", "")
        return os.environ.get("ALERT_TARGET") or config.get("target") or channel

    def _alert_config(self) -> dict[str, Any]:
        try:
            from configs.loader import load_config
            return load_config().get("alerts", {})
        except Exception:
            return {}
