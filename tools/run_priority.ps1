# 우선순위 기반 실행 PowerShell 스크립트
# 복잡도 순위에 따른 단계별 Agent 실행
# UTF-8 BOM 인코딩으로 저장

param(
    [string]$InputFile = "tasks.reflected.json",
    [string]$Strategy = "dependency",
    [switch]$Parallel,
    [int]$MaxWorkers = 2,
    [string]$Output = "reports/priority_execution_report.md",
    [switch]$Verbose
)

# 스크립트 시작
Write-Host "🚀 우선순위 기반 태스크 실행 시작" -ForegroundColor Green
Write-Host "입력 파일: $InputFile" -ForegroundColor Cyan
Write-Host "실행 전략: $Strategy" -ForegroundColor Cyan

# Python 스크립트 경로 확인
$pythonScript = "tools\execute_priority.py"
if (-not (Test-Path $pythonScript)) {
    Write-Error "Python 스크립트를 찾을 수 없습니다: $pythonScript"
    exit 1
}

# 입력 파일 확인
if (-not (Test-Path $InputFile)) {
    Write-Error "입력 파일을 찾을 수 없습니다: $InputFile"
    exit 1
}

# 출력 디렉토리 생성
$outputDir = Split-Path $Output -Parent
if ($outputDir -and -not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Host "출력 디렉토리 생성: $outputDir" -ForegroundColor Yellow
}

# 명령어 구성
$command = "python $pythonScript --input $InputFile --strategy $Strategy"

if ($Parallel) {
    $command += " --parallel --max-workers $MaxWorkers"
    Write-Host "병렬 실행 모드 활성화 (워커 수: $MaxWorkers)" -ForegroundColor Yellow
}

if ($Output) {
    $command += " --output $Output"
}

# 실행 전 상태 확인
Write-Host "`n📊 실행 전 상태 확인:" -ForegroundColor Blue
Write-Host "- Python 버전: $(python --version)"
Write-Host "- 현재 디렉토리: $(Get-Location)"
Write-Host "- 입력 파일 크기: $((Get-Item $InputFile).Length) bytes"

# 태스크 파일 내용 미리보기
Write-Host "`n📋 태스크 미리보기:" -ForegroundColor Blue
$taskData = Get-Content $InputFile | ConvertFrom-Json
$taskCount = $taskData.tasks.Count
Write-Host "- 총 태스크 수: $taskCount"

foreach ($task in $taskData.tasks) {
    $complexity = $task.complexity
    $deps = $task.deps.Count
    Write-Host "  • $($task.id): 복잡도 $complexity, 의존성 $deps개" -ForegroundColor Gray
}

# 실행 확인
Write-Host "`n⚠️ 실행을 계속하시겠습니까? (Y/N)" -ForegroundColor Yellow
$confirm = Read-Host
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "실행이 취소되었습니다." -ForegroundColor Red
    exit 0
}

# 실행 시작
Write-Host "`n🔄 태스크 실행 시작..." -ForegroundColor Green
$startTime = Get-Date

try {
    # Python 스크립트 실행
    if ($Verbose) {
        Invoke-Expression $command
    } else {
        Invoke-Expression $command 2>&1 | Tee-Object -FilePath "priority_execution.log"
    }
    
    $exitCode = $LASTEXITCODE
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    # 실행 결과 처리
    Write-Host "`n📈 실행 완료!" -ForegroundColor Green
    Write-Host "- 실행 시간: $($duration.TotalSeconds.ToString('F2'))초"
    Write-Host "- 종료 코드: $exitCode"
    
    if ($exitCode -eq 0) {
        Write-Host "✅ 모든 태스크가 성공적으로 실행되었습니다!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ 일부 태스크가 실패했습니다. (종료 코드: $exitCode)" -ForegroundColor Yellow
    }
    
    # 리포트 파일 확인
    if (Test-Path $Output) {
        Write-Host "`n📄 리포트 생성 완료: $Output" -ForegroundColor Cyan
        Write-Host "리포트 미리보기:" -ForegroundColor Blue
        Get-Content $Output -Head 20 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
    }
    
    # 로그 파일 확인
    if (Test-Path "priority_execution.log") {
        Write-Host "`n📝 실행 로그: priority_execution.log" -ForegroundColor Cyan
    }
    
} catch {
    Write-Error "실행 중 오류 발생: $_"
    exit 1
}

# 다음 단계 제안
Write-Host "`n🔧 다음 단계 제안:" -ForegroundColor Blue
Write-Host "1. 리포트 확인: Get-Content $Output"
Write-Host "2. 로그 확인: Get-Content priority_execution.log"
Write-Host "3. 다음 우선순위 실행: .\tools\run_priority.ps1 -Strategy complexity -Parallel"

Write-Host "`n🎉 우선순위 기반 실행 완료!" -ForegroundColor Green
