import sqlite3
import bcrypt
import os
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets



# ============================================================
# ============ AGT: HASH E QR CODE ===========================
# ============================================================

def gerar_hash_factura(numero, serie, data, nif_empresa, total, cliente_nif=""):
    """
    Gera hash SHA-256 de uma factura para AGT.
    Não substitui assinatura RSA (essa virá da AGT).
    
    Ordem dos dados (padrão AGT):
    numero;serie;data;nif_empresa;total;cliente_nif
    """
    dados = f"{numero};{serie};{data};{nif_empresa};{total};{cliente_nif}"
    hash_obj = hashlib.sha256(dados.encode("utf-8"))
    return hash_obj.hexdigest().upper()


def gerar_qr_code_factura(numero, serie, hash_documento, base_url="https://jamsoft-plataforma-nthcjcruax7wmg9rqxr4qz.streamlit.app"):
    """
    Gera o conteúdo do QR code (link para verificação).
    O QR será desenhado na impressão.
    """
    url = f"{base_url}/verificar?numero={numero}&serie={serie}&hash={hash_documento}"
    return url


def guardar_hash_factura(factura_id, hash_documento, qr_code):
    """Guarda o hash e QR code de uma factura."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        UPDATE facturas
        SET hash_documento = ?, qr_code = ?
        WHERE id = ?
    """, (hash_documento, qr_code, factura_id))
    conn.commit()
    conn.close()


def obter_hash_factura(factura_id):
    """Retorna o hash guardado de uma factura."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT hash_documento, qr_code FROM facturas WHERE id = ?", (factura_id,))
    r = cur.fetchone()
    conn.close()
    return r


def conectar():
    conn = sqlite3.connect('farmacia.db')
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            nif TEXT UNIQUE,
            telefone TEXT,
            email TEXT,
            endereco TEXT,
            observacoes TEXT,
            criado_em TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            nif TEXT UNIQUE,
            telefone TEXT,
            email TEXT,
            endereco TEXT,
            data_nascimento TEXT,
            observacoes TEXT,
            criado_em TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            descricao TEXT,
            criado_em TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            codigo_barras TEXT UNIQUE,
            principio_ativo TEXT,
            laboratorio TEXT,
            preco_custo REAL,
            preco_venda REAL,
            estoque_minimo INTEGER DEFAULT 5,
            estoque_atual INTEGER DEFAULT 0,
            isento_iva INTEGER DEFAULT 0,
            fornecedor_id INTEGER,
            categoria_id INTEGER,
            FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id),
            FOREIGN KEY (categoria_id) REFERENCES categorias (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            numero_lote TEXT,
            data_validade TEXT,
            quantidade INTEGER,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            fornecedor_id INTEGER,
            numero_fatura TEXT,
            total REAL,
            observacoes TEXT,
            utilizador_id INTEGER,
            uuid TEXT,
            terminal_id TEXT,
            farmacia_id INTEGER,
            sincronizado INTEGER DEFAULT 0,
            FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            compra_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            preco_custo_unitario REAL,
            numero_lote TEXT,
            data_validade TEXT,
            subtotal REAL,
            FOREIGN KEY (compra_id) REFERENCES compras (id),
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            utilizador_id INTEGER,
            utilizador_nome TEXT,
            observacoes TEXT,
            total_itens INTEGER,
            total_diferencas INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventario_id INTEGER,
            produto_id INTEGER,
            estoque_sistema INTEGER,
            estoque_contado INTEGER,
            diferenca INTEGER,
            justificacao TEXT,
            FOREIGN KEY (inventario_id) REFERENCES inventarios (id),
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS caixas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_abertura TEXT,
            data_fecho TEXT,
            utilizador_abertura_id INTEGER,
            utilizador_abertura_nome TEXT,
            utilizador_fecho_id INTEGER,
            utilizador_fecho_nome TEXT,
            valor_inicial REAL DEFAULT 0,
            total_vendas_dinheiro REAL DEFAULT 0,
            total_tpa REAL DEFAULT 0,
            total_sangrias REAL DEFAULT 0,
            total_reforcos REAL DEFAULT 0,
            valor_esperado REAL DEFAULT 0,
            valor_contado REAL DEFAULT 0,
            diferenca REAL DEFAULT 0,
            contado_tpa REAL DEFAULT 0,
            num_taloes_tpa INTEGER DEFAULT 0,
            diferenca_tpa REAL DEFAULT 0,
            detalhe_notas TEXT,
            uuid TEXT,
            terminal_id TEXT,
            farmacia_id INTEGER,
            sincronizado INTEGER DEFAULT 0,
            estado TEXT DEFAULT 'ABERTO',
            observacoes TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentos_caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caixa_id INTEGER,
            data TEXT,
            tipo TEXT,
            valor REAL,
            descricao TEXT,
            utilizador_id INTEGER,
            utilizador_nome TEXT,
            autorizado_por TEXT,
            numero_documento TEXT,
            uuid TEXT,
            terminal_id TEXT,
            farmacia_id INTEGER,
            sincronizado INTEGER DEFAULT 0,
            FOREIGN KEY (caixa_id) REFERENCES caixas (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            total REAL,
            valor_dinheiro REAL DEFAULT 0,
            valor_tpa REAL DEFAULT 0,
            valor_transferencia REAL DEFAULT 0,
            subtotal_original REAL DEFAULT 0,
            desconto_global_valor REAL DEFAULT 0,
            autorizado_por TEXT,
            forma_pagamento TEXT,
            utilizador_id INTEGER,
            cliente_id INTEGER,
            caixa_id INTEGER,
            uuid TEXT,
            terminal_id TEXT,
            farmacia_id INTEGER,
            sincronizado INTEGER DEFAULT 0,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id),
            FOREIGN KEY (caixa_id) REFERENCES caixas (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER,
            produto_id INTEGER,
            lote_id INTEGER,
            quantidade INTEGER,
            preco_unitario REAL,
            uuid TEXT,
            terminal_id TEXT,
            farmacia_id INTEGER,
            sincronizado INTEGER DEFAULT 0,
            FOREIGN KEY (venda_id) REFERENCES vendas (id),
            FOREIGN KEY (produto_id) REFERENCES produtos (id),
            FOREIGN KEY (lote_id) REFERENCES lotes (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_venda_lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_venda_id INTEGER NOT NULL,
            lote_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL CHECK (quantidade > 0),
            FOREIGN KEY (item_venda_id) REFERENCES itens_venda (id),
            FOREIGN KEY (lote_id) REFERENCES lotes (id),
            UNIQUE (item_venda_id, lote_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS utilizadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            perfil TEXT NOT NULL DEFAULT 'farmaceutico',
            ativo INTEGER DEFAULT 1,
            criado_em TEXT,
            ultimo_login TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            utilizador_id INTEGER,
            utilizador_nome TEXT,
            acao TEXT,
            detalhes TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empresa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            nif TEXT,
            endereco TEXT,
            telefone TEXT,
            email TEXT,
            regime_fiscal TEXT DEFAULT 'GERAL',
            serie_padrao TEXT DEFAULT 'FT 2026/',
            proximo_numero INTEGER DEFAULT 1,
            serie_proforma TEXT DEFAULT 'FP 2026/',
            proximo_numero_proforma INTEGER DEFAULT 1,
            logo_path TEXT,
            criado_em TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT UNIQUE NOT NULL,
            serie TEXT NOT NULL,
            tipo TEXT DEFAULT 'FT',
            data TEXT,
            venda_id INTEGER,
            cliente_id INTEGER,
            cliente_nome TEXT,
            cliente_nif TEXT,
            cliente_endereco TEXT,
            subtotal REAL DEFAULT 0,
            total_iva REAL DEFAULT 0,
            total REAL DEFAULT 0,
            estado TEXT DEFAULT 'EMITIDA',
            motivo_anulacao TEXT,
            data_anulacao TEXT,
            utilizador_id INTEGER,
            utilizador_nome TEXT,
            forma_pagamento TEXT,
            ref_multicaixa TEXT,
            valor_dinheiro REAL DEFAULT 0,
            valor_segunda REAL DEFAULT 0,
            data_validade_proforma TEXT,
            proforma_convertida INTEGER DEFAULT 0,
            uuid TEXT,
            terminal_id TEXT,
            farmacia_id INTEGER,
            sincronizado INTEGER DEFAULT 0,
            FOREIGN KEY (venda_id) REFERENCES vendas (id),
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_factura (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factura_id INTEGER,
            produto_id INTEGER,
            descricao TEXT,
            quantidade INTEGER,
            preco_unitario REAL,
            isento_iva INTEGER DEFAULT 0,
            taxa_iva REAL DEFAULT 0,
            valor_iva REAL DEFAULT 0,
            subtotal REAL,
            desconto_percent REAL DEFAULT 0,
            desconto_valor REAL DEFAULT 0,
            FOREIGN KEY (factura_id) REFERENCES facturas (id),
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devolucoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referencia TEXT UNIQUE,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            venda_original_id INTEGER,
            factura_original TEXT,
            produto_id INTEGER NOT NULL,
            produto_nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_unitario REAL NOT NULL,
            valor_total REAL NOT NULL,
            motivo TEXT NOT NULL,
            autorizado_por TEXT NOT NULL,
            autorizado_por_id INTEGER,
            utilizador_id INTEGER,
            utilizador_nome TEXT,
            estado TEXT DEFAULT 'REGISTADA',
            lote_id INTEGER,
            uuid TEXT,
            terminal_id TEXT,
            farmacia_id INTEGER,
            sincronizado INTEGER DEFAULT 0,
            criado_em TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS depositos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referencia TEXT UNIQUE NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            valor REAL NOT NULL,
            banco TEXT NOT NULL,
            numero_comprovante TEXT NOT NULL,
            observacoes TEXT,
            turno_id INTEGER,
            gerente_id INTEGER,
            gerente_nome TEXT NOT NULL,
            estado TEXT DEFAULT 'REGISTADO',
            aprovado_por TEXT,
            data_aprovacao TEXT,
            criado_em TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saldo_farmacia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            referencia TEXT,
            descricao TEXT NOT NULL,
            saldo_anterior REAL NOT NULL,
            saldo_atual REAL NOT NULL,
            utilizador_nome TEXT NOT NULL,
            criado_em TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_financeira (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT NOT NULL,
            atualizado_em TEXT NOT NULL,
            atualizado_por TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dias_operacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT UNIQUE NOT NULL,
            hora_abertura TEXT,
            hora_fecho TEXT,
            gerente_abertura_id INTEGER,
            gerente_abertura_nome TEXT,
            gerente_fecho_id INTEGER,
            gerente_fecho_nome TEXT,
            total_turnos INTEGER DEFAULT 0,
            total_vendas REAL DEFAULT 0,
            total_dinheiro REAL DEFAULT 0,
            total_tpa REAL DEFAULT 0,
            total_pix REAL DEFAULT 0,
            total_clientes INTEGER DEFAULT 0,
            ticket_medio REAL DEFAULT 0,
            total_faltas REAL DEFAULT 0,
            total_sobras REAL DEFAULT 0,
            valor_depositar REAL DEFAULT 0,
            orcamento_dia REAL DEFAULT 0,
            percentagem_atingida REAL DEFAULT 0,
            estado TEXT DEFAULT 'ABERTO',
            observacoes TEXT,
            relatorio_z_gerado INTEGER DEFAULT 0,
            criado_em TEXT,
            uuid TEXT,
            terminal_id TEXT,
            farmacia_id INTEGER,
            sincronizado INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metas_farmacia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes TEXT UNIQUE NOT NULL,
            orcamento_mes REAL NOT NULL,
            observacoes TEXT,
            definido_por TEXT,
            criado_em TEXT,
            atualizado_em TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relatorios_guardados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            referencia TEXT,
            data_geracao TEXT,
            gerado_por TEXT,
            caminho_pdf TEXT,
            dados_json TEXT,
            criado_em TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tentativas_login (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            data TEXT NOT NULL,
            ip TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_ia_orcamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT NOT NULL,
            atualizado_em TEXT NOT NULL,
            atualizado_por TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perdas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            produto_id INTEGER,
            lote_id INTEGER,
            quantidade INTEGER,
            valor_perdido REAL,
            motivo TEXT,
            utilizador_id INTEGER,
            utilizador_nome TEXT,
            uuid TEXT,
            terminal_id TEXT,
            farmacia_id INTEGER,
            sincronizado INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nao_conformidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT UNIQUE,
            data_criacao TEXT,
            titulo TEXT,
            descricao TEXT,
            area TEXT,
            severidade TEXT,
            estado TEXT DEFAULT 'ABERTA',
            evidencia TEXT,
            criado_por_id INTEGER,
            criado_por_nome TEXT,
            data_encerramento TEXT,
            encerrado_por_nome TEXT,
            conclusao TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auditorias_realizadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            area TEXT,
            descricao TEXT,
            resultado TEXT,
            auditor_id INTEGER,
            auditor_nome TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS turnos_caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caixa_id INTEGER,
            data_abertura TEXT,
            data_fecho TEXT,
            utilizador_id INTEGER,
            utilizador_nome TEXT,
            valor_inicial REAL DEFAULT 0,
            total_vendas REAL DEFAULT 0,
            total_dinheiro REAL DEFAULT 0,
            total_tpa REAL DEFAULT 0,
            total_pix REAL DEFAULT 0,
            dinheiro_contado REAL DEFAULT 0,
            tpa_contado REAL DEFAULT 0,
            total_contado REAL DEFAULT 0,
            total_sistema REAL DEFAULT 0,
            diferenca REAL DEFAULT 0,
            estado TEXT DEFAULT 'ABERTO',
            observacoes TEXT,
            uuid TEXT,
            terminal_id TEXT,
            farmacia_id INTEGER,
            sincronizado INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detalhe_notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            turno_id INTEGER,
            tipo TEXT,
            nota_5000 INTEGER DEFAULT 0,
            nota_2000 INTEGER DEFAULT 0,
            nota_1000 INTEGER DEFAULT 0,
            nota_500 INTEGER DEFAULT 0,
            nota_200 INTEGER DEFAULT 0,
            nota_100 INTEGER DEFAULT 0,
            nota_50 INTEGER DEFAULT 0,
            nota_20 INTEGER DEFAULT 0,
            nota_10 INTEGER DEFAULT 0,
            total REAL DEFAULT 0
        )
    ''')

    # Tabelas usadas pela sincronizacao e pela identidade local da farmacia.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fila_sincronizacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            tipo TEXT NOT NULL,
            tabela_origem TEXT NOT NULL,
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
            data TEXT NOT NULL,
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
            atualizado_em TEXT,
            atualizado_por TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS farmacias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            nif TEXT,
            endereco TEXT,
            telefone TEXT,
            email TEXT,
            responsavel TEXT,
            notas TEXT,
            activo INTEGER DEFAULT 1,
            criado_em TEXT,
            ultima_sincronizacao TEXT,
            sincronizado INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS terminais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT,
            farmacia_id INTEGER,
            criado_em TEXT,
            ultima_atividade TEXT,
            uuid TEXT,
            sincronizado INTEGER DEFAULT 0
        )
    ''')

    # Tabelas IBT ficam locais e prontas para a funcionalidade existente.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transferencias_filiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referencia TEXT UNIQUE NOT NULL,
            data_criacao TEXT NOT NULL,
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
            transferencia_id INTEGER NOT NULL,
            produto_id INTEGER,
            produto_nome TEXT,
            codigo_barras TEXT,
            quantidade_enviada INTEGER DEFAULT 0,
            quantidade_recebida INTEGER DEFAULT 0,
            diferenca INTEGER DEFAULT 0,
            lote TEXT,
            validade TEXT,
            preco_custo REAL DEFAULT 0,
            subtotal REAL DEFAULT 0,
            justificacao TEXT,
            FOREIGN KEY (transferencia_id) REFERENCES transferencias_filiais(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_ibt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transferencia_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            acao TEXT NOT NULL,
            utilizador_nome TEXT,
            estado_anterior TEXT,
            estado_novo TEXT,
            detalhes TEXT,
            FOREIGN KEY (transferencia_id) REFERENCES transferencias_filiais(id)
        )
    ''')

    # Migra as bases antigas sem remover nem reescrever registos existentes.
    colunas_novas = {
        "caixas": {
            "total_tpa": "REAL DEFAULT 0",
            "contado_tpa": "REAL DEFAULT 0",
            "num_taloes_tpa": "INTEGER DEFAULT 0",
            "diferenca_tpa": "REAL DEFAULT 0",
            "detalhe_notas": "TEXT",
            "uuid": "TEXT",
            "terminal_id": "TEXT",
            "farmacia_id": "INTEGER",
            "sincronizado": "INTEGER DEFAULT 0",
        },
        "movimentos_caixa": {
            "autorizado_por": "TEXT",
            "numero_documento": "TEXT",
        },
        "fila_sincronizacao": {
            "uuid": "TEXT",
            "tipo": "TEXT",
            "tabela_origem": "TEXT",
            "registo_id": "INTEGER",
            "payload": "TEXT",
            "estado": "TEXT DEFAULT 'PENDENTE'",
            "tentativas": "INTEGER DEFAULT 0",
            "criado_em": "TEXT",
            "ultima_tentativa": "TEXT",
            "enviado_em": "TEXT",
            "ultimo_erro": "TEXT",
        },
        "log_sincronizacao": {
            "data": "TEXT",
            "total_enviado": "INTEGER DEFAULT 0",
            "total_erros": "INTEGER DEFAULT 0",
            "duracao_segundos": "REAL DEFAULT 0",
            "resultado": "TEXT",
        },
        "configuracao_global": {
            "chave": "TEXT",
            "valor": "TEXT",
            "atualizado_em": "TEXT",
            "atualizado_por": "TEXT",
        },
        "vendas": {
            "valor_dinheiro": "REAL DEFAULT 0",
            "valor_tpa": "REAL DEFAULT 0",
            "valor_transferencia": "REAL DEFAULT 0",
        },
        "facturas": {
            "valor_dinheiro": "REAL DEFAULT 0",
            "valor_segunda": "REAL DEFAULT 0",
        },
        "farmacias": {
            "uuid": "TEXT",
            "codigo": "TEXT",
            "nome": "TEXT",
            "nif": "TEXT",
            "endereco": "TEXT",
            "telefone": "TEXT",
            "email": "TEXT",
            "responsavel": "TEXT",
            "notas": "TEXT",
            "activo": "INTEGER DEFAULT 1",
            "criado_em": "TEXT",
            "ultima_sincronizacao": "TEXT",
            "sincronizado": "INTEGER DEFAULT 0",
        },
        "terminais": {
            "codigo": "TEXT",
            "nome": "TEXT",
            "farmacia_id": "INTEGER",
            "criado_em": "TEXT",
            "ultima_atividade": "TEXT",
            "uuid": "TEXT",
            "sincronizado": "INTEGER DEFAULT 0",
        },
        "transferencias_filiais": {
            "referencia": "TEXT",
            "data_criacao": "TEXT",
            "data_envio": "TEXT",
            "data_recepcao": "TEXT",
            "farmacia_origem_id": "INTEGER",
            "farmacia_origem_codigo": "TEXT",
            "farmacia_origem_nome": "TEXT",
            "farmacia_destino_id": "INTEGER",
            "farmacia_destino_codigo": "TEXT",
            "farmacia_destino_nome": "TEXT",
            "utilizador_criou_id": "INTEGER",
            "utilizador_criou_nome": "TEXT",
            "autorizado_por": "TEXT",
            "estado": "TEXT DEFAULT 'RASCUNHO'",
            "total_itens": "INTEGER DEFAULT 0",
            "total_quantidade": "INTEGER DEFAULT 0",
            "valor_estimado": "REAL DEFAULT 0",
            "observacoes": "TEXT",
            "uuid": "TEXT",
            "terminal_id": "TEXT",
            "farmacia_id": "INTEGER",
            "sincronizado": "INTEGER DEFAULT 0",
        },
        "itens_transferencia": {
            "transferencia_id": "INTEGER",
            "produto_id": "INTEGER",
            "produto_nome": "TEXT",
            "codigo_barras": "TEXT",
            "quantidade_enviada": "INTEGER DEFAULT 0",
            "quantidade_recebida": "INTEGER DEFAULT 0",
            "diferenca": "INTEGER DEFAULT 0",
            "lote": "TEXT",
            "validade": "TEXT",
            "preco_custo": "REAL DEFAULT 0",
            "subtotal": "REAL DEFAULT 0",
            "justificacao": "TEXT",
        },
        "historico_ibt": {
            "transferencia_id": "INTEGER",
            "data": "TEXT",
            "acao": "TEXT",
            "utilizador_nome": "TEXT",
            "estado_anterior": "TEXT",
            "estado_novo": "TEXT",
            "detalhes": "TEXT",
        },
        "turnos_caixa": {
            "total_vendas": "REAL DEFAULT 0",
            "total_dinheiro": "REAL DEFAULT 0",
            "total_tpa": "REAL DEFAULT 0",
            "total_pix": "REAL DEFAULT 0",
            "dinheiro_contado": "REAL DEFAULT 0",
            "tpa_contado": "REAL DEFAULT 0",
            "total_contado": "REAL DEFAULT 0",
            "total_sistema": "REAL DEFAULT 0",
            "diferenca": "REAL DEFAULT 0",
            "uuid": "TEXT",
            "terminal_id": "TEXT",
            "farmacia_id": "INTEGER",
            "sincronizado": "INTEGER DEFAULT 0",
        },
        "dias_operacao": {
            "total_tpa": "REAL DEFAULT 0",
            "uuid": "TEXT",
            "terminal_id": "TEXT",
            "farmacia_id": "INTEGER",
            "sincronizado": "INTEGER DEFAULT 0",
        },
    }
    for tabela, definicoes in colunas_novas.items():
        cursor.execute(f"PRAGMA table_info({tabela})")
        existentes = {linha[1] for linha in cursor.fetchall()}
        for coluna, definicao in definicoes.items():
            if coluna not in existentes:
                cursor.execute(
                    f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}"
                )

    # Recupera a divisao de pagamentos mistos antigos somente quando uma
    # factura ligada guarda valores cuja soma confere com o total da venda.
    cursor.execute("""
        UPDATE vendas
        SET valor_dinheiro = (
                SELECT f.valor_dinheiro FROM facturas f
                WHERE f.venda_id = vendas.id
                  AND ABS(COALESCE(f.valor_dinheiro, 0)
                        + COALESCE(f.valor_segunda, 0)
                        - COALESCE(vendas.total, 0)) < 0.01
                ORDER BY f.id DESC LIMIT 1
            ),
            valor_tpa = CASE
                WHEN forma_pagamento LIKE '%Multicaixa%' THEN (
                    SELECT f.valor_segunda FROM facturas f
                    WHERE f.venda_id = vendas.id
                      AND ABS(COALESCE(f.valor_dinheiro, 0)
                            + COALESCE(f.valor_segunda, 0)
                            - COALESCE(vendas.total, 0)) < 0.01
                    ORDER BY f.id DESC LIMIT 1
                )
                ELSE 0
            END,
            valor_transferencia = CASE
                WHEN forma_pagamento LIKE '%Transferencia%' THEN (
                    SELECT f.valor_segunda FROM facturas f
                    WHERE f.venda_id = vendas.id
                      AND ABS(COALESCE(f.valor_dinheiro, 0)
                            + COALESCE(f.valor_segunda, 0)
                            - COALESCE(vendas.total, 0)) < 0.01
                    ORDER BY f.id DESC LIMIT 1
                )
                ELSE 0
            END
        WHERE forma_pagamento LIKE 'Misto:%'
          AND COALESCE(valor_dinheiro, 0) = 0
          AND COALESCE(valor_tpa, 0) = 0
          AND COALESCE(valor_transferencia, 0) = 0
          AND EXISTS (
              SELECT 1 FROM facturas f
              WHERE f.venda_id = vendas.id
                AND ABS(COALESCE(f.valor_dinheiro, 0)
                      + COALESCE(f.valor_segunda, 0)
                      - COALESCE(vendas.total, 0)) < 0.01
                AND (COALESCE(f.valor_dinheiro, 0) <> 0
                     OR COALESCE(f.valor_segunda, 0) <> 0)
          )
    """)

    # Algumas versões antigas usavam 'ativo'; a aplicação lê 'activo'.
    colunas_farmacias = {linha[1] for linha in cursor.execute(
        "PRAGMA table_info(farmacias)").fetchall()}
    if "ativo" in colunas_farmacias and "activo" in colunas_farmacias:
        cursor.execute("UPDATE farmacias SET activo = ativo WHERE ativo IS NOT NULL")
    
    conn.commit()
    conn.close()
    
    try:
        _inicializar_config_financeira()
    except Exception as e:
        print(f"[Config Financeira] Aviso: {e}")
    
    try:
        _inicializar_config_ia()
    except Exception as e:
        print(f"[Config IA] Aviso: {e}")


# ============================================================
# ============ SEGURANCA E SENHAS ============================
# ============================================================

def gerar_hash_senha(senha, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((senha + salt).encode())
    return hash_obj.hexdigest(), salt


def verificar_senha(senha, senha_hash, salt):
    novo_hash, _ = gerar_hash_senha(senha, salt)
    return novo_hash == senha_hash


def gerar_hash_senha_bcrypt(senha):
    try:
        salt = bcrypt.gensalt(rounds=12)
        hash_bytes = bcrypt.hashpw(senha.encode('utf-8'), salt)
        return hash_bytes.decode('utf-8')
    except Exception as e:
        print(f"[Seguranca] Erro ao gerar hash bcrypt: {e}")
        return None


def verificar_senha_bcrypt(senha, hash_guardado):
    try:
        return bcrypt.checkpw(
            senha.encode('utf-8'),
            hash_guardado.encode('utf-8')
        )
    except Exception:
        return False


def e_hash_bcrypt(hash_str):
    if not hash_str:
        return False
    return hash_str.startswith("$2b$") or hash_str.startswith("$2a$") or hash_str.startswith("$2y$")


# ============================================================
# ============ TENTATIVAS DE LOGIN ===========================
# ============================================================

MAX_TENTATIVAS = 3
JANELA_BLOQUEIO = 15


def registar_tentativa_falhada(username, ip=None):
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO tentativas_login (username, data, ip)
        VALUES (?, ?, ?)
    """, (username, agora, ip))
    conn.commit()
    conn.close()


def contar_tentativas_falhadas(username):
    conn = conectar()
    cur = conn.cursor()
    limite = (datetime.now() - timedelta(minutes=JANELA_BLOQUEIO)).strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        SELECT COUNT(*) FROM tentativas_login
        WHERE username = ? AND data >= ?
    """, (username, limite))
    total = cur.fetchone()[0] or 0
    conn.close()
    return total


def esta_bloqueado(username):
    tentativas = contar_tentativas_falhadas(username)
    return tentativas >= MAX_TENTATIVAS


def tentativas_restantes(username):
    tentativas = contar_tentativas_falhadas(username)
    restantes = MAX_TENTATIVAS - tentativas
    return max(0, restantes)


def limpar_tentativas(username):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM tentativas_login WHERE username = ?", (username,))
    conn.commit()
    conn.close()


def tempo_restante_bloqueio(username):
    conn = conectar()
    cur = conn.cursor()
    limite = (datetime.now() - timedelta(minutes=JANELA_BLOQUEIO)).strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        SELECT data FROM tentativas_login
        WHERE username = ? AND data >= ?
        ORDER BY data ASC
    """, (username, limite))
    resultados = cur.fetchall()
    conn.close()
    
    if not resultados:
        return 0
    
    try:
        primeira = datetime.strptime(resultados[0][0], "%Y-%m-%d %H:%M:%S")
        expira = primeira + timedelta(minutes=JANELA_BLOQUEIO)
        restante = (expira - datetime.now()).total_seconds() / 60
        return max(0, int(restante))
    except Exception:
        return 0


def limpar_tentativas_antigas():
    conn = conectar()
    cur = conn.cursor()
    limite = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("DELETE FROM tentativas_login WHERE data < ?", (limite,))
    removidos = cur.rowcount
    conn.commit()
    conn.close()
    return removidos


# ============================================================
# ============ UTILIZADORES ==================================
# ============================================================

def criar_utilizador(nome, username, senha, perfil="farmaceutico"):
    conn = conectar()
    cursor = conn.cursor()
    senha_hash = gerar_hash_senha_bcrypt(senha)
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
            INSERT INTO utilizadores (nome, username, senha_hash, salt, perfil, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nome, username, senha_hash, "", perfil, criado_em))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def autenticar(username, senha):
    if esta_bloqueado(username):
        minutos = tempo_restante_bloqueio(username)
        return False, {
            "erro": "bloqueado",
            "minutos": minutos
        }
    
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, senha_hash, salt, perfil, ativo FROM utilizadores WHERE username = ?", (username,))
    resultado = cursor.fetchone()
    
    if not resultado:
        conn.close()
        registar_tentativa_falhada(username)
        return False, None
    
    uid, nome, senha_hash, salt, perfil, ativo = resultado
    
    if not ativo:
        conn.close()
        registar_tentativa_falhada(username)
        return False, None
    
    senha_ok = False
    migrar = False
    
    if e_hash_bcrypt(senha_hash):
        senha_ok = verificar_senha_bcrypt(senha, senha_hash)
    else:
        senha_ok = verificar_senha(senha, senha_hash, salt)
        if senha_ok:
            migrar = True
    
    if not senha_ok:
        conn.close()
        registar_tentativa_falhada(username)
        return False, None
    
    if migrar:
        try:
            novo_hash = gerar_hash_senha_bcrypt(senha)
            if novo_hash:
                cursor.execute("""
                    UPDATE utilizadores SET senha_hash = ?, salt = '' WHERE id = ?
                """, (novo_hash, uid))
                conn.commit()
                print(f"[Seguranca] Senha de '{username}' migrada para bcrypt")
        except Exception as e:
            print(f"[Seguranca] Aviso na migracao: {e}")
    
    cursor.execute("UPDATE utilizadores SET ultimo_login = ? WHERE id = ?",
                   (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), uid))
    conn.commit()
    conn.close()
    
    limpar_tentativas(username)
    
    return True, {"id": uid, "nome": nome, "username": username, "perfil": perfil}


def listar_utilizadores():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, username, perfil, ativo, criado_em, ultimo_login FROM utilizadores ORDER BY nome")
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def atualizar_utilizador(user_id, nome, perfil, ativo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('UPDATE utilizadores SET nome = ?, perfil = ?, ativo = ? WHERE id = ?',
                   (nome, perfil, ativo, user_id))
    conn.commit()
    conn.close()


def alterar_senha(user_id, nova_senha):
    conn = conectar()
    cursor = conn.cursor()
    senha_hash = gerar_hash_senha_bcrypt(nova_senha)
    cursor.execute('UPDATE utilizadores SET senha_hash = ?, salt = ? WHERE id = ?',
                   (senha_hash, "", user_id))
    conn.commit()
    conn.close()


def eliminar_utilizador(user_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM utilizadores WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def registar_auditoria(utilizador_id, utilizador_nome, acao, detalhes=""):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO auditoria (data, utilizador_id, utilizador_nome, acao, detalhes)
        VALUES (?, ?, ?, ?, ?)
    ''', (data, utilizador_id, utilizador_nome, acao, detalhes))
    conn.commit()
    conn.close()


def listar_auditoria(limite=100):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT data, utilizador_nome, acao, detalhes FROM auditoria ORDER BY id DESC LIMIT ?", (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


# ============================================================
# ============ FORNECEDORES ==================================
# ============================================================

def criar_fornecedor(nome, nif, telefone, email, endereco, observacoes=""):
    conn = conectar()
    cursor = conn.cursor()
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
            INSERT INTO fornecedores (nome, nif, telefone, email, endereco, observacoes, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nome, nif, telefone, email, endereco, observacoes, criado_em))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def listar_fornecedores():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, nif, telefone, email, endereco FROM fornecedores ORDER BY nome")
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def atualizar_fornecedor(fid, nome, nif, telefone, email, endereco, observacoes):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE fornecedores SET nome = ?, nif = ?, telefone = ?, email = ?, endereco = ?, observacoes = ?
        WHERE id = ?
    ''', (nome, nif, telefone, email, endereco, observacoes, fid))
    conn.commit()
    conn.close()


def eliminar_fornecedor(fid):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fornecedores WHERE id = ?", (fid,))
    conn.commit()
    conn.close()


def buscar_fornecedor_por_id(fid):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, nif, telefone, email, endereco, observacoes FROM fornecedores WHERE id = ?", (fid,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado


# ============================================================
# ============ CLIENTES ======================================
# ============================================================

def criar_cliente(nome, nif, telefone, email, endereco, data_nascimento, observacoes=""):
    conn = conectar()
    cursor = conn.cursor()
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
            INSERT INTO clientes (nome, nif, telefone, email, endereco, data_nascimento, observacoes, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nome, nif, telefone, email, endereco, data_nascimento, observacoes, criado_em))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def listar_clientes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, nif, telefone, email, data_nascimento FROM clientes ORDER BY nome")
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def atualizar_cliente(cid, nome, nif, telefone, email, endereco, data_nascimento, observacoes):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE clientes SET nome = ?, nif = ?, telefone = ?, email = ?, endereco = ?, data_nascimento = ?, observacoes = ?
        WHERE id = ?
    ''', (nome, nif, telefone, email, endereco, data_nascimento, observacoes, cid))
    conn.commit()
    conn.close()


def eliminar_cliente(cid):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cid,))
    conn.commit()
    conn.close()


def buscar_cliente_por_id(cid):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, nif, telefone, email, endereco, data_nascimento, observacoes FROM clientes WHERE id = ?", (cid,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado


# ============================================================
# ============ CATEGORIAS ====================================
# ============================================================

def criar_categoria(nome, descricao=""):
    conn = conectar()
    cursor = conn.cursor()
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('''
            INSERT INTO categorias (nome, descricao, criado_em)
            VALUES (?, ?, ?)
        ''', (nome, descricao, criado_em))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def listar_categorias():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, descricao FROM categorias ORDER BY nome")
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def atualizar_categoria(cat_id, nome, descricao):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('UPDATE categorias SET nome = ?, descricao = ? WHERE id = ?',
                   (nome, descricao, cat_id))
    conn.commit()
    conn.close()


def eliminar_categoria(cat_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categorias WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()


def buscar_categoria_por_id(cat_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, descricao FROM categorias WHERE id = ?", (cat_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado


# ============================================================
# ============ PRODUTOS ======================================
# ============================================================

def inserir_produto_completo(nome, codigo, principio, laboratorio, preco_custo, preco_venda,
                              estoque_minimo, isento_iva=0, fornecedor_id=None, categoria_id=None):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO produtos (nome, codigo_barras, principio_ativo, laboratorio, preco_custo, preco_venda,
                              estoque_minimo, isento_iva, fornecedor_id, categoria_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nome, codigo, principio, laboratorio, preco_custo, preco_venda,
          estoque_minimo, isento_iva, fornecedor_id, categoria_id))
    conn.commit()
    conn.close()


def listar_produtos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, codigo_barras, preco_venda, estoque_atual, estoque_minimo, isento_iva FROM produtos ORDER BY nome")
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def listar_produtos_completos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, codigo_barras, preco_custo, preco_venda, estoque_atual FROM produtos ORDER BY nome")
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def buscar_por_codigo(codigo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco_venda, estoque_atual, isento_iva FROM produtos WHERE codigo_barras = ?", (codigo,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado


def buscar_produto_por_id(pid):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, codigo_barras, preco_custo, preco_venda, estoque_atual FROM produtos WHERE id = ?", (pid,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado


def aumentar_estoque(produto_id, quantidade):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE produtos SET estoque_atual = estoque_atual + ? WHERE id = ?", (quantidade, produto_id))
    conn.commit()
    conn.close()


def ajustar_estoque(produto_id, novo_estoque):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE produtos SET estoque_atual = ? WHERE id = ?", (novo_estoque, produto_id))
    conn.commit()
    conn.close()


def adicionar_lote(produto_id, numero_lote, data_validade, quantidade):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO lotes (produto_id, numero_lote, data_validade, quantidade) VALUES (?, ?, ?, ?)",
                   (produto_id, numero_lote, data_validade, quantidade))
    conn.commit()
    conn.close()


# ============================================================
# ============ FEFO ==========================================
# ============================================================

def listar_lotes_fefo(produto_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, numero_lote, data_validade, quantidade
        FROM lotes
        WHERE produto_id = ? AND quantidade > 0
        ORDER BY data_validade ASC
    ''', (produto_id,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def dar_baixa_estoque_fefo(produto_id, quantidade):
    lotes = listar_lotes_fefo(produto_id)
    restante = quantidade
    retirados = []
    
    conn = conectar()
    cursor = conn.cursor()
    
    for lote in lotes:
        if restante <= 0:
            break
        lote_id, num_lote, validade, qtd_lote = lote
        
        if qtd_lote >= restante:
            cursor.execute("UPDATE lotes SET quantidade = quantidade - ? WHERE id = ?",
                           (restante, lote_id))
            retirados.append((lote_id, num_lote, restante))
            restante = 0
        else:
            cursor.execute("UPDATE lotes SET quantidade = 0 WHERE id = ?", (lote_id,))
            retirados.append((lote_id, num_lote, qtd_lote))
            restante -= qtd_lote
    
    cursor.execute("UPDATE produtos SET estoque_atual = estoque_atual - ? WHERE id = ?",
                   (quantidade, produto_id))
    
    conn.commit()
    conn.close()
    return retirados


def lotes_para_relatorio_fefo():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.nome, p.codigo_barras, l.numero_lote, l.data_validade, l.quantidade
        FROM lotes l
        JOIN produtos p ON p.id = l.produto_id
        WHERE l.quantidade > 0
        ORDER BY l.data_validade ASC
    ''')
    resultado = cursor.fetchall()
    conn.close()
    return resultado


# ============================================================
# ============ IDENTIDADE EM OPERACOES =======================
# ============================================================

def _obter_identidade_operacao():
    try:
        from identidade import (gerar_uuid, obter_terminal_codigo,
                                  obter_farmacia_id)
        return (gerar_uuid(), obter_terminal_codigo(), obter_farmacia_id())
    except Exception:
        return (None, None, None)

    # ============================================================
# ============ COMPRAS =======================================
# ============================================================

def criar_compra(fornecedor_id, numero_fatura, total, observacoes, utilizador_id):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    u, term, farm = _obter_identidade_operacao()
    
    cursor.execute("""
        INSERT INTO compras (data, fornecedor_id, numero_fatura, total,
                              observacoes, utilizador_id, uuid, terminal_id,
                              farmacia_id, sincronizado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (data, fornecedor_id, numero_fatura, total, observacoes,
          utilizador_id, u, term, farm))
    compra_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return compra_id


def adicionar_item_compra(compra_id, produto_id, quantidade, preco_custo_unitario,
                            numero_lote, data_validade):
    conn = conectar()
    cursor = conn.cursor()
    subtotal = quantidade * preco_custo_unitario
    cursor.execute('''
        INSERT INTO itens_compra (compra_id, produto_id, quantidade, preco_custo_unitario,
                                    numero_lote, data_validade, subtotal)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (compra_id, produto_id, quantidade, preco_custo_unitario,
          numero_lote, data_validade, subtotal))
    conn.commit()
    conn.close()
    aumentar_estoque(produto_id, quantidade)
    adicionar_lote(produto_id, numero_lote, data_validade, quantidade)
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE produtos SET preco_custo = ? WHERE id = ?", (preco_custo_unitario, produto_id))
    conn.commit()
    conn.close()


def listar_compras(limite=100):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, c.data, f.nome, c.numero_fatura, c.total
        FROM compras c
        LEFT JOIN fornecedores f ON f.id = c.fornecedor_id
        ORDER BY c.id DESC LIMIT ?
    ''', (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def listar_itens_compra(compra_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ic.id, p.nome, ic.quantidade, ic.preco_custo_unitario,
               ic.numero_lote, ic.data_validade, ic.subtotal
        FROM itens_compra ic
        JOIN produtos p ON p.id = ic.produto_id
        WHERE ic.compra_id = ?
        ORDER BY ic.id
    ''', (compra_id,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


# ============================================================
# ============ INVENTARIO ====================================
# ============================================================

def criar_inventario(utilizador_id, utilizador_nome, observacoes, total_itens, total_diferencas):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO inventarios (data, utilizador_id, utilizador_nome, observacoes, total_itens, total_diferencas)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data, utilizador_id, utilizador_nome, observacoes, total_itens, total_diferencas))
    inv_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return inv_id


def adicionar_item_inventario(inventario_id, produto_id, estoque_sistema, estoque_contado, diferenca, justificacao):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO itens_inventario (inventario_id, produto_id, estoque_sistema,
                                        estoque_contado, diferenca, justificacao)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (inventario_id, produto_id, estoque_sistema, estoque_contado, diferenca, justificacao))
    conn.commit()
    conn.close()


def listar_inventarios(limite=50):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, data, utilizador_nome, total_itens, total_diferencas
        FROM inventarios
        ORDER BY id DESC LIMIT ?
    ''', (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def listar_itens_inventario(inventario_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ii.id, p.nome, ii.estoque_sistema, ii.estoque_contado,
               ii.diferenca, ii.justificacao
        FROM itens_inventario ii
        JOIN produtos p ON p.id = ii.produto_id
        WHERE ii.inventario_id = ?
        ORDER BY ii.id
    ''', (inventario_id,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


# ============================================================
# ============ CAIXA =========================================
# ============================================================

def caixa_aberto():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, data_abertura, utilizador_abertura_nome, valor_inicial FROM caixas WHERE estado = 'ABERTO' LIMIT 1")
    resultado = cursor.fetchone()
    conn.close()
    return resultado


def abrir_caixa(utilizador_id, utilizador_nome, valor_inicial):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO caixas (data_abertura, utilizador_abertura_id, utilizador_abertura_nome,
                             valor_inicial, valor_esperado, estado)
        VALUES (?, ?, ?, ?, ?, 'ABERTO')
    ''', (data, utilizador_id, utilizador_nome, valor_inicial, valor_inicial))
    caixa_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return caixa_id


def registar_movimento_caixa(caixa_id, tipo, valor, descricao,
                                utilizador_id, utilizador_nome):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    u, term, farm = _obter_identidade_operacao()
    
    cursor.execute("""
        INSERT INTO movimentos_caixa (caixa_id, data, tipo, valor, descricao,
                                        utilizador_id, utilizador_nome, uuid,
                                        terminal_id, farmacia_id, sincronizado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (caixa_id, data, tipo, valor, descricao, utilizador_id,
          utilizador_nome, u, term, farm))
    conn.commit()
    conn.close()


def atualizar_totais_caixa(caixa_id):
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(SUM(
            CASE WHEN forma_pagamento = 'Dinheiro' THEN total
                 ELSE COALESCE(valor_dinheiro, 0) END
        ), 0)
        FROM vendas WHERE caixa_id = ?
    """, (caixa_id,))
    total_vendas = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT COALESCE(SUM(
            CASE WHEN forma_pagamento = 'Multicaixa' THEN total
                 ELSE COALESCE(valor_tpa, 0) END
        ), 0)
        FROM vendas WHERE caixa_id = ?
    """, (caixa_id,))
    total_tpa = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(valor) FROM movimentos_caixa WHERE caixa_id = ? AND tipo = 'SANGRIA'", (caixa_id,))
    total_sangrias = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(valor) FROM movimentos_caixa WHERE caixa_id = ? AND tipo = 'REFORCO'", (caixa_id,))
    total_reforcos = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT valor_inicial FROM caixas WHERE id = ?", (caixa_id,))
    valor_inicial = cursor.fetchone()[0] or 0
    
    valor_esperado = valor_inicial + total_vendas + total_reforcos - total_sangrias
    
    cursor.execute('''
        UPDATE caixas SET total_vendas_dinheiro = ?, total_tpa = ?,
            total_sangrias = ?, total_reforcos = ?, valor_esperado = ?
        WHERE id = ?
    ''', (total_vendas, total_tpa, total_sangrias, total_reforcos,
          valor_esperado, caixa_id))
    
    conn.commit()
    conn.close()
    
    return {
        "valor_inicial": valor_inicial,
        "total_vendas": total_vendas,
        "total_tpa": total_tpa,
        "total_sangrias": total_sangrias,
        "total_reforcos": total_reforcos,
        "valor_esperado": valor_esperado
    }


def fechar_caixa(caixa_id, utilizador_id, utilizador_nome, valor_contado,
                  observacoes="", contado_tpa=0, num_taloes_tpa=0,
                  detalhe_notas=None):
    """
    Fecha o caixa com contagem detalhada.

    valor_contado: total das notas contadas (cash)
    contado_tpa:   total dos talões TPA
    num_taloes_tpa: nº de talões TPA
    detalhe_notas: string JSON com {nota: quantidade, ...}
    """
    import json as _json

    dados = atualizar_totais_caixa(caixa_id)
    valor_esperado_cash = dados["valor_esperado"]
    diferenca_cash = valor_contado - valor_esperado_cash

    # Calcular esperado TPA
    esperado_tpa = dados.get("total_tpa", 0) or 0
    diferenca_tpa = contado_tpa - esperado_tpa

    # Guardar detalhe notas como JSON
    detalhe_json = None
    if detalhe_notas:
        try:
            detalhe_json = _json.dumps(detalhe_notas)
        except Exception:
            detalhe_json = None

    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute('''
            UPDATE caixas SET
                data_fecho = ?,
                utilizador_fecho_id = ?,
                utilizador_fecho_nome = ?,
                valor_contado = ?,
                diferenca = ?,
                diferenca_tpa = ?,
                estado = 'FECHADO',
                observacoes = ?,
                contado_tpa = ?,
                num_taloes_tpa = ?,
                detalhe_notas = ?
            WHERE id = ?
        ''', (data, utilizador_id, utilizador_nome,
              valor_contado, diferenca_cash, diferenca_tpa, observacoes,
              contado_tpa, num_taloes_tpa, detalhe_json,
              caixa_id))
        conn.commit()
    except Exception as e:
        # Fallback se as colunas novas nao existirem
        print(f"[FechoCaixa] Aviso - colunas novas nao existem: {e}")
        cursor.execute('''
            UPDATE caixas SET
                data_fecho = ?,
                utilizador_fecho_id = ?,
                utilizador_fecho_nome = ?,
                valor_contado = ?,
                diferenca = ?,
                estado = 'FECHADO',
                observacoes = ?
            WHERE id = ?
        ''', (data, utilizador_id, utilizador_nome,
              valor_contado, diferenca_cash, observacoes,
              caixa_id))
        conn.commit()
    finally:
        conn.close()

    return {
        "esperado": valor_esperado_cash,
        "contado": valor_contado,
        "diferenca": diferenca_cash,
        "esperado_tpa": esperado_tpa,
        "contado_tpa": contado_tpa,
        "diferenca_tpa": diferenca_tpa,
        "num_taloes_tpa": num_taloes_tpa,
    }


def listar_caixas(limite=50):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, data_abertura, data_fecho, utilizador_abertura_nome,
               valor_inicial, valor_esperado, valor_contado, diferenca, estado
        FROM caixas
        ORDER BY id DESC LIMIT ?
    ''', (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def listar_movimentos_caixa(caixa_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT data, tipo, valor, descricao, utilizador_nome
        FROM movimentos_caixa
        WHERE caixa_id = ?
        ORDER BY id
    ''', (caixa_id,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


# ============================================================
# ============ VENDAS ========================================
# ============================================================

def registrar_venda(total, forma_pagamento, utilizador_id=None,
                     cliente_id=None, caixa_id=None):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    u, term, farm = _obter_identidade_operacao()
    
    cursor.execute("""
        INSERT INTO vendas (data, total, forma_pagamento, utilizador_id,
                             cliente_id, caixa_id, uuid, terminal_id,
                             farmacia_id, sincronizado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (data, total, forma_pagamento, utilizador_id, cliente_id,
          caixa_id, u, term, farm))
    venda_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return venda_id


def registrar_item_venda(venda_id, produto_id, lote_id, quantidade, preco_unitario):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO itens_venda (venda_id, produto_id, lote_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?, ?)",
                   (venda_id, produto_id, lote_id, quantidade, preco_unitario))
    conn.commit()
    conn.close()


def listar_vendas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, data, total, forma_pagamento FROM vendas ORDER BY id DESC LIMIT 100")
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def listar_vendas_cliente(cliente_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT v.id, v.data, v.total, v.forma_pagamento
        FROM vendas v
        WHERE v.cliente_id = ?
        ORDER BY v.id DESC
    ''', (cliente_id,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def total_vendas_dia():
    conn = conectar()
    cursor = conn.cursor()
    hoje = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT SUM(total) FROM vendas WHERE data LIKE ?", (f"{hoje}%",))
    resultado = cursor.fetchone()[0] or 0
    conn.close()
    return resultado


# ============================================================
# ============ FISCAL - EMPRESA E FACTURAS ===================
# ============================================================

def obter_empresa():
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, nome, nif, endereco, telefone, email, regime_fiscal,
                   serie_padrao, proximo_numero, logo_path,
                   COALESCE(serie_proforma, 'FP 2026/'),
                   COALESCE(proximo_numero_proforma, 1)
            FROM empresa LIMIT 1
        ''')
        resultado = cursor.fetchone()
        conn.close()
        return resultado
    except Exception:
        cursor.execute('''
            SELECT id, nome, nif, endereco, telefone, email, regime_fiscal,
                   serie_padrao, proximo_numero
            FROM empresa LIMIT 1
        ''')
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return resultado + (None, "FP 2026/", 1)
        return None


def guardar_empresa(nome, nif, endereco, telefone, email, regime_fiscal, serie_padrao, proximo_numero):
    conn = conectar()
    cursor = conn.cursor()
    
    existente = obter_empresa()
    if existente:
        cursor.execute('''
            UPDATE empresa SET nome = ?, nif = ?, endereco = ?, telefone = ?, email = ?,
                                regime_fiscal = ?, serie_padrao = ?, proximo_numero = ?
            WHERE id = ?
        ''', (nome, nif, endereco, telefone, email, regime_fiscal, serie_padrao, proximo_numero, existente[0]))
    else:
        criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO empresa (nome, nif, endereco, telefone, email, regime_fiscal, serie_padrao, proximo_numero, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nome, nif, endereco, telefone, email, regime_fiscal, serie_padrao, proximo_numero, criado_em))
    
    conn.commit()
    conn.close()


def proximo_numero_factura():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, serie_padrao, proximo_numero FROM empresa LIMIT 1")
    resultado = cursor.fetchone()
    
    if not resultado:
        conn.close()
        return None, None
    
    emp_id, serie, prox = resultado
    numero_completo = f"{serie}{prox:05d}"
    
    cursor.execute("UPDATE empresa SET proximo_numero = proximo_numero + 1 WHERE id = ?", (emp_id,))
    conn.commit()
    conn.close()
    
    return serie, numero_completo


def criar_factura(serie, numero, tipo, venda_id, cliente_id, cliente_nome,
                   cliente_nif, cliente_endereco, subtotal, total_iva,
                   total, utilizador_id, utilizador_nome,
                   forma_pagamento=None, ref_multicaixa=None,
                   valor_dinheiro=None, valor_segunda=None):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    u, term, farm = _obter_identidade_operacao()
    
    if valor_dinheiro is None:
        valor_dinheiro = total if forma_pagamento == "Dinheiro" else 0
    if valor_segunda is None:
        valor_segunda = 0
    
    cursor.execute("""
        INSERT INTO facturas (numero, serie, tipo, data, venda_id, cliente_id,
                               cliente_nome, cliente_nif, cliente_endereco,
                               subtotal, total_iva, total, utilizador_id,
                               utilizador_nome, forma_pagamento, ref_multicaixa,
                               valor_dinheiro, valor_segunda,
                               uuid, terminal_id, farmacia_id, sincronizado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (numero, serie, tipo, data, venda_id, cliente_id, cliente_nome,
          cliente_nif, cliente_endereco, subtotal, total_iva, total,
          utilizador_id, utilizador_nome, forma_pagamento, ref_multicaixa,
          valor_dinheiro, valor_segunda,
          u, term, farm))
    factura_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return factura_id


def adicionar_item_factura(factura_id, produto_id, descricao, quantidade, preco_unitario,
                            isento_iva, taxa_iva, valor_iva, subtotal):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO itens_factura (factura_id, produto_id, descricao, quantidade, preco_unitario,
                                     isento_iva, taxa_iva, valor_iva, subtotal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (factura_id, produto_id, descricao, quantidade, preco_unitario,
          isento_iva, taxa_iva, valor_iva, subtotal))
    conn.commit()
    conn.close()


def listar_facturas(limite=100):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, numero, tipo, data, cliente_nome, total, estado
        FROM facturas
        WHERE tipo = 'FT' OR tipo IS NULL OR tipo = ''
        ORDER BY id DESC LIMIT ?
    ''', (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def buscar_factura_por_id(fid):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, numero, serie, tipo, data, cliente_nome, cliente_nif, cliente_endereco,
               subtotal, total_iva, total, estado, motivo_anulacao,
               forma_pagamento, ref_multicaixa,
               COALESCE(valor_dinheiro, 0),
               COALESCE(valor_segunda, 0)
        FROM facturas WHERE id = ?
    ''', (fid,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado


def listar_itens_factura(factura_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT descricao, quantidade, preco_unitario, isento_iva, taxa_iva, valor_iva, subtotal
        FROM itens_factura
        WHERE factura_id = ?
        ORDER BY id
    ''', (factura_id,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def obter_itens_factura_com_desconto(factura_id):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT descricao, quantidade, preco_unitario, isento_iva, taxa_iva,
                   valor_iva, subtotal, desconto_percent, desconto_valor
            FROM itens_factura WHERE factura_id = ? ORDER BY id
        ''', (factura_id,))
        resultado = cursor.fetchall()
        conn.close()
        return resultado
    except Exception:
        cursor.execute('''
            SELECT descricao, quantidade, preco_unitario, isento_iva, taxa_iva,
                   valor_iva, subtotal
            FROM itens_factura WHERE factura_id = ? ORDER BY id
        ''', (factura_id,))
        resultado = cursor.fetchall()
        conn.close()
        return [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], 0, 0) for r in resultado]


def anular_factura(factura_id, motivo, utilizador_id, utilizador_nome):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        UPDATE facturas SET estado = 'ANULADA', motivo_anulacao = ?, data_anulacao = ?
        WHERE id = ?
    ''', (motivo, data, factura_id))
    conn.commit()
    conn.close()


# ============================================================
# ============ PROFORMAS =====================================
# ============================================================

def obter_serie_proforma():
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute("SELECT serie_proforma FROM empresa LIMIT 1")
        r = cur.fetchone()
        conn.close()
        if r and r[0]:
            return r[0]
        return "FP 2026/"
    except Exception:
        conn.close()
        return "FP 2026/"


def proximo_numero_proforma():
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, COALESCE(serie_proforma, 'FP 2026/'),
                   COALESCE(proximo_numero_proforma, 1)
            FROM empresa LIMIT 1
        """)
        r = cur.fetchone()
        
        if not r:
            conn.close()
            return None, None
        
        emp_id, serie, prox = r
        numero_completo = f"{serie}{prox:05d}"
        
        cur.execute("UPDATE empresa SET proximo_numero_proforma = proximo_numero_proforma + 1 WHERE id = ?", (emp_id,))
        conn.commit()
        conn.close()
        
        return serie, numero_completo
    except Exception as e:
        print(f"[Proforma] Erro: {e}")
        conn.close()
        return None, None


def criar_proforma(serie, numero, venda_id, cliente_id, cliente_nome,
                    cliente_nif, cliente_endereco, subtotal, total_iva,
                    total, utilizador_id, utilizador_nome,
                    forma_pagamento=None, ref_multicaixa=None):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        validade = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    except Exception:
        validade = None
    
    u, term, farm = _obter_identidade_operacao()
    
    try:
        cursor.execute("""
            INSERT INTO facturas (numero, serie, tipo, data, venda_id, cliente_id,
                                   cliente_nome, cliente_nif, cliente_endereco,
                                   subtotal, total_iva, total, utilizador_id,
                                   utilizador_nome, forma_pagamento, ref_multicaixa,
                                   data_validade_proforma,
                                   uuid, terminal_id, farmacia_id, sincronizado)
            VALUES (?, ?, 'FP', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (numero, serie, data, venda_id, cliente_id, cliente_nome,
              cliente_nif, cliente_endereco, subtotal, total_iva, total,
              utilizador_id, utilizador_nome, forma_pagamento, ref_multicaixa,
              validade, u, term, farm))
        fid = cursor.lastrowid
        conn.commit()
        conn.close()
        return fid
    except Exception as e:
        print(f"[Proforma] Erro ao criar: {e}")
        conn.close()
        return None


def listar_proformas(limite=100):
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, numero, data, cliente_nome, total, estado,
                   COALESCE(data_validade_proforma, '-')
            FROM facturas
            WHERE tipo = 'FP'
            ORDER BY id DESC LIMIT ?
        """, (limite,))
        resultado = cur.fetchall()
        conn.close()
        return resultado
    except Exception as e:
        print(f"[Proforma] Erro ao listar: {e}")
        conn.close()
        return []


def buscar_proforma_por_id(fid):
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, numero, serie, tipo, data, cliente_nome, cliente_nif,
                   cliente_endereco, subtotal, total_iva, total, estado,
                   motivo_anulacao, forma_pagamento, ref_multicaixa,
                   COALESCE(data_validade_proforma, '-')
            FROM facturas WHERE id = ? AND tipo = 'FP'
        """, (fid,))
        r = cur.fetchone()
        conn.close()
        return r
    except Exception:
        conn.close()
        return None


def anular_proforma(proforma_id, motivo, utilizador_id, utilizador_nome):
    conn = conectar()
    cur = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        UPDATE facturas 
        SET estado = 'ANULADA', motivo_anulacao = ?, data_anulacao = ?
        WHERE id = ? AND tipo = 'FP'
    """, (motivo, data, proforma_id))
    conn.commit()
    conn.close()


def converter_proforma_em_factura(proforma_id, utilizador_id, utilizador_nome):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        UPDATE facturas SET proforma_convertida = 1 
        WHERE id = ? AND tipo = 'FP'
    """, (proforma_id,))
    conn.commit()
    conn.close()


# ============================================================
# ============ VALIDADE E ESTOQUE ============================
# ============================================================

def produtos_validade_proxima(dias=90):
    conn = conectar()
    cursor = conn.cursor()
    limite = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")
    hoje = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''
        SELECT p.nome, l.numero_lote, l.data_validade, l.quantidade
        FROM lotes l
        JOIN produtos p ON p.id = l.produto_id
        WHERE l.data_validade <= ? AND l.data_validade >= ? AND l.quantidade > 0
        ORDER BY l.data_validade
    ''', (limite, hoje))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def produtos_estoque_baixo():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT nome, codigo_barras, estoque_atual, estoque_minimo
        FROM produtos
        WHERE estoque_atual <= estoque_minimo
        ORDER BY estoque_atual
    ''')
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def migrar_tabela_facturas():
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(facturas)")
        colunas = [c[1] for c in cursor.fetchall()]
        
        if "forma_pagamento" not in colunas:
            cursor.execute("ALTER TABLE facturas ADD COLUMN forma_pagamento TEXT")
            print("[Migracao] Coluna 'forma_pagamento' adicionada em facturas")
        
        if "ref_multicaixa" not in colunas:
            cursor.execute("ALTER TABLE facturas ADD COLUMN ref_multicaixa TEXT")
            print("[Migracao] Coluna 'ref_multicaixa' adicionada em facturas")
        
        if "data_validade_proforma" not in colunas:
            cursor.execute("ALTER TABLE facturas ADD COLUMN data_validade_proforma TEXT")
            print("[Migracao] Coluna 'data_validade_proforma' adicionada em facturas")
        
        if "proforma_convertida" not in colunas:
            cursor.execute("ALTER TABLE facturas ADD COLUMN proforma_convertida INTEGER DEFAULT 0")
            print("[Migracao] Coluna 'proforma_convertida' adicionada em facturas")
                
        if "valor_dinheiro" not in colunas:
            cursor.execute("ALTER TABLE facturas ADD COLUMN valor_dinheiro REAL DEFAULT 0")
            print("[Migracao] Coluna 'valor_dinheiro' adicionada")
        
        if "valor_segunda" not in colunas:
            cursor.execute("ALTER TABLE facturas ADD COLUMN valor_segunda REAL DEFAULT 0")
            print("[Migracao] Coluna 'valor_segunda' adicionada")    
        
        cursor.execute("PRAGMA table_info(empresa)")
        colunas_emp = [c[1] for c in cursor.fetchall()]
        
        if "serie_proforma" not in colunas_emp:
            cursor.execute("ALTER TABLE empresa ADD COLUMN serie_proforma TEXT DEFAULT 'FP 2026/'")
            print("[Migracao] Coluna 'serie_proforma' adicionada em empresa")
        
        if "proximo_numero_proforma" not in colunas_emp:
            cursor.execute("ALTER TABLE empresa ADD COLUMN proximo_numero_proforma INTEGER DEFAULT 1")
            print("[Migracao] Coluna 'proximo_numero_proforma' adicionada em empresa")
        
        if "logo_path" not in colunas_emp:
            cursor.execute("ALTER TABLE empresa ADD COLUMN logo_path TEXT")
            print("[Migracao] Coluna 'logo_path' adicionada em empresa")
        
        cursor.execute("PRAGMA table_info(itens_factura)")
        colunas_if = [c[1] for c in cursor.fetchall()]
        
        if "desconto_percent" not in colunas_if:
            cursor.execute("ALTER TABLE itens_factura ADD COLUMN desconto_percent REAL DEFAULT 0")
            print("[Migracao] Coluna 'desconto_percent' adicionada em itens_factura")
        
        if "desconto_valor" not in colunas_if:
            cursor.execute("ALTER TABLE itens_factura ADD COLUMN desconto_valor REAL DEFAULT 0")
            print("[Migracao] Coluna 'desconto_valor' adicionada em itens_factura")
        
        cursor.execute("PRAGMA table_info(vendas)")
        colunas_v = [c[1] for c in cursor.fetchall()]
        
        if "subtotal_original" not in colunas_v:
            cursor.execute("ALTER TABLE vendas ADD COLUMN subtotal_original REAL DEFAULT 0")
            print("[Migracao] Coluna 'subtotal_original' adicionada em vendas")
        
        if "desconto_global_valor" not in colunas_v:
            cursor.execute("ALTER TABLE vendas ADD COLUMN desconto_global_valor REAL DEFAULT 0")
            print("[Migracao] Coluna 'desconto_global_valor' adicionada em vendas")
        
        if "autorizado_por" not in colunas_v:
            cursor.execute("ALTER TABLE vendas ADD COLUMN autorizado_por TEXT")
            print("[Migracao] Coluna 'autorizado_por' adicionada em vendas")
        
        for tabela in ["vendas", "compras", "perdas", "movimentos_caixa", "facturas", "itens_venda"]:
            try:
                cursor.execute(f"PRAGMA table_info({tabela})")
                cols = [c[1] for c in cursor.fetchall()]
                if "uuid" not in cols:
                    cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN uuid TEXT")
                if "terminal_id" not in cols:
                    cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN terminal_id TEXT")
                if "farmacia_id" not in cols:
                    cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN farmacia_id INTEGER")
                if "sincronizado" not in cols:
                    cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN sincronizado INTEGER DEFAULT 0")
            except Exception:
                pass
    # ─── Campos AGT (hash, QR, assinatura) ───
        for coluna, tipo in [
            ("hash_documento", "TEXT"),
            ("hash_anterior", "TEXT"), 
            ("qr_code", "TEXT"),
            ("assinatura_digital", "TEXT"),
            ("numero_validacao_agt", "TEXT"),
            ("data_validacao_agt", "TEXT"),
        ]:
            if coluna not in colunas:
                cursor.execute(f"ALTER TABLE facturas ADD COLUMN {coluna} {tipo}")
                print(f"[Migracao] Coluna '{coluna}' adicionada em facturas")

        # ─── Tabela de configuração AGT ───
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_agt (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_validacao TEXT,
                chave_rsa_path TEXT,
                activo INTEGER DEFAULT 0,
                data_activacao TEXT,
                ativado_por TEXT,
                observacoes TEXT
            )
        """)
        print("[Migracao] Tabela 'config_agt' criada/verificada")


        conn.commit()
    except Exception as e:
        print(f"[Migracao] Erro: {e}")
    finally:
        conn.close()


def guardar_logo_empresa(caminho_logo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE empresa SET logo_path = ?", (caminho_logo,))
    conn.commit()
    conn.close()


def obter_logo_empresa():
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT logo_path FROM empresa LIMIT 1")
        resultado = cursor.fetchone()
        conn.close()
        if resultado and resultado[0]:
            return resultado[0]
        return None
    except Exception:
        conn.close()
        return None


# ============================================================
# ============ PERDAS ========================================
# ============================================================

def registar_perda(tipo, produto_id, lote_id, quantidade, valor_perdido,
                    motivo, utilizador_id, utilizador_nome):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    u, term, farm = _obter_identidade_operacao()
    
    cursor.execute("""
        INSERT INTO perdas (data, tipo, produto_id, lote_id, quantidade,
                             valor_perdido, motivo, utilizador_id,
                             utilizador_nome, uuid, terminal_id,
                             farmacia_id, sincronizado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (data, tipo, produto_id, lote_id, quantidade, valor_perdido,
          motivo, utilizador_id, utilizador_nome, u, term, farm))
    conn.commit()
    conn.close()


def listar_perdas(limite=100):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.data, p.tipo, pr.nome, p.quantidade, p.valor_perdido,
               p.motivo, p.utilizador_nome
        FROM perdas p
        LEFT JOIN produtos pr ON pr.id = p.produto_id
        ORDER BY p.id DESC
        LIMIT ?
    ''', (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def resumo_perdas_mes(mes=None):
    if mes is None:
        mes = datetime.now().strftime("%Y-%m")
    
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*), COALESCE(SUM(valor_perdido), 0)
        FROM perdas
        WHERE strftime('%Y-%m', data) = ?
    ''', (mes,))
    total_n, total_valor = cursor.fetchone()
    
    cursor.execute('''
        SELECT tipo, COUNT(*), COALESCE(SUM(valor_perdido), 0)
        FROM perdas
        WHERE strftime('%Y-%m', data) = ?
        GROUP BY tipo
        ORDER BY SUM(valor_perdido) DESC
    ''', (mes,))
    por_tipo = cursor.fetchall()
    
    conn.close()
    return {
        "total_n": total_n,
        "total_valor": total_valor,
        "por_tipo": por_tipo,
        "mes": mes
    }


def listar_perdas_mes(mes=None):
    if mes is None:
        mes = datetime.now().strftime("%Y-%m")
    
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.data, p.tipo, pr.nome, p.quantidade, p.valor_perdido,
               p.motivo, p.utilizador_nome
        FROM perdas p
        LEFT JOIN produtos pr ON pr.id = p.produto_id
        WHERE strftime('%Y-%m', p.data) = ?
        ORDER BY p.id DESC
    ''', (mes,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def listar_perdas_tipo(tipo, limite=50):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.data, pr.nome, p.quantidade, p.valor_perdido, p.motivo, p.utilizador_nome
        FROM perdas p
        LEFT JOIN produtos pr ON pr.id = p.produto_id
        WHERE p.tipo = ?
        ORDER BY p.id DESC
        LIMIT ?
    ''', (tipo, limite))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def dar_baixa_lote(lote_id, quantidade):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE lotes SET quantidade = quantidade - ? WHERE id = ?",
                   (quantidade, lote_id))
    conn.commit()
    conn.close()


def obter_produto_com_lotes(produto_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco_custo, preco_venda, estoque_atual FROM produtos WHERE id = ?", (produto_id,))
    produto = cursor.fetchone()
    
    if produto:
        cursor.execute("SELECT id, numero_lote, data_validade, quantidade FROM lotes WHERE produto_id = ? AND quantidade > 0 ORDER BY data_validade", (produto_id,))
        lotes = cursor.fetchall()
    else:
        lotes = []
    
    conn.close()
    return produto, lotes


def obter_produto_por_codigo_com_id(codigo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco_custo, preco_venda, estoque_atual FROM produtos WHERE codigo_barras = ?", (codigo,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado


def aumentar_estoque_produto(produto_id, quantidade):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE produtos SET estoque_atual = estoque_atual + ? WHERE id = ?",
                   (quantidade, produto_id))
    conn.commit()
    conn.close()


def aumentar_lote(lote_id, quantidade):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE lotes SET quantidade = quantidade + ? WHERE id = ?",
                   (quantidade, lote_id))
    conn.commit()
    conn.close()


# ============================================================
# ============ AUDITORIA - NAO CONFORMIDADES =================
# ============================================================

def criar_nao_conformidade(titulo, descricao, area, severidade,
                             evidencia, utilizador_id, utilizador_nome):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ano = datetime.now().strftime("%Y")
    cursor.execute("SELECT COUNT(*) FROM nao_conformidades WHERE numero LIKE ?", (f"NC-{ano}-%",))
    total = cursor.fetchone()[0] + 1
    numero = f"NC-{ano}-{total:04d}"
    cursor.execute("""
        INSERT INTO nao_conformidades 
        (numero, data_criacao, titulo, descricao, area, severidade, estado,
         evidencia, criado_por_id, criado_por_nome)
        VALUES (?, ?, ?, ?, ?, ?, 'ABERTA', ?, ?, ?)
    """, (numero, data, titulo, descricao, area, severidade, evidencia,
          utilizador_id, utilizador_nome))
    conn.commit()
    conn.close()
    return numero


def listar_nao_conformidades(limite=100, estado=None):
    conn = conectar()
    cursor = conn.cursor()
    if estado:
        cursor.execute("""
            SELECT id, numero, data_criacao, titulo, area, severidade, estado,
                   criado_por_nome
            FROM nao_conformidades WHERE estado = ?
            ORDER BY id DESC LIMIT ?
        """, (estado, limite))
    else:
        cursor.execute("""
            SELECT id, numero, data_criacao, titulo, area, severidade, estado,
                   criado_por_nome
            FROM nao_conformidades
            ORDER BY id DESC LIMIT ?
        """, (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def buscar_nao_conformidade(nc_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, numero, data_criacao, titulo, descricao, area, severidade,
               estado, evidencia, criado_por_nome, data_encerramento,
               encerrado_por_nome, conclusao
        FROM nao_conformidades WHERE id = ?
    """, (nc_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado


def atualizar_estado_nc(nc_id, novo_estado, utilizador_nome, conclusao=None):
    conn = conectar()
    cursor = conn.cursor()
    if novo_estado == "ENCERRADA":
        data_enc = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE nao_conformidades 
            SET estado = ?, data_encerramento = ?, encerrado_por_nome = ?, conclusao = ?
            WHERE id = ?
        """, (novo_estado, data_enc, utilizador_nome, conclusao, nc_id))
    else:
        cursor.execute("UPDATE nao_conformidades SET estado = ? WHERE id = ?",
                       (novo_estado, nc_id))
    conn.commit()
    conn.close()


def contagem_nc_por_estado():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT estado, COUNT(*) FROM nao_conformidades GROUP BY estado")
    resultado = cursor.fetchall()
    conn.close()
    return dict(resultado)


def aud_vendas_com_desconto(limite=50):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.id, v.data, v.total, v.desconto_global_valor, v.subtotal_original,
               v.forma_pagamento, u.nome, v.autorizado_por
        FROM vendas v
        LEFT JOIN utilizadores u ON u.id = v.utilizador_id
        WHERE v.desconto_global_valor > 0
          AND DATE(v.data) >= DATE('now', '-30 days')
        ORDER BY v.id DESC LIMIT ?
    """, (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def aud_sangrias(limite=50):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.data, m.valor, m.descricao, m.utilizador_nome
        FROM movimentos_caixa m
        WHERE m.tipo = 'SANGRIA'
          AND DATE(m.data) >= DATE('now', '-30 days')
        ORDER BY m.id DESC LIMIT ?
    """, (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def aud_anulacoes(limite=50):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT numero, data, cliente_nome, total, motivo_anulacao, utilizador_nome
        FROM facturas WHERE estado = 'ANULADA'
        ORDER BY id DESC LIMIT ?
    """, (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def aud_perdas_recentes(limite=50):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.data, p.tipo, pr.nome, p.quantidade, p.valor_perdido,
               p.motivo, p.utilizador_nome
        FROM perdas p
        LEFT JOIN produtos pr ON pr.id = p.produto_id
        WHERE DATE(p.data) >= DATE('now', '-30 days')
        ORDER BY p.id DESC LIMIT ?
    """, (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def aud_lotes_vencidos():
    conn = conectar()
    cursor = conn.cursor()
    hoje = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT p.nome, l.numero_lote, l.data_validade, l.quantidade
        FROM lotes l
        JOIN produtos p ON p.id = l.produto_id
        WHERE l.data_validade < ? AND l.quantidade > 0
        ORDER BY l.data_validade
    """, (hoje,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def aud_alteracoes_produtos(limite=50):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data, utilizador_nome, acao, detalhes
        FROM auditoria
        WHERE acao IN ('EDITAR PRODUTO', 'NOVO PRODUTO', 'ELIMINAR PRODUTO',
                       'ENTRADA MANUAL', 'SAIDA MANUAL')
        ORDER BY id DESC LIMIT ?
    """, (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def registar_auditoria_realizada(tipo, area, descricao, resultado,
                                    auditor_id, auditor_nome):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO auditorias_realizadas 
        (data, tipo, area, descricao, resultado, auditor_id, auditor_nome)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data, tipo, area, descricao, resultado, auditor_id, auditor_nome))
    conn.commit()
    conn.close()


def listar_auditorias_realizadas(limite=50):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data, tipo, area, descricao, resultado, auditor_nome
        FROM auditorias_realizadas
        ORDER BY id DESC LIMIT ?
    """, (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


# ============================================================
# ============ CORRIGIR OPERACOES ANTIGAS ====================
# ============================================================

def corrigir_operacoes_antigas():
    import uuid as uuid_lib
    
    conn = conectar()
    cursor = conn.cursor()
    
    farm_id = None
    terminal = "TERM-01"
    try:
        from identidade import obter_farmacia_id, obter_terminal_codigo
        farm_id = obter_farmacia_id()
        terminal = obter_terminal_codigo()
    except Exception:
        pass
    
    tabelas = ["vendas", "compras", "perdas", "movimentos_caixa", "facturas"]
    total_corrigido = 0
    
    for tab in tabelas:
        try:
            cursor.execute(f"SELECT id FROM {tab} WHERE uuid IS NULL")
            ids = [r[0] for r in cursor.fetchall()]
            
            for pid in ids:
                novo_uuid = str(uuid_lib.uuid4())
                cursor.execute(f"""
                    UPDATE {tab}
                    SET uuid = ?, terminal_id = ?, farmacia_id = ?
                    WHERE id = ?
                """, (novo_uuid, terminal, farm_id, pid))
                total_corrigido += 1
        except Exception as e:
            print(f"[{tab}] Erro: {e}")
    
    conn.commit()
    conn.close()
    return total_corrigido

# ============================================================
# ============ TURNOS DE CAIXA ===============================
# ============================================================

def abrir_turno(caixa_id, utilizador_id, utilizador_nome, valor_inicial,
                 notas_dict=None, observacoes=""):
    conn = conectar()
    cur = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("""
        INSERT INTO turnos_caixa 
        (caixa_id, data_abertura, utilizador_id, utilizador_nome,
         valor_inicial, estado, observacoes)
        VALUES (?, ?, ?, ?, ?, 'ABERTO', ?)
    """, (caixa_id, data, utilizador_id, utilizador_nome,
          valor_inicial, observacoes))
    
    turno_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    if notas_dict:
        _registrar_detalhe_notas(turno_id, "ABERTURA", notas_dict, valor_inicial)
    
    return turno_id


def _registrar_detalhe_notas(turno_id, tipo, notas_dict, total):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO detalhe_notas 
        (turno_id, tipo, nota_5000, nota_2000, nota_1000, nota_500,
         nota_200, nota_100, nota_50, nota_20, nota_10, total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (turno_id, tipo,
          notas_dict.get(5000, 0), notas_dict.get(2000, 0),
          notas_dict.get(1000, 0), notas_dict.get(500, 0),
          notas_dict.get(200, 0), notas_dict.get(100, 0),
          notas_dict.get(50, 0), notas_dict.get(20, 0),
          notas_dict.get(10, 0), total))
    conn.commit()
    conn.close()


def turno_aberto():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, caixa_id, data_abertura, utilizador_nome, valor_inicial
        FROM turnos_caixa
        WHERE estado = 'ABERTO'
        ORDER BY id DESC LIMIT 1
    """)
    r = cur.fetchone()
    conn.close()
    return r


def obter_turno(turno_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, caixa_id, data_abertura, data_fecho, utilizador_id,
               utilizador_nome, valor_inicial, total_vendas, total_dinheiro,
               total_tpa, total_pix, dinheiro_contado, tpa_contado,
               total_contado, total_sistema, diferenca, estado, observacoes
        FROM turnos_caixa WHERE id = ?
    """, (turno_id,))
    r = cur.fetchone()
    conn.close()
    return r


def calcular_totais_turno(turno_id):
    turno = obter_turno(turno_id)
    if not turno:
        return None
    
    caixa_id = turno[1]
    data_abertura = turno[2]
    
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            COALESCE(SUM(total), 0),
            COALESCE(SUM(CASE WHEN forma_pagamento = 'Dinheiro' THEN total ELSE COALESCE(valor_dinheiro, 0) END), 0),
            COALESCE(SUM(CASE WHEN forma_pagamento = 'Multicaixa' THEN total ELSE COALESCE(valor_tpa, 0) END), 0),
            COALESCE(SUM(CASE WHEN forma_pagamento IN ('Transferencia', 'PIX / Transferencia') THEN total ELSE COALESCE(valor_transferencia, 0) END), 0),
            COUNT(*)
        FROM vendas
        WHERE caixa_id = ? AND data >= ?
    """, (caixa_id, data_abertura))
    
    r = cur.fetchone()
    conn.close()
    
    return {
        "total_geral": r[0] or 0,
        "dinheiro": r[1] or 0,
        "tpa": r[2] or 0,
        "pix": r[3] or 0,
        "num_vendas": r[4] or 0,
    }


def fechar_turno(turno_id, dinheiro_contado, tpa_contado,
                   notas_dict=None, observacoes=""):
    turno = obter_turno(turno_id)
    if not turno:
        return None
    
    totais = calcular_totais_turno(turno_id)
    total_sistema = totais["dinheiro"] + totais["tpa"]
    total_contado = dinheiro_contado + tpa_contado
    diferenca = total_contado - total_sistema
    
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        UPDATE turnos_caixa SET
            data_fecho = ?,
            total_vendas = ?,
            total_dinheiro = ?,
            total_tpa = ?,
            total_pix = ?,
            dinheiro_contado = ?,
            tpa_contado = ?,
            total_contado = ?,
            total_sistema = ?,
            diferenca = ?,
            estado = 'FECHADO',
            observacoes = ?
        WHERE id = ?
    """, (data, totais["total_geral"], totais["dinheiro"], totais["tpa"],
          totais["pix"], dinheiro_contado, tpa_contado, total_contado,
          total_sistema, diferenca, observacoes, turno_id))
    conn.commit()
    conn.close()
    
    if notas_dict:
        _registrar_detalhe_notas(turno_id, "FECHO", notas_dict, dinheiro_contado)
    
    return {
        "total_vendas": totais["total_geral"],
        "dinheiro_sistema": totais["dinheiro"],
        "tpa_sistema": totais["tpa"],
        "pix_sistema": totais["pix"],
        "dinheiro_contado": dinheiro_contado,
        "tpa_contado": tpa_contado,
        "total_contado": total_contado,
        "total_sistema": total_sistema,
        "diferenca": diferenca,
        "estado": "OK" if abs(diferenca) < 0.01 else ("FALTA" if diferenca < 0 else "SOBRA"),
    }


def listar_turnos_dia(data_ref=None, limite=50):
    if not data_ref:
        data_ref = datetime.now().strftime("%Y-%m-%d")
    
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, data_abertura, data_fecho, utilizador_nome,
               total_vendas, total_dinheiro, total_tpa, total_pix,
               total_contado, total_sistema, diferenca, estado
        FROM turnos_caixa
        WHERE DATE(data_abertura) = DATE(?)
        ORDER BY id ASC
        LIMIT ?
    """, (data_ref, limite))
    resultado = cur.fetchall()
    conn.close()
    return resultado


def listar_turnos_historico(limite=100):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, data_abertura, data_fecho, utilizador_nome,
               total_vendas, total_dinheiro, total_tpa, total_pix,
               total_contado, total_sistema, diferenca, estado
        FROM turnos_caixa
        WHERE estado IN ('FECHADO', 'CONCILIADO')
        ORDER BY id DESC
        LIMIT ?
    """, (limite,))
    resultado = cur.fetchall()
    conn.close()
    return resultado


def obter_detalhe_notas(turno_id, tipo="FECHO"):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT nota_5000, nota_2000, nota_1000, nota_500, nota_200,
               nota_100, nota_50, nota_20, nota_10, total
        FROM detalhe_notas
        WHERE turno_id = ? AND tipo = ?
        ORDER BY id DESC LIMIT 1
    """, (turno_id, tipo))
    r = cur.fetchone()
    conn.close()
    return r


# ============================================================
# ============ RELATORIOS ====================================
# ============================================================

def relatorio_vendas_periodo(data_inicio, data_fim):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT v.data, v.total, v.forma_pagamento, u.nome
        FROM vendas v
        LEFT JOIN utilizadores u ON u.id = v.utilizador_id
        WHERE DATE(v.data) >= DATE(?) AND DATE(v.data) <= DATE(?)
        ORDER BY v.data DESC
    ''', (data_inicio, data_fim))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def resumo_vendas_periodo(data_inicio, data_fim):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*), COALESCE(SUM(total), 0), COALESCE(AVG(total), 0)
        FROM vendas
        WHERE DATE(data) >= DATE(?) AND DATE(data) <= DATE(?)
    ''', (data_inicio, data_fim))
    resultado = cursor.fetchone()
    conn.close()
    return resultado


def produtos_mais_vendidos(data_inicio, data_fim, limite=20):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.nome, p.codigo_barras,
               SUM(iv.quantidade) as qtd_total,
               SUM(iv.quantidade * iv.preco_unitario) as receita_total
        FROM itens_venda iv
        JOIN produtos p ON p.id = iv.produto_id
        JOIN vendas v ON v.id = iv.venda_id
        WHERE DATE(v.data) >= DATE(?) AND DATE(v.data) <= DATE(?)
        GROUP BY p.id
        ORDER BY qtd_total DESC
        LIMIT ?
    ''', (data_inicio, data_fim, limite))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def vendas_por_forma_pagamento(data_inicio, data_fim):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT forma_pagamento, COUNT(*), COALESCE(SUM(total), 0)
        FROM vendas
        WHERE DATE(data) >= DATE(?) AND DATE(data) <= DATE(?)
        GROUP BY forma_pagamento
        ORDER BY SUM(total) DESC
    ''', (data_inicio, data_fim))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def vendas_por_utilizador(data_inicio, data_fim):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.nome, COUNT(v.id), COALESCE(SUM(v.total), 0)
        FROM vendas v
        LEFT JOIN utilizadores u ON u.id = v.utilizador_id
        WHERE DATE(v.data) >= DATE(?) AND DATE(v.data) <= DATE(?)
        GROUP BY u.id
        ORDER BY SUM(v.total) DESC
    ''', (data_inicio, data_fim))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def margem_produtos(data_inicio, data_fim):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.nome, p.preco_custo, p.preco_venda,
               SUM(iv.quantidade) as qtd,
               SUM(iv.quantidade * iv.preco_unitario) as receita,
               SUM(iv.quantidade * p.preco_custo) as custo,
               SUM(iv.quantidade * (iv.preco_unitario - p.preco_custo)) as lucro
        FROM itens_venda iv
        JOIN produtos p ON p.id = iv.produto_id
        JOIN vendas v ON v.id = iv.venda_id
        WHERE DATE(v.data) >= DATE(?) AND DATE(v.data) <= DATE(?)
        GROUP BY p.id
        ORDER BY lucro DESC
    ''', (data_inicio, data_fim))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def resumo_facturacao_periodo(data_inicio, data_fim):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*), COALESCE(SUM(subtotal), 0),
               COALESCE(SUM(total_iva), 0), COALESCE(SUM(total), 0)
        FROM facturas
        WHERE DATE(data) >= DATE(?) AND DATE(data) <= DATE(?)
          AND estado != 'ANULADA'
          AND (tipo = 'FT' OR tipo IS NULL OR tipo = '')
    ''', (data_inicio, data_fim))
    resultado = cursor.fetchone()
    conn.close()
    return resultado


def inventario_valorizado():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            COALESCE(SUM(estoque_atual * preco_custo), 0) as valor_custo,
            COALESCE(SUM(estoque_atual * preco_venda), 0) as valor_venda,
            COUNT(*) as n_produtos,
            COALESCE(SUM(estoque_atual), 0) as total_unidades
        FROM produtos
    ''')
    resultado = cursor.fetchone()
    conn.close()
    return resultado


# ============================================================
# ============ RELATORIOS AVANCADOS ==========================
# ============================================================

def curva_abc(data_inicio, data_fim):
    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT p.id, p.nome, p.codigo_barras,
               COALESCE(SUM(iv.quantidade), 0) as qtd,
               COALESCE(SUM(iv.quantidade * iv.preco_unitario), 0) as receita
        FROM itens_venda iv
        JOIN produtos p ON p.id = iv.produto_id
        JOIN vendas v ON v.id = iv.venda_id
        WHERE DATE(v.data) >= DATE(?) AND DATE(v.data) <= DATE(?)
        GROUP BY p.id
        ORDER BY receita DESC
    """, (data_inicio, data_fim))
    produtos = cur.fetchall()
    conn.close()
    
    if not produtos:
        return []
    
    receita_total = sum(p[4] for p in produtos)
    if receita_total <= 0:
        return []
    
    resultado = []
    acumulado = 0
    for p in produtos:
        pid, nome, codigo, qtd, receita = p
        acumulado += receita
        perc_acum = (acumulado / receita_total) * 100
        perc_individual = (receita / receita_total) * 100
        
        if perc_acum <= 80:
            classe = "A"
        elif perc_acum <= 95:
            classe = "B"
        else:
            classe = "C"
        
        resultado.append({
            "id": pid,
            "nome": nome,
            "codigo": codigo,
            "quantidade": qtd,
            "receita": receita,
            "percentagem": perc_individual,
            "acumulado": perc_acum,
            "classe": classe,
        })
    
    return resultado


def resumo_curva_abc(data_inicio, data_fim):
    dados = curva_abc(data_inicio, data_fim)
    
    resumo = {
        "A": {"qtd": 0, "receita": 0, "produtos": 0},
        "B": {"qtd": 0, "receita": 0, "produtos": 0},
        "C": {"qtd": 0, "receita": 0, "produtos": 0},
        "total_produtos": 0,
        "total_receita": 0,
    }
    
    for d in dados:
        classe = d["classe"]
        resumo[classe]["qtd"] += d["quantidade"]
        resumo[classe]["receita"] += d["receita"]
        resumo[classe]["produtos"] += 1
        resumo["total_produtos"] += 1
        resumo["total_receita"] += d["receita"]
    
    return resumo


def vendas_por_hora(data_inicio, data_fim):
    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT strftime('%H', data) as hora,
               COUNT(*) as num_vendas,
               COALESCE(SUM(total), 0) as total
        FROM vendas
        WHERE DATE(data) >= DATE(?) AND DATE(data) <= DATE(?)
        GROUP BY hora
        ORDER BY hora
    """, (data_inicio, data_fim))
    resultado = cur.fetchall()
    conn.close()
    
    dados_horas = {int(h): (n, t) for h, n, t in resultado}
    
    lista_final = []
    for hora in range(24):
        num, total = dados_horas.get(hora, (0, 0))
        lista_final.append({
            "hora": f"{hora:02d}:00",
            "hora_int": hora,
            "num_vendas": num,
            "total": total,
        })
    
    return lista_final


def top_clientes(data_inicio, data_fim, limite=20):
    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT c.id, c.nome, c.nif, c.telefone,
               COUNT(v.id) as num_compras,
               COALESCE(SUM(v.total), 0) as total,
               COALESCE(AVG(v.total), 0) as ticket_medio
        FROM clientes c
        JOIN vendas v ON v.cliente_id = c.id
        WHERE DATE(v.data) >= DATE(?) AND DATE(v.data) <= DATE(?)
        GROUP BY c.id
        ORDER BY total DESC
        LIMIT ?
    """, (data_inicio, data_fim, limite))
    resultado = cur.fetchall()
    conn.close()
    
    lista = []
    for r in resultado:
        cid, nome, nif, telefone, num_compras, total, ticket_medio = r
        lista.append({
            "id": cid,
            "nome": nome,
            "nif": nif,
            "telefone": telefone,
            "num_compras": num_compras,
            "total": total,
            "ticket_medio": ticket_medio,
        })
    
    return lista


def projecao_fecho_mes():
    hoje = datetime.now()
    dia_atual = hoje.day
    mes = hoje.strftime("%Y-%m")
    
    if hoje.month == 12:
        proximo = hoje.replace(year=hoje.year + 1, month=1, day=1)
    else:
        proximo = hoje.replace(month=hoje.month + 1, day=1)
    
    dias_no_mes = (proximo - hoje.replace(day=1)).days
    dias_restantes = dias_no_mes - dia_atual
    
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(total), 0), COUNT(*)
        FROM vendas
        WHERE strftime('%Y-%m', data) = ?
    """, (mes,))
    vendido_ate_hoje, num_vendas = cur.fetchone()
    
    cur.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM vendas
        WHERE DATE(data) >= DATE('now', '-7 days')
    """)
    vendido_7dias = cur.fetchone()[0] or 0
    
    conn.close()
    
    media_diaria_recente = vendido_7dias / 7 if vendido_7dias > 0 else 0
    projecao = vendido_ate_hoje + (media_diaria_recente * dias_restantes)
    
    orc = obter_orcamento_mes(mes)
    orcamento = orc[2] if orc else 0
    
    perc_atual = (vendido_ate_hoje / orcamento * 100) if orcamento > 0 else 0
    perc_projetada = (projecao / orcamento * 100) if orcamento > 0 else 0
    
    if orcamento > 0:
        falta_para_meta = max(0, orcamento - vendido_ate_hoje)
        necessario_dia = (falta_para_meta / dias_restantes) if dias_restantes > 0 else 0
    else:
        falta_para_meta = 0
        necessario_dia = 0
    
    return {
        "mes": mes,
        "dia_atual": dia_atual,
        "dias_no_mes": dias_no_mes,
        "dias_restantes": dias_restantes,
        "vendido_ate_hoje": vendido_ate_hoje,
        "num_vendas": num_vendas,
        "media_diaria": media_diaria_recente,
        "projecao": projecao,
        "orcamento": orcamento,
        "percentagem_atual": perc_atual,
        "percentagem_projetada": perc_projetada,
        "falta_para_meta": falta_para_meta,
        "necessario_por_dia": necessario_dia,
        "vai_bater": projecao >= orcamento,
    }


def produtos_em_queda(limite=20):
    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT p.id, p.nome, p.codigo_barras,
               COALESCE(SUM(iv.quantidade), 0) as qtd
        FROM itens_venda iv
        JOIN produtos p ON p.id = iv.produto_id
        JOIN vendas v ON v.id = iv.venda_id
        WHERE DATE(v.data) >= DATE('now', '-30 days')
        GROUP BY p.id
    """)
    recentes = {r[0]: {"nome": r[1], "codigo": r[2], "qtd_atual": r[3]} for r in cur.fetchall()}
    
    cur.execute("""
        SELECT p.id,
               COALESCE(SUM(iv.quantidade), 0) as qtd
        FROM itens_venda iv
        JOIN produtos p ON p.id = iv.produto_id
        JOIN vendas v ON v.id = iv.venda_id
        WHERE DATE(v.data) >= DATE('now', '-60 days')
          AND DATE(v.data) < DATE('now', '-30 days')
        GROUP BY p.id
    """)
    anteriores = {r[0]: r[1] for r in cur.fetchall()}
    
    conn.close()
    
    resultado = []
    for pid, info in recentes.items():
        qtd_antes = anteriores.get(pid, 0)
        qtd_agora = info["qtd_atual"]
        
        if qtd_antes < 5:
            continue
        
        variacao = qtd_agora - qtd_antes
        perc_variacao = (variacao / qtd_antes * 100) if qtd_antes > 0 else 0
        
        if perc_variacao > -30:
            continue
        
        resultado.append({
            "id": pid,
            "nome": info["nome"],
            "codigo": info["codigo"],
            "qtd_antes": qtd_antes,
            "qtd_agora": qtd_agora,
            "variacao": variacao,
            "percentagem": perc_variacao,
        })
    
    resultado.sort(key=lambda x: x["percentagem"])
    
    return resultado[:limite]


# ============================================================
# ============ MODULO FINANCEIRO =============================
# ============================================================

def _inicializar_config_financeira():
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    defaults = [
        ("limite_deposito_gerente", "500000"),
        ("exigir_aprovacao_acima_de", "500000"),
        ("exigir_comprovante", "1"),
        ("bancos_ativos", "BAI,BFA,BIC,BCI,BPC,Standard Bank,Banco Sol,Millennium Atlântico,Banco Keve,Banco Económico"),
    ]
    
    for chave, valor in defaults:
        cur.execute("SELECT id FROM config_financeira WHERE chave = ?", (chave,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO config_financeira (chave, valor, atualizado_em)
                VALUES (?, ?, ?)
            """, (chave, valor, agora))
    
    conn.commit()
    conn.close()


def obter_config_financeira(chave, padrao=None):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT valor FROM config_financeira WHERE chave = ?", (chave,))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else padrao


def gravar_config_financeira(chave, valor, utilizador_nome=None):
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("SELECT id FROM config_financeira WHERE chave = ?", (chave,))
    existe = cur.fetchone()
    
    if existe:
        cur.execute("""
            UPDATE config_financeira SET valor = ?, atualizado_em = ?, atualizado_por = ?
            WHERE chave = ?
        """, (str(valor), agora, utilizador_nome, chave))
    else:
        cur.execute("""
            INSERT INTO config_financeira (chave, valor, atualizado_em, atualizado_por)
            VALUES (?, ?, ?, ?)
        """, (chave, str(valor), agora, utilizador_nome))
    
    conn.commit()
    conn.close()


def listar_bancos_ativos():
    valor = obter_config_financeira("bancos_ativos", "")
    if not valor:
        return []
    return [b.strip() for b in valor.split(",") if b.strip()]


def gerar_referencia_deposito():
    ano = datetime.now().strftime("%Y")
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM depositos WHERE referencia LIKE ?
    """, (f"DEP-{ano}-%",))
    total = cur.fetchone()[0] + 1
    conn.close()
    return f"DEP-{ano}-{total:04d}"


def saldo_atual_farmacia():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT saldo_atual FROM saldo_farmacia
        ORDER BY id DESC LIMIT 1
    """)
    r = cur.fetchone()
    conn.close()
    return r[0] if r else 0.0


def registar_movimento_saldo(tipo, valor, referencia, descricao, utilizador_nome):
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    saldo_anterior = saldo_atual_farmacia()
    
    if tipo == "ENTRADA":
        saldo_atual = saldo_anterior + valor
    elif tipo == "SAIDA":
        saldo_atual = saldo_anterior - valor
    else:
        saldo_atual = valor
    
    cur.execute("""
        INSERT INTO saldo_farmacia 
        (data, tipo, valor, referencia, descricao, saldo_anterior, saldo_atual,
         utilizador_nome, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d"),
        tipo, valor, referencia, descricao,
        saldo_anterior, saldo_atual, utilizador_nome, agora
    ))
    
    conn.commit()
    conn.close()
    return saldo_atual


def criar_deposito(valor, banco, numero_comprovante, observacoes,
                    gerente_id, gerente_nome, turno_id=None):
    import uuid as _uuid
    limite = float(obter_config_financeira("limite_deposito_gerente", "500000"))

    precisa_aprovacao = valor > limite
    estado = "PENDENTE_APROVACAO" if precisa_aprovacao else "REGISTADO"
    referencia = gerar_referencia_deposito()

    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Gerar UUID para sincronizacao
    uid = str(_uuid.uuid4())

    # Buscar farmacia_id local
    try:
        from identidade import obter_farmacia_id, obter_terminal_codigo
        farm_id = obter_farmacia_id()
        terminal = obter_terminal_codigo()
    except Exception:
        farm_id = 1
        terminal = "TERM-01"

    cur.execute("""
        INSERT INTO depositos
        (referencia, data, hora, valor, banco, numero_comprovante, observacoes,
         turno_id, gerente_id, gerente_nome, estado, criado_em,
         uuid, sincronizado, farmacia_id, terminal_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
    """, (
        referencia,
        datetime.now().strftime("%Y-%m-%d"),
        datetime.now().strftime("%H:%M"),
        valor, banco, numero_comprovante, observacoes,
        turno_id, gerente_id, gerente_nome, estado, agora,
        uid, farm_id, terminal
    ))

    conn.commit()
    conn.close()

    if not precisa_aprovacao:
        registar_movimento_saldo(
            "ENTRADA", valor, referencia,
            f"Deposito {banco} - {referencia}",
            gerente_nome
        )

    print(f"[Deposito] Criado {referencia} com UUID {uid[:8]}...")
    return referencia, estado, precisa_aprovacao

def aprovar_deposito(deposito_id, admin_nome):
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("""
        SELECT referencia, valor, banco FROM depositos WHERE id = ?
    """, (deposito_id,))
    r = cur.fetchone()
    
    if not r:
        conn.close()
        return False
    
    referencia, valor, banco = r
    
    cur.execute("""
        UPDATE depositos 
        SET estado = 'APROVADO', aprovado_por = ?, data_aprovacao = ?
        WHERE id = ?
    """, (admin_nome, agora, deposito_id))
    
    conn.commit()
    conn.close()
    
    registar_movimento_saldo(
        "ENTRADA", valor, referencia,
        f"Deposito {banco} - {referencia} (aprovado por {admin_nome})",
        admin_nome
    )
    
    return True


def cancelar_deposito(deposito_id, motivo, admin_nome):
    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE depositos 
        SET estado = 'CANCELADO', observacoes = COALESCE(observacoes, '') || ?
        WHERE id = ?
    """, (f" | CANCELADO por {admin_nome}: {motivo}", deposito_id))
    
    conn.commit()
    conn.close()
    return True


def listar_depositos(limite=100, gerente_id=None, estado=None):
    conn = conectar()
    cur = conn.cursor()
    
    sql = """
        SELECT id, referencia, data, hora, valor, banco, numero_comprovante,
               observacoes, gerente_nome, estado, aprovado_por, data_aprovacao,
               criado_em
        FROM depositos
        WHERE 1=1
    """
    params = []
    
    if gerente_id:
        sql += " AND gerente_id = ?"
        params.append(gerente_id)
    
    if estado:
        sql += " AND estado = ?"
        params.append(estado)
    
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limite)
    
    cur.execute(sql, params)
    resultado = cur.fetchall()
    conn.close()
    return resultado


def obter_deposito(deposito_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, referencia, data, hora, valor, banco, numero_comprovante,
               observacoes, turno_id, gerente_id, gerente_nome, estado,
               aprovado_por, data_aprovacao, criado_em
        FROM depositos WHERE id = ?
    """, (deposito_id,))
    r = cur.fetchone()
    conn.close()
    return r


def listar_movimentos_saldo(limite=100):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT data, tipo, valor, referencia, descricao,
               saldo_anterior, saldo_atual, utilizador_nome
        FROM saldo_farmacia
        ORDER BY id DESC LIMIT ?
    """, (limite,))
    resultado = cur.fetchall()
    conn.close()
    return resultado


def resumo_financeiro_dia(data_ref=None):
    if not data_ref:
        data_ref = datetime.now().strftime("%Y-%m-%d")
    
    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            COUNT(*),
            COALESCE(SUM(total_vendas), 0),
            COALESCE(SUM(total_dinheiro), 0),
            COALESCE(SUM(total_tpa), 0),
            COALESCE(SUM(total_pix), 0),
            COALESCE(SUM(total_contado), 0),
            COALESCE(SUM(total_sistema), 0),
            COALESCE(SUM(diferenca), 0)
        FROM turnos_caixa
        WHERE DATE(data_abertura) = DATE(?)
          AND estado = 'FECHADO'
    """, (data_ref,))
    r = cur.fetchone()
    
    cur.execute("""
        SELECT COUNT(*), COALESCE(SUM(valor), 0)
        FROM depositos
        WHERE data = ? AND estado IN ('REGISTADO', 'APROVADO')
    """, (data_ref,))
    d = cur.fetchone()
    
    conn.close()
    
    return {
        "data": data_ref,
        "num_turnos": r[0] or 0,
        "total_vendas": r[1] or 0,
        "total_dinheiro": r[2] or 0,
        "total_tpa": r[3] or 0,
        "total_pix": r[4] or 0,
        "total_contado": r[5] or 0,
        "total_sistema": r[6] or 0,
        "diferenca": r[7] or 0,
        "num_depositos": d[0] or 0,
        "total_depositado": d[1] or 0,
    }

# ============================================================
# ============ MODULO OPERACIONAL — DIAS =====================
# ============================================================

def abrir_dia(gerente_id, gerente_nome, observacoes=""):
    """
    Abre o dia de operacao.
    REGRA: se houver dia anterior ABERTO (nao fechado), BLOQUEIA.
    """
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, data, hora_abertura, gerente_abertura_nome
        FROM dias_operacao
        WHERE estado = 'ABERTO'
          AND data < ?
        ORDER BY data ASC
    """, (hoje,))
    dias_anteriores = cur.fetchall()
    
    if dias_anteriores:
        conn.close()
        nomes = [f"  - {d[1]} (aberto as {d[2]} por {d[3]})" 
                 for d in dias_anteriores]
        msg = (
            f"NAO E POSSIVEL ABRIR O DIA DE HOJE\n\n"
            f"Existe(m) {len(dias_anteriores)} dia(s) ANTERIOR(ES) em ABERTO:\n\n"
            + "\n".join(nomes) +
            f"\n\nFeche primeiro o(s) dia(s) anterior(es) antes de "
            f"abrir um novo dia.\n\n"
            f"Va a: DIA DE OPERACAO -> Fechar Dia"
        )
        return False, msg
    
    cur.execute("SELECT id, estado FROM dias_operacao WHERE data = ?", (hoje,))
    existente = cur.fetchone()
    
    if existente:
        conn.close()
        if existente[1] == "ABERTO":
            return False, "O dia de hoje ja esta aberto."
        return False, "O dia de hoje ja foi aberto e fechado."
    
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hora = datetime.now().strftime("%H:%M")
    
    cur.execute("""
        INSERT INTO dias_operacao 
        (data, hora_abertura, gerente_abertura_id, gerente_abertura_nome,
         estado, observacoes, criado_em)
        VALUES (?, ?, ?, ?, 'ABERTO', ?, ?)
    """, (hoje, hora, gerente_id, gerente_nome, observacoes, agora))
    
    conn.commit()
    conn.close()
    return True, f"Dia {hoje} aberto com sucesso."


def dia_aberto():
    hoje = datetime.now().strftime("%Y-%m-%d")
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, data, hora_abertura, gerente_abertura_nome, estado
        FROM dias_operacao
        WHERE data = ? AND estado = 'ABERTO'
        LIMIT 1
    """, (hoje,))
    r = cur.fetchone()
    conn.close()
    return r


def obter_dia(data_ref):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, data, hora_abertura, hora_fecho,
               gerente_abertura_nome, gerente_fecho_nome,
               total_turnos, total_vendas, total_dinheiro, total_tpa,
               total_pix, total_clientes, ticket_medio,
               total_faltas, total_sobras, valor_depositar,
               orcamento_dia, percentagem_atingida, estado, observacoes,
               relatorio_z_gerado
        FROM dias_operacao WHERE data = ?
    """, (data_ref,))
    r = cur.fetchone()
    conn.close()
    return r


def verificar_turnos_abertos(data_ref=None):
    if not data_ref:
        data_ref = datetime.now().strftime("%Y-%m-%d")
    
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, utilizador_nome, data_abertura, valor_inicial
        FROM turnos_caixa
        WHERE DATE(data_abertura) = DATE(?)
          AND estado = 'ABERTO'
        ORDER BY data_abertura ASC
    """, (data_ref,))
    resultado = cur.fetchall()
    conn.close()
    return resultado


def consolidar_dia(data_ref=None):
    if not data_ref:
        data_ref = datetime.now().strftime("%Y-%m-%d")
    
    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            COUNT(*),
            COALESCE(SUM(total_vendas), 0),
            COALESCE(SUM(total_dinheiro), 0),
            COALESCE(SUM(total_tpa), 0),
            COALESCE(SUM(total_pix), 0),
            COALESCE(SUM(total_contado), 0),
            COALESCE(SUM(total_sistema), 0),
            COALESCE(SUM(diferenca), 0)
        FROM turnos_caixa
        WHERE DATE(data_abertura) = DATE(?)
          AND estado = 'FECHADO'
    """, (data_ref,))
    r = cur.fetchone()
    
    num_turnos = r[0] or 0
    total_vendas = r[1] or 0
    total_dinheiro = r[2] or 0
    total_tpa = r[3] or 0
    total_pix = r[4] or 0
    total_contado = r[5] or 0
    total_sistema = r[6] or 0
    diferenca_total = r[7] or 0
    
    cur.execute("""
        SELECT COUNT(*) FROM vendas
        WHERE DATE(data) = DATE(?)
    """, (data_ref,))
    total_clientes = cur.fetchone()[0] or 0
    
    ticket_medio = (total_vendas / total_clientes) if total_clientes > 0 else 0
    
    cur.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN diferenca < 0 THEN ABS(diferenca) ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN diferenca > 0 THEN diferenca ELSE 0 END), 0)
        FROM turnos_caixa
        WHERE DATE(data_abertura) = DATE(?)
          AND estado = 'FECHADO'
    """, (data_ref,))
    fs = cur.fetchone()
    total_faltas = fs[0] or 0
    total_sobras = fs[1] or 0
    
    conn.close()
    
    return {
        "data": data_ref,
        "num_turnos": num_turnos,
        "total_vendas": total_vendas,
        "total_dinheiro": total_dinheiro,
        "total_tpa": total_tpa,
        "total_pix": total_pix,
        "total_contado": total_contado,
        "total_sistema": total_sistema,
        "diferenca_total": diferenca_total,
        "total_clientes": total_clientes,
        "ticket_medio": ticket_medio,
        "total_faltas": total_faltas,
        "total_sobras": total_sobras,
        "valor_depositar": total_dinheiro,
    }


def fechar_dia(gerente_id, gerente_nome, observacoes="", data_ref=None):
    """
    Fecha um dia de operacao.
    Se data_ref for None, fecha o dia ABERTO mais antigo (nao so hoje).
    """
    conn = conectar()
    cur = conn.cursor()
    
    if data_ref:
        cur.execute("""
            SELECT id, data, estado FROM dias_operacao
            WHERE data = ? AND estado = 'ABERTO'
        """, (data_ref,))
    else:
        cur.execute("""
            SELECT id, data, estado FROM dias_operacao
            WHERE estado = 'ABERTO'
            ORDER BY data ASC
            LIMIT 1
        """)
    
    dia = cur.fetchone()
    
    if not dia:
        conn.close()
        return False, "Nao existe nenhum dia aberto para fechar.", None
    
    dia_id, dia_data, _ = dia
    
    cur.execute("""
        SELECT id, utilizador_nome, data_abertura, valor_inicial
        FROM turnos_caixa
        WHERE DATE(data_abertura) = DATE(?)
          AND estado = 'ABERTO'
        ORDER BY data_abertura ASC
    """, (dia_data,))
    turnos_abertos = cur.fetchall()
    conn.close()
    
    if turnos_abertos:
        nomes = [f"  - {t[1]} (aberto as {t[2][11:16]})" for t in turnos_abertos]
        msg = (
            f"NAO E POSSIVEL FECHAR O DIA {dia_data}\n\n"
            f"Existem {len(turnos_abertos)} turno(s) AINDA ABERTO(S):\n\n"
            + "\n".join(nomes) +
            "\n\nFeche primeiro estes turnos (contagem de notas + "
            "autorizacao do gerente), e so depois podera fechar o dia."
        )
        return False, msg, None
    
    dados = consolidar_dia(dia_data)
    
    orcamento_dia = calcular_orcamento_dia(dia_data)
    percentagem = 0
    if orcamento_dia > 0:
        percentagem = (dados["total_vendas"] / orcamento_dia) * 100
    
    hora = datetime.now().strftime("%H:%M")
    
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        UPDATE dias_operacao SET
            hora_fecho = ?,
            gerente_fecho_id = ?,
            gerente_fecho_nome = ?,
            total_turnos = ?,
            total_vendas = ?,
            total_dinheiro = ?,
            total_tpa = ?,
            total_pix = ?,
            total_clientes = ?,
            ticket_medio = ?,
            total_faltas = ?,
            total_sobras = ?,
            valor_depositar = ?,
            orcamento_dia = ?,
            percentagem_atingida = ?,
            estado = 'FECHADO',
            observacoes = ?
        WHERE id = ?
    """, (
        hora, gerente_id, gerente_nome,
        dados["num_turnos"], dados["total_vendas"], dados["total_dinheiro"],
        dados["total_tpa"], dados["total_pix"], dados["total_clientes"],
        dados["ticket_medio"], dados["total_faltas"], dados["total_sobras"],
        dados["valor_depositar"], orcamento_dia, percentagem,
        observacoes, dia_id
    ))
    
    conn.commit()
    conn.close()
    
    return True, f"Dia {dia_data} fechado com sucesso.", dados


def listar_dias(limite=30):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, data, hora_abertura, hora_fecho,
               gerente_abertura_nome, gerente_fecho_nome,
               total_vendas, total_clientes, total_dinheiro,
               percentagem_atingida, estado
        FROM dias_operacao
        ORDER BY data DESC
        LIMIT ?
    """, (limite,))
    resultado = cur.fetchall()
    conn.close()
    return resultado


# ============================================================
# ============ MODULO OPERACIONAL — METAS ====================
# ============================================================

def definir_orcamento_mes(mes, orcamento, definido_por, observacoes=""):
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("SELECT id FROM metas_farmacia WHERE mes = ?", (mes,))
    existe = cur.fetchone()
    
    if existe:
        cur.execute("""
            UPDATE metas_farmacia 
            SET orcamento_mes = ?, observacoes = ?, 
                definido_por = ?, atualizado_em = ?
            WHERE mes = ?
        """, (orcamento, observacoes, definido_por, agora, mes))
    else:
        cur.execute("""
            INSERT INTO metas_farmacia 
            (mes, orcamento_mes, observacoes, definido_por, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (mes, orcamento, observacoes, definido_por, agora, agora))
    
    conn.commit()
    conn.close()
    return True


def obter_orcamento_mes(mes=None):
    if not mes:
        mes = datetime.now().strftime("%Y-%m")
    
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, mes, orcamento_mes, observacoes, definido_por,
               criado_em, atualizado_em
        FROM metas_farmacia WHERE mes = ?
    """, (mes,))
    r = cur.fetchone()
    conn.close()
    return r


def calcular_orcamento_dia(data_ref=None):
    if not data_ref:
        data_ref = datetime.now().strftime("%Y-%m-%d")
    
    try:
        dt = datetime.strptime(data_ref, "%Y-%m-%d")
    except Exception:
        dt = datetime.now()
    
    mes = dt.strftime("%Y-%m")
    orc = obter_orcamento_mes(mes)
    
    if not orc:
        return 0.0
    
    orcamento_mes = orc[2]
    
    if dt.month == 12:
        proximo = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        proximo = dt.replace(month=dt.month + 1, day=1)
    
    dias_no_mes = (proximo - dt.replace(day=1)).days
    
    if dias_no_mes <= 0:
        return 0.0
    
    return orcamento_mes / dias_no_mes


def progresso_mes(mes=None):
    if not mes:
        mes = datetime.now().strftime("%Y-%m")
    
    orc = obter_orcamento_mes(mes)
    orcamento = orc[2] if orc else 0
    
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(total), 0) FROM vendas
        WHERE strftime('%Y-%m', data) = ?
    """, (mes,))
    vendido = cur.fetchone()[0] or 0
    conn.close()
    
    percentagem = (vendido / orcamento * 100) if orcamento > 0 else 0
    falta = max(0, orcamento - vendido)
    
    return {
        "mes": mes,
        "orcamento": orcamento,
        "vendido": vendido,
        "percentagem": percentagem,
        "falta": falta,
    }


def progresso_dia(data_ref=None):
    if not data_ref:
        data_ref = datetime.now().strftime("%Y-%m-%d")
    
    orcamento = calcular_orcamento_dia(data_ref)
    
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(total), 0) FROM vendas
        WHERE DATE(data) = DATE(?)
    """, (data_ref,))
    vendido = cur.fetchone()[0] or 0
    conn.close()
    
    percentagem = (vendido / orcamento * 100) if orcamento > 0 else 0
    falta = max(0, orcamento - vendido)
    
    return {
        "data": data_ref,
        "orcamento": orcamento,
        "vendido": vendido,
        "percentagem": percentagem,
        "falta": falta,
    }


# ============================================================
# ============ MODULO OPERACIONAL — RELATORIOS ==============
# ============================================================

def guardar_relatorio(tipo, referencia, gerado_por, caminho_pdf=None,
                       dados_json=None):
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("""
        INSERT INTO relatorios_guardados 
        (tipo, referencia, data_geracao, gerado_por, caminho_pdf,
         dados_json, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tipo, referencia, agora, gerado_por, caminho_pdf,
          dados_json, agora))
    
    relatorio_id = cur.lastrowid
    conn.commit()
    conn.close()
    return relatorio_id


def listar_relatorios_guardados(limite=100, tipo=None):
    conn = conectar()
    cur = conn.cursor()
    
    if tipo:
        cur.execute("""
            SELECT id, tipo, referencia, data_geracao, gerado_por,
                   caminho_pdf
            FROM relatorios_guardados
            WHERE tipo = ?
            ORDER BY id DESC LIMIT ?
        """, (tipo, limite))
    else:
        cur.execute("""
            SELECT id, tipo, referencia, data_geracao, gerado_por,
                   caminho_pdf
            FROM relatorios_guardados
            ORDER BY id DESC LIMIT ?
        """, (limite,))
    
    resultado = cur.fetchall()
    conn.close()
    return resultado


def obter_relatorio(relatorio_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, tipo, referencia, data_geracao, gerado_por,
               caminho_pdf, dados_json, criado_em
        FROM relatorios_guardados WHERE id = ?
    """, (relatorio_id,))
    r = cur.fetchone()
    conn.close()
    return r


def marcar_relatorio_z_gerado(data_ref):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        UPDATE dias_operacao SET relatorio_z_gerado = 1 WHERE data = ?
    """, (data_ref,))
    conn.commit()
    conn.close()


# ============================================================
# ============ IA PARA ORCAMENTO =============================
# ============================================================

def _inicializar_config_ia():
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    defaults = [
        ("crescimento_anual_percentual", "20"),
        ("inflacao_anual_percentual", "15"),
        ("usar_crescimento_automatico", "1"),
        ("usar_inflacao", "1"),
        ("usar_dia_semana", "1"),
        ("usar_historico_anos", "1"),
    ]
    
    for chave, valor in defaults:
        cur.execute("SELECT id FROM config_ia_orcamento WHERE chave = ?", (chave,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO config_ia_orcamento (chave, valor, atualizado_em)
                VALUES (?, ?, ?)
            """, (chave, valor, agora))
    
    conn.commit()
    conn.close()


def obter_config_ia(chave, padrao=None):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT valor FROM config_ia_orcamento WHERE chave = ?", (chave,))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else padrao


def gravar_config_ia(chave, valor, utilizador_nome=None):
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("SELECT id FROM config_ia_orcamento WHERE chave = ?", (chave,))
    existe = cur.fetchone()
    
    if existe:
        cur.execute("""
            UPDATE config_ia_orcamento SET valor = ?, atualizado_em = ?, atualizado_por = ?
            WHERE chave = ?
        """, (str(valor), agora, utilizador_nome, chave))
    else:
        cur.execute("""
            INSERT INTO config_ia_orcamento (chave, valor, atualizado_em, atualizado_por)
            VALUES (?, ?, ?, ?)
        """, (chave, str(valor), agora, utilizador_nome))
    
    conn.commit()
    conn.close()


def calcular_crescimento_real():
    hoje = datetime.now()
    ha_12_meses = (hoje - timedelta(days=365)).strftime("%Y-%m-%d")
    ha_24_meses = (hoje - timedelta(days=730)).strftime("%Y-%m-%d")
    
    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT COALESCE(SUM(total), 0) FROM vendas
        WHERE DATE(data) >= DATE(?) AND DATE(data) <= DATE(?)
    """, (ha_12_meses, hoje.strftime("%Y-%m-%d")))
    vendas_12m = cur.fetchone()[0] or 0
    
    cur.execute("""
        SELECT COALESCE(SUM(total), 0) FROM vendas
        WHERE DATE(data) >= DATE(?) AND DATE(data) < DATE(?)
    """, (ha_24_meses, ha_12_meses))
    vendas_12m_anterior = cur.fetchone()[0] or 0
    
    conn.close()
    
    if vendas_12m_anterior <= 0 or vendas_12m <= 0:
        try:
            return float(obter_config_ia("crescimento_anual_percentual", "20"))
        except Exception:
            return 20.0
    
    crescimento = ((vendas_12m - vendas_12m_anterior) / vendas_12m_anterior) * 100
    crescimento = max(-50, min(200, crescimento))
    
    return crescimento


def obter_vendas_historico_dia(mes, dia, anos_atras=3):
    hoje = datetime.now()
    ano_atual = hoje.year
    
    resultados = []
    
    conn = conectar()
    cur = conn.cursor()
    
    for i in range(1, anos_atras + 1):
        ano = ano_atual - i
        try:
            data_alvo = f"{ano}-{mes:02d}-{dia:02d}"
            cur.execute("""
                SELECT COALESCE(SUM(total), 0), COUNT(*)
                FROM vendas
                WHERE DATE(data) = DATE(?)
            """, (data_alvo,))
            r = cur.fetchone()
            total = r[0] or 0
            num_vendas = r[1] or 0
            
            if total > 0:
                resultados.append({
                    "ano": ano,
                    "data": data_alvo,
                    "total": total,
                    "num_vendas": num_vendas,
                })
        except Exception:
            pass
    
    conn.close()
    return resultados


def obter_media_dia_semana(dia_semana, meses_atras=3):
    hoje = datetime.now()
    inicio = (hoje - timedelta(days=meses_atras * 30)).strftime("%Y-%m-%d")
    
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT data, total FROM vendas
        WHERE DATE(data) >= DATE(?) AND DATE(data) <= DATE(?)
    """, (inicio, hoje.strftime("%Y-%m-%d")))
    vendas = cur.fetchall()
    conn.close()
    
    if not vendas:
        return 0.0
    
    totais = {}
    for data_str, total in vendas:
        try:
            dt = datetime.strptime(data_str[:10], "%Y-%m-%d")
            dia = dt.weekday()
            if dia not in totais:
                totais[dia] = []
            totais[dia].append(total)
        except Exception:
            continue
    
    if dia_semana not in totais or not totais[dia_semana]:
        return 0.0
    
    return sum(totais[dia_semana]) / len(totais[dia_semana])


def sugerir_orcamento_dia(data_ref=None):
    if not data_ref:
        data_ref = datetime.now().strftime("%Y-%m-%d")
    
    try:
        dt = datetime.strptime(data_ref, "%Y-%m-%d")
    except Exception:
        dt = datetime.now()
    
    mes = dt.month
    dia = dt.day
    dia_semana = dt.weekday()
    
    historico_anos = obter_vendas_historico_dia(mes, dia, anos_atras=3)
    media_dia_semana = obter_media_dia_semana(dia_semana, meses_atras=3)
    
    usar_auto = obter_config_ia("usar_crescimento_automatico", "1") == "1"
    if usar_auto:
        crescimento = calcular_crescimento_real()
        origem_crescimento = "historico real"
    else:
        try:
            crescimento = float(obter_config_ia("crescimento_anual_percentual", "20"))
        except Exception:
            crescimento = 20.0
        origem_crescimento = "configurado"
    
    usar_inflacao = obter_config_ia("usar_inflacao", "1") == "1"
    if usar_inflacao:
        try:
            inflacao = float(obter_config_ia("inflacao_anual_percentual", "15"))
        except Exception:
            inflacao = 0.0
    else:
        inflacao = 0.0
    
    base_historico = 0
    if historico_anos:
        base_historico = sum(h["total"] for h in historico_anos) / len(historico_anos)
        
        anos_passados = len(historico_anos)
        fator_crescimento = (1 + crescimento / 100) ** anos_passados
        fator_inflacao = (1 + inflacao / 100) ** anos_passados
        
        base_ajustada = base_historico * fator_crescimento * fator_inflacao
    else:
        base_ajustada = media_dia_semana * (1 + crescimento / 100) * (1 + inflacao / 100)
    
    if base_ajustada <= 0:
        orcamento_mes = 0
        try:
            orc = obter_orcamento_mes(dt.strftime("%Y-%m"))
            if orc:
                orcamento_mes = orc[2]
        except Exception:
            pass
        
        if orcamento_mes > 0:
            if dt.month == 12:
                proximo = dt.replace(year=dt.year + 1, month=1, day=1)
            else:
                proximo = dt.replace(month=dt.month + 1, day=1)
            dias_no_mes = (proximo - dt.replace(day=1)).days
            base_ajustada = orcamento_mes / dias_no_mes
    
    return {
        "data": data_ref,
        "dia_semana": dia_semana,
        "historico_anos": historico_anos,
        "media_dia_semana": media_dia_semana,
        "crescimento_percentual": crescimento,
        "origem_crescimento": origem_crescimento,
        "inflacao_percentual": inflacao,
        "sugestao": round(base_ajustada, 2),
    }


def distribuir_orcamento_mes(mes=None):
    if not mes:
        mes = datetime.now().strftime("%Y-%m")
    
    orc = obter_orcamento_mes(mes)
    if not orc:
        return None
    
    orcamento_mes = orc[2]
    
    ano, m = mes.split("-")
    ano = int(ano)
    m = int(m)
    
    if m == 12:
        proximo = datetime(ano + 1, 1, 1)
    else:
        proximo = datetime(ano, m + 1, 1)
    
    inicio = datetime(ano, m, 1)
    dias_no_mes = (proximo - inicio).days
    
    sugestoes = []
    total_sugerido = 0
    
    for d in range(1, dias_no_mes + 1):
        data_str = f"{ano}-{m:02d}-{d:02d}"
        try:
            sug = sugerir_orcamento_dia(data_str)
            sugestoes.append(sug)
            total_sugerido += sug["sugestao"]
        except Exception as e:
            print(f"[IA] Erro em {data_str}: {e}")
            sugestoes.append({
                "data": data_str,
                "sugestao": 0,
                "historico_anos": [],
                "media_dia_semana": 0,
                "crescimento_percentual": 0,
                "inflacao_percentual": 0,
            })
    
    if total_sugerido > 0:
        fator_ajuste = orcamento_mes / total_sugerido
        
        for s in sugestoes:
            s["sugestao_original"] = s["sugestao"]
            s["sugestao"] = round(s["sugestao"] * fator_ajuste, 2)
    
    return {
        "mes": mes,
        "orcamento_mes": orcamento_mes,
        "dias_no_mes": dias_no_mes,
        "sugestoes": sugestoes,
        "total_original": total_sugerido,
    }


# ============================================================
# ============ DEVOLUCOES ====================================
# ============================================================

def gerar_referencia_devolucao():
    """Gera referencia tipo DEV-2026-0001."""
    conn = conectar()
    cursor = conn.cursor()
    ano = datetime.now().year
    cursor.execute("""
        SELECT referencia FROM devolucoes
        WHERE referencia LIKE ?
        ORDER BY id DESC LIMIT 1
    """, (f"DEV-{ano}-%",))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        try:
            ultimo = int(row[0].split("-")[-1])
            novo = ultimo + 1
        except Exception:
            novo = 1
    else:
        novo = 1
    
    return f"DEV-{ano}-{novo:04d}"


def criar_devolucao(venda_original_id, factura_original, produto_id,
                     produto_nome, quantidade, valor_unitario,
                     motivo, autorizado_por, autorizado_por_id,
                     utilizador_id, utilizador_nome,
                     lote_id=None, farmacia_id=None):
    """Cria uma devolucao e devolve o ID."""
    conn = conectar()
    cursor = conn.cursor()
    
    referencia = gerar_referencia_devolucao()
    agora = datetime.now()
    data = agora.strftime("%Y-%m-%d")
    hora = agora.strftime("%H:%M:%S")
    valor_total = quantidade * valor_unitario
    uuid_str = str(uuid.uuid4())
    criado_em = agora.strftime("%Y-%m-%d %H:%M:%S")
    terminal_id = os.environ.get("COMPUTERNAME", "PC")
    
    cursor.execute("""
        INSERT INTO devolucoes (
            referencia, data, hora, venda_original_id, factura_original,
            produto_id, produto_nome, quantidade, valor_unitario, valor_total,
            motivo, autorizado_por, autorizado_por_id,
            utilizador_id, utilizador_nome,
            estado, lote_id, uuid, terminal_id, farmacia_id,
            sincronizado, criado_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        referencia, data, hora, venda_original_id, factura_original,
        produto_id, produto_nome, quantidade, valor_unitario, valor_total,
        motivo, autorizado_por, autorizado_por_id,
        utilizador_id, utilizador_nome,
        "REGISTADA", lote_id, uuid_str, terminal_id, farmacia_id,
        0, criado_em
    ))
    
    dev_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return dev_id


def listar_devolucoes(limite=200):
    """Lista as devolucoes mais recentes."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, referencia, data, hora, factura_original,
               produto_nome, quantidade, valor_total,
               motivo, autorizado_por, utilizador_nome, estado
        FROM devolucoes
        ORDER BY id DESC
        LIMIT ?
    """, (limite,))
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def obter_devolucao(dev_id):
    """Devolve todos os campos de uma devolucao."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devolucoes WHERE id = ?", (dev_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def anular_devolucao(dev_id, autorizado_por, autorizado_por_id):
    """Anula uma devolucao (so admin/gerente)."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE devolucoes
        SET estado = 'ANULADA',
            autorizado_por = ?,
            autorizado_por_id = ?
        WHERE id = ?
    """, (autorizado_por, autorizado_por_id, dev_id))
    conn.commit()
    conn.close()
    return True

# ============================================================
# ============ TURNO POR UTILIZADOR ==========================
# ============================================================

def turno_aberto_do_utilizador(utilizador_id):
    """Devolve o turno ABERTO de um utilizador especifico."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, caixa_id, data_abertura, utilizador_nome, valor_inicial
        FROM turnos_caixa
        WHERE estado = 'ABERTO'
          AND utilizador_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (utilizador_id,))
    r = cur.fetchone()
    conn.close()
    return r

# ============================================================
# ============ ESTATISTICAS DE DEVOLUCOES ====================
# ============================================================

def estatisticas_devolucoes(mes=None):
    """Devolve estatisticas das devolucoes de um mes."""
    if not mes:
        mes = datetime.now().strftime("%Y-%m")
    
    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT COUNT(*), COALESCE(SUM(valor_total), 0)
        FROM devolucoes
        WHERE strftime('%Y-%m', data) = ?
          AND estado != 'ANULADA'
    """, (mes,))
    total_n, total_valor = cur.fetchone()
    
    cur.execute("""
        SELECT COUNT(*), COALESCE(SUM(valor_total), 0)
        FROM devolucoes
        WHERE strftime('%Y-%m', data) = ?
          AND estado = 'ANULADA'
    """, (mes,))
    anuladas_n, anuladas_valor = cur.fetchone()
    
    cur.execute("""
        SELECT motivo, COUNT(*), COALESCE(SUM(valor_total), 0)
        FROM devolucoes
        WHERE strftime('%Y-%m', data) = ?
          AND estado != 'ANULADA'
        GROUP BY motivo
        ORDER BY SUM(valor_total) DESC
        LIMIT 10
    """, (mes,))
    por_motivo = cur.fetchall()
    
    conn.close()
    
    return {
        "mes": mes,
        "total_n": total_n or 0,
        "total_valor": total_valor or 0,
        "anuladas_n": anuladas_n or 0,
        "anuladas_valor": anuladas_valor or 0,
        "por_motivo": por_motivo,
    }


# ============================================================
# ============ INICIALIZACAO =================================
# ============================================================

if __name__ == "__main__":
    criar_tabelas()
    migrar_tabela_facturas()
    print("Banco de dados JAM Soft criado/atualizado!")




# ============================================================
# ============ TRANSACCAO ATOMICA DE VENDA ===================
# ============================================================

def finalizar_venda(itens, forma_pagamento, utilizador, cliente_id=None,
                     caixa_id=None, cliente_info=None,
                     desconto_global=0, autorizado_por=None,
                     valores_pagamento=None):
    """
    REGISTA UMA VENDA COMPLETA NUMA UNICA TRANSACCAO.

    Se qualquer passo falhar, TUDO e revertido (ROLLBACK).

    itens = [
        {
            "produto_id": int,
            "nome": str,
            "quantidade": int,
            "preco_unitario": float,
            "isento_iva": bool,
            "desconto_percent": float (opcional),
        },
        ...
    ]

    forma_pagamento = "Dinheiro" / "Multicaixa" / etc.

    utilizador = dict com "id" e "nome"

    Retorna:
      (True, {"venda_id": X, "factura_id": Y, "factura_numero": "FT ...", "total": Z})
      ou
      (False, "mensagem de erro")
    """
    from datetime import datetime as _dt

    if not itens:
        return False, "Carrinho vazio."

    if caixa_id is None:
        return False, "Caixa nao identificada."

    # Verificar se ha turno aberto
    t = turno_aberto()
    if not t:
        return False, "Nao existe turno aberto. Abra um turno antes de vender."
    turno_id = t[0]

    # Calcular totais
    subtotal = 0
    total_iva = 0
    total_com_iva = 0

    for item in itens:
        qtd = item.get("quantidade", 0)
        preco = item.get("preco_unitario", 0)
        isento = item.get("isento_iva", False)
        desc_pct = item.get("desconto_percent", 0) or 0

        linha_base = qtd * preco
        desc_valor = linha_base * (desc_pct / 100)
        linha_sub = linha_base - desc_valor

        if isento:
            linha_iva = 0
        else:
            linha_iva = linha_sub * 0.14

        subtotal += linha_sub
        total_iva += linha_iva

    total_com_iva = subtotal + total_iva - (desconto_global or 0)

    # Guardar a parte efectiva de cada meio de pagamento. Nos pagamentos em
    # dinheiro, o valor recebido pode incluir troco; por isso a parte registada
    # é o total da venda, e nao o montante entregue pelo cliente.
    if valores_pagamento is None:
        if forma_pagamento == "Dinheiro":
            valores_pagamento = {"dinheiro": total_com_iva}
        elif forma_pagamento == "Multicaixa":
            valores_pagamento = {"tpa": total_com_iva}
        elif forma_pagamento in ("Transferencia", "PIX / Transferencia"):
            valores_pagamento = {"transferencia": total_com_iva}
        else:
            return False, "Indique os valores de cada meio de pagamento."

    try:
        valor_dinheiro = float(valores_pagamento.get("dinheiro", 0) or 0)
        valor_tpa = float(valores_pagamento.get("tpa", 0) or 0)
        valor_transferencia = float(valores_pagamento.get("transferencia", 0) or 0)
    except (AttributeError, TypeError, ValueError):
        return False, "Os valores do pagamento sao invalidos."

    valores = (valor_dinheiro, valor_tpa, valor_transferencia)
    if any(valor < 0 for valor in valores):
        return False, "Os valores do pagamento nao podem ser negativos."
    if round(sum(valores), 2) != round(total_com_iva, 2):
        return False, "A soma dos meios de pagamento nao corresponde ao total da venda."

    # Abrir UMA unica conexao para tudo
    conn = conectar()
    cur = conn.cursor()

    try:
        # Adquire o bloqueio de escrita antes de ler o stock, evitando que
        # duas vendas concorrentes validem as mesmas unidades em paralelo.
        cur.execute("BEGIN IMMEDIATE")

        # Validar e reservar em memória todos os lotes antes de gravar a venda.
        # Produtos repetidos no carrinho partilham a mesma disponibilidade.
        lotes_disponiveis = {}
        alocacoes_por_item = []
        quantidades_por_produto = {}
        for item in itens:
            produto_id = item.get("produto_id")
            qtd = item.get("quantidade", 0)
            if not isinstance(qtd, int) or isinstance(qtd, bool) or qtd <= 0:
                raise ValueError("A quantidade de cada produto deve ser um inteiro maior que zero.")
            if produto_id is None:
                raise ValueError("Produto inválido no carrinho.")
            quantidades_por_produto[produto_id] = quantidades_por_produto.get(produto_id, 0) + qtd

        for produto_id, qtd_solicitada in quantidades_por_produto.items():
            cur.execute("SELECT nome, estoque_atual FROM produtos WHERE id = ?", (produto_id,))
            produto = cur.fetchone()
            if not produto:
                raise ValueError(f"Produto {produto_id} não encontrado.")
            nome_produto, estoque_produto = produto
            cur.execute("""
                SELECT id, quantidade
                FROM lotes
                WHERE produto_id = ?
                  AND quantidade > 0
                  AND date(data_validade) >= date('now', 'localtime')
                ORDER BY date(data_validade) ASC, id ASC
            """, (produto_id,))
            lotes_validos = [[lote_id, quantidade] for lote_id, quantidade in cur.fetchall()]
            disponivel_lotes = sum(quantidade for _, quantidade in lotes_validos)
            disponivel = min(disponivel_lotes, max(0, estoque_produto or 0))
            if disponivel < qtd_solicitada:
                raise ValueError(
                    f"Stock insuficiente para {nome_produto}: solicitado {qtd_solicitada}, "
                    f"disponível {disponivel} em lotes válidos."
                )
            lotes_disponiveis[produto_id] = lotes_validos

        # Calcular a distribuição FEFO por linha, incluindo produtos repetidos.
        for item in itens:
            produto_id = item["produto_id"]
            restante = item["quantidade"]
            alocacoes = []
            for lote in lotes_disponiveis[produto_id]:
                if restante <= 0:
                    break
                qtd_lote = min(restante, lote[1])
                if qtd_lote:
                    alocacoes.append((lote[0], qtd_lote))
                    lote[1] -= qtd_lote
                    restante -= qtd_lote
            if restante:
                raise ValueError("Stock insuficiente nos lotes válidos para concluir a venda.")
            alocacoes_por_item.append(alocacoes)

        # ============ 1. INSERIR VENDA ============
        agora = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
        u, term, farm = _obter_identidade_operacao()

        cur.execute("""
            INSERT INTO vendas (data, total, valor_dinheiro, valor_tpa,
                                 valor_transferencia, subtotal_original, desconto_global_valor,
                                 autorizado_por, forma_pagamento, utilizador_id,
                                 cliente_id, caixa_id, uuid, terminal_id,
                                 farmacia_id, sincronizado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (agora, total_com_iva, valor_dinheiro, valor_tpa,
              valor_transferencia, subtotal + total_iva, desconto_global,
              autorizado_por, forma_pagamento, utilizador["id"],
              cliente_id, caixa_id, u, term, farm))
        venda_id = cur.lastrowid

        # ============ 2. PROCESSAR ITENS (FEFO + INSERT) ============
        for item, alocacoes in zip(itens, alocacoes_por_item):
            produto_id = item["produto_id"]
            qtd = item["quantidade"]
            preco = item["preco_unitario"]
            lote_principal_id = alocacoes[0][0] if alocacoes else None

            # Aplicar exactamente as alocações FEFO validadas acima.
            for lote_id, qtd_lote in alocacoes:
                cur.execute("""
                    UPDATE lotes SET quantidade = quantidade - ?
                    WHERE id = ? AND quantidade >= ?
                """, (qtd_lote, lote_id, qtd_lote))
                if cur.rowcount != 1:
                    raise ValueError("O stock do lote mudou durante a venda. Tente novamente.")

            # A condição protege também contra divergência no stock agregado.
            cur.execute("""
                UPDATE produtos SET estoque_atual = estoque_atual - ?
                WHERE id = ? AND estoque_atual >= ?
            """, (qtd, produto_id, qtd))
            if cur.rowcount != 1:
                raise ValueError("Stock insuficiente no produto. A venda foi cancelada.")

            # Inserir item de venda
            uuid_item = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO itens_venda (venda_id, produto_id, lote_id, quantidade,
                                          preco_unitario, uuid, terminal_id,
                                          farmacia_id, sincronizado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (venda_id, produto_id, lote_principal_id, qtd, preco,
                  uuid_item, term, farm))
            item_venda_id = cur.lastrowid
            cur.executemany("""
                INSERT INTO itens_venda_lotes (item_venda_id, lote_id, quantidade)
                VALUES (?, ?, ?)
            """, [(item_venda_id, lote_id, qtd_lote) for lote_id, qtd_lote in alocacoes])

        # ============ 3. NUMERO DE FACTURA ============
        cur.execute("SELECT id, serie_padrao, proximo_numero FROM empresa LIMIT 1")
        emp = cur.fetchone()
        if not emp:
            raise Exception("Empresa nao configurada.")

        emp_id, serie, prox = emp
        numero_factura = f"{serie}{prox:05d}"
        cur.execute("UPDATE empresa SET proximo_numero = proximo_numero + 1 WHERE id = ?",
                    (emp_id,))

        # ============ 4. INSERIR FACTURA ============
        fact_uuid = str(uuid.uuid4())
        cliente_nome = cliente_info.get("nome") if cliente_info else "Consumidor Final"
        cliente_nif = cliente_info.get("nif") if cliente_info else None
        cliente_end = cliente_info.get("endereco") if cliente_info else None

        cur.execute("""
            INSERT INTO facturas (numero, serie, tipo, data, venda_id, cliente_id,
                                   cliente_nome, cliente_nif, cliente_endereco,
                                   subtotal, total_iva, total, utilizador_id,
                                   utilizador_nome, forma_pagamento,
                                   valor_dinheiro, valor_segunda,
                                   uuid, terminal_id, farmacia_id, sincronizado)
            VALUES (?, ?, 'FT', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (numero_factura, serie, agora, venda_id, cliente_id,
              cliente_nome, cliente_nif, cliente_end,
              subtotal, total_iva, total_com_iva,
              utilizador["id"], utilizador["nome"], forma_pagamento,
              valor_dinheiro, valor_tpa + valor_transferencia,
              fact_uuid, term, farm))
        factura_id = cur.lastrowid

        
        # ─── Gerar hash encadeado e QR code (AGT) ───
        try:
            from database import gerar_qr_code_factura
            from agt_hash import calcular_hash_factura

            # Buscar NIF da empresa
            cur.execute("SELECT nif FROM empresa LIMIT 1")
            emp_row = cur.fetchone()
            nif_empresa = emp_row[0] if emp_row else ""

            # Hash encadeado (depende da factura anterior da série)
            hash_doc, hash_ant = calcular_hash_factura(
                numero=numero_factura,
                serie=serie,
                data=agora,
                nif_empresa=nif_empresa,
                total=total_com_iva,
                cliente_nif=cliente_nif or "",
            )
            qr = gerar_qr_code_factura(numero_factura, serie, hash_doc)

            cur.execute("""
                UPDATE facturas
                SET hash_documento = ?, hash_anterior = ?, qr_code = ?
                WHERE id = ?
            """, (hash_doc, hash_ant, qr, factura_id))

            print(f"[AGT] Hash encadeado gerado: {numero_factura} (anterior: {hash_ant[:12]}...)")
        except Exception as e_hash:
            print(f"[AGT] Aviso: erro ao gerar hash: {e_hash}")

        # ============ 5. INSERIR ITENS DA FACTURA ============
        for item in itens:
            qtd = item["quantidade"]
            preco = item["preco_unitario"]
            isento = 1 if item.get("isento_iva", False) else 0
            desc_pct = item.get("desconto_percent", 0) or 0

            linha_base = qtd * preco
            desc_valor = linha_base * (desc_pct / 100)
            linha_sub = linha_base - desc_valor

            if isento:
                taxa = 0
                iva = 0
            else:
                taxa = 0.14
                iva = linha_sub * 0.14

            cur.execute("""
                INSERT INTO itens_factura (factura_id, produto_id, descricao,
                                             quantidade, preco_unitario,
                                             isento_iva, taxa_iva, valor_iva,
                                             subtotal, desconto_percent,
                                             desconto_valor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (factura_id, item["produto_id"], item.get("nome", "Produto"),
                  qtd, preco, isento, taxa, iva,
                  linha_sub, desc_pct, desc_valor))

        # ============ 6. AUDITORIA ============
        cur.execute("""
            INSERT INTO auditoria (data, utilizador_id, utilizador_nome, acao, detalhes)
            VALUES (?, ?, ?, 'VENDA FINALIZADA', ?)
        """, (agora, utilizador["id"], utilizador["nome"],
              f"Venda #{venda_id} | Factura {numero_factura} | Total {total_com_iva:.2f}"))

        # ============ COMMIT ============
        conn.commit()

        return True, {
            "venda_id": venda_id,
            "factura_id": factura_id,
            "factura_numero": numero_factura,
            "total": total_com_iva,
            "subtotal": subtotal,
            "total_iva": total_iva,
            "turno_id": turno_id,
        }

    except Exception as e:
        # ROLLBACK - nada fica gravado
        try:
            conn.rollback()
        except Exception:
            pass
        if isinstance(e, ValueError):
            return False, str(e)
        return False, f"Erro na venda: {str(e)}"

    finally:
        try:
            conn.close()
        except Exception:
            pass

# ============================================================
# ============ NUMERACAO DE MOVIMENTOS =======================
# ============================================================

def proximo_numero_saida():
    """Gera o proximo numero de saida: SAI-2026-0001."""
    ano = datetime.now().strftime("%Y")
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT numero_documento FROM movimentos_caixa
        WHERE numero_documento LIKE ?
        ORDER BY id DESC LIMIT 1
    """, (f"SAI-{ano}-%",))
    r = cur.fetchone()
    conn.close()

    if r and r[0]:
        try:
            ultimo = int(r[0].split("-")[-1])
            novo = ultimo + 1
        except Exception:
            novo = 1
    else:
        novo = 1

    return f"SAI-{ano}-{novo:04d}"


def proximo_numero_entrada():
    """Gera o proximo numero de entrada: ENT-2026-0001."""
    ano = datetime.now().strftime("%Y")
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT numero_documento FROM movimentos_caixa
        WHERE numero_documento LIKE ?
        ORDER BY id DESC LIMIT 1
    """, (f"ENT-{ano}-%",))
    r = cur.fetchone()
    conn.close()

    if r and r[0]:
        try:
            ultimo = int(r[0].split("-")[-1])
            novo = ultimo + 1
        except Exception:
            novo = 1
    else:
        novo = 1

    return f"ENT-{ano}-{novo:04d}"


def registar_movimento_caixa_completo(caixa_id, tipo, valor, descricao,
                                        utilizador_id, utilizador_nome,
                                        autorizado_por, numero_documento):
    """Regista um movimento de caixa com todos os campos."""
    conn = conectar()
    cur = conn.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    u, term, farm = _obter_identidade_operacao()

    cur.execute("""
        INSERT INTO movimentos_caixa
        (caixa_id, data, tipo, valor, descricao, utilizador_id, utilizador_nome,
         uuid, terminal_id, farmacia_id, sincronizado,
         autorizado_por, numero_documento)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
    """, (caixa_id, data, tipo, valor, descricao, utilizador_id,
          utilizador_nome, u, term, farm,
          autorizado_por, numero_documento))

    mov_id = cur.lastrowid
    conn.commit()
    conn.close()
    return mov_id




# ============================================================
# ============ CONFIGURACAO AGT ==============================
# ============================================================

def obter_config_agt():
    """
    Retorna a configuração AGT activa.
    Retorna dict ou None se ainda não estiver configurada.
    """
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, numero_validacao, chave_rsa_path, activo,
                   data_activacao, ativado_por, observacoes
            FROM config_agt
            ORDER BY id DESC
            LIMIT 1
        """)
        r = cur.fetchone()
        if r:
            return {
                "id": r[0],
                "numero_validacao": r[1],
                "chave_rsa_path": r[2],
                "activo": bool(r[3]),
                "data_activacao": r[4],
                "ativado_por": r[5],
                "observacoes": r[6],
            }
        return None
    except Exception:
        return None
    finally:
        conn.close()


def guardar_config_agt(numero_validacao, chave_rsa_path, ativado_por, observacoes=""):
    """
    Guarda ou actualiza a configuração AGT.
    """
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Verificar se já existe
    cur.execute("SELECT id FROM config_agt LIMIT 1")
    r = cur.fetchone()

    if r:
        cur.execute("""
            UPDATE config_agt
            SET numero_validacao = ?,
                chave_rsa_path = ?,
                activo = 1,
                data_activacao = ?,
                ativado_por = ?,
                observacoes = ?
            WHERE id = ?
        """, (numero_validacao, chave_rsa_path, agora,
              ativado_por, observacoes, r[0]))
    else:
        cur.execute("""
            INSERT INTO config_agt
            (numero_validacao, chave_rsa_path, activo, data_activacao,
             ativado_por, observacoes)
            VALUES (?, ?, 1, ?, ?, ?)
        """, (numero_validacao, chave_rsa_path, agora,
              ativado_por, observacoes))

    conn.commit()
    conn.close()
    return True


def desactivar_config_agt():
    """Desactiva a configuração AGT (volta ao aviso temporário)."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("UPDATE config_agt SET activo = 0")
    conn.commit()
    conn.close()
    return True


def tem_validacao_agt():
    """Retorna True se o software está validado pela AGT."""
    cfg = obter_config_agt()
    return bool(cfg and cfg.get("activo") and cfg.get("numero_validacao"))


def obter_numero_validacao_agt():
    """Retorna o número de validação AGT ou None."""
    cfg = obter_config_agt()
    if cfg and cfg.get("activo"):
        return cfg.get("numero_validacao")
    return None


def obter_aviso_fiscal_actual():
    """
    Retorna o aviso fiscal que deve aparecer nas facturas:
    - Se AGT validou: "Processado por programa validado n.º XXX/AGT/YYYY"
    - Se não: "DOCUMENTO LOCAL - NAO VALIDADO PELA AGT"
    """
    numero = obter_numero_validacao_agt()
    if numero:
        return f"Processado por programa validado n.º {numero}"
    return "DOCUMENTO LOCAL - NAO VALIDADO PELA AGT"


def aplicar_assinatura_rsa(factura_id, hash_documento):
    """
    Aplica assinatura RSA ao hash de uma factura.
    Usa a chave privada configurada.

    Retorna (sucesso, assinatura_base64 ou erro).
    """
    cfg = obter_config_agt()
    if not cfg or not cfg.get("activo"):
        return False, "AGT nao configurada"

    chave_path = cfg.get("chave_rsa_path")
    if not chave_path or not os.path.exists(chave_path):
        return False, "Chave RSA nao encontrada"

    try:
        # Tentar importar cryptography
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        import base64

        with open(chave_path, "rb") as f:
            chave_privada = serialization.load_pem_private_key(
                f.read(), password=None
            )

        # Assinar o hash
        assinatura = chave_privada.sign(
            hash_documento.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        assinatura_base64 = base64.b64encode(assinatura).decode("utf-8")

        # Guardar na BD
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            UPDATE facturas
            SET assinatura_digital = ?
            WHERE id = ?
        """, (assinatura_base64, factura_id))
        conn.commit()
        conn.close()

        return True, assinatura_base64

    except ImportError:
        return False, "Biblioteca 'cryptography' nao instalada. Corre: pip install cryptography"
    except Exception as e:
        return False, f"Erro ao assinar: {e}"