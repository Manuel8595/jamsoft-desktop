@echo off
chcp 65001 >nul
title JAM Soft - Sistema de Farmacia
color 0B
cd /d "%~dp0"

REM --- Auto-update via git (se existir .git) ---
if exist "codigo\.git" (
    echo A verificar actualizacoes...
    cd codigo
    git pull --quiet 2>nul
    cd ..
)

REM --- Iniciar aplicacao ---
cd codigo
python main.py
cd ..
