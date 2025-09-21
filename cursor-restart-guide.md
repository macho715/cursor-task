# Cursor IDE 재시작 가이드

## MCP 설정 적용을 위한 재시작 방법

### 방법 1: 개발자 리로드 (권장)
1. **Ctrl+Shift+P** 키 조합
2. `Developer: Reload Window` 입력 후 실행
3. 창이 자동으로 리로드됩니다

### 방법 2: 완전 종료 후 재시작
1. **Ctrl+Q** 또는 `File` → `Exit`
2. Cursor IDE 완전 종료
3. 다시 Cursor IDE 실행

### 방법 3: 명령줄 재시작
```powershell
# 모든 Cursor 프로세스 종료
taskkill /F /IM Cursor.exe

# Cursor IDE 재시작
Start-Process "Cursor.exe"
```

## 재시작 후 확인사항

### MCP 서버 로딩 확인
1. **Ctrl+Shift+P** → `MCP: Show Server Status`
2. Shrimp MCP 서버 상태 확인
3. 연결 상태 및 기능 테스트

### 설정 적용 확인
- `~/.cursor/mcp.json` 설정이 올바르게 로드되었는지 확인
- Shrimp MCP 서버가 정상적으로 시작되었는지 확인
- 의존성 분석 및 복잡도 관리 기능 테스트

## 문제 해결

### MCP 서버가 로드되지 않는 경우
1. `C:\Tools\shrimp\shrimp.exe` 경로 확인
2. Shrimp MCP 설치 상태 확인
3. 환경 변수 설정 확인

### 권한 문제 발생 시
1. 관리자 권한으로 Cursor IDE 실행
2. Windows Defender 예외 설정 확인
3. 방화벽 설정 확인

## 다음 단계
재시작 완료 후:
1. `/test-shrimp-mcp` 명령으로 기능 테스트
2. `/validate-mcp-connection` 명령으로 연결 확인
3. `/test-workflow-integration` 명령으로 워크플로우 검증
