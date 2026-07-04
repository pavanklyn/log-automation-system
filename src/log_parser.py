"""
log_parser.py

Parses raw log lines into structured records. Supports:
- Python `logging` module default format:
    2026-07-02 10:15:32,123 - myapp - ERROR - Connection refused
- Apache/Nginx common log style:
    127.0.0.1 - - [02/Jul/2026:10:15:32 +0000] "GET /api/x HTTP/1.1" 500 231
- JSON lines:
    {"timestamp": "...", "level": "ERROR", "message": "..."}
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional


LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

# Python logging module style: "2026-07-02 10:15:32,123 - name - LEVEL - message"
_PY_LOG_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d{3})?)\s*-\s*"
    r"(?P<source>[\w.\-]+)\s*-\s*(?P<level>[A-Z]+)\s*-\s*(?P<message>.*)$"
)

# Common Apache/Nginx log format
_ACCESS_LOG_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d{3}) (?P<size>\S+)'
)


@dataclass
class LogRecord:
    timestamp: Optional[datetime]
    level: str
    message: str
    source: Optional[str] = None
    raw: str = field(default="", repr=False)

    @property
    def is_error(self) -> bool:
        return self.level in ("ERROR", "CRITICAL")


def _parse_py_timestamp(ts: str) -> Optional[datetime]:
    ts = ts.replace(",", ".")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None


def parse_line(line: str) -> Optional[LogRecord]:
    """Parse a single log line into a LogRecord. Returns None if unparseable."""
    line = line.rstrip("\n")
    if not line.strip():
        return None

    # Try JSON first
    if line.lstrip().startswith("{"):
        try:
            data = json.loads(line)
            level = str(data.get("level", "INFO")).upper()
            ts_raw = data.get("timestamp")
            ts = None
            if ts_raw:
                try:
                    ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                except ValueError:
                    ts = None
            return LogRecord(
                timestamp=ts,
                level=level if level in LEVELS else "INFO",
                message=str(data.get("message", "")),
                source=data.get("source"),
                raw=line,
            )
        except (json.JSONDecodeError, AttributeError):
            pass

    # Try Python logging format
    m = _PY_LOG_RE.match(line)
    if m:
        level = m.group("level").upper()
        return LogRecord(
            timestamp=_parse_py_timestamp(m.group("timestamp")),
            level=level if level in LEVELS else "INFO",
            message=m.group("message"),
            source=m.group("source"),
            raw=line,
        )

    # Try access log format
    m = _ACCESS_LOG_RE.match(line)
    if m:
        status = int(m.group("status"))
        level = "ERROR" if status >= 500 else ("WARNING" if status >= 400 else "INFO")
        message = f'{m.group("method")} {m.group("path")} -> {status}'
        return LogRecord(
            timestamp=None,  # apache timestamp format parsing omitted for brevity
            level=level,
            message=message,
            source=m.group("ip"),
            raw=line,
        )

    # Fallback: unstructured line, still capture keyword-based errors
    upper = line.upper()
    for level in ("CRITICAL", "ERROR", "WARNING"):
        if level in upper:
            return LogRecord(timestamp=None, level=level, message=line, raw=line)

    return LogRecord(timestamp=None, level="INFO", message=line, raw=line)


def parse_file(path: str | Path) -> Iterator[LogRecord]:
    """Yield LogRecord objects for every parseable line in a log file."""
    path = Path(path)
    with path.open("r", errors="replace") as f:
        for line in f:
            record = parse_line(line)
            if record is not None:
                yield record


def summarize(records: list[LogRecord]) -> dict:
    """Produce summary stats used by the report generator and alert manager."""
    total = len(records)
    level_counts = {level: 0 for level in LEVELS}
    for r in records:
        level_counts[r.level] = level_counts.get(r.level, 0) + 1

    error_records = [r for r in records if r.is_error]

    return {
        "total_lines": total,
        "level_counts": level_counts,
        "error_count": len(error_records),
        "error_rate": (len(error_records) / total * 100) if total else 0.0,
        "sample_errors": [r.message for r in error_records[:10]],
    }
