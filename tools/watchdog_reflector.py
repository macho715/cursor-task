#!/usr/bin/env python3
"""
Watchdog 기반 고급 파일 감지 및 트리거 시스템
외부 레퍼런스: https://python-watchdog.readthedocs.io/en/stable/

사용법:
    python tools/watchdog_reflector.py --watch docs/PRD.md tasks.json
    python tools/watchdog_reflector.py --config watchdog_config.yaml
"""

import json
import argparse
import subprocess
import sys
import time
import logging
import hashlib
import pathlib
from datetime import datetime
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
import yaml

# Watchdog imports
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileMovedEvent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('watchdog_reflection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class WatchdogConfig:
    """Watchdog 설정"""
    watch_files: List[str] = field(default_factory=lambda: ["docs/PRD.md", "tasks.json"])
    watch_directories: List[str] = field(default_factory=lambda: ["docs", "."])
    debounce_time: float = 2.0  # 2초 디바운스
    hash_check: bool = True     # 해시 기반 변경 감지
    recursive: bool = True      # 재귀적 디렉토리 감시
    exclude_patterns: List[str] = field(default_factory=lambda: ["*.tmp", "*.log", ".git/*"])
    include_extensions: List[str] = field(default_factory=lambda: [".md", ".json", ".yaml", ".yml"])
    
    # 리플렉션 설정
    reflect_command: List[str] = field(default_factory=lambda: [
        "python", "tools/tasks_reflect.py",
        "--in", "tasks.json",
        "--out", "tasks.reflected.json", 
        "--report", "reports/tasks_reflect_report.md"
    ])
    
    # 성능 설정
    max_file_size: int = 10485760  # 10MB
    batch_processing: bool = False
    parallel_reflection: bool = False

class AdvancedFileHandler(FileSystemEventHandler):
    """고급 파일 변경 핸들러"""
    
    def __init__(self, config: WatchdogConfig):
        super().__init__()
        self.config = config
        self.file_hashes: Dict[str, str] = {}
        self.last_triggered: Dict[str, float] = {}
        self.pending_changes: Set[str] = set()
        self.reflection_in_progress = False
        
        # 성능 통계
        self.total_events = 0
        self.processed_events = 0
        self.skipped_events = 0
        self.failed_reflections = 0
        
    def should_process_file(self, file_path: str) -> bool:
        """파일 처리 여부 판단"""
        path = pathlib.Path(file_path)
        
        # 파일 존재 확인
        if not path.exists() or not path.is_file():
            return False
        
        # 확장자 확인
        if path.suffix.lower() not in self.config.include_extensions:
            return False
        
        # 제외 패턴 확인
        for pattern in self.config.exclude_patterns:
            if path.match(pattern):
                return False
        
        # 파일 크기 확인
        try:
            if path.stat().st_size > self.config.max_file_size:
                logger.warning(f"파일 크기 초과: {file_path}")
                return False
        except OSError:
            return False
        
        return True
    
    def should_trigger_reflection(self, file_path: str) -> bool:
        """리플렉션 트리거 여부 판단"""
        if not self.should_process_file(file_path):
            return False
        
        # 디바운스 확인
        now = time.time()
        if file_path in self.last_triggered:
            if now - self.last_triggered[file_path] < self.config.debounce_time:
                self.skipped_events += 1
                return False
        
        # 해시 기반 변경 확인
        if self.config.hash_check:
            try:
                current_hash = self._calculate_file_hash(file_path)
                if file_path in self.file_hashes and self.file_hashes[file_path] == current_hash:
                    self.skipped_events += 1
                    return False
                
                self.file_hashes[file_path] = current_hash
            except Exception as e:
                logger.warning(f"파일 해시 계산 실패 {file_path}: {e}")
        
        self.last_triggered[file_path] = now
        return True
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산 (SHA-256)"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"해시 계산 오류 {file_path}: {e}")
            return ""
    
    def _trigger_reflection(self, file_path: str, event_type: str):
        """리플렉션 트리거"""
        if self.reflection_in_progress:
            logger.info(f"리플렉션 진행 중, 대기열에 추가: {file_path}")
            self.pending_changes.add(file_path)
            return
        
        logger.info(f"리플렉션 트리거: {event_type} - {file_path}")
        
        try:
            self.reflection_in_progress = True
            start_time = time.time()
            
            # 리플렉션 명령어 실행
            result = subprocess.run(
                self.config.reflect_command,
                capture_output=True,
                text=True,
                timeout=60  # 1분 타임아웃
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"리플렉션 성공 ({duration:.2f}초)")
                self.processed_events += 1
                
                # 대기열의 다른 변경사항 처리
                if self.pending_changes:
                    logger.info(f"대기열 처리: {len(self.pending_changes)}개 파일")
                    self.pending_changes.clear()
                    
            else:
                logger.error(f"리플렉션 실패: {result.stderr}")
                self.failed_reflections += 1
                
        except subprocess.TimeoutExpired:
            logger.error("리플렉션 실행 타임아웃")
            self.failed_reflections += 1
        except Exception as e:
            logger.error(f"리플렉션 실행 중 오류: {e}")
            self.failed_reflections += 1
        finally:
            self.reflection_in_progress = False
    
    def on_modified(self, event):
        """파일 수정 이벤트"""
        if event.is_directory:
            return
        
        self.total_events += 1
        file_path = event.src_path
        
        if self.should_trigger_reflection(file_path):
            self._trigger_reflection(file_path, "file_modified")
    
    def on_created(self, event):
        """파일 생성 이벤트"""
        if event.is_directory:
            return
        
        self.total_events += 1
        file_path = event.src_path
        
        if self.should_trigger_reflection(file_path):
            self._trigger_reflection(file_path, "file_created")
    
    def on_moved(self, event):
        """파일 이동 이벤트"""
        if event.is_directory:
            return
        
        self.total_events += 1
        file_path = event.dest_path
        
        if self.should_trigger_reflection(file_path):
            self._trigger_reflection(file_path, "file_moved")
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        success_rate = (self.processed_events / self.total_events * 100) if self.total_events > 0 else 0
        
        return {
            "total_events": self.total_events,
            "processed_events": self.processed_events,
            "skipped_events": self.skipped_events,
            "failed_reflections": self.failed_reflections,
            "success_rate": success_rate,
            "pending_changes": len(self.pending_changes),
            "reflection_in_progress": self.reflection_in_progress
        }

class WatchdogReflector:
    """Watchdog 기반 리플렉션 시스템"""
    
    def __init__(self, config: WatchdogConfig):
        self.config = config
        self.observer = None
        self.handler = None
        self.is_running = False
        
    def start(self):
        """Watchdog 감시 시작"""
        logger.info("Watchdog 리플렉션 시스템 시작")
        logger.info(f"감시 파일: {self.config.watch_files}")
        logger.info(f"감시 디렉토리: {self.config.watch_directories}")
        logger.info(f"디바운스 시간: {self.config.debounce_time}초")
        
        self.handler = AdvancedFileHandler(self.config)
        self.observer = Observer()
        
        # 디렉토리 감시 설정
        for directory in self.config.watch_directories:
            if pathlib.Path(directory).exists():
                self.observer.schedule(
                    self.handler, 
                    directory, 
                    recursive=self.config.recursive
                )
                logger.info(f"감시 디렉토리 추가: {directory} (재귀: {self.config.recursive})")
            else:
                logger.warning(f"감시 디렉토리가 존재하지 않음: {directory}")
        
        # 개별 파일 감시 설정
        for file_path in self.config.watch_files:
            file_obj = pathlib.Path(file_path)
            if file_obj.exists():
                # 파일의 부모 디렉토리를 감시
                parent_dir = file_obj.parent
                if str(parent_dir) not in self.config.watch_directories:
                    self.observer.schedule(self.handler, str(parent_dir), recursive=False)
                    logger.info(f"파일 감시 추가: {file_path}")
            else:
                logger.warning(f"감시 파일이 존재하지 않음: {file_path}")
        
        self.observer.start()
        self.is_running = True
        
        logger.info("Watchdog 감시 시작 완료")
        
        try:
            while self.is_running:
                time.sleep(1)
                
                # 주기적 통계 출력 (1분마다)
                if int(time.time()) % 60 == 0:
                    stats = self.handler.get_statistics()
                    logger.info(f"통계: {stats['total_events']}개 이벤트, "
                              f"{stats['processed_events']}개 처리, "
                              f"성공률 {stats['success_rate']:.1f}%")
                
        except KeyboardInterrupt:
            logger.info("사용자 중단 신호 수신")
            self.stop()
    
    def stop(self):
        """Watchdog 감시 중지"""
        logger.info("Watchdog 리플렉션 시스템 중지 중...")
        
        self.is_running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # 최종 통계 출력
        if self.handler:
            stats = self.handler.get_statistics()
            logger.info(f"최종 통계: {stats}")
        
        logger.info("Watchdog 리플렉션 시스템 중지 완료")

def load_config(config_file: str) -> WatchdogConfig:
    """설정 파일 로드"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        return WatchdogConfig(**config_data)
    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")
        return WatchdogConfig()

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Watchdog 기반 리플렉션 시스템')
    parser.add_argument('--watch', '-w', nargs='+', help='감시할 파일/디렉토리')
    parser.add_argument('--config', '-c', help='설정 파일')
    parser.add_argument('--debounce', type=float, default=2.0, help='디바운스 시간 (초)')
    parser.add_argument('--no-hash', action='store_true', help='해시 기반 변경 감지 비활성화')
    parser.add_argument('--no-recursive', action='store_true', help='재귀적 감시 비활성화')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 로깅')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 설정 로드
        if args.config:
            config = load_config(args.config)
        else:
            config = WatchdogConfig(
                watch_files=args.watch or ["docs/PRD.md", "tasks.json"],
                debounce_time=args.debounce,
                hash_check=not args.no_hash,
                recursive=not args.no_recursive
            )
        
        # Watchdog 리플렉션 시스템 시작
        reflector = WatchdogReflector(config)
        reflector.start()
    
    except KeyboardInterrupt:
        logger.info("프로그램 종료")
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
