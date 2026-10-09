# Daily nursing job scraper for Nurse Explorer
# Usage: PowerShell -ExecutionPolicy Bypass -File C:\Users\Drewhitt\nursing-salary-app\run_scraper_daily.ps1

$ErrorActionPreference = "Stop"

$appDirectory = "C:\Users\Drewhitt\nursing-salary-app"
$logFile = "$appDirectory\scraper_log.txt"
$python = "$appDirectory\venv\Scripts\python.exe"

function Write-Log($message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $message
    Add-Content -Path $logFile -Value $line
    Write-Host $line
}

try {
    Set-Location $appDirectory
    Write-Log "Starting daily scraper"

    & $python scraper_rolling_daily.py
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Log "Scraper completed successfully"
    } else {
        Write-Log "Scraper FAILED with exit code $exitCode"
    }
}
catch {
    Write-Log "ERROR: $($_.Exception.Message)"
}