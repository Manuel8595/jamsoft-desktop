"""
CORRIGIR_TUDO.PY - Correcção automática dos 7 bugs críticos
JAM Soft — 01/10/2026

Este script:
1. Corrige o typo "0#" em seguranca.py
2. Adiciona colunas TPA à tabela caixas
3. Corrige atualizar_totais_caixa() para calcular total_tpa
4. Adiciona tabelas fila_sincronizacao e log_sincronizacao ao criar_tabelas()
5. Adiciona autorizado_por e numero_documento a movimentos_caixa
6. Adiciona configuracao_global, farmacias, terminais ao criar_tabelas()
7. Adiciona tabelas IBT ao criar_tabelas()

FAZ BACKUP de cada ficheiro antes de mexer (.bak3, .bak4, etc.)
"""

import os
import shutil
import sys
from datetime import datetime

# Cores para o terminal
VERDE = "\033[92m"
VERMELHO = "\033[91m"
AMARELO = "\033[93m"
AZUL = "\033[94m"
RESET = "\033[0m"

LOG = []


def log(msg, cor=RESET):
    print(f"{cor}{msg}{RESET}")
    LOG.append(msg)


def backup(ficheiro):
    """Faz backup de um ficheiro com timestamp."""
    if not os.path.exists(ficheiro):
        log(f"  ⚠️  {ficheiro} não existe — salto backup", AMARELO)
        return False
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = f"{ficheiro}.bak_{ts}"
    try:
        shutil.copy2(ficheiro, destino)
        log(f"  💾 Backup: {destino}", AZUL)
        return True
    except Exception as e:
        log(f"  ❌ Erro backup: {e}", VERMELHO)
        return False


# ============================================================
# BUG 1 — Corrigir typo em seguranca.py
# ============================================================

def corrigir_bug1():
    log("\n[1/7] A corrigir seguranca.py (typo 0#)...", AMARELO)
    ficheiro = "seguranca.py"
    if not os.path.exists(ficheiro):
        log(f"  ❌ {ficheiro} não encontrado!", VERMELHO)
        return False

    backup(ficheiro)

    with open(ficheiro, "r", encoding="utf-8") as f:
        conteudo = f.read()

    if conteudo.startswith("0#"):
        conteudo = conteudo[1:]  # remove o "0"
        with open(ficheiro, "w", encoding="utf-8") as f:
            f.write(conteudo)
        log("  ✅ Typo corrigido: '0#' → '#'", VERDE)
        return True
    else:
        log("  ℹ️  Não tem '0#' no início — já está OK", AZUL)
        return True


# ============================================================
# BUG 2+4+5+6+7 — Adicionar colunas e tabelas em database.py
# ============================================================

def corrigir_database():
    log("\n[2-7/7] A corrigir database.py...", AMARELO)
    ficheiro = "database.py"
    if not os.path.exists(ficheiro):
        log(f"  ❌ {ficheiro} não encontrado!", VERMELHO)
        return False

    backup(ficheiro)

    with open(ficheiro, "r", encoding="utf-8") as f:
        conteudo = f.read()

    alterado = False

    # ---------------------------------------------------------
    # BUG 2 — Colunas TPA na tabela caixas
    # ---------------------------------------------------------
    if "contado_tpa REAL DEFAULT 0" not in conteudo:
        antigo = """            valor_contado REAL DEFAULT 0,
            diferenca REAL DEFAULT 0,
            estado TEXT DEFAULT 'ABERTO',
            observacoes TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentos_caixa ("""

        novo = """            valor_contado REAL DEFAULT 0,
            diferenca REAL DEFAULT 0,
            estado TEXT DEFAULT 'ABERTO',
            observacoes TEXT,
            contado_tpa REAL DEFAULT 0,
            num_taloes_tpa INTEGER DEFAULT 0,
            detalhe_notas TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentos_caixa ("""

        if antigo in conteudo:
            conteudo = conteudo.replace(antigo, novo)
            log("  ✅ Colunas TPA adicionadas à tabela caixas", VERDE)
            alterado = True
        else:
            log("  ⚠️  Padrão de caixas não encontrado (pode já estar corrigido)", AMARELO)
    else:
        log("  ℹ️  Colunas TPA já existem em caixas", AZUL)

    # ---------------------------------------------------------
    # BUG 5 — autorizado_por + numero_documento em movimentos_caixa
    # ---------------------------------------------------------
    if "autorizado_por TEXT" not in conteudo.split("CREATE TABLE IF NOT EXISTS movimentos_caixa")[1].split("''')")[0] if "CREATE TABLE IF NOT EXISTS movimentos_caixa" in conteudo else True:
        antigo_mov = """            uuid TEXT,
            terminal_id TEXT,
            farmacia_id INTEGER,
            sincronizado INTEGER DEFAULT 0,
            FOREIGN KEY (caixa_id) REFERENCES caixas (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas ("""

        novo_mov = """            uuid TEXT,
            terminal_id TEXT,
            farmacia_id INTEGER,
            sincronizado INTEGER DEFAULT 0,
            autorizado_por TEXT,
            numero_documento TEXT,
            FOREIGN KEY (caixa_id) REFERENCES caixas (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas ("""

        if antigo_mov in conteudo:
            conteudo = conteudo.replace(antigo_mov, novo_mov)
            log("  ✅ autorizado_por + numero_documento adicionados a movimentos_caixa", VERDE)
            alterado = True
        else:
            log("  ⚠️  Padrão de movimentos_caixa não encontrado", AMARELO)
    else:
        log("  ℹ️  autorizado_por já existe em movimentos_caixa", AZUL)

    # ---------------------------------------------------------
    # BUG 3+4+6+7 — Novas tabelas antes de "conn.commit()"
    # na função criar_tabelas()
    # ---------------------------------------------------------
    if "CREATE TABLE IF NOT EXISTS fila_sincronizacao" not in conteudo:
        # Procurar o marcador "conn.commit()\n    conn.close()" que está no fim de criar_tabelas()
        marcador = """    conn.commit()
    conn.close()
    
    try:
        _inicializar_config_financeira()"""

        novas_tabelas = """    # ══════════════════════════════════════════════════════════
    # TABELAS ADICIONAIS (correcção de bugs)
    # ══════════════════════════════════════════════════════════
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fila_sincronizacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE,
            tipo TEXT,
            tabela_origem TEXT,
            registo_id INTEGER,
            payload TEXT,
            estado TEXT DEFAULT 'PENDENTE',
            tentativas INTEGER DEFAULT 0,
            criado_em TEXT,
            ultima_tentativa TEXT,
            enviado_em TEXT,
            ultimo_erro TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS log_sincronizacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            total_enviado INTEGER DEFAULT 0,
            total_erros INTEGER DEFAULT 0,
            duracao_segundos REAL DEFAULT 0,
            resultado TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracao_global (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT,
            atualizado_em TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS farmacias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT,
            codigo TEXT UNIQUE,
            nome TEXT,
            nif TEXT,
            endereco TEXT,
            telefone TEXT,
            email TEXT,
            responsavel TEXT,
            notas TEXT,
            activo INTEGER DEFAULT 1,
            criado_em TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS terminais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nome TEXT,
            farmacia_id INTEGER,
            criado_em TEXT,
            ultima_atividade TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transferencias_filiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referencia TEXT UNIQUE,
            data_criacao TEXT,
            data_envio TEXT,
            data_recepcao TEXT,
            farmacia_origem_id INTEGER,
            farmacia_origem_codigo TEXT,
            farmacia_origem_nome TEXT,
            farmacia_destino_id INTEGER,
            farmacia_destino_codigo TEXT,
            farmacia_destino_nome TEXT,
            utilizador_criou_id INTEGER,
            utilizador_criou_nome TEXT,
            autorizado_por TEXT,
            estado TEXT DEFAULT 'RASCUNHO',
            total_itens INTEGER DEFAULT 0,
            total_quantidade INTEGER DEFAULT 0,
            valor_estimado REAL DEFAULT 0,
            observacoes TEXT,
            uuid TEXT,
            terminal_id TEXT,
            farmacia_id INTEGER,
            sincronizado INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_transferencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transferencia_id INTEGER,
            produto_id INTEGER,
            produto_nome TEXT,
            codigo_barras TEXT,
            quantidade_enviada INTEGER,
            quantidade_recebida INTEGER DEFAULT 0,
            diferenca INTEGER DEFAULT 0,
            lote TEXT,
            validade TEXT,
            preco_custo REAL,
            subtotal REAL,
            justificacao TEXT,
            FOREIGN KEY (transferencia_id) REFERENCES transferencias_filiais (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_ibt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transferencia_id INTEGER,
            data TEXT,
            acao TEXT,
            utilizador_nome TEXT,
            estado_anterior TEXT,
            estado_novo TEXT,
            detalhes TEXT,
            FOREIGN KEY (transferencia_id) REFERENCES transferencias_filiais (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    try:
        _inicializar_config_financeira()"""

        if marcador in conteudo:
            conteudo = conteudo.replace(marcador, novas_tabelas)
            log("  ✅ 8 tabelas novas adicionadas a criar_tabelas()", VERDE)
            alterado = True
        else:
            log("  ⚠️  Marcador 'conn.commit()' não encontrado no fim de criar_tabelas()", AMARELO)
            log("     Vou tentar abordagem alternativa...", AMARELO)
            # Tentar outro padrão (mais permissivo)
            marcador2 = "    conn.commit()\n    conn.close()\n\n    try:"
            if marcador2 in conteudo:
                # Contar quantas vezes aparece — queremos o da função criar_tabelas()
                partes = conteudo.split(marcador2)
                if len(partes) >= 2:
                    # Inserir depois da primeira ocorrência (criar_tabelas está cedo no ficheiro)
                    conteudo = partes[0] + novas_tabelas + marcador2 + marcador2.join(partes[1:])
                    # Isto pode não funcionar bem; vou avisar
                    log("  ⚠️  Correcção parcial — verifica manualmente", AMARELO)
                    alterado = True
    else:
        log("  ℹ️  Tabelas novas já existem em criar_tabelas()", AZUL)

    # ---------------------------------------------------------
    # Guardar se houve alterações
    # ---------------------------------------------------------
    if alterado:
        with open(ficheiro, "w", encoding="utf-8") as f:
            f.write(conteudo)
        log("  ✅ database.py guardado", VERDE)
        return True
    else:
        log("  ℹ️  Nada a alterar em database.py", AZUL)
        return True


# ============================================================
# BUG 3b — Corrigir atualizar_totais_caixa() para calcular TPA
# ============================================================

def corrigir_atualizar_totais():
    log("\n[3b/7] A corrigir atualizar_totais_caixa() para calcular TPA...", AMARELO)
    ficheiro = "database.py"
    if not os.path.exists(ficheiro):
        log(f"  ❌ {ficheiro} não encontrado!", VERMELHO)
        return False

    with open(ficheiro, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Verificar se já foi corrigido
    if 'SELECT SUM(total) FROM vendas WHERE caixa_id = ? AND forma_pagamento = \'Multicaixa\'' in conteudo:
        log("  ℹ️  Já está corrigido", AZUL)
        return True

    # Procurar a linha antiga
    antigo = '''    cursor.execute("SELECT SUM(total) FROM vendas WHERE caixa_id = ? AND forma_pagamento = 'Dinheiro'", (caixa_id,))
    total_vendas = cursor.fetchone()[0] or 0'''

    novo = '''    cursor.execute("SELECT SUM(total) FROM vendas WHERE caixa_id = ? AND forma_pagamento = 'Dinheiro'", (caixa_id,))
    total_vendas = cursor.fetchone()[0] or 0
    
    # Calcular total TPA (Multicaixa)
    cursor.execute("SELECT SUM(total) FROM vendas WHERE caixa_id = ? AND forma_pagamento = 'Multicaixa'", (caixa_id,))
    total_tpa = cursor.fetchone()[0] or 0'''

    if antigo in conteudo:
        conteudo = conteudo.replace(antigo, novo)
        log("  ✅ Cálculo de total_tpa adicionado", VERDE)
    else:
        log("  ⚠️  Padrão de total_vendas não encontrado", AMARELO)

    # Adicionar total_tpa ao return
    antigo_return = '''    return {
        "valor_inicial": valor_inicial,
        "total_vendas": total_vendas,
        "total_sangrias": total_sangrias,
        "total_reforcos": total_reforcos,
        "valor_esperado": valor_esperado
    }'''

    novo_return = '''    return {
        "valor_inicial": valor_inicial,
        "total_vendas": total_vendas,
        "total_sangrias": total_sangrias,
        "total_reforcos": total_reforcos,
        "valor_esperado": valor_esperado,
        "total_tpa": total_tpa
    }'''

    if antigo_return in conteudo:
        conteudo = conteudo.replace(antigo_return, novo_return)
        log("  ✅ total_tpa adicionado ao retorno", VERDE)

    with open(ficheiro, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return True


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "=" * 60)
    print("  CORRECÇÃO AUTOMÁTICA — JAM SOFT")
    print("  7 bugs críticos")
    print("=" * 60)

    # Verificar que estamos na pasta certa
    if not os.path.exists("database.py") or not os.path.exists("main.py"):
        log("\n❌ ERRO: Não estás na pasta do projecto!", VERMELHO)
        log("   Corre este script da pasta 'farmacia-app'", AMARELO)
        input("\nEnter para sair...")
        return

    log("\n✅ Pasta do projecto detectada", VERDE)
    log(f"   Localização: {os.getcwd()}")

    # Correr as correcções
    corrigir_bug1()
    corrigir_database()
    corrigir_atualizar_totais()

    # Resumo
    print("\n" + "=" * 60)
    print("  RESUMO")
    print("=" * 60)
    for linha in LOG:
        print(linha)

    print("\n" + "=" * 60)
    print("  ✅ CORRECÇÃO CONCLUÍDA")
    print("=" * 60)
    print("\nPróximos passos:")
    print("1. Testar se a app arranca (INICIAR_FARMACIA.bat)")
    print("2. Se arrancar, testar venda + fecho de turno")
    print("3. Voltar ao chat e reportar resultado")

    input("\nEnter para fechar...")


if __name__ == "__main__":
    main()