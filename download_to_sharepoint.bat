@echo off
chcp 65001 >nul
:: Skript pro automatické stažení nejnovějšího souboru vysledky.xlsx z GitHubu přímo do SharePoint složky.

set SHAREPOINT_DIR=C:\Users\cervenka\mappaostrava\Data - Dokumenty\4_MAPPA_PRAC\CERVENKA\Scrapper
set TARGET_FILE=%SHAREPOINT_DIR%\vysledky.xlsx
set RAW_URL=https://raw.githubusercontent.com/adamekcerv/scrapper_dop/main/vysledky.xlsx

echo [%date% %time%] Stahuji aktualni vysledky.xlsx z GitHubu do SharePointu...

if not exist "%SHAREPOINT_DIR%" (
    mkdir "%SHAREPOINT_DIR%" 2>nul
)

powershell -Command "Invoke-WebRequest -Uri '%RAW_URL%' -OutFile '%TARGET_FILE%'"

if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] OK: Soubor byl uspesne ulozen na SharePoint: %TARGET_FILE%
) else (
    echo [%date% %time%] CHYBA: Nepodarilo se stahnout soubor z GitHubu.
)
