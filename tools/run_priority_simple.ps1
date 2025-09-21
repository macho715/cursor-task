param(
    [string]$InputFile = "tasks.reflected.json",
    [string]$Strategy = "dependency",
    [switch]$Parallel,
    [int]$MaxWorkers = 2,
    [string]$Output = "reports/priority_execution_report.md"
)

Write-Host "Priority-based Task Execution" -ForegroundColor Green
Write-Host "Input File: $InputFile" -ForegroundColor Cyan
Write-Host "Strategy: $Strategy" -ForegroundColor Cyan

$pythonScript = "tools\execute_priority.py"
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

$command = "python $pythonScript --input $InputFile --strategy $Strategy"

if ($Parallel) {
    $command += " --parallel --max-workers $MaxWorkers"
    Write-Host "Parallel execution enabled (workers: $MaxWorkers)" -ForegroundColor Yellow
}

if ($Output) {
    $command += " --output $Output"
}

Write-Host "`nPre-execution Status:" -ForegroundColor Blue
Write-Host "- Python version: $(python --version)"
Write-Host "- Current directory: $(Get-Location)"
Write-Host "- Input file size: $((Get-Item $InputFile).Length) bytes"

Write-Host "`nTask Preview:" -ForegroundColor Blue
$taskData = Get-Content $InputFile | ConvertFrom-Json
$taskCount = $taskData.tasks.Count
Write-Host "- Total tasks: $taskCount"

foreach ($task in $taskData.tasks) {
    $complexity = $task.complexity
    $deps = $task.deps.Count
    Write-Host "  • $($task.id): complexity $complexity, dependencies $deps" -ForegroundColor Gray
}

Write-Host "`nContinue with execution? (Y/N)" -ForegroundColor Yellow
$confirm = Read-Host
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Execution cancelled." -ForegroundColor Red
    exit 0
}

Write-Host "`nStarting task execution..." -ForegroundColor Green
$startTime = Get-Date

try {
    Invoke-Expression $command
    $exitCode = $LASTEXITCODE
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host "`nExecution completed!" -ForegroundColor Green
    Write-Host "- Execution time: $($duration.TotalSeconds.ToString('F2')) seconds"
    Write-Host "- Exit code: $exitCode"
    
    if ($exitCode -eq 0) {
        Write-Host "All tasks executed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Some tasks failed. (Exit code: $exitCode)" -ForegroundColor Yellow
    }
    
    if (Test-Path $Output) {
        Write-Host "`nReport generated: $Output" -ForegroundColor Cyan
        Write-Host "Report preview:" -ForegroundColor Blue
        Get-Content $Output -Head 20 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
    }
    
    if (Test-Path "priority_execution.log") {
        Write-Host "`nExecution log: priority_execution.log" -ForegroundColor Cyan
    }
    
} catch {
    Write-Error "Error during execution: $_"
    exit 1
}

Write-Host "`nNext steps:" -ForegroundColor Blue
Write-Host "1. Check report: Get-Content $Output"
Write-Host "2. Check log: Get-Content priority_execution.log"
Write-Host "3. Next priority execution: .\tools\run_priority_simple.ps1 -Strategy complexity -Parallel"

Write-Host "`nPriority-based execution completed!" -ForegroundColor Green
