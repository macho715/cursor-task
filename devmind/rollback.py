"""롤백 유틸리티/Rollback utility."""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from .utils import ensure_directory, read_jsonl

console = Console()


def rollback_from_journal(journal_path: Path) -> None:
    """저널 기반 롤백 수행/Roll back using journal."""

    entries = read_jsonl(journal_path)
    if not entries:
        console.print("[yellow]저널 데이터가 없습니다/No journal data found.[/yellow]")
        return
    for entry in reversed(entries):
        original_raw = entry.get("original_path")
        target_raw = entry.get("target_path")
        if not isinstance(original_raw, str) or not isinstance(target_raw, str):
            continue
        original = Path(original_raw)
        target = Path(target_raw)
        if not target.exists():
            continue
        ensure_directory(original.parent)
        shutil.move(str(target), str(original))
    message = (
        "[green]총 {count}개 이동 롤백 완료/Rolled back {count} moves.[/green]"
    ).format(count=len(entries))
    console.print(message)
