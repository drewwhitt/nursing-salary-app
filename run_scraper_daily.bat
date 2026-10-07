@echo off
REM Daily nursing job scraper for Nurse Explorer
REM This script runs the scraper and can be scheduled with Windows Task Scheduler

cd /d C:\Users\Drewhitt\nursing-salary-app

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the scraper
python scraper_rolling_daily.py

REM Log the execution
echo Scraper executed at %date% %time% >> scraper_log.txt

REM Deactivate virtual environment
deactivate