param(
    [string]$InputFile = "tasks.reflected.json",
    [string]$Strategy = "smart",
    [int]$MaxWorkers = 4,
    [string]$Output = "reports/parallel_execution_report.md",
    [switch]$Visualize,
    [switch]$Verbose
)

Write-Host "🚀 Parallel Task Execution System" -ForegroundColor Green
Write-Host "Input File: $InputFile" -ForegroundColor Cyan
Write-Host "Strategy: $Strategy" -ForegroundColor Cyan
Write-Host "Max Workers: $MaxWorkers" -ForegroundColor Cyan

$pythonScript = "tools\parallel_executor.py"
if (-not (Test-Path $pythonScript)) {
    Write-Error "Python script not found: $pythonScript"
    exit 1
}

if (-not (Test-Path $InputFile)) {
    Write-Error "Input file not found: $InputFile"
    exit 1
}

$outputDir = Split-Path $Output -Parent
if ($outputDir -and -not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Host "Output directory created: $outputDir" -ForegroundColor Yellow
}

$command = "python $pythonScript --input $InputFile --strategy $Strategy --max-workers $MaxWorkers"

if ($Output) {
    $command += " --output $Output"
}

if ($Visualize) {
    $command += " --visualize"
}

Write-Host "`nPre-execution Analysis:" -ForegroundColor Blue
Write-Host "- Python version: $(python --version)"
Write-Host "- Current directory: $(Get-Location)"
Write-Host "- Input file size: $((Get-Item $InputFile).Length) bytes"
Write-Host "- Available CPU cores: $([System.Environment]::ProcessorCount)"

Write-Host "`nTask Analysis:" -ForegroundColor Blue
$taskData = Get-Content $InputFile | ConvertFrom-Json
$taskCount = $taskData.tasks.Count
Write-Host "- Total tasks: $taskCount"

# 태스크 타입별 분석
$typeGroups = @{}
foreach ($task in $taskData.tasks) {
    $type = $task.type
    if (-not $typeGroups.ContainsKey($type)) {
        $typeGroups[$type] = @()
    }
    $typeGroups[$type] += $task
}

Write-Host "`nTask Type Distribution:" -ForegroundColor Blue
foreach ($type in $typeGroups.Keys) {
    $count = $typeGroups[$type].Count
    $avgComplexity = ($typeGroups[$type] | Measure-Object -Property complexity -Average).Average
    Write-Host "  • $type : $count tasks (avg complexity: $([math]::Round($avgComplexity, 2)))" -ForegroundColor Gray
}

# 병렬 처리 가능성 분석
$parallelTasks = $taskData.tasks | Where-Object { $_.type -in @('config', 'cli', 'doc', 'test') }
$sequentialTasks = $taskData.tasks | Where-Object { $_.type -in @('code', 'ide', 'mcp') }

Write-Host "`nParallel Processing Potential:" -ForegroundColor Blue
Write-Host "- Parallel-capable tasks: $($parallelTasks.Count)"
Write-Host "- Sequential-only tasks: $($sequentialTasks.Count)"
Write-Host "- Parallel efficiency estimate: $([math]::Round(($parallelTasks.Count / $taskCount) * 100, 1))%"

# 의존성 분석
$maxDependencies = ($taskData.tasks | Measure-Object -Property @{Expression={$_.deps.Count}} -Maximum).Maximum
$avgDependencies = ($taskData.tasks | Measure-Object -Property @{Expression={$_.deps.Count}} -Average).Average

Write-Host "`nDependency Analysis:" -ForegroundColor Blue
Write-Host "- Max dependencies: $maxDependencies"
Write-Host "- Average dependencies: $([math]::Round($avgDependencies, 2))"

# 성능 예측
$totalComplexity = ($taskData.tasks | Measure-Object -Property complexity -Sum).Sum
$estimatedSequentialTime = $totalComplexity * 2.5  # 복잡도당 2.5초 추정
$estimatedParallelTime = $estimatedSequentialTime / $MaxWorkers

Write-Host "`nPerformance Prediction:" -ForegroundColor Blue
Write-Host "- Estimated sequential time: $([math]::Round($estimatedSequentialTime, 1)) seconds"
Write-Host "- Estimated parallel time: $([math]::Round($estimatedParallelTime, 1)) seconds"
Write-Host "- Expected speedup: $([math]::Round($estimatedSequentialTime / $estimatedParallelTime, 1))x"

Write-Host "`nContinue with parallel execution? (Y/N)" -ForegroundColor Yellow
$confirm = Read-Host
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Execution cancelled." -ForegroundColor Red
    exit 0
}

Write-Host "`nStarting parallel task execution..." -ForegroundColor Green
$startTime = Get-Date

try {
    if ($Verbose) {
        Invoke-Expression $command
    } else {
        Invoke-Expression $command 2>&1 | Tee-Object -FilePath "parallel_execution.log"
    }
    
    $exitCode = $LASTEXITCODE
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host "`nParallel execution completed!" -ForegroundColor Green
    Write-Host "- Total execution time: $($duration.TotalSeconds.ToString('F2')) seconds"
    Write-Host "- Exit code: $exitCode"
    
    if ($exitCode -eq 0) {
        Write-Host "All tasks executed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Some tasks failed. (Exit code: $exitCode)" -ForegroundColor Yellow
    }
    
    # 실제 성능 분석
    $actualSpeedup = $estimatedSequentialTime / $duration.TotalSeconds
    $efficiency = ($actualSpeedup / $MaxWorkers) * 100
    
    Write-Host "`nActual Performance Analysis:" -ForegroundColor Blue
    Write-Host "- Actual speedup: $([math]::Round($actualSpeedup, 1))x"
    Write-Host "- Parallel efficiency: $([math]::Round($efficiency, 1))%"
    
    if ($efficiency > 80) {
        Write-Host "- Excellent parallel efficiency!" -ForegroundColor Green
    } elseif ($efficiency > 60) {
        Write-Host "- Good parallel efficiency." -ForegroundColor Yellow
    } else {
        Write-Host "- Parallel efficiency could be improved." -ForegroundColor Red
    }
    
    # 리포트 파일 확인
    if (Test-Path $Output) {
        Write-Host "`nReport generated: $Output" -ForegroundColor Cyan
        Write-Host "Report preview:" -ForegroundColor Blue
        Get-Content $Output -Head 30 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
    }
    
    # 로그 파일 확인
    if (Test-Path "parallel_execution.log") {
        Write-Host "`nExecution log: parallel_execution.log" -ForegroundColor Cyan
    }
    
    # 시각화 파일 확인
    if ($Visualize -and (Test-Path "dependency_graph.png")) {
        Write-Host "`nDependency graph: dependency_graph.png" -ForegroundColor Cyan
    }
    
} catch {
    Write-Error "Error during execution: $_"
    exit 1
}

Write-Host "`nNext steps:" -ForegroundColor Blue
Write-Host "1. Check report: Get-Content $Output"
Write-Host "2. Check log: Get-Content parallel_execution.log"
Write-Host "3. Optimize workers: .\tools\run_parallel.ps1 -MaxWorkers 6 -Strategy aggressive"
Write-Host "4. Visualize dependencies: .\tools\run_parallel.ps1 -Visualize"

Write-Host "`nParallel execution completed!" -ForegroundColor Green
