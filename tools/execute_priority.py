#!/usr/bin/env python3
"""
우선순위 기반 태스크 실행 시스템
복잡도 순위에 따른 단계별 Agent 실행

사용법:
    python tools/execute_priority.py --input tasks.reflected.json
    python tools/execute_priority.py --input tasks.reflected.json --strategy complexity
    python tools/execute_priority.py --input tasks.reflected.json --parallel --max-workers 2
"""

import json
import argparse
import subprocess
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import concurrent.futures
import threading

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('priority_execution.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ExecutionStrategy(Enum):
    """실행 전략"""
    DEPENDENCY = "dependency"  # 의존성 순서 (토폴로지 정렬)
    COMPLEXITY = "complexity"  # 복잡도 높은 순
    EFFICIENCY = "efficiency"  # 효율성 최적화 (병렬 가능한 것들 우선)

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
    
    @property
    def is_ready(self) -> bool:
        """의존성이 모두 완료되었는지 확인"""
        return len(self.deps) == 0 or all(dep in TaskExecutor.completed_tasks for dep in self.deps)
    
    @property
    def can_run_parallel(self) -> bool:
        """병렬 실행 가능한지 확인"""
        # config, cli 타입은 병렬 실행 가능
        return self.type in ['config', 'cli', 'doc']

@dataclass
class ExecutionResult:
    """실행 결과"""
    task_id: str
    success: bool
    duration: float
    output: str
    error: Optional[str] = None
    timestamp: str = ""

class TaskExecutor:
    """태스크 실행기"""
    
    completed_tasks = set()
    failed_tasks = set()
    
    def __init__(self, strategy: ExecutionStrategy = ExecutionStrategy.DEPENDENCY):
        self.strategy = strategy
        self.results: List[ExecutionResult] = []
        self.start_time = None
        self.end_time = None
    
    def load_tasks(self, input_file: str) -> List[Task]:
        """태스크 파일 로드"""
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
                tasks.append(task)
            
            logger.info(f"태스크 {len(tasks)}개 로드 완료")
            return tasks
            
        except Exception as e:
            logger.error(f"태스크 로드 실패: {e}")
            raise
    
    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """전략에 따른 태스크 정렬"""
        if self.strategy == ExecutionStrategy.DEPENDENCY:
            # 토폴로지 정렬 순서 유지
            return sorted(tasks, key=lambda t: t.order)
        
        elif self.strategy == ExecutionStrategy.COMPLEXITY:
            # 복잡도 높은 순 (의존성 고려)
            return sorted(tasks, key=lambda t: (-t.complexity, t.order))
        
        elif self.strategy == ExecutionStrategy.EFFICIENCY:
            # 병렬 가능한 것들 우선, 복잡도 고려
            return sorted(tasks, key=lambda t: (not t.can_run_parallel, -t.complexity, t.order))
        
        return tasks
    
    def execute_task(self, task: Task) -> ExecutionResult:
        """단일 태스크 실행"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        logger.info(f"태스크 실행 시작: {task.id} ({task.title})")
        
        try:
            # 태스크 타입에 따른 실행 명령어 생성
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
                logger.info(f"태스크 성공: {task.id} ({duration:.2f}초)")
                self.completed_tasks.add(task.id)
                
                return ExecutionResult(
                    task_id=task.id,
                    success=True,
                    duration=duration,
                    output=result.stdout,
                    timestamp=timestamp
                )
            else:
                logger.error(f"태스크 실패: {task.id} - {result.stderr}")
                self.failed_tasks.add(task.id)
                
                return ExecutionResult(
                    task_id=task.id,
                    success=False,
                    duration=duration,
                    output=result.stdout,
                    error=result.stderr,
                    timestamp=timestamp
                )
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"태스크 타임아웃: {task.id}")
            self.failed_tasks.add(task.id)
            
            return ExecutionResult(
                task_id=task.id,
                success=False,
                duration=duration,
                output="",
                error="Task execution timeout (5 minutes)",
                timestamp=timestamp
            )
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"태스크 실행 중 오류: {task.id} - {e}")
            self.failed_tasks.add(task.id)
            
            return ExecutionResult(
                task_id=task.id,
                success=False,
                duration=duration,
                output="",
                error=str(e),
                timestamp=timestamp
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
            return f'python tools/tasks_reflect.py --in tasks.json --out tasks.reflected.json'
        
        elif task.type == "ide":
            return f'cursor agent --apply=ask --rules "{task.title}"'
        
        else:
            return f'echo "Unknown task type: {task.type}"'
    
    def execute_sequential(self, tasks: List[Task]) -> List[ExecutionResult]:
        """순차 실행"""
        logger.info("순차 실행 모드 시작")
        
        sorted_tasks = self.sort_tasks(tasks)
        results = []
        
        for task in sorted_tasks:
            if not task.is_ready:
                logger.warning(f"태스크 {task.id}의 의존성이 미완료되어 건너뜀")
                continue
            
            result = self.execute_task(task)
            results.append(result)
            
            if not result.success:
                logger.error(f"태스크 {task.id} 실패로 인한 실행 중단")
                break
        
        return results
    
    def execute_parallel(self, tasks: List[Task], max_workers: int = 2) -> List[ExecutionResult]:
        """병렬 실행"""
        logger.info(f"병렬 실행 모드 시작 (최대 {max_workers}개 워커)")
        
        sorted_tasks = self.sort_tasks(tasks)
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 실행 가능한 태스크들을 워커에 제출
            future_to_task = {}
            
            while sorted_tasks or future_to_task:
                # 실행 준비된 태스크들을 찾아서 제출
                ready_tasks = [t for t in sorted_tasks if t.is_ready and len(future_to_task) < max_workers]
                
                for task in ready_tasks:
                    if task in sorted_tasks:
                        sorted_tasks.remove(task)
                    
                    future = executor.submit(self.execute_task, task)
                    future_to_task[future] = task
                
                # 완료된 태스크들 처리
                completed_futures = []
                for future in concurrent.futures.as_completed(future_to_task, timeout=1):
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        results.append(result)
                        completed_futures.append(future)
                        
                        if not result.success:
                            logger.error(f"태스크 {task.id} 실패로 인한 실행 중단")
                            # 실패한 태스크의 의존성을 가진 태스크들 제거
                            sorted_tasks = [t for t in sorted_tasks if task.id not in t.deps]
                    
                    except Exception as e:
                        logger.error(f"태스크 {task.id} 실행 중 예외: {e}")
                        completed_futures.append(future)
                
                # 완료된 태스크들 정리
                for future in completed_futures:
                    del future_to_task[future]
                
                # 모든 태스크가 완료되면 종료
                if not sorted_tasks and not future_to_task:
                    break
        
        return results
    
    def generate_report(self, results: List[ExecutionResult]) -> str:
        """실행 결과 리포트 생성"""
        total_tasks = len(results)
        successful_tasks = len([r for r in results if r.success])
        failed_tasks = total_tasks - successful_tasks
        
        total_duration = sum(r.duration for r in results)
        avg_duration = total_duration / total_tasks if total_tasks > 0 else 0
        
        report = f"""
# 우선순위 기반 실행 결과 리포트

## 📊 **실행 요약**
- **실행 전략**: {self.strategy.value}
- **총 태스크 수**: {total_tasks}
- **성공한 태스크**: {successful_tasks}
- **실패한 태스크**: {failed_tasks}
- **성공률**: {(successful_tasks/total_tasks*100):.1f}%
- **총 실행 시간**: {total_duration:.2f}초
- **평균 실행 시간**: {avg_duration:.2f}초

## 📋 **태스크별 결과**
"""
        
        for result in results:
            status = "✅ 성공" if result.success else "❌ 실패"
            report += f"""
### {result.task_id}
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
        
        report += f"""
## 🎯 **개선 제안**
"""
        
        if failed_tasks > 0:
            report += "- 실패한 태스크의 의존성 및 설정을 재검토하세요\n"
        
        if avg_duration > 60:
            report += "- 실행 시간이 긴 태스크들을 병렬 처리로 최적화하세요\n"
        
        if successful_tasks / total_tasks < 0.8:
            report += "- 태스크 실행 전 조건을 더 엄격히 검증하세요\n"
        
        return report

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='우선순위 기반 태스크 실행')
    parser.add_argument('--input', '-i', required=True, help='입력 태스크 파일 (tasks.reflected.json)')
    parser.add_argument('--strategy', '-s', choices=['dependency', 'complexity', 'efficiency'], 
                       default='dependency', help='실행 전략')
    parser.add_argument('--parallel', '-p', action='store_true', help='병렬 실행 모드')
    parser.add_argument('--max-workers', '-w', type=int, default=2, help='최대 워커 수 (병렬 모드)')
    parser.add_argument('--output', '-o', help='결과 리포트 출력 파일')
    
    args = parser.parse_args()
    
    try:
        # 실행기 초기화
        strategy = ExecutionStrategy(args.strategy)
        executor = TaskExecutor(strategy)
        
        # 태스크 로드
        tasks = executor.load_tasks(args.input)
        
        # 실행 시작
        executor.start_time = time.time()
        
        if args.parallel:
            results = executor.execute_parallel(tasks, args.max_workers)
        else:
            results = executor.execute_sequential(tasks)
        
        executor.end_time = time.time()
        
        # 리포트 생성
        report = executor.generate_report(results)
        
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
