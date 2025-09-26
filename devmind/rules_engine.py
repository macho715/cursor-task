"""규칙 기반 분류 엔진/Rule-based classification engine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import yaml
from rich.console import Console

from .config import BucketRule, FileDocument, RuleConfig
from .utils import load_documents, save_json, score_match

console = Console()


def load_rule_config(path: Path) -> RuleConfig:
    """규칙 설정 로드/Load rule configuration."""

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    data = raw if isinstance(raw, dict) else {}
    buckets_raw = data.get("buckets", {})
    if isinstance(buckets_raw, dict):
        bucket_items = list(buckets_raw.items())
    else:
        bucket_items = []
    buckets = {
        str(name): BucketRule(
            name=str(name),
            exts=[str(ext).lower() for ext in config.get("exts", [])],
            name_keywords=[str(item) for item in config.get("name_keywords", [])],
            dir_keywords=[str(item) for item in config.get("dir_keywords", [])],
            code_hints=[str(item) for item in config.get("code_hints", [])],
            imports=[str(item) for item in config.get("imports", [])],
            title_keywords=[str(item) for item in config.get("title_keywords", [])],
        )
        for name, config in bucket_items
        if isinstance(config, dict)
    }
    weights_raw = data.get("weights", {})
    weights = (
        {str(key): int(value) for key, value in weights_raw.items()}
        if isinstance(weights_raw, dict)
        else {}
    )
    hints_raw = data.get("project_hints", [])
    project_hints = [str(item) for item in hints_raw]
    return RuleConfig(buckets=buckets, weights=weights, project_hints=project_hints)


@dataclass(slots=True)
class ScoredDocument:
    """스코어가 부여된 문서/Document with scores."""

    doc_id: str
    best_bucket: str
    score: float
    reasons: List[str]


def score_document(document: FileDocument, rule_config: RuleConfig) -> ScoredDocument:
    """문서 규칙 스코어링/Score document for rules."""

    best_bucket = "archive"
    best_score = 0
    best_reasons: List[str] = ["fallback"]
    for bucket_name, rule in rule_config.buckets.items():
        score = 0
        reasons: List[str] = []
        if document.ext in rule.exts:
            score += rule_config.weights.get("mimetype", 1)
            reasons.append(f"ext:{document.ext}")
        name_score, name_matches = score_match(document.name, rule.name_keywords)
        if name_score:
            score += name_score * rule_config.weights.get("name", 1)
            reasons.append(f"name:{','.join(name_matches)}")
        dir_score, dir_matches = score_match(document.dir_hint, rule.dir_keywords)
        if dir_score:
            score += dir_score * rule_config.weights.get("dir", 1)
            reasons.append(f"dir:{','.join(dir_matches)}")
        content_score, content_matches = score_match(
            document.sample_text, rule.code_hints
        )
        if content_score:
            score += content_score * rule_config.weights.get("content", 1)
            reasons.append(f"content:{','.join(content_matches)}")
        import_score, import_matches = score_match(
            " ".join(document.imports_first), rule.imports
        )
        if import_score:
            score += import_score * rule_config.weights.get("content", 1)
            reasons.append(f"imports:{','.join(import_matches)}")
        title_score, title_matches = score_match(
            " ".join(document.md_headings), rule.title_keywords
        )
        if title_score:
            score += title_score * rule_config.weights.get("content", 1)
            reasons.append(f"titles:{','.join(title_matches)}")
        if score > best_score:
            best_score = score
            best_bucket = bucket_name
            best_reasons = reasons or ["matched"]
    return ScoredDocument(
        doc_id=document.doc_id,
        best_bucket=best_bucket,
        score=float(best_score),
        reasons=best_reasons,
    )


def apply_rules(
    db_path: Path,
    rule_config_path: Path,
    output_path: Path,
) -> List[Dict[str, object]]:
    """규칙 적용 실행/Execute rule application."""

    documents = [FileDocument.from_dict(item) for item in load_documents(db_path)]
    if not documents:
        console.print("[yellow]스캔 데이터가 없습니다/No scan data found.[/yellow]")
        return []
    config = load_rule_config(rule_config_path)
    results: List[Dict[str, object]] = []
    for document in documents:
        scored = score_document(document, config)
        results.append(
            {
                "doc_id": scored.doc_id,
                "bucket": scored.best_bucket,
                "score": scored.score,
                "reasons": scored.reasons,
            }
        )
    save_json(output_path, results)
    message = (
        "[green]총 {count}개 파일 규칙 분류 완료/Completed rule classification"
        " for {count} files.[/green]"
    ).format(count=len(results))
    console.print(message)
    return results
