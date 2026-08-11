@echo off
chcp 65001 >nul
:: ============================================================
:: sync_from_github.bat
:: Stáhne aktualizovaný vysledky.xlsx z GitHubu do této složky.
:: Spouštěn automaticky Task Schedulerem každý den v 9:00.
:: ============================================================

set LOG=%~dp0sync.log
echo [%date% %time%] Stahuji aktualizace z GitHubu... >> "%LOG%"

cd /d "%~dp0"
git pull --rebase >> "%LOG%" 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] OK – vysledky.xlsx aktualizovan. >> "%LOG%"
) else (
    echo [%date% %time%] CHYBA pri git pull. >> "%LOG%"
)
