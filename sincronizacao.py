"""
Sincronizacao com a nuvem (Supabase).
"""

import os
import time
import requests
from datetime import datetime

from database import conectar


# ============================================================
# ============ CONFIGURACAO ==================================
# ============================================================

from config_cloud import (SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY,
                         CLOUD_ACCESS_ENABLED, SYNC_ENABLED,
                         SYNC_TIMEOUT, SYNC_MAX_LOTES)

import fila_sync


# ============================================================
# ============ JWT DO UTILIZADOR =============================
# ============================================================

_JWT_PC = None


def definir_jwt_pc(jwt):
    """Guarda o JWT do utilizador (após login Supabase)."""
    global _JWT_PC
    _JWT_PC = jwt
    print(f"[Sync] JWT definido ({'OK' if jwt else 'vazio'})")


def limpar_jwt_pc():
    """Remove o JWT (após logout)."""
    global _JWT_PC
    _JWT_PC = None


import json
from pathlib import Path

_FICHEIRO_SESSAO = Path(__file__).parent / ".sessao_supabase.json"


def login_supabase(email, senha):
    """
    Faz login no Supabase Auth.
    Retorna (sucesso, dict_com_tokens_ou_erro).
    """
    if not CLOUD_ACCESS_ENABLED:
        return False, "Cloud desligada"

    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_PUBLISHABLE_KEY,
        "Content-Type": "application/json",
    }
    dados = {"email": email, "password": senha}

    try:
        r = requests.post(url, headers=headers, json=dados, timeout=10)
    except Exception as e:
        return False, f"Sem ligação: {e}"

    if r.status_code != 200:
        return False, f"Login falhou ({r.status_code})"

    resposta = r.json()
    access_token = resposta.get("access_token", "")
    refresh_token = resposta.get("refresh_token", "")
    expires_in = resposta.get("expires_in", 3600)

    if not access_token:
        return False, "Sem token na resposta"

    definir_jwt_pc(access_token)

    return True, {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "email": email,
    }


def guardar_sessao(dados):
    """Guarda tokens no ficheiro local (chmod 600)."""
    try:
        _FICHEIRO_SESSAO.write_text(
            json.dumps(dados, indent=2),
            encoding="utf-8"
        )
        print(f"[Sync] Sessão guardada em {_FICHEIRO_SESSAO}")
    except Exception as e:
        print(f"[Sync] Erro ao guardar sessão: {e}")


def carregar_sessao():
    """Lê tokens do ficheiro local."""
    try:
        if not _FICHEIRO_SESSAO.exists():
            return None
        dados = json.loads(_FICHEIRO_SESSAO.read_text(encoding="utf-8"))
        if dados.get("refresh_token"):
            return dados
    except Exception as e:
        print(f"[Sync] Erro ao ler sessão: {e}")
    return None


def renovar_sessao(sessao):
    """
    Usa refresh_token para obter novo access_token.
    Retorna (sucesso, msg).
    """
    refresh_token = sessao.get("refresh_token")
    if not refresh_token:
        return False, "Sem refresh_token"

    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"
    headers = {
        "apikey": SUPABASE_PUBLISHABLE_KEY,
        "Content-Type": "application/json",
    }
    dados = {"refresh_token": refresh_token}

    try:
        r = requests.post(url, headers=headers, json=dados, timeout=10)
    except Exception as e:
        return False, f"Sem ligação: {e}"

    if r.status_code != 200:
        return False, f"Refresh falhou ({r.status_code})"

    resposta = r.json()
    novo_access = resposta.get("access_token", "")
    novo_refresh = resposta.get("refresh_token", refresh_token)

    if not novo_access:
        return False, "Sem token na resposta"

    definir_jwt_pc(novo_access)

    # Actualizar sessão guardada
    guardar_sessao({
        "access_token": novo_access,
        "refresh_token": novo_refresh,
        "expires_in": resposta.get("expires_in", 3600),
        "email": sessao.get("email", ""),
    })

    return True, "Renovado"


def fazer_logout():
    """Apaga a sessão guardada."""
    try:
        if _FICHEIRO_SESSAO.exists():
            _FICHEIRO_SESSAO.unlink()
        limpar_jwt_pc()
        return True
    except Exception as e:
        print(f"[Sync] Erro ao fazer logout: {e}")
        return False


# ============================================================
# ============ HELPERS HTTP ==================================
# ============================================================

def _headers():
    """Headers com JWT se existir, senão chave pública."""
    if _JWT_PC:
        return {
            "apikey": SUPABASE_PUBLISHABLE_KEY,
            "Authorization": f"Bearer {_JWT_PC}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
    return {
        "apikey": SUPABASE_PUBLISHABLE_KEY,
        "Authorization": f"Bearer {SUPABASE_PUBLISHABLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def _url(tabela):
    return f"{SUPABASE_URL}/rest/v1/{tabela}"


def tem_internet():
    if not SYNC_ENABLED:
        return False, "Sincronizacao desactivada nas definicoes de seguranca."
    if not _JWT_PC:
        return False, "Sem JWT — precisa fazer login no Supabase"
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/farmacias?select=id&limit=1",
            headers=_headers(),
            timeout=5,
        )
        return (200 <= r.status_code < 300), r.status_code
    except Exception as e:
        return False, str(e)


# ============================================================
# ============ IDENTIDADE DA FARMACIA ========================
# ============================================================

def _obter_info_farmacia():
    try:
        from identidade import obter_farmacia_id, obter_terminal_codigo
        fid = obter_farmacia_id()
        term = obter_terminal_codigo()
        return fid, term
    except Exception:
        return None, "TERM-01"


def garantir_farmacia_na_nuvem():
    if not CLOUD_ACCESS_ENABLED or not SYNC_ENABLED:
        return None
    farm_id, terminal = _obter_info_farmacia()

    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT nome, nif, endereco, telefone, email
            FROM empresa LIMIT 1
        """)
        emp = cur.fetchone()
    except Exception:
        emp = None

    conn.close()

    if not emp:
        return None

    nome, nif, endereco, tel, email = emp

    try:
        r = requests.get(
            f"{_url('farmacias')}?nif=eq.{nif}&select=id",
            headers=_headers(),
            timeout=SYNC_TIMEOUT,
        )
        if r.status_code == 200 and r.json():
            return r.json()[0]["id"]
    except Exception:
        pass

    dados = {
        "codigo": f"FARM-{nif or 'LOCAL'}",
        "nome": nome,
        "nif": nif,
        "endereco": endereco,
        "telefone": tel,
        "email": email,
        "responsavel": "Sistema",
        "ativo": True,
    }

    try:
        r = requests.post(_url("farmacias"), headers=_headers(),
                            json=dados, timeout=SYNC_TIMEOUT)
        if r.status_code in (200, 201):
            return 1
    except Exception:
        pass

    return None


# ============================================================
# ============ PREPARAR PAYLOAD POR TIPO =====================
# ============================================================

def _preparar_payload(tipo, tabela_origem, registo_id, farmacia_id):
    conn = conectar()
    cur = conn.cursor()
    payload = None

    # ============ VENDA ============
    if tipo == "VENDA":
        cur.execute("""
            SELECT uuid, data, total, forma_pagamento, cliente_id,
                   utilizador_id, terminal_id
            FROM vendas WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            cli_nome = None
            if r[4]:
                cur.execute("SELECT nome FROM clientes WHERE id = ?", (r[4],))
                c = cur.fetchone()
                if c:
                    cli_nome = c[0]
            user_nome = None
            if r[5]:
                cur.execute("SELECT nome FROM utilizadores WHERE id = ?", (r[5],))
                u = cur.fetchone()
                if u:
                    user_nome = u[0]
            payload = {
                "uuid": r[0],
                "farmacia_id": farmacia_id,
                "terminal_id": r[6],
                "data": r[1],
                "total": r[2],
                "forma_pagamento": r[3],
                "cliente_nome": cli_nome,
                "utilizador_nome": user_nome,
            }

    # ============ COMPRA ============
    elif tipo == "COMPRA":
        cur.execute("""
            SELECT uuid, data, fornecedor_id, numero_fatura, total,
                   utilizador_id, terminal_id
            FROM compras WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            forn_nome = None
            if r[2]:
                cur.execute("SELECT nome FROM fornecedores WHERE id = ?", (r[2],))
                f = cur.fetchone()
                if f:
                    forn_nome = f[0]
            user_nome = None
            if r[5]:
                cur.execute("SELECT nome FROM utilizadores WHERE id = ?", (r[5],))
                u = cur.fetchone()
                if u:
                    user_nome = u[0]
            payload = {
                "uuid": r[0],
                "farmacia_id": farmacia_id,
                "terminal_id": r[6],
                "data": r[1],
                "fornecedor_nome": forn_nome,
                "numero_fatura": r[3],
                "total": r[4],
                "utilizador_nome": user_nome,
            }

    # ============ PERDA ============
    elif tipo == "PERDA":
        cur.execute("""
            SELECT uuid, data, tipo, produto_id, quantidade,
                   valor_perdido, motivo, utilizador_nome, terminal_id
            FROM perdas WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            prod_nome = None
            if r[3]:
                cur.execute("SELECT nome FROM produtos WHERE id = ?", (r[3],))
                p = cur.fetchone()
                if p:
                    prod_nome = p[0]
            payload = {
                "uuid": r[0],
                "farmacia_id": farmacia_id,
                "terminal_id": r[8],
                "data": r[1],
                "tipo": r[2],
                "produto_nome": prod_nome,
                "quantidade": r[4],
                "valor_perdido": r[5],
                "motivo": r[6],
                "utilizador_nome": r[7],
            }

    # ============ MOVIMENTO ============
    elif tipo == "MOVIMENTO":
        cur.execute("""
            SELECT uuid, data, tipo, valor, descricao,
                   utilizador_nome, terminal_id,
                   autorizado_por, numero_documento
            FROM movimentos_caixa WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "uuid": r[0],
                "farmacia_id": farmacia_id,
                "terminal_id": r[6],
                "data": r[1],
                "tipo": r[2],
                "valor": r[3],
                "descricao": r[4],
                "utilizador_nome": r[5],
                "autorizado_por": r[7],
                "numero_documento": r[8],
            }

    # ============ ITEM DE VENDA ============
    elif tipo == "ITEN_VENDA":
        cur.execute("""
            SELECT iv.uuid, iv.venda_id, iv.produto_id, iv.quantidade,
                   iv.preco_unitario, v.uuid AS venda_uuid,
                   p.nome AS produto_nome, p.codigo_barras,
                   p.isento_iva, iv.terminal_id
            FROM itens_venda iv
            LEFT JOIN vendas v ON v.id = iv.venda_id
            LEFT JOIN produtos p ON p.id = iv.produto_id
            WHERE iv.id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            subtotal = (r[3] or 0) * (r[4] or 0)
            payload = {
                "uuid": r[0],
                "farmacia_id": farmacia_id,
                "terminal_id": r[9],
                "venda_uuid": r[5],
                "venda_id_origem": r[1],
                "produto_id": r[2],
                "produto_nome": r[6],
                "codigo_barras": r[7],
                "quantidade": r[3],
                "preco_unitario": r[4],
                "isento_iva": r[8],
                "subtotal": subtotal,
            }

    # ============ PRODUTO ============
    elif tipo == "PRODUTO":
        cur.execute("""
            SELECT uuid, nome, codigo_barras, principio_ativo, laboratorio,
                   preco_custo, preco_venda, estoque_atual, estoque_minimo,
                   isento_iva, categoria_id, fornecedor_id
            FROM produtos WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            cat_nome = None
            if r[10]:
                cur.execute("SELECT nome FROM categorias WHERE id = ?", (r[10],))
                c = cur.fetchone()
                if c:
                    cat_nome = c[0]
            forn_nome = None
            if r[11]:
                cur.execute("SELECT nome FROM fornecedores WHERE id = ?", (r[11],))
                f = cur.fetchone()
                if f:
                    forn_nome = f[0]
            payload = {
                "uuid": r[0],
                "farmacia_id": farmacia_id,
                "nome": r[1],
                "codigo_barras": r[2],
                "principio_ativo": r[3],
                "laboratorio": r[4],
                "preco_custo": r[5],
                "preco_venda": r[6],
                "estoque_atual": r[7],
                "estoque_minimo": r[8],
                "isento_iva": r[9],
                "categoria_nome": cat_nome,
                "fornecedor_nome": forn_nome,
            }

    # ============ LOTE ============
    elif tipo == "LOTE":
        cur.execute("""
            SELECT l.uuid, l.produto_id, l.numero_lote, l.data_validade,
                   l.quantidade, p.nome AS produto_nome, p.codigo_barras
            FROM lotes l
            LEFT JOIN produtos p ON p.id = l.produto_id
            WHERE l.id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "uuid": r[0],
                "farmacia_id": farmacia_id,
                "produto_id": r[1],
                "produto_nome": r[5],
                "codigo_barras": r[6],
                "numero_lote": r[2],
                "data_validade": r[3],
                "quantidade": r[4],
            }

    # ============ CLIENTE ============
    elif tipo == "CLIENTE":
        cur.execute("""
            SELECT uuid, nome, nif, telefone, email, endereco,
                   data_nascimento, criado_em
            FROM clientes WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "uuid": r[0],
                "farmacia_id": farmacia_id,
                "nome": r[1],
                "nif": r[2],
                "telefone": r[3],
                "email": r[4],
                "endereco": r[5],
                "data_nascimento": r[6],
                "criado_em": r[7],
            }

    # ============ FACTURA ============
    elif tipo == "FACTURA":
        cur.execute("""
            SELECT uuid, numero, serie, tipo, data, cliente_nome,
                   cliente_nif, subtotal, total_iva, total, estado,
                   forma_pagamento, utilizador_nome, terminal_id
            FROM facturas WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "uuid": r[0],
                "farmacia_id": farmacia_id,
                "terminal_id": r[13],
                "numero": r[1],
                "serie": r[2],
                "tipo": r[3],
                "data": r[4],
                "cliente_nome": r[5],
                "cliente_nif": r[6],
                "subtotal": r[7],
                "total_iva": r[8],
                "total": r[9],
                "estado": r[10],
                "forma_pagamento": r[11],
                "utilizador_nome": r[12],
            }

    # ============ DEVOLUCAO ============
    elif tipo == "DEVOLUCAO":
        cur.execute("""
            SELECT uuid, referencia, data, hora, factura_original,
                   produto_nome, quantidade, valor_unitario, valor_total,
                   motivo, autorizado_por, utilizador_nome, estado,
                   terminal_id
            FROM devolucoes WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "uuid": r[0],
                "farmacia_id": farmacia_id,
                "terminal_id": r[13],
                "referencia": r[1],
                "data": r[2],
                "hora": r[3],
                "factura_original": r[4],
                "produto_nome": r[5],
                "quantidade": r[6],
                "valor_unitario": r[7],
                "valor_total": r[8],
                "motivo": r[9],
                "autorizado_por": r[10],
                "utilizador_nome": r[11],
                "estado": r[12],
            }

    # ============ TURNO ============
    elif tipo == "TURNO":
        cur.execute("""
            SELECT id, caixa_id, data_abertura, data_fecho,
                   utilizador_nome, valor_inicial, total_vendas,
                   total_dinheiro, total_tpa, total_contado,
                   total_sistema, diferenca, estado, observacoes
            FROM turnos_caixa WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "turno_id_local": r[0],
                "farmacia_id": farmacia_id,
                "caixa_id": r[1],
                "data_abertura": r[2],
                "data_fecho": r[3],
                "utilizador_nome": r[4],
                "valor_inicial": r[5],
                "total_vendas": r[6],
                "total_dinheiro": r[7],
                "total_tpa": r[8],
                "total_contado": r[9],
                "total_sistema": r[10],
                "diferenca": r[11],
                "estado": r[12],
                "observacoes": r[13],
            }

    # ============ DIA ============
    elif tipo == "DIA":
        cur.execute("""
            SELECT data, hora_abertura, hora_fecho,
                   gerente_abertura_nome, gerente_fecho_nome,
                   total_turnos, total_vendas, total_dinheiro,
                   total_tpa, total_clientes, ticket_medio,
                   total_faltas, total_sobras, orcamento_dia,
                   percentagem_atingida, estado
            FROM dias_operacao WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "data": r[0],
                "hora_abertura": r[1],
                "hora_fecho": r[2],
                "gerente_abertura_nome": r[3],
                "gerente_fecho_nome": r[4],
                "total_turnos": r[5],
                "total_vendas": r[6],
                "total_dinheiro": r[7],
                "total_tpa": r[8],
                "total_clientes": r[9],
                "ticket_medio": r[10],
                "total_faltas": r[11],
                "total_sobras": r[12],
                "orcamento_dia": r[13],
                "percentagem_atingida": r[14],
                "estado": r[15],
            }

    # ============ META ============
    elif tipo == "META":
        cur.execute("""
            SELECT id, mes, orcamento_mes, observacoes, definido_por,
                   criado_em, atualizado_em
            FROM metas_farmacia WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "mes": r[1],
                "farmacia_id": farmacia_id,
                "orcamento_mes": r[2],
                "observacoes": r[3],
                "definido_por": r[4],
                "criado_em": r[5],
                "atualizado_em": r[6],
            }

    # ============ CAIXA ============
    elif tipo == "CAIXA":
        cur.execute("""
            SELECT uuid, data_abertura, data_fecho,
                   utilizador_abertura_nome, utilizador_fecho_nome,
                   valor_inicial, total_vendas_dinheiro, total_sangrias,
                   total_reforcos, valor_esperado, valor_contado,
                   diferenca, estado, observacoes,
                   contado_tpa, num_taloes_tpa, detalhe_notas,
                   terminal_id
            FROM caixas WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "uuid": r[0],
                "farmacia_id": farmacia_id,
                "terminal_id": r[17],
                "data_abertura": r[1],
                "data_fecho": r[2],
                "utilizador_abertura_nome": r[3],
                "utilizador_fecho_nome": r[4],
                "valor_inicial": r[5],
                "total_vendas_dinheiro": r[6],
                "total_sangrias": r[7],
                "total_reforcos": r[8],
                "valor_esperado": r[9],
                "valor_contado": r[10],
                "diferenca": r[11],
                "estado": r[12],
                "observacoes": r[13],
                "contado_tpa": r[14] or 0,
                "num_taloes_tpa": r[15] or 0,
                "detalhe_notas": r[16],
            }

    # ============ IBT (TRANSFERENCIA) ============
    elif tipo == "IBT":
        cur.execute("""
            SELECT uuid, referencia, data_criacao, data_envio, data_recepcao,
                   farmacia_origem_id, farmacia_origem_codigo, farmacia_origem_nome,
                   farmacia_destino_id, farmacia_destino_codigo, farmacia_destino_nome,
                   utilizador_criou_nome, autorizado_por,
                   estado, total_itens, total_quantidade, valor_estimado,
                   observacoes, terminal_id
            FROM transferencias_filiais WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "uuid": r[0],
                "farmacia_id": farmacia_id,
                "referencia": r[1],
                "data_criacao": r[2],
                "data_envio": r[3],
                "data_recepcao": r[4],
                "farmacia_origem_id": r[5],
                "farmacia_origem_codigo": r[6],
                "farmacia_origem_nome": r[7],
                "farmacia_destino_id": r[8],
                "farmacia_destino_codigo": r[9],
                "farmacia_destino_nome": r[10],
                "utilizador_criou_nome": r[11],
                "autorizado_por": r[12],
                "estado": r[13],
                "total_itens": r[14],
                "total_quantidade": r[15],
                "valor_estimado": r[16],
                "observacoes": r[17],
                "terminal_id": r[18],
            }

    # ============ ITEM DE IBT ============
    elif tipo == "ITEN_IBT":
        cur.execute("""
            SELECT it.id, t.uuid AS transf_uuid, t.referencia,
                   it.produto_id, it.produto_nome, it.codigo_barras,
                   it.quantidade_enviada, it.quantidade_recebida, it.diferenca,
                   it.lote, it.validade, it.preco_custo, it.subtotal, it.justificacao
            FROM itens_transferencia it
            LEFT JOIN transferencias_filiais t ON t.id = it.transferencia_id
            WHERE it.id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "transferencia_uuid": r[1],
                "transferencia_referencia": r[2],
                "produto_id": r[3],
                "produto_nome": r[4],
                "codigo_barras": r[5],
                "quantidade_enviada": r[6],
                "quantidade_recebida": r[7],
                "diferenca": r[8],
                "lote": r[9],
                "validade": r[10],
                "preco_custo": r[11],
                "subtotal": r[12],
                "justificacao": r[13],
            }

    # ============ HISTORICO IBT ============
    elif tipo == "HISTORICO_IBT":
        cur.execute("""
            SELECT h.id, t.uuid AS transf_uuid,
                   h.data, h.acao, h.utilizador_nome,
                   h.estado_anterior, h.estado_novo, h.detalhes
            FROM historico_ibt h
            LEFT JOIN transferencias_filiais t ON t.id = h.transferencia_id
            WHERE h.id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "transferencia_uuid": r[1],
                "data": r[2],
                "acao": r[3],
                "utilizador_nome": r[4],
                "estado_anterior": r[5],
                "estado_novo": r[6],
                "detalhes": r[7],
            }

    # ============ CATEGORIA ============
    elif tipo == "CATEGORIA":
        cur.execute("""
            SELECT id, nome, descricao, criado_em
            FROM categorias WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "nome": r[1],
                "descricao": r[2],
                "criado_em": r[3],
            }

    # ============ FORNECEDOR ============
    elif tipo == "FORNECEDOR":
        cur.execute("""
            SELECT id, nome, nif, telefone, email, endereco,
                   observacoes, criado_em
            FROM fornecedores WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "nome": r[1],
                "nif": r[2],
                "telefone": r[3],
                "email": r[4],
                "endereco": r[5],
                "observacoes": r[6],
                "criado_em": r[7],
            }

    # ============ UTILIZADOR ============
    elif tipo == "UTILIZADOR":
        cur.execute("""
            SELECT id, nome, username, perfil, ativo,
                   criado_em, ultimo_login
            FROM utilizadores WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "nome": r[1],
                "username": r[2],
                "perfil": r[3],
                "ativo": bool(r[4]),
                "criado_em": r[5],
                "ultimo_login": r[6],
            }

    # ============ ITEN_FACTURA ============
    elif tipo == "ITEN_FACTURA":
        cur.execute("""
            SELECT ifa.id, f.uuid AS factura_uuid, f.numero AS factura_numero,
                   ifa.produto_id, ifa.descricao, ifa.quantidade,
                   ifa.preco_unitario, ifa.isento_iva, ifa.taxa_iva,
                   ifa.valor_iva, ifa.subtotal,
                   ifa.desconto_percent, ifa.desconto_valor
            FROM itens_factura ifa
            LEFT JOIN facturas f ON f.id = ifa.factura_id
            WHERE ifa.id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "factura_uuid": r[1],
                "factura_numero": r[2],
                "produto_id": r[3],
                "descricao": r[4],
                "quantidade": r[5],
                "preco_unitario": r[6],
                "isento_iva": r[7],
                "taxa_iva": r[8],
                "valor_iva": r[9],
                "subtotal": r[10],
                "desconto_percent": r[11],
                "desconto_valor": r[12],
            }

    # ============ INVENTARIO ============
    elif tipo == "INVENTARIO":
        cur.execute("""
            SELECT id, data, utilizador_nome, observacoes,
                   total_itens, total_diferencas
            FROM inventarios WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "data": r[1],
                "utilizador_nome": r[2],
                "observacoes": r[3],
                "total_itens": r[4],
                "total_diferencas": r[5],
            }

    # ============ ITEN_INVENTARIO ============
    elif tipo == "ITEN_INVENTARIO":
        cur.execute("""
            SELECT ii.id, ii.inventario_id, ii.produto_id,
                   p.nome AS produto_nome,
                   ii.estoque_sistema, ii.estoque_contado,
                   ii.diferenca, ii.justificacao
            FROM itens_inventario ii
            LEFT JOIN produtos p ON p.id = ii.produto_id
            WHERE ii.id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "inventario_id_local": r[1],
                "produto_id": r[2],
                "produto_nome": r[3],
                "estoque_sistema": r[4],
                "estoque_contado": r[5],
                "diferenca": r[6],
                "justificacao": r[7],
            }

    # ============ DEPOSITO ============
    elif tipo == "DEPOSITO":
        cur.execute("""
            SELECT id, referencia, data, hora, valor, banco,
                   numero_comprovante, observacoes, turno_id,
                   gerente_nome, estado, aprovado_por,
                   data_aprovacao, criado_em
            FROM depositos WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "referencia": r[1],
                "data": r[2],
                "hora": r[3],
                "valor": r[4],
                "banco": r[5],
                "numero_comprovante": r[6],
                "observacoes": r[7],
                "turno_id": r[8],
                "gerente_nome": r[9],
                "estado": r[10],
                "aprovado_por": r[11],
                "data_aprovacao": r[12],
                "criado_em": r[13],
            }

    # ============ SALDO ============
    elif tipo == "SALDO":
        cur.execute("""
            SELECT id, data, tipo, valor, referencia, descricao,
                   saldo_anterior, saldo_atual, utilizador_nome, criado_em
            FROM saldo_farmacia WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "data": r[1],
                "tipo": r[2],
                "valor": r[3],
                "referencia": r[4],
                "descricao": r[5],
                "saldo_anterior": r[6],
                "saldo_atual": r[7],
                "utilizador_nome": r[8],
                "criado_em": r[9],
            }

    # ============ NAO_CONFORMIDADE ============
    elif tipo == "NAO_CONFORMIDADE":
        cur.execute("""
            SELECT id, numero, data_criacao, titulo, descricao,
                   area, severidade, estado, evidencia,
                   criado_por_nome, data_encerramento,
                   encerrado_por_nome, conclusao
            FROM nao_conformidades WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "numero": r[1],
                "data_criacao": r[2],
                "titulo": r[3],
                "descricao": r[4],
                "area": r[5],
                "severidade": r[6],
                "estado": r[7],
                "evidencia": r[8],
                "criado_por_nome": r[9],
                "data_encerramento": r[10],
                "encerrado_por_nome": r[11],
                "conclusao": r[12],
            }

    # ============ AUDITORIA_REALIZADA ============
    elif tipo == "AUDITORIA_REALIZADA":
        cur.execute("""
            SELECT id, data, tipo, area, descricao, resultado,
                   auditor_nome
            FROM auditorias_realizadas WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "data": r[1],
                "tipo": r[2],
                "area": r[3],
                "descricao": r[4],
                "resultado": r[5],
                "auditor_nome": r[6],
            }

    # ============ LOG_AUDITORIA ============
    elif tipo == "LOG_AUDITORIA":
        cur.execute("""
            SELECT id, data, utilizador_nome, acao, detalhes
            FROM auditoria WHERE id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "data": r[1],
                "utilizador_nome": r[2],
                "acao": r[3],
                "detalhes": r[4],
            }

    # ============ ITEN_COMPRA ============
    elif tipo == "ITEN_COMPRA":
        cur.execute("""
            SELECT ic.id, c.uuid AS compra_uuid, ic.produto_id,
                   p.nome AS produto_nome, ic.quantidade,
                   ic.preco_custo_unitario, ic.numero_lote,
                   ic.data_validade, ic.subtotal
            FROM itens_compra ic
            LEFT JOIN compras c ON c.id = ic.compra_id
            LEFT JOIN produtos p ON p.id = ic.produto_id
            WHERE ic.id = ?
        """, (registo_id,))
        r = cur.fetchone()
        if r:
            payload = {
                "farmacia_id": farmacia_id,
                "compra_uuid": r[1],
                "produto_id": r[2],
                "produto_nome": r[3],
                "quantidade": r[4],
                "preco_custo_unitario": r[5],
                "numero_lote": r[6],
                "data_validade": r[7],
                "subtotal": r[8],
            }

    conn.close()
    return payload


# ============================================================
# ============ MAPA TIPO -> TABELA SUPABASE ==================
# ============================================================

MAPA_TABELAS = {
    "VENDA": "vendas",
    "COMPRA": "compras",
    "PERDA": "perdas",
    "MOVIMENTO": "movimentos_caixa",
    "ITEN_VENDA": "itens_venda",
    "PRODUTO": "produtos",
    "LOTE": "lotes",
    "CLIENTE": "clientes",
    "FACTURA": "facturas",
    "DEVOLUCAO": "devolucoes",
    "TURNO": "turnos_caixa",
    "DIA": "dias_operacao",
    "META": "metas_farmacia",
    "CAIXA": "caixas",
    "CATEGORIA": "categorias",
    "FORNECEDOR": "fornecedores",
    "UTILIZADOR": "utilizadores",
    "ITEN_FACTURA": "itens_factura",
    "INVENTARIO": "inventarios",
    "ITEN_INVENTARIO": "itens_inventario",
    "DEPOSITO": "depositos",
    "SALDO": "saldo_farmacia",
    "NAO_CONFORMIDADE": "nao_conformidades",
    "AUDITORIA_REALIZADA": "auditorias_realizadas",
    "LOG_AUDITORIA": "auditoria",
    "ITEN_COMPRA": "itens_compra",
    "IBT": "transferencias_filiais",
    "ITEN_IBT": "itens_transferencia",
    "HISTORICO_IBT": "historico_ibt",
}


# ============================================================
# ============ ENVIAR UMA OPERACAO ===========================
# ============================================================

def _enviar_operacao(fila_item, farmacia_id):
    """Envia uma operacao da fila para o Supabase (UPSERT)."""
    if not SYNC_ENABLED:
        return False, "Sincronizacao desactivada nas definicoes de seguranca."
    try:
        fila_id = fila_item[0]
        tipo = fila_item[2]
        tabela = fila_item[3]
        registo_id = fila_item[4]

        payload = _preparar_payload(tipo, tabela, registo_id, farmacia_id)
        if not payload:
            return True, "payload vazio (ignorado)"

        tabela_destino = MAPA_TABELAS.get(tipo)
        if not tabela_destino:
            return False, f"tipo desconhecido: {tipo}"

        headers = _headers()
        headers["Prefer"] = "resolution=merge-duplicates,return=minimal"

        r = requests.post(
            f"{_url(tabela_destino)}?on_conflict=uuid",
            headers=headers,
            json=payload,
            timeout=SYNC_TIMEOUT,
        )

        if 200 <= r.status_code < 300:
            return True, "ok"
        elif r.status_code == 409:
            return True, "duplicado (ja existia)"
        else:
            return False, f"HTTP {r.status_code}: {r.text[:200]}"

    except Exception as e:
        return False, str(e)


# ============================================================
# ============ ALIMENTAR A FILA ==============================
# ============================================================

def _alimentar_fila():
    """Adiciona à fila TODOS os registos pendentes das 25 tabelas."""
    conn = conectar()
    cur = conn.cursor()
    adicionados = 0

    mapeamento = [
        ("vendas", "VENDA"),
        ("compras", "COMPRA"),
        ("perdas", "PERDA"),
        ("movimentos_caixa", "MOVIMENTO"),
        ("itens_venda", "ITEN_VENDA"),
        ("produtos", "PRODUTO"),
        ("lotes", "LOTE"),
        ("clientes", "CLIENTE"),
        ("facturas", "FACTURA"),
        ("devolucoes", "DEVOLUCAO"),
        ("turnos_caixa", "TURNO"),
        ("dias_operacao", "DIA"),
        ("metas_farmacia", "META"),
        ("caixas", "CAIXA"),
        ("categorias", "CATEGORIA"),
        ("fornecedores", "FORNECEDOR"),
        ("utilizadores", "UTILIZADOR"),
        ("itens_factura", "ITEN_FACTURA"),
        ("inventarios", "INVENTARIO"),
        ("itens_inventario", "ITEN_INVENTARIO"),
        ("depositos", "DEPOSITO"),
        ("saldo_farmacia", "SALDO"),
        ("nao_conformidades", "NAO_CONFORMIDADE"),
        ("auditorias_realizadas", "AUDITORIA_REALIZADA"),
        ("auditoria", "LOG_AUDITORIA"),
        ("itens_compra", "ITEN_COMPRA"),
        ("transferencias_filiais", "IBT"),
        ("itens_transferencia", "ITEN_IBT"),
        ("historico_ibt", "HISTORICO_IBT"),
    ]

    for tabela, tipo in mapeamento:
        try:
            cur.execute(f"PRAGMA table_info({tabela})")
            cols = [c[1] for c in cur.fetchall()]
            if "uuid" not in cols or "sincronizado" not in cols:
                continue

            cur.execute(f"""
                SELECT id, uuid FROM {tabela}
                WHERE sincronizado = 0 AND uuid IS NOT NULL
            """)

            for registo_id, uuid_reg in cur.fetchall():
                if fila_sync.adicionar_a_fila(uuid_reg, tipo, tabela,
                                                registo_id, {}):
                    adicionados += 1
        except Exception as e:
            print(f"[Sync] _alimentar_fila erro em {tabela}: {e}")

    conn.close()
    return adicionados


# ============================================================
# ============ SINCRONIZAR TUDO ==============================
# ============================================================

def sincronizar_tudo():
    """Sincroniza TUDO em ciclo, ate esgotar a fila."""
    inicio = time.time()

    resultado = {
        "sucesso": False, "motivo": "",
        "vendas": 0, "compras": 0, "perdas": 0, "movimentos": 0,
        "itens_venda": 0, "produtos": 0, "lotes": 0, "clientes": 0,
        "facturas": 0, "devolucoes": 0, "turnos": 0, "dias": 0,
        "metas": 0, "caixas": 0,
        "categorias": 0, "fornecedores": 0, "utilizadores": 0,
        "itens_factura": 0, "inventarios": 0, "itens_inventario": 0,
        "depositos": 0, "saldos": 0, "nao_conformidades": 0,
        "auditorias_realizadas": 0, "logs_auditoria": 0,
        "itens_compra": 0,
        "transf_ibt": 0, "transf_itens": 0, "transf_hist": 0,
        "total": 0, "erros": 0, "farmacia_id": None,
        "duracao": 0, "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if not SYNC_ENABLED:
        resultado["motivo"] = "Sincronizacao desactivada nas definicoes de seguranca."
        return resultado
    
    if not _JWT_PC:
        resultado["motivo"] = "Sem JWT — precisa fazer login no Supabase."
        return resultado
    
    if not _JWT_PC:
        resultado["motivo"] = "Sem JWT — precisa fazer login no Supabase."
        return resultado

    if not _JWT_PC:
        resultado["motivo"] = "Sem JWT — precisa fazer login no Supabase."
        return resultado

    online, motivo = tem_internet()
    if not online:
        resultado["motivo"] = f"Sem ligacao: {motivo}"
        return resultado

    farmacia_id = garantir_farmacia_na_nuvem()
    if not farmacia_id:
        resultado["motivo"] = "Nao foi possivel identificar a farmacia"
        return resultado
    resultado["farmacia_id"] = farmacia_id

    _alimentar_fila()

    contadores = {
        "VENDA": "vendas", "COMPRA": "compras", "PERDA": "perdas",
        "MOVIMENTO": "movimentos", "ITEN_VENDA": "itens_venda",
        "PRODUTO": "produtos", "LOTE": "lotes", "CLIENTE": "clientes",
        "FACTURA": "facturas", "DEVOLUCAO": "devolucoes",
        "TURNO": "turnos", "DIA": "dias", "META": "metas",
        "CAIXA": "caixas",
        "CATEGORIA": "categorias", "FORNECEDOR": "fornecedores",
        "UTILIZADOR": "utilizadores", "ITEN_FACTURA": "itens_factura",
        "INVENTARIO": "inventarios", "ITEN_INVENTARIO": "itens_inventario",
        "DEPOSITO": "depositos", "SALDO": "saldos",
        "NAO_CONFORMIDADE": "nao_conformidades",
        "AUDITORIA_REALIZADA": "auditorias_realizadas",
        "LOG_AUDITORIA": "logs_auditoria",
        "ITEN_COMPRA": "itens_compra",
        "IBT": "transf_ibt",
        "ITEN_IBT": "transf_itens",
        "HISTORICO_IBT": "transf_hist",
    }
    # Enviar heartbeat ANTES de processar a fila
    try:
        enviar_heartbeat()
    except Exception as e_hb:
        print(f"[Sync] Aviso heartbeat: {e_hb}")
    # Enviar heartbeat ANTES de processar a fila
    try:
        enviar_heartbeat()
    except Exception as e_hb:
        print(f"[Sync] Aviso heartbeat: {e_hb}")

    total_enviado = 0
    total_erros = 0

    LOTE = 100
    MAX_CICLOS = 50

    for ciclo in range(MAX_CICLOS):
        pendentes = fila_sync.listar_pendentes(LOTE)

        if not pendentes:
            break

        enviados_neste_ciclo = 0

        for item in pendentes:
            fila_id = item[0]
            item_tipo = item[2]

            ok, motivo_envio = _enviar_operacao(item, farmacia_id)

            if ok:
                fila_sync.marcar_enviado(fila_id)
                total_enviado += 1
                enviados_neste_ciclo += 1
                chave = contadores.get(item_tipo)
                if chave:
                    resultado[chave] += 1
            else:
                fila_sync.marcar_erro(fila_id, motivo_envio)
                total_erros += 1

        if enviados_neste_ciclo == 0:
            break

    resultado["total"] = total_enviado
    resultado["erros"] = total_erros
    resultado["sucesso"] = True
    resultado["duracao"] = round(time.time() - inicio, 2)

    registar_sincronizacao(True, total_enviado)

    # Enviar heartbeat (estado do PC)
    try:
        enviar_heartbeat()
    except Exception as e_hb:
        print(f"[Sync] Aviso heartbeat: {e_hb}")

    return resultado


# ============================================================
# ============ ESTADO DA FILA ================================
# ============================================================

def contar_pendentes():
    return fila_sync.estatisticas()


def obter_ultima_sincronizacao():
    try:
        return fila_sync.ultima_sincronizacao_log()
    except Exception as e:
        print(f"[Sync] Aviso: {e}")
        return None


def registar_sincronizacao(sucesso, total):
    try:
        fila_sync.registar_log(
            total_enviado=total,
            total_erros=0,
            duracao=0,
            resultado="OK" if sucesso else "ERRO"
        )
    except Exception as e:
        print(f"[Sync] Aviso ao registar log: {e}")


def ha_quanto_tempo():
    return fila_sync.ha_quanto_tempo()

    

# ============================================================
# ============ BAIXAR ORCAMENTOS (WEB -> PC) =================
# ============================================================

def baixar_orcamentos_do_supabase():
    """
    Vai buscar as metas/orcamentos ao Supabase e guarda no SQLite local.
    Chamado ao arrancar a app.
    """
    if not SYNC_ENABLED or not _JWT_PC:
        return 0

    try:
        # Buscar todas as metas activas
        url = f"{_url('metas_farmacia')}?select=*&order=id.desc"
        r = requests.get(url, headers=_headers(), timeout=SYNC_TIMEOUT)

        if r.status_code != 200:
            print(f"[Sync] Erro ao baixar metas: HTTP {r.status_code}")
            return 0

        metas = r.json()
        if not metas:
            return 0

        # Guardar no SQLite (tabela local metas_farmacia)
        conn = conectar()
        cur = conn.cursor()

        # Garantir tabela local
        cur.execute("""
            CREATE TABLE IF NOT EXISTS metas_farmacia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes TEXT UNIQUE NOT NULL,
                orcamento_mes REAL NOT NULL,
                observacoes TEXT,
                definido_por TEXT,
                criado_em TEXT,
                atualizado_em TEXT
            )
        """)

        gravadas = 0
        for m in metas:
            mes = m.get("mes")
            orcamento = m.get("orcamento_mes", 0)
            if not mes or orcamento <= 0:
                continue

            # Procurar se existe
            cur.execute("SELECT id FROM metas_farmacia WHERE mes = ?", (mes,))
            existe = cur.fetchone()

            if existe:
                cur.execute("""
                    UPDATE metas_farmacia
                    SET orcamento_mes = ?, observacoes = ?, definido_por = ?,
                        atualizado_em = ?
                    WHERE mes = ?
                """, (
                    orcamento,
                    m.get("observacoes", ""),
                    m.get("definido_por", "CEO"),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    mes,
                ))
            else:
                cur.execute("""
                    INSERT INTO metas_farmacia
                    (mes, orcamento_mes, observacoes, definido_por, criado_em, atualizado_em)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    mes,
                    orcamento,
                    m.get("observacoes", ""),
                    m.get("definido_por", "CEO"),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ))
            gravadas += 1

        conn.commit()
        conn.close()

        print(f"[Sync] {gravadas} orcamentos baixados do Supabase")
        return gravadas

    except Exception as e:
        print(f"[Sync] Erro ao baixar orcamentos: {e}")
        return 0

        

# ============================================================
# ============ HEARTBEAT (estado do PC) ======================
# ============================================================

def enviar_heartbeat():
    """
    Envia o estado actual do PC para o Supabase.
    Chamado automaticamente a cada sincronização.
    """
    if not SYNC_ENABLED or not _JWT_PC:
        return False

    try:
        # Info da farmácia
        farm_id, terminal = _obter_info_farmacia()

        # Última venda hoje
        try:
            from datetime import datetime as _dt
            hoje = _dt.now().strftime("%Y-%m-%d")
            conn = conectar()
            cur = conn.cursor()

            cur.execute("""
                SELECT COALESCE(SUM(total), 0), COUNT(*)
                FROM vendas
                WHERE DATE(data) = DATE(?)
            """, (hoje,))
            r = cur.fetchone()
            vendas_hoje = r[0] or 0

            # Pendentes na fila
            cur.execute("""
                SELECT COUNT(*) FROM fila_sincronizacao
                WHERE estado IN ('PENDENTE', 'ERRO')
            """)
            pendentes = cur.fetchone()[0] or 0

            conn.close()
        except Exception:
            vendas_hoje = 0
            pendentes = 0

        dados = {
            "farmacia_id": farm_id or 1,
            "terminal_id": terminal,
            "versao": "1.0",
            "ultima_sync": datetime.now().isoformat(),
            "vendas_hoje": float(vendas_hoje),
            "total_pendentes": int(pendentes),
            "ultimo_erro": None,
            "online": True,
            "updated_at": datetime.now().isoformat(),
        }

        # Tentar atualizar (UPSERT)
        url = f"{_url('estado_pcs')}?on_conflict=farmacia_id,terminal_id"
        headers = _headers()
        headers["Prefer"] = "resolution=merge-duplicates,return=minimal"

        r = requests.post(url, headers=headers, json=dados, timeout=SYNC_TIMEOUT)

        if 200 <= r.status_code < 300:
            print(f"[Heartbeat] Enviado (farmacia={farm_id}, terminal={terminal})")
            return True
        else:
            print(f"[Heartbeat] Erro HTTP {r.status_code}: {r.text[:100]}")
            return False

    except Exception as e:
        print(f"[Heartbeat] Erro: {e}")
        return False

        

# ============================================================
# ============ ENVIO DE EMAIL ================================
# ============================================================

def _obter_config_email():
    """Lê configuração de email do .env."""
    from config_cloud import _carregar_env_local
    _carregar_env_local()
    import os as _os
    return {
        "remetente": _os.environ.get("EMAIL_REMETENTE", ""),
        "senha": _os.environ.get("EMAIL_SENHA_APP", ""),
        "smtp": _os.environ.get("EMAIL_SMTP", "smtp.gmail.com"),
        "porta": int(_os.environ.get("EMAIL_PORTA", "587")),
    }


def enviar_email(destinatarios, assunto, corpo_html):
    """
    Envia email via SMTP.
    destinatarios: lista de emails
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    if not destinatarios:
        return False, "Sem destinatários"

    cfg = _obter_config_email()
    if not cfg["remetente"] or not cfg["senha"]:
        return False, "Email nao configurado no .env"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = f"JAM Soft <{cfg['remetente']}>"
        msg["To"] = ", ".join(destinatarios)

        # Versão HTML
        parte_html = MIMEText(corpo_html, "html", "utf-8")
        msg.attach(parte_html)

        with smtplib.SMTP(cfg["smtp"], cfg["porta"], timeout=15) as server:
            server.starttls()
            server.login(cfg["remetente"], cfg["senha"])
            server.sendmail(cfg["remetente"], destinatarios, msg.as_string())

        print(f"[Email] Enviado para {len(destinatarios)} destinatario(s)")
        return True, "Enviado"

    except Exception as e:
        print(f"[Email] Erro: {e}")
        return False, str(e)


def obter_destinatarios_emails():
    """
    Retorna lista de emails de todos os CEOs registados.
    Lê do Supabase (plataforma_utilizadores).
    """
    if not SYNC_ENABLED or not _JWT_PC:
        return []

    try:
        url = f"{_url('plataforma_utilizadores')}?select=email&ativo=eq.true"
        r = requests.get(url, headers=_headers(), timeout=SYNC_TIMEOUT)

        if r.status_code == 200:
            dados = r.json()
            return [d.get("email") for d in dados if d.get("email")]

        return []
    except Exception as e:
        print(f"[Email] Erro ao obter destinatarios: {e}")
        return []


def gerar_html_relatorio_semanal():
    """
    Gera HTML do relatório semanal com alertas.
    """
    from datetime import datetime as _dt, timedelta

    hoje = _dt.now()
    semana_passada = hoje - timedelta(days=7)

    # Recolher dados de todas as farmácias
    conn = conectar()
    cur = conn.cursor()

    try:
        # Vendas da semana por farmácia (local)
        cur.execute("""
            SELECT COALESCE(SUM(total), 0), COUNT(*)
            FROM vendas
            WHERE DATE(data) >= DATE(?)
        """, (semana_passada.strftime("%Y-%m-%d"),))
        r = cur.fetchone()
        vendas_semana = r[0] or 0
        num_vendas = r[1] or 0

        conn.close()
    except Exception:
        vendas_semana = 0
        num_vendas = 0

    # HTML
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px;">
        <div style="max-width: 700px; margin: 0 auto; background: #1e293b; border-radius: 10px; padding: 30px;">
            <h1 style="color: #a78bfa; margin-top: 0;">💊 JAM Soft — Resumo Semanal</h1>
            <p style="color: #94a3b8;">Período: {semana_passada.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')}</p>

            <hr style="border: 1px solid #334155; margin: 20px 0;">

            <h2 style="color: #10b981;">📊 Vendas da Semana</h2>
            <table style="width: 100%; color: #f8fafc; font-size: 16px;">
                <tr>
                    <td style="padding: 8px 0;">Total vendido:</td>
                    <td style="text-align: right; font-weight: bold; color: #10b981;">
                        Kz {vendas_semana:,.0f}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;">Número de vendas:</td>
                    <td style="text-align: right; font-weight: bold;">
                        {num_vendas}
                    </td>
                </tr>
            </table>

            <hr style="border: 1px solid #334155; margin: 20px 0;">

            <h2 style="color: #fbbf24;">📋 Para mais detalhes:</h2>
            <p>
                <a href="https://jamsoft-plataforma-nthcjcruax7wmg9rqxr4qz.streamlit.app"
                   style="background: #7c3aed; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">
                    Abrir Plataforma
                </a>
            </p>

            <hr style="border: 1px solid #334155; margin: 20px 0;">

            <p style="font-size: 12px; color: #64748b; text-align: center;">
                JAM Soft © {hoje.year} — Email automático
            </p>
        </div>
    </body>
    </html>
    """

    return html


def enviar_relatorio_semanal():
    """
    Envia o relatório semanal para todos os CEOs.
    Chamado por agendador.
    """
    destinatarios = obter_destinatarios_emails()

    if not destinatarios:
        print("[Email] Sem destinatarios")
        return False

    html = gerar_html_relatorio_semanal()
    assunto = f"📊 JAM Soft — Resumo Semanal ({datetime.now().strftime('%d/%m/%Y')})"

    return enviar_email(destinatarios, assunto, html)


def testar_email():
    """Envia email de teste para o remetente."""
    cfg = _obter_config_email()

    if not cfg["remetente"]:
        return False, "Email remetente nao configurado"

    html = """
    <html>
    <body style="font-family: Arial;">
        <h2>✅ Teste de Email — JAM Soft</h2>
        <p>Se recebeste este email, a configuração está correcta!</p>
        <p>Agora a IA pode enviar alertas automáticos.</p>
    </body>
    </html>
    """

    return enviar_email([cfg["remetente"]], "🧪 Teste — JAM Soft", html)