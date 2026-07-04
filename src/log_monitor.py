"""
log_monitor.py

Watches a log directory for new or modified `.log` files and triggers a
callback with parsed records whenever a file changes. Uses `watchdog` for
efficient filesystem event notification (no polling loop needed).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from . import log_parser


class LogFileHandler(FileSystemEventHandler):
    def __init__(self, on_new_records: Callable[[str, list], None]):
        self.on_new_records = on_new_records
        self._offsets: dict[str, int] = {}

    def _handle(self, path_str: str) -> None:
        if not path_str.endswith(".log"):
            return
        path = Path(path_str)
        if not path.exists():
            return

        last_offset = self._offsets.get(path_str, 0)
        with path.open("r", errors="replace") as f:
            f.seek(last_offset)
            new_lines = f.readlines()
            self._offsets[path_str] = f.tell()

        if not new_lines:
            return

        records = [r for r in (log_parser.parse_line(l) for l in new_lines) if r]
        if records:
            self.on_new_records(path_str, records)

    def on_modified(self, event):
        if not event.is_directory:
            self._handle(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self._handle(event.src_path)


def watch_directory(
    directory: str,
    on_new_records: Callable[[str, list], None],
    poll_interval: float = 1.0,
) -> None:
    """Blocking call: watches `directory` and invokes `on_new_records(path, records)`
    whenever new lines are appended to a .log file. Ctrl+C to stop."""
    handler = LogFileHandler(on_new_records)
    observer = Observer()
    observer.schedule(handler, directory, recursive=False)
    observer.start()
    print(f"[log_monitor] Watching '{directory}' for changes... (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
