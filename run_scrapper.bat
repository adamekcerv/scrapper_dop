@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [%date% %time%] Spoustim scrapper... >> scrapper.log
python -X utf8 app.py >> scrapper.log 2>&1
echo [%date% %time%] Hotovo. >> scrapper.log
