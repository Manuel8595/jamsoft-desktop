# -*- coding: utf-8 -*-
"""
Gera pacote de instalacao profissional JAM Soft.
Estrutura organizada + BD exemplo + README personalizado.
"""
import os
import shutil
import sqlite3
import zipfile
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIGURACAO
# ============================================================
VERSAO = "1.0.3"
NOME_PACOTE = f"JAM_Soft_v{VERSAO}_Setup"
PASTA_RAIZ = Path(".").resolve()
PASTA_TEMP = PASTA_RAIZ / "setup_temp" / NOME_PACOTE
ZIP_FINAL = PASTA_RAIZ / f"{NOME_PACOTE}.zip"

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
    pastas = [
        "codigo",
        "logos",
        "docs",
        "exemplos",
    ]
    for p in pastas:
        (PASTA_TEMP / p).mkdir(exist_ok=True)
    print(f"[1/5] Estrutura criada em {PASTA_TEMP}")

def copiar_python():
    """Copia todos os .py para codigo/ (mantem estrutura)."""
    n = 0
    # .py da raiz
    for f in PASTA_RAIZ.glob("*.py"):
        shutil.copy2(f, PASTA_TEMP / "codigo" / f.name)
        n += 1
    
    # .py da pasta services/
    if (PASTA_RAIZ / "services").exists():
        (PASTA_TEMP / "codigo" / "services").mkdir(exist_ok=True)
        for f in (PASTA_RAIZ / "services").glob("*.py"):
            shutil.copy2(f, PASTA_TEMP / "codigo" / "services" / f.name)
            n += 1
    
    print(f"[2/5] {n} ficheiros Python copiados")
    return n

def copiar_logos():
    n = 0
    for f in (PASTA_RAIZ / "logos").glob("*"):
        if f.is_file():
            shutil.copy2(f, PASTA_TEMP / "logos" / f.name)
            n += 1
    (PASTA_TEMP / "codigo" / "logos").mkdir(exist_ok=True)
    for f in (PASTA_RAIZ / "logos").glob("*"):
        if f.is_file():
            shutil.copy2(f, PASTA_TEMP / "codigo" / "logos" / f.name)
    print(f"[3/5] {n} logos copiados (raiz + codigo/logos/)")
    return n

def copiar_docs():
    n = 0
    docs = ["LEIA-ME.txt", "MANUAL_JAMSOFT.md", "RESUMO_SISTEMA.md",
            "VERSION_HISTORY.md", "DOCUMENTO_TECNICO_AGT.md",
            "VERSION", "requirements.txt",
            "INSTALAR.bat", "INICIAR_FARMACIA.bat", "DESINSTALAR.bat"]
    for doc in docs:
        origem = PASTA_RAIZ / doc
        if origem.exists():
            shutil.copy2(origem, PASTA_TEMP / doc)
            n += 1
    print(f"[4/5] {n} ficheiros de documentacao copiados")
    return n

def criar_bd_exemplo():
    """Cria BD limpa com dados de exemplo + utilizador admin."""
    origem = PASTA_RAIZ / "farmacia.db"
    destino = PASTA_TEMP / "codigo" / "farmacia_exemplo.db"
    
    if not origem.exists():
        print("[AVISO] farmacia.db nao existe - a saltar BD exemplo")
        return
    
    shutil.copy2(origem, destino)
    
    conn = sqlite3.connect(destino)
    cur = conn.cursor()
    
    try:
        # Limpar tabelas de transaccao
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
        
        # Substituir empresa por exemplo
        try:
            cur.execute("UPDATE empresa SET nome = ?, nif = ?, endereco = ?, telefone = ?, email = ? WHERE id = 1",
                        ("FARMACIA EXEMPLO LDA", "5000000000", "Rua Exemplo, Luanda", "+244 900 000 000", "exemplo@farmacia.ao"))
        except:
            pass
        
        # Manter APENAS um utilizador admin
        try:
            cur.execute("DELETE FROM utilizadores")
        except:
            pass
        
        # Criar admin com senha admin (hash SHA-256)
        import hashlib
        import secrets
        salt = secrets.token_hex(16)
        senha_hash = hashlib.sha256((salt + "admin").encode()).hexdigest()
        
        try:
            cur.execute("""INSERT INTO utilizadores 
                (nome, username, senha_hash, salt, perfil, ativo, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                ("Administrador", "admin", senha_hash, salt, "ADMINISTRADOR", 1))
            print("[5/5] BD exemplo criada + admin/admin adicionado")
        except Exception as e:
            print("[AVISO] Nao foi possivel criar admin: " + str(e))
        
        # Limpar clientes
        try:
            cur.execute("DELETE FROM clientes")
            cur.execute("INSERT INTO clientes (nome, nif, telefone, email) VALUES (?, ?, ?, ?)",
                        ("Consumidor Final", "-", "-", "-"))
        except:
            pass
        
        conn.commit()
    except Exception as e:
        print("[AVISO] Erro a limpar BD: " + str(e))
    finally:
        conn.close()


def criar_readme():
    """Cria LEIA-ME personalizado."""
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

4. Login: admin / admin (muda depois!)

========================================
ESTRUTURA
========================================

- codigo/      Todos os ficheiros Python
- logos/       Logotipos JAM Soft
- docs/        Documentacao completa
- exemplos/    BD de exemplo (sem dados reais)

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
    """Empacota tudo num ZIP."""
    with zipfile.ZipFile(ZIP_FINAL, "w", zipfile.ZIP_DEFLATED) as z:
        for f in PASTA_TEMP.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(PASTA_TEMP.parent))
    
    tam = ZIP_FINAL.stat().st_size / 1024 / 1024
    print(f"[ZIP] Criado: {ZIP_FINAL.name} ({tam:.2f} MB)")

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
print(f"  Pasta:    {ZIP_FINAL}")
print()
