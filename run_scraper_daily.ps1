# Daily nursing job scraper for Nurse Explorer
# This script runs the scraper and can be scheduled with Windows Task Scheduler
# Usage: PowerShell -ExecutionPolicy Bypass -File C:\path\to\run_scraper_daily.ps1

$appDirectory = "C:\Users\Drewhitt\nursing-salary-app"
$logFile = "$appDirectory\scraper_log.txt"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

try {
    Set-Location $appDirectory

    # Activate virtual environment
    & "venv\Scripts\Activate.ps1"

    # Run the scraper
    Write-Host "[$timestamp] Starting daily scraper..."
    python scraper_rolling_daily.py

    # Log the execution
    Add-Content -Path $logFile -Value "[$timestamp] Scraper executed successfully"
    Write-Host "[$timestamp] Scraper completed successfully"
}
catch {
    $errorMsg = $_.Exception.Message
    Add-Content -Path $logFile -Value "[$timestamp] ERROR: $errorMsg"
    Write-Host "[$timestamp] ERROR: $errorMsg"
}
finally {
    # Deactivate virtual environment
    deactivate 2>&1 | Out-Null
}
