# 자동 리플렉션 시스템

파일 변경 감지 및 자동 리플렉션을 위한 완전한 시스템입니다.

## 📁 파일 구조

```
tools/
├── auto_reflector.py           # 메인 자동 리플렉션 엔진
├── auto_reflect_config.yaml    # 설정 파일
├── run_auto_reflect.ps1       # PowerShell 실행 스크립트
├── test_auto_reflect.py       # 테스트 스크립트
├── demo_auto_reflect.py       # 데모 스크립트
└── AUTO_REFLECTION_README.md  # 이 파일
```

## 🚀 빠른 시작

### 1. 데모 실행 (시뮬레이션)
```bash
# 자동 리플렉션 데모 실행
python tools/demo_auto_reflect.py

# 테스트 실행
python tools/test_auto_reflect.py
```

### 2. 실제 자동 리플렉션 실행
```powershell
# PowerShell 스크립트 실행 (권장)
.\tools\run_auto_reflect.ps1

# 또는 직접 Python 실행
python tools/auto_reflector.py --mode watch --input tasks.json
```

## 🎯 실행 모드

### 1. Watch Mode (파일 감시)
파일 변경을 실시간으로 감지하여 자동 리플렉션

```bash
python tools/auto_reflector.py --mode watch --input tasks.json
```

**특징:**
- 실시간 파일 변경 감지
- 해시 기반 변경 확인
- 디바운스 처리 (2초)
- 재귀적 디렉토리 감시

### 2. Scheduled Mode (스케줄)
정기적으로 리플렉션 실행

```bash
python tools/auto_reflector.py --mode scheduled --interval 300
```

**특징:**
- 설정 가능한 간격 (초 단위)
- 백그라운드 실행
- 안정적인 주기적 실행

### 3. Webhook Mode (웹훅)
HTTP 웹훅을 통한 리플렉션 트리거

```bash
python tools/auto_reflector.py --mode webhook --port 8080
```

**엔드포인트:**
- `POST /reflect` - 리플렉션 트리거
- `GET /status` - 상태 조회
- `GET /history` - 실행 이력 조회

### 4. Daemon Mode (데몬)
모든 모드를 통합한 백그라운드 서비스

```bash
python tools/auto_reflector.py --mode daemon --config auto_reflect_config.yaml
```

**특징:**
- 파일 감시 + 스케줄 + 웹훅 통합
- 백그라운드 실행
- 완전한 자동화

## ⚙️ 설정 파일

`auto_reflect_config.yaml`에서 다음을 설정할 수 있습니다:

```yaml
# 기본 파일 경로
input_file: "tasks.json"
output_file: "tasks.reflected.json"
report_file: "reports/tasks_reflect_report.md"

# 파일 감시 설정
watch_directories: [".", "docs", "src", "tools"]
watch_extensions: [".json", ".md", ".yaml", ".yml", ".py"]

# 스케줄 설정
reflection_interval: 300  # 5분

# 웹훅 설정
webhook_port: 8080
webhook_endpoints: ["/reflect", "/update", "/trigger"]

# 알림 설정
notification_channels: ["console", "log"]
```

## 📊 모니터링 및 통계

### 실시간 통계
```bash
# 웹훅 모드에서 상태 확인
curl http://localhost:8080/status
```

### 실행 이력 조회
```bash
# 최근 10개 실행 이력
curl http://localhost:8080/history?limit=10
```

### 통계 정보
- 총 리플렉션 수
- 성공/실패 횟수
- 성공률
- 평균 실행 시간
- 최근 실행 시간

## 🔔 알림 시스템

### 콘솔 알림
실시간 콘솔 출력으로 리플렉션 상태 확인

### 로그 알림
`auto_reflection.log` 파일에 상세 로그 기록

### 웹훅 알림 (확장 가능)
```yaml
notification_channels:
  - "webhook:http://monitoring.example.com/alerts"
```

### 이메일 알림 (확장 가능)
```yaml
notification_channels:
  - "email:admin@example.com"
```

## 🛠️ 고급 사용법

### 1. 설정 파일 사용
```bash
python tools/auto_reflector.py --config auto_reflect_config.yaml
```

### 2. 커스텀 감시 설정
```bash
python tools/auto_reflector.py --mode watch \
  --watch-dirs . docs src \
  --watch-exts .json .md .yaml
```

### 3. 웹훅 트리거
```bash
# 리플렉션 트리거
curl -X POST http://localhost:8080/reflect \
  -H "Content-Type: application/json" \
  -d '{"file_path": "tasks.json"}'
```

### 4. PowerShell 실행
```powershell
# 기본 실행
.\tools\run_auto_reflect.ps1

# 커스텀 설정
.\tools\run_auto_reflect.ps1 -Mode webhook -Port 8080 -Verbose

# 드라이 런 (테스트)
.\tools\run_auto_reflect.ps1 -Mode watch -DryRun
```

## 🔍 문제 해결

### 1. 파일 감시가 작동하지 않음
```bash
# 권한 확인
ls -la tasks.json

# 디렉토리 확인
ls -la docs/ src/ tools/
```

### 2. 웹훅이 응답하지 않음
```bash
# 포트 사용 확인
netstat -an | grep 8080

# 방화벽 확인
sudo ufw status
```

### 3. 리플렉션 실패
```bash
# 로그 확인
tail -f auto_reflection.log

# 수동 리플렉션 테스트
python tools/tasks_reflect.py --in tasks.json --out test.reflected.json
```

### 4. 의존성 문제
```bash
# 필요한 패키지 설치
pip install watchdog schedule flask pyyaml requests

# 패키지 확인
python -c "import watchdog, schedule, flask, yaml, requests; print('All packages available')"
```

## 📈 성능 최적화

### 1. 감시 디렉토리 최적화
```yaml
watch_directories:
  - "."        # 필요한 디렉토리만
  - "docs"     # 불필요한 디렉토리 제외
```

### 2. 감시 확장자 최적화
```yaml
watch_extensions:
  - ".json"    # 필요한 확장자만
  - ".md"      # 불필요한 확장자 제외
```

### 3. 스케줄 간격 조정
```yaml
reflection_interval: 600  # 10분으로 증가 (리소스 절약)
```

### 4. 디바운스 시간 조정
```yaml
advanced:
  file_watching:
    debounce_time: 5.0  # 5초로 증가 (빈번한 트리거 방지)
```

## 🔒 보안 설정

### 1. 허용된 디렉토리 제한
```yaml
advanced:
  security:
    allowed_directories:
      - "."
      - "docs"
      - "src"
```

### 2. 차단된 확장자 설정
```yaml
advanced:
  security:
    blocked_extensions:
      - ".exe"
      - ".bat"
      - ".sh"
```

### 3. 최대 파일 크기 제한
```yaml
advanced:
  security:
    max_file_size: 10485760  # 10MB
```

## 📚 예제

### 기본 자동 리플렉션
```bash
# 1. 설정 파일 생성
cp tools/auto_reflect_config.yaml my_config.yaml

# 2. 자동 리플렉션 시작
python tools/auto_reflector.py --config my_config.yaml

# 3. 파일 수정하여 테스트
echo '{"test": "data"}' >> tasks.json
```

### 웹훅 통합
```bash
# 1. 웹훅 모드 시작
python tools/auto_reflector.py --mode webhook --port 8080

# 2. 다른 터미널에서 트리거
curl -X POST http://localhost:8080/reflect

# 3. 상태 확인
curl http://localhost:8080/status
```

### CI/CD 통합
```yaml
# .github/workflows/auto-reflect.yml
name: Auto Reflection
on: [push, pull_request]
jobs:
  auto-reflect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Trigger Reflection
        run: |
          curl -X POST http://localhost:8080/reflect \
            -H "Content-Type: application/json" \
            -d '{"file_path": "tasks.json"}'
```

## 🎯 다음 단계

1. **경량 Tasks MCP**: Node.js 기반 Cursor IDE 통합
2. **실시간 모니터링**: 태스크 진행 상황 실시간 추적
3. **머신러닝 최적화**: 성능 데이터 기반 자동 최적화
4. **클라우드 통합**: AWS/Azure 클라우드 서비스 연동

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. `auto_reflection.log` 파일
2. `reports/` 디렉토리의 리포트 파일
3. 설정 파일 형식 (`auto_reflect_config.yaml`)
4. 필요한 Python 패키지 설치

---

**자동 리플렉션으로 효율적이고 지능적인 태스크 관리를 시작하세요!** 🚀
