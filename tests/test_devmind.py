"""Devmind 파이프라인 테스트/Tests for Devmind pipeline."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from devmind.clusterer import ClusterInput, cluster_documents
from devmind.config import ClusterProject, ClusterResult, ScanConfig
from devmind.organizer import build_plans, execute_plans, load_schema
from devmind.reporting import generate_summary
from devmind.rollback import rollback_from_journal
from devmind.rules_engine import apply_rules
from devmind.scanner import scan
from devmind.utils import load_documents, load_json


def _load_scores_map(path: Path) -> dict[str, str]:
    """스코어 파일 로드 헬퍼/Helper to load score map."""

    raw_scores = load_json(path)
    if isinstance(raw_scores, list):
        items = raw_scores
    elif isinstance(raw_scores, dict):
        candidate = raw_scores.get("scores", [])
        items = candidate if isinstance(candidate, list) else []
    else:
        items = []
    mapping: dict[str, str] = {}
    for entry in items:
        if not isinstance(entry, dict):
            continue
        doc_id = str(entry.get("doc_id", ""))
        if not doc_id:
            continue
        mapping[doc_id] = str(entry.get("bucket", "archive"))
    return mapping


@pytest.fixture()
def sample_workspace(tmp_path: Path) -> Path:
    """샘플 작업공간 생성/Create sample workspace."""

    fixture_dir = Path("tests/fixtures/sample_project")
    workspace = tmp_path / "workspace"
    shutil.copytree(fixture_dir, workspace)
    return workspace


def test_scan_collects_metadata(sample_workspace: Path, tmp_path: Path) -> None:
    """스캔이 메타데이터를 수집한다/Scan collects metadata."""

    config = ScanConfig(
        paths=[sample_workspace],
        max_size_bytes=1_000_000,
        sample_bytes=1024,
        cache_path=tmp_path / "scan.db",
        output_path=tmp_path / "scan.json",
    )
    documents = scan(config)
    names = {doc.name for doc in documents}
    assert names == {"app.py", "README.md", "data.csv"}
    app_doc = next(doc for doc in documents if doc.name == "app.py")
    assert "if __name__" in app_doc.sample_text
    assert app_doc.imports_first == []


def test_rules_classification(sample_workspace: Path, tmp_path: Path) -> None:
    """규칙 분류가 예상 버킷을 반환한다/Rules classification returns expected bucket."""

    config = ScanConfig(
        paths=[sample_workspace],
        max_size_bytes=1_000_000,
        sample_bytes=1024,
        cache_path=tmp_path / "scan.db",
        output_path=tmp_path / "scan.json",
    )
    documents = scan(config)
    rules_path = tmp_path / "rules.yml"
    rules_path.write_text(
        """
        buckets:
          scripts:
            code_hints: ['if __name__ == "__main__":']
        weights:
          name: 4
          dir: 3
          content: 2
          mimetype: 1
        project_hints: ['sample']
        """,
        encoding="utf-8",
    )
    scores_path = tmp_path / "scores.json"
    apply_rules(config.cache_path, rules_path, scores_path)
    mapping = _load_scores_map(scores_path)
    app_doc = next(doc for doc in documents if doc.name == "app.py")
    assert mapping[app_doc.doc_id] == "scripts"


def test_cluster_and_plan(sample_workspace: Path, tmp_path: Path) -> None:
    """군집과 계획이 생성된다/Cluster and plans are generated."""

    config = ScanConfig(
        paths=[sample_workspace],
        max_size_bytes=1_000_000,
        sample_bytes=1024,
        cache_path=tmp_path / "scan.db",
        output_path=tmp_path / "scan.json",
    )
    documents = scan(config)
    scores_path = tmp_path / "scores.json"
    rules_path = Path("rules.yml")
    apply_rules(config.cache_path, rules_path, scores_path)
    scores = _load_scores_map(scores_path)
    cluster_inputs = [
        ClusterInput(
            doc_id=doc.doc_id,
            path=doc.path,
            name=doc.name,
            bucket=scores.get(doc.doc_id, "archive"),
            dir_hint=doc.dir_hint,
        )
        for doc in documents
    ]
    cluster_result = cluster_documents(
        cluster_inputs,
        ["sample", "workspace"],
        scores,
    )
    assert cluster_result.projects
    schema_path = tmp_path / "schema.yml"
    schema_path.write_text(
        Path("schema.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    schema = load_schema(schema_path)
    schema = schema.__class__(
        target_root=tmp_path / "target",
        structure=schema.structure,
        conflict_policy=schema.conflict_policy,
        mode="move",
    )
    scan_index = {item["doc_id"]: item for item in load_documents(config.cache_path)}
    plans = build_plans(cluster_result, schema, scores, scan_index)
    assert plans


def test_execute_and_rollback(tmp_path: Path) -> None:
    """이동 및 롤백 흐름/Move and rollback flow."""

    source_a = tmp_path / "source" / "projA"
    source_b = tmp_path / "source" / "projB"
    source_a.mkdir(parents=True)
    source_b.mkdir(parents=True)
    file_a = source_a / "run.py"
    file_b = source_b / "run.py"
    file_a.write_text("print('a')", encoding="utf-8")
    file_b.write_text("print('b')", encoding="utf-8")
    config = ScanConfig(
        paths=[tmp_path / "source"],
        max_size_bytes=1_000_000,
        sample_bytes=1024,
        cache_path=tmp_path / "scan.db",
        output_path=tmp_path / "scan.json",
    )
    documents = scan(config)
    scores_path = tmp_path / "scores.json"
    rules_path = tmp_path / "rules.yml"
    rules_path.write_text(
        Path("rules.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    apply_rules(config.cache_path, rules_path, scores_path)
    scores = _load_scores_map(scores_path)
    project = ClusterProject(
        project_id="project_001",
        project_label="proj_auto",
        doc_ids=[doc.doc_id for doc in documents],
        role_bucket_map=scores,
        confidence=0.9,
        reasons=["test"],
    )
    cluster_result = ClusterResult(projects=[project])
    schema_path = tmp_path / "schema.yml"
    schema_path.write_text(
        Path("schema.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    schema = load_schema(schema_path)
    schema = schema.__class__(
        target_root=tmp_path / "target",
        structure=schema.structure,
        conflict_policy=schema.conflict_policy,
        mode="move",
    )
    scan_index = {item["doc_id"]: item for item in load_documents(config.cache_path)}
    plans = build_plans(cluster_result, schema, scores, scan_index)
    journal_path = tmp_path / "journal.jsonl"
    execute_plans(plans, journal_path, "move")
    target_files = sorted((tmp_path / "target").rglob("run*.py"))
    assert len(target_files) == 2
    report_path = tmp_path / "report.html"
    generate_summary(
        cluster_result,
        journal_path,
        report_path,
        report_path.with_suffix(".json"),
        report_path.with_suffix(".csv"),
    )
    assert report_path.exists()
    rollback_from_journal(journal_path)
    assert file_a.exists()
    assert file_b.exists()
