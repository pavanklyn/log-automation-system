import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import log_parser


def test_parse_python_logging_format():
    line = "2026-07-02 09:05:33,001 - myapp - ERROR - Connection refused"
    record = log_parser.parse_line(line)
    assert record is not None
    assert record.level == "ERROR"
    assert record.source == "myapp"
    assert "Connection refused" in record.message
    assert record.is_error is True


def test_parse_json_log():
    line = '{"timestamp": "2026-07-02T09:05:33", "level": "warning", "message": "disk 90% full"}'
    record = log_parser.parse_line(line)
    assert record is not None
    assert record.level == "WARNING"
    assert record.message == "disk 90% full"


def test_parse_access_log():
    line = '127.0.0.1 - - [02/Jul/2026:09:05:33 +0000] "GET /api/orders HTTP/1.1" 500 231'
    record = log_parser.parse_line(line)
    assert record is not None
    assert record.level == "ERROR"
    assert "500" in record.message


def test_parse_blank_line_returns_none():
    assert log_parser.parse_line("") is None
    assert log_parser.parse_line("   \n") is None


def test_summarize_counts_errors():
    lines = [
        "2026-07-02 09:00:00,000 - app - INFO - ok",
        "2026-07-02 09:00:01,000 - app - ERROR - failure one",
        "2026-07-02 09:00:02,000 - app - ERROR - failure two",
        "2026-07-02 09:00:03,000 - app - CRITICAL - crash",
    ]
    records = [log_parser.parse_line(l) for l in lines]
    summary = log_parser.summarize(records)
    assert summary["total_lines"] == 4
    assert summary["error_count"] == 3  # ERROR + ERROR + CRITICAL
    assert summary["level_counts"]["INFO"] == 1


def test_parse_file(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text(
        "2026-07-02 09:00:00,000 - app - INFO - started\n"
        "2026-07-02 09:00:01,000 - app - ERROR - broke\n"
    )
    records = list(log_parser.parse_file(log_file))
    assert len(records) == 2
    assert records[1].is_error
