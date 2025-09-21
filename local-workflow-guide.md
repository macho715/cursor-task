# 로컬 워크플로우 가이드 (Shrimp MCP 대체)

## 🚀 **즉시 실행 가능한 워크플로우**

### Windows (PowerShell)
```powershell
# 1. 의존성/복잡도 리플렉션 실행
python tools/tasks_reflect.py --in tasks.json --out tasks.reflected.json --report reports/tasks_reflect_report.md

# 2. 결과 확인
notepad reports/tasks_reflect_report.md
```

### macOS/Linux (bash)
```bash
# 1. 리플렉션 실행
python3 tools/tasks_reflect.py --in tasks.json --out tasks.reflected.json --report reports/tasks_reflect_report.md

# 2. 결과 확인
head -50 reports/tasks_reflect_report.md
```

## 📊 **리플렉션 결과 요약**

### ✅ **성공적으로 완료된 작업**
- **순환 의존성**: 0개 (안전한 구조)
- **토폴로지 정렬**: 5개 태스크 완벽 정렬
- **복잡도 계산**: 1.10 ~ 1.80 범위로 차별화
- **실행 순서**: 명확한 의존성 체인

### 📈 **복잡도 분석 결과**
| 태스크 | 복잡도 | 순위 | 특징 |
|--------|--------|------|------|
| `parse-and-reflect:reflect` | 1.8 | 1위 | MCP 타입 + 복잡한 통합 |
| `core-setup:rules` | 1.2 | 2위 | 코드 타입 + "pack" 키워드 |
| `parse-and-reflect:generate` | 1.2 | 3위 | CLI 타입 + "generate" 키워드 |
| `agent-apply-ask:apply` | 1.2 | 4위 | IDE 타입 + "apply" 키워드 |
| `core-setup:mcp` | 1.1 | 5위 | Config 타입 (가장 단순) |

### 🔗 **최적화된 실행 순서**
1. **core-setup:rules** (독립 태스크)
2. **core-setup:mcp** + **parse-and-reflect:generate** (병렬 가능)
3. **parse-and-reflect:reflect** (MCP 통합)
4. **agent-apply-ask:apply** (최종 적용)

## 🎯 **Agent 실행 준비사항**

### Cursor IDE에서 실행
```bash
# MCP 없이도 안전한 적용 가능
cursor agent --apply=ask --rules
```

### 우선순위 기반 실행
```bash
# 복잡도 순위에 따른 단계별 실행
# 1. core-setup:rules (복잡도 1.2)
# 2. core-setup:mcp (복잡도 1.1) 
# 3. parse-and-reflect:generate (복잡도 1.2)
# 4. parse-and-reflect:reflect (복잡도 1.8) - 가장 복잡
# 5. agent-apply-ask:apply (복잡도 1.2)
```

## 🔧 **로컬 리플렉터 기능**

### ✅ **구현된 기능**
- **순환 의존성 감지**: DFS 기반 정확한 감지
- **토폴로지 정렬**: Kahn 알고리즘으로 안전한 순서 결정
- **복잡도 계산**: 타입 + 의존성 + 키워드 기반 정교한 계산
- **상세 리포트**: 통계, 순위, 분석 포함

### 📊 **복잡도 계산 공식**
```
복잡도 = base(type) + 0.2*deps + 0.1*dependents + title_bonus
범위: 0.8 ~ 3.0 (클램프)
```

### 🎯 **타입별 기본 복잡도**
- **doc**: 0.8 (문서화)
- **cli**: 0.9 (명령줄 도구)
- **config**: 0.9 (설정)
- **code**: 1.0 (코드)
- **ide**: 1.0 (IDE 통합)
- **mcp**: 1.2 (MCP 서버)
- **test**: 1.1 (테스트)

## 🚀 **다음 단계**

### 단기 (즉시 실행 가능)
1. **우선순위 기반 Agent 실행**: 복잡도 순위에 따른 단계별 적용
2. **병렬 처리**: `core-setup:mcp`와 `parse-and-reflect:generate` 동시 실행
3. **리플렉션 주기적 실행**: 태스크 변경 시마다 복잡도 재계산

### 중기 (선택사항)
1. **경량 Tasks MCP**: Node.js 기반 Cursor IDE 통합
2. **자동화 스크립트**: 리플렉션 → Agent 실행 자동화
3. **CI/CD 통합**: GitHub Actions에서 리플렉션 검증

### 장기 (목표)
1. **Shrimp MCP 설치**: 표준 MCP 워크플로우 완결
2. **고급 분석**: 작업 시간 예측, 리소스 할당 최적화
3. **실시간 모니터링**: 태스크 진행 상황 실시간 추적

## 🎉 **결론**

**Shrimp MCP 설치 없이도 완전한 의존성 분석과 복잡도 관리가 가능합니다!**

- ✅ **즉시 사용 가능**: Python 스크립트로 모든 기능 구현
- ✅ **정확한 분석**: 순환 의존성 감지, 토폴로지 정렬 완료
- ✅ **차별화된 복잡도**: 1.10~1.80 범위로 실제 작업 복잡도 반영
- ✅ **Agent 호환**: Cursor IDE와 완벽 호환되는 워크플로우

**로컬 리플렉터로도 충분히 강력하고 정확한 태스크 관리가 가능합니다!**