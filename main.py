"""
main.py

CLI entrypoint for the Log File Automation System.

Commands:
    scan       - Parse all logs in the log directory once, print/report summary
    watch      - Continuously monitor the log directory for changes
    archive    - Compress and (optionally) upload old logs to S3
    schedule   - Run scan/archive/report on recurring intervals (no external cron needed)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import schedule as schedule_lib
import time
import yaml

from src import log_parser, log_monitor, archiver, s3_uploader, report_generator
from src.alert_manager import AlertManager


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def run_scan(config: dict) -> dict:
    log_dir = Path(config["log_directory"])
    all_records = []
    for log_file in log_dir.glob("*.log"):
        all_records.extend(log_parser.parse_file(log_file))

    summary = log_parser.summarize(all_records)
    print(
        f"[scan] {summary['total_lines']} lines, "
        f"{summary['error_count']} errors ({summary['error_rate']:.2f}%)"
    )

    alert_mgr = AlertManager(config)
    if summary["error_count"]:
        alert_mgr.record_errors(summary["error_count"])
        if alert_mgr.should_alert():
            details = "\n".join(summary["sample_errors"])
            alert_mgr.send_alert(details)

    return summary


def run_archive(config: dict) -> None:
    archived = archiver.archive_old_logs(
        log_directory=config["log_directory"],
        archive_directory=config["archive_directory"],
        days=config.get("archive_after_days", 7),
    )

    aws_cfg = config.get("aws", {})
    if aws_cfg.get("enabled") and archived:
        s3_uploader.upload_files(
            archived, bucket_name=aws_cfg["bucket_name"], region=aws_cfg["region"]
        )


def run_report(config: dict, summary: dict | None = None) -> None:
    if summary is None:
        summary = run_scan(config)
    report_cfg = config.get("report", {})
    report_generator.generate_html_report(summary, report_cfg.get("output_path", "./reports"))


def run_watch(config: dict) -> None:
    alert_mgr = AlertManager(config)

    def on_new_records(path: str, records: list) -> None:
        error_count = sum(1 for r in records if r.is_error)
        print(f"[watch] {path}: {len(records)} new lines, {error_count} errors")
        if error_count:
            alert_mgr.record_errors(error_count)
            if alert_mgr.should_alert():
                details = "\n".join(r.message for r in records if r.is_error)
                alert_mgr.send_alert(details)

    log_monitor.watch_directory(config["log_directory"], on_new_records)


def run_schedule(config: dict) -> None:
    sched_cfg = config.get("schedule", {})

    schedule_lib.every(sched_cfg.get("scan_interval_minutes", 5)).minutes.do(run_scan, config)
    schedule_lib.every(sched_cfg.get("archive_interval_hours", 24)).hours.do(run_archive, config)
    schedule_lib.every(sched_cfg.get("report_interval_hours", 24)).hours.do(run_report, config)

    print("[schedule] Scheduler started. Ctrl+C to stop.")
    while True:
        schedule_lib.run_pending()
        time.sleep(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Log File Automation System")
    parser.add_argument(
        "command", choices=["scan", "watch", "archive", "schedule", "report"]
    )
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.command == "scan":
        run_scan(config)
    elif args.command == "watch":
        run_watch(config)
    elif args.command == "archive":
        run_archive(config)
    elif args.command == "report":
        run_report(config)
    elif args.command == "schedule":
        run_schedule(config)


if __name__ == "__main__":
    main()
