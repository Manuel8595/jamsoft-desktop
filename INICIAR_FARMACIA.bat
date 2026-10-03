@echo off
chcp 65001 >nul
title JAM Soft Premium

echo ============================================
echo    JAM Soft Premium - Iniciando...
echo ============================================
echo.

cd /d "%~dp0"

REM Ativar venv
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Limpar cache
echo [1/3] A limpar cache...
if exist "__pycache__" rmdir /s /q "__pycache__" 2>nul

REM Iniciar aplicacao
echo [2/3] A iniciar aplicacao...
echo.

python main.py

REM Se fechar com erro, manter aberto
if errorlevel 1 pause