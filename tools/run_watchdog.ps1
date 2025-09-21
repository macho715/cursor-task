param(
    [string[]]$WatchFiles = @("docs/PRD.md", "tasks.json"),
    [string]$ConfigFile = "tools/watchdog_config.yaml",
    [double]$Debounce = 2.0,
    [switch]$NoHash,
    [switch]$NoRecursive,
    [switch]$Verbose,
    [switch]$DryRun
)

Write-Host "🐕 Watchdog Reflection System" -ForegroundColor Green
Write-Host "Watch Files: $($WatchFiles -join ', ')" -ForegroundColor Cyan

$pythonScript = "tools\watchdog_reflector.py"
if (-not (Test-Path $pythonScript)) {
    Write-Error "Python script not found: $pythonScript"
    exit 1
}

# 종속성 확인
Write-Host "`nDependency Check:" -ForegroundColor Blue
$dependencies = @("watchdog", "pyyaml")

foreach ($dep in $dependencies) {
    try {
        $result = python -c "import $dep; print('OK')" 2>$null
        if ($result -eq "OK") {
            Write-Host "  ✅ $dep : Available" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $dep : Not available" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ $dep : Not available" -ForegroundColor Red
    }
}

# 설정 파일 확인
if ($ConfigFile -and (Test-Path $ConfigFile)) {
    Write-Host "`nUsing config file: $ConfigFile" -ForegroundColor Yellow
} else {
    Write-Host "`nUsing command line parameters" -ForegroundColor Yellow
}

# 감시 대상 확인
Write-Host "`nWatch Target Analysis:" -ForegroundColor Blue
foreach ($file in $WatchFiles) {
    if (Test-Path $file) {
        $fileSize = (Get-Item $file).Length
        Write-Host "  ✅ $file : $fileSize bytes" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file : Not found" -ForegroundColor Red
    }
}

# 디렉토리 감시 확인
$watchDirs = @(".", "docs", "src", "tools")
foreach ($dir in $watchDirs) {
    if (Test-Path $dir) {
        $fileCount = (Get-ChildItem -Path $dir -Recurse -File -Include "*.md", "*.json", "*.yaml", "*.yml" | Measure-Object).Count
        Write-Host "  📁 $dir : $fileCount matching files" -ForegroundColor Gray
    } else {
        Write-Host "  ❌ $dir : Directory not found" -ForegroundColor Red
    }
}

# 성능 예측
Write-Host "`nPerformance Prediction:" -ForegroundColor Blue
Write-Host "- Debounce time: $Debounce seconds"
Write-Host "- Hash checking: $(if ($NoHash) { 'Disabled' } else { 'Enabled' })"
Write-Host "- Recursive watching: $(if ($NoRecursive) { 'Disabled' } else { 'Enabled' })"

if (-not $NoHash) {
    Write-Host "- SHA-256 hash verification enabled" -ForegroundColor Green
} else {
    Write-Host "- Hash verification disabled (faster but less accurate)" -ForegroundColor Yellow
}

# 명령어 구성
$command = "python $pythonScript"

if ($ConfigFile -and (Test-Path $ConfigFile)) {
    $command += " --config $ConfigFile"
} else {
    $watchFilesStr = $WatchFiles -join " "
    $command += " --watch $watchFilesStr"
    $command += " --debounce $Debounce"
    
    if ($NoHash) {
        $command += " --no-hash"
    }
    
    if ($NoRecursive) {
        $command += " --no-recursive"
    }
}

if ($Verbose) {
    $command += " --verbose"
}

if ($DryRun) {
    Write-Host "`n🔍 Dry Run Mode - Command Preview:" -ForegroundColor Yellow
    Write-Host $command
    Write-Host "`nDry run completed. No actual execution performed."
    exit 0
}

Write-Host "`nStart watchdog reflection system? (Y/N)" -ForegroundColor Yellow
$confirm = Read-Host
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Watchdog reflection cancelled." -ForegroundColor Red
    exit 0
}

Write-Host "`nStarting watchdog reflection system..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host "`nCommand: $command" -ForegroundColor Gray

$startTime = Get-Date

try {
    if ($Verbose) {
        Invoke-Expression $command
    } else {
        Invoke-Expression $command 2>&1 | Tee-Object -FilePath "watchdog_reflection.log"
    }
    
    $exitCode = $LASTEXITCODE
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host "`nWatchdog reflection completed!" -ForegroundColor Green
    Write-Host "- Total runtime: $($duration.TotalMinutes.ToString('F1')) minutes"
    Write-Host "- Exit code: $exitCode"
    
    if ($exitCode -eq 0) {
        Write-Host "Watchdog reflection system stopped normally." -ForegroundColor Green
    } else {
        Write-Host "Watchdog reflection system stopped with errors. (Exit code: $exitCode)" -ForegroundColor Yellow
    }
    
} catch {
    Write-Error "Error during watchdog reflection: $_"
    exit 1
}

# 실행 결과 확인
Write-Host "`nResults:" -ForegroundColor Blue

if (Test-Path "tasks.reflected.json") {
    $outputSize = (Get-Item "tasks.reflected.json").Length
    Write-Host "✅ Output file: tasks.reflected.json ($outputSize bytes)" -ForegroundColor Green
}

if (Test-Path "reports/tasks_reflect_report.md") {
    Write-Host "✅ Report file: reports/tasks_reflect_report.md" -ForegroundColor Green
}

if (Test-Path "watchdog_reflection.log") {
    Write-Host "✅ Execution log: watchdog_reflection.log" -ForegroundColor Green
}

# 로그 파일 미리보기
if (Test-Path "watchdog_reflection.log") {
    Write-Host "`nLog Preview (last 10 lines):" -ForegroundColor Blue
    Get-Content "watchdog_reflection.log" -Tail 10 | ForEach-Object { 
        Write-Host "  $_" -ForegroundColor Gray 
    }
}

Write-Host "`nNext steps:" -ForegroundColor Blue
Write-Host "1. Check output: Get-Content tasks.reflected.json"
Write-Host "2. Check report: Get-Content reports/tasks_reflect_report.md"
Write-Host "3. Check log: Get-Content watchdog_reflection.log"
Write-Host "4. Restart: .\tools\run_watchdog.ps1 -WatchFiles docs/PRD.md,tasks.json"

Write-Host "`nWatchdog reflection system completed!" -ForegroundColor Green
