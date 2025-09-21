#!/usr/bin/env python3
"""
우선순위 기반 실행 데모
실제 실행 없이 시뮬레이션으로 데모 실행
"""

import json
import time
import sys
import os
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from execute_priority import TaskExecutor, ExecutionStrategy, Task

def simulate_task_execution(task: Task) -> dict:
    """태스크 실행 시뮬레이션"""
    print(f"  🔄 {task.id} 실행 중... (복잡도: {task.complexity})")
    
    # 복잡도에 따른 실행 시간 시뮬레이션
    execution_time = task.complexity * 2  # 복잡도 * 2초
    time.sleep(0.1)  # 실제로는 0.1초만 대기 (데모용)
    
    # 성공률 시뮬레이션 (복잡도가 높을수록 실패 확률 증가)
    success_rate = max(0.7, 1.0 - (task.complexity - 1.0) * 0.2)
    success = task.complexity < 2.0  # 복잡도 2.0 이상은 실패로 시뮬레이션
    
    result = {
        "task_id": task.id,
        "success": success,
        "duration": execution_time,
        "timestamp": datetime.now().isoformat()
    }
    
    if success:
        print(f"  ✅ {task.id} 완료 ({execution_time:.1f}초)")
    else:
        print(f"  ❌ {task.id} 실패 (복잡도 {task.complexity} > 2.0)")
    
    return result

def demo_dependency_strategy():
    """의존성 전략 데모"""
    print("🎯 의존성 전략 데모 실행")
    print("=" * 50)
    
    # 태스크 파일 로드
    with open("tasks.reflected.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    tasks = []
    for task_data in data["tasks"]:
        task = Task(
            id=task_data["id"],
            title=task_data["title"],
            module=task_data["module"],
            type=task_data["type"],
            deps=task_data.get("deps", []),
            complexity=task_data.get("complexity", 1.0),
            acceptance=task_data.get("acceptance", []),
            order=task_data.get("order", 0)
        )
        tasks.append(task)
    
    # 의존성 전략으로 정렬
    executor = TaskExecutor(ExecutionStrategy.DEPENDENCY)
    sorted_tasks = executor.sort_tasks(tasks)
    
    print(f"총 {len(sorted_tasks)}개 태스크를 의존성 순서로 실행:")
    print()
    
    results = []
    completed_tasks = set()
    
    for task in sorted_tasks:
        # 의존성 확인
        if not all(dep in completed_tasks for dep in task.deps):
            print(f"  ⏸️ {task.id} 대기 중 (의존성 미완료)")
            continue
        
        # 태스크 실행 시뮬레이션
        result = simulate_task_execution(task)
        results.append(result)
        
        if result["success"]:
            completed_tasks.add(task.id)
        else:
            print(f"  🛑 {task.id} 실패로 인한 실행 중단")
            break
        
        print()
    
    # 결과 요약
    successful = len([r for r in results if r["success"]])
    total = len(results)
    total_time = sum(r["duration"] for r in results)
    
    print("=" * 50)
    print("📊 실행 결과 요약:")
    print(f"  - 성공한 태스크: {successful}/{total}")
    print(f"  - 성공률: {(successful/total*100):.1f}%" if total > 0 else "  - 성공률: 0%")
    print(f"  - 총 실행 시간: {total_time:.1f}초")
    print(f"  - 평균 실행 시간: {(total_time/total):.1f}초" if total > 0 else "  - 평균 실행 시간: 0초")

def demo_complexity_strategy():
    """복잡도 전략 데모"""
    print("\n🎯 복잡도 전략 데모 실행")
    print("=" * 50)
    
    # 태스크 파일 로드
    with open("tasks.reflected.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    tasks = []
    for task_data in data["tasks"]:
        task = Task(
            id=task_data["id"],
            title=task_data["title"],
            module=task_data["module"],
            type=task_data["type"],
            deps=task_data.get("deps", []),
            complexity=task_data.get("complexity", 1.0),
            acceptance=task_data.get("acceptance", []),
            order=task_data.get("order", 0)
        )
        tasks.append(task)
    
    # 복잡도 전략으로 정렬
    executor = TaskExecutor(ExecutionStrategy.COMPLEXITY)
    sorted_tasks = executor.sort_tasks(tasks)
    
    print(f"총 {len(sorted_tasks)}개 태스크를 복잡도 높은 순으로 실행:")
    print()
    
    results = []
    
    for task in sorted_tasks:
        print(f"  📋 {task.id}")
        print(f"      복잡도: {task.complexity}")
        print(f"      의존성: {len(task.deps)}개")
        print(f"      타입: {task.type}")
        
        # 태스크 실행 시뮬레이션
        result = simulate_task_execution(task)
        results.append(result)
        
        print()
    
    # 결과 요약
    successful = len([r for r in results if r["success"]])
    total = len(results)
    total_time = sum(r["duration"] for r in results)
    
    print("=" * 50)
    print("📊 실행 결과 요약:")
    print(f"  - 성공한 태스크: {successful}/{total}")
    print(f"  - 성공률: {(successful/total*100):.1f}%" if total > 0 else "  - 성공률: 0%")
    print(f"  - 총 실행 시간: {total_time:.1f}초")
    print(f"  - 평균 실행 시간: {(total_time/total):.1f}초" if total > 0 else "  - 평균 실행 시간: 0초")

def main():
    """메인 함수"""
    print("🚀 우선순위 기반 실행 데모")
    print("실제 실행 없이 시뮬레이션으로 데모를 진행합니다.")
    print()
    
    try:
        # 의존성 전략 데모
        demo_dependency_strategy()
        
        # 복잡도 전략 데모
        demo_complexity_strategy()
        
        print("\n🎉 데모 완료!")
        print("\n💡 실제 실행을 원하시면:")
        print("   python tools/execute_priority.py --input tasks.reflected.json")
        print("   또는")
        print("   .\\tools\\run_priority.ps1")
        
    except FileNotFoundError:
        print("❌ tasks.reflected.json 파일을 찾을 수 없습니다.")
        print("   먼저 python tools/tasks_reflect.py를 실행하여 파일을 생성하세요.")
    except Exception as e:
        print(f"❌ 데모 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
