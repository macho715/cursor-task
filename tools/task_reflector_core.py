"""태스크 리플렉션 코어 모듈 | Task reflection core module."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence, Tuple


DEFAULT_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


@dataclass(frozen=True)
class TaskSpec:
    """태스크 원본 스펙 | Original task specification."""

    task_id: str
    title: str = ""
    task_type: str = "code"
    dependencies: Tuple[str, ...] = field(default_factory=tuple)
    module: str = "unknown"
    extra: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TaskSpec":
        """매핑으로부터 태스크 생성 | Build task from mapping."""

        dependencies = tuple(payload.get("deps", []))
        extra = {
            key: value
            for key, value in payload.items()
            if key not in {"id", "title", "type", "deps", "module"}
        }
        return cls(
            task_id=str(payload["id"]),
            title=str(payload.get("title", "")),
            task_type=str(payload.get("type", "code")),
            dependencies=dependencies,
            module=str(payload.get("module", "unknown")),
            extra=extra,
        )

    def to_mapping(self) -> Dict[str, Any]:
        """태스크를 매핑으로 변환 | Convert task to mapping."""

        payload: Dict[str, Any] = {
            "id": self.task_id,
            "title": self.title,
            "type": self.task_type,
            "deps": list(self.dependencies),
            "module": self.module,
        }
        payload.update(self.extra)
        return payload


@dataclass(frozen=True)
class ReflectedTask(TaskSpec):
    """리플렉션된 태스크 스펙 | Reflected task specification."""

    order: int = 0
    complexity: float = 0.0

    def to_mapping(self) -> Dict[str, Any]:
        """리플렉션 결과 매핑 변환 | Convert reflection result to mapping."""

        payload = super().to_mapping()
        payload.update({"order": self.order, "complexity": round(self.complexity, 2)})
        return payload


@dataclass(frozen=True)
class TaskDataset:
    """태스크 데이터 세트 | Task dataset container."""

    tasks: List[TaskSpec]
    meta: MutableMapping[str, Any] = field(default_factory=dict)
    extras: MutableMapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TaskDataset":
        """매핑으로부터 데이터 세트 생성 | Build dataset from mapping."""

        tasks = [TaskSpec.from_mapping(task) for task in payload.get("tasks", [])]
        meta: MutableMapping[str, Any] = dict(payload.get("meta", {}))
        extras: MutableMapping[str, Any] = {
            key: value
            for key, value in payload.items()
            if key not in {"tasks", "meta"}
        }
        return cls(tasks=tasks, meta=meta, extras=extras)

    def to_mapping(self, tasks: Sequence[ReflectedTask], meta: Mapping[str, Any]) -> Dict[str, Any]:
        """리플렉션 결과를 병합 | Merge reflection results into mapping."""

        payload: Dict[str, Any] = dict(self.extras)
        payload["tasks"] = [task.to_mapping() for task in tasks]
        payload["meta"] = dict(meta)
        return payload


@dataclass(frozen=True)
class ReflectionResult:
    """리플렉션 결과 | Reflection result container."""

    dataset: TaskDataset
    tasks: List[ReflectedTask]
    topo_order: List[str]
    cycles: List[List[str]]
    meta: Dict[str, Any]

    def to_mapping(self) -> Dict[str, Any]:
        """리플렉션 결과 매핑 반환 | Build mapping for reflected dataset."""

        full_meta = dict(self.dataset.meta)
        full_meta.update(self.meta)
        full_meta["topo_order"] = self.topo_order
        full_meta["cycles_detected"] = len(self.cycles)
        return self.dataset.to_mapping(self.tasks, full_meta)


class TaskReflector:
    """태스크 리플렉션 엔진 | Task reflection engine."""

    def __init__(self) -> None:
        self.type_complexity: Mapping[str, float] = {
            "doc": 0.8,
            "cli": 0.9,
            "config": 0.9,
            "code": 1.0,
            "ide": 1.0,
            "mcp": 1.2,
            "test": 1.1,
        }
        self.title_bonus: Mapping[str, float] = {
            "complex": 0.3,
            "advanced": 0.2,
            "integration": 0.2,
            "optimization": 0.2,
            "validation": 0.1,
            "analysis": 0.1,
            "reflection": 0.1,
            "management": 0.1,
        }

    def detect_cycles(self, tasks: Sequence[TaskSpec]) -> List[List[str]]:
        """순환 의존성 탐지 | Detect cyclic dependencies."""

        graph: Dict[str, Tuple[str, ...]] = {
            task.task_id: task.dependencies for task in tasks
        }
        cycles: List[List[str]] = []
        visited: set[str] = set()
        recursion_stack: set[str] = set()
        path: List[str] = []

        def depth_first(node: str) -> None:
            if node in recursion_stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return

            visited.add(node)
            recursion_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, ()):  # type: ignore[arg-type]
                depth_first(neighbor)

            recursion_stack.remove(node)
            path.pop()

        for task_id in graph:
            if task_id not in visited:
                depth_first(task_id)

        return cycles

    def topological_sort(self, tasks: Sequence[TaskSpec]) -> Tuple[List[str], List[str]]:
        """토폴로지 정렬 수행 | Execute topological sort."""

        in_degree: Dict[str, int] = {}
        dependents: Dict[str, List[str]] = {}

        for task in tasks:
            in_degree[task.task_id] = len(task.dependencies)
            for dependency in task.dependencies:
                dependents.setdefault(dependency, []).append(task.task_id)

        queue: List[str] = [task_id for task_id, degree in in_degree.items() if degree == 0]
        result: List[str] = []

        while queue:
            current = queue.pop(0)
            result.append(current)
            for dependent in dependents.get(current, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        remaining = [task_id for task_id in in_degree if task_id not in result]
        return result, remaining

    def calculate_complexity(
        self, task: TaskSpec, tasks: Mapping[str, TaskSpec]
    ) -> float:
        """복잡도 계산 | Calculate task complexity."""

        base_complexity = self.type_complexity.get(task.task_type, 1.0)
        dependency_complexity = 0.2 * len(task.dependencies)
        dependents = sum(1 for candidate in tasks.values() if task.task_id in candidate.dependencies)
        dependents_complexity = 0.1 * dependents
        title_lower = task.title.lower()
        bonus = sum(
            value for keyword, value in self.title_bonus.items() if keyword in title_lower
        )
        total = base_complexity + dependency_complexity + dependents_complexity + bonus
        return max(0.8, min(3.0, total))

    def reflect_dataset(self, dataset: TaskDataset) -> ReflectionResult:
        """데이터 세트 리플렉션 | Reflect dataset."""

        cycles = self.detect_cycles(dataset.tasks)
        topo_order, remaining = self.topological_sort(dataset.tasks)

        if remaining:
            cycles.extend([[task_id] for task_id in remaining])

        task_lookup: Dict[str, TaskSpec] = {task.task_id: task for task in dataset.tasks}
        reflected_tasks: List[ReflectedTask] = []

        for order, task_id in enumerate(topo_order):
            task = task_lookup[task_id]
            complexity = self.calculate_complexity(task, task_lookup)
            reflected_tasks.append(
                ReflectedTask(
                    task_id=task.task_id,
                    title=task.title,
                    task_type=task.task_type,
                    dependencies=task.dependencies,
                    module=task.module,
                    extra=task.extra,
                    order=order,
                    complexity=round(complexity, 2),
                )
            )

        meta = {
            "reflected_at": datetime.utcnow().strftime(DEFAULT_DATETIME_FORMAT),
            "topo_order": topo_order,
            "cycles_detected": len(cycles),
        }

        return ReflectionResult(
            dataset=dataset,
            tasks=reflected_tasks,
            topo_order=topo_order,
            cycles=cycles,
            meta=meta,
        )

    def reflect_mapping(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """매핑 리플렉션 | Reflect mapping payload."""

        dataset = TaskDataset.from_mapping(payload)
        return self.reflect_dataset(dataset).to_mapping()

    def generate_report(self, result: ReflectionResult, report_path: str) -> None:
        """리포트 생성 | Generate reflection report."""

        tasks = result.tasks
        total_tasks = len(tasks)
        average_complexity = (
            sum(task.complexity for task in tasks) / total_tasks if total_tasks else 0.0
        )
        max_complexity = max((task.complexity for task in tasks), default=0.0)
        min_complexity = min((task.complexity for task in tasks), default=0.0)

        type_stats: Dict[str, List[float]] = {}
        module_stats: Dict[str, List[float]] = {}

        for task in tasks:
            type_stats.setdefault(task.task_type, []).append(task.complexity)
            module_stats.setdefault(task.module, []).append(task.complexity)

        reflected_at = result.meta.get("reflected_at", "N/A")
        source = result.dataset.meta.get("source", "N/A")

        lines = ["# 태스크 리플렉션 리포트", "", "## 📊 **리플렉션 요약**"]
        lines.append(f"- **생성일**: {reflected_at}")
        lines.append(f"- **원본 파일**: {source}")
        lines.append(f"- **태스크 수**: {total_tasks}개")
        lines.append(f"- **순환 의존성**: {len(result.cycles)}개 발견")
        lines.append("")

        lines.append("## 📈 **복잡도 통계**")
        lines.append(f"- **평균 복잡도**: {average_complexity:.2f}")
        lines.append(f"- **최대 복잡도**: {max_complexity:.2f}")
        lines.append(f"- **최소 복잡도**: {min_complexity:.2f}")
        lines.append("")

        lines.append("## 🔗 **실행 순서 (토폴로지 정렬)**")
        for order, task in enumerate(tasks, start=1):
            lines.append(f"{order}. **{task.task_id}** (복잡도: {task.complexity:.2f})")
            lines.append(f"   - 제목: {task.title or 'N/A'}")
            lines.append(f"   - 타입: {task.task_type}")
            lines.append(f"   - 모듈: {task.module}")
            lines.append(f"   - 의존성: {len(task.dependencies)}개")
            lines.append("")

        lines.append("## 📋 **타입별 복잡도 분석**")
        lines.append("")
        for task_type, complexities in type_stats.items():
            average = sum(complexities) / len(complexities)
            lines.append(
                f"- **{task_type}**: 평균 {average:.2f} (n={len(complexities)})"
            )

        lines.append("")
        lines.append("## 🏗️ **모듈별 복잡도 분석**")
        lines.append("")
        for module, complexities in module_stats.items():
            average = sum(complexities) / len(complexities)
            lines.append(
                f"- **{module}**: 평균 {average:.2f} (n={len(complexities)})"
            )

        lines.append("")
        lines.append("## 🎯 **복잡도 순위 (높은 순)**")
        lines.append("")
        sorted_tasks = sorted(tasks, key=lambda item: item.complexity, reverse=True)
        for index, task in enumerate(sorted_tasks[:5], start=1):
            lines.append(f"{index}. **{task.task_id}**: {task.complexity:.2f}")

        lines.append("")
        lines.append(f"---\n*리플렉션 완료: {datetime.utcnow().strftime(DEFAULT_DATETIME_FORMAT)}*")

        with open(report_path, "w", encoding="utf-8") as file:
            file.write("\n".join(lines))


def load_dataset(filepath: str) -> TaskDataset:
    """파일에서 데이터 세트 로드 | Load dataset from file."""

    import json
    import pathlib

    path = pathlib.Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {filepath}")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    dataset = TaskDataset.from_mapping(payload)
    dataset.meta.setdefault("source", str(filepath))
    return dataset


__all__ = [
    "TaskDataset",
    "TaskReflector",
    "TaskSpec",
    "ReflectedTask",
    "ReflectionResult",
    "load_dataset",
]

