"""리포트 생성기/Report generator."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Mapping

from .config import ClusterResult
from .utils import ensure_directory, get_console, read_jsonl

console = get_console()


def generate_summary(
    cluster: ClusterResult,
    journal_path: Path,
    html_path: Path,
    json_path: Path,
    csv_path: Path,
) -> None:
    """프로젝트 리포트 생성/Generate project report."""

    ensure_directory(html_path.parent)
    ensure_directory(json_path.parent)
    ensure_directory(csv_path.parent)
    journal_entries = read_jsonl(journal_path)
    totals = Counter(entry.get("project_label", "unknown") for entry in journal_entries)
    bucket_totals = Counter(entry.get("bucket", "archive") for entry in journal_entries)
    summary: Dict[str, Any] = {
        "projects": [
            {
                "project_id": project.project_id,
                "project_label": project.project_label,
                "doc_count": len(project.doc_ids),
                "confidence": project.confidence,
            }
            for project in cluster.projects
        ],
        "moves": journal_entries,
        "project_totals": dict(totals),
        "bucket_totals": dict(bucket_totals),
    }
    json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    csv_lines = ["project_label,count"]
    for label, count in sorted(totals.items()):
        csv_lines.append(f"{label},{count}")
    csv_path.write_text("\n".join(csv_lines), encoding="utf-8")
    html_path.write_text(_render_html(summary), encoding="utf-8")
    message = ("[green]리포트 생성 완료/Report generated at {path}[/green]").format(
        path=html_path
    )
    console.print(message)


def _render_html(summary: Mapping[str, Any]) -> str:
    """HTML 문자열 렌더링/Render HTML string."""

    style_lines = [
        "body { background-color: #0B1220; color: #E5E7EB; font-family: Inter; }",
        ".container { max-width: 960px; margin: 0 auto; padding: 32px; }",
        "h1 { color: #60A5FA; }",
        "table { width: 100%; border-collapse: collapse; margin-top: 24px; }",
        "th, td { border: 1px solid #111827; padding: 12px; text-align: left; }",
        "th { background-color: #111827; color: #22D3EE; }",
        ".card { background-color: #111827; border-radius: 12px; padding: 16px; }",
    ]
    style = "\n".join(style_lines)
    project_rows = "".join(
        (
            "<tr><td>{pid}</td><td>{label}</td><td>{count}</td>"
            "<td>{conf:.2f}</td></tr>"
        ).format(
            pid=item["project_id"],
            label=item["project_label"],
            count=item["doc_count"],
            conf=item["confidence"],
        )
        for item in summary.get("projects", [])
    )
    bucket_totals = summary.get("bucket_totals", {})
    if isinstance(bucket_totals, dict):
        bucket_items = list(bucket_totals.items())
    else:
        bucket_items = []
    bucket_rows = "".join(
        f"<tr><td>{bucket}</td><td>{count}</td></tr>" for bucket, count in bucket_items
    )
    project_rows = project_rows or "<tr><td colspan='4'>No projects</td></tr>"
    bucket_rows = bucket_rows or "<tr><td colspan='2'>No buckets</td></tr>"
    return f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Project Summary</title>
        <style>{style}</style>
      </head>
      <body>
        <div class="container">
          <h1>프로젝트 요약 / Project Summary</h1>
          <div class="card">
            <h2>Projects</h2>
            <table>
              <thead>
                <tr><th>ID</th><th>Label</th><th>Docs</th><th>Confidence</th></tr>
              </thead>
              <tbody>{project_rows}</tbody>
            </table>
          </div>
          <div class="card">
            <h2>Buckets</h2>
            <table>
              <thead>
                <tr><th>Bucket</th><th>Count</th></tr>
              </thead>
              <tbody>{bucket_rows}</tbody>
            </table>
          </div>
        </div>
      </body>
    </html>
    """
