param(
    [string]$Mode = "watch",
    [string]$InputFile = "tasks.json",
    [string]$OutputFile = "tasks.reflected.json",
    [string]$ReportFile = "reports/tasks_reflect_report.md",
    [string]$ConfigFile = "tools/auto_reflect_config.yaml",
    [int]$Interval = 300,
    [int]$Port = 8080,
    [string[]]$WatchDirs = @(".", "docs", "src"),
    [string[]]$WatchExts = @(".json", ".md", ".yaml", ".yml"),
    [switch]$Verbose,
    [switch]$DryRun
)

Write-Host "🔄 Auto Reflection System" -ForegroundColor Green
Write-Host "Mode: $Mode" -ForegroundColor Cyan
Write-Host "Input File: $InputFile" -ForegroundColor Cyan

$pythonScript = "tools\auto_reflector.py"
if (-not (Test-Path $pythonScript)) {
    Write-Error "Python script not found: $pythonScript"
    exit 1
}

if (-not (Test-Path $InputFile)) {
    Write-Error "Input file not found: $InputFile"
    exit 1
}

# 출력 디렉토리 생성
$outputDir = Split-Path $OutputFile -Parent
if ($outputDir -and -not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Host "Output directory created: $outputDir" -ForegroundColor Yellow
}

$reportDir = Split-Path $ReportFile -Parent
if ($reportDir -and -not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
    Write-Host "Report directory created: $reportDir" -ForegroundColor Yellow
}

# 명령어 구성
$command = "python $pythonScript --mode $Mode --input $InputFile --output $OutputFile --report $ReportFile"

if ($ConfigFile -and (Test-Path $ConfigFile)) {
    $command += " --config $ConfigFile"
    Write-Host "Using config file: $ConfigFile" -ForegroundColor Yellow
} else {
    $command += " --interval $Interval --port $Port"
    
    if ($WatchDirs) {
        $watchDirsStr = $WatchDirs -join " "
        $command += " --watch-dirs $watchDirsStr"
    }
    
    if ($WatchExts) {
        $watchExtsStr = $WatchExts -join " "
        $command += " --watch-exts $watchExtsStr"
    }
}

Write-Host "`nPre-execution Status:" -ForegroundColor Blue
Write-Host "- Python version: $(python --version)"
Write-Host "- Current directory: $(Get-Location)"
Write-Host "- Input file size: $((Get-Item $InputFile).Length) bytes"

# 감시 설정 확인
if ($Mode -eq "watch" -or $Mode -eq "daemon") {
    Write-Host "`nWatch Configuration:" -ForegroundColor Blue
    Write-Host "- Watch directories: $($WatchDirs -join ', ')"
    Write-Host "- Watch extensions: $($WatchExts -join ', ')"
    
    foreach ($dir in $WatchDirs) {
        if (Test-Path $dir) {
            $fileCount = (Get-ChildItem -Path $dir -Recurse -File | Where-Object { $WatchExts -contains $_.Extension }).Count
            Write-Host "  • $dir : $fileCount matching files" -ForegroundColor Gray
        } else {
            Write-Host "  • $dir : Directory not found" -ForegroundColor Red
        }
    }
}

# 스케줄 설정 확인
if ($Mode -eq "scheduled" -or $Mode -eq "daemon") {
    Write-Host "`nSchedule Configuration:" -ForegroundColor Blue
    Write-Host "- Reflection interval: $Interval seconds"
    Write-Host "- Next reflection: $([DateTime]::Now.AddSeconds($Interval).ToString('HH:mm:ss'))"
}

# 웹훅 설정 확인
if ($Mode -eq "webhook" -or $Mode -eq "daemon") {
    Write-Host "`nWebhook Configuration:" -ForegroundColor Blue
    Write-Host "- Port: $Port"
    Write-Host "- Endpoints: /reflect, /status, /history"
    
    # 포트 사용 확인
    $portInUse = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($portInUse) {
        Write-Warning "Port $Port is already in use"
    } else {
        Write-Host "- Port $Port is available" -ForegroundColor Green
    }
}

# 종속성 확인
Write-Host "`nDependency Check:" -ForegroundColor Blue
$dependencies = @("watchdog", "schedule", "flask", "pyyaml", "requests")

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

if ($DryRun) {
    Write-Host "`n🔍 Dry Run Mode - Command Preview:" -ForegroundColor Yellow
    Write-Host $command
    Write-Host "`nDry run completed. No actual execution performed."
    exit 0
}

Write-Host "`nStart auto reflection system? (Y/N)" -ForegroundColor Yellow
$confirm = Read-Host
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Auto reflection cancelled." -ForegroundColor Red
    exit 0
}

Write-Host "`nStarting auto reflection system..." -ForegroundColor Green
$startTime = Get-Date

try {
    if ($Verbose) {
        Invoke-Expression $command
    } else {
        Invoke-Expression $command 2>&1 | Tee-Object -FilePath "auto_reflection.log"
    }
    
    $exitCode = $LASTEXITCODE
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host "`nAuto reflection completed!" -ForegroundColor Green
    Write-Host "- Total runtime: $($duration.TotalMinutes.ToString('F1')) minutes"
    Write-Host "- Exit code: $exitCode"
    
    if ($exitCode -eq 0) {
        Write-Host "Auto reflection system stopped normally." -ForegroundColor Green
    } else {
        Write-Host "Auto reflection system stopped with errors. (Exit code: $exitCode)" -ForegroundColor Yellow
    }
    
} catch {
    Write-Error "Error during auto reflection: $_"
    exit 1
}

# 실행 결과 확인
if (Test-Path $OutputFile) {
    Write-Host "`nOutput file generated: $OutputFile" -ForegroundColor Cyan
    $outputSize = (Get-Item $OutputFile).Length
    Write-Host "- File size: $outputSize bytes"
}

if (Test-Path $ReportFile) {
    Write-Host "`nReport file generated: $ReportFile" -ForegroundColor Cyan
}

if (Test-Path "auto_reflection.log") {
    Write-Host "`nExecution log: auto_reflection.log" -ForegroundColor Cyan
}

# 웹훅 상태 확인
if (($Mode -eq "webhook" -or $Mode -eq "daemon") -and $exitCode -eq 0) {
    Write-Host "`nWebhook Status:" -ForegroundColor Blue
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$Port/status" -Method Get -TimeoutSec 5
        Write-Host "- Status: $($response.status)"
        Write-Host "- Total reflections: $($response.total_reflections)"
        Write-Host "- Success rate: $([math]::Round($response.success_rate, 1))%"
    } catch {
        Write-Host "- Webhook not responding" -ForegroundColor Yellow
    }
}

Write-Host "`nNext steps:" -ForegroundColor Blue
Write-Host "1. Check output: Get-Content $OutputFile"
Write-Host "2. Check report: Get-Content $ReportFile"
Write-Host "3. Check log: Get-Content auto_reflection.log"
Write-Host "4. Webhook status: Invoke-RestMethod -Uri http://localhost:$Port/status"

Write-Host "`nAuto reflection system completed!" -ForegroundColor Green
