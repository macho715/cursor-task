#!/usr/bin/env python3
"""
Watchdog 리플렉션 시스템 테스트
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

from watchdog_reflector import WatchdogReflector, WatchdogConfig

def create_test_files():
    """테스트용 파일 생성"""
    test_files = {
        "test_watch_tasks.json": {
            "tasks": [
                {
                    "id": "watchdog:test1",
                    "title": "Watchdog Test 1",
                    "type": "code",
                    "deps": [],
                    "complexity": 1.0
                },
                {
                    "id": "watchdog:test2",
                    "title": "Watchdog Test 2", 
                    "type": "config",
                    "deps": ["watchdog:test1"],
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

def test_watchdog_config():
    """Watchdog 설정 테스트"""
    print("🧪 Watchdog 설정 테스트")
    
    config = WatchdogConfig(
        watch_files=["test_watch_tasks.json"],
        watch_directories=["."],
        debounce_time=1.0,
        hash_check=True
    )
    
    print(f"감시 파일: {config.watch_files}")
    print(f"감시 디렉토리: {config.watch_directories}")
    print(f"디바운스 시간: {config.debounce_time}초")
    print(f"해시 확인: {config.hash_check}")
    
    assert "test_watch_tasks.json" in config.watch_files, "감시 파일 설정 오류"
    assert config.debounce_time == 1.0, "디바운스 시간 설정 오류"
    assert config.hash_check == True, "해시 확인 설정 오류"
    
    print("✅ Watchdog 설정 테스트 통과")

def test_file_hash_calculation():
    """파일 해시 계산 테스트"""
    print("\n🧪 파일 해시 계산 테스트")
    
    # 테스트 파일 생성
    test_content = {"test": "hash_calculation", "timestamp": datetime.now().isoformat()}
    test_file = "test_hash_watchdog.json"
    
    try:
        with open(test_file, 'w') as f:
            json.dump(test_content, f)
        
        config = WatchdogConfig()
        from watchdog_reflector import AdvancedFileHandler
        
        handler = AdvancedFileHandler(config)
        hash1 = handler._calculate_file_hash(test_file)
        
        # 파일 수정
        test_content["modified"] = True
        with open(test_file, 'w') as f:
            json.dump(test_content, f)
        
        hash2 = handler._calculate_file_hash(test_file)
        
        print(f"원본 파일 해시: {hash1}")
        print(f"수정된 파일 해시: {hash2}")
        print(f"해시 변경 여부: {hash1 != hash2}")
        
        assert hash1 != hash2, "파일 수정 후 해시가 변경되지 않음"
        assert len(hash1) == 64, "SHA-256 해시 길이 오류"
        assert len(hash2) == 64, "SHA-256 해시 길이 오류"
    
    finally:
        cleanup_test_files([test_file])
    
    print("✅ 파일 해시 계산 테스트 통과")

def test_file_filtering():
    """파일 필터링 테스트"""
    print("\n🧪 파일 필터링 테스트")
    
    config = WatchdogConfig(
        include_extensions=[".json", ".md"],
        exclude_patterns=["*.tmp", "*.log"],
        max_file_size=1000
    )
    
    from watchdog_reflector import AdvancedFileHandler
    handler = AdvancedFileHandler(config)
    
    # 테스트 파일들 생성
    test_files = {
        "test.json": '{"test": "data"}',
        "test.md": "# Test",
        "test.tmp": "temporary data",
        "test.log": "log data",
        "test.txt": "text data"
    }
    
    created_files = []
    try:
        for filename, content in test_files.items():
            with open(filename, 'w') as f:
                f.write(content)
            created_files.append(filename)
        
        # 파일 필터링 테스트
        print("파일 필터링 결과:")
        for filename in test_files.keys():
            should_process = handler.should_process_file(filename)
            print(f"  • {filename}: {'✅ 처리' if should_process else '❌ 제외'}")
            
            if filename.endswith('.json') or filename.endswith('.md'):
                assert should_process, f"{filename}이 처리되어야 함"
            else:
                assert not should_process, f"{filename}이 제외되어야 함"
    
    finally:
        cleanup_test_files(created_files)
    
    print("✅ 파일 필터링 테스트 통과")

def test_debounce_mechanism():
    """디바운스 메커니즘 테스트"""
    print("\n🧪 디바운스 메커니즘 테스트")
    
    config = WatchdogConfig(debounce_time=2.0)
    from watchdog_reflector import AdvancedFileHandler
    
    handler = AdvancedFileHandler(config)
    
    # 테스트 파일 생성
    test_file = "test_debounce.json"
    try:
        with open(test_file, 'w') as f:
            json.dump({"test": "debounce"}, f)
        
        # 첫 번째 트리거
        should_trigger1 = handler.should_trigger_reflection(test_file)
        print(f"첫 번째 트리거: {should_trigger1}")
        assert should_trigger1, "첫 번째 트리거는 허용되어야 함"
        
        # 즉시 두 번째 트리거 (디바운스 시간 내)
        should_trigger2 = handler.should_trigger_reflection(test_file)
        print(f"즉시 두 번째 트리거: {should_trigger2}")
        assert not should_trigger2, "디바운스 시간 내 트리거는 차단되어야 함"
        
        # 디바운스 시간 경과 후 트리거
        time.sleep(2.1)
        with open(test_file, 'w') as f:
            json.dump({'test': 'debounce', 'updated_at': datetime.now().isoformat()}, f)

        should_trigger3 = handler.should_trigger_reflection(test_file)
        print(f"디바운스 후 트리거: {should_trigger3}")
        assert should_trigger3, "디바운스 시간 경과 후 트리거는 허용되어야 함"
    
    finally:
        cleanup_test_files([test_file])
    
    print("✅ 디바운스 메커니즘 테스트 통과")

def test_statistics_tracking():
    """통계 추적 테스트"""
    print("\n🧪 통계 추적 테스트")
    
    config = WatchdogConfig()
    from watchdog_reflector import AdvancedFileHandler
    
    handler = AdvancedFileHandler(config)
    
    # 초기 통계
    stats1 = handler.get_statistics()
    print(f"초기 통계: {stats1}")
    
    # 가짜 이벤트 시뮬레이션
    handler.total_events = 10
    handler.processed_events = 8
    handler.skipped_events = 2
    handler.failed_reflections = 1
    
    # 통계 확인
    stats2 = handler.get_statistics()
    print(f"업데이트된 통계: {stats2}")
    
    assert stats2["total_events"] == 10, "총 이벤트 수 오류"
    assert stats2["processed_events"] == 8, "처리된 이벤트 수 오류"
    assert stats2["skipped_events"] == 2, "건너뛴 이벤트 수 오류"
    assert stats2["failed_reflections"] == 1, "실패한 리플렉션 수 오류"
    assert stats2["success_rate"] == 80.0, "성공률 계산 오류"
    
    print("✅ 통계 추적 테스트 통과")

def test_reflection_command():
    """리플렉션 명령어 테스트"""
    print("\n🧪 리플렉션 명령어 테스트")
    
    # 테스트 파일 생성
    test_files = create_test_files()
    
    try:
        config = WatchdogConfig(
            watch_files=["test_watch_tasks.json"],
            reflect_command=[
                "python", "tools/tasks_reflect.py",
                "--in", "test_watch_tasks.json",
                "--out", "test_watch_tasks.reflected.json",
                "--report", "test_report.md"
            ]
        )
        
        from watchdog_reflector import AdvancedFileHandler
        handler = AdvancedFileHandler(config)
        
        # 리플렉션 트리거 시뮬레이션
        print("리플렉션 트리거 시뮬레이션...")
        handler._trigger_reflection("test_watch_tasks.json", "test")
        
        # 결과 확인
        if os.path.exists("test_watch_tasks.reflected.json"):
            print("✅ 출력 파일 생성 확인")
        
        if os.path.exists("test_report.md"):
            print("✅ 리포트 파일 생성 확인")
        
        # 통계 확인
        stats = handler.get_statistics()
        print(f"리플렉션 통계: {stats}")
        
    finally:
        cleanup_test_files(test_files)
        cleanup_test_files(["test_watch_tasks.reflected.json", "test_report.md"])
    
    print("✅ 리플렉션 명령어 테스트 통과")

def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 Watchdog 리플렉션 테스트 시작\n")
    
    try:
        test_watchdog_config()
        test_file_hash_calculation()
        test_file_filtering()
        test_debounce_mechanism()
        test_statistics_tracking()
        test_reflection_command()
        
        print("\n🎉 모든 Watchdog 리플렉션 테스트 통과!")
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
