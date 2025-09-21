#!/usr/bin/env python3
"""
리플렉션 자동화 시스템
파일 변경 감지 및 자동 리플렉션

사용법:
    python tools/auto_reflector.py --watch --input tasks.json
    python tools/auto_reflector.py --daemon --config auto_reflect_config.yaml
    python tools/auto_reflector.py --trigger webhook --port 8080
"""

import json
import argparse
import subprocess
import sys
import time
import logging
import threading
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import yaml
from pathlib import Path
import schedule
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
from flask import Flask, request, jsonify

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_reflection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ReflectionMode(Enum):
    """리플렉션 모드"""
    WATCH = "watch"          # 파일 변경 감지
    SCHEDULED = "scheduled"   # 스케줄 기반
    WEBHOOK = "webhook"      # 웹훅 기반
    DAEMON = "daemon"        # 백그라운드 데몬

@dataclass
class ReflectionConfig:
    """리플렉션 설정"""
    input_file: str = "tasks.json"
    output_file: str = "tasks.reflected.json"
    report_file: str = "reports/tasks_reflect_report.md"
    watch_directories: List[str] = None
    watch_extensions: List[str] = None
    reflection_interval: int = 300  # 5분
    max_retries: int = 3
    retry_delay: int = 5
    webhook_port: int = 8080
    webhook_endpoints: List[str] = None
    notification_channels: List[str] = None
    
    def __post_init__(self):
        if self.watch_directories is None:
            self.watch_directories = [".", "docs", "src"]
        if self.watch_extensions is None:
            self.watch_extensions = [".json", ".md", ".yaml", ".yml"]
        if self.webhook_endpoints is None:
            self.webhook_endpoints = ["/reflect", "/update"]
        if self.notification_channels is None:
            self.notification_channels = ["console", "log"]

@dataclass
class ReflectionEvent:
    """리플렉션 이벤트"""
    timestamp: datetime
    event_type: str
    file_path: str
    file_hash: str
    success: bool
    duration: float
    error_message: Optional[str] = None
    triggered_by: str = "manual"

class FileChangeHandler(FileSystemEventHandler):
    """파일 변경 감지 핸들러"""
    
    def __init__(self, auto_reflector: 'AutoReflector'):
        self.auto_reflector = auto_reflector
        self.file_hashes = {}
        self.debounce_time = 2.0  # 2초 디바운스
        self.last_triggered = {}
    
    def should_trigger_reflection(self, file_path: str) -> bool:
        """리플렉션 트리거 여부 판단"""
        # 파일 확장자 확인
        if not any(file_path.endswith(ext) for ext in self.auto_reflector.config.watch_extensions):
            return False
        
        # 디바운스 확인
        now = time.time()
        if file_path in self.last_triggered:
            if now - self.last_triggered[file_path] < self.debounce_time:
                return False
        
        self.last_triggered[file_path] = now
        
        # 파일 해시 확인
        try:
            current_hash = self._calculate_file_hash(file_path)
            if file_path in self.file_hashes and self.file_hashes[file_path] == current_hash:
                return False  # 파일 내용이 변경되지 않음
            
            self.file_hashes[file_path] = current_hash
            return True
        except Exception as e:
            logger.warning(f"파일 해시 계산 실패 {file_path}: {e}")
            return True  # 안전을 위해 트리거
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def on_modified(self, event):
        """파일 수정 이벤트 처리"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        if self.should_trigger_reflection(file_path):
            logger.info(f"파일 변경 감지: {file_path}")
            self.auto_reflector.trigger_reflection(
                event_type="file_modified",
                file_path=file_path,
                triggered_by="file_watcher"
            )
    
    def on_created(self, event):
        """파일 생성 이벤트 처리"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        if self.should_trigger_reflection(file_path):
            logger.info(f"파일 생성 감지: {file_path}")
            self.auto_reflector.trigger_reflection(
                event_type="file_created",
                file_path=file_path,
                triggered_by="file_watcher"
            )

class AutoReflector:
    """자동 리플렉션 시스템"""
    
    def __init__(self, config: ReflectionConfig):
        self.config = config
        self.reflection_history: List[ReflectionEvent] = []
        self.observer = None
        self.is_running = False
        self.webhook_app = None
        self.webhook_thread = None
        
        # 리플렉션 통계
        self.total_reflections = 0
        self.successful_reflections = 0
        self.failed_reflections = 0
        self.last_reflection_time = None
        
    def start_watch_mode(self):
        """파일 감시 모드 시작"""
        logger.info(f"파일 감시 모드 시작: {self.config.watch_directories}")
        
        self.observer = Observer()
        handler = FileChangeHandler(self)
        
        for directory in self.config.watch_directories:
            if os.path.exists(directory):
                self.observer.schedule(handler, directory, recursive=True)
                logger.info(f"감시 디렉토리 추가: {directory}")
            else:
                logger.warning(f"감시 디렉토리가 존재하지 않음: {directory}")
        
        self.observer.start()
        self.is_running = True
        
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("파일 감시 모드 종료")
            self.stop()
    
    def start_scheduled_mode(self):
        """스케줄 모드 시작"""
        logger.info(f"스케줄 모드 시작: {self.config.reflection_interval}초 간격")
        
        # 스케줄 설정
        schedule.every(self.config.reflection_interval).seconds.do(
            self.trigger_reflection,
            event_type="scheduled",
            file_path="",
            triggered_by="scheduler"
        )
        
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("스케줄 모드 종료")
            self.stop()
    
    def start_webhook_mode(self):
        """웹훅 모드 시작"""
        logger.info(f"웹훅 모드 시작: 포트 {self.config.webhook_port}")
        
        self.webhook_app = Flask(__name__)
        self._setup_webhook_routes()
        
        self.webhook_thread = threading.Thread(
            target=self.webhook_app.run,
            kwargs={'host': '0.0.0.0', 'port': self.config.webhook_port, 'debug': False}
        )
        self.webhook_thread.daemon = True
        self.webhook_thread.start()
        
        self.is_running = True
        
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("웹훅 모드 종료")
            self.stop()
    
    def start_daemon_mode(self):
        """데몬 모드 시작"""
        logger.info("데몬 모드 시작")
        
        # 모든 모드 통합
        self._start_webhook_mode()
        self._start_scheduled_mode()
        
        self.is_running = True
        
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("데몬 모드 종료")
            self.stop()
    
    def _setup_webhook_routes(self):
        """웹훅 라우트 설정"""
        if self.webhook_app is None:
            self.webhook_app = Flask(__name__)
        
        @self.webhook_app.route('/reflect', methods=['POST'])
        def trigger_reflection_webhook():
            """리플렉션 트리거 웹훅"""
            try:
                data = request.get_json() or {}
                file_path = data.get('file_path', '')
                
                success = self.trigger_reflection(
                    event_type="webhook",
                    file_path=file_path,
                    triggered_by="webhook"
                )
                
                return jsonify({
                    'success': success,
                    'message': 'Reflection triggered successfully' if success else 'Reflection failed',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"웹훅 처리 오류: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.webhook_app.route('/status', methods=['GET'])
        def get_status():
            """상태 조회"""
            return jsonify({
                'status': 'running' if self.is_running else 'stopped',
                'total_reflections': self.total_reflections,
                'successful_reflections': self.successful_reflections,
                'failed_reflections': self.failed_reflections,
                'last_reflection_time': self.last_reflection_time.isoformat() if self.last_reflection_time else None,
                'success_rate': (self.successful_reflections / self.total_reflections * 100) if self.total_reflections > 0 else 0
            })
        
        @self.webhook_app.route('/history', methods=['GET'])
        def get_history():
            """리플렉션 이력 조회"""
            limit = request.args.get('limit', 10, type=int)
            recent_events = self.reflection_history[-limit:]
            
            return jsonify({
                'events': [
                    {
                        'timestamp': event.timestamp.isoformat(),
                        'event_type': event.event_type,
                        'file_path': event.file_path,
                        'success': event.success,
                        'duration': event.duration,
                        'error_message': event.error_message,
                        'triggered_by': event.triggered_by
                    }
                    for event in recent_events
                ]
            })
    
    def trigger_reflection(self, event_type: str, file_path: str, triggered_by: str) -> bool:
        """리플렉션 트리거"""
        logger.info(f"리플렉션 트리거: {event_type} - {file_path} (by {triggered_by})")
        
        start_time = time.time()
        success = False
        error_message = None
        
        try:
            # 리플렉션 실행
            success = self._execute_reflection()
            
            if success:
                self.successful_reflections += 1
                logger.info("리플렉션 성공")
            else:
                self.failed_reflections += 1
                error_message = "Reflection execution failed"
                logger.error("리플렉션 실패")
        
        except Exception as e:
            self.failed_reflections += 1
            error_message = str(e)
            logger.error(f"리플렉션 실행 중 오류: {e}")
        
        finally:
            self.total_reflections += 1
            duration = time.time() - start_time
            self.last_reflection_time = datetime.now()
            
            # 이벤트 기록
            event = ReflectionEvent(
                timestamp=datetime.now(),
                event_type=event_type,
                file_path=file_path,
                file_hash=self._calculate_file_hash(file_path) if file_path else "",
                success=success,
                duration=duration,
                error_message=error_message,
                triggered_by=triggered_by
            )
            
            self.reflection_history.append(event)
            
            # 알림 발송
            self._send_notifications(event)
        
        return success
    
    def _execute_reflection(self) -> bool:
        """리플렉션 실행"""
        try:
            # 출력 디렉토리 생성
            output_dir = os.path.dirname(self.config.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            report_dir = os.path.dirname(self.config.report_file)
            if report_dir and not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            # 리플렉션 명령어 실행
            command = [
                "python", "tools/tasks_reflect.py",
                "--in", self.config.input_file,
                "--out", self.config.output_file,
                "--report", self.config.report_file
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60  # 1분 타임아웃
            )
            
            if result.returncode == 0:
                logger.info("리플렉션 명령어 실행 성공")
                return True
            else:
                logger.error(f"리플렉션 명령어 실행 실패: {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            logger.error("리플렉션 실행 타임아웃")
            return False
        except Exception as e:
            logger.error(f"리플렉션 실행 중 예외: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _send_notifications(self, event: ReflectionEvent):
        """알림 발송"""
        for channel in self.config.notification_channels:
            try:
                if channel == "console":
                    self._send_console_notification(event)
                elif channel == "log":
                    self._send_log_notification(event)
                elif channel.startswith("webhook:"):
                    self._send_webhook_notification(event, channel)
                elif channel.startswith("email:"):
                    self._send_email_notification(event, channel)
            except Exception as e:
                logger.warning(f"알림 발송 실패 ({channel}): {e}")
    
    def _send_console_notification(self, event: ReflectionEvent):
        """콘솔 알림"""
        status = "✅ 성공" if event.success else "❌ 실패"
        print(f"[{event.timestamp.strftime('%H:%M:%S')}] {status} 리플렉션 ({event.duration:.2f}초)")
    
    def _send_log_notification(self, event: ReflectionEvent):
        """로그 알림"""
        status = "SUCCESS" if event.success else "FAILURE"
        logger.info(f"리플렉션 완료: {status} - {event.event_type} - {event.duration:.2f}초")
    
    def _send_webhook_notification(self, event: ReflectionEvent, channel: str):
        """웹훅 알림"""
        url = channel.replace("webhook:", "")
        data = {
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "success": event.success,
            "duration": event.duration,
            "file_path": event.file_path
        }
        
        try:
            response = requests.post(url, json=data, timeout=5)
            if response.status_code == 200:
                logger.info(f"웹훅 알림 발송 성공: {url}")
            else:
                logger.warning(f"웹훅 알림 발송 실패: {response.status_code}")
        except Exception as e:
            logger.warning(f"웹훅 알림 발송 오류: {e}")
    
    def _send_email_notification(self, event: ReflectionEvent, channel: str):
        """이메일 알림 (구현 예정)"""
        # TODO: 이메일 알림 구현
        pass
    
    def stop(self):
        """자동 리플렉션 중지"""
        logger.info("자동 리플렉션 중지 중...")
        
        self.is_running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        if self.webhook_thread and self.webhook_thread.is_alive():
            # Flask 앱 종료는 별도 처리 필요
            pass
        
        logger.info("자동 리플렉션 중지 완료")
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        return {
            "total_reflections": self.total_reflections,
            "successful_reflections": self.successful_reflections,
            "failed_reflections": self.failed_reflections,
            "success_rate": (self.successful_reflections / self.total_reflections * 100) if self.total_reflections > 0 else 0,
            "last_reflection_time": self.last_reflection_time.isoformat() if self.last_reflection_time else None,
            "average_duration": sum(event.duration for event in self.reflection_history) / len(self.reflection_history) if self.reflection_history else 0,
            "uptime": time.time() - (self.reflection_history[0].timestamp.timestamp() if self.reflection_history else time.time())
        }

def load_config(config_file: str) -> ReflectionConfig:
    """설정 파일 로드"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        return ReflectionConfig(**config_data)
    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")
        return ReflectionConfig()

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='자동 리플렉션 시스템')
    parser.add_argument('--mode', '-m', choices=['watch', 'scheduled', 'webhook', 'daemon'], 
                       default='watch', help='실행 모드')
    parser.add_argument('--input', '-i', default='tasks.json', help='입력 파일')
    parser.add_argument('--output', '-o', default='tasks.reflected.json', help='출력 파일')
    parser.add_argument('--report', '-r', default='reports/tasks_reflect_report.md', help='리포트 파일')
    parser.add_argument('--config', '-c', help='설정 파일')
    parser.add_argument('--interval', type=int, default=300, help='스케줄 간격 (초)')
    parser.add_argument('--port', type=int, default=8080, help='웹훅 포트')
    parser.add_argument('--watch-dirs', nargs='+', default=['.', 'docs', 'src'], help='감시 디렉토리')
    parser.add_argument('--watch-exts', nargs='+', default=['.json', '.md', '.yaml', '.yml'], help='감시 확장자')
    
    args = parser.parse_args()
    
    try:
        # 설정 로드
        if args.config:
            config = load_config(args.config)
        else:
            config = ReflectionConfig(
                input_file=args.input,
                output_file=args.output,
                report_file=args.report,
                reflection_interval=args.interval,
                webhook_port=args.port,
                watch_directories=args.watch_dirs,
                watch_extensions=args.watch_exts
            )
        
        # 자동 리플렉션 시스템 초기화
        auto_reflector = AutoReflector(config)
        
        # 모드별 실행
        mode = ReflectionMode(args.mode)
        
        if mode == ReflectionMode.WATCH:
            auto_reflector.start_watch_mode()
        elif mode == ReflectionMode.SCHEDULED:
            auto_reflector.start_scheduled_mode()
        elif mode == ReflectionMode.WEBHOOK:
            auto_reflector.start_webhook_mode()
        elif mode == ReflectionMode.DAEMON:
            auto_reflector.start_daemon_mode()
    
    except KeyboardInterrupt:
        logger.info("프로그램 종료")
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
