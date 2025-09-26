"""프로젝트 군집기/Project clusterer."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from .config import ClusterProject, ClusterResult
from .utils import load_json


@dataclass(slots=True)
class ClusterInput:
    """군집 입력 구조/Cluster input structure."""

    doc_id: str
    path: Path
    name: str
    bucket: str
    dir_hint: str


def _normalize_label(label: str) -> str:
    """라벨 정규화/Normalize label."""

    normalized = "".join(
        ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in label
    )
    normalized = normalized.strip("_ ")
    return normalized.lower()


def infer_project_label(path: Path, hints: Iterable[str]) -> str:
    """프로젝트 라벨 추론/Infer project label."""

    segments = [segment.lower() for segment in path.parts if len(segment) > 2]
    for hint in hints:
        if hint.lower() in segments:
            return _normalize_label(hint)
    if len(segments) >= 2:
        return _normalize_label("_".join(segments[-2:]))
    if segments:
        return _normalize_label(segments[-1])
    return "general_project"


def cluster_documents(
    documents: List[ClusterInput],
    hints: Iterable[str],
    score_map: Dict[str, str],
) -> ClusterResult:
    """문서들을 프로젝트로 군집화/Cluster documents into projects."""

    clusters: Dict[str, List[ClusterInput]] = defaultdict(list)
    for document in documents:
        label = infer_project_label(document.path.parent, hints)
        clusters[label].append(document)
    projects: List[ClusterProject] = []
    for index, (label, docs) in enumerate(sorted(clusters.items())):
        project_id = f"project_{index+1:03d}"
        doc_ids = [doc.doc_id for doc in docs]
        role_bucket_map = {
            doc.doc_id: score_map.get(doc.doc_id, doc.bucket) for doc in docs
        }
        confidence = round(min(1.0, 0.6 + len(docs) * 0.05), 2)
        reasons = [f"grouped_by:{label}", f"docs:{len(docs)}"]
        projects.append(
            ClusterProject(
                project_id=project_id,
                project_label=label,
                doc_ids=doc_ids,
                role_bucket_map=role_bucket_map,
                confidence=confidence,
                reasons=reasons,
            )
        )
    return ClusterResult(projects=projects)


def load_scores(path: Path) -> Dict[str, str]:
    """스코어 파일 로드/Load score file."""

    data = load_json(path)
    if isinstance(data, dict):
        raw_items = data.get("scores", [])
    elif isinstance(data, list):
        raw_items = data
    else:
        raw_items = []
    mapping: Dict[str, str] = {}
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        doc_id = str(item.get("doc_id", ""))
        if not doc_id:
            continue
        mapping[doc_id] = str(item.get("bucket", "archive"))
    return mapping
