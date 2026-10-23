# Daily nursing job scraper for Nurse Explorer
# Usage: PowerShell -ExecutionPolicy Bypass -File <full path to this file>
# The app folder is taken from this file's own location, so the script keeps
# working if the project folder moves (for example into a combined repo).

$ErrorActionPreference = "Stop"

$appDirectory = $PSScriptRoot
$logFile = Join-Path $appDirectory "scraper_log.txt"
$venvPython = Join-Path $appDirectory "venv\Scripts\python.exe"

# Use the project venv when it exists; otherwise fall back to the system Python.
if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $python = "python"
}

function Write-Log($message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $message
    Add-Content -Path $logFile -Value $line
    Write-Host $line
}

try {
    Set-Location $appDirectory
    Write-Log "Starting daily scraper (folder: $appDirectory, python: $python)"

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

# Put the PC back to sleep when done, but only if nobody was using it.
# Sleep (not shutdown) keeps the wake timer working, so the next run can still wake the PC.
# Set $sleepAfterRun = $false to leave the PC on.
$sleepAfterRun = $false
$recentInputMinutes = 60

Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class IdleTime {
    [StructLayout(LayoutKind.Sequential)]
    struct LASTINPUTINFO { public uint cbSize; public uint dwTime; }
    [DllImport("user32.dll")]
    static extern bool GetLastInputInfo(ref LASTINPUTINFO plii);
    public static double MinutesSinceLastInput() {
        LASTINPUTINFO info = new LASTINPUTINFO();
        info.cbSize = (uint)Marshal.SizeOf(info);
        GetLastInputInfo(ref info);
        return (Environment.TickCount - (int)info.dwTime) / 60000.0;
    }
}
"@

if ($sleepAfterRun) {
    $minutesIdle = [IdleTime]::MinutesSinceLastInput()
    if ($minutesIdle -lt $recentInputMinutes) {
        Write-Log ("Skipping sleep: keyboard/mouse input {0:N0} min ago" -f $minutesIdle)
    } else {
        Write-Log ("Putting PC to sleep (last input {0:N0} min ago)" -f $minutesIdle)
        Start-Sleep -Seconds 5
        rundll32.exe powrprof.dll,SetSuspendState 0,1,0
    }
}
