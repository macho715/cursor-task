#!/usr/bin/env python3
"""
자동 리플렉션 데모
자동 리플렉션 시스템의 실제 동작을 시뮬레이션으로 보여주는 데모
"""

import json
import time
import sys
import os
import threading
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auto_reflector import AutoReflector, ReflectionConfig

def create_demo_tasks():
    """데모용 태스크 파일 생성"""
    demo_tasks = {
        "tasks": [
            {
                "id": "demo:setup",
                "title": "Demo Setup",
                "module": "demo",
                "type": "config",
                "deps": [],
                "complexity": 1.1,
                "acceptance": ["setup complete"],
                "order": 0
            },
            {
                "id": "demo:build",
                "title": "Demo Build",
                "module": "demo", 
                "type": "code",
                "deps": ["demo:setup"],
                "complexity": 1.3,
                "acceptance": ["build success"],
                "order": 1
            },
            {
                "id": "demo:test",
                "title": "Demo Test",
                "module": "demo",
                "type": "test",
                "deps": ["demo:build"],
                "complexity": 1.2,
                "acceptance": ["tests pass"],
                "order": 2
            }
        ]
    }
    
    with open("demo_tasks.json", "w") as f:
        json.dump(demo_tasks, f, indent=2)
    
    print("📁 데모 태스크 파일 생성: demo_tasks.json")
    return "demo_tasks.json"

def simulate_file_changes(auto_reflector, duration=10):
    """파일 변경 시뮬레이션"""
    print(f"\n🔄 {duration}초간 파일 변경 시뮬레이션 시작...")
    
    start_time = time.time()
    change_count = 0
    
    while time.time() - start_time < duration:
        # 파일 내용 수정
        with open("demo_tasks.json", "r") as f:
            data = json.load(f)
        
        # 복잡도 업데이트 (시뮬레이션)
        for task in data["tasks"]:
            task["complexity"] = round(task["complexity"] + 0.1, 1)
        
        with open("demo_tasks.json", "w") as f:
            json.dump(data, f, indent=2)
        
        change_count += 1
        print(f"  📝 파일 변경 #{change_count} - 복잡도 업데이트")
        
        # 리플렉션 트리거
        auto_reflector.trigger_reflection(
            event_type="file_modified",
            file_path="demo_tasks.json",
            triggered_by="demo_simulation"
        )
        
        time.sleep(2)  # 2초 간격
    
    print(f"✅ 파일 변경 시뮬레이션 완료 ({change_count}회 변경)")

def demo_watch_mode():
    """파일 감시 모드 데모"""
    print("🎯 파일 감시 모드 데모")
    print("=" * 60)
    
    # 데모 파일 생성
    input_file = create_demo_tasks()
    
    # 설정
    config = ReflectionConfig(
        input_file=input_file,
        output_file="demo_tasks.reflected.json",
        report_file="reports/demo_reflect_report.md",
        watch_directories=["."],
        watch_extensions=[".json"],
        notification_channels=["console", "log"]
    )
    
    # 자동 리플렉션 시스템 초기화
    auto_reflector = AutoReflector(config)
    
    print(f"설정 완료:")
    print(f"  - 입력 파일: {config.input_file}")
    print(f"  - 출력 파일: {config.output_file}")
    print(f"  - 감시 디렉토리: {config.watch_directories}")
    print(f"  - 감시 확장자: {config.watch_extensions}")
    
    # 파일 변경 시뮬레이션 (별도 스레드)
    simulation_thread = threading.Thread(
        target=simulate_file_changes,
        args=(auto_reflector, 15)
    )
    simulation_thread.start()
    
    # 감시 모드 시뮬레이션
    print("\n👀 파일 감시 시작...")
    time.sleep(18)  # 시뮬레이션 완료까지 대기
    
    simulation_thread.join()
    
    # 결과 확인
    print("\n📊 감시 모드 결과:")
    stats = auto_reflector.get_statistics()
    print(f"  - 총 리플렉션: {stats['total_reflections']}")
    print(f"  - 성공한 리플렉션: {stats['successful_reflections']}")
    print(f"  - 실패한 리플렉션: {stats['failed_reflections']}")
    print(f"  - 성공률: {stats['success_rate']:.1f}%")
    
    if os.path.exists("demo_tasks.reflected.json"):
        print(f"  - 출력 파일 생성: demo_tasks.reflected.json")
    
    if os.path.exists("reports/demo_reflect_report.md"):
        print(f"  - 리포트 파일 생성: reports/demo_reflect_report.md")

def demo_scheduled_mode():
    """스케줄 모드 데모"""
    print("\n🎯 스케줄 모드 데모")
    print("=" * 60)
    
    # 설정 (10초 간격)
    config = ReflectionConfig(
        input_file="demo_tasks.json",
        output_file="demo_tasks_scheduled.reflected.json",
        report_file="reports/demo_scheduled_report.md",
        reflection_interval=5,  # 5초 간격
        notification_channels=["console"]
    )
    
    auto_reflector = AutoReflector(config)
    
    print(f"스케줄 설정:")
    print(f"  - 리플렉션 간격: {config.reflection_interval}초")
    print(f"  - 예상 실행 횟수: 3회 (15초간)")
    
    # 스케줄 모드 시뮬레이션
    print("\n⏰ 스케줄 모드 시작...")
    
    for i in range(3):
        print(f"  🔄 스케줄 실행 #{i+1}")
        auto_reflector.trigger_reflection(
            event_type="scheduled",
            file_path="demo_tasks.json",
            triggered_by="scheduler"
        )
        time.sleep(5)
    
    print("✅ 스케줄 모드 완료")
    
    # 결과 확인
    stats = auto_reflector.get_statistics()
    print(f"\n📊 스케줄 모드 결과:")
    print(f"  - 총 리플렉션: {stats['total_reflections']}")
    print(f"  - 성공률: {stats['success_rate']:.1f}%")

def demo_webhook_mode():
    """웹훅 모드 데모"""
    print("\n🎯 웹훅 모드 데모")
    print("=" * 60)
    
    # 설정
    config = ReflectionConfig(
        input_file="demo_tasks.json",
        output_file="demo_tasks_webhook.reflected.json",
        report_file="reports/demo_webhook_report.md",
        webhook_port=8082,  # 테스트용 포트
        notification_channels=["console"]
    )
    
    auto_reflector = AutoReflector(config)
    
    print(f"웹훅 설정:")
    print(f"  - 포트: {config.webhook_port}")
    print(f"  - 엔드포인트: /reflect, /status, /history")
    
    # 웹훅 트리거 시뮬레이션
    print("\n🌐 웹훅 트리거 시뮬레이션...")
    
    webhook_triggers = [
        {"event_type": "webhook", "file_path": "demo_tasks.json", "triggered_by": "webhook_client_1"},
        {"event_type": "webhook", "file_path": "demo_tasks.json", "triggered_by": "webhook_client_2"},
        {"event_type": "webhook", "file_path": "demo_tasks.json", "triggered_by": "webhook_client_3"}
    ]
    
    for i, trigger in enumerate(webhook_triggers):
        print(f"  📡 웹훅 트리거 #{i+1}: {trigger['triggered_by']}")
        auto_reflector.trigger_reflection(**trigger)
        time.sleep(1)
    
    print("✅ 웹훅 모드 완료")
    
    # 결과 확인
    stats = auto_reflector.get_statistics()
    print(f"\n📊 웹훅 모드 결과:")
    print(f"  - 총 리플렉션: {stats['total_reflections']}")
    print(f"  - 성공률: {stats['success_rate']:.1f}%")

def demo_error_handling():
    """에러 처리 데모"""
    print("\n🎯 에러 처리 데모")
    print("=" * 60)
    
    # 잘못된 설정으로 에러 시뮬레이션
    config = ReflectionConfig(
        input_file="nonexistent_file.json",  # 존재하지 않는 파일
        output_file="error_output.json",
        report_file="reports/error_report.md",
        notification_channels=["console"]
    )
    
    auto_reflector = AutoReflector(config)
    
    print("에러 상황 시뮬레이션:")
    print("  - 존재하지 않는 입력 파일 사용")
    print("  - 리플렉션 실패 처리")
    
    # 에러 발생 리플렉션
    print("\n❌ 에러 발생 리플렉션 시도...")
    success = auto_reflector.trigger_reflection(
        event_type="error_test",
        file_path="nonexistent_file.json",
        triggered_by="error_demo"
    )
    
    print(f"  결과: {'성공' if success else '실패'}")
    
    # 에러 통계 확인
    stats = auto_reflector.get_statistics()
    print(f"\n📊 에러 처리 결과:")
    print(f"  - 총 리플렉션: {stats['total_reflections']}")
    print(f"  - 실패한 리플렉션: {stats['failed_reflections']}")
    print(f"  - 성공률: {stats['success_rate']:.1f}%")
    
    if auto_reflector.reflection_history:
        error_event = auto_reflector.reflection_history[0]
        print(f"  - 에러 메시지: {error_event.error_message}")

def cleanup_demo_files():
    """데모 파일 정리"""
    demo_files = [
        "demo_tasks.json",
        "demo_tasks.reflected.json",
        "demo_tasks_scheduled.reflected.json", 
        "demo_tasks_webhook.reflected.json",
        "error_output.json",
        "reports/demo_reflect_report.md",
        "reports/demo_scheduled_report.md",
        "reports/demo_webhook_report.md",
        "reports/error_report.md",
        "auto_reflection.log"
    ]
    
    cleaned = 0
    for file in demo_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                cleaned += 1
            except PermissionError:
                # 로그 파일 등은 삭제하지 않음
                pass
    
    print(f"\n🧹 데모 파일 정리 완료: {cleaned}개 파일 삭제")

def main():
    """메인 함수"""
    print("🚀 자동 리플렉션 데모")
    print("자동 리플렉션 시스템의 다양한 모드를 시뮬레이션으로 보여줍니다.")
    print()
    
    try:
        # 각 모드별 데모 실행
        demo_watch_mode()
        demo_scheduled_mode()
        demo_webhook_mode()
        demo_error_handling()
        
        print("\n🎉 자동 리플렉션 데모 완료!")
        print("\n💡 실제 자동 리플렉션을 원하시면:")
        print("   python tools/auto_reflector.py --mode watch --input tasks.json")
        print("   또는")
        print("   .\\tools\\run_auto_reflect.ps1 -Mode watch -InputFile tasks.json")
        
    except KeyboardInterrupt:
        print("\n⏹️ 데모가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 데모 실행 중 오류 발생: {e}")
    finally:
        # 데모 파일 정리
        cleanup_demo_files()

if __name__ == "__main__":
    main()
