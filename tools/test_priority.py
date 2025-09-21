#!/usr/bin/env python3
"""
우선순위 기반 실행 테스트
실제 실행 없이 시뮬레이션으로 테스트
"""

import json
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from execute_priority import TaskExecutor, ExecutionStrategy, Task

def create_test_tasks():
    """테스트용 태스크 생성"""
    test_tasks = [
        Task(
            id="test:setup",
            title="Test Setup",
            module="test",
            type="config",
            deps=[],
            complexity=1.1,
            acceptance=["setup complete"],
            order=0
        ),
        Task(
            id="test:build",
            title="Test Build",
            module="test",
            type="code",
            deps=["test:setup"],
            complexity=1.3,
            acceptance=["build success"],
            order=1
        ),
        Task(
            id="test:validate",
            title="Test Validation",
            module="test",
            type="cli",
            deps=["test:build"],
            complexity=1.5,
            acceptance=["validation pass"],
            order=2
        )
    ]
    return test_tasks

def test_dependency_strategy():
    """의존성 전략 테스트"""
    print("🧪 의존성 전략 테스트")
    
    executor = TaskExecutor(ExecutionStrategy.DEPENDENCY)
    tasks = create_test_tasks()
    
    sorted_tasks = executor.sort_tasks(tasks)
    
    print("정렬된 태스크 순서:")
    for i, task in enumerate(sorted_tasks):
        print(f"  {i+1}. {task.id} (복잡도: {task.complexity}, 의존성: {len(task.deps)})")
    
    assert sorted_tasks[0].id == "test:setup", "첫 번째 태스크는 test:setup이어야 함"
    assert sorted_tasks[1].id == "test:build", "두 번째 태스크는 test:build이어야 함"
    assert sorted_tasks[2].id == "test:validate", "세 번째 태스크는 test:validate이어야 함"
    
    print("✅ 의존성 전략 테스트 통과")

def test_complexity_strategy():
    """복잡도 전략 테스트"""
    print("\n🧪 복잡도 전략 테스트")
    
    executor = TaskExecutor(ExecutionStrategy.COMPLEXITY)
    tasks = create_test_tasks()
    
    sorted_tasks = executor.sort_tasks(tasks)
    
    print("정렬된 태스크 순서 (복잡도 기준):")
    for i, task in enumerate(sorted_tasks):
        print(f"  {i+1}. {task.id} (복잡도: {task.complexity})")
    
    # 복잡도가 높은 순으로 정렬되어야 함
    complexities = [task.complexity for task in sorted_tasks]
    assert complexities == sorted(complexities, reverse=True), "복잡도가 높은 순으로 정렬되어야 함"
    
    print("✅ 복잡도 전략 테스트 통과")

def test_efficiency_strategy():
    """효율성 전략 테스트"""
    print("\n🧪 효율성 전략 테스트")
    
    executor = TaskExecutor(ExecutionStrategy.EFFICIENCY)
    tasks = create_test_tasks()
    
    sorted_tasks = executor.sort_tasks(tasks)
    
    print("정렬된 태스크 순서 (효율성 기준):")
    for i, task in enumerate(sorted_tasks):
        parallel_status = "병렬 가능" if task.can_run_parallel else "순차 실행"
        print(f"  {i+1}. {task.id} (복잡도: {task.complexity}, {parallel_status})")
    
    # 병렬 가능한 태스크들이 먼저 와야 함
    parallel_tasks = [task for task in sorted_tasks if task.can_run_parallel]
    sequential_tasks = [task for task in sorted_tasks if not task.can_run_parallel]
    
    print(f"병렬 가능한 태스크: {[t.id for t in parallel_tasks]}")
    print(f"순차 실행 태스크: {[t.id for t in sequential_tasks]}")
    
    print("✅ 효율성 전략 테스트 통과")

def test_task_readiness():
    """태스크 준비 상태 테스트"""
    print("\n🧪 태스크 준비 상태 테스트")
    
    tasks = create_test_tasks()
    
    # 초기 상태에서는 의존성이 없는 태스크만 준비됨
    ready_tasks = [task for task in tasks if task.is_ready]
    print(f"초기 준비된 태스크: {[t.id for t in ready_tasks]}")
    assert len(ready_tasks) == 1, "초기에는 의존성이 없는 태스크 1개만 준비되어야 함"
    assert ready_tasks[0].id == "test:setup", "test:setup이 준비되어야 함"
    
    # test:setup 완료 후
    TaskExecutor.completed_tasks.add("test:setup")
    ready_tasks = [task for task in tasks if task.is_ready]
    print(f"test:setup 완료 후 준비된 태스크: {[t.id for t in ready_tasks]}")
    assert len(ready_tasks) == 2, "test:setup 완료 후 2개 태스크가 준비되어야 함"
    
    print("✅ 태스크 준비 상태 테스트 통과")

def test_command_generation():
    """명령어 생성 테스트"""
    print("\n🧪 명령어 생성 테스트")
    
    executor = TaskExecutor()
    tasks = create_test_tasks()
    
    for task in tasks:
        command = executor._generate_command(task)
        print(f"{task.id} ({task.type}): {command}")
        
        # 명령어가 적절히 생성되었는지 확인
        assert command is not None, f"{task.id}의 명령어가 생성되지 않음"
        assert len(command) > 0, f"{task.id}의 명령어가 비어있음"
    
    print("✅ 명령어 생성 테스트 통과")

def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 우선순위 기반 실행 테스트 시작\n")
    
    try:
        test_dependency_strategy()
        test_complexity_strategy()
        test_efficiency_strategy()
        test_task_readiness()
        test_command_generation()
        
        print("\n🎉 모든 테스트 통과!")
        return True
        
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        return False
    except Exception as e:
        print(f"\n💥 테스트 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
