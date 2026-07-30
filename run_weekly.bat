@echo off
REM Weekly prospecting run. Point Windows Task Scheduler at this file.
REM
REM   schtasks /create /tn "Antibody Prospecting" /tr "C:\Users\aniru\biotech\run_weekly.bat" ^
REM            /sc weekly /d MON /st 07:00
REM
REM Reviewer decisions are read from output\prospect_review_queue.xlsx before the
REM new report is written, so close Excel before the scheduled time.

cd /d "%~dp0"

echo ============================================================
echo  Antibody Intent Prospecting - weekly run
echo  %DATE% %TIME%
echo ============================================================

python -m intent_pipeline.run --max-results 12

if errorlevel 1 (
    echo.
    echo RUN FAILED - see the output above.
    exit /b 1
)

echo.
echo Report: %CD%\output\prospect_review_queue.xlsx
