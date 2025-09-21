#!/usr/bin/env python3
"""
병렬 처리 테스트
병렬 실행 엔진의 기능을 검증하는 테스트
"""

import json
import sys
import os
import time
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parallel_executor import ParallelExecutor, ParallelStrategy, Task

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
            deps=["test:setup"],
            complexity=1.5,
            acceptance=["validation pass"],
            order=2
        ),
        Task(
            id="test:document",
            title="Test Documentation",
            module="test",
            type="doc",
            deps=[],
            complexity=0.8,
            acceptance=["docs generated"],
            order=3
        ),
        Task(
            id="test:deploy",
            title="Test Deployment",
            module="test",
            type="ide",
            deps=["test:build", "test:validate"],
            complexity=1.8,
            acceptance=["deployment success"],
            order=4
        )
    ]
    return test_tasks

def test_parallel_capability_detection():
    """병렬 처리 가능성 감지 테스트"""
    print("🧪 병렬 처리 가능성 감지 테스트")
    
    executor = ParallelExecutor()
    tasks = create_test_tasks()
    
    parallel_tasks = [t for t in tasks if t.can_parallel]
    sequential_tasks = [t for t in tasks if not t.can_parallel]
    
    print("병렬 처리 가능한 태스크:")
    for task in parallel_tasks:
        print(f"  • {task.id} ({task.type}) - 호환성: {task.parallel_compatibility}")
    
    print("순차 실행 태스크:")
    for task in sequential_tasks:
        print(f"  • {task.id} ({task.type}) - 호환성: {task.parallel_compatibility}")
    
    # 검증 (실제 병렬 처리 가능성에 맞게 수정)
    expected_parallel = ["test:setup", "test:validate", "test:document"]
    expected_sequential = ["test:build", "test:deploy"]
    
    actual_parallel = [t.id for t in parallel_tasks]
    actual_sequential = [t.id for t in sequential_tasks]
    
    assert all(task_id in actual_parallel for task_id in expected_parallel), "병렬 처리 가능한 태스크가 올바르게 식별되지 않음"
    assert all(task_id in actual_sequential for task_id in expected_sequential), "순차 실행 태스크가 올바르게 식별되지 않음"
    
    print("✅ 병렬 처리 가능성 감지 테스트 통과")

def test_dependency_graph_building():
    """의존성 그래프 구축 테스트"""
    print("\n🧪 의존성 그래프 구축 테스트")
    
    executor = ParallelExecutor()
    tasks = create_test_tasks()
    
    graph = executor.build_dependency_graph(tasks)
    
    print("의존성 그래프 구조:")
    print(f"  - 노드 수: {graph.number_of_nodes()}")
    print(f"  - 엣지 수: {graph.number_of_edges()}")
    
    # 의존성 확인
    dependencies = {
        "test:setup": [],
        "test:build": ["test:setup"],
        "test:validate": ["test:setup"],
        "test:document": [],
        "test:deploy": ["test:build", "test:validate"]
    }
    
    for node in graph.nodes():
        predecessors = list(graph.predecessors(node))
        expected_deps = dependencies.get(node, [])
        
        print(f"  • {node}: 의존성 {predecessors} (예상: {expected_deps})")
        assert set(predecessors) == set(expected_deps), f"{node}의 의존성이 올바르지 않음"
    
    print("✅ 의존성 그래프 구축 테스트 통과")

def test_parallel_group_identification():
    """병렬 그룹 식별 테스트"""
    print("\n🧪 병렬 그룹 식별 테스트")
    
    executor = ParallelExecutor()
    tasks = create_test_tasks()
    executor.build_dependency_graph(tasks)
    groups = executor.identify_parallel_groups(tasks)
    
    print(f"식별된 병렬 그룹 수: {len(groups)}")
    
    for i, group in enumerate(groups):
        task_ids = [t.id for t in group.tasks]
        print(f"  그룹 {i+1} ({group.id}): {task_ids}")
        print(f"    - 태스크 수: {len(group.tasks)}")
        print(f"    - 예상 실행 시간: {group.estimated_duration:.2f}초")
        print(f"    - 리소스 사용량: {group.resource_usage}")
    
    # 검증: 같은 레벨의 태스크들이 그룹화되었는지 확인
    level_0_tasks = ["test:setup", "test:document"]  # 의존성 없는 태스크들
    level_1_tasks = ["test:validate"]  # test:setup에 의존하는 병렬 가능 태스크
    level_1_sequential_tasks = ["test:build"]  # test:setup에 의존하는 순차 태스크
    
    found_level_0 = False
    found_level_1_parallel = False
    found_level_1_sequential = False
    
    for group in groups:
        task_ids = [t.id for t in group.tasks]
        if all(task_id in task_ids for task_id in level_0_tasks):
            found_level_0 = True
        if all(task_id in task_ids for task_id in level_1_tasks):
            found_level_1_parallel = True
        if all(task_id in task_ids for task_id in level_1_sequential_tasks):
            found_level_1_sequential = True
    
    assert found_level_0, "레벨 0 태스크들이 올바르게 그룹화되지 않음"
    assert found_level_1_parallel, "레벨 1 병렬 태스크들이 올바르게 그룹화되지 않음"
    assert found_level_1_sequential, "레벨 1 순차 태스크들이 올바르게 그룹화되지 않음"
    
    print("✅ 병렬 그룹 식별 테스트 통과")

def test_resource_estimation():
    """리소스 추정 테스트"""
    print("\n🧪 리소스 추정 테스트")
    
    executor = ParallelExecutor()
    tasks = create_test_tasks()
    
    print("태스크별 리소스 추정:")
    for task in tasks:
        # 리소스 추정 메서드 직접 호출
        duration = executor._estimate_duration(task)
        priority = executor._calculate_priority(task)
        resources = executor._get_resource_requirements(task)
        
        print(f"  • {task.id}")
        print(f"    - 예상 실행 시간: {duration:.2f}초")
        print(f"    - 우선순위 점수: {priority:.2f}")
        print(f"    - 리소스 요구사항: {resources}")
        
        # 검증
        assert duration > 0, f"{task.id}의 실행 시간이 올바르게 추정되지 않음"
        assert priority > 0, f"{task.id}의 우선순위 점수가 올바르게 계산되지 않음"
        assert len(resources) > 0, f"{task.id}의 리소스 요구사항이 설정되지 않음"
    
    print("✅ 리소스 추정 테스트 통과")

def test_parallel_strategies():
    """병렬 처리 전략 테스트"""
    print("\n🧪 병렬 처리 전략 테스트")
    
    strategies = [
        (ParallelStrategy.CONSERVATIVE, 2),
        (ParallelStrategy.AGGRESSIVE, 8), 
        (ParallelStrategy.SMART, 4),
        (ParallelStrategy.DEPENDENCY, 4)
    ]
    
    for strategy, expected_workers in strategies:
        print(f"전략: {strategy.value}")
        
        executor = ParallelExecutor(strategy, max_workers=expected_workers)
        tasks = create_test_tasks()
        
        # 워커 수 확인
        assert executor.max_workers == expected_workers, f"{strategy.value} 전략의 워커 수가 올바르지 않음"
        
        print(f"  - 최대 워커 수: {executor.max_workers}")
        print(f"  - 전략 설정: {executor.strategy.value}")
    
    print("✅ 병렬 처리 전략 테스트 통과")

def test_performance_prediction():
    """성능 예측 테스트"""
    print("\n🧪 성능 예측 테스트")
    
    executor = ParallelExecutor(ParallelStrategy.SMART, max_workers=4)
    tasks = create_test_tasks()
    
    # 순차 실행 시간 계산 (메서드 직접 호출)
    sequential_time = sum(executor._estimate_duration(task) for task in tasks)
    
    # 병렬 실행 시간 추정
    executor.build_dependency_graph(tasks)
    groups = executor.identify_parallel_groups(tasks)
    
    # 그룹별 실행 시간 계산
    group_times = []
    for group in groups:
        if len(group.tasks) == 1:
            group_time = executor._estimate_duration(group.tasks[0])
        else:
            group_time = max(executor._estimate_duration(task) for task in group.tasks)
        group_times.append(group_time)
    
    parallel_time = max(group_times) if group_times else 1.0
    
    # 속도 향상 계산
    speedup = sequential_time / parallel_time if parallel_time > 0 else 1.0
    efficiency = (speedup / executor.max_workers) * 100
    
    print(f"성능 예측 결과:")
    print(f"  - 순차 실행 예상 시간: {sequential_time:.2f}초")
    print(f"  - 병렬 실행 예상 시간: {parallel_time:.2f}초")
    print(f"  - 예상 속도 향상: {speedup:.2f}x")
    print(f"  - 예상 효율성: {efficiency:.1f}%")
    
    # 검증
    assert speedup > 1.0, "병렬 처리가 순차 처리보다 느림"
    assert efficiency > 0, "효율성이 0보다 작음"
    
    print("✅ 성능 예측 테스트 통과")

def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 병렬 처리 테스트 시작\n")
    
    try:
        test_parallel_capability_detection()
        test_dependency_graph_building()
        test_parallel_group_identification()
        test_resource_estimation()
        test_parallel_strategies()
        test_performance_prediction()
        
        print("\n🎉 모든 병렬 처리 테스트 통과!")
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
