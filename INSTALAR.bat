@echo off
chcp 65001 >nul
title JAM Soft - Instalacao
color 0A

cd /d "%~dp0"

cls
echo.
echo ========================================
echo      JAM SOFT - INSTALACAO
echo ========================================
echo.
echo  Este script vai:
echo   1. Verificar se tens Python instalado
echo   2. Instalar as dependencias necessarias
echo   3. Criar pastas de trabalho
echo   4. Configurar arranque automatico no Windows
echo.
echo ========================================
echo.
pause

REM ─── Passo 1: Verificar Python ───
echo.
echo [1/5] A verificar Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo    ERRO: Python nao encontrado!
    echo.
    echo    Instala Python 3.12 ou superior em:
    echo      https://www.python.org/downloads/
    echo.
    echo    IMPORTANTE: Marca a opcao "Add Python to PATH" na instalacao.
    echo.
    pause
    exit /b 1
)
python --version
echo    Python OK!

REM ─── Passo 2: Instalar dependencias ───
echo.
echo [2/5] A instalar dependencias (pode demorar 2-5 min)...
pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo.
    echo    AVISO: Algumas dependencias falharam.
    echo    Tenta correr novamente.
)

REM ─── Passo 3: Criar pastas ───
echo.
echo [3/5] A criar pastas de trabalho...
if not exist "backups" mkdir backups
if not exist "facturas" mkdir facturas
if not exist "saft" mkdir saft
if not exist "logs" mkdir logs
echo    Pastas criadas.

REM ─── Passo 4: Arranque automatico ───
echo.
echo [4/5] A configurar arranque automatico...

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "ATALHO=%STARTUP_FOLDER%\JAMSoft.lnk"

set "SCRIPT_PATH=%~dp0INICIAR_FARMACIA.bat"
set "WORK_DIR=%~dp0"

powershell -Command ^
    "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%ATALHO%'); $sc.TargetPath = '%SCRIPT_PATH%'; $sc.WorkingDirectory = '%WORK_DIR%'; $sc.Description = 'JAM Soft - Farmacia'; $sc.Save()"

if exist "%ATALHO%" (
    echo    Atalho criado em: %STARTUP_FOLDER%
) else (
    echo    AVISO: Nao foi possivel criar atalho automatico.
    echo    Cria manualmente um atalho de INICIAR_FARMACIA.bat em:
    echo      shell:startup
)

REM ─── Passo 5: Testar ───
echo.
echo [5/5] A verificar instalacao...
if exist "farmacia.db" (
    echo    Base de dados encontrada.
) else (
    echo    Base de dados sera criada no primeiro arranque.
)

echo.
echo ========================================
echo      INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo  Proximos passos:
echo   1. Duplo-clique em INICIAR_FARMACIA.bat
echo   2. Fazer login com credenciais fornecidas
echo.
echo  A aplicacao vai abrir AUTOMATICAMENTE
echo  sempre que ligares este PC.
echo.
echo ========================================
echo.
pause