"""설정 데이터 구조 정의/Define configuration data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


@dataclass(slots=True)
class ScanConfig:
    """스캔 파라미터 설정/Configure scanning parameters."""

    paths: Iterable[Path]
    max_size_bytes: int
    sample_bytes: int
    cache_path: Path = Path(".cache/devmind_scan.db")
    output_path: Path = Path(".cache/scan_results.json")


@dataclass(slots=True)
class BucketRule:
    """버킷 규칙 정의/Define bucket rule."""

    name: str
    exts: List[str] = field(default_factory=list)
    name_keywords: List[str] = field(default_factory=list)
    dir_keywords: List[str] = field(default_factory=list)
    code_hints: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    title_keywords: List[str] = field(default_factory=list)


@dataclass(slots=True)
class RuleConfig:
    """규칙 구성 래퍼/Wrapper for rule configuration."""

    buckets: Dict[str, BucketRule]
    weights: Mapping[str, int]
    project_hints: List[str]


@dataclass(slots=True)
class SchemaConfig:
    """스키마 설정 값/Schema configuration values."""

    target_root: Path
    structure: List[str]
    conflict_policy: str
    mode: str


@dataclass(slots=True)
class JournalEntry:
    """조직화 작업 로그 항목/Organize operation journal entry."""

    original_path: Path
    target_path: Path
    doc_id: str
    blake3: str
    project_id: str
    bucket: str
    status: str
    timestamp: float


@dataclass(slots=True)
class ClusterProject:
    """군집된 프로젝트 메타/Clustered project metadata."""

    project_id: str
    project_label: str
    doc_ids: List[str]
    role_bucket_map: Dict[str, str]
    confidence: float
    reasons: List[str]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ClusterProject":
        """사전에서 프로젝트 생성/Create project from dict."""

        doc_ids = [str(value) for value in payload.get("doc_ids", [])]
        role_map_raw = payload.get("role_bucket_map", {})
        role_map = (
            {
                str(key): str(value)
                for key, value in role_map_raw.items()
                if isinstance(key, str)
            }
            if isinstance(role_map_raw, dict)
            else {}
        )
        reasons_raw = payload.get("reasons", [])
        reasons = [str(reason) for reason in reasons_raw]
        return cls(
            project_id=str(payload.get("project_id", "")),
            project_label=str(payload.get("project_label", "")),
            doc_ids=doc_ids,
            role_bucket_map=role_map,
            confidence=float(payload.get("confidence", 0.0)),
            reasons=reasons,
        )


@dataclass(slots=True)
class ClusterResult:
    """군집 결과 래퍼/Wrapper for cluster results."""

    projects: List[ClusterProject]


@dataclass(slots=True)
class FileDocument:
    """파일 메타 데이터 구조/File metadata structure."""

    doc_id: str
    path: Path
    name: str
    ext: str
    size: int
    mtime: float
    blake3: str
    mimetype: str
    dir_hint: str
    imports_first: List[str]
    top_comment: Optional[str]
    md_headings: List[str]
    json_root_keys: List[str]
    csv_header: List[str]
    sample_text: str

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "FileDocument":
        """사전에서 파일 문서 생성/Create file document from dict."""

        return cls(
            doc_id=str(payload.get("doc_id", "")),
            path=Path(str(payload.get("path", ""))),
            name=str(payload.get("name", "")),
            ext=str(payload.get("ext", "")),
            size=int(payload.get("size", 0)),
            mtime=float(payload.get("mtime", 0.0)),
            blake3=str(payload.get("blake3", "")),
            mimetype=str(payload.get("mimetype", "application/octet-stream")),
            dir_hint=str(payload.get("dir_hint", "")),
            imports_first=[str(value) for value in payload.get("imports_first", [])],
            top_comment=(
                str(payload["top_comment"])
                if payload.get("top_comment") is not None
                else None
            ),
            md_headings=[str(value) for value in payload.get("md_headings", [])],
            json_root_keys=[str(value) for value in payload.get("json_root_keys", [])],
            csv_header=[str(value) for value in payload.get("csv_header", [])],
            sample_text=str(payload.get("sample_text", "")),
        )


@dataclass(slots=True)
class BucketScore:
    """버킷 스코어 데이터/Bucket score data."""

    doc_id: str
    bucket: str
    score: float
    reasons: List[str]


@dataclass(slots=True)
class OrganizePlan:
    """파일 이동 계획/File relocation plan."""

    doc_id: str
    project_id: str
    project_label: str
    bucket: str
    source_path: Path
    target_path: Path
    hash_suffix: str
