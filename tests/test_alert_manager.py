import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.alert_manager import AlertManager


def test_send_alert_missing_password_does_not_mark_last_alert_sent(monkeypatch):
    config = {
        "alerts": {
            "enabled": True,
            "error_threshold": 1,
            "window_minutes": 15,
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "sender": "alerts@example.com",
                "sender_password_env": "LOG_MISSING_PASSWORD",
                "recipients": ["user@example.com"],
            },
        }
    }

    monkeypatch.delenv("LOG_MISSING_PASSWORD", raising=False)

    alert_mgr = AlertManager(config)
    alert_mgr.record_errors(1)

    assert alert_mgr.should_alert()
    assert alert_mgr.send_alert("details") is False
    assert alert_mgr._last_alert_sent is None
    assert alert_mgr.should_alert()
