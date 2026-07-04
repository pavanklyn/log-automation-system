"""
archiver.py

Finds log files older than a configured age, compresses them to .gz in an
archive directory, and removes the originals. Keeps the live log directory
small and ready for long-term storage (locally or in S3).
"""

from __future__ import annotations

import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path


def find_old_logs(log_directory: str, days: int) -> list[Path]:
    """Return log files whose last-modified time is older than `days`."""
    cutoff = datetime.now() - timedelta(days=days)
    directory = Path(log_directory)
    old_files = []
    for path in directory.glob("*.log"):
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        if mtime < cutoff:
            old_files.append(path)
    return old_files


def compress_file(path: Path, archive_directory: str) -> Path:
    """Gzip-compress a single file into the archive directory. Returns new path."""
    archive_dir = Path(archive_directory)
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / f"{path.name}.gz"

    with path.open("rb") as f_in, gzip.open(dest, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    return dest


def archive_old_logs(
    log_directory: str, archive_directory: str, days: int, delete_originals: bool = True
) -> list[Path]:
    """Compress all logs older than `days` and optionally delete originals.
    Returns list of archived file paths (the .gz files)."""
    archived = []
    for log_file in find_old_logs(log_directory, days):
        compressed_path = compress_file(log_file, archive_directory)
        archived.append(compressed_path)
        if delete_originals:
            log_file.unlink()
        print(f"[archiver] Archived {log_file.name} -> {compressed_path}")
    return archived
