# ============================================================
# ============ TRANSFERENCIAS ENTRE FILIAIS (IBT) ============
# ============================================================
#
# Sistema completo de Inter-Branch Transfer:
#   - Criar nova IBT (origem -> destino)
#   - Adicionar produtos
#   - Autorizar e enviar (baixa stock na origem)
#   - Listar IBTs (com filtros)
#   - Ver detalhes + historico completo
#   - Receber IBT (na filial destino)
#   - Dashboard para o admin
#   - PDF do comprovativo
#   - Rascunhos (gravar e continuar depois)
#
# ============================================================

import os
from datetime import datetime
from tkinter import *
from tkinter import messagebox, ttk

from database import (conectar, registar_auditoria, autenticar,
                       listar_produtos, buscar_produto_por_id,
                       listar_lotes_fefo)
from moeda import formatar_kz


# ============================================================
# ============ CORES =========================================
# ============================================================

COR_FUNDO = "#0f172a"
COR_CARD = "#1e293b"
COR_CARD_HOVER = "#334155"
COR_PRIMARIA = "#7c3aed"
COR_DOURADO = "#fbbf24"
COR_VERDE = "#10b981"
COR_VERMELHO = "#ef4444"
COR_ALERTA = "#f97316"
COR_AZUL = "#0ea5e9"
COR_ROXO = "#a78bfa"
COR_TEXTO = "#f8fafc"
COR_TEXTO_SEC = "#94a3b8"
COR_BORDA = "#334155"

ESTADO_RASCUNHO = "RASCUNHO"
ESTADO_EM_TRANSITO = "EM_TRANSITO"
ESTADO_RECEBIDA_PARCIAL = "RECEBIDA_PARCIAL"
ESTADO_CONCLUIDA = "CONCLUIDA"
ESTADO_CANCELADA = "CANCELADA"
ESTADO_DIVERGENCIA = "DIVERGENCIA"

CORES_ESTADO = {
    ESTADO_RASCUNHO: COR_TEXTO_SEC,
    ESTADO_EM_TRANSITO: COR_DOURADO,
    ESTADO_RECEBIDA_PARCIAL: COR_ALERTA,
    ESTADO_CONCLUIDA: COR_VERDE,
    ESTADO_CANCELADA: COR_VERMELHO,
    ESTADO_DIVERGENCIA: COR_VERMELHO,
}


# ============================================================
# ============ FUNCOES DE BASE DE DADOS ======================
# ============================================================

def listar_farmacias_locais():
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, uuid, codigo, nome, nif, endereco,
                   telefone, email, responsavel, activo
            FROM farmacias
            WHERE activo = 1 OR activo IS NULL
            ORDER BY nome
        """)
        resultado = cur.fetchall()
    except Exception:
        resultado = []
    conn.close()
    return resultado


def obter_farmacia_actual():
    try:
        from identidade import (obter_farmacia_id, obter_farmacia_codigo,
                                 obter_farmacia_nome)
        return {
            "id": obter_farmacia_id(),
            "codigo": obter_farmacia_codigo(),
            "nome": obter_farmacia_nome(),
        }
    except Exception:
        return None


def gerar_referencia_ibt():
    conn = conectar()
    cur = conn.cursor()
    ano = datetime.now().strftime("%Y")
    cur.execute("""
        SELECT referencia FROM transferencias_filiais
        WHERE referencia LIKE ?
        ORDER BY id DESC LIMIT 1
    """, (f"IBT-{ano}-%",))
    r = cur.fetchone()
    conn.close()

    if r and r[0]:
        try:
            novo = int(r[0].split("-")[-1]) + 1
        except Exception:
            novo = 1
    else:
        novo = 1

    return f"IBT-{ano}-{novo:04d}"


def criar_transferencia(origem_id, origem_codigo, origem_nome,
                          destino_id, destino_codigo, destino_nome,
                          utilizador_id, utilizador_nome,
                          observacoes=""):
    from identidade import gerar_uuid, obter_terminal_codigo, obter_farmacia_id

    referencia = gerar_referencia_ibt()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    uuid_str = gerar_uuid()
    terminal = obter_terminal_codigo()
    farmacia_id = obter_farmacia_id()

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transferencias_filiais
        (referencia, data_criacao,
         farmacia_origem_id, farmacia_origem_codigo, farmacia_origem_nome,
         farmacia_destino_id, farmacia_destino_codigo, farmacia_destino_nome,
         utilizador_criou_id, utilizador_criou_nome,
         estado, observacoes,
         uuid, terminal_id, farmacia_id, sincronizado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (referencia, agora,
          origem_id, origem_codigo, origem_nome,
          destino_id, destino_codigo, destino_nome,
          utilizador_id, utilizador_nome,
          ESTADO_RASCUNHO, observacoes,
          uuid_str, terminal, farmacia_id))

    trans_id = cur.lastrowid
    conn.commit()
    conn.close()

    registar_historico_ibt(trans_id, "CRIOU", utilizador_nome,
                             None, ESTADO_RASCUNHO,
                             f"Transferencia {referencia} criada")
    return trans_id


def adicionar_item_transferencia(transferencia_id, produto_id, produto_nome,
                                    codigo_barras, quantidade, lote,
                                    validade, preco_custo):
    subtotal = quantidade * (preco_custo or 0)

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO itens_transferencia
        (transferencia_id, produto_id, produto_nome, codigo_barras,
         quantidade_enviada, quantidade_recebida, diferenca,
         lote, validade, preco_custo, subtotal)
        VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?)
    """, (transferencia_id, produto_id, produto_nome, codigo_barras,
          quantidade, lote, validade, preco_custo, subtotal))
    conn.commit()
    conn.close()


def atualizar_totais_transferencia(transferencia_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*), COALESCE(SUM(quantidade_enviada), 0),
               COALESCE(SUM(subtotal), 0)
        FROM itens_transferencia WHERE transferencia_id = ?
    """, (transferencia_id,))
    n_itens, total_qtd, total_valor = cur.fetchone()

    cur.execute("""
        UPDATE transferencias_filiais
        SET total_itens = ?, total_quantidade = ?, valor_estimado = ?
        WHERE id = ?
    """, (n_itens, total_qtd, total_valor, transferencia_id))
    conn.commit()
    conn.close()


def registar_historico_ibt(trans_id, acao, utilizador_nome,
                             estado_anterior=None, estado_novo=None,
                             detalhes=""):
    conn = conectar()
    cur = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO historico_ibt
        (transferencia_id, data, acao, utilizador_nome,
         estado_anterior, estado_novo, detalhes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (trans_id, agora, acao, utilizador_nome,
          estado_anterior, estado_novo, detalhes))
    conn.commit()
    conn.close()


def enviar_transferencia(trans_id, autorizado_por):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT estado FROM transferencias_filiais WHERE id = ?
    """, (trans_id,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return False, "Transferencia nao encontrada."

    if r[0] != ESTADO_RASCUNHO:
        conn.close()
        return False, (f"BLOQUEADO: Estado actual ({r[0]}) nao permite envio.\n\n"
                        "Apenas RASCUNHOS podem ser enviados.")

    cur.execute("""
        SELECT produto_id, quantidade_enviada FROM itens_transferencia
        WHERE transferencia_id = ?
    """, (trans_id,))
    itens = cur.fetchall()

    if not itens:
        conn.close()
        return False, "Sem produtos na transferencia."

    for produto_id, qtd in itens:
        cur.execute("SELECT estoque_atual FROM produtos WHERE id = ?",
                      (produto_id,))
        est = cur.fetchone()
        if not est or est[0] < qtd:
            conn.close()
            return False, f"Stock insuficiente do produto ID {produto_id}."

    for produto_id, qtd in itens:
        cur.execute("UPDATE produtos SET estoque_atual = estoque_atual - ? WHERE id = ?",
                      (qtd, produto_id))

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        UPDATE transferencias_filiais
        SET estado = ?, data_envio = ?, autorizado_por = ?, sincronizado = 0
        WHERE id = ?
    """, (ESTADO_EM_TRANSITO, agora, autorizado_por, trans_id))

    conn.commit()
    conn.close()

    registar_historico_ibt(trans_id, "ENVIOU", autorizado_por,
                             ESTADO_RASCUNHO, ESTADO_EM_TRANSITO,
                             f"Autorizado por: {autorizado_por}")
    return True, "Transferencia enviada."


def receber_transferencia(trans_id, utilizador_nome, itens_recebidos):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT estado FROM transferencias_filiais WHERE id = ?",
                  (trans_id,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return False, "Transferencia nao encontrada."

    if r[0] != ESTADO_EM_TRANSITO:
        conn.close()
        return False, (f"BLOQUEADO: Estado actual ({r[0]}) nao permite recepcao.\n\n"
                        "Apenas IBTs EM TRANSITO podem ser recebidas.")

    tem_divergencia = False
    for item_id, qtd_rec in itens_recebidos.items():
        cur.execute("""
            SELECT quantidade_enviada, produto_id
            FROM itens_transferencia WHERE id = ?
        """, (item_id,))
        r = cur.fetchone()
        if not r:
            continue

        qtd_env, produto_id = r
        diferenca = qtd_rec - qtd_env

        cur.execute("""
            UPDATE itens_transferencia
            SET quantidade_recebida = ?, diferenca = ?
            WHERE id = ?
        """, (qtd_rec, diferenca, item_id))

        if qtd_rec > 0:
            cur.execute("UPDATE produtos SET estoque_atual = estoque_atual + ? WHERE id = ?",
                          (qtd_rec, produto_id))

        if diferenca != 0:
            tem_divergencia = True

    novo_estado = ESTADO_DIVERGENCIA if tem_divergencia else ESTADO_CONCLUIDA
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
        UPDATE transferencias_filiais
        SET estado = ?, data_recepcao = ?, sincronizado = 0
        WHERE id = ?
    """, (novo_estado, agora, trans_id))

    conn.commit()
    conn.close()

    registar_historico_ibt(trans_id, "RECEBEU", utilizador_nome,
                             ESTADO_EM_TRANSITO, novo_estado,
                             "Recebido com divergencia" if tem_divergencia else "Recebido OK")
    return True, f"Transferencia recebida ({novo_estado})."


def cancelar_transferencia(trans_id, motivo, utilizador_nome):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT estado FROM transferencias_filiais WHERE id = ?",
                  (trans_id,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return False, "Nao encontrada."

    estado = r[0]

    # BLOQUEIO ANTI-FRAUDE
    if estado in (ESTADO_CONCLUIDA, ESTADO_CANCELADA):
        conn.close()
        return False, (f"BLOQUEADO: IBT {estado} nao pode ser cancelada.\n\n"
                        "Apenas RASCUNHOS e EM_TRANSITO podem ser cancelados.")
    if estado == ESTADO_EM_TRANSITO:
        cur.execute("SELECT produto_id, quantidade_enviada FROM itens_transferencia WHERE transferencia_id = ?",
                      (trans_id,))
        for produto_id, qtd in cur.fetchall():
            cur.execute("UPDATE produtos SET estoque_atual = estoque_atual + ? WHERE id = ?",
                          (qtd, produto_id))

    cur.execute("UPDATE transferencias_filiais SET estado = ?, sincronizado = 0 WHERE id = ?",
                  (ESTADO_CANCELADA, trans_id))
    conn.commit()
    conn.close()

    registar_historico_ibt(trans_id, "CANCELOU", utilizador_nome,
                             estado, ESTADO_CANCELADA, f"Motivo: {motivo}")
    return True, "Cancelada."


def eliminar_transferencia(trans_id, utilizador_nome):
    """
    Elimina uma transferencia que esteja em RASCUNHO.
    Nao permite eliminar transferencias em outros estados.
    """
    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT estado, referencia FROM transferencias_filiais WHERE id = ?",
                  (trans_id,))
    r = cur.fetchone()

    if not r:
        conn.close()
        return False, "Transferencia nao encontrada."

    estado, referencia = r

    if estado != ESTADO_RASCUNHO:
        conn.close()
        return False, f"Apenas RASCUNHOS podem ser eliminados. Estado actual: {estado}"

    # Eliminar itens e historico (CASCADE ja faz, mas garantimos)
    cur.execute("DELETE FROM itens_transferencia WHERE transferencia_id = ?",
                  (trans_id,))
    cur.execute("DELETE FROM historico_ibt WHERE transferencia_id = ?",
                  (trans_id,))
    cur.execute("DELETE FROM transferencias_filiais WHERE id = ?",
                  (trans_id,))

    conn.commit()
    conn.close()

    registar_auditoria(
        0, utilizador_nome,
        "IBT ELIMINADA",
        f"ID {trans_id} | {referencia} | RASCUNHO eliminado"
    )
    return True, f"Transferencia {referencia} eliminada."


def pode_editar_transferencia(trans_id):
    """
    Verifica se uma transferencia pode ser editada.
    So RASCUNHOS podem ser editados.
    Retorna (pode_editar: bool, estado: str)
    """
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT estado FROM transferencias_filiais WHERE id = ?",
                  (trans_id,))
    r = cur.fetchone()
    conn.close()

    if not r:
        return False, None

    return r[0] == ESTADO_RASCUNHO, r[0]


def listar_transferencias(estado=None, limite=100, incluir_arquivadas=False):
    """
    Lista transferencias.
    
    Por defeito, NAO mostra as CONCLUIDAS nem CANCELADAS (arquivadas).
    Para ver as arquivadas, passa incluir_arquivadas=True.
    """
    conn = conectar()
    cur = conn.cursor()

    # Estados arquivados (nao aparecem por defeito)
    arquivados = (ESTADO_CONCLUIDA, ESTADO_CANCELADA)

    if estado:
        # Se pediu estado especifico, mostrar tudo desse estado
        cur.execute("""
            SELECT id, referencia, data_criacao, data_envio, data_recepcao,
                   farmacia_origem_nome, farmacia_destino_nome,
                   total_itens, total_quantidade, valor_estimado,
                   estado, utilizador_criou_nome, autorizado_por
            FROM transferencias_filiais WHERE estado = ?
            ORDER BY id DESC LIMIT ?
        """, (estado, limite))
    elif incluir_arquivadas:
        # Mostrar TODAS (incluindo arquivadas)
        cur.execute("""
            SELECT id, referencia, data_criacao, data_envio, data_recepcao,
                   farmacia_origem_nome, farmacia_destino_nome,
                   total_itens, total_quantidade, valor_estimado,
                   estado, utilizador_criou_nome, autorizado_por
            FROM transferencias_filiais ORDER BY id DESC LIMIT ?
        """, (limite,))
    else:
        # So as activas (nao arquivadas)
        cur.execute("""
            SELECT id, referencia, data_criacao, data_envio, data_recepcao,
                   farmacia_origem_nome, farmacia_destino_nome,
                   total_itens, total_quantidade, valor_estimado,
                   estado, utilizador_criou_nome, autorizado_por
            FROM transferencias_filiais
            WHERE estado NOT IN (?, ?)
            ORDER BY id DESC LIMIT ?
        """, (ESTADO_CONCLUIDA, ESTADO_CANCELADA, limite))

    resultado = cur.fetchall()
    conn.close()
    return resultado


def obter_transferencia(trans_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, referencia, data_criacao, data_envio, data_recepcao,
               farmacia_origem_id, farmacia_origem_codigo, farmacia_origem_nome,
               farmacia_destino_id, farmacia_destino_codigo, farmacia_destino_nome,
               utilizador_criou_id, utilizador_criou_nome, autorizado_por,
               estado, total_itens, total_quantidade, valor_estimado, observacoes
        FROM transferencias_filiais WHERE id = ?
    """, (trans_id,))
    r = cur.fetchone()
    conn.close()
    return r


def listar_itens_transferencia(trans_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, produto_id, produto_nome, codigo_barras,
               quantidade_enviada, quantidade_recebida, diferenca,
               lote, validade, preco_custo, subtotal, justificacao
        FROM itens_transferencia WHERE transferencia_id = ?
        ORDER BY id
    """, (trans_id,))
    r = cur.fetchall()
    conn.close()
    return r


def listar_historico_ibt(trans_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT data, acao, utilizador_nome,
               estado_anterior, estado_novo, detalhes
        FROM historico_ibt WHERE transferencia_id = ?
        ORDER BY id ASC
    """, (trans_id,))
    r = cur.fetchall()
    conn.close()
    return r


def estatisticas_ibt():
    conn = conectar()
    cur = conn.cursor()
    stats = {}
    for estado in [ESTADO_RASCUNHO, ESTADO_EM_TRANSITO,
                    ESTADO_RECEBIDA_PARCIAL, ESTADO_CONCLUIDA,
                    ESTADO_CANCELADA, ESTADO_DIVERGENCIA]:
        cur.execute("SELECT COUNT(*) FROM transferencias_filiais WHERE estado = ?",
                      (estado,))
        stats[estado] = cur.fetchone()[0]
    conn.close()
    return stats



# ============================================================
# ============ JANELA PRINCIPAL ==============================
# ============================================================

def abrir_transferencias(utilizador_logado, parent=None):
    if parent is None:
        parent = Toplevel()
        parent.withdraw()

    janela = Toplevel(parent)
    janela.title("Transferencias entre Filiais (IBT)")
    janela.geometry("1200x800")
    janela.configure(bg=COR_FUNDO)

    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 1200) // 2
    y = (janela.winfo_screenheight() - 800) // 2
    janela.geometry(f"1200x800+{x}+{y}")

    header = Frame(janela, bg=COR_PRIMARIA, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="🔄 Transferencias entre Filiais",
          font=("Segoe UI", 20, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=(15, 0))
    Label(header, text=f"Utilizador: {utilizador_logado['nome']}",
          font=("Segoe UI", 10, "italic"),
          bg=COR_PRIMARIA, fg="#e0e7ff").pack()

    content = Frame(janela, bg=COR_FUNDO)
    content.pack(fill=BOTH, expand=True)

    def recarregar():
        for w in content.winfo_children():
            w.destroy()
        _construir_menu(content, utilizador_logado, janela, recarregar)

    _construir_menu(content, utilizador_logado, janela, recarregar)


def _construir_menu(content, utilizador, janela, recarregar):
    farm_atual = obter_farmacia_actual()
    if farm_atual:
        Label(content, text=f"Farmacia actual: {farm_atual['nome']} ({farm_atual['codigo']})",
              font=("Segoe UI", 11, "italic"),
              bg=COR_FUNDO, fg=COR_DOURADO).pack(pady=15)
    else:
        Label(content, text="⚠️ Farmacia nao configurada",
              font=("Segoe UI", 11, "italic"),
              bg=COR_FUNDO, fg=COR_VERMELHO).pack(pady=15)

    stats = estatisticas_ibt()

    cards = Frame(content, bg=COR_FUNDO)
    cards.pack(fill=X, padx=30, pady=10)

    def criar_card(parent, titulo, subtitulo, cor, comando, coluna):
        card = Frame(parent, bg=cor, cursor="hand2", width=250, height=130)
        card.grid(row=0, column=coluna, padx=8, pady=8, sticky="nsew")
        card.pack_propagate(False)
        parent.columnconfigure(coluna, weight=1)

        lbl1 = Label(card, text=titulo, font=("Segoe UI", 14, "bold"),
                      bg=cor, fg="white", cursor="hand2",
                      wraplength=230, justify=CENTER)
        lbl1.pack(pady=(30, 5))

        lbl2 = Label(card, text=subtitulo, font=("Segoe UI", 10, "italic"),
                      bg=cor, fg="#e0e7ff", cursor="hand2",
                      wraplength=230, justify=CENTER)
        lbl2.pack()

        for w in [card, lbl1, lbl2]:
            w.bind("<Button-1>", lambda e: comando())

    criar_card(cards, "➕ Nova Transferencia", "Criar e enviar IBT",
                COR_VERDE,
                lambda: abrir_nova_ibt(utilizador, janela, recarregar), 0)
    criar_card(cards, "📋 Listar IBTs", f"{sum(stats.values())} registos",
                COR_AZUL,
                lambda: abrir_lista_ibt(utilizador, janela, recarregar), 1)
    criar_card(cards, "📊 Dashboard", "Rastreio do admin",
                COR_PRIMARIA,
                lambda: abrir_dashboard_ibt(utilizador, janela), 2)

    Label(content, text="Estado Actual",
          font=("Segoe UI", 13, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=30, pady=(20, 10))

    painel = Frame(content, bg=COR_FUNDO)
    painel.pack(fill=X, padx=30)

    for i, (estado, qtd) in enumerate(stats.items()):
        cor = CORES_ESTADO.get(estado, COR_TEXTO_SEC)
        box = Frame(painel, bg=COR_CARD, highlightthickness=2,
                     highlightbackground=cor, width=170, height=100)
        box.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
        box.pack_propagate(False)
        painel.columnconfigure(i, weight=1)

        Label(box, text=estado.replace("_", " "),
              font=("Segoe UI", 9, "bold"),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(15, 3))
        Label(box, text=str(qtd),
              font=("Segoe UI", 24, "bold"),
              bg=COR_CARD, fg=cor).pack()


# ============================================================
# ============ JANELA: NOVA IBT ==============================
# ============================================================

def abrir_nova_ibt(utilizador, parent, callback=None, trans_id_existente=None):
    # BLOQUEIO ANTI-FRAUDE: se for para continuar, verificar que ainda e RASCUNHO
    if trans_id_existente:
        pode_editar, estado_atual = pode_editar_transferencia(trans_id_existente)
        if not pode_editar:
            messagebox.showerror("BLOQUEADO",
                f"Esta IBT nao pode ser editada.\n\n"
                f"Estado actual: {estado_atual}\n\n"
                "Apenas RASCUNHOS podem ser editados.")
            return

    janela = Toplevel(parent)
    if trans_id_existente:
        janela.title("Continuar Transferencia (IBT)")
    else:
        janela.title("Nova Transferencia (IBT)")
    janela.geometry("1000x850")
    janela.configure(bg=COR_FUNDO)

    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 1000) // 2
    y = (janela.winfo_screenheight() - 850) // 2
    janela.geometry(f"1000x850+{x}+{y}")

    header = Frame(janela, bg=COR_VERDE, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="➕ Nova Transferencia (IBT)",
          font=("Segoe UI", 18, "bold"),
          bg=COR_VERDE, fg="white").pack(pady=20)

    carrinho = []

    if trans_id_existente:
        try:
            for it in listar_itens_transferencia(trans_id_existente):
                (iid, pid, nome, cod, qtd_env, qtd_rec, dif,
                 lote, val, custo, sub, just) = it
                carrinho.append({
                    "produto_id": pid, "nome": nome,
                    "codigo": cod or "", "qtd": qtd_env,
                    "custo": custo or 0, "subtotal": sub or 0,
                })
        except Exception as e:
            print(f"[IBT] Erro rascunho: {e}")

    Label(janela, text="Farmacias",
          font=("Segoe UI", 12, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=25, pady=(15, 5))

    card_farm = Frame(janela, bg=COR_CARD, highlightthickness=1,
                       highlightbackground=COR_BORDA)
    card_farm.pack(fill=X, padx=25, pady=5)
    inner = Frame(card_farm, bg=COR_CARD)
    inner.pack(padx=20, pady=15, fill=X)

    farm_atual = obter_farmacia_actual()
    if not farm_atual:
        messagebox.showerror("Erro", "Farmacia nao configurada.")
        janela.destroy()
        return

    farmacias = listar_farmacias_locais()

    Label(inner, text="Origem:", font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=0, sticky=W, padx=5, pady=5)
    Label(inner, text=f"{farm_atual['nome']} ({farm_atual['codigo']})",
          font=("Segoe UI", 10),
          bg=COR_CARD, fg=COR_VERDE).grid(row=0, column=1, sticky=W, padx=10, pady=5)

    Label(inner, text="Destino:", font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=1, column=0, sticky=W, padx=5, pady=5)

    destinos = [f for f in farmacias if f[2] != farm_atual["codigo"]]
    lista_dest = ["(Selecione)"] + [f"{f[2]} - {f[3]}" for f in destinos]
    destino_var = StringVar(value="(Selecione)")
    combo_dest = ttk.Combobox(inner, textvariable=destino_var,
                                values=lista_dest, state="readonly",
                                font=("Segoe UI", 10), width=50)
    combo_dest.grid(row=1, column=1, sticky=W, padx=10, pady=5)

    Label(inner, text="Observacoes:", font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=2, column=0, sticky=W, padx=5, pady=5)
    entry_obs = Entry(inner, font=("Segoe UI", 10), width=50, bd=1, relief=SOLID)
    entry_obs.grid(row=2, column=1, sticky=W, padx=10, pady=5, ipady=4)

    Label(janela, text="Adicionar Produtos",
          font=("Segoe UI", 12, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=25, pady=(15, 5))

    card_add = Frame(janela, bg=COR_CARD, highlightthickness=1,
                      highlightbackground=COR_BORDA)
    card_add.pack(fill=X, padx=25, pady=5)
    inner_add = Frame(card_add, bg=COR_CARD)
    inner_add.pack(padx=20, pady=15, fill=X)

    Label(inner_add, text="Codigo:", font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=0, sticky=W, padx=5, pady=5)
    entry_cod = Entry(inner_add, font=("Segoe UI", 11), width=20, bd=1, relief=SOLID)
    entry_cod.grid(row=0, column=1, padx=5, pady=5, ipady=4)
    entry_cod.focus()

    Label(inner_add, text="Qtd:", font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=2, sticky=W, padx=5, pady=5)
    entry_qtd = Entry(inner_add, font=("Segoe UI", 11), width=8,
                        justify=CENTER, bd=1, relief=SOLID)
    entry_qtd.grid(row=0, column=3, padx=5, pady=5, ipady=4)

    info_var = StringVar(value="Digite o codigo de barras")
    Label(inner_add, textvariable=info_var,
          font=("Segoe UI", 9, "italic"),
          bg=COR_CARD, fg=COR_TEXTO_SEC).grid(row=1, column=0, columnspan=4,
                                                sticky=W, padx=5, pady=5)

    Label(janela, text="Itens da Transferencia",
          font=("Segoe UI", 12, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=25, pady=(15, 5))

    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=25, pady=5)

    colunas = ("ID", "Produto", "Codigo", "Qtd", "Custo Unit.", "Subtotal")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=10)
    for c in colunas:
        tree.heading(c, text=c)
    tree.column("ID", width=60)
    tree.column("Produto", width=300)
    tree.column("Codigo", width=150)
    tree.column("Qtd", width=80)
    tree.column("Custo Unit.", width=130)
    tree.column("Subtotal", width=130)
    tree.pack(fill=BOTH, expand=True, side=LEFT)

    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)

    total_var = StringVar(value="0 itens | 0 unidades | Kz 0,00")
    Label(janela, textvariable=total_var,
          font=("Segoe UI", 12, "bold"),
          bg=COR_FUNDO, fg=COR_VERDE).pack(pady=10)

    def refresh_tree():
        for i in tree.get_children():
            tree.delete(i)
        for it in carrinho:
            tree.insert("", END, values=(it["produto_id"], it["nome"],
                                          it["codigo"], it["qtd"],
                                          formatar_kz(it["custo"]),
                                          formatar_kz(it["subtotal"])))
        if not carrinho:
            total_var.set("0 itens | 0 unidades | Kz 0,00")
        else:
            n = len(carrinho)
            qtd = sum(i["qtd"] for i in carrinho)
            val = sum(i["subtotal"] for i in carrinho)
            total_var.set(f"{n} itens | {qtd} unidades | {formatar_kz(val)}")

    if carrinho:
        refresh_tree()

    def adicionar(event=None):
        codigo = entry_cod.get().strip()
        if not codigo:
            return
        try:
            qtd = int(entry_qtd.get() or 0)
        except ValueError:
            qtd = 0
        if qtd <= 0:
            info_var.set("Digite uma quantidade valida.")
            return

        from database import obter_produto_por_codigo_com_id
        p = obter_produto_por_codigo_com_id(codigo)
        if not p:
            info_var.set(f"Produto '{codigo}' nao encontrado.")
            entry_cod.delete(0, END)
            return

        pid, nome, custo, venda, estoque = p
        if qtd > estoque:
            info_var.set(f"So ha {estoque} unidades em stock.")
            return

        for item in carrinho:
            if item["produto_id"] == pid:
                if item["qtd"] + qtd > estoque:
                    info_var.set(f"So ha {estoque} unidades em stock.")
                    return
                item["qtd"] += qtd
                item["subtotal"] = item["qtd"] * item["custo"]
                break
        else:
            carrinho.append({
                "produto_id": pid, "nome": nome, "codigo": codigo,
                "qtd": qtd, "custo": custo or 0,
                "subtotal": qtd * (custo or 0),
            })

        refresh_tree()
        entry_cod.delete(0, END)
        entry_qtd.delete(0, END)
        info_var.set("")
        entry_cod.focus()

    def remover():
        sel = tree.selection()
        if not sel:
            return
        idx = tree.index(sel[0])
        carrinho.pop(idx)
        refresh_tree()

    entry_cod.bind('<Return>', lambda e: entry_qtd.focus())
    entry_qtd.bind('<Return>', adicionar)

    def buscar_produto(event=None):
        codigo = entry_cod.get().strip()
        if not codigo:
            info_var.set("")
            return
        from database import obter_produto_por_codigo_com_id
        p = obter_produto_por_codigo_com_id(codigo)
        if p:
            info_var.set(f"{p[1]} | Stock: {p[4]} | Custo: {formatar_kz(p[2] or 0)}")

    entry_cod.bind('<KeyRelease>', buscar_produto)

    def parse_destino():
        destino_txt = destino_var.get()
        if destino_txt.startswith("(Selecione"):
            return None, None, None, "Selecione a farmacia de destino."
        try:
            partes = destino_txt.split(" - ", 1)
            codigo = partes[0].strip()
            nome = partes[1].strip() if len(partes) > 1 else codigo
            did = None
            for f in farmacias:
                if f[2] == codigo:
                    did = f[0]
                    break
            return did, codigo, nome, None
        except Exception:
            return None, None, None, "Nao foi possivel ler o destino."

    def confirmar():
        if not carrinho:
            messagebox.showwarning("Aviso", "Adicione pelo menos um produto.")
            return

        did, dcod, dnome, erro = parse_destino()
        if erro:
            messagebox.showwarning("Aviso", erro)
            return

        from caixa import _pedir_autorizacao_gerente
        ok, autoriz = _pedir_autorizacao_gerente(
            janela,
            f"Enviar IBT para {dnome}\nTotal: {len(carrinho)} itens",
            utilizador
        )
        if not ok:
            return

        try:
            tid = criar_transferencia(
                farm_atual["id"], farm_atual["codigo"], farm_atual["nome"],
                did, dcod, dnome,
                utilizador["id"], utilizador["nome"],
                entry_obs.get().strip()
            )
            for it in carrinho:
                adicionar_item_transferencia(tid, it["produto_id"], it["nome"],
                                              it["codigo"], it["qtd"], "", "",
                                              it["custo"])
            atualizar_totais_transferencia(tid)
            sucesso, msg = enviar_transferencia(tid, autoriz)
            if not sucesso:
                messagebox.showerror("Erro", msg)
                return

            registar_auditoria(utilizador["id"], utilizador["nome"],
                                "IBT ENVIADA",
                                f"ID {tid} -> {dnome} | {len(carrinho)} itens | Auth: {autoriz}")
            messagebox.showinfo("Sucesso",
                f"✅ IBT enviada!\n\nDestino: {dnome}\nItens: {len(carrinho)}\n"
                f"Autorizado por: {autoriz}")
            janela.destroy()
            if callback:
                callback()
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"Erro: {e}")

    def gravar_rascunho():
        # BLOQUEIO: se estiver a editar rascunho, verificar estado
        if trans_id_existente:
            pode_editar, estado_atual = pode_editar_transferencia(trans_id_existente)
            if not pode_editar:
                messagebox.showerror("BLOQUEADO",
                    f"Esta IBT ja foi enviada ou concluida.\n\n"
                    f"Estado actual: {estado_atual}\n\n"
                    "Nao pode mais alterar.")
                return

        if not carrinho:
            messagebox.showwarning("Aviso", "Adicione pelo menos um produto.")
            return

        did, dcod, dnome, erro = parse_destino()
        if erro:
            messagebox.showwarning("Aviso", erro)
            return

        try:
            if trans_id_existente:
                conn = conectar()
                cur = conn.cursor()
                cur.execute("DELETE FROM itens_transferencia WHERE transferencia_id = ?",
                              (trans_id_existente,))
                cur.execute("""
                    UPDATE transferencias_filiais
                    SET farmacia_destino_id = ?, farmacia_destino_codigo = ?,
                        farmacia_destino_nome = ?, observacoes = ?, sincronizado = 0
                    WHERE id = ?
                """, (did, dcod, dnome, entry_obs.get().strip(), trans_id_existente))
                conn.commit()
                conn.close()
                tid = trans_id_existente
                registar_historico_ibt(tid, "ACTUALIZOU RASCUNHO", utilizador["nome"],
                                         ESTADO_RASCUNHO, ESTADO_RASCUNHO,
                                         "Rascunho actualizado")
            else:
                tid = criar_transferencia(
                    farm_atual["id"], farm_atual["codigo"], farm_atual["nome"],
                    did, dcod, dnome,
                    utilizador["id"], utilizador["nome"],
                    entry_obs.get().strip()
                )

            for it in carrinho:
                adicionar_item_transferencia(tid, it["produto_id"], it["nome"],
                                              it["codigo"], it["qtd"], "", "",
                                              it["custo"])
            atualizar_totais_transferencia(tid)
            registar_auditoria(utilizador["id"], utilizador["nome"],
                                "IBT RASCUNHO", f"ID {tid} | {len(carrinho)} itens")

            messagebox.showinfo("💾 Gravado",
                f"Rascunho guardado!\n\nRef: ID {tid}\nDestino: {dnome}\n"
                f"Itens: {len(carrinho)}\n\nPode continuar em:\n"
                f"Transferencias → Listar IBTs → Continuar")
            janela.destroy()
            if callback:
                callback()
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"Erro: {e}")

    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=15)

    Button(frame_btn, text="❌ Remover",
           font=("Segoe UI", 11, "bold"),
           bg=COR_VERMELHO, fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=remover).pack(side=LEFT, padx=5)
    Button(frame_btn, text="💾 Gravar (RASCUNHO)",
           font=("Segoe UI", 11, "bold"),
           bg=COR_DOURADO, fg="#0f172a",
           width=20, height=2, bd=0, cursor="hand2",
           command=gravar_rascunho).pack(side=LEFT, padx=5)
    Button(frame_btn, text="✅ Enviar com Autorizacao",
           font=("Segoe UI", 12, "bold"),
           bg=COR_VERDE, fg="white",
           width=25, height=2, bd=0, cursor="hand2",
           command=confirmar).pack(side=LEFT, padx=5)
    Button(frame_btn, text="❌ Cancelar",
           font=("Segoe UI", 11),
           bg="#64748b", fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=5)

    

# ============================================================
# ============ JANELA: LISTA DE IBTs =========================
# ============================================================

def abrir_lista_ibt(utilizador, parent, callback=None):
    janela = Toplevel(parent)
    janela.title("Lista de Transferencias")
    janela.geometry("1300x800")
    janela.configure(bg=COR_FUNDO)

    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 1300) // 2
    y = (janela.winfo_screenheight() - 800) // 2
    janela.geometry(f"1300x800+{x}+{y}")

    header = Frame(janela, bg=COR_AZUL, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="📋 Transferencias entre Filiais",
          font=("Segoe UI", 18, "bold"),
          bg=COR_AZUL, fg="white").pack(pady=20)

    # ============================================================
    # BARRA DE BOTOES FIXA EM BAIXO (primeiro!)
    # ============================================================
    frame_btn = Frame(janela, bg=COR_CARD, height=80)
    frame_btn.pack(fill=X, side=BOTTOM)
    frame_btn.pack_propagate(False)

    # Filtro
    frame_filtro = Frame(janela, bg=COR_CARD, highlightthickness=1,
                           highlightbackground=COR_BORDA)
    frame_filtro.pack(fill=X, padx=20, pady=15)

    inner = Frame(frame_filtro, bg=COR_CARD)
    inner.pack(padx=20, pady=12, fill=X)

    Label(inner, text="Estado:",
          font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=(0, 8))

    estados = ["TODOS (activas)", "TODOS (com arquivadas)",
               ESTADO_RASCUNHO, ESTADO_EM_TRANSITO,
               ESTADO_RECEBIDA_PARCIAL, ESTADO_CONCLUIDA,
               ESTADO_CANCELADA, ESTADO_DIVERGENCIA]
    filtro_var = StringVar(value="TODOS")
    ttk.Combobox(inner, textvariable=filtro_var, values=estados,
                  state="readonly", font=("Segoe UI", 10), width=22).pack(side=LEFT)

    # Tabela
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=20, pady=10)

    colunas = ("ID", "Referencia", "Criada", "Origem", "Destino",
               "Itens", "Qtd", "Valor", "Estado", "Criada por")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=12)
    for c in colunas:
        tree.heading(c, text=c)
    tree.column("ID", width=50)
    tree.column("Referencia", width=140)
    tree.column("Criada", width=130)
    tree.column("Origem", width=180)
    tree.column("Destino", width=180)
    tree.column("Itens", width=60)
    tree.column("Qtd", width=60)
    tree.column("Valor", width=120)
    tree.column("Estado", width=140)
    tree.column("Criada por", width=140)
    tree.pack(fill=BOTH, expand=True, side=LEFT)

    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)

    def carregar():
        for i in tree.get_children():
            tree.delete(i)

        estado = filtro_var.get()

        if estado.startswith("TODOS (activas"):
            estado_f = None
            incluir_arquivadas = False
        elif estado.startswith("TODOS (com arquiv"):
            estado_f = None
            incluir_arquivadas = True
        else:
            estado_f = estado
            incluir_arquivadas = True

        for t in listar_transferencias(estado_f, 200, incluir_arquivadas):
            (tid, ref, dt_c, dt_e, dt_r, orig, dest, n_itens, qtd,
             valor, est, user, aut) = t
            tree.insert("", END, values=(
                tid, ref, dt_c or "-", orig or "-", dest or "-",
                n_itens or 0, qtd or 0, formatar_kz(valor or 0),
                est, user or "-"
            ), tags=(est,))

        for est, cor in CORES_ESTADO.items():
            tree.tag_configure(est, foreground=cor)

    filtro_var.trace("w", lambda *a: carregar())
    carregar()

    def ver_detalhes():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma transferencia.")
            return
        tid = tree.item(sel[0])["values"][0]
        abrir_detalhes_ibt(tid, utilizador, janela, carregar)

    def receber():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma transferencia.")
            return
        tid = tree.item(sel[0])["values"][0]
        estado = tree.item(sel[0])["values"][8]
        if estado != ESTADO_EM_TRANSITO:
            messagebox.showinfo("Info", "Esta IBT nao esta em transito.")
            return
        abrir_receber_ibt(tid, utilizador, janela, carregar)

    def continuar_rascunho():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma transferencia.")
            return
        tid = tree.item(sel[0])["values"][0]
        estado = tree.item(sel[0])["values"][8]
        if estado != ESTADO_RASCUNHO:
            messagebox.showinfo("Info",
                "Apenas RASCUNHOS podem ser continuados.\n\n"
                f"Estado actual: {estado}")
            return
        abrir_nova_ibt(utilizador, janela, callback=carregar,
                        trans_id_existente=tid)

    def eliminar_rascunho():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma transferencia.")
            return
        tid = tree.item(sel[0])["values"][0]
        ref = tree.item(sel[0])["values"][1]
        estado = tree.item(sel[0])["values"][8]

        if estado != ESTADO_RASCUNHO:
            messagebox.showinfo("Info",
                "Apenas RASCUNHOS podem ser eliminados.\n\n"
                f"Estado actual: {estado}\n\n"
                "Para cancelar uma IBT ja enviada, use 'Cancelar'.")
            return

        if not messagebox.askyesno("Eliminar Rascunho",
            f"Eliminar DEFINITIVAMENTE o rascunho {ref}?\n\n"
            "Esta accao nao pode ser revertida."):
            return

        sucesso, msg = eliminar_transferencia(tid, utilizador["nome"])
        if sucesso:
            messagebox.showinfo("Sucesso", f"✅ {msg}")
            carregar()
        else:
            messagebox.showerror("Erro", msg)

    # Duplo-clique na linha
    def duplo_clique(event=None):
        sel = tree.selection()
        if not sel:
            return
        tid = tree.item(sel[0])["values"][0]
        estado = tree.item(sel[0])["values"][8]

        if estado == ESTADO_RASCUNHO:
            abrir_nova_ibt(utilizador, janela, callback=carregar,
                            trans_id_existente=tid)
        elif estado == ESTADO_EM_TRANSITO:
            abrir_receber_ibt(tid, utilizador, janela, carregar)
        else:
            abrir_detalhes_ibt(tid, utilizador, janela, carregar)

    tree.bind("<Double-Button-1>", duplo_clique)

    # Botoes
    estilo = {"font": ("Segoe UI", 10, "bold"),
              "bd": 0, "cursor": "hand2", "fg": "white",
              "width": 15, "height": 2}

    Button(frame_btn, text="▶️ Continuar",
           bg=COR_DOURADO, fg="#0f172a",
           command=continuar_rascunho, **estilo).pack(side=LEFT, padx=6, pady=15)
    Button(frame_btn, text="🔍 Ver Detalhes",
           bg=COR_AZUL, command=ver_detalhes, **estilo).pack(side=LEFT, padx=6, pady=15)
    Button(frame_btn, text="📥 Receber",
           bg=COR_VERDE, command=receber, **estilo).pack(side=LEFT, padx=6, pady=15)
    Button(frame_btn, text="🔄 Actualizar",
           bg="#64748b", command=carregar, **estilo).pack(side=LEFT, padx=6, pady=15)
    Button(frame_btn, text="🗑️ Eliminar",
           bg="#7f1d1d", command=eliminar_rascunho, **estilo).pack(side=LEFT, padx=6, pady=15)
    Button(frame_btn, text="❌ Fechar",
           bg=COR_VERMELHO,
           command=janela.destroy, **estilo).pack(side=RIGHT, padx=6, pady=15)


# ============================================================
# ============ JANELA: DETALHES IBT ==========================
# ============================================================

def abrir_detalhes_ibt(trans_id, utilizador, parent, callback=None):
    trans = obter_transferencia(trans_id)
    if not trans:
        messagebox.showerror("Erro", "IBT nao encontrada.")
        return

    (tid, ref, dt_c, dt_e, dt_r, o_id, o_cod, o_nome,
     d_id, d_cod, d_nome, uc_id, uc_nome, aut, estado,
     n_itens, qtd, valor, obs) = trans

    itens = listar_itens_transferencia(trans_id)
    historico = listar_historico_ibt(trans_id)

    janela = Toplevel(parent)
    janela.title(f"Detalhes - {ref}")
    janela.geometry("1000x850")
    janela.configure(bg=COR_FUNDO)

    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 1000) // 2
    y = (janela.winfo_screenheight() - 850) // 2
    janela.geometry(f"1000x850+{x}+{y}")

    header = Frame(janela, bg=COR_PRIMARIA, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text=f"📄 {ref}",
          font=("Segoe UI", 18, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=20)

    card = Frame(janela, bg=COR_CARD, highlightthickness=1,
                   highlightbackground=COR_BORDA)
    card.pack(fill=X, padx=20, pady=15)

    def linha(label, valor, cor=COR_TEXTO):
        f = Frame(card, bg=COR_CARD)
        f.pack(fill=X, padx=20, pady=3)
        Label(f, text=label, font=("Segoe UI", 10, "bold"),
              bg=COR_CARD, fg=COR_TEXTO_SEC, width=20, anchor=W).pack(side=LEFT)
        Label(f, text=str(valor or "-"), font=("Segoe UI", 10),
              bg=COR_CARD, fg=cor, anchor=W).pack(side=LEFT)

    cor_est = CORES_ESTADO.get(estado, COR_TEXTO)
    linha("Estado:", estado, cor_est)
    linha("Origem:", f"{o_nome} ({o_cod})")
    linha("Destino:", f"{d_nome} ({d_cod})")
    linha("Criada em:", dt_c)
    linha("Enviada em:", dt_e)
    linha("Recebida em:", dt_r)
    linha("Criada por:", uc_nome)
    linha("Autorizada por:", aut)
    linha("Total itens:", n_itens)
    linha("Total unidades:", qtd)
    linha("Valor estimado:", formatar_kz(valor or 0), COR_VERDE)
    if obs:
        linha("Observacoes:", obs)

    Label(janela, text="Itens",
          font=("Segoe UI", 12, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=25, pady=(10, 5))

    frame_it = Frame(janela, bg=COR_FUNDO)
    frame_it.pack(fill=X, padx=20)

    cols = ("Produto", "Codigo", "Enviado", "Recebido", "Dif.", "Justificacao")
    tree_it = ttk.Treeview(frame_it, columns=cols, show="headings", height=6)
    for c in cols:
        tree_it.heading(c, text=c)
    tree_it.column("Produto", width=280)
    tree_it.column("Codigo", width=140)
    tree_it.column("Enviado", width=90)
    tree_it.column("Recebido", width=90)
    tree_it.column("Dif.", width=90)
    tree_it.column("Justificacao", width=200)
    tree_it.pack(fill=X)

    for it in itens:
        (iid, pid, nome, cod, qtd_env, qtd_rec, dif, lote, val, custo, sub, just) = it
        tag = "div" if dif and dif != 0 else ""
        tree_it.insert("", END, values=(nome, cod or "-", qtd_env, qtd_rec,
                                          dif, just or "-"), tags=(tag,))
    tree_it.tag_configure("div", foreground=COR_VERMELHO)

    Label(janela, text="Historico",
          font=("Segoe UI", 12, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=25, pady=(15, 5))

    frame_hist = Frame(janela, bg=COR_FUNDO)
    frame_hist.pack(fill=BOTH, expand=True, padx=20, pady=(0, 10))

    cols_h = ("Data", "Acao", "Utilizador", "Estado Antes", "Estado Depois", "Detalhes")
    tree_h = ttk.Treeview(frame_hist, columns=cols_h, show="headings", height=6)
    for c in cols_h:
        tree_h.heading(c, text=c)
    tree_h.column("Data", width=140)
    tree_h.column("Acao", width=100)
    tree_h.column("Utilizador", width=130)
    tree_h.column("Estado Antes", width=120)
    tree_h.column("Estado Depois", width=120)
    tree_h.column("Detalhes", width=250)
    tree_h.pack(fill=BOTH, expand=True)

    for h in historico:
        tree_h.insert("", END, values=h)

    def gerar_pdf():
        try:
            from relatorio_ibt import abrir_escolha_impressao_ibt
            abrir_escolha_impressao_ibt(trans_id, parent=janela)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar PDF: {e}")

    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=10)

    Button(frame_btn, text="🖨️ Gerar PDF",
           font=("Segoe UI", 11, "bold"),
           bg=COR_AZUL, fg="white",
           width=18, height=2, bd=0, cursor="hand2",
           command=gerar_pdf).pack(side=LEFT, padx=5)
    Button(frame_btn, text="❌ Fechar",
           font=("Segoe UI", 11),
           bg="#64748b", fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=5)


# ============================================================
# ============ JANELA: RECEBER IBT ===========================
# ============================================================

def abrir_receber_ibt(trans_id, utilizador, parent, callback=None):
    trans = obter_transferencia(trans_id)
    if not trans:
        messagebox.showerror("Erro", "IBT nao encontrada.")
        return

    ref = trans[1]
    o_nome = trans[7]
    d_nome = trans[10]
    itens = listar_itens_transferencia(trans_id)

    janela = Toplevel(parent)
    janela.title(f"Receber {ref}")
    janela.geometry("900x700")
    janela.configure(bg=COR_FUNDO)

    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 900) // 2
    y = (janela.winfo_screenheight() - 700) // 2
    janela.geometry(f"900x700+{x}+{y}")

    header = Frame(janela, bg=COR_VERDE, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text=f"📥 Receber {ref}",
          font=("Segoe UI", 18, "bold"),
          bg=COR_VERDE, fg="white").pack(pady=20)

    Label(janela, text=f"Origem: {o_nome}  →  Destino: {d_nome}",
          font=("Segoe UI", 11, "italic"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(pady=10)

    Label(janela, text="Confirme o que realmente chegou:",
          font=("Segoe UI", 11),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=5)

    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=20, pady=10)

    cols = ("ID", "Produto", "Enviado", "RECEBIDO")
    tree = ttk.Treeview(frame_tab, columns=cols, show="headings", height=12)
    for c in cols:
        tree.heading(c, text=c)
    tree.column("ID", width=60)
    tree.column("Produto", width=380)
    tree.column("Enviado", width=100)
    tree.column("RECEBIDO", width=100)
    tree.pack(fill=BOTH, expand=True, side=LEFT)

    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)

    itens_map = {}
    for it in itens:
        iid, pid, nome, cod, qtd_env, qtd_rec, dif, lote, val, custo, sub, just = it
        tree.insert("", END, values=(iid, nome, qtd_env, qtd_env))
        itens_map[iid] = {"enviado": qtd_env, "recebido": qtd_env}

    def editar(event=None):
        sel = tree.selection()
        if not sel:
            return
        iid = tree.item(sel[0])["values"][0]
        enviado = itens_map[iid]["enviado"]

        from tkinter import simpledialog
        nova = simpledialog.askinteger(
            "Quantidade Recebida",
            f"Quanto chegou?\n\nEnviado: {enviado}",
            initialvalue=itens_map[iid]["recebido"],
            minvalue=0, maxvalue=enviado,
            parent=janela
        )
        if nova is not None:
            itens_map[iid]["recebido"] = nova
            tree.item(sel[0], values=(iid, tree.item(sel[0])["values"][1],
                                        enviado, nova))

    tree.bind("<Double-Button-1>", editar)

    Label(janela, text="(Duplo-clique num item para alterar a quantidade)",
          font=("Segoe UI", 9, "italic"),
          bg=COR_FUNDO, fg=COR_TEXTO_SEC).pack()

    def confirmar():
        ok, msg = receber_transferencia(
            trans_id, utilizador["nome"],
            {iid: d["recebido"] for iid, d in itens_map.items()}
        )
        if ok:
            registar_auditoria(utilizador["id"], utilizador["nome"],
                                "IBT RECEBIDA", f"{ref} | {msg}")
            messagebox.showinfo("Sucesso", f"✅ {msg}")
            janela.destroy()
            if callback:
                callback()
        else:
            messagebox.showerror("Erro", msg)

    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=15)

    Button(frame_btn, text="✅ Confirmar Recepcao",
           font=("Segoe UI", 12, "bold"),
           bg=COR_VERDE, fg="white",
           width=25, height=2, bd=0, cursor="hand2",
           command=confirmar).pack(side=LEFT, padx=5)
    Button(frame_btn, text="❌ Cancelar",
           font=("Segoe UI", 11),
           bg="#64748b", fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=5)


# ============================================================
# ============ JANELA: DASHBOARD IBT =========================
# ============================================================

def abrir_dashboard_ibt(utilizador, parent):
    janela = Toplevel(parent)
    janela.title("Dashboard IBT")
    janela.geometry("1100x750")
    janela.configure(bg=COR_FUNDO)

    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 1100) // 2
    y = (janela.winfo_screenheight() - 750) // 2
    janela.geometry(f"1100x750+{x}+{y}")

    header = Frame(janela, bg=COR_PRIMARIA, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="📊 Dashboard de Transferencias",
          font=("Segoe UI", 18, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=20)

    stats = estatisticas_ibt()

    cards = Frame(janela, bg=COR_FUNDO)
    cards.pack(fill=X, padx=20, pady=20)

    for i, (est, qtd) in enumerate(stats.items()):
        cor = CORES_ESTADO.get(est, COR_TEXTO_SEC)
        card = Frame(cards, bg=COR_CARD, highlightthickness=2,
                       highlightbackground=cor, width=160, height=110)
        card.grid(row=0, column=i, padx=6, pady=6, sticky="nsew")
        card.pack_propagate(False)
        cards.columnconfigure(i, weight=1)

        Label(card, text=est.replace("_", " "),
              font=("Segoe UI", 9, "bold"),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(15, 3))
        Label(card, text=str(qtd),
              font=("Segoe UI", 22, "bold"),
              bg=COR_CARD, fg=cor).pack()

    Label(janela, text="IBTs Pendentes (em transito):",
          font=("Segoe UI", 12, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=30, pady=(20, 5))

    frame_pend = Frame(janela, bg=COR_FUNDO)
    frame_pend.pack(fill=X, padx=20)

    cols = ("Referencia", "Criada", "Origem", "Destino", "Itens", "Estado")
    tree = ttk.Treeview(frame_pend, columns=cols, show="headings", height=8)
    for c in cols:
        tree.heading(c, text=c)
    tree.column("Referencia", width=140)
    tree.column("Criada", width=130)
    tree.column("Origem", width=250)
    tree.column("Destino", width=250)
    tree.column("Itens", width=80)
    tree.column("Estado", width=140)
    tree.pack(fill=X)

    pendentes = listar_transferencias(ESTADO_EM_TRANSITO, 50)
    for t in pendentes:
        tree.insert("", END, values=(t[1], t[2], t[5], t[6], t[7], t[10]),
                      tags=("transito",))
    tree.tag_configure("transito", foreground=COR_DOURADO)

    if not pendentes:
        Label(frame_pend, text="(Nenhuma IBT em transito)",
              font=("Segoe UI", 10, "italic"),
              bg=COR_FUNDO, fg=COR_TEXTO_SEC).pack(pady=10)

    Button(janela, text="❌ Fechar",
           font=("Segoe UI", 11),
           bg="#64748b", fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(pady=20)


# ============================================================
# ============ TESTE DIRETO ==================================
# ============================================================

if __name__ == "__main__":
    from tkinter import Tk
    root = Tk()
    root.withdraw()
    utilizador = {"id": 1, "nome": "Teste", "perfil": "admin"}
    abrir_transferencias(utilizador, root)
    root.mainloop()