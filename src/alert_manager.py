"""
alert_manager.py

Tracks error events in a rolling time window and sends an email alert once
the configured threshold is crossed. SMTP credentials are read from an
environment variable, never stored in config.yaml.
"""

from __future__ import annotations

import os
import smtplib
from collections import deque
from datetime import datetime, timedelta
from email.mime.text import MIMEText


class AlertManager:
    def __init__(self, config: dict):
        alert_cfg = config.get("alerts", {})
        self.enabled = alert_cfg.get("enabled", False)
        self.threshold = alert_cfg.get("error_threshold", 10)
        self.window = timedelta(minutes=alert_cfg.get("window_minutes", 15))
        self.email_cfg = alert_cfg.get("email", {})
        self._error_timestamps: deque[datetime] = deque()
        self._last_alert_sent: datetime | None = None
        self._cooldown = timedelta(minutes=30)  # don't spam alerts

    def record_errors(self, count: int) -> None:
        """Record `count` error events at the current time."""
        now = datetime.now()
        for _ in range(count):
            self._error_timestamps.append(now)
        self._prune(now)

    def _prune(self, now: datetime) -> None:
        while self._error_timestamps and now - self._error_timestamps[0] > self.window:
            self._error_timestamps.popleft()

    def should_alert(self) -> bool:
        now = datetime.now()
        self._prune(now)
        if len(self._error_timestamps) < self.threshold:
            return False
        if self._last_alert_sent and now - self._last_alert_sent < self._cooldown:
            return False
        return True

    def send_alert(self, details: str = "") -> bool:
        """Send an email alert. Returns True on success."""
        if not self.enabled:
            print("[alert_manager] Alerts disabled in config; skipping send.")
            return False

        count = len(self._error_timestamps)
        subject = f"[Log Alert] {count} errors in the last {self.window}"
        body = (
            f"Error threshold crossed: {count} errors detected in the last "
            f"{self.window}.\n\n{details}"
        )

        password = os.environ.get(self.email_cfg.get("sender_password_env", ""), "")
        if not password:
            print(
                "[alert_manager] No SMTP password found in env var "
                f"'{self.email_cfg.get('sender_password_env')}'. Skipping send; "
                "logging alert instead:\n" + body
            )
            return False

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.email_cfg["sender"]
        msg["To"] = ", ".join(self.email_cfg["recipients"])

        try:
            with smtplib.SMTP(self.email_cfg["smtp_host"], self.email_cfg["smtp_port"]) as server:
                server.starttls()
                server.login(self.email_cfg["sender"], password)
                server.sendmail(
                    self.email_cfg["sender"], self.email_cfg["recipients"], msg.as_string()
                )
            self._last_alert_sent = datetime.now()
            print(f"[alert_manager] Alert sent to {self.email_cfg['recipients']}")
            return True
        except Exception as e:  # noqa: BLE001 - want to surface any SMTP failure
            print(f"[alert_manager] Failed to send alert email: {e}")
            return False
