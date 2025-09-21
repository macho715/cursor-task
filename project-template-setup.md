# 🚀 **다른 프로젝트에 Hybrid AI Development Workflow 적용하기**

## 📋 **적용 전 체크리스트**

### **필수 요구사항**
- [ ] Python 3.9+ 설치됨
- [ ] Git 저장소 초기화됨
- [ ] Cursor IDE 또는 VSCode 설치됨
- [ ] GitHub 계정 및 저장소 준비됨

### **선택 요구사항**
- [ ] Graphviz 설치 (시각화용)
- [ ] PowerShell 또는 Bash 터미널
- [ ] Node.js (경량 MCP용)

---

## 🎯 **1단계: 템플릿 다운로드 및 설정**

### **방법 1: Git Clone (권장)**
```bash
# 기존 프로젝트에서 템플릿 복사
git clone https://github.com/macho715/cursor-task.git your-project-name
cd your-project-name

# 원격 저장소 변경
git remote remove origin
git remote add origin https://github.com/your-username/your-project-name.git
```

### **방법 2: 수동 복사**
```bash
# 핵심 파일들만 복사
mkdir your-new-project
cd your-new-project

# 필수 디렉토리 생성
mkdir docs tools reports .github/workflows .cursor/rules
```

---

## 📝 **2단계: PRD 작성**

### **새 프로젝트용 PRD 템플릿**
```markdown
# PRD (Product Requirements Doc) - Your Project Name

```yml
meta:
  id: prj-your-project
  owner: "Your Name <your-email@example.com>"
  repo: "your-project-repo"
  due: "2025-12-31"
  risk_tolerance: "medium"   # low|med|high
  incoterms: "N/A"

objectives:
  - "프로젝트 목표 1"
  - "프로젝트 목표 2"
  - "프로젝트 목표 3"

deliverables:
  - "핵심 기능 1"
  - "핵심 기능 2"
  - "핵심 기능 3"

constraints:
  - "기술적 제약사항"
  - "시간적 제약사항"
  - "리소스 제약사항"

modules:
  - id: setup
    title: "프로젝트 초기 설정"
    value: "high"
    acceptance:
      - "환경 설정 완료"
      - "의존성 설치 완료"

  - id: core-features
    title: "핵심 기능 개발"
    value: "high"
    acceptance:
      - "주요 기능 구현"
      - "테스트 통과"

work_items:
  - id: setup:env
    title: "개발 환경 설정"
    module: "setup"
    type: "config"
    deps: []
    complexity: 1.0
    acceptance:
      - "Python 가상환경 설정"
      - "필수 패키지 설치"

  - id: setup:deps
    title: "의존성 관리 설정"
    module: "setup"
    type: "config"
    deps: ["setup:env"]
    complexity: 1.2
    acceptance:
      - "requirements.txt 생성"
      - "패키지 버전 고정"

  - id: core:main
    title: "메인 기능 구현"
    module: "core-features"
    type: "code"
    deps: ["setup:deps"]
    complexity: 2.0
    acceptance:
      - "핵심 로직 구현"
      - "단위 테스트 작성"

quality_gates:
  - "모든 테스트 통과"
  - "코드 커버리지 ≥ 80%"
  - "린팅 오류 없음"
```
```

---

## ⚙️ **3단계: 프로젝트별 설정 커스터마이징**

### **프로젝트 타입별 설정 적용**
```bash
# 웹 애플리케이션 프로젝트
python tools/config_manager.py --project-type web

# 마이크로서비스 프로젝트
python tools/config_manager.py --project-type microservices

# 스타트업 팀 설정
python tools/config_manager.py --team-size startup

# 엔터프라이즈 팀 설정
python tools/config_manager.py --team-size enterprise
```

### **수동 설정 파일 편집**
```bash
# 프로젝트별 설정 파일 생성
cp tools/watchdog_config.yaml tools/watchdog_config_myproject.yaml
cp tools/priority_config.yaml tools/priority_config_myproject.yaml

# 설정 파일 편집
vim tools/watchdog_config_myproject.yaml
vim tools/priority_config_myproject.yaml
```

---

## 🔧 **4단계: 핵심 도구 설정**

### **태스크 리플렉션 설정**
```bash
# PRD에서 태스크 생성
python tools/tasks_reflect.py --in docs/PRD.md --out tasks.json --report reports/tasks_reflect_report.md

# 또는 기존 tasks.json 수정
vim tasks.json
```

### **워크플로우 설정**
```bash
# Git 훅 설치
python tools/setup_git_hooks.py --install

# GitHub Actions 설정
cp .github/workflows/reflect.yml .github/workflows/myproject-reflect.yml
vim .github/workflows/myproject-reflect.yml
```

---

## 🚀 **5단계: 첫 실행 및 테스트**

### **기본 워크플로우 테스트**
```bash
# 1. 태스크 리플렉션
python tools/tasks_reflect.py --in tasks.json --out tasks.reflected.json --report reports/tasks_reflect_report.md

# 2. 우선순위 실행 (시뮬레이션)
python tools/demo_priority.py

# 3. 실제 실행
python tools/execute_priority.py --input tasks.reflected.json --strategy dependency

# 4. 시각화 생성
python tools/dag_visualizer.py --input tasks.reflected.json
```

### **고급 기능 테스트**
```bash
# 병렬 처리 테스트
python tools/demo_parallel.py

# 자동 리플렉션 테스트
python tools/demo_auto_reflect.py

# Conventional Commits 테스트
python tools/test_conventional_commits.py
```

---

## 📊 **6단계: 모니터링 및 최적화**

### **성능 모니터링**
```bash
# 실행 로그 확인
tail -f priority_execution.log
tail -f parallel_execution.log
tail -f auto_reflection.log

# 리포트 생성
python tools/dag_visualizer.py --input tasks.reflected.json
```

### **지속적 개선**
```bash
# 설정 최적화
python tools/config_manager.py --interactive

# 새로운 기능 추가
# tools/ 디렉토리에 커스텀 스크립트 추가
```

---

## 🎯 **프로젝트별 적용 예시**

### **웹 애플리케이션 프로젝트**
```bash
# React/Next.js 프로젝트
python tools/config_manager.py --project-type web --team-size startup

# 감시 대상 파일 설정
echo "src/**/*.tsx" >> tools/watchdog_config.yaml
echo "src/**/*.ts" >> tools/watchdog_config.yaml
echo "package.json" >> tools/watchdog_config.yaml
```

### **마이크로서비스 프로젝트**
```bash
# Docker/Kubernetes 프로젝트
python tools/config_manager.py --project-type microservices --team-size enterprise

# 서비스별 설정
echo "services/**/*.py" >> tools/watchdog_config.yaml
echo "k8s/**/*.yaml" >> tools/watchdog_config.yaml
echo "docker-compose.yml" >> tools/watchdog_config.yaml
```

### **데이터 사이언스 프로젝트**
```bash
# Jupyter/ML 프로젝트
python tools/config_manager.py --project-type custom

# 감시 대상 설정
echo "notebooks/**/*.ipynb" >> tools/watchdog_config.yaml
echo "data/**/*.csv" >> tools/watchdog_config.yaml
echo "models/**/*.pkl" >> tools/watchdog_config.yaml
```

---

## 🔄 **7단계: CI/CD 통합**

### **GitHub Actions 설정**
```yaml
# .github/workflows/myproject.yml
name: My Project Workflow

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'docs/**'
      - 'tasks.json'
      - 'src/**'
  pull_request:
    branches: [ main ]

jobs:
  reflect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install watchdog pyyaml graphviz pytest
      - name: Run reflection
        run: |
          python tools/tasks_reflect.py --in tasks.json --out tasks.reflected.json --report reports/tasks_reflect_report.md
      - name: Generate visualization
        run: |
          python tools/dag_visualizer.py --input tasks.reflected.json
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: workflow-artifacts
          path: |
            tasks.reflected.json
            reports/
            tasks_dag.svg
```

---

## ✅ **적용 완료 체크리스트**

### **기본 설정**
- [ ] PRD 작성 완료
- [ ] tasks.json 생성 완료
- [ ] 프로젝트별 설정 적용 완료
- [ ] Git 훅 설치 완료

### **기능 테스트**
- [ ] 태스크 리플렉션 테스트 통과
- [ ] 우선순위 실행 테스트 통과
- [ ] 병렬 처리 테스트 통과
- [ ] 시각화 생성 테스트 통과

### **CI/CD 설정**
- [ ] GitHub Actions 워크플로우 설정
- [ ] Conventional Commits 설정
- [ ] 자동 릴리즈 설정
- [ ] 모니터링 설정

---

## 🎉 **성공적인 적용을 위한 팁**

### **1. 점진적 적용**
- 먼저 기본 워크플로우부터 적용
- 성공 후 고급 기능 추가
- 팀 피드백을 통한 지속적 개선

### **2. 팀 교육**
- 팀원들에게 새로운 워크플로우 교육
- 문서화 및 가이드 제공
- 정기적인 워크플로우 리뷰

### **3. 모니터링**
- 성능 지표 정기적 확인
- 오류 로그 모니터링
- 사용자 피드백 수집

---

**🚀 이제 다른 프로젝트에서도 Hybrid AI Development Workflow를 활용할 수 있습니다!**
