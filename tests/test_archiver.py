import gzip
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import archiver


def test_find_old_logs(tmp_path):
    old_file = tmp_path / "old.log"
    old_file.write_text("old log content")
    # backdate the mtime to 10 days ago
    old_time = time.time() - (10 * 86400)
    os.utime(old_file, (old_time, old_time))

    new_file = tmp_path / "new.log"
    new_file.write_text("new log content")

    old_logs = archiver.find_old_logs(str(tmp_path), days=7)
    assert old_file in old_logs
    assert new_file not in old_logs


def test_compress_file(tmp_path):
    src_file = tmp_path / "sample.log"
    src_file.write_text("hello world log line\n")
    archive_dir = tmp_path / "archive"

    dest = archiver.compress_file(src_file, str(archive_dir))
    assert dest.exists()
    assert dest.suffix == ".gz"

    with gzip.open(dest, "rt") as f:
        content = f.read()
    assert content == "hello world log line\n"


def test_archive_old_logs_deletes_originals(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    archive_dir = tmp_path / "archive"

    old_file = log_dir / "old.log"
    old_file.write_text("stale log")
    old_time = time.time() - (10 * 86400)
    os.utime(old_file, (old_time, old_time))

    archived = archiver.archive_old_logs(
        str(log_dir), str(archive_dir), days=7, delete_originals=True
    )

    assert len(archived) == 1
    assert not old_file.exists()
    assert archived[0].exists()
