@echo off
chcp 65001 >nul
:: ============================================================
:: setup_task.bat – Registrace automatického spouštění scrapperu
:: Spustte tento soubor JEDNOU jako Administrator!
:: Vytvoří Task Scheduler úlohu: "WebScrapper"
:: Spuštění: každý den v 8:00 ráno
:: ============================================================

set TASK_NAME=WebScrapper
set SCRIPT_DIR=%~dp0
set BAT_FILE=%SCRIPT_DIR%run_scrapper.bat

echo.
echo ============================================================
echo  Registrace Task Scheduler ulohy: %TASK_NAME%
echo  Skript: %BAT_FILE%
echo  Cas spusteni: Kazdy den v 8:00
echo ============================================================
echo.

:: Smazat existující úlohu (pokud existuje)
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: Vytvořit novou úlohu
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%BAT_FILE%\"" ^
    /sc DAILY ^
    /st 08:00 ^
    /ru "%USERNAME%" ^
    /rl HIGHEST ^
    /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo  [OK] Uloha '%TASK_NAME%' byla uspesne zaregistrovana!
    echo  Scrapper se bude automaticky spoustet kazdy den v 8:00.
    echo.
    echo  Pro okamzite otestovani spuste:
    echo    schtasks /run /tn "%TASK_NAME%"
    echo.
    echo  Pro zobrazeni ulohy v Task Scheduleru:
    echo    taskschd.msc
) else (
    echo.
    echo  [CHYBA] Registrace se nepodarila.
    echo  Zkuste spustit tento soubor jako Administrator:
    echo  Kliknete pravym tlacitkem na setup_task.bat a zvolte 'Spustit jako spravce'
)

echo.
pause
