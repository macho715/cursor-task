"""리플렉션 핵심 로직 모듈. Reflection core logic module."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence

from .config import ReflectionConfig
from .exceptions import ReflectionError, TaskValidationError

TaskMapping = Mapping[str, Any]
TaskSequence = Sequence[TaskMapping]
CyclePaths = List[List[str]]


@dataclass(slots=True)
class ReflectionResult:
    """리플렉션 실행 결과 모델. Reflection execution result model."""

    tasks: List[Dict[str, Any]]
    meta: Dict[str, Any]
    cycles: List[List[str]]
    topo_order: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """JSON 직렬화용 딕셔너리. Dictionary representation for JSON."""

        return {"tasks": self.tasks, "meta": self.meta}


class TaskReflector:
    """태스크 리플렉션 엔진. Task reflection engine."""

    def __init__(self, config: ReflectionConfig | None = None):
        self.config = config or ReflectionConfig()

    def load_tasks(self, path: Path | str) -> Dict[str, Any]:
        """JSON 태스크 파일 로드. Load JSON task file."""

        try:
            import json

            with Path(path).open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError as exc:  # pragma: no cover - 직접 확인 용이
            message = f"입력 파일을 찾을 수 없습니다: {path}"
            raise ReflectionError(message) from exc
        except OSError as exc:  # pragma: no cover - 환경 문제 보고
            message = f"입력 파일을 읽을 수 없습니다: {exc}"
            raise ReflectionError(message) from exc
        except ValueError as exc:
            message = f"유효한 JSON 형식이 아닙니다: {exc}"
            raise TaskValidationError(message) from exc
        if not isinstance(data, MutableMapping):
            raise TaskValidationError(
                "최상위 데이터는 객체여야 합니다. Root data must be object."
            )
        return dict(data)

    def detect_cycles(self, tasks: TaskSequence) -> CyclePaths:
        """순환 의존성 탐지. Detect cyclic dependencies."""

        graph: Dict[str, List[str]] = {}
        for task in tasks:
            task_id = str(task.get("id"))
            if not task_id:
                raise TaskValidationError(
                    "모든 태스크는 ID가 필요합니다. Every task requires id."
                )
            graph[task_id] = [str(dep) for dep in task.get("deps", [])]

        cycles: List[List[str]] = []
        visited: set[str] = set()
        stack: set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> None:
            if node in stack:
                idx = path.index(node)
                cycles.append(path[idx:] + [node])
                return
            if node in visited:
                return
            visited.add(node)
            stack.add(node)
            path.append(node)
            for neighbor in graph.get(node, []):
                dfs(neighbor)
            stack.remove(node)
            path.pop()

        for task_id in graph:
            if task_id not in visited:
                dfs(task_id)
        return cycles

    def topological_sort(self, tasks: TaskSequence) -> List[str]:
        """토폴로지 정렬 수행. Perform topological sort."""

        in_degree: Dict[str, int] = {}
        graph: Dict[str, List[str]] = {}
        for task in tasks:
            task_id = str(task.get("id"))
            if not task_id:
                raise TaskValidationError(
                    "모든 태스크는 ID가 필요합니다. Every task requires id."
                )
            deps = [str(dep) for dep in task.get("deps", [])]
            graph[task_id] = deps
            in_degree[task_id] = len(deps)
        zero_degree: List[str] = []
        for task_id, degree in in_degree.items():
            if degree == 0:
                zero_degree.append(task_id)
        queue = deque(zero_degree)
        order: List[str] = []
        while queue:
            current = queue.popleft()
            order.append(current)
            for task_id, deps in graph.items():
                if current in deps:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)
        return order

    def calculate_complexity(
        self,
        task: TaskMapping,
        all_tasks: TaskSequence,
    ) -> float:
        """복잡도 점수 계산. Calculate complexity score."""

        task_type = str(task.get("type", "code"))
        base_complexity = self.config.type_complexity.get(task_type, 1.0)
        deps = task.get("deps", [])
        deps_count = len(deps) if isinstance(deps, Sequence) else 0
        dependents = 0
        for candidate in all_tasks:
            deps = candidate.get("deps", [])
            if task.get("id") in deps:
                dependents += 1
        title = str(task.get("title", "")).lower()
        bonus = 0.0
        for keyword, weight in self.config.title_bonus.items():
            if keyword in title:
                bonus += weight
        components = (
            base_complexity,
            0.2 * deps_count,
            0.1 * dependents,
            bonus,
        )
        total = sum(components)
        bounded = max(self.config.clamp_min, min(self.config.clamp_max, total))
        return round(bounded, 2)

    def reflect(self, tasks_data: TaskMapping) -> ReflectionResult:
        """태스크 데이터를 리플렉션. Reflect task data structure."""

        tasks = tasks_data.get("tasks")
        if not isinstance(tasks, Sequence):
            raise TaskValidationError(
                "'tasks' 키는 리스트여야 합니다. 'tasks' must be list."
            )
        normalized_tasks = [dict(task) for task in tasks]
        cycles = self.detect_cycles(normalized_tasks)
        topo_order = self.topological_sort(normalized_tasks)
        all_ids = [str(task.get("id")) for task in normalized_tasks]
        missing_ids: List[str] = []
        for task_id in all_ids:
            if task_id not in topo_order:
                missing_ids.append(task_id)
        ordered_ids = topo_order + missing_ids
        reflected_tasks: List[Dict[str, Any]] = []
        for index, task_id in enumerate(ordered_ids):
            task = None
            for candidate in normalized_tasks:
                if candidate.get("id") == task_id:
                    task = candidate
                    break
            if task is None:
                continue
            complexity = self.calculate_complexity(task, normalized_tasks)
            reflected_task = dict(task)
            reflected_task["order"] = index
            reflected_task["complexity"] = complexity
            reflected_tasks.append(reflected_task)
        meta = dict(tasks_data.get("meta", {}))
        meta["reflected_at"] = datetime.now().isoformat()
        meta["topo_order"] = topo_order
        meta["cycles_detected"] = len(cycles)
        if missing_ids:
            meta["unordered_tasks"] = missing_ids
        return ReflectionResult(reflected_tasks, meta, cycles, topo_order)

    def build_report(
        self,
        original_data: Mapping[str, Any],
        reflection: ReflectionResult,
    ) -> str:
        """리플렉션 결과 리포트 생성. Generate reflection report text."""

        tasks = reflection.tasks
        total_tasks = len(tasks)
        complexities = [task["complexity"] for task in tasks]
        avg_complexity = 0.0
        if total_tasks:
            avg_complexity = sum(complexities) / total_tasks
        max_complexity = max(complexities, default=0)
        min_complexity = min(complexities, default=0)
        type_stats: Dict[str, List[float]] = defaultdict(list)
        module_stats: Dict[str, List[float]] = defaultdict(list)
        for task in tasks:
            task_type = str(task.get("type", "unknown"))
            module = str(task.get("module", "unknown"))
            type_stats[task_type].append(task["complexity"])
            module_stats[module].append(task["complexity"])
        source_meta = original_data.get("meta", {})
        source_value = source_meta.get("source", "N/A")
        report_lines = [
            "# 태스크 리플렉션 리포트",
            "",
            "## 📊 **리플렉션 요약**",
            f"- **생성일**: {reflection.meta.get('reflected_at', 'N/A')}",
            f"- **원본 파일**: {source_value}",
            f"- **태스크 수**: {total_tasks}개",
            f"- **순환 의존성**: {reflection.meta.get('cycles_detected', 0)}개 발견",
            "",
            "## 📈 **복잡도 통계**",
            f"- **평균 복잡도**: {avg_complexity:.2f}",
            f"- **최대 복잡도**: {max_complexity:.2f}",
            f"- **최소 복잡도**: {min_complexity:.2f}",
            "",
            "## 🔗 **실행 순서 (토폴로지 정렬)**",
        ]
        for index, task in enumerate(tasks):
            task_id = task.get("id")
            complexity_value = task["complexity"]
            deps_count = len(task.get("deps", []))
            headline = "{index}. **{task_id}** (복잡도: {complexity})".format(
                index=index + 1,
                task_id=task_id,
                complexity=complexity_value,
            )
            report_lines.extend(
                [
                    headline,
                    f"   - 제목: {task.get('title', 'N/A')}",
                    f"   - 타입: {task.get('type', 'N/A')}",
                    f"   - 모듈: {task.get('module', 'N/A')}",
                    f"   - 의존성: {deps_count}개",
                    "",
                ]
            )
        report_lines.append("## 📋 **타입별 복잡도 분석**\n")
        for task_type, complexities in type_stats.items():
            avg_value = sum(complexities) / len(complexities)
            sample_count = len(complexities)
            summary = "- **{name}**: 평균 {avg:.2f} (n={count})".format(
                name=task_type,
                avg=avg_value,
                count=sample_count,
            )
            report_lines.append(summary)
        report_lines.append("\n## 🏗️ **모듈별 복잡도 분석**\n")
        for module, complexities in module_stats.items():
            avg_value = sum(complexities) / len(complexities)
            sample_count = len(complexities)
            summary = "- **{name}**: 평균 {avg:.2f} (n={count})".format(
                name=module,
                avg=avg_value,
                count=sample_count,
            )
            report_lines.append(summary)
        report_lines.append("\n## 🎯 **복잡도 순위 (높은 순)**\n")
        top_tasks = sorted(
            tasks,
            key=lambda candidate: candidate["complexity"],
            reverse=True,
        )[:5]
        for index, task in enumerate(top_tasks):
            task_id = task.get("id")
            ranking_line = "{index}. **{task_id}**: {score}".format(
                index=index + 1,
                task_id=task_id,
                score=task["complexity"],
            )
            report_lines.append(ranking_line)
        completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer = f"---\n*리플렉션 완료: {completed_at}*"
        report_lines.extend(["", footer, ""])
        return "\n".join(report_lines)
