#!/usr/bin/env python3
"""
병렬 처리 데모
병렬 실행 엔진의 실제 동작을 시뮬레이션으로 보여주는 데모
"""

import json
import time
import sys
import os
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parallel_executor import ParallelExecutor, ParallelStrategy, Task

def simulate_task_execution(task: Task, worker_id: int) -> dict:
    """태스크 실행 시뮬레이션"""
    print(f"  [워커 {worker_id}] 🔄 {task.id} 실행 중... (복잡도: {task.complexity}, 타입: {task.type})")
    
    # 복잡도와 타입에 따른 실행 시간 시뮬레이션
    base_time = 2.0
    complexity_factor = task.complexity
    type_factor = {
        'code': 1.5,
        'config': 0.8,
        'cli': 1.0,
        'mcp': 2.0,
        'ide': 1.2,
        'doc': 0.5,
        'test': 1.0
    }.get(task.type, 1.0)
    
    execution_time = base_time * complexity_factor * type_factor
    
    # 시뮬레이션을 위한 짧은 대기
    time.sleep(0.1)
    
    # 성공률 시뮬레이션 (복잡도가 높을수록 실패 확률 증가)
    success_rate = max(0.7, 1.0 - (task.complexity - 1.0) * 0.2)
    success = task.complexity < 2.5  # 복잡도 2.5 이상은 실패로 시뮬레이션
    
    result = {
        "task_id": task.id,
        "success": success,
        "duration": execution_time,
        "timestamp": datetime.now().isoformat(),
        "worker_id": worker_id,
        "type": task.type,
        "complexity": task.complexity
    }
    
    if success:
        print(f"  [워커 {worker_id}] ✅ {task.id} 완료 ({execution_time:.1f}초)")
    else:
        print(f"  [워커 {worker_id}] ❌ {task.id} 실패 (복잡도 {task.complexity} > 2.5)")
    
    return result

def demo_sequential_execution():
    """순차 실행 데모"""
    print("🎯 순차 실행 데모")
    print("=" * 60)
    
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
    
    print(f"총 {len(tasks)}개 태스크를 순차적으로 실행:")
    print()
    
    results = []
    completed_tasks = set()
    start_time = time.time()
    
    for task in tasks:
        # 의존성 확인
        if not all(dep in completed_tasks for dep in task.deps):
            print(f"  ⏸️ {task.id} 대기 중 (의존성 미완료)")
            continue
        
        # 태스크 실행 시뮬레이션
        result = simulate_task_execution(task, worker_id=0)
        results.append(result)
        
        if result["success"]:
            completed_tasks.add(task.id)
        else:
            print(f"  🛑 {task.id} 실패로 인한 실행 중단")
            break
        
        print()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # 결과 요약
    successful = len([r for r in results if r["success"]])
    total = len(results)
    
    print("=" * 60)
    print("📊 순차 실행 결과 요약:")
    print(f"  - 성공한 태스크: {successful}/{total}")
    print(f"  - 성공률: {(successful/total*100):.1f}%" if total > 0 else "  - 성공률: 0%")
    print(f"  - 총 실행 시간: {total_time:.2f}초")
    print(f"  - 평균 실행 시간: {(total_time/total):.2f}초" if total > 0 else "  - 평균 실행 시간: 0초")
    
    return total_time, results

def demo_parallel_execution():
    """병렬 실행 데모"""
    print("\n🎯 병렬 실행 데모 (Smart Strategy)")
    print("=" * 60)
    
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
    
    # 병렬 실행기 초기화
    executor = ParallelExecutor(ParallelStrategy.SMART, max_workers=3)
    
    # 의존성 그래프 구축
    executor.build_dependency_graph(tasks)
    
    # 병렬 그룹 식별
    groups = executor.identify_parallel_groups(tasks)
    
    print(f"총 {len(tasks)}개 태스크를 {len(groups)}개 병렬 그룹으로 실행:")
    print()
    
    all_results = []
    completed_tasks = set()
    start_time = time.time()
    
    for i, group in enumerate(groups):
        print(f"🚀 그룹 {i+1} 실행 시작: {group.id}")
        print(f"   태스크: {[t.id for t in group.tasks]}")
        print(f"   예상 실행 시간: {group.estimated_duration:.2f}초")
        
        group_start_time = time.time()
        
        # 그룹 내 태스크들을 병렬로 시뮬레이션
        group_results = []
        if len(group.tasks) == 1:
            # 단일 태스크
            task = group.tasks[0]
            if all(dep in completed_tasks for dep in task.deps):
                result = simulate_task_execution(task, worker_id=0)
                group_results.append(result)
        else:
            # 다중 태스크 병렬 실행 시뮬레이션
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(group.tasks), 3)) as executor_pool:
                future_to_task = {}
                
                for j, task in enumerate(group.tasks):
                    if all(dep in completed_tasks for dep in task.deps):
                        future = executor_pool.submit(simulate_task_execution, task, worker_id=j % 3)
                        future_to_task[future] = task
                
                # 결과 수집
                for future in concurrent.futures.as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        group_results.append(result)
                    except Exception as e:
                        print(f"  ❌ {task.id} 실행 중 오류: {e}")
        
        group_end_time = time.time()
        group_duration = group_end_time - group_start_time
        
        print(f"✅ 그룹 {i+1} 완료 ({group_duration:.2f}초)")
        print()
        
        # 완료된 태스크 업데이트
        for result in group_results:
            if result["success"]:
                completed_tasks.add(result["task_id"])
            all_results.append(result)
        
        # 실패한 태스크가 있으면 중단
        if any(not result["success"] for result in group_results):
            print("  🛑 그룹에서 실패한 태스크가 있어 실행 중단")
            break
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # 결과 요약
    successful = len([r for r in all_results if r["success"]])
    total = len(all_results)
    
    print("=" * 60)
    print("📊 병렬 실행 결과 요약:")
    print(f"  - 성공한 태스크: {successful}/{total}")
    print(f"  - 성공률: {(successful/total*100):.1f}%" if total > 0 else "  - 성공률: 0%")
    print(f"  - 총 실행 시간: {total_time:.2f}초")
    print(f"  - 평균 실행 시간: {(total_time/total):.2f}초" if total > 0 else "  - 평균 실행 시간: 0초")
    
    # 워커별 통계
    worker_stats = {}
    for result in all_results:
        worker_id = result["worker_id"]
        if worker_id not in worker_stats:
            worker_stats[worker_id] = {"count": 0, "duration": 0.0, "success": 0}
        worker_stats[worker_id]["count"] += 1
        worker_stats[worker_id]["duration"] += result["duration"]
        if result["success"]:
            worker_stats[worker_id]["success"] += 1
    
    print("\n🔧 워커별 성능:")
    for worker_id, stats in worker_stats.items():
        success_rate = (stats["success"] / stats["count"] * 100) if stats["count"] > 0 else 0
        print(f"  - 워커 {worker_id}: {stats['count']}개 태스크, {stats['duration']:.1f}초, 성공률 {success_rate:.1f}%")
    
    return total_time, all_results

def demo_performance_comparison():
    """성능 비교 데모"""
    print("\n🎯 성능 비교 데모")
    print("=" * 60)
    
    # 순차 실행
    sequential_time, sequential_results = demo_sequential_execution()
    
    # 병렬 실행
    parallel_time, parallel_results = demo_parallel_execution()
    
    # 성능 비교
    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    efficiency = (speedup / 3) * 100  # 3개 워커 기준
    
    print("\n📈 성능 비교 결과:")
    print("=" * 60)
    print(f"순차 실행:")
    print(f"  - 실행 시간: {sequential_time:.2f}초")
    print(f"  - 성공한 태스크: {len([r for r in sequential_results if r['success']])}/{len(sequential_results)}")
    
    print(f"\n병렬 실행:")
    print(f"  - 실행 시간: {parallel_time:.2f}초")
    print(f"  - 성공한 태스크: {len([r for r in parallel_results if r['success']])}/{len(parallel_results)}")
    
    print(f"\n성능 향상:")
    print(f"  - 속도 향상: {speedup:.2f}x")
    print(f"  - 병렬 효율성: {efficiency:.1f}%")
    print(f"  - 시간 절약: {(sequential_time - parallel_time):.2f}초")
    
    if efficiency > 80:
        print(f"  - 평가: 🟢 우수한 병렬 효율성!")
    elif efficiency > 60:
        print(f"  - 평가: 🟡 양호한 병렬 효율성")
    else:
        print(f"  - 평가: 🔴 병렬 효율성 개선 필요")

def main():
    """메인 함수"""
    print("🚀 병렬 처리 데모")
    print("실제 실행 없이 시뮬레이션으로 병렬 처리의 효과를 보여줍니다.")
    print()
    
    try:
        # 성능 비교 데모
        demo_performance_comparison()
        
        print("\n🎉 병렬 처리 데모 완료!")
        print("\n💡 실제 병렬 실행을 원하시면:")
        print("   python tools/parallel_executor.py --input tasks.reflected.json --strategy smart")
        print("   또는")
        print("   .\\tools\\run_parallel.ps1 -Strategy smart -MaxWorkers 4")
        
    except FileNotFoundError:
        print("❌ tasks.reflected.json 파일을 찾을 수 없습니다.")
        print("   먼저 python tools/tasks_reflect.py를 실행하여 파일을 생성하세요.")
    except Exception as e:
        print(f"❌ 데모 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
