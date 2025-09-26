"""유틸리티 함수 모음/Collection of utility helpers."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Protocol,
    Tuple,
    TypeVar,
    cast,
)

T = TypeVar("T")
HasherFactory = Callable[[], "HashProtocol"]

UUID_NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")

PATH_PATTERN = re.compile(r"([A-Za-z]:\\\\[^\s]+|/[^\s]+)")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
DIGIT_PATTERN = re.compile(r"\d{4,}")


def ensure_directory(path: Path) -> None:
    """디렉터리 생성 보장/Ensure directory exists."""

    path.mkdir(parents=True, exist_ok=True)


class ConsoleProtocol(Protocol):
    """콘솔 인터페이스 규약/Console interface protocol."""

    def print(self, message: str) -> None:
        """메시지 출력/Print message."""


class HashProtocol(Protocol):
    """해시 객체 규약/Hash object protocol."""

    def update(self, data: bytes) -> None:
        """해시 데이터 업데이트/Update hash with data."""

    def hexdigest(self) -> str:
        """해시 헥사 문자열 반환/Return hexadecimal digest."""


_BLAKE3_FACTORY: HasherFactory | None = None


def _load_blake3_factory() -> HasherFactory | None:
    """BLAKE3 생성기 로드/Load BLAKE3 factory."""

    global _BLAKE3_FACTORY
    if _BLAKE3_FACTORY is not None:
        return _BLAKE3_FACTORY
    try:
        module = importlib.import_module("blake3")
        factory = getattr(module, "blake3", None)
        if callable(factory):
            _BLAKE3_FACTORY = cast(HasherFactory, factory)
            return _BLAKE3_FACTORY
    except Exception:  # pragma: no cover - optional dependency
        pass
    _BLAKE3_FACTORY = None
    return None


def get_console() -> ConsoleProtocol:
    """콘솔 인스턴스 제공/Provide console instance."""

    try:
        console_module = importlib.import_module("rich.console")
        console_cls = getattr(console_module, "Console", None)
        if callable(console_cls):
            return cast(ConsoleProtocol, console_cls())
    except Exception:  # pragma: no cover - best effort import
        pass

    class SimpleConsole:
        """단순 콘솔 구현/Simple console implementation."""

        def print(self, message: str) -> None:
            """텍스트 출력/Print message."""

            print(message)

    return cast(ConsoleProtocol, SimpleConsole())


def iter_with_progress(iterable: Iterable[T], description: str = "") -> Iterator[T]:
    """진행 표시 반복기/Iterate with optional progress."""

    try:
        progress_module = importlib.import_module("rich.progress")
        track_fn = getattr(progress_module, "track", None)
        if callable(track_fn):
            yield from track_fn(iterable, description=description)
            return
    except Exception:  # pragma: no cover - best effort import
        pass
    yield from iterable


def _ensure_dict(data: object) -> Dict[str, Any]:
    """사전 객체 보장/Ensure dictionary object."""

    if isinstance(data, dict):
        return {str(key): value for key, value in data.items()}
    return {}


def load_yaml_or_json_dict(path: Path) -> Dict[str, Any]:
    """YAML/JSON 사전 로드/Load dict from YAML or JSON."""

    try:
        yaml_module = importlib.import_module("yaml")
    except Exception:  # pragma: no cover - optional dependency
        return _ensure_dict(load_json(path))
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        loaded = yaml_module.safe_load(text)
    except Exception:
        return _ensure_dict(load_json(path))
    return _ensure_dict(loaded)


def compute_blake3(path: Path) -> str:
    """파일 해시 계산(BLAKE3 선호)/Compute file hash preferring BLAKE3."""

    factory = _load_blake3_factory()
    hasher: HashProtocol
    if factory is not None:
        hasher = factory()
    else:
        hasher = cast(HashProtocol, hashlib.blake2b(digest_size=32))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def mask_sensitive_text(value: str) -> str:
    """민감 정보 마스킹/Mask sensitive data."""

    masked = PATH_PATTERN.sub("[PATH]", value)
    masked = EMAIL_PATTERN.sub("[EMAIL]", masked)
    masked = DIGIT_PATTERN.sub("####", masked)
    return masked


def generate_doc_id(path: Path, digest: str) -> str:
    """문서 ID 생성/Generate document identifier."""

    return str(uuid.uuid5(UUID_NAMESPACE, f"{path.as_posix()}::{digest}"))


def now_ts() -> float:
    """현재 타임스탬프 반환/Return current timestamp."""

    return time.time()


@contextmanager
def sqlite_connection(db_path: Path) -> Iterator[sqlite3.Connection]:
    """SQLite 연결 컨텍스트/SQLite connection context."""

    ensure_directory(db_path.parent)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.commit()
        connection.close()


def store_documents(db_path: Path, documents: Iterable[Dict[str, Any]]) -> None:
    """문서 메타데이터 저장/Store document metadata."""

    with sqlite_connection(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT OR REPLACE INTO documents (doc_id, payload) VALUES (?, ?)",
            ((doc["doc_id"], json.dumps(doc, ensure_ascii=False)) for doc in documents),
        )


def load_documents(db_path: Path) -> List[Dict[str, Any]]:
    """문서 메타데이터 로드/Load document metadata."""

    if not db_path.exists():
        return []
    with sqlite_connection(db_path) as connection:
        cursor = connection.execute("SELECT payload FROM documents")
        return [json.loads(row[0]) for row in cursor.fetchall()]


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    """JSONL 파일 작성/Write JSONL file."""

    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + os.linesep)


def append_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    """JSONL 파일 추가 작성/Append JSONL file."""

    ensure_directory(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + os.linesep)


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """JSONL 파일 읽기/Read JSONL file."""

    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def save_json(path: Path, data: object) -> None:
    """JSON 파일 저장/Save JSON file."""

    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def load_json(path: Path) -> object:
    """JSON 파일 로드/Load JSON file."""

    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def score_match(value: str, keywords: Iterable[str]) -> Tuple[int, List[str]]:
    """키워드 매칭 점수/Score keyword matches."""

    matches: List[str] = []
    score = 0
    lowered = value.lower()
    for keyword in keywords:
        if keyword.lower() in lowered:
            matches.append(keyword)
            score += 1
    return score, matches
