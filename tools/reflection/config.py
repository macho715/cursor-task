"""태스크 리플렉션 설정 구성. Task reflection configuration module."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping

from .exceptions import ReflectionError


@dataclass(slots=True)
class ReflectionConfig:
    """리플렉션 파라미터 컨테이너. Reflection parameter container."""

    type_complexity: Dict[str, float] = field(
        default_factory=lambda: {
            "doc": 0.8,
            "cli": 0.9,
            "config": 0.9,
            "code": 1.0,
            "ide": 1.0,
            "mcp": 1.2,
            "test": 1.1,
        }
    )
    title_bonus: Dict[str, float] = field(
        default_factory=lambda: {
            "complex": 0.3,
            "advanced": 0.2,
            "integration": 0.2,
            "optimization": 0.2,
            "validation": 0.1,
            "analysis": 0.1,
            "reflection": 0.1,
            "management": 0.1,
        }
    )
    clamp_min: float = 0.8
    clamp_max: float = 3.0

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ReflectionConfig":
        """매핑 기반 설정 생성. Build configuration from mapping."""

        type_complexity = dict(raw.get("type_complexity", {}))
        title_bonus = dict(raw.get("title_bonus", {}))
        base = cls()
        clamp_min = float(raw.get("clamp_min", base.clamp_min))
        clamp_max = float(raw.get("clamp_max", base.clamp_max))
        if type_complexity:
            base.type_complexity.update(type_complexity)
        if title_bonus:
            base.title_bonus.update(title_bonus)
        base.clamp_min = clamp_min
        base.clamp_max = clamp_max
        return base

    def merge(self, overrides: Mapping[str, Any]) -> "ReflectionConfig":
        """오버라이드 반영 설정 복제. Clone config with overrides."""

        return ReflectionConfig.from_mapping(
            {
                "type_complexity": {
                    **self.type_complexity,
                    **overrides.get("type_complexity", {}),
                },
                "title_bonus": {
                    **self.title_bonus,
                    **overrides.get("title_bonus", {}),
                },
                "clamp_min": overrides.get("clamp_min", self.clamp_min),
                "clamp_max": overrides.get("clamp_max", self.clamp_max),
            }
        )


def _load_raw_config(path: Path) -> Any:
    """구성 파일 파싱 유틸. Configuration file parsing utility."""

    if not path.exists():
        message = f"구성 파일을 찾을 수 없습니다: {path}"
        raise ReflectionError(message)
    if path.suffix.lower() in {".json"}:
        import json

        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:  # pragma: no cover
            message = "PyYAML이 필요합니다. Install PyYAML for YAML configs."
            raise ReflectionError(message) from exc
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    message = f"지원하지 않는 구성 형식입니다: {path.suffix}"
    raise ReflectionError(message)


def load_config(path: Path | str) -> ReflectionConfig:
    """파일 기반 설정 로드. Load configuration from file."""

    raw = _load_raw_config(Path(path))
    if not isinstance(raw, Mapping):
        raise ReflectionError(
            "구성 파일 최상위는 매핑이어야 합니다. Config root must be mapping."
        )
    return ReflectionConfig.from_mapping(raw)
