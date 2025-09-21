"""리플렉션 모듈 단위 테스트. Reflection module unit tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest
from reflection import ReflectionConfig, TaskReflector, load_config


def sample_tasks() -> Dict[str, Any]:
    """샘플 태스크 데이터 제공. Provide sample task data."""

    return {
        "meta": {"source": "sample.json"},
        "tasks": [
            {
                "id": "alpha",
                "title": "Alpha Task",
                "module": "core",
                "type": "code",
                "deps": [],
            },
            {
                "id": "beta",
                "title": "Beta Integration",
                "module": "core",
                "type": "integration",
                "deps": ["alpha"],
            },
        ],
    }


def test_reflector_reflects_tasks(tmp_path: Path) -> None:
    """리플렉터가 태스크를 리플렉션. Reflector processes task list."""

    reflector = TaskReflector()
    data = sample_tasks()
    result = reflector.reflect(data)
    assert len(result.tasks) == 2
    assert all("complexity" in task for task in result.tasks)
    report = reflector.build_report(data, result)
    assert "태스크 수" in report

    output_file = tmp_path / "out.json"
    output_file.write_text(json.dumps(result.to_dict()), encoding="utf-8")
    stored = json.loads(output_file.read_text(encoding="utf-8"))
    assert stored["meta"]["topo_order"] == ["alpha", "beta"]


def test_config_override() -> None:
    """설정 오버라이드 적용 확인. Validate config override application."""

    overrides = {"type_complexity": {"integration": 2.0}}
    config = ReflectionConfig().merge(overrides)
    reflector = TaskReflector(config)
    data = sample_tasks()
    result = reflector.reflect(data)
    integration_task = None
    for task in result.tasks:
        if task["id"] == "beta":
            integration_task = task
            break
    assert integration_task is not None
    assert integration_task["complexity"] >= 2.0


@pytest.mark.parametrize("config_ext", ["json"])
def test_load_config(tmp_path: Path, config_ext: str) -> None:
    """구성 파일 로드 확인. Ensure config file loading."""

    config_payload = {"type_complexity": {"integration": 1.7}}
    config_file = tmp_path / f"config.{config_ext}"
    config_file.write_text(json.dumps(config_payload), encoding="utf-8")
    _ = load_config(config_file)
    reflector = TaskReflector(ReflectionConfig.from_mapping(config_payload))
    result = reflector.reflect(sample_tasks())
    assert result.meta["cycles_detected"] == 0
