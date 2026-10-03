# ============================================================
# ============ FILA PERSISTENTE DE SINCRONIZACAO =============
# ============================================================
# 
# Cada operacao a sincronizar entra numa fila persistente.
# Mesmo que o PC desligue, a fila mantem-se.
# 
# Estados:
#   PENDENTE    -> por enviar
#   ENVIANDO    -> a enviar agora
#   ENVIADO     -> enviado com sucesso
#   ERRO        -> falhou (tentara novamente)
#   CONFLITO    -> UUID duplicado no servidor
#   ABANDONADO  -> demasiadas tentativas
# 
# ============================================================

import json
from datetime import datetime
from database import conectar


MAX_TENTATIVAS = 5


# ============================================================
# ============ ADICIONAR A FILA ==============================
# ============================================================

def adicionar_a_fila(uuid, tipo, tabela_origem, registo_id, payload):
    """Adiciona uma operacao a fila persistente.
    
    Args:
        uuid: UUID unico da operacao
        tipo: 'VENDA', 'COMPRA', 'PERDA', 'MOVIMENTO', 'FACTURA'
        tabela_origem: tabela local (vendas, compras, etc.)
        registo_id: ID do registo local
        payload: dict com dados a enviar
    """
    if not uuid:
        return False
    
    try:
        payload_json = json.dumps(payload, default=str)
    except Exception:
        payload_json = "{}"
    
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cur.execute("""
            INSERT INTO fila_sincronizacao 
            (uuid, tipo, tabela_origem, registo_id, payload, estado, tentativas, criado_em)
            VALUES (?, ?, ?, ?, ?, 'PENDENTE', 0, ?)
        """, (uuid, tipo, tabela_origem, registo_id, payload_json, agora))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        # Pode ja existir (UNIQUE em uuid)
        conn.close()
        return False


# ============================================================
# ============ LISTAR PENDENTES ==============================
# ============================================================

def listar_pendentes(limite=50, incluir_erros=True):
    """Retorna operacoes pendentes (PENDENTE ou ERRO com tentativas < max)."""
    conn = conectar()
    cur = conn.cursor()
    
    if incluir_erros:
        cur.execute("""
            SELECT id, uuid, tipo, tabela_origem, registo_id, payload,
                   estado, tentativas
            FROM fila_sincronizacao
            WHERE estado IN ('PENDENTE', 'ERRO')
              AND tentativas < ?
            ORDER BY id ASC
            LIMIT ?
        """, (MAX_TENTATIVAS, limite))
    else:
        cur.execute("""
            SELECT id, uuid, tipo, tabela_origem, registo_id, payload,
                   estado, tentativas
            FROM fila_sincronizacao
            WHERE estado = 'PENDENTE'
            ORDER BY id ASC
            LIMIT ?
        """, (limite,))
    
    resultado = cur.fetchall()
    conn.close()
    return resultado


def listar_por_tipo(tipo, limite=50):
    """Retorna pendentes de um tipo especifico."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, uuid, tipo, tabela_origem, registo_id, payload,
               estado, tentativas
        FROM fila_sincronizacao
        WHERE tipo = ? AND estado IN ('PENDENTE', 'ERRO')
          AND tentativas < ?
        ORDER BY id ASC
        LIMIT ?
    """, (tipo, MAX_TENTATIVAS, limite))
    resultado = cur.fetchall()
    conn.close()
    return resultado


# ============================================================
# ============ MARCAR ESTADOS ================================
# ============================================================

def marcar_enviando(fila_id):
    """Marca uma entrada como ENVIANDO."""
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        UPDATE fila_sincronizacao 
        SET estado = 'ENVIANDO', ultima_tentativa = ?, tentativas = tentativas + 1
        WHERE id = ?
    """, (agora, fila_id))
    conn.commit()
    conn.close()


def marcar_enviado(fila_id):
    """Marca uma entrada como ENVIADO."""
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        UPDATE fila_sincronizacao 
        SET estado = 'ENVIADO', enviado_em = ?, ultimo_erro = NULL
        WHERE id = ?
    """, (agora, fila_id))
    conn.commit()
    conn.close()


def marcar_erro(fila_id, erro_msg):
    """Marca como ERRO com mensagem."""
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        UPDATE fila_sincronizacao 
        SET estado = 'ERRO', ultima_tentativa = ?, ultimo_erro = ?
        WHERE id = ?
    """, (agora, erro_msg[:500], fila_id))
    conn.commit()
    conn.close()


def marcar_conflito(fila_id, msg):
    """Marca como CONFLITO (UUID duplicado)."""
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        UPDATE fila_sincronizacao 
        SET estado = 'CONFLITO', ultima_tentativa = ?, ultimo_erro = ?
        WHERE id = ?
    """, (agora, msg[:500], fila_id))
    conn.commit()
    conn.close()


def abandonar(fila_id):
    """Marca como ABANDONADO (demasiadas tentativas)."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        UPDATE fila_sincronizacao SET estado = 'ABANDONADO'
        WHERE id = ?
    """, (fila_id,))
    conn.commit()
    conn.close()


# ============================================================
# ============ ESTATISTICAS ==================================
# ============================================================

def estatisticas():
    """Retorna contagem por estado."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT estado, COUNT(*) FROM fila_sincronizacao
        GROUP BY estado
    """)
    resultado = dict(cur.fetchall())
    conn.close()
    
    # Calcular totais
    total = sum(resultado.values())
    pendentes = resultado.get("PENDENTE", 0) + resultado.get("ERRO", 0)
    enviados = resultado.get("ENVIADO", 0)
    conflitos = resultado.get("CONFLITO", 0)
    abandonados = resultado.get("ABANDONADO", 0)
    
    return {
        "total": total,
        "pendentes": pendentes,
        "enviados": enviados,
        "conflitos": conflitos,
        "abandonados": abandonados,
        "por_estado": resultado,
    }


def detalhes_erros(limite=20):
    """Retorna detalhes dos erros mais recentes."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT uuid, tipo, estado, tentativas, ultima_tentativa, ultimo_erro
        FROM fila_sincronizacao
        WHERE estado IN ('ERRO', 'CONFLITO', 'ABANDONADO')
        ORDER BY ultima_tentativa DESC
        LIMIT ?
    """, (limite,))
    resultado = cur.fetchall()
    conn.close()
    return resultado


# ============================================================
# ============ LIMPEZA =======================================
# ============================================================

def limpar_enviados(dias=30):
    """Remove entradas enviadas ha mais de X dias."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM fila_sincronizacao
        WHERE estado = 'ENVIADO'
          AND enviado_em < datetime('now', '-' || ? || ' days')
    """, (dias,))
    apagados = cur.rowcount
    conn.commit()
    conn.close()
    return apagados


# ============================================================
# ============ LOG DE SINCRONIZACAO ==========================
# ============================================================

def registar_log(total_enviado, total_erros, duracao, resultado):
    """Regista uma sincronizacao no log."""
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO log_sincronizacao 
        (data, total_enviado, total_erros, duracao_segundos, resultado)
        VALUES (?, ?, ?, ?, ?)
    """, (agora, total_enviado, total_erros, duracao, resultado))
    conn.commit()
    conn.close()


def listar_log(limite=20):
    """Retorna historico de sincronizacoes."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT data, total_enviado, total_erros, duracao_segundos, resultado
        FROM log_sincronizacao
        ORDER BY id DESC
        LIMIT ?
    """, (limite,))
    resultado = cur.fetchall()
    conn.close()
    return resultado


def ultima_sincronizacao_log():
    """Retorna a ultima entrada do log."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT data, total_enviado, total_erros, duracao_segundos, resultado
        FROM log_sincronizacao
        ORDER BY id DESC
        LIMIT 1
    """)
    resultado = cur.fetchone()
    conn.close()
    return resultado


# ============================================================
# ============ TESTE =========================================
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  FILA DE SINCRONIZACAO - ESTADO ATUAL")
    print("="*60)
    
    e = estatisticas()
    print(f"\n  Total:        {e['total']}")
    print(f"  Pendentes:    {e['pendentes']}")
    print(f"  Enviados:     {e['enviados']}")
    print(f"  Conflitos:    {e['conflitos']}")
    print(f"  Abandonados:  {e['abandonados']}")
    
    print(f"\n  Detalhe por estado:")
    for k, v in e["por_estado"].items():
        print(f"    {k}: {v}")
    
    erros = detalhes_erros(5)
    if erros:
        print(f"\n  Ultimos erros:")
        for err in erros:
            print(f"    [{err[3]}x] {err[1]} - {err[5][:60] if err[5] else 'sem detalhe'}")
    
    print("\n" + "="*60 + "\n")