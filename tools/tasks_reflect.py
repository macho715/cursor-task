#!/usr/bin/env python3
"""Local task reflection CLI for reuse across projects."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from reflection import (
    ReflectionConfig,
    ReflectionError,
    ReflectionResult,
    TaskReflector,
    TaskValidationError,
    load_config,
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Analyze task graph and calculate complexity scores.",
    )
    parser.add_argument(
        "--in",
        dest="input_file",
        required=True,
        help="Input tasks JSON file",
    )
    parser.add_argument(
        "--out",
        dest="output_file",
        required=True,
        help="Destination path for reflected JSON",
    )
    parser.add_argument(
        "--report",
        dest="report_file",
        required=True,
        help="Destination path for markdown report",
    )
    parser.add_argument(
        "--config",
        dest="config_file",
        help="Optional JSON/YAML config overriding complexity weights",
    )
    return parser.parse_args()


def build_reflector(config_path: str | None) -> TaskReflector:
    """Initialise task reflector using optional config file."""

    if config_path:
        config = load_config(config_path)
        return TaskReflector(config)
    return TaskReflector(ReflectionConfig())


def serialise_result(result: ReflectionResult) -> str:
    """Return JSON serialisation for reflection output."""

    return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)


def run_cli(args: argparse.Namespace) -> int:
    """Execute reflection workflow based on parsed args."""

    reflector = build_reflector(args.config_file)
    tasks_data = reflector.load_tasks(args.input_file)
    reflection = reflector.reflect(tasks_data)

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(serialise_result(reflection), encoding="utf-8")

    report_path = Path(args.report_file)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_content = reflector.build_report(tasks_data, reflection)
    report_path.write_text(report_content, encoding="utf-8")

    print(f"Reflection complete: {output_path}")
    print(f"Report generated: {report_path}")

    if reflection.cycles:
        cycle_count = len(reflection.cycles)
        print(f"Warning: detected {cycle_count} cycle(s): {reflection.cycles}")
    unordered = reflection.meta.get("unordered_tasks", [])
    if unordered:
        print(f"Warning: unresolved order for tasks: {', '.join(unordered)}")
    return 0


def main() -> None:
    """Program entry point."""

    args = parse_args()
    try:
        status = run_cli(args)
    except (ReflectionError, TaskValidationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(status)


if __name__ == "__main__":
    main()
