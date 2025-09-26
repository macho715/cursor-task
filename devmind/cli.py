"""CLI 엔트리포인트/CLI entry point."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Callable, Protocol, TypeVar, cast

from .clusterer import ClusterInput, cluster_documents, load_scores
from .config import ClusterProject, ClusterResult, ScanConfig, SchemaConfig
from .organizer import build_plans, ensure_schema_structure, execute_plans, load_schema
from .reporting import generate_summary
from .rollback import rollback_from_journal
from .rules_engine import apply_rules
from .scanner import scan
from .utils import get_console, load_documents, load_json, save_json

TFunc = TypeVar("TFunc", bound=Callable[..., Any])


class TyperAppProtocol(Protocol):
    """Typer 앱 인터페이스/Typer app interface."""

    def command(self, *args: Any, **kwargs: Any) -> Callable[[TFunc], TFunc]:
        """명령 데코레이터 반환/Return command decorator."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """애플리케이션 실행/Invoke application."""


class TyperModuleProtocol(Protocol):
    """Typer 모듈 인터페이스/Typer module interface."""

    def Typer(self, *args: Any, **kwargs: Any) -> TyperAppProtocol:
        """Typer 앱 생성/Create Typer app."""

    def Option(self, default: Any = ..., **kwargs: Any) -> Any:
        """옵션 생성/Create option."""

    def Argument(self, default: Any = ..., **kwargs: Any) -> Any:
        """인자 생성/Create argument."""


class _TyperFallbackApp:
    """Typer 대체 앱/Fallback Typer app."""

    def command(self, *args: Any, **kwargs: Any) -> Callable[[TFunc], TFunc]:
        """기본 데코레이터 반환/Return identity decorator."""

        def decorator(func: TFunc) -> TFunc:
            """원본 함수 반환/Return original function."""

            return func

        return decorator

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        """대체 실행/No-op execution."""

        print("Typer module is unavailable.")


class _TyperFallbackModule:
    """Typer 대체 모듈/Fallback Typer module."""

    def Typer(self, *args: Any, **kwargs: Any) -> TyperAppProtocol:
        """대체 앱 생성/Create fallback app."""

        return _TyperFallbackApp()

    def Option(self, default: Any = ..., **kwargs: Any) -> Any:
        """기본값 반환/Return default value."""

        return default

    def Argument(self, default: Any = ..., **kwargs: Any) -> Any:
        """기본값 반환/Return default value."""

        return default


def _load_typer_module() -> TyperModuleProtocol:
    """Typer 모듈 로드/Load Typer module."""

    try:
        module = importlib.import_module("typer")
        return cast(TyperModuleProtocol, module)
    except Exception:  # pragma: no cover - optional dependency
        return _TyperFallbackModule()


typer_module = _load_typer_module()
Option = typer_module.Option
Argument = typer_module.Argument
app = typer_module.Typer(help="프로젝트 자동 정리 CLI/Project organization CLI")
console = get_console()


@app.command()
def scan_cmd(
    paths: list[str] = Option(..., help="스캔 경로 목록/Paths to scan"),
    max_size: int = Option(500 * 1024 * 1024, help="최대 파일 크기/Max file size"),
    sample_bytes: int = Option(4096, help="샘플 바이트 수/Sample bytes"),
) -> None:
    """scan 명령 실행/Execute scan command."""

    config = ScanConfig(
        paths=[Path(p) for p in paths],
        max_size_bytes=max_size,
        sample_bytes=sample_bytes,
    )
    scan(config)


@app.command()
def rules(
    config_path: Path = Option(..., help="규칙 설정 경로/Path to rules config"),
    emit: Path = Option(Path(".cache/scores.json"), help="출력 경로/Output path"),
) -> None:
    """규칙 엔진 실행/Run rules engine."""

    apply_rules(Path(".cache/devmind_scan.db"), config_path, emit)


@app.command()
def cluster(
    model: str = Option("heuristic", help="모델 이름/Model name"),
    budget: str = Option("$0", help="예산/Budget"),
    project_mode: bool = Option(True, help="프로젝트 모드/Project mode"),
    out: Path = Option(Path(".cache/projects.json"), help="결과 경로/Output path"),
) -> None:
    """군집 작업 실행/Execute clustering."""

    documents_raw = load_documents(Path(".cache/devmind_scan.db"))
    scores = load_scores(Path(".cache/scores.json"))
    documents: list[ClusterInput] = []
    for item in documents_raw:
        doc_id = str(item.get("doc_id", ""))
        path_value = Path(str(item.get("path", "")))
        name_value = str(item.get("name", ""))
        bucket_value = scores.get(doc_id, "archive")
        dir_hint_value = str(item.get("dir_hint", ""))
        documents.append(
            ClusterInput(
                doc_id=doc_id,
                path=path_value,
                name=name_value,
                bucket=bucket_value,
                dir_hint=dir_hint_value,
            )
        )
    if Path("rules.yml").exists():
        raw_rules = load_json(Path("rules.yml"))
        rules_data = raw_rules if isinstance(raw_rules, dict) else {}
    else:
        rules_data = {}
    hints = [str(hint) for hint in rules_data.get("project_hints", ["project"])]
    cluster_result = cluster_documents(documents, hints, scores)
    payload = {"projects": [project.__dict__ for project in cluster_result.projects]}
    save_json(out, payload)
    console.print(
        f"[green]총 {len(cluster_result.projects)}개 프로젝트 군집/Clustered"
        f" {len(cluster_result.projects)} projects.[/green]"
    )


@app.command()
def organize(
    projects: Path = Option(
        Path(".cache/projects.json"), help="프로젝트 파일/Projects file"
    ),
    target: Path = Option(Path("C:/PROJECTS_STRUCT"), help="대상 루트/Target root"),
    schema_path: Path = Option(Path("schema.yml"), help="스키마 경로/Schema path"),
    clusters: Path = Option(
        Path(".cache/projects.json"), help="클러스터 경로/Cluster path"
    ),
    mode: str = Option("move", help="이동 모드/Move mode"),
    conflict: str = Option("version", help="충돌 정책/Conflict policy"),
    journal: Path = Option(Path(".cache/journal.jsonl"), help="저널 경로/Journal path"),
) -> None:
    """조직화 수행/Perform organization."""

    schema = load_schema(schema_path)
    schema = SchemaConfig(
        target_root=target,
        structure=schema.structure,
        conflict_policy=conflict,
        mode=mode,
    )
    ensure_schema_structure(schema.target_root, schema.structure)
    raw_cluster = load_json(clusters)
    if isinstance(raw_cluster, dict):
        cluster_payloads = [
            payload
            for payload in raw_cluster.get("projects", [])
            if isinstance(payload, dict)
        ]
    else:
        cluster_payloads = []
    cluster_result = ClusterResult(
        projects=[ClusterProject.from_dict(payload) for payload in cluster_payloads]
    )
    scan_documents = load_documents(Path(".cache/devmind_scan.db"))
    scan_index = {
        str(item.get("doc_id", "")): item for item in scan_documents if "doc_id" in item
    }
    score_map = load_scores(Path(".cache/scores.json"))
    plans = build_plans(cluster_result, schema, score_map, scan_index)
    execute_plans(plans, journal, schema.mode)


@app.command()
def report(
    clusters: Path = Option(
        Path(".cache/projects.json"), help="클러스터 파일/Cluster file"
    ),
    journal: Path = Option(Path(".cache/journal.jsonl"), help="저널 파일/Journal file"),
    out: Path = Option(
        Path("reports/projects_summary.html"), help="HTML 출력/HTML output"
    ),
) -> None:
    """리포트 생성/Generate report."""

    raw_cluster = load_json(clusters)
    if isinstance(raw_cluster, dict):
        cluster_payloads = [
            payload
            for payload in raw_cluster.get("projects", [])
            if isinstance(payload, dict)
        ]
    else:
        cluster_payloads = []
    cluster_result = ClusterResult(
        projects=[ClusterProject.from_dict(payload) for payload in cluster_payloads]
    )
    html_path = out
    json_path = out.with_suffix(".json")
    csv_path = out.with_suffix(".csv")
    generate_summary(cluster_result, journal, html_path, json_path, csv_path)


@app.command()
def rollback(journal: Path = Argument(..., help="저널 경로/Journal path")) -> None:
    """저널 롤백 실행/Execute journal rollback."""

    rollback_from_journal(journal)


def main() -> None:
    """엔트리 포인트/Entry point."""

    app()


if __name__ == "__main__":
    main()
