#!/usr/bin/env python3
"""
병렬 처리 디버깅 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parallel_executor import ParallelExecutor, Task

def debug_parallel_detection():
    """병렬 처리 가능성 감지 디버깅"""
    print("🔍 병렬 처리 가능성 감지 디버깅")
    
    executor = ParallelExecutor()
    
    # 테스트 태스크 생성
    test_task = Task(
        id="test:build",
        title="Test Build",
        module="test",
        type="code",
        deps=[],
        complexity=1.3,
        acceptance=["build success"],
        order=1
    )
    
    print(f"태스크: {test_task.id}")
    print(f"타입: {test_task.type}")
    print(f"복잡도: {test_task.complexity}")
    print(f"can_parallel: {test_task.can_parallel}")
    print(f"parallel_compatibility: {test_task.parallel_compatibility}")
    
    # 리소스 추정 확인
    executor = ParallelExecutor()
    estimated_duration = executor._estimate_duration(test_task)
    priority_score = executor._calculate_priority(test_task)
    resource_requirements = executor._get_resource_requirements(test_task)
    
    print(f"예상 실행 시간: {estimated_duration}")
    print(f"우선순위 점수: {priority_score}")
    print(f"리소스 요구사항: {resource_requirements}")
    
    # 타입별 분류 확인
    parallel_types = ['config', 'cli', 'doc', 'test']
    sequential_types = ['code', 'ide', 'mcp']
    
    print(f"\n타입 분류:")
    print(f"parallel_types: {parallel_types}")
    print(f"sequential_types: {sequential_types}")
    print(f"task.type in parallel_types: {test_task.type in parallel_types}")
    print(f"task.type in sequential_types: {test_task.type in sequential_types}")

if __name__ == "__main__":
    debug_parallel_detection()
