#!/usr/bin/env python3
"""Bootstrap a new project that reuses the hybrid AI workflow toolkit."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence, Tuple

DEFAULT_DIRECTORIES: Sequence[str] = (
    "docs",
    "tools",
    "reports",
    ".github/workflows",
    ".cursor/rules",
    "src",
    "tests",
)

ESSENTIAL_ITEMS: Sequence[Tuple[str, str]] = (
    ("tools/tasks_reflect.py", "tools/tasks_reflect.py"),
    ("tools/execute_priority.py", "tools/execute_priority.py"),
    ("tools/parallel_executor.py", "tools/parallel_executor.py"),
    ("tools/dag_visualizer.py", "tools/dag_visualizer.py"),
    ("tools/auto_reflector.py", "tools/auto_reflector.py"),
    ("tools/conventional_commits.py", "tools/conventional_commits.py"),
    ("tools/setup_git_hooks.py", "tools/setup_git_hooks.py"),
    ("tools/reflection", "tools/reflection"),
    (".github/workflows/reflect.yml", ".github/workflows/reflect.yml"),
    (".gitignore", ".gitignore"),
    ("LICENSE", "LICENSE"),
)

WATCHDOG_CONFIGS = {
    "web": "watchdog_config_web.yaml",
    "microservices": "watchdog_config_microservices.yaml",
    "generic": "watchdog_config.yaml",
}

PRIORITY_CONFIGS = {
    "startup": "priority_config_startup.yaml",
    "enterprise": "priority_config_enterprise.yaml",
    "default": "priority_config.yaml",
}


class ProjectSetup:
    """Create a ready-to-use project scaffold from the template."""

    def __init__(self, destination_root: Path, force: bool = False):
        self.template_root = Path(__file__).resolve().parents[1]
        self.destination_root = destination_root
        self.force = force

    def create_project_structure(self, project_name: str, project_type: str, team_size: str) -> Path:
        """Generate directories, copy tools, and seed starter files."""

        project_root = (self.destination_root / project_name).resolve()
        self._prepare_target(project_root)
        print(f"Creating scaffold at {project_root}")
        self._ensure_directories(project_root, DEFAULT_DIRECTORIES)
        self._copy_essential_files(project_root)
        self._create_prd_template(project_root, project_name, project_type)
        self._create_tasks_template(project_root, project_name)
        self._create_config_files(project_root, project_type, team_size)
        print("Scaffold complete")
        return project_root

    def _prepare_target(self, project_root: Path) -> None:
        """Ensure the target path is ready for file generation."""

        if project_root.exists():
            if not project_root.is_dir():
                raise RuntimeError(f"Target path exists and is not a directory: {project_root}")
            if not self.force and any(project_root.iterdir()):
                raise RuntimeError(
                    f"Target directory {project_root} is not empty. Use --force to continue."
                )
        else:
            project_root.mkdir(parents=True, exist_ok=True)

    def _ensure_directories(self, project_root: Path, directories: Iterable[str]) -> None:
        for relative in directories:
            target = project_root / relative
            target.mkdir(parents=True, exist_ok=True)
            print(f"  created {relative}/")

    def _copy_essential_files(self, project_root: Path) -> None:
        for src_rel, dst_rel in ESSENTIAL_ITEMS:
            src = self.template_root / src_rel
            if not src.exists():
                print(f"  missing template item: {src_rel}")
                continue
            dst = project_root / dst_rel
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            print(f"  copied {dst_rel}")

    def _create_prd_template(self, project_root: Path, project_name: str, project_type: str) -> None:
        slug = project_name.lower().replace(" ", "-")
        prd_content = f"""# PRD (Product Requirements Doc) - {project_name}

```yml
meta:
  id: prj-{slug}
  owner: "Your Name <your-email@example.com>"
  repo: "{slug}"
  due: "2025-12-31"
  risk_tolerance: "medium"
  project_type: "{project_type}"

objectives:
  - "Deliver the hybrid AI workflow automation"
  - "Provide repeatable task reflection outputs"
  - "Enable fast onboarding for new contributors"

deliverables:
  - "Seeded tasks.json and reports"
  - "Automated reflection scripts"
  - "Visualization assets"

constraints:
  - "Python 3.9+ runtime"
  - "Graphviz available for visualisation"
  - "Git repository initialised"

modules:
  - id: setup
    title: "Environment bootstrap"
    value: "high"
    acceptance:
      - "Python dependencies installed"
      - "Project scaffold generated"

  - id: core-development
    title: "Core workflow tooling"
    value: "high"
    acceptance:
      - "Reflection CLI configured"
      - "Priority logic available"

  - id: testing-deployment
    title: "CI and automation"
    value: "medium"
    acceptance:
      - "Smoke tests configured"
      - "GitHub workflow enabled"

quality_gates:
  - "All reflection scripts run locally"
  - "Task complexity report generated"
  - "Git hooks validated"
```
"""
        docs_path = project_root / "docs" / "PRD.md"
        docs_path.write_text(prd_content, encoding="utf-8")
        print("  wrote docs/PRD.md")

    def _create_tasks_template(self, project_root: Path, project_name: str) -> None:
        tasks_template = {
            "": "https://schemas.cursor.sh/tm.tasks.json",
            "meta": {
                "source": "docs/PRD.md",
                "generated_at": datetime.now().isoformat(),
                "project": project_name,
            },
            "tasks": [
                {
                    "id": "setup:env",
                    "title": "Provision Python environment",
                    "module": "setup",
                    "type": "config",
                    "deps": [],
                    "complexity": 1.0,
                    "acceptance": [
                        "Virtual environment created",
                        "Core dependencies installed",
                    ],
                },
                {
                    "id": "setup:deps",
                    "title": "Install workflow dependencies",
                    "module": "setup",
                    "type": "config",
                    "deps": ["setup:env"],
                    "complexity": 1.2,
                    "acceptance": [
                        "requirements.txt curated",
                        "Tooling verified",
                    ],
                },
                {
                    "id": "core:reflection",
                    "title": "Configure task reflection CLI",
                    "module": "core-development",
                    "type": "code",
                    "deps": ["setup:deps"],
                    "complexity": 1.8,
                    "acceptance": [
                        "tasks_reflect.py executed",
                        "Report generated",
                    ],
                },
                {
                    "id": "core:priority",
                    "title": "Tune priority execution strategy",
                    "module": "core-development",
                    "type": "code",
                    "deps": ["core:reflection"],
                    "complexity": 1.6,
                    "acceptance": [
                        "Priority config aligned",
                        "Smoke tests updated",
                    ],
                },
                {
                    "id": "test:integration",
                    "title": "Author integration smoke tests",
                    "module": "testing-deployment",
                    "type": "test",
                    "deps": ["core:priority"],
                    "complexity": 1.4,
                    "acceptance": [
                        "CI command documented",
                        "Tests green locally",
                    ],
                },
                {
                    "id": "deploy:automation",
                    "title": "Wire GitHub automation",
                    "module": "testing-deployment",
                    "type": "config",
                    "deps": ["test:integration"],
                    "complexity": 1.3,
                    "acceptance": [
                        "Workflow committed",
                        "Badge visible in README",
                    ],
                },
            ],
        }
        tasks_path = project_root / "tasks.json"
        tasks_path.write_text(json.dumps(tasks_template, indent=2), encoding="utf-8")
        print("  wrote tasks.json")

    def _create_config_files(self, project_root: Path, project_type: str, team_size: str) -> None:
        watchdog_key = WATCHDOG_CONFIGS.get(project_type, WATCHDOG_CONFIGS["generic"])
        self._copy_optional(
            self.template_root / "tools" / watchdog_key,
            project_root / "tools" / "watchdog_config.yaml",
            f"tools/watchdog_config.yaml ({project_type})",
        )
        priority_key = PRIORITY_CONFIGS.get(team_size, PRIORITY_CONFIGS["default"])
        self._copy_optional(
            self.template_root / "tools" / priority_key,
            project_root / "tools" / "priority_config.yaml",
            f"tools/priority_config.yaml ({team_size})",
        )

    def _copy_optional(self, src: Path, dst: Path, label: str) -> None:
        if not src.exists():
            print(f"  missing template item: {label}")
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  copied {label}")

    def setup_git_repository(self, project_root: Path, project_name: str, remote_url: str | None = None) -> None:
        print("Initialising git repository")
        commands = [
            (["git", "init"], "git init"),
            (["git", "add", "."], "git add ."),
            (
                [
                    "git",
                    "commit",
                    "-m",
                    f"feat: initialize {project_name} project with hybrid workflow",
                ],
                "git commit",
            ),
        ]
        for cmd, label in commands:
            try:
                subprocess.run(cmd, check=True, cwd=project_root)
                print(f"  {label}")
            except subprocess.CalledProcessError as exc:
                print(
                    f"  warning: {label} failed with exit code {exc.returncode}. Configure git and retry."
                )
                return
        if remote_url:
            try:
                subprocess.run(["git", "remote", "add", "origin", remote_url], check=True, cwd=project_root)
                print(f"  git remote add origin {remote_url}")
            except subprocess.CalledProcessError as exc:
                print(
                    f"  warning: failed to add remote ({exc.returncode}). Run 'git remote add origin' manually."
                )

    def run_initial_tests(self, project_root: Path) -> None:
        print("Running smoke tests")
        python = sys.executable
        commands = [
            (
                [
                    python,
                    "tools/tasks_reflect.py",
                    "--in",
                    "tasks.json",
                    "--out",
                    "tasks.reflected.json",
                    "--report",
                    "reports/tasks_reflect_report.md",
                ],
                "task reflection",
            ),
            (
                [python, "tools/dag_visualizer.py", "--input", "tasks.reflected.json"],
                "visualisation",
            ),
        ]
        for cmd, label in commands:
            result = subprocess.run(cmd, cwd=project_root)
            if result.returncode == 0:
                print(f"  ok: {label}")
            else:
                print(f"  warning: {label} exited with code {result.returncode}")

    def interactive_setup(self) -> None:
        print("Hybrid workflow project setup wizard")
        project_name = input("Project name: ").strip() or "my-hybrid-project"
        print("\nSelect project profile:")
        print("  1) web application")
        print("  2) microservices")
        print("  3) generic")
        profile_choice = input("Choice (1/2/3): ").strip()
        project_type = {"1": "web", "2": "microservices", "3": "generic"}.get(profile_choice, "generic")
        print("\nSelect team size profile:")
        print("  1) startup")
        print("  2) enterprise")
        print("  3) default")
        team_choice = input("Choice (1/2/3): ").strip()
        team_size = {"1": "startup", "2": "enterprise", "3": "default"}.get(team_choice, "default")
        remote_url = None
        if input("\nConfigure git repository now? (y/n): ").strip().lower() == "y":
            remote_url = input("Remote origin URL (optional): ").strip() or None
        try:
            project_root = self.create_project_structure(project_name, project_type, team_size)
        except RuntimeError as exc:
            print(f"Error: {exc}")
            return
        if remote_url:
            self.setup_git_repository(project_root, project_name, remote_url)
        if input("Run smoke tests? (y/n): ").strip().lower() == "y":
            self.run_initial_tests(project_root)
        print(f"\nProject ready at {project_root}")
        print("Next steps:")
        print("  - Review docs/PRD.md and refine requirements")
        print("  - Execute python tools/tasks_reflect.py --in tasks.json --out tasks.reflected.json --report reports/tasks_reflect_report.md")
        print("  - Commit your changes and push to the configured remote")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a reusable project scaffold from the hybrid AI workflow template",
    )
    parser.add_argument("--project-name", help="Name of the project to generate")
    parser.add_argument(
        "--type",
        choices=["web", "microservices", "generic"],
        default="generic",
        help="Project profile that selects default configs",
    )
    parser.add_argument(
        "--team-size",
        choices=["startup", "enterprise", "default"],
        default="default",
        help="Team size profile for priority configuration",
    )
    parser.add_argument(
        "--destination",
        default=".",
        help="Directory where the project should be created (default: current directory)",
    )
    parser.add_argument("--remote-url", help="Git remote URL to configure after initial commit")
    parser.add_argument("--interactive", action="store_true", help="Launch the interactive setup wizard")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running smoke tests after scaffolding")
    parser.add_argument("--force", action="store_true", help="Allow using a non-empty destination directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    destination_root = Path(args.destination).expanduser().resolve()
    setup = ProjectSetup(destination_root=destination_root, force=args.force)
    if args.interactive:
        setup.interactive_setup()
        return
    if not args.project_name:
        print("Error: --project-name is required in non-interactive mode")
        return
    try:
        project_root = setup.create_project_structure(args.project_name, args.type, args.team_size)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return
    if args.remote_url:
        setup.setup_git_repository(project_root, args.project_name, args.remote_url)
    if not args.skip_tests:
        setup.run_initial_tests(project_root)
    print(f"\nProject ready at {project_root}")
    print("Next steps:")
    print("  - Update docs/PRD.md to reflect your requirements")
    print("  - Run python tools/tasks_reflect.py --in tasks.json --out tasks.reflected.json --report reports/tasks_reflect_report.md")
    if not args.remote_url:
        print("  - Run 'git init' and commit when you are ready")


if __name__ == "__main__":
    main()
