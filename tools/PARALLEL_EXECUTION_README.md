# 병렬 처리 실행 시스템

의존성 그래프 분석을 통한 최적화된 병렬 태스크 실행 시스템입니다.

## 📁 파일 구조

```
tools/
├── parallel_executor.py          # 메인 병렬 실행 엔진
├── parallel_config.yaml          # 병렬 처리 설정
├── run_parallel.ps1             # PowerShell 실행 스크립트
├── test_parallel.py             # 테스트 스크립트
├── demo_parallel.py             # 데모 스크립트
└── PARALLEL_EXECUTION_README.md # 이 파일
```

## 🚀 빠른 시작

### 1. 데모 실행 (시뮬레이션)
```bash
# 병렬 처리 데모 실행
python tools/demo_parallel.py

# 테스트 실행
python tools/test_parallel.py
```

### 2. 실제 병렬 실행
```powershell
# PowerShell 스크립트 실행 (권장)
.\tools\run_parallel.ps1

# 또는 직접 Python 실행
python tools/parallel_executor.py --input tasks.reflected.json --strategy smart
```

## 🎯 병렬 처리 전략

### 1. Smart Strategy (기본값)
- 지능적 병렬 처리
- 태스크 타입과 복잡도를 고려한 최적화
- 자동 워커 할당 조정

```bash
python tools/parallel_executor.py --input tasks.reflected.json --strategy smart --max-workers 4
```

### 2. Conservative Strategy
- 안전한 병렬 처리
- 최대 2개 워커 사용
- 높은 안정성 우선

```bash
python tools/parallel_executor.py --input tasks.reflected.json --strategy conservative
```

### 3. Aggressive Strategy
- 공격적인 병렬 처리
- 최대 8개 워커 사용
- 최대 성능 우선

```bash
python tools/parallel_executor.py --input tasks.reflected.json --strategy aggressive --max-workers 8
```

### 4. Dependency Strategy
- 의존성 기반 병렬 처리
- 의존성 레벨별 그룹화
- 순차 실행 폴백 지원

```bash
python tools/parallel_executor.py --input tasks.reflected.json --strategy dependency
```

## ⚡ 고급 기능

### 1. 의존성 그래프 분석
```bash
# 의존성 그래프 시각화
python tools/parallel_executor.py --input tasks.reflected.json --visualize
```

### 2. 리소스 관리
- CPU 코어별 워커 할당
- 메모리 사용량 모니터링
- 디스크 I/O 최적화

### 3. 성능 모니터링
- 실시간 실행 상태 추적
- 워커별 성능 통계
- 병렬 효율성 분석

## 📊 성능 지표

### 병렬 처리 효율성
- **속도 향상**: 순차 대비 병렬 실행 시간 단축
- **효율성**: 이론적 최대 성능 대비 실제 성능
- **워커 활용도**: 워커별 태스크 처리 분배

### 최적화 기준
- **80% 이상**: 우수한 병렬 효율성
- **60-80%**: 양호한 병렬 효율성
- **60% 미만**: 병렬 효율성 개선 필요

## 🔧 설정 파일

`parallel_config.yaml`에서 다음을 설정할 수 있습니다:

```yaml
parallel_execution:
  default_strategy: "smart"
  max_workers: 4
  timeout_per_task: 300

resource_management:
  limits:
    cpu_cores: 8
    memory_gb: 16
    disk_gb: 100
```

## 📈 실행 결과

### 1. 콘솔 출력
- 실시간 병렬 실행 상태
- 워커별 태스크 처리 현황
- 성능 통계 및 분석

### 2. 로그 파일
- `parallel_execution.log`: 상세 실행 로그
- 워커별 실행 이력
- 에러 및 예외 정보

### 3. 리포트 파일
- `reports/parallel_execution_report.md`: 실행 결과 리포트
- 성능 분석 및 개선 제안
- 워커별 통계

### 4. 시각화 파일
- `dependency_graph.png`: 의존성 그래프
- 태스크 간 관계 시각화
- 병렬 그룹 식별

## 🛠️ 고급 사용법

### 1. 워커 수 최적화
```bash
# 워커 수별 성능 테스트
python tools/parallel_executor.py --input tasks.reflected.json --max-workers 2
python tools/parallel_executor.py --input tasks.reflected.json --max-workers 4
python tools/parallel_executor.py --input tasks.reflected.json --max-workers 6
python tools/parallel_executor.py --input tasks.reflected.json --max-workers 8
```

### 2. 전략별 성능 비교
```bash
# 전략별 실행 시간 비교
python tools/parallel_executor.py --input tasks.reflected.json --strategy conservative
python tools/parallel_executor.py --input tasks.reflected.json --strategy smart
python tools/parallel_executor.py --input tasks.reflected.json --strategy aggressive
```

### 3. 리소스 모니터링
```bash
# 리소스 사용량 모니터링과 함께 실행
python tools/parallel_executor.py --input tasks.reflected.json --strategy smart --max-workers 4
```

## 🔍 문제 해결

### 1. 낮은 병렬 효율성
```bash
# 워커 수 조정
python tools/parallel_executor.py --input tasks.reflected.json --max-workers 2

# 전략 변경
python tools/parallel_executor.py --input tasks.reflected.json --strategy conservative
```

### 2. 태스크 실행 실패
```bash
# 로그 확인
cat parallel_execution.log

# 의존성 그래프 확인
python tools/parallel_executor.py --input tasks.reflected.json --visualize
```

### 3. 리소스 부족
```bash
# 워커 수 감소
python tools/parallel_executor.py --input tasks.reflected.json --max-workers 2

# 보수적 전략 사용
python tools/parallel_executor.py --input tasks.reflected.json --strategy conservative
```

## 📚 예제

### 기본 병렬 실행
```bash
# 1. 태스크 리플렉션
python tools/tasks_reflect.py --in tasks.json --out tasks.reflected.json

# 2. 병렬 실행
python tools/parallel_executor.py --input tasks.reflected.json --strategy smart

# 3. 결과 확인
cat reports/parallel_execution_report.md
```

### 고급 병렬 실행
```bash
# 1. 의존성 그래프 시각화
python tools/parallel_executor.py --input tasks.reflected.json --visualize

# 2. 공격적 병렬 실행
python tools/parallel_executor.py \
  --input tasks.reflected.json \
  --strategy aggressive \
  --max-workers 6 \
  --output reports/aggressive_execution_report.md

# 3. 성능 분석
python tools/demo_parallel.py
```

### PowerShell 실행
```powershell
# 기본 실행
.\tools\run_parallel.ps1

# 고급 실행
.\tools\run_parallel.ps1 -Strategy aggressive -MaxWorkers 6 -Visualize

# 성능 분석
.\tools\run_parallel.ps1 -Strategy smart -MaxWorkers 4 -Verbose
```

## 🎯 다음 단계

1. **리플렉션 자동화**: 파일 변경 감지 및 자동 리플렉션
2. **실시간 모니터링**: 태스크 진행 상황 실시간 추적
3. **CI/CD 통합**: GitHub Actions에서 자동 병렬 실행
4. **머신러닝 최적화**: 성능 데이터 기반 자동 최적화

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. `parallel_execution.log` 파일
2. `reports/parallel_execution_report.md` 리포트
3. `dependency_graph.png` 시각화
4. 태스크 파일 형식 (`tasks.reflected.json`)

---

**병렬 처리로 효율적이고 빠른 태스크 실행을 경험하세요!** 🚀
