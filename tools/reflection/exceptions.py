"""리플렉션 예외 정의. Reflection exceptions definitions."""

from __future__ import annotations


class ReflectionError(Exception):
    """리플렉션 도메인 기본 예외. Base reflection domain error."""


class TaskValidationError(ReflectionError):
    """태스크 데이터 검증 오류. Task data validation error."""
