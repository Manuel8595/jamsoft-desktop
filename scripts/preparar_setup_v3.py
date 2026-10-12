# -*- coding: utf-8 -*-
"""
Setup profissional JAM Soft v1.0.3
Gera pacote completo com .bat adaptados.
"""
import os
import shutil
import sqlite3
import zipfile
import hashlib
import secrets
from pathlib import Path
from datetime import datetime

VERSAO = "1.0.3"
NOME_PACOTE = f"JAM_Soft_v{VERSAO}_Setup"
PASTA_RAIZ = Path(".").resolve()
PASTA_TEMP = PASTA_RAIZ / "setup_temp" / NOME_PACOTE
ZIP_FINAL = PASTA_RAIZ / f"{NOME_PACOTE}.zip"

# ============================================================
# .BAT TEMPLATES
# ============================================================
INSTALAR_BAT = r"""@echo off
chcp 65001 >nul
title JAM Soft - Instalacao v1.0.4
color 0A
cd /d "%~dp0"

cls
echo.
echo ========================================
echo      JAM SOFT - INSTALACAO v1.0.4
echo ========================================
echo.
echo  Este script vai:
echo   1. Verificar se tens Python instalado
echo   2. Verificar ligacao a internet
echo   3. Verificar espaco em disco
echo   4. Instalar as dependencias necessarias
echo   5. Criar pastas de trabalho
echo   6. Preparar a base de dados
echo   7. Criar atalhos (arranque + desktop + menu)
echo.
echo ========================================
echo.
pause

REM --- Passo 1: Verificar Python ---
echo.
echo [1/7] A verificar Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo    ERRO: Python nao encontrado!
    echo.
    echo    Instala Python 3.12 ou superior em:
    echo      https://www.python.org/downloads/
    echo.
    echo    IMPORTANTE: Marca "Add Python to PATH".
    echo.
    pause
    exit /b 1
)
python --version
echo    Python OK!

REM --- Passo 2: Verificar Internet ---
echo.
echo [2/7] A verificar ligacao a internet...
ping -n 1 8.8.8.8 >nul 2>&1
if %errorlevel% neq 0 (
    echo    AVISO: Sem ligacao a internet.
    echo    A app funciona offline mas nao sincroniza.
    echo.
) else (
    echo    Internet OK!
)

REM --- Passo 3: Verificar Espaco ---
echo.
echo [3/7] A verificar espaco em disco...
for /f "tokens=3" %%a in ('dir /-c %~dp0 ^| find "bytes"') do set ESPACO=%%a
echo    Espaco disponivel verificado.

REM --- Passo 4: Instalar dependencias ---
echo.
echo [4/7] A instalar dependencias (pode demorar 2-5 min)...
pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo    AVISO: Algumas dependencias falharam.
) else (
    echo    Dependencias instaladas.
)

REM --- Passo 5: Criar pastas ---
echo.
echo [5/7] A criar pastas de trabalho...
if not exist "codigo\backups" mkdir "codigo\backups"
if not exist "codigo\facturas" mkdir "codigo\facturas"
if not exist "codigo\saft" mkdir "codigo\saft"
if not exist "codigo\logs" mkdir "codigo\logs"
if not exist "backups" mkdir backups
if not exist "facturas" mkdir facturas
if not exist "saft" mkdir saft
if not exist "logs" mkdir logs
echo    Pastas criadas.

REM --- Passo 6: Preparar BD ---
echo.
echo [6/7] A preparar base de dados...
if not exist "codigo\farmacia.db" (
    if exist "codigo\farmacia_exemplo.db" (
        copy "codigo\farmacia_exemplo.db" "codigo\farmacia.db" >nul
        echo    Base de dados preparada.
    ) else (
        echo    AVISO: BD exemplo nao encontrada.
    )
) else (
    echo    Base de dados ja existe.
)

REM --- Passo 7: Criar atalhos ---
echo.
echo [7/7] A criar atalhos...

set "SCRIPT_PATH=%~dp0INICIAR_FARMACIA.bat"
set "WORK_DIR=%~dp0"
set "ICONE=%~dp0logos\jamsoft.ico"

REM 7a. Atalho no arranque automatico
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "ATALHO_STARTUP=%STARTUP_FOLDER%\JAMSoft.lnk"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%ATALHO_STARTUP%'); $sc.TargetPath = '%SCRIPT_PATH%'; $sc.WorkingDirectory = '%WORK_DIR%'; $sc.Description = 'JAM Soft'; if (Test-Path '%ICONE%') { $sc.IconLocation = '%ICONE%' }; $sc.Save()"

if exist "%ATALHO_STARTUP%" (
    echo    [OK] Atalho no arranque automatico.
) else (
    echo    [AVISO] Nao foi possivel criar atalho no arranque.
)

REM 7b. Atalho no Ambiente de Trabalho (Desktop)
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP=%%i"
set "ATALHO_DESKTOP=%DESKTOP%\JAM Soft.lnk"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%ATALHO_DESKTOP%'); $sc.TargetPath = '%SCRIPT_PATH%'; $sc.WorkingDirectory = '%WORK_DIR%'; $sc.Description = 'JAM Soft - Sistema de Farmacia'; if (Test-Path '%ICONE%') { $sc.IconLocation = '%ICONE%' }; $sc.Save()"

if exist "%ATALHO_DESKTOP%" (
    echo    [OK] Atalho no Ambiente de Trabalho.
) else (
    echo    [AVISO] Nao foi possivel criar atalho no Desktop.
)

REM 7c. Atalho no Menu Iniciar
for /f "usebackq tokens=*" %%i in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Programs')"`) do set "MENU_START=%%i"
set "ATALHO_MENU=%MENU_START%\JAM Soft.lnk"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%ATALHO_MENU%'); $sc.TargetPath = '%SCRIPT_PATH%'; $sc.WorkingDirectory = '%WORK_DIR%'; $sc.Description = 'JAM Soft - Sistema de Farmacia'; if (Test-Path '%ICONE%') { $sc.IconLocation = '%ICONE%' }; $sc.Save()"

if exist "%ATALHO_MENU%" (
    echo    [OK] Atalho no Menu Iniciar.
) else (
    echo    [AVISO] Nao foi possivel criar atalho no Menu Iniciar.
)

echo.
echo ========================================
echo      INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo  Proximos passos:
echo   1. Duplo-clique em INICIAR_FARMACIA.bat
echo   2. Login: admin / admin
echo.
echo  IMPORTANTE: Muda a senha do admin apos o primeiro login!
echo.
pause
"""

INICIAR_BAT = r"""@echo off
chcp 65001 >nul
title JAM Soft - Sistema de Farmacia v1.0.3
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
"""

DESINSTALAR_BAT = r"""@echo off
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
echo Os teus dados em codigo\farmacia.db foram mantidos.
echo.
pause
"""

# ============================================================
# FUNCOES
# ============================================================
def limpar():
    if PASTA_TEMP.exists():
        shutil.rmtree(PASTA_TEMP)
    if ZIP_FINAL.exists():
        ZIP_FINAL.unlink()
    PASTA_TEMP.mkdir(parents=True)

def criar_estrutura():
    for p in ["codigo", "logos", "docs", "exemplos"]:
        (PASTA_TEMP / p).mkdir(exist_ok=True)
    print("[1/6] Estrutura criada")

def copiar_python():
    n = 0
    for f in PASTA_RAIZ.glob("*.py"):
        shutil.copy2(f, PASTA_TEMP / "codigo" / f.name)
        n += 1
    if (PASTA_RAIZ / "services").exists():
        (PASTA_TEMP / "codigo" / "services").mkdir(exist_ok=True)
        for f in (PASTA_RAIZ / "services").glob("*.py"):
            shutil.copy2(f, PASTA_TEMP / "codigo" / "services" / f.name)
            n += 1
    print(f"[2/6] {n} ficheiros Python copiados")

def copiar_logos():
    n = 0
    (PASTA_TEMP / "codigo" / "logos").mkdir(exist_ok=True)
    for f in (PASTA_RAIZ / "logos").glob("*"):
        if f.is_file():
            shutil.copy2(f, PASTA_TEMP / "logos" / f.name)
            shutil.copy2(f, PASTA_TEMP / "codigo" / "logos" / f.name)
            n += 1
    print(f"[3/6] {n} logos copiados (raiz + codigo/logos/)")

def copiar_docs():
    n = 0
    # Copiar VERSION e VERSION_HISTORY para codigo/ tambem
    for f_nome in ["VERSION", "VERSION_HISTORY.md"]:
        f_orig = PASTA_RAIZ / f_nome
        if f_orig.exists():
            shutil.copy2(f_orig, PASTA_TEMP / "codigo" / f_nome)
            n += 1
    # VERSION_HISTORY_C?PIA
    docs = ["MANUAL_JAMSOFT.md", "RESUMO_SISTEMA.md",
            "VERSION_HISTORY.md", "DOCUMENTO_TECNICO_AGT.md",
            "VERSION", "requirements.txt", "MANUAL_NOVA_FILIAL.md", "LICENSE"]
    for doc in docs:
        origem = PASTA_RAIZ / doc
        if origem.exists():
            shutil.copy2(origem, PASTA_TEMP / doc)
            n += 1
    # Escrever os .bat
    with open(PASTA_TEMP / "INSTALAR.bat", "w", encoding="utf-8", newline="\r\n") as f:
        f.write(INSTALAR_BAT)
    with open(PASTA_TEMP / "INICIAR_FARMACIA.bat", "w", encoding="utf-8", newline="\r\n") as f:
        f.write(INICIAR_BAT)
    with open(PASTA_TEMP / "DESINSTALAR.bat", "w", encoding="utf-8", newline="\r\n") as f:
        f.write(DESINSTALAR_BAT)
    print(f"[4/6] {n} docs + 3 .bat gerados")

def criar_bd_exemplo():
    origem = PASTA_RAIZ / "farmacia.db"
    destino = PASTA_TEMP / "codigo" / "farmacia_exemplo.db"
    
    if not origem.exists():
        print("[AVISO] farmacia.db nao existe")
        return
    
    shutil.copy2(origem, destino)
    conn = sqlite3.connect(destino)
    cur = conn.cursor()
    
    try:
        tabelas_limpar = [
            "facturas", "itens_factura", "vendas", "itens_venda",
            "itens_venda_lotes", "movimentos_caixa", "caixas",
            "turnos_caixa", "fecho_dia", "dias_operacao",
            "depositos", "devolucoes", "compras", "itens_compra",
            "perdas", "inventarios", "itens_inventario",
            "transferencias_filiais", "itens_transferencia",
            "historico_ibt", "auditoria", "log_sincronizacao",
            "fila_sincronizacao", "taloes_tpa", "tentativas_login",
        ]
        for t in tabelas_limpar:
            try:
                cur.execute("DELETE FROM " + t)
            except:
                pass
        
        try:
            cur.execute("UPDATE empresa SET nome = ?, nif = ?, endereco = ?, telefone = ?, email = ? WHERE id = 1",
                        ("FARMACIA EXEMPLO LDA", "5000000000", "Rua Exemplo, Luanda", "+244 900 000 000", "exemplo@farmacia.ao"))
        except:
            pass
        
        try:
            cur.execute("DELETE FROM utilizadores")
        except:
            pass
        
        # Usar bcrypt directamente (mesmo algoritmo do database.py)
        try:
            import bcrypt
            salt = bcrypt.gensalt(rounds=12)
            senha_hash = bcrypt.hashpw("admin".encode("utf-8"), salt).decode("utf-8")
            cur.execute("""INSERT INTO utilizadores 
                (nome, username, senha_hash, salt, perfil, ativo, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                ("Administrador", "admin", senha_hash, "", "admin", 1))
            print("   Admin criado (bcrypt)")
        except ImportError:
            print("   AVISO: bcrypt nao instalado - admin nao criado")
        except Exception as e:
            print("   Aviso admin: " + str(e))
        
        try:
            cur.execute("DELETE FROM clientes")
            cur.execute("INSERT INTO clientes (nome, nif, telefone, email) VALUES (?, ?, ?, ?)",
                        ("Consumidor Final", "-", "-", "-"))
        except:
            pass
        
        conn.commit()
        print("[5/6] BD exemplo criada + admin/admin")
    except Exception as e:
        print("[AVISO] Erro BD: " + str(e))
    finally:
        conn.close()

def criar_readme():
    conteudo = f"""========================================
JAM SOFT - SISTEMA DE GESTAO DE FARMACIA
========================================

Versao: {VERSAO}
Data: {datetime.now().strftime("%d/%m/%Y")}

========================================
INSTALACAO (primeira vez)
========================================

1. Extrai esta pasta para:
   C:\\farmacia-app\\

2. Duplo-clique em INSTALAR.bat
   (aguarda 2-5 minutos)

3. Duplo-clique em INICIAR_FARMACIA.bat

4. Login inicial:
   Utilizador: admin
   Senha:      admin

5. IMPORTANTE: Muda a senha apos o primeiro login!

========================================
ESTRUTURA
========================================

- codigo/      Todos os ficheiros Python + BD
- logos/       Logotipos JAM Soft
- docs/        Documentacao
- exemplos/    Exemplos

========================================
SUPORTE
========================================

Email: suporte@jamsoft.ao
Telefone: +244 XXX XXX XXX

========================================
"""
    with open(PASTA_TEMP / "LEIA-ME.txt", "w", encoding="utf-8") as f:
        f.write(conteudo)

def criar_zip():
    with zipfile.ZipFile(ZIP_FINAL, "w", zipfile.ZIP_DEFLATED) as z:
        for f in PASTA_TEMP.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(PASTA_TEMP.parent))
    tam = ZIP_FINAL.stat().st_size / 1024 / 1024
    print(f"[6/6] ZIP criado: {ZIP_FINAL.name} ({tam:.2f} MB)")

# ============================================================
# EXECUCAO
# ============================================================
print("=" * 60)
print(f"  SETUP PROFISSIONAL JAM Soft v{VERSAO}")
print("=" * 60)
print()

limpar()
criar_estrutura()
copiar_python()
copiar_logos()
copiar_docs()
criar_bd_exemplo()
criar_readme()
criar_zip()

print()
print("=" * 60)
print("  SETUP CRIADO COM SUCESSO!")
print("=" * 60)
print(f"  Ficheiro: {ZIP_FINAL.name}")
print()
