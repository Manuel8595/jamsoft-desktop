@echo off
chcp 65001 >nul
title JAM Soft - Farmacia
color 0A

cd /d "%~dp0"

cls
echo.
echo ========================================
echo      JAM SOFT - FARMACIA
echo ========================================
echo.

REM --- Passo 1: Verificar actualizacoes ---
echo [1/5] A verificar actualizacoes...
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo    Git nao instalado - a ignorar actualizacao
    goto SEM_GIT
)

git fetch origin main --quiet 2>nul
if %errorlevel% neq 0 (
    echo    Sem internet - a continuar com versao local
    goto SEM_GIT
)

for /f %%i in ('git rev-parse HEAD') do set LOCAL_HASH=%%i
for /f %%i in ('git rev-parse origin/main') do set REMOTE_HASH=%%i

if "%LOCAL_HASH%"=="%REMOTE_HASH%" (
    echo    Ja esta na versao mais recente
    goto SEM_GIT
)

echo    Nova versao encontrada - a actualizar...
git pull origin main --quiet 2>nul
if %errorlevel% neq 0 (
    echo    Erro ao actualizar - a continuar com versao local
) else (
    echo    Actualizacao concluida!
)

:SEM_GIT

REM --- Passo 2: Backup automatico ---
echo.
echo [2/5] A criar backup da base de dados...
if not exist "backups" mkdir backups

if exist "farmacia.db" (
    set BACKUP_FILE=backups\farmacia_%date:~-4%%date:~3,2%%date:~0,2%.db
    copy "farmacia.db" "%BACKUP_FILE%" >nul 2>&1
    if %errorlevel% equ 0 (
        echo    Backup criado
    ) else (
        echo    Aviso: nao foi possivel criar backup
    )
) else (
    echo    Sem base de dados - primeiro arranque
)

REM --- Passo 3: Verificar Python ---
echo.
echo [3/5] A verificar Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo    ERRO: Python nao encontrado!
    echo    Instale Python 3.12 ou superior.
    echo.
    pause
    exit /b 1
)

REM --- Passo 4: Dependencias ---
echo.
echo [4/5] A verificar dependencias...
pip install -r requirements.txt --quiet --disable-pip-version-check 2>nul

REM --- Passo 5: Abrir aplicacao ---
echo.
echo [5/5] A iniciar aplicacao...
echo.
echo ========================================
echo.

python main.py

echo.
echo ========================================
echo    Aplicacao encerrada
echo ========================================
echo.
pause