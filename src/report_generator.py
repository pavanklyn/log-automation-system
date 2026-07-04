"""
report_generator.py

Builds a simple HTML summary report from parsed log records: total lines,
level breakdown, error rate, and a sample of recent errors.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Template

_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Log Report - {{ generated_at }}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; color: #222; }
    h1 { color: #1a1a1a; }
    table { border-collapse: collapse; width: 100%; margin-top: 20px; }
    th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
    th { background-color: #f4f4f4; }
    .error-count { color: #c0392b; font-weight: bold; }
    .errors-list { background: #fdf2f2; padding: 12px; border-left: 4px solid #c0392b; }
  </style>
</head>
<body>
  <h1>Log Summary Report</h1>
  <p>Generated: {{ generated_at }}</p>

  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Total lines processed</td><td>{{ summary.total_lines }}</td></tr>
    <tr><td>Error count</td><td class="error-count">{{ summary.error_count }}</td></tr>
    <tr><td>Error rate</td><td>{{ "%.2f"|format(summary.error_rate) }}%</td></tr>
    {% for level, count in summary.level_counts.items() %}
    <tr><td>{{ level }}</td><td>{{ count }}</td></tr>
    {% endfor %}
  </table>

  {% if summary.sample_errors %}
  <h2>Sample Errors</h2>
  <div class="errors-list">
    <ul>
      {% for err in summary.sample_errors %}
      <li>{{ err }}</li>
      {% endfor %}
    </ul>
  </div>
  {% endif %}
</body>
</html>
""")


def generate_html_report(summary: dict, output_path: str) -> Path:
    """Render the summary dict into an HTML file. Returns the output path."""
    out_dir = Path(output_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_file = out_dir / f"log_report_{timestamp}.html"

    html = _TEMPLATE.render(summary=summary, generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    out_file.write_text(html)

    print(f"[report_generator] Report written to {out_file}")
    return out_file
