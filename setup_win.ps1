# PowerShell
$ErrorActionPreference = "Stop"

Write-Host "[*] Creating skeleton..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path ".\docs" | Out-Null
New-Item -ItemType Directory -Force -Path ".\.cursor\rules" | Out-Null

Write-Host "[*] Done. Next:" -ForegroundColor Green
Write-Host "tm parse prd .\docs\PRD.md -o .\tasks.json"
Write-Host "cursor agent --apply=ask --rules --mcp"
