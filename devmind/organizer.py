"""파일 이동 오케스트레이터/File organization orchestrator."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from rich.console import Console

from .config import ClusterResult, OrganizePlan, SchemaConfig
from .utils import append_jsonl, ensure_directory, load_json, now_ts

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

console = Console()


BUCKET_DIRECTORY_MAP: Dict[str, str] = {
    "src": "src/core",
    "scripts": "scripts",
    "tests": "tests/unit",
    "docs": "docs",
    "reports": "reports",
    "configs": "configs",
    "data": "data/raw",
    "notebooks": "notebooks",
    "archive": "archive",
    "tmp": "tmp",
}


def load_schema(path: Path) -> SchemaConfig:
    """스키마 로드/Load schema configuration."""

    if yaml is not None:
        data_raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        data_raw = load_json(path)
    data = data_raw if isinstance(data_raw, dict) else {}
    structure_raw = data.get("structure", [])
    structure = [str(item) for item in structure_raw]
    target_root = Path(str(data.get("target_root", "C:/PROJECTS_STRUCT")))
    return SchemaConfig(
        target_root=target_root,
        structure=structure,
        conflict_policy=str(data.get("conflict_policy", "version")),
        mode=str(data.get("mode", "move")),
    )


def ensure_schema_structure(target_root: Path, structure: Iterable[str]) -> None:
    """스키마 폴더 구조 생성/Ensure schema folder structure."""

    for relative in structure:
        ensure_directory(target_root / relative)


def resolve_target_path(
    project_root: Path,
    bucket: str,
    source_name: str,
    digest: str,
    used_targets: set[Path],
) -> Tuple[Path, str]:
    """대상 경로 결정/Resolve target path."""

    relative = BUCKET_DIRECTORY_MAP.get(bucket, "archive")
    base = project_root / relative
    ensure_directory(base)
    stem = Path(source_name).stem
    suffix = Path(source_name).suffix
    hash_suffix = digest[:7]
    candidate = base / source_name
    attempt = 0
    while candidate in used_targets or candidate.exists():
        name_suffix = (
            f"__{hash_suffix}" if attempt == 0 else f"__{hash_suffix}_{attempt}"
        )
        candidate = base / f"{stem}{name_suffix}{suffix}"
        attempt += 1
    used_targets.add(candidate)
    return candidate, hash_suffix


def build_plans(
    cluster: ClusterResult,
    schema: SchemaConfig,
    score_map: Dict[str, str],
    scan_index: Dict[str, Dict[str, Any]],
) -> List[OrganizePlan]:
    """조직화 계획 생성/Build organization plan."""

    plans: List[OrganizePlan] = []
    for project in cluster.projects:
        project_root = schema.target_root / project.project_label
        ensure_schema_structure(project_root, schema.structure)
        used_targets: set[Path] = set()
        for doc_id in project.doc_ids:
            metadata = scan_index.get(doc_id)
            if not metadata:
                continue
            source_path = Path(str(metadata.get("path", "")))
            digest = str(metadata.get("blake3", ""))
            bucket = project.role_bucket_map.get(
                doc_id,
                score_map.get(doc_id, "archive"),
            )
            target_path, hash_suffix = resolve_target_path(
                project_root=project_root,
                bucket=bucket,
                source_name=source_path.name,
                digest=digest,
                used_targets=used_targets,
            )
            plans.append(
                OrganizePlan(
                    doc_id=doc_id,
                    project_id=project.project_id,
                    project_label=project.project_label,
                    bucket=bucket,
                    source_path=source_path,
                    target_path=target_path,
                    hash_suffix=hash_suffix,
                )
            )
    return plans


def execute_plans(plans: Iterable[OrganizePlan], journal_path: Path, mode: str) -> None:
    """이동 계획 실행/Execute move plans."""

    entries = []
    for plan in plans:
        if not plan.source_path.exists():
            status = "missing"
            target_path = plan.target_path
        else:
            ensure_directory(plan.target_path.parent)
            if mode == "move":
                shutil.move(str(plan.source_path), str(plan.target_path))
            else:
                shutil.copy2(str(plan.source_path), str(plan.target_path))
            target_path = plan.target_path
            status = "moved" if mode == "move" else "copied"
        entries.append(
            {
                "original_path": str(plan.source_path),
                "target_path": str(target_path),
                "doc_id": plan.doc_id,
                "project_id": plan.project_id,
                "project_label": plan.project_label,
                "bucket": plan.bucket,
                "hash_suffix": plan.hash_suffix,
                "timestamp": now_ts(),
                "status": status,
            }
        )
    append_jsonl(journal_path, entries)
    message = (
        "[green]총 {count}개 파일 이동 기록/Recorded {count} moves.[/green]"
    ).format(count=len(entries))
    console.print(message)
