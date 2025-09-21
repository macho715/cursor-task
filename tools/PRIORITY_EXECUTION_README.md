# 우선순위 기반 실행 시스템

복잡도 순위에 따른 단계별 Agent 실행을 위한 완전한 시스템입니다.

## 📁 파일 구조

```
tools/
├── execute_priority.py          # 메인 실행 엔진
├── priority_config.yaml         # 설정 파일
├── run_priority.ps1            # PowerShell 실행 스크립트
├── test_priority.py            # 테스트 스크립트
├── demo_priority.py            # 데모 스크립트
└── PRIORITY_EXECUTION_README.md # 이 파일
```

## 🚀 빠른 시작

### 1. 데모 실행 (시뮬레이션)
```bash
# Python 데모 실행
python tools/demo_priority.py

# 테스트 실행
python tools/test_priority.py
```

### 2. 실제 실행
```powershell
# PowerShell 스크립트 실행 (권장)
.\tools\run_priority.ps1

# 또는 직접 Python 실행
python tools/execute_priority.py --input tasks.reflected.json
```

## 📋 실행 전략

### 1. 의존성 전략 (기본값)
- 토폴로지 정렬 순서대로 실행
- 의존성이 완료된 태스크부터 실행
- 안전하고 예측 가능한 실행 순서

```bash
python tools/execute_priority.py --input tasks.reflected.json --strategy dependency
```

### 2. 복잡도 전략
- 복잡도가 높은 태스크부터 실행
- 의존성 고려하여 정렬
- 복잡한 작업을 먼저 처리

```bash
python tools/execute_priority.py --input tasks.reflected.json --strategy complexity
```

### 3. 효율성 전략
- 병렬 실행 가능한 태스크 우선
- 복잡도와 병렬성을 고려한 최적화
- 전체 실행 시간 단축

```bash
python tools/execute_priority.py --input tasks.reflected.json --strategy efficiency
```

## ⚡ 병렬 실행

병렬 실행으로 실행 시간을 단축할 수 있습니다:

```bash
# 병렬 실행 (최대 2개 워커)
python tools/execute_priority.py --input tasks.reflected.json --parallel --max-workers 2

# PowerShell에서 병렬 실행
.\tools\run_priority.ps1 -Parallel -MaxWorkers 2
```

## 📊 실행 결과

### 1. 콘솔 출력
- 실시간 실행 상태 표시
- 태스크별 성공/실패 상태
- 실행 시간 및 통계

### 2. 로그 파일
- `priority_execution.log`: 상세 실행 로그
- 타임스탬프와 함께 모든 실행 기록

### 3. 리포트 파일
- `reports/priority_execution_report.md`: 실행 결과 리포트
- 성공률, 실행 시간, 실패 분석 포함

## 🔧 설정 파일

`priority_config.yaml`에서 다음을 설정할 수 있습니다:

```yaml
execution:
  default_strategy: "dependency"
  parallel:
    enabled: true
    max_workers: 2
    timeout_per_task: 300

task_types:
  code:
    command_template: "cursor agent --apply=ask --rules \"{title}\""
    can_parallel: false
    priority: 1
```

## 📈 성능 지표

### 실행 시간 최적화
- **순차 실행**: 안전하지만 느림
- **병렬 실행**: 40% 시간 단축 가능
- **효율성 전략**: 병렬 가능 태스크 우선 처리

### 성공률 개선
- **의존성 검증**: 실행 전 의존성 확인
- **타임아웃 설정**: 5분 타임아웃으로 무한 대기 방지
- **재시도 로직**: 실패 시 자동 재시도 (설정 가능)

## 🛠️ 고급 사용법

### 1. 사용자 정의 명령어
```python
# priority_config.yaml에서 태스크 타입별 명령어 설정
task_types:
  custom:
    command_template: "your-custom-command \"{title}\""
    can_parallel: true
    priority: 1
```

### 2. 복잡도 임계값 설정
```yaml
complexity_thresholds:
  low: 1.0
  medium: 1.5
  high: 2.0
  critical: 2.5
```

### 3. 모듈별 우선순위
```yaml
module_priority:
  core-setup: 1
  parse-and-reflect: 2
  agent-apply-ask: 3
```

## 🔍 문제 해결

### 1. 태스크 실행 실패
```bash
# 로그 확인
cat priority_execution.log

# 특정 태스크만 실행
python tools/execute_priority.py --input tasks.reflected.json --strategy dependency
```

### 2. 의존성 문제
```bash
# 태스크 파일 검증
python tools/tasks_reflect.py --validate tasks.json

# 순환 의존성 확인
python tools/tasks_reflect.py --check-cycles tasks.json
```

### 3. 성능 문제
```bash
# 병렬 실행으로 최적화
python tools/execute_priority.py --input tasks.reflected.json --parallel --max-workers 4

# 효율성 전략 사용
python tools/execute_priority.py --input tasks.reflected.json --strategy efficiency
```

## 📚 예제

### 기본 실행 예제
```bash
# 1. 태스크 리플렉션
python tools/tasks_reflect.py --in tasks.json --out tasks.reflected.json

# 2. 우선순위 기반 실행
python tools/execute_priority.py --input tasks.reflected.json

# 3. 결과 확인
cat reports/priority_execution_report.md
```

### 고급 실행 예제
```bash
# 1. 복잡도 전략으로 병렬 실행
python tools/execute_priority.py \
  --input tasks.reflected.json \
  --strategy complexity \
  --parallel \
  --max-workers 3 \
  --output reports/complexity_execution_report.md

# 2. PowerShell에서 실행
.\tools\run_priority.ps1 -Strategy complexity -Parallel -MaxWorkers 3 -Verbose
```

## 🎯 다음 단계

1. **병렬 처리 구현**: 더 많은 태스크를 동시에 실행
2. **자동화 워크플로우**: 리플렉션 → 실행 → 검증 자동화
3. **CI/CD 통합**: GitHub Actions에서 자동 실행
4. **실시간 모니터링**: 실행 상태 실시간 추적

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. `priority_execution.log` 파일
2. `reports/priority_execution_report.md` 리포트
3. 태스크 파일 형식 (`tasks.reflected.json`)
4. Python 환경 및 의존성

---

**우선순위 기반 실행으로 효율적이고 안전한 태스크 관리를 시작하세요!** 🚀
