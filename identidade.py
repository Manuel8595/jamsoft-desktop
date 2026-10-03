# ============================================================
# ============ IDENTIDADE MULTI-FARMACIA =====================
# ============================================================
# 
# Cada instalacao do JAM Soft tem:
#   - UM codigo de farmacia (FARM-XXX-000)
#   - UM codigo de terminal (TERM-00)
#   - UUIDs unicos para cada operacao
#
# ============================================================

import uuid
import socket
import platform
from datetime import datetime
from database import conectar


# ============================================================
# ============ CONFIGURACAO GLOBAL (chave-valor) =============
# ============================================================

def obter_config(chave, padrao=None):
    """Le um valor da configuracao global."""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT valor FROM configuracao_global WHERE chave = ?", (chave,))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else padrao


def gravar_config(chave, valor):
    """Grava um valor na configuracao global (insere ou atualiza)."""
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("SELECT id FROM configuracao_global WHERE chave = ?", (chave,))
    existe = cur.fetchone()
    
    if existe:
        cur.execute("UPDATE configuracao_global SET valor = ?, atualizado_em = ? WHERE chave = ?",
                    (str(valor), agora, chave))
    else:
        cur.execute("INSERT INTO configuracao_global (chave, valor, atualizado_em) VALUES (?, ?, ?)",
                    (chave, str(valor), agora))
    
    conn.commit()
    conn.close()


# ============================================================
# ============ IDENTIDADE DA INSTALACAO ======================
# ============================================================

def obter_farmacia_id():
    """Retorna o ID da farmacia configurada (interno)."""
    return obter_config("farmacia_id")


def obter_farmacia_codigo():
    """Retorna o CODIGO da farmacia (ex: FARM-LDA-001)."""
    return obter_config("farmacia_codigo", "NAO-CONFIGURADA")


def obter_farmacia_nome():
    """Retorna o NOME da farmacia."""
    return obter_config("farmacia_nome", "Nao configurada")


def obter_terminal_codigo():
    """Retorna o CODIGO deste terminal (ex: TERM-01)."""
    return obter_config("terminal_codigo", "TERM-01")


def esta_configurada():
    """Retorna True se a farmacia ja foi configurada."""
    return obter_config("farmacia_id") is not None


# ============================================================
# ============ CONFIGURAR FARMACIA ===========================
# ============================================================

def configurar_farmacia(codigo, nome, nif, endereco, telefone,
                          email, responsavel, notas=""):
    """Configura a farmacia pela primeira vez ou atualiza."""
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Verifica se ja existe pelo codigo
    cur.execute("SELECT id FROM farmacias WHERE codigo = ?", (codigo,))
    existe = cur.fetchone()
    
    if existe:
        fid = existe[0]
        cur.execute("""
            UPDATE farmacias 
            SET nome = ?, nif = ?, endereco = ?, telefone = ?,
                email = ?, responsavel = ?, notas = ?
            WHERE id = ?
        """, (nome, nif, endereco, telefone, email, responsavel, notas, fid))
    else:
        cur.execute("""
            INSERT INTO farmacias (codigo, nome, nif, endereco, telefone,
                                    email, responsavel, criado_em, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (codigo, nome, nif, endereco, telefone, email, responsavel, agora, notas))
        fid = cur.lastrowid
    
    conn.commit()
    conn.close()
    
    # Grava na configuracao global
    gravar_config("farmacia_id", fid)
    gravar_config("farmacia_codigo", codigo)
    gravar_config("farmacia_nome", nome)
    
    return fid


def configurar_terminal(codigo, nome=None):
    """Configura ou atualiza o terminal atual."""
    if nome is None:
        nome = f"Terminal {codigo}"
    
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fid = obter_farmacia_id()
    
    cur.execute("SELECT id FROM terminais WHERE codigo = ?", (codigo,))
    existe = cur.fetchone()
    
    if existe:
        tid = existe[0]
        cur.execute("""
            UPDATE terminais SET nome = ?, farmacia_id = ?, ultima_atividade = ?
            WHERE id = ?
        """, (nome, fid, agora, tid))
    else:
        cur.execute("""
            INSERT INTO terminais (codigo, nome, farmacia_id, criado_em, ultima_atividade)
            VALUES (?, ?, ?, ?, ?)
        """, (codigo, nome, fid, agora, agora))
        tid = cur.lastrowid
    
    conn.commit()
    conn.close()
    
    gravar_config("terminal_codigo", codigo)
    return tid


# ============================================================
# ============ UUID E TIMESTAMP ==============================
# ============================================================

def gerar_uuid():
    """Gera um UUID unico universal (string)."""
    return str(uuid.uuid4())


def timestamp_utc():
    """Retorna timestamp UTC formatado."""
    from datetime import timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def timestamp_local():
    """Retorna timestamp local formatado."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# ============ INFORMACAO DO SISTEMA =========================
# ============================================================

def obter_info_computador():
    """Retorna informacoes deste computador (para identificacao)."""
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "desconhecido"
    
    return {
        "hostname": hostname,
        "sistema": platform.system(),
        "versao": platform.version(),
    }


def resumo_identidade():
    """Retorna resumo da identidade atual (para mostrar no ecra)."""
    return {
        "configurada": esta_configurada(),
        "farmacia_codigo": obter_farmacia_codigo(),
        "farmacia_nome": obter_farmacia_nome(),
        "terminal": obter_terminal_codigo(),
    }


# ============================================================
# ============ TESTE =========================================
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  IDENTIDADE JAM SOFT - Estado Atual")
    print("="*60)
    
    info = resumo_identidade()
    
    print(f"\n  Configurada:        {'SIM' if info['configurada'] else 'NAO'}")
    print(f"  Codigo Farmácia:    {info['farmacia_codigo']}")
    print(f"  Nome Farmácia:      {info['farmacia_nome']}")
    print(f"  Codigo Terminal:    {info['terminal']}")
    
    print(f"\n  Exemplo UUID:       {gerar_uuid()}")
    print(f"  Timestamp local:    {timestamp_local()}")
    print(f"  Timestamp UTC:      {timestamp_utc()}")
    
    print(f"\n  Info computador:")
    for k, v in obter_info_computador().items():
        print(f"    {k}: {v}")
    
    print("\n" + "="*60 + "\n")