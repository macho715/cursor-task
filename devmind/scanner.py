"""파일 시스템 스캐너/File system scanner."""

from __future__ import annotations

import csv
import json
import mimetypes
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

from .config import FileDocument, ScanConfig
from .utils import (
    compute_blake3,
    ensure_directory,
    generate_doc_id,
    get_console,
    iter_with_progress,
    mask_sensitive_text,
    store_documents,
)

console = get_console()


def _read_text_sample(path: Path, sample_bytes: int) -> str:
    """텍스트 샘플 추출/Extract text sample."""

    try:
        raw = path.read_bytes()[:sample_bytes]
    except OSError:
        return ""
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        decoded = raw.decode("latin-1", errors="ignore")
    return mask_sensitive_text(decoded)


def _extract_imports(text: str) -> List[str]:
    """임포트 목록 추출/Extract imports list."""

    imports: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            imports.append(stripped)
        elif stripped.startswith("from ") and " import " in stripped:
            imports.append(stripped)
        if len(imports) >= 5:
            break
    return imports


def _extract_top_comment(text: str) -> Optional[str]:
    """상단 주석 추출/Extract top comment."""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    first = lines[0]
    if first.startswith("#"):
        return first[:200]
    if first.startswith('""') or first.startswith("'''"):
        return first[:200]
    return None


def _extract_markdown_headings(text: str) -> List[str]:
    """마크다운 헤더 추출/Extract markdown headings."""

    headings: List[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            stripped = line.strip("# ")
            if stripped:
                headings.append(stripped)
        if len(headings) >= 5:
            break
    return headings


def _extract_json_keys(text: str) -> List[str]:
    """JSON 루트 키 추출/Extract JSON root keys."""

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        return list(data.keys())[:10]
    return []


def _extract_csv_header(path: Path) -> List[str]:
    """CSV 헤더 추출/Extract CSV header."""

    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
    except (OSError, UnicodeDecodeError):
        header = []
    return header[:20]


def _detect_mimetype(path: Path) -> str:
    """MIME 타입 감지/Detect MIME type."""

    guess, _ = mimetypes.guess_type(path.name)
    return guess or "application/octet-stream"


def _scan_file(path: Path, config: ScanConfig) -> Optional[FileDocument]:
    """단일 파일 스캔/Scan single file."""

    try:
        size = path.stat().st_size
        mtime = path.stat().st_mtime
    except OSError:
        return None
    if size > config.max_size_bytes:
        return None
    digest = compute_blake3(path)
    doc_id = generate_doc_id(path, digest)
    sample_text = _read_text_sample(path, config.sample_bytes)
    mimetype_value = _detect_mimetype(path)
    imports = _extract_imports(sample_text)
    top_comment = _extract_top_comment(sample_text)
    headings = _extract_markdown_headings(sample_text)
    json_keys = _extract_json_keys(sample_text)
    csv_header = _extract_csv_header(path) if path.suffix.lower() == ".csv" else []
    dir_hint = str(path.parent.name)
    return FileDocument(
        doc_id=doc_id,
        path=path,
        name=path.name,
        ext=path.suffix.lower(),
        size=size,
        mtime=mtime,
        blake3=digest,
        mimetype=mimetype_value,
        dir_hint=dir_hint,
        imports_first=imports,
        top_comment=top_comment,
        md_headings=headings,
        json_root_keys=json_keys,
        csv_header=csv_header,
        sample_text=sample_text,
    )


def scan(config: ScanConfig) -> List[FileDocument]:
    """경로 스캔 실행/Execute path scanning."""

    documents: List[FileDocument] = []
    paths = [Path(path).expanduser() for path in config.paths]
    ensure_directory(config.cache_path.parent)
    with ThreadPoolExecutor() as executor:
        futures = []
        for root in paths:
            if not root.exists():
                console.print(f"[yellow]경로 없음/Path missing:[/] {root}")
                continue
            for file_path in iter_with_progress(
                list(root.rglob("*")),
                description=f"스캔 중/Scanning {root}",
            ):
                if file_path.is_file():
                    futures.append(executor.submit(_scan_file, file_path, config))
        for future in futures:
            document = future.result()
            if document:
                documents.append(document)
    serialized = []
    for document in documents:
        doc_dict = asdict(document)
        doc_dict["path"] = str(document.path)
        serialized.append(doc_dict)
    store_documents(config.cache_path, serialized)
    ensure_directory(config.output_path.parent)
    with config.output_path.open("w", encoding="utf-8") as handle:
        json.dump(serialized, handle, ensure_ascii=False, indent=2)
    message = (
        "[green]총 {count}개 파일 스캔 완료/Completed scanning {count} files.[/green]"
    ).format(count=len(documents))
    console.print(message)
    return documents
