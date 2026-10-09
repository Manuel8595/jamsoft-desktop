@echo off
chcp 65001 >nul
title JAM Soft - Desinstalar
color 0C

echo ========================================
echo   JAM SOFT - DESINSTALAR
echo ========================================
echo.
echo  Isto vai remover o arranque automatico.
echo  Os teus DADOS (farmacia.db) serao mantidos.
echo.
pause

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "ATALHO=%STARTUP_FOLDER%\JAMSoft.lnk"

if exist "%ATALHO%" (
    del "%ATALHO%"
    echo Atalho removido.
) else (
    echo Atalho nao encontrado.
)

echo.
echo Aplicacao desinstalada.
echo Os teus dados em farmacia.db foram mantidos.
echo.
pause
