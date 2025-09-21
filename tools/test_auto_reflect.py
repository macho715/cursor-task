#!/usr/bin/env python3
"""
자동 리플렉션 테스트
자동 리플렉션 시스템의 기능을 검증하는 테스트
"""

import json
import sys
import os
import time
import tempfile
import threading
from datetime import datetime

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auto_reflector import AutoReflector, ReflectionConfig, ReflectionMode

def create_test_files():
    """테스트용 파일 생성"""
    test_files = {
        "test_tasks.json": {
            "tasks": [
                {
                    "id": "test:task1",
                    "title": "Test Task 1",
                    "type": "code",
                    "deps": [],
                    "complexity": 1.0
                },
                {
                    "id": "test:task2", 
                    "title": "Test Task 2",
                    "type": "config",
                    "deps": ["test:task1"],
                    "complexity": 1.2
                }
            ]
        }
    }
    
    created_files = []
    for filename, content in test_files.items():
        with open(filename, 'w') as f:
            json.dump(content, f, indent=2)
        created_files.append(filename)
    
    return created_files

def cleanup_test_files(files):
    """테스트 파일 정리"""
    for file in files:
        if os.path.exists(file):
            os.remove(file)

def test_reflection_config():
    """리플렉션 설정 테스트"""
    print("🧪 리플렉션 설정 테스트")
    
    config = ReflectionConfig(
        input_file="test_tasks.json",
        output_file="test_tasks.reflected.json",
        report_file="test_report.md",
        watch_directories=["."],
        watch_extensions=[".json"],
        reflection_interval=60
    )
    
    print(f"입력 파일: {config.input_file}")
    print(f"출력 파일: {config.output_file}")
    print(f"감시 디렉토리: {config.watch_directories}")
    print(f"감시 확장자: {config.watch_extensions}")
    
    assert config.input_file == "test_tasks.json", "입력 파일 설정 오류"
    assert config.output_file == "test_tasks.reflected.json", "출력 파일 설정 오류"
    assert ".json" in config.watch_extensions, "감시 확장자 설정 오류"
    
    print("✅ 리플렉션 설정 테스트 통과")

def test_auto_reflector_initialization():
    """자동 리플렉션 시스템 초기화 테스트"""
    print("\n🧪 자동 리플렉션 시스템 초기화 테스트")
    
    config = ReflectionConfig(
        input_file="test_tasks.json",
        output_file="test_tasks.reflected.json",
        report_file="test_report.md"
    )
    
    auto_reflector = AutoReflector(config)
    
    print(f"설정 로드: {auto_reflector.config.input_file}")
    print(f"이력 초기화: {len(auto_reflector.reflection_history)}")
    print(f"실행 상태: {auto_reflector.is_running}")
    
    assert auto_reflector.config.input_file == "test_tasks.json", "설정 로드 오류"
    assert len(auto_reflector.reflection_history) == 0, "이력 초기화 오류"
    assert auto_reflector.is_running == False, "초기 실행 상태 오류"
    
    print("✅ 자동 리플렉션 시스템 초기화 테스트 통과")

def test_reflection_trigger():
    """리플렉션 트리거 테스트"""
    print("\n🧪 리플렉션 트리거 테스트")
    
    # 테스트 파일 생성
    test_files = create_test_files()
    
    try:
        config = ReflectionConfig(
            input_file="test_tasks.json",
            output_file="test_tasks.reflected.json",
            report_file="test_report.md"
        )
        
        auto_reflector = AutoReflector(config)
        
        # 리플렉션 트리거
        success = auto_reflector.trigger_reflection(
            event_type="test",
            file_path="test_tasks.json",
            triggered_by="test_script"
        )
        
        print(f"리플렉션 실행 결과: {success}")
        print(f"이력 개수: {len(auto_reflector.reflection_history)}")
        print(f"총 리플렉션 수: {auto_reflector.total_reflections}")
        print(f"성공한 리플렉션 수: {auto_reflector.successful_reflections}")
        
        assert len(auto_reflector.reflection_history) > 0, "이력 기록 오류"
        assert auto_reflector.total_reflections > 0, "총 리플렉션 수 오류"
        
        # 출력 파일 확인
        if os.path.exists("test_tasks.reflected.json"):
            print("✅ 출력 파일 생성 확인")
        
        # 리포트 파일 확인
        if os.path.exists("test_report.md"):
            print("✅ 리포트 파일 생성 확인")
    
    finally:
        cleanup_test_files(test_files)
        # 생성된 파일들도 정리
        cleanup_test_files(["test_tasks.reflected.json", "test_report.md"])
    
    print("✅ 리플렉션 트리거 테스트 통과")

def test_file_hash_calculation():
    """파일 해시 계산 테스트"""
    print("\n🧪 파일 해시 계산 테스트")
    
    # 테스트 파일 생성
    test_content = {"test": "data", "timestamp": datetime.now().isoformat()}
    test_file = "test_hash.json"
    
    try:
        with open(test_file, 'w') as f:
            json.dump(test_content, f)
        
        config = ReflectionConfig()
        auto_reflector = AutoReflector(config)
        
        # 해시 계산
        hash1 = auto_reflector._calculate_file_hash(test_file)
        
        # 파일 수정
        test_content["modified"] = True
        with open(test_file, 'w') as f:
            json.dump(test_content, f)
        
        hash2 = auto_reflector._calculate_file_hash(test_file)
        
        print(f"원본 파일 해시: {hash1}")
        print(f"수정된 파일 해시: {hash2}")
        print(f"해시 변경 여부: {hash1 != hash2}")
        
        assert hash1 != hash2, "파일 수정 후 해시가 변경되지 않음"
        assert len(hash1) == 32, "MD5 해시 길이 오류"
        assert len(hash2) == 32, "MD5 해시 길이 오류"
    
    finally:
        cleanup_test_files([test_file])
    
    print("✅ 파일 해시 계산 테스트 통과")

def test_statistics_tracking():
    """통계 추적 테스트"""
    print("\n🧪 통계 추적 테스트")
    
    config = ReflectionConfig(
        input_file="test_tasks.json",
        output_file="test_tasks.reflected.json",
        report_file="test_report.md"
    )
    
    auto_reflector = AutoReflector(config)
    
    # 초기 통계
    stats1 = auto_reflector.get_statistics()
    print(f"초기 통계: {stats1}")
    
    # 가짜 이벤트 추가
    from auto_reflector import ReflectionEvent
    
    event1 = ReflectionEvent(
        timestamp=datetime.now(),
        event_type="test",
        file_path="test.json",
        file_hash="hash1",
        success=True,
        duration=1.5,
        triggered_by="test"
    )
    
    event2 = ReflectionEvent(
        timestamp=datetime.now(),
        event_type="test",
        file_path="test.json",
        file_hash="hash2",
        success=False,
        duration=2.0,
        error_message="Test error",
        triggered_by="test"
    )
    
    auto_reflector.reflection_history.extend([event1, event2])
    auto_reflector.total_reflections = 2
    auto_reflector.successful_reflections = 1
    auto_reflector.failed_reflections = 1
    
    # 통계 확인
    stats2 = auto_reflector.get_statistics()
    print(f"업데이트된 통계: {stats2}")
    
    assert stats2["total_reflections"] == 2, "총 리플렉션 수 오류"
    assert stats2["successful_reflections"] == 1, "성공한 리플렉션 수 오류"
    assert stats2["failed_reflections"] == 1, "실패한 리플렉션 수 오류"
    assert stats2["success_rate"] == 50.0, "성공률 계산 오류"
    
    print("✅ 통계 추적 테스트 통과")

def test_notification_system():
    """알림 시스템 테스트"""
    print("\n🧪 알림 시스템 테스트")
    
    config = ReflectionConfig(
        notification_channels=["console", "log"]
    )
    
    auto_reflector = AutoReflector(config)
    
    # 테스트 이벤트
    from auto_reflector import ReflectionEvent
    
    event = ReflectionEvent(
        timestamp=datetime.now(),
        event_type="test",
        file_path="test.json",
        file_hash="test_hash",
        success=True,
        duration=1.0,
        triggered_by="test"
    )
    
    # 알림 발송 테스트 (콘솔 출력 확인)
    print("알림 발송 테스트:")
    auto_reflector._send_notifications(event)
    
    print("✅ 알림 시스템 테스트 통과")

def test_webhook_endpoints():
    """웹훅 엔드포인트 테스트"""
    print("\n🧪 웹훅 엔드포인트 테스트")
    
    config = ReflectionConfig(
        webhook_port=8081  # 테스트용 포트
    )
    
    auto_reflector = AutoReflector(config)
    
    # 웹훅 앱 설정
    auto_reflector._setup_webhook_routes()
    
    print("웹훅 앱 설정 완료")
    print(f"엔드포인트: /reflect, /status, /history")
    
    # 기본 테스트 (실제 서버 시작 없이)
    assert auto_reflector.webhook_app is not None, "웹훅 앱 초기화 오류"
    
    print("✅ 웹훅 엔드포인트 테스트 통과")

def test_error_handling():
    """에러 처리 테스트"""
    print("\n🧪 에러 처리 테스트")
    
    config = ReflectionConfig(
        input_file="nonexistent_file.json",  # 존재하지 않는 파일
        output_file="test_output.json",
        report_file="test_report.md"
    )
    
    auto_reflector = AutoReflector(config)
    
    # 존재하지 않는 파일로 리플렉션 시도
    success = auto_reflector.trigger_reflection(
        event_type="test",
        file_path="nonexistent_file.json",
        triggered_by="test"
    )
    
    print(f"존재하지 않는 파일 처리 결과: {success}")
    print(f"에러 이력: {len(auto_reflector.reflection_history)}")
    
    assert success == False, "존재하지 않는 파일이 성공으로 처리됨"
    assert len(auto_reflector.reflection_history) > 0, "에러 이력이 기록되지 않음"
    assert auto_reflector.reflection_history[0].success == False, "에러 상태가 올바르게 기록되지 않음"
    
    print("✅ 에러 처리 테스트 통과")

def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 자동 리플렉션 테스트 시작\n")
    
    try:
        test_reflection_config()
        test_auto_reflector_initialization()
        test_reflection_trigger()
        test_file_hash_calculation()
        test_statistics_tracking()
        test_notification_system()
        test_webhook_endpoints()
        test_error_handling()
        
        print("\n🎉 모든 자동 리플렉션 테스트 통과!")
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
