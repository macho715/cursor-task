#!/usr/bin/env python3
"""
병렬 처리 실행 엔진
의존성 그래프 분석을 통한 최적화된 병렬 실행

사용법:
    python tools/parallel_executor.py --input tasks.reflected.json --max-workers 4
    python tools/parallel_executor.py --input tasks.reflected.json --strategy smart --visualize
"""

import json
import argparse
import subprocess
import sys
import time
import logging
import threading
import queue
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, field
from enum import Enum
import concurrent.futures
import networkx as nx
from collections import defaultdict, deque

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parallel_execution.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ParallelStrategy(Enum):
    """병렬 처리 전략"""
    CONSERVATIVE = "conservative"  # 안전한 병렬 처리
    AGGRESSIVE = "aggressive"      # 공격적인 병렬 처리
    SMART = "smart"               # 지능적 병렬 처리
    DEPENDENCY = "dependency"      # 의존성 기반 병렬 처리

@dataclass
class Task:
    """태스크 정보"""
    id: str
    title: str
    module: str
    type: str
    deps: List[str]
    complexity: float
    acceptance: List[str]
    order: int
    
    # 병렬 처리 관련 필드
    _can_parallel: bool = True
    estimated_duration: float = 0.0
    priority_score: float = 0.0
    resource_requirements: Dict[str, int] = field(default_factory=dict)
    
    @property
    def can_parallel(self) -> bool:
        """병렬 처리 가능성"""
        parallel_types = ['config', 'cli', 'doc', 'test']
        sequential_types = ['code', 'ide', 'mcp']
        
        if self.type in parallel_types:
            return True
        elif self.type in sequential_types:
            return False
        else:
            return False
    
    @property
    def is_ready(self) -> bool:
        """의존성이 모두 완료되었는지 확인"""
        return len(self.deps) == 0 or all(dep in ParallelExecutor.completed_tasks for dep in self.deps)
    
    @property
    def parallel_compatibility(self) -> str:
        """병렬 호환성 레벨"""
        if self.can_parallel:
            if self.type in ['config', 'cli', 'doc']:
                return "high"
            elif self.type in ['test']:
                return "medium"
            else:
                return "medium"
        else:
            return "low"

@dataclass
class ExecutionResult:
    """실행 결과"""
    task_id: str
    success: bool
    duration: float
    output: str
    error: Optional[str] = None
    timestamp: str = ""
    worker_id: Optional[int] = None
    parallel_group: Optional[str] = None

@dataclass
class ParallelGroup:
    """병렬 실행 그룹"""
    id: str
    tasks: List[Task]
    estimated_duration: float
    resource_usage: Dict[str, int]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ParallelExecutor:
    """병렬 실행기"""
    
    completed_tasks = set()
    failed_tasks = set()
    
    def __init__(self, strategy: ParallelStrategy = ParallelStrategy.SMART, max_workers: int = 4):
        self.strategy = strategy
        self.max_workers = max_workers
        self.results: List[ExecutionResult] = []
        self.parallel_groups: List[ParallelGroup] = []
        self.dependency_graph = nx.DiGraph()
        self.resource_pool = defaultdict(int)
        self.worker_pool = queue.Queue()
        
        # 워커 풀 초기화
        for i in range(max_workers):
            self.worker_pool.put(i)
    
    def load_tasks(self, input_file: str) -> List[Task]:
        """태스크 파일 로드 및 분석"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            tasks = []
            for task_data in data.get('tasks', []):
                task = Task(
                    id=task_data['id'],
                    title=task_data['title'],
                    module=task_data['module'],
                    type=task_data['type'],
                    deps=task_data.get('deps', []),
                    complexity=task_data.get('complexity', 1.0),
                    acceptance=task_data.get('acceptance', []),
                    order=task_data.get('order', 0)
                )
                
                # 병렬 처리 관련 속성 설정
                task.estimated_duration = self._estimate_duration(task)
                task.priority_score = self._calculate_priority(task)
                task.resource_requirements = self._get_resource_requirements(task)
                
                tasks.append(task)
            
            logger.info(f"태스크 {len(tasks)}개 로드 완료")
            return tasks
            
        except Exception as e:
            logger.error(f"태스크 로드 실패: {e}")
            raise
    
    
    def _estimate_duration(self, task: Task) -> float:
        """태스크 실행 시간 추정"""
        # 복잡도 기반 시간 추정 (초)
        base_time = 2.0
        complexity_factor = task.complexity
        type_factor = {
            'code': 1.5,
            'config': 0.8,
            'cli': 1.0,
            'mcp': 2.0,
            'ide': 1.2,
            'test': 1.0,
            'doc': 0.5
        }.get(task.type, 1.0)
        
        return base_time * complexity_factor * type_factor
    
    def _calculate_priority(self, task: Task) -> float:
        """태스크 우선순위 점수 계산"""
        # 복잡도가 높을수록, 의존성이 적을수록 높은 우선순위
        complexity_score = task.complexity * 0.4
        dependency_score = (10 - len(task.deps)) * 0.3
        type_score = {
            'code': 0.3,
            'config': 0.2,
            'cli': 0.25,
            'mcp': 0.35,
            'ide': 0.3,
            'test': 0.2,
            'doc': 0.1
        }.get(task.type, 0.2)
        
        return complexity_score + dependency_score + type_score
    
    def _get_resource_requirements(self, task: Task) -> Dict[str, int]:
        """태스크 리소스 요구사항"""
        return {
            'cpu': 1 if task.type in ['code', 'mcp'] else 0.5,
            'memory': 512 if task.type in ['code', 'mcp'] else 256,
            'disk': 100 if task.type in ['doc', 'test'] else 50
        }
    
    def build_dependency_graph(self, tasks: List[Task]) -> nx.DiGraph:
        """의존성 그래프 구축"""
        graph = nx.DiGraph()
        
        # 노드 추가
        for task in tasks:
            graph.add_node(task.id, task=task)
        
        # 엣지 추가 (의존성)
        for task in tasks:
            for dep in task.deps:
                graph.add_edge(dep, task.id)
        
        self.dependency_graph = graph
        logger.info(f"의존성 그래프 구축 완료: {graph.number_of_nodes()}개 노드, {graph.number_of_edges()}개 엣지")
        
        return graph
    
    def identify_parallel_groups(self, tasks: List[Task]) -> List[ParallelGroup]:
        """병렬 실행 그룹 식별"""
        groups = []
        visited = set()
        
        # 의존성 레벨별로 그룹화
        levels = self._get_dependency_levels(tasks)
        
        for level, level_tasks in levels.items():
            if len(level_tasks) > 1:
                # 같은 레벨의 태스크들을 병렬 그룹으로 구성
                parallel_tasks = [t for t in level_tasks if t.can_parallel]
                sequential_tasks = [t for t in level_tasks if not t.can_parallel]
                
                if parallel_tasks:
                    group = ParallelGroup(
                        id=f"level_{level}_parallel",
                        tasks=parallel_tasks,
                        estimated_duration=max(t.estimated_duration for t in parallel_tasks),
                        resource_usage=self._calculate_group_resources(parallel_tasks)
                    )
                    groups.append(group)
                
                # 순차 실행 태스크들도 개별 그룹으로 추가
                for task in sequential_tasks:
                    group = ParallelGroup(
                        id=f"sequential_{task.id}",
                        tasks=[task],
                        estimated_duration=task.estimated_duration,
                        resource_usage=task.resource_requirements
                    )
                    groups.append(group)
            else:
                # 단일 태스크 그룹
                task = level_tasks[0]
                group = ParallelGroup(
                    id=f"single_{task.id}",
                    tasks=[task],
                    estimated_duration=task.estimated_duration,
                    resource_usage=task.resource_requirements
                )
                groups.append(group)
        
        self.parallel_groups = groups
        logger.info(f"병렬 그룹 {len(groups)}개 식별 완료")
        
        return groups
    
    def _get_dependency_levels(self, tasks: List[Task]) -> Dict[int, List[Task]]:
        """의존성 레벨별 태스크 분류"""
        levels = defaultdict(list)
        task_dict = {task.id: task for task in tasks}
        
        # 의존성 깊이별로 레벨 계산
        def get_dependency_depth(task_id: str, visited: set = None) -> int:
            if visited is None:
                visited = set()
            
            if task_id in visited:
                return 0  # 순환 의존성 방지
            
            visited.add(task_id)
            task = task_dict[task_id]
            
            if not task.deps:
                return 0
            
            max_depth = max(get_dependency_depth(dep, visited.copy()) for dep in task.deps)
            return max_depth + 1
        
        # 각 태스크의 의존성 깊이 계산
        for task in tasks:
            depth = get_dependency_depth(task.id)
            levels[depth].append(task)
        
        return dict(levels)
    
    def _calculate_group_resources(self, tasks: List[Task]) -> Dict[str, int]:
        """그룹 리소스 사용량 계산"""
        total_resources = defaultdict(int)
        for task in tasks:
            for resource, amount in task.resource_requirements.items():
                total_resources[resource] += amount
        return dict(total_resources)
    
    def execute_parallel_groups(self, groups: List[ParallelGroup]) -> List[ExecutionResult]:
        """병렬 그룹 실행"""
        logger.info(f"병렬 그룹 실행 시작 (최대 {self.max_workers}개 워커)")
        
        all_results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 그룹별로 실행
            for group in groups:
                group.start_time = datetime.now()
                logger.info(f"그룹 {group.id} 실행 시작 ({len(group.tasks)}개 태스크)")
                
                # 그룹 내 태스크들을 병렬로 실행
                if len(group.tasks) == 1:
                    # 단일 태스크
                    task = group.tasks[0]
                    result = self.execute_task(task, worker_id=0)
                    all_results.append(result)
                else:
                    # 다중 태스크 병렬 실행
                    future_to_task = {}
                    for i, task in enumerate(group.tasks):
                        if task.is_ready:
                            future = executor.submit(self.execute_task, task, worker_id=i % self.max_workers)
                            future_to_task[future] = task
                    
                    # 결과 수집
                    for future in concurrent.futures.as_completed(future_to_task):
                        task = future_to_task[future]
                        try:
                            result = future.result()
                            all_results.append(result)
                            
                            if not result.success:
                                logger.error(f"태스크 {task.id} 실패로 인한 그룹 실행 중단")
                                break
                        
                        except Exception as e:
                            logger.error(f"태스크 {task.id} 실행 중 예외: {e}")
                            result = ExecutionResult(
                                task_id=task.id,
                                success=False,
                                duration=0.0,
                                output="",
                                error=str(e),
                                timestamp=datetime.now().isoformat()
                            )
                            all_results.append(result)
                
                group.end_time = datetime.now()
                group_duration = (group.end_time - group.start_time).total_seconds()
                logger.info(f"그룹 {group.id} 완료 ({group_duration:.2f}초)")
        
        self.results = all_results
        return all_results
    
    def execute_task(self, task: Task, worker_id: int = 0) -> ExecutionResult:
        """단일 태스크 실행"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        logger.info(f"[워커 {worker_id}] 태스크 실행 시작: {task.id} ({task.title})")
        
        try:
            # 태스크 타입에 따른 명령어 생성
            command = self._generate_command(task)
            
            # 명령어 실행
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5분 타임아웃
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"[워커 {worker_id}] 태스크 성공: {task.id} ({duration:.2f}초)")
                self.completed_tasks.add(task.id)
                
                return ExecutionResult(
                    task_id=task.id,
                    success=True,
                    duration=duration,
                    output=result.stdout,
                    timestamp=timestamp,
                    worker_id=worker_id
                )
            else:
                logger.error(f"[워커 {worker_id}] 태스크 실패: {task.id} - {result.stderr}")
                self.failed_tasks.add(task.id)
                
                return ExecutionResult(
                    task_id=task.id,
                    success=False,
                    duration=duration,
                    output=result.stdout,
                    error=result.stderr,
                    timestamp=timestamp,
                    worker_id=worker_id
                )
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"[워커 {worker_id}] 태스크 타임아웃: {task.id}")
            self.failed_tasks.add(task.id)
            
            return ExecutionResult(
                task_id=task.id,
                success=False,
                duration=duration,
                output="",
                error="Task execution timeout (5 minutes)",
                timestamp=timestamp,
                worker_id=worker_id
            )
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[워커 {worker_id}] 태스크 실행 중 오류: {task.id} - {e}")
            self.failed_tasks.add(task.id)
            
            return ExecutionResult(
                task_id=task.id,
                success=False,
                duration=duration,
                output="",
                error=str(e),
                timestamp=timestamp,
                worker_id=worker_id
            )
    
    def _generate_command(self, task: Task) -> str:
        """태스크 타입에 따른 명령어 생성"""
        if task.type == "code":
            return f'cursor agent --apply=ask --rules "{task.title}"'
        
        elif task.type == "config":
            return f'cursor agent --apply=ask --rules "{task.title}"'
        
        elif task.type == "cli":
            return f'cursor agent --apply=ask --rules "{task.title}"'
        
        elif task.type == "mcp":
            return f'python tools/tasks_reflect.py --in tasks.json --out tasks.reflected.json --report reports/tasks_reflect_report.md'
        
        elif task.type == "ide":
            return f'cursor agent --apply=ask --rules "{task.title}"'
        
        else:
            return f'echo "Unknown task type: {task.type}"'
    
    def generate_parallel_report(self, results: List[ExecutionResult]) -> str:
        """병렬 실행 결과 리포트 생성"""
        total_tasks = len(results)
        successful_tasks = len([r for r in results if r.success])
        failed_tasks = total_tasks - successful_tasks
        
        total_duration = sum(r.duration for r in results)
        max_duration = max(r.duration for r in results) if results else 0
        min_duration = min(r.duration for r in results) if results else 0
        avg_duration = total_duration / total_tasks if total_tasks > 0 else 0
        
        # 워커별 통계
        worker_stats = defaultdict(lambda: {'count': 0, 'duration': 0.0, 'success': 0})
        for result in results:
            worker_id = result.worker_id or 0
            worker_stats[worker_id]['count'] += 1
            worker_stats[worker_id]['duration'] += result.duration
            if result.success:
                worker_stats[worker_id]['success'] += 1
        
        # 병렬 그룹별 통계
        group_stats = []
        for group in self.parallel_groups:
            if group.start_time and group.end_time:
                group_duration = (group.end_time - group.start_time).total_seconds()
                group_stats.append({
                    'id': group.id,
                    'tasks': len(group.tasks),
                    'duration': group_duration,
                    'parallel_efficiency': group.estimated_duration / group_duration if group_duration > 0 else 0
                })
        
        report = f"""
# 병렬 처리 실행 결과 리포트

## 📊 **실행 요약**
- **실행 전략**: {self.strategy.value}
- **최대 워커 수**: {self.max_workers}
- **총 태스크 수**: {total_tasks}
- **성공한 태스크**: {successful_tasks}
- **실패한 태스크**: {failed_tasks}
- **성공률**: {(successful_tasks/total_tasks*100):.1f}%
- **총 실행 시간**: {total_duration:.2f}초
- **최대 실행 시간**: {max_duration:.2f}초
- **최소 실행 시간**: {min_duration:.2f}초
- **평균 실행 시간**: {avg_duration:.2f}초

## 🔧 **워커별 성능**
"""
        
        for worker_id, stats in worker_stats.items():
            success_rate = (stats['success'] / stats['count'] * 100) if stats['count'] > 0 else 0
            avg_worker_duration = stats['duration'] / stats['count'] if stats['count'] > 0 else 0
            report += f"""
### 워커 {worker_id}
- **처리한 태스크**: {stats['count']}개
- **총 실행 시간**: {stats['duration']:.2f}초
- **평균 실행 시간**: {avg_worker_duration:.2f}초
- **성공률**: {success_rate:.1f}%
"""
        
        report += f"""
## 🚀 **병렬 그룹별 성능**
"""
        
        for group_stat in group_stats:
            efficiency = group_stat['parallel_efficiency']
            report += f"""
### {group_stat['id']}
- **태스크 수**: {group_stat['tasks']}개
- **실행 시간**: {group_stat['duration']:.2f}초
- **병렬 효율성**: {efficiency:.2f}x
"""
        
        report += f"""
## 📋 **태스크별 결과**
"""
        
        for result in results:
            status = "✅ 성공" if result.success else "❌ 실패"
            worker_info = f" (워커 {result.worker_id})" if result.worker_id is not None else ""
            report += f"""
### {result.task_id}{worker_info}
- **상태**: {status}
- **실행 시간**: {result.duration:.2f}초
- **타임스탬프**: {result.timestamp}
"""
            
            if result.error:
                report += f"- **오류**: {result.error}\n"
        
        if failed_tasks > 0:
            report += f"""
## ⚠️ **실패한 태스크 분석**
"""
            for result in results:
                if not result.success:
                    report += f"- **{result.task_id}**: {result.error}\n"
        
        # 병렬 처리 효율성 분석
        sequential_time = sum(t.estimated_duration for t in self._get_all_tasks())
        parallel_time = max(group_stat['duration'] for group_stat in group_stats) if group_stats else 0
        speedup = sequential_time / parallel_time if parallel_time > 0 else 0
        
        report += f"""
## 🎯 **병렬 처리 효율성**
- **순차 실행 예상 시간**: {sequential_time:.2f}초
- **병렬 실행 실제 시간**: {parallel_time:.2f}초
- **속도 향상**: {speedup:.2f}x
- **효율성**: {(speedup/self.max_workers*100):.1f}%

## 💡 **개선 제안**
"""
        
        if speedup < self.max_workers * 0.7:
            report += "- 워커 수를 조정하거나 태스크 분할을 재검토하세요\n"
        
        if failed_tasks > 0:
            report += "- 실패한 태스크의 의존성 및 설정을 재검토하세요\n"
        
        if any(stat['success'] / stat['count'] < 0.8 for stat in worker_stats.values()):
            report += "- 워커별 성공률을 개선하기 위해 리소스 할당을 최적화하세요\n"
        
        return report
    
    def _get_all_tasks(self) -> List[Task]:
        """모든 태스크 가져오기"""
        tasks = []
        for group in self.parallel_groups:
            tasks.extend(group.tasks)
        return tasks
    
    def visualize_dependency_graph(self, output_file: str = "dependency_graph.png"):
        """의존성 그래프 시각화"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
            
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(self.dependency_graph, k=3, iterations=50)
            
            # 노드 색상 설정 (태스크 타입별)
            node_colors = []
            color_map = {
                'code': 'red',
                'config': 'blue',
                'cli': 'green',
                'mcp': 'orange',
                'ide': 'purple',
                'test': 'brown',
                'doc': 'pink'
            }
            
            for node in self.dependency_graph.nodes():
                task = self.dependency_graph.nodes[node]['task']
                node_colors.append(color_map.get(task.type, 'gray'))
            
            # 그래프 그리기
            nx.draw(self.dependency_graph, pos, 
                   node_color=node_colors,
                   node_size=1000,
                   font_size=8,
                   font_weight='bold',
                   with_labels=True,
                   arrows=True,
                   arrowsize=20,
                   edge_color='gray')
            
            # 범례 추가
            legend_elements = [mpatches.Patch(color=color, label=task_type) 
                             for task_type, color in color_map.items()]
            plt.legend(handles=legend_elements, loc='upper right')
            
            plt.title("Task Dependency Graph", fontsize=16, fontweight='bold')
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"의존성 그래프 시각화 완료: {output_file}")
            
        except ImportError:
            logger.warning("matplotlib가 설치되지 않아 그래프 시각화를 건너뜁니다.")
        except Exception as e:
            logger.error(f"그래프 시각화 중 오류 발생: {e}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='병렬 처리 태스크 실행')
    parser.add_argument('--input', '-i', required=True, help='입력 태스크 파일')
    parser.add_argument('--strategy', '-s', choices=['conservative', 'aggressive', 'smart', 'dependency'], 
                       default='smart', help='병렬 처리 전략')
    parser.add_argument('--max-workers', '-w', type=int, default=4, help='최대 워커 수')
    parser.add_argument('--output', '-o', help='결과 리포트 출력 파일')
    parser.add_argument('--visualize', '-v', action='store_true', help='의존성 그래프 시각화')
    
    args = parser.parse_args()
    
    try:
        # 실행기 초기화
        strategy = ParallelStrategy(args.strategy)
        executor = ParallelExecutor(strategy, args.max_workers)
        
        # 태스크 로드
        tasks = executor.load_tasks(args.input)
        
        # 의존성 그래프 구축
        executor.build_dependency_graph(tasks)
        
        # 시각화 (옵션)
        if args.visualize:
            executor.visualize_dependency_graph()
        
        # 병렬 그룹 식별
        groups = executor.identify_parallel_groups(tasks)
        
        # 병렬 실행
        results = executor.execute_parallel_groups(groups)
        
        # 리포트 생성
        report = executor.generate_parallel_report(results)
        
        # 리포트 출력
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"리포트 저장: {args.output}")
        else:
            print(report)
        
        # 성공/실패 종료 코드
        failed_count = len([r for r in results if not r.success])
        sys.exit(failed_count)
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
