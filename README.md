# Log File Automation System

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-S3-orange?logo=amazonaws&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/tests-9%20passing-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A Python-based automation tool that monitors, parses, analyzes, archives, and reports on
application log files — with optional AWS S3 archival and email alerting.

Built for real-world ops/DevOps workflows: catch errors early, keep log directories clean,
and get a daily summary without manually opening a single log file.

## Features

- **Log Monitoring** — watches a directory for new/updated log files in real time
- **Log Parsing** — regex-based parser supporting common formats (Apache/Nginx style,
  Python `logging` module output, and custom JSON logs)
- **Error/Anomaly Detection** — flags ERROR/CRITICAL entries and configurable keyword
  patterns (e.g. `OutOfMemory`, `Timeout`, `Connection refused`)
- **Alerting** — sends an email alert when error counts cross a threshold in a rolling window
- **Log Rotation & Archiving** — compresses logs older than N days into `.gz`, deletes
  originals, keeps the working directory lean
- **AWS S3 Upload** — pushes archived logs to an S3 bucket for long-term, cheap storage
- **Report Generation** — daily/weekly HTML summary report (log volume, error rate,
  top error types, busiest hours)
- **CLI** — single entrypoint to run one-off scans or start continuous monitoring
- **Dockerized** — run it anywhere without local Python setup
- **Unit tested** — pytest suite covering the parser and archiver

## Project Structure

```
log-automation-system/
├── main.py                  # CLI entrypoint
├── config.yaml               # All configuration (paths, thresholds, AWS, email)
├── requirements.txt
├── Dockerfile
├── src/
│   ├── log_parser.py         # Parses raw log lines into structured records
│   ├── log_monitor.py        # Watches directory, triggers parsing on change
│   ├── alert_manager.py      # Threshold checks + email alerts
│   ├── archiver.py           # Compresses/deletes old logs
│   ├── s3_uploader.py        # Uploads archives to S3
│   └── report_generator.py   # Builds HTML summary reports
├── tests/
│   ├── test_log_parser.py
│   └── test_archiver.py
└── sample_logs/
    └── app.log                # Sample log file to try things out on
```

## Setup

```bash
git clone <your-repo-url>
cd log-automation-system
pip install -r requirements.txt
cp config.yaml.example config.yaml   # then edit paths/credentials
```

AWS credentials are picked up the standard boto3 way (env vars, `~/.aws/credentials`,
or IAM role) — never hardcode keys in `config.yaml`.

## Usage

**One-off scan + report (good for cron):**
```bash
python main.py scan --config config.yaml
```

**Continuous monitoring:**
```bash
python main.py watch --config config.yaml
```

**Archive logs older than N days and upload to S3:**
```bash
python main.py archive --config config.yaml
```

**Run everything on a schedule (built-in scheduler, no external cron needed):**
```bash
python main.py schedule --config config.yaml
```

## Example config.yaml

```yaml
log_directory: "./sample_logs"
archive_directory: "./archive"
archive_after_days: 7

alerts:
  enabled: true
  error_threshold: 10
  window_minutes: 15
  email:
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    sender: "alerts@example.com"
    recipients: ["you@example.com"]

aws:
  enabled: false
  bucket_name: "my-log-archive-bucket"
  region: "ap-south-1"

report:
  output_path: "./reports"
  format: "html"
```

## Running Tests

```bash
pytest tests/ -v
```

## Docker

```bash
docker build -t log-automation .
docker run -v $(pwd)/sample_logs:/app/sample_logs log-automation scan
```

## Tech Stack

Python 3.11, `watchdog` (file monitoring), `boto3` (AWS S3), `schedule` (job scheduling),
`Jinja2` (HTML reports), `pytest` (testing), Docker.

## Resume-friendly summary

Pick the bullet that best fits the role you're applying for — or use the project summary
as-is under a Projects section.

**Project summary (for a Projects section):**
> **Log File Automation System** — Python, AWS S3, Docker, pytest
> Built a Python automation system that monitors, parses, and analyzes application logs
> in real time; automatically archives and uploads logs older than a configurable
> threshold to AWS S3; and sends threshold-based email alerts on error spikes — reducing
> manual log review effort and log storage footprint.

**Single bullet (Software Engineer / backend-leaning roles):**
> Designed and built a Python log automation pipeline with regex-based multi-format
> parsing, real-time file monitoring, and automated AWS S3 archival, cutting manual log
> triage effort and improving mean-time-to-detect for error spikes.

**Single bullet (Cloud/AWS-leaning roles):**
> Automated log lifecycle management using Python and AWS S3 (boto3) — including
> log rotation, gzip compression, and long-term archival — reducing local storage
> footprint while preserving log retention for audit/debugging needs.

**Single bullet (Ops/DevOps-leaning roles):**
> Built a threshold-based alerting system in Python that monitors application logs in
> real time and triggers email notifications on error-rate spikes within a configurable
> rolling window, reducing incident detection time.
