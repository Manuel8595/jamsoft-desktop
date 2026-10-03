from tkinter import *
from tkinter import messagebox, ttk, simpledialog
from database import (criar_nao_conformidade, listar_nao_conformidades,
                       buscar_nao_conformidade, atualizar_estado_nc,
                       contagem_nc_por_estado, aud_vendas_com_desconto,
                       aud_sangrias, aud_anulacoes, aud_perdas_recentes,
                       aud_lotes_vencidos, aud_alteracoes_produtos,
                       registar_auditoria_realizada, listar_auditorias_realizadas,
                       registar_auditoria)
from moeda import formatar_kz
from seguranca import verificar_acesso
from datetime import datetime

COR_FUNDO = "#f1f5f9"
COR_PRIMARIA = "#334155"
COR_TEXTO = "#0f172a"
COR_PERIGO = "#dc2626"
COR_HEADER = "#1e293b"
COR_CARD = "#ffffff"
COR_VERDE = "#16a34a"
COR_AZUL = "#0891b2"
COR_ROXO = "#7c3aed"
COR_LARANJA = "#ea580c"
COR_AMARELO = "#f59e0b"


def abrir_painel_auditoria(utilizador_logado):
    """Abre o Painel de Auditoria - modulo exclusivo do auditor."""
    
    if not verificar_acesso(utilizador_logado, "auditoria.ver_log", "Painel de Auditoria"):
        return
    
    janela = Toplevel()
    janela.title("JAM Soft - Painel de Auditoria")
    janela.geometry("1200x800")
    janela.configure(bg=COR_FUNDO)
    janela.state("zoomed")
    
    # ===== HEADER =====
    header = Frame(janela, bg=COR_HEADER, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    
    Label(header, text="🔐 Painel de Auditoria e Conformidade",
          font=("Arial", 20, "bold"), bg=COR_HEADER, fg="white").pack(pady=(15, 0))
    
    Label(header, text=f"Auditor: {utilizador_logado['nome']}  |  "
                        f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  "
                        f"Modo: Leitura Controlada",
          font=("Arial", 10, "italic"), bg=COR_HEADER, fg="#cbd5e1").pack()
    
    # ===== CARDS DE RESUMO =====
    cards_frame = Frame(janela, bg=COR_FUNDO)
    cards_frame.pack(fill=X, padx=20, pady=15)
    
    contagens = contagem_nc_por_estado()
    nc_abertas = contagens.get("ABERTA", 0)
    nc_analise = contagens.get("EM_ANALISE", 0)
    nc_resolvidas = contagens.get("RESOLVIDA", 0)
    nc_encerradas = contagens.get("ENCERRADA", 0)
    nc_total = nc_abertas + nc_analise + nc_resolvidas + nc_encerradas
    
    def criar_card(parent, titulo, valor, cor, subtitulo="", coluna=0):
        card = Frame(parent, bg=COR_CARD, highlightthickness=2, highlightbackground=cor)
        card.grid(row=0, column=coluna, padx=8, pady=5, sticky="nsew")
        parent.columnconfigure(coluna, weight=1)
        
        Label(card, text=titulo, font=("Arial", 10, "bold"),
              bg=COR_CARD, fg="#64748b").pack(pady=(15, 3))
        Label(card, text=str(valor), font=("Arial", 24, "bold"),
              bg=COR_CARD, fg=cor).pack()
        if subtitulo:
            Label(card, text=subtitulo, font=("Arial", 9, "italic"),
                  bg=COR_CARD, fg="#94a3b8").pack(pady=(3, 15))
        else:
            Label(card, text="", bg=COR_CARD).pack(pady=(0, 15))
    
    criar_card(cards_frame, "Total Não Conformidades", nc_total, COR_PRIMARIA, "registadas", 0)
    criar_card(cards_frame, "Abertas", nc_abertas, COR_PERIGO, "por resolver", 1)
    criar_card(cards_frame, "Em Análise", nc_analise, COR_LARANJA, "em tratamento", 2)
    criar_card(cards_frame, "Resolvidas", nc_resolvidas, COR_AZUL, "aguardam encerramento", 3)
    criar_card(cards_frame, "Encerradas", nc_encerradas, COR_VERDE, "concluídas", 4)
    
    # ===== ÁREAS DE AUDITORIA =====
    Label(janela, text="Áreas de Auditoria", font=("Arial", 14, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, padx=25, pady=(15, 5))
    
    areas_frame = Frame(janela, bg=COR_FUNDO)
    areas_frame.pack(fill=X, padx=20, pady=5)
    
    estilo_area = {"font": ("Arial", 11, "bold"), "width": 22, "height": 2,
                   "bd": 0, "cursor": "hand2", "fg": "white"}
    
    def criar_area(parent, texto, cor, cmd, col):
        b = Button(parent, text=texto, bg=cor, command=cmd, **estilo_area)
        b.grid(row=0, column=col, padx=6, pady=6, sticky="ew")
        parent.columnconfigure(col, weight=1)
        return b
    
    criar_area(areas_frame, "💰 Auditoria de Vendas",
               COR_VERDE, lambda: ver_vendas_desconto(utilizador_logado), 0)
    
    criar_area(areas_frame, "📦 Auditoria de Stock",
               COR_AZUL, lambda: ver_stock_perdas(utilizador_logado), 1)
    
    criar_area(areas_frame, "💵 Auditoria de Caixa",
               COR_ROXO, lambda: ver_caixa_movimentos(utilizador_logado), 2)
    
    criar_area(areas_frame, "💊 Auditoria Farmacêutica",
               COR_LARANJA, lambda: ver_farmaceutica(utilizador_logado), 3)
    
    # ===== SEGUNDA LINHA DE BOTÕES =====
    areas_frame2 = Frame(janela, bg=COR_FUNDO)
    areas_frame2.pack(fill=X, padx=20, pady=5)
    
    criar_area(areas_frame2, "📋 Não Conformidades",
               COR_PERIGO, lambda: ver_nao_conformidades(utilizador_logado, janela), 0)
    
    criar_area(areas_frame2, "📝 Alterações de Produtos",
               "#64748b", lambda: ver_alteracoes(utilizador_logado), 1)
    
    criar_area(areas_frame2, "❌ Anulações",
               "#991b1b", lambda: ver_anulacoes(utilizador_logado), 2)
    
    criar_area(areas_frame2, "📊 Histórico de Auditorias",
               COR_AMARELO, lambda: ver_historico_auditorias(utilizador_logado), 3)
    
    # ===== INFO RODAPÉ =====
    rodape = Frame(janela, bg=COR_CARD, height=50)
    rodape.pack(fill=X, side=BOTTOM)
    rodape.pack_propagate(False)
    
    Label(rodape, text="🔒 Perfil Auditor - Apenas Leitura | "
                        "Todas as ações são registadas para rastreabilidade",
          font=("Arial", 9, "italic"), bg=COR_CARD, fg="#64748b").pack(pady=15)

    # ============================================================
# ============ FUNCOES AUXILIARES ============================
# ============================================================

def criar_janela_tabela(titulo, colunas, widths=None, cor_header=None):
    """Cria janela padrao de tabela para auditoria."""
    if cor_header is None:
        cor_header = COR_HEADER
    
    janela = Toplevel()
    janela.title(f"JAM Soft - {titulo}")
    janela.geometry("1100x650")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=cor_header, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text=titulo, font=("Arial", 16, "bold"),
          bg=cor_header, fg="white").pack(pady=20)
    
    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(fill=BOTH, expand=True, padx=15, pady=15)
    
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=18)
    for i, col in enumerate(colunas):
        tree.heading(col, text=col)
        w = widths[i] if widths else 150
        tree.column(col, width=w)
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    return janela, tree


# ============================================================
# ============ AREA: VENDAS ==================================
# ============================================================

def ver_vendas_desconto(utilizador_logado):
    """Auditoria de vendas com desconto (ultimos 30 dias)."""
    janela, tree = criar_janela_tabela(
        "Auditoria de Vendas - Descontos (últimos 30 dias)",
        ("ID", "Data", "Total", "Desconto", "Subtotal Original", "Forma Pag.", "Operador", "Autorizado"),
        [60, 150, 110, 110, 130, 120, 150, 130],
        cor_header=COR_VERDE
    )
    
    dados = aud_vendas_com_desconto(100)
    
    total_descontos = 0
    
    for v in dados:
        vid, data, total, desconto, sub_o, forma, operador, autorizado = v
        desconto = desconto or 0
        total_descontos += desconto
        
        tag = ""
        if desconto > 5000:
            tag = "alto"
        
        tree.insert("", END, values=(
            vid, data, formatar_kz(total), formatar_kz(desconto),
            formatar_kz(sub_o or 0), forma or "-", operador or "-",
            autorizado or "-"
        ), tags=(tag,))
    
    tree.tag_configure("alto", background="#fee2e2", foreground="#991b1b")
    
    Label(janela, text=f"Total de vendas com desconto: {len(dados)}  |  "
                        f"Valor total descontado: {formatar_kz(total_descontos)}",
          font=("Arial", 11, "bold"), bg=COR_FUNDO, fg=COR_PERIGO).pack(pady=10)
    
    # Registar auditoria realizada
    registar_auditoria_realizada(
        "CONSULTA", "VENDAS",
        "Auditoria de vendas com desconto",
        f"{len(dados)} registos analisados | {formatar_kz(total_descontos)} em descontos",
        utilizador_logado["id"], utilizador_logado["nome"]
    )


def ver_anulacoes(utilizador_logado):
    """Auditoria de facturas anuladas."""
    janela, tree = criar_janela_tabela(
        "Auditoria - Facturas Anuladas",
        ("Número", "Data", "Cliente", "Total", "Motivo", "Utilizador"),
        [130, 150, 220, 120, 250, 150],
        cor_header="#991b1b"
    )
    
    dados = aud_anulacoes(100)
    
    for a in dados:
        tree.insert("", END, values=(
            a[0], a[1], a[2] or "Consumidor Final",
            formatar_kz(a[3] or 0), a[4] or "-", a[5] or "-"
        ))
    
    Label(janela, text=f"Total: {len(dados)} facturas anuladas",
          font=("Arial", 11, "bold"), bg=COR_FUNDO, fg=COR_PERIGO).pack(pady=10)
    
    registar_auditoria_realizada(
        "CONSULTA", "VENDAS",
        "Auditoria de facturas anuladas",
        f"{len(dados)} facturas analisadas",
        utilizador_logado["id"], utilizador_logado["nome"]
    )


# ============================================================
# ============ AREA: STOCK ===================================
# ============================================================

def ver_stock_perdas(utilizador_logado):
    """Auditoria de perdas (ultimos 30 dias)."""
    janela, tree = criar_janela_tabela(
        "Auditoria de Stock - Perdas (últimos 30 dias)",
        ("Data", "Tipo", "Produto", "Qtd", "Valor Perdido", "Motivo", "Utilizador"),
        [150, 100, 220, 60, 130, 220, 150],
        cor_header=COR_AZUL
    )
    
    dados = aud_perdas_recentes(100)
    
    total_valor = 0
    for p in dados:
        data, tipo, nome, qtd, valor, motivo, user = p
        valor = valor or 0
        total_valor += valor
        
        tag = ""
        if tipo == "FURTO":
            tag = "furto"
        elif tipo == "QUEBRA":
            tag = "quebra"
        elif tipo == "VENCIMENTO":
            tag = "vencimento"
        
        tree.insert("", END, values=(
            data, tipo, nome or "-", qtd, formatar_kz(valor),
            motivo or "-", user or "-"
        ), tags=(tag,))
    
    tree.tag_configure("furto", foreground="#991b1b")
    tree.tag_configure("quebra", foreground=COR_LARANJA)
    tree.tag_configure("vencimento", foreground=COR_PERIGO)
    
    Label(janela, text=f"Total: {len(dados)} registos  |  "
                        f"Valor total perdido: {formatar_kz(total_valor)}",
          font=("Arial", 11, "bold"), bg=COR_FUNDO, fg=COR_PERIGO).pack(pady=10)
    
    registar_auditoria_realizada(
        "CONSULTA", "STOCK",
        "Auditoria de perdas",
        f"{len(dados)} registos | {formatar_kz(total_valor)} perdidos",
        utilizador_logado["id"], utilizador_logado["nome"]
    )


def ver_lotes_vencidos(utilizador_logado):
    """Lotes vencidos que ainda estao no sistema."""
    janela, tree = criar_janela_tabela(
        "Auditoria Farmacêutica - Lotes Vencidos",
        ("Produto", "Lote", "Validade", "Quantidade"),
        [400, 150, 150, 130],
        cor_header=COR_PERIGO
    )
    
    dados = aud_lotes_vencidos()
    
    for l in dados:
        nome, lote, validade, qtd = l
        tree.insert("", END, values=(nome, lote or "-", validade, qtd), tags=("vencido",))
    
    tree.tag_configure("vencido", background="#fee2e2", foreground="#991b1b")
    
    Label(janela, text=f"Total: {len(dados)} lotes vencidos que ainda estao no sistema. "
                        f"⚠️ Estes produtos NAO devem ser vendidos!",
          font=("Arial", 11, "bold"), bg=COR_FUNDO, fg=COR_PERIGO).pack(pady=10)
    
    registar_auditoria_realizada(
        "CONSULTA", "FARMACEUTICA",
        "Auditoria de lotes vencidos",
        f"{len(dados)} lotes vencidos identificados",
        utilizador_logado["id"], utilizador_logado["nome"]
    )


# ============================================================
# ============ AREA: CAIXA ===================================
# ============================================================

def ver_caixa_movimentos(utilizador_logado):
    """Auditoria de movimentos de caixa (sangrias)."""
    janela, tree = criar_janela_tabela(
        "Auditoria de Caixa - Sangrias (últimos 30 dias)",
        ("Data", "Valor", "Descrição", "Utilizador"),
        [150, 150, 350, 200],
        cor_header=COR_ROXO
    )
    
    dados = aud_sangrias(100)
    
    total_sangrias = sum(s[1] or 0 for s in dados)
    
    for s in dados:
        data, valor, desc, user = s
        tree.insert("", END, values=(
            data, formatar_kz(valor or 0), desc or "-", user or "-"
        ))
    
    Label(janela, text=f"Total: {len(dados)} sangrias  |  "
                        f"Valor total retirado: {formatar_kz(total_sangrias)}",
          font=("Arial", 11, "bold"), bg=COR_FUNDO, fg=COR_ROXO).pack(pady=10)
    
    registar_auditoria_realizada(
        "CONSULTA", "CAIXA",
        "Auditoria de sangrias",
        f"{len(dados)} sangrias | {formatar_kz(total_sangrias)} retirados",
        utilizador_logado["id"], utilizador_logado["nome"]
    )


# ============================================================
# ============ AREA: FARMACEUTICA ============================
# ============================================================

def ver_farmaceutica(utilizador_logado):
    """Menu de auditoria farmaceutica."""
    janela = Toplevel()
    janela.title("JAM Soft - Auditoria Farmacêutica")
    janela.geometry("700x500")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_LARANJA, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="💊 Auditoria Farmacêutica",
          font=("Arial", 16, "bold"), bg=COR_LARANJA, fg="white").pack(pady=20)
    
    Label(janela, text="Selecione o tipo de verificação:",
          font=("Arial", 12, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=20)
    
    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(pady=10)
    
    estilo = {"font": ("Arial", 11, "bold"), "width": 28, "height": 2,
              "bd": 0, "cursor": "hand2", "fg": "white"}
    
    Button(frame, text="📅 Lotes Vencidos", bg=COR_PERIGO,
           command=lambda: ver_lotes_vencidos(utilizador_logado),
           **estilo).pack(pady=6)
    
    Button(frame, text="⚠️ Lotes a Vencer (30 dias)", bg=COR_LARANJA,
           command=lambda: ver_lotes_a_vencer(utilizador_logado),
           **estilo).pack(pady=6)


def ver_lotes_a_vencer(utilizador_logado):
    """Lotes a vencer nos proximos 30 dias."""
    from database import produtos_validade_proxima
    janela, tree = criar_janela_tabela(
        "Auditoria Farmacêutica - Lotes a Vencer (30 dias)",
        ("Produto", "Lote", "Validade", "Quantidade"),
        [400, 150, 150, 130],
        cor_header=COR_LARANJA
    )
    
    dados = produtos_validade_proxima(30)
    
    for l in dados:
        tree.insert("", END, values=(l[0], l[1] or "-", l[2], l[3]), tags=("atencao",))
    
    tree.tag_configure("atencao", background="#fef3c7", foreground="#78350f")
    
    Label(janela, text=f"Total: {len(dados)} lotes a vencer nos proximos 30 dias",
          font=("Arial", 11, "bold"), bg=COR_FUNDO, fg=COR_LARANJA).pack(pady=10)
    
    registar_auditoria_realizada(
        "CONSULTA", "FARMACEUTICA",
        "Auditoria de lotes a vencer",
        f"{len(dados)} lotes a vencer",
        utilizador_logado["id"], utilizador_logado["nome"]
    )


# ============================================================
# ============ AREA: ALTERACOES ==============================
# ============================================================

def ver_alteracoes(utilizador_logado):
    """Alteracoes de produtos (rastreabilidade)."""
    janela, tree = criar_janela_tabela(
        "Auditoria - Alterações de Produtos",
        ("Data", "Utilizador", "Ação", "Detalhes"),
        [150, 150, 180, 450],
        cor_header="#64748b"
    )
    
    dados = aud_alteracoes_produtos(100)
    
    for a in dados:
        tree.insert("", END, values=(a[0], a[1] or "-", a[2], a[3] or "-"))
    
    Label(janela, text=f"Total: {len(dados)} alterações registadas",
          font=("Arial", 11, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=10)
    
    registar_auditoria_realizada(
        "CONSULTA", "PRODUTOS",
        "Auditoria de alteracoes de produtos",
        f"{len(dados)} alteracoes analisadas",
        utilizador_logado["id"], utilizador_logado["nome"]
    )

    # ============================================================
# ============ AREA: NAO CONFORMIDADES =======================
# ============================================================

def ver_nao_conformidades(utilizador_logado, parent=None):
    """Lista de nao conformidades."""
    janela = Toplevel()
    janela.title("JAM Soft - Não Conformidades")
    janela.geometry("1100x650")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_PERIGO, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="📋 Não Conformidades",
          font=("Arial", 16, "bold"), bg=COR_PERIGO, fg="white").pack(pady=20)
    
    # Filtro por estado
    frame_filtro = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#fecaca")
    frame_filtro.pack(fill=X, padx=15, pady=10)
    
    Label(frame_filtro, text="Filtrar por estado:",
          font=("Arial", 11, "bold"), bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=15, pady=10)
    
    filtro_var = StringVar(value="TODAS")
    combo = ttk.Combobox(frame_filtro, textvariable=filtro_var,
                          values=["TODAS", "ABERTA", "EM_ANALISE", "RESOLVIDA", "ENCERRADA"],
                          state="readonly", font=("Arial", 10), width=15)
    combo.pack(side=LEFT, padx=5, pady=10, ipady=4)
    
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=15, pady=10)
    
    colunas = ("ID", "Número", "Data", "Título", "Área", "Severidade", "Estado", "Criado por")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
    tree.column("ID", width=50)
    tree.column("Número", width=100)
    tree.column("Data", width=140)
    tree.column("Título", width=250)
    tree.column("Área", width=110)
    tree.column("Severidade", width=100)
    tree.column("Estado", width=110)
    tree.column("Criado por", width=130)
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    def carregar():
        for i in tree.get_children():
            tree.delete(i)
        
        estado = filtro_var.get()
        if estado == "TODAS":
            estado = None
        
        dados = listar_nao_conformidades(100, estado)
        
        for nc in dados:
            ncid, numero, data, titulo, area, sev, est, criado = nc
            
            tag = ""
            if est == "ABERTA":
                tag = "aberta"
            elif est == "EM_ANALISE":
                tag = "analise"
            elif est == "RESOLVIDA":
                tag = "resolvida"
            elif est == "ENCERRADA":
                tag = "encerrada"
            
            tree.insert("", END, values=(
                ncid, numero, data, titulo, area or "-",
                sev or "-", est, criado or "-"
            ), tags=(tag,))
        
        tree.tag_configure("aberta", background="#fee2e2", foreground="#991b1b")
        tree.tag_configure("analise", background="#fef3c7", foreground="#78350f")
        tree.tag_configure("resolvida", background="#dbeafe", foreground="#1e40af")
        tree.tag_configure("encerrada", background="#dcfce7", foreground="#166534")
    
    combo.bind('<<ComboboxSelected>>', lambda e: carregar())
    carregar()
    
    def nova_nc():
        dialog_nova_nc(utilizador_logado, carregar)
    
    def ver_detalhes():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma não conformidade.")
            return
        
        ncid = tree.item(sel[0])["values"][0]
        dialog_ver_nc(ncid, utilizador_logado, carregar)
    
    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=10)
    
    estilo = {"font": ("Arial", 11, "bold"), "width": 20, "height": 2,
              "bd": 0, "cursor": "hand2", "fg": "white"}
    
    Button(frame_btn, text="➕ Nova NC", bg=COR_PERIGO,
           command=nova_nc, **estilo).pack(side=LEFT, padx=5)
    
    Button(frame_btn, text="👁️ Ver / Atualizar", bg=COR_AZUL,
           command=ver_detalhes, **estilo).pack(side=LEFT, padx=5)
    
    Button(frame_btn, text="🔄 Actualizar", bg="#64748b",
           command=carregar, **estilo).pack(side=LEFT, padx=5)


def dialog_nova_nc(utilizador_logado, callback=None):
    """Dialog para criar uma nova nao conformidade."""
    j = Toplevel()
    j.title("Nova Não Conformidade")
    j.geometry("600x700")
    j.configure(bg=COR_FUNDO)
    j.transient()
    j.grab_set()
    
    header = Frame(j, bg=COR_PERIGO, height=60)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="➕ Nova Não Conformidade",
          font=("Arial", 14, "bold"), bg=COR_PERIGO, fg="white").pack(pady=15)
    
    card = Frame(j, bg=COR_CARD, highlightthickness=1, highlightbackground="#fecaca")
    card.pack(padx=20, pady=15, fill=X)
    
    frame = Frame(card, bg=COR_CARD)
    frame.pack(padx=20, pady=15, fill=X)
    
    Label(frame, text="Título: *", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
    entry_titulo = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
    entry_titulo.pack(fill=X, ipady=6)
    entry_titulo.focus()
    
    Label(frame, text="Descrição:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
    text_desc = Text(frame, height=5, font=("Arial", 11), bd=1, relief=SOLID)
    text_desc.pack(fill=X)
    
    Label(frame, text="Área: *", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
    area_var = StringVar(value="VENDAS")
    ttk.Combobox(frame, textvariable=area_var,
                 values=["VENDAS", "STOCK", "CAIXA", "FARMACEUTICA", "FINANCEIRO", "OUTRO"],
                 state="readonly", font=("Arial", 11)).pack(fill=X, ipady=4)
    
    Label(frame, text="Severidade: *", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
    sev_var = StringVar(value="MEDIA")
    ttk.Combobox(frame, textvariable=sev_var,
                 values=["BAIXA", "MEDIA", "ALTA", "CRITICA"],
                 state="readonly", font=("Arial", 11)).pack(fill=X, ipady=4)
    
    Label(frame, text="Evidência / Observações:",
          font=("Arial", 11, "bold"), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
    text_ev = Text(frame, height=4, font=("Arial", 11), bd=1, relief=SOLID)
    text_ev.pack(fill=X)
    
    def salvar():
        titulo = entry_titulo.get().strip()
        descricao = text_desc.get("1.0", END).strip()
        area = area_var.get()
        sev = sev_var.get()
        ev = text_ev.get("1.0", END).strip()
        
        if not titulo:
            messagebox.showwarning("Aviso", "O título é obrigatório.")
            return
        
        try:
            numero = criar_nao_conformidade(titulo, descricao, area, sev, ev,
                                              utilizador_logado["id"], utilizador_logado["nome"])
            
            registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                "NC CRIADA", f"{numero} | {titulo}")
            
            messagebox.showinfo("Sucesso",
                f"Não Conformidade criada!\n\nNúmero: {numero}\nÁrea: {area}\nSeveridade: {sev}")
            
            j.destroy()
            if callback:
                callback()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")
    
    Button(j, text="💾 Criar Não Conformidade",
           font=("Arial", 12, "bold"), bg=COR_PERIGO, fg="white",
           width=25, height=2, bd=0, cursor="hand2",
           command=salvar).pack(pady=20)


def dialog_ver_nc(nc_id, utilizador_logado, callback=None):
    """Ver e atualizar uma nao conformidade."""
    nc = buscar_nao_conformidade(nc_id)
    if not nc:
        messagebox.showerror("Erro", "Não conformidade não encontrada.")
        return
    
    (ncid, numero, data_criacao, titulo, descricao, area, severidade,
     estado, evidencia, criado_por, data_enc, encerrado_por, conclusao) = nc
    
    j = Toplevel()
    j.title(f"Não Conformidade {numero}")
    j.geometry("700x750")
    j.configure(bg=COR_FUNDO)
    j.transient()
    j.grab_set()
    
    header = Frame(j, bg=COR_PERIGO, height=60)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text=f"📋 {numero}",
          font=("Arial", 14, "bold"), bg=COR_PERIGO, fg="white").pack(pady=15)
    
    # Info
    card = Frame(j, bg=COR_CARD, highlightthickness=1, highlightbackground="#fecaca")
    card.pack(padx=20, pady=10, fill=X)
    
    def linha(label, valor, cor=COR_TEXTO):
        f = Frame(card, bg=COR_CARD)
        f.pack(fill=X, padx=15, pady=4)
        Label(f, text=label, font=("Arial", 10, "bold"),
              bg=COR_CARD, fg="#64748b", width=18, anchor=W).pack(side=LEFT)
        Label(f, text=valor or "-", font=("Arial", 10),
              bg=COR_CARD, fg=cor, wraplength=450, justify=LEFT, anchor=W).pack(side=LEFT, fill=X, expand=True)
    
    linha("Data:", data_criacao)
    linha("Título:", titulo)
    linha("Área:", area)
    linha("Severidade:", severidade)
    linha("Estado:", estado, COR_PERIGO if estado == "ABERTA" else COR_VERDE)
    linha("Criado por:", criado_por)
    
    if descricao:
        linha("Descrição:", descricao)
    if evidencia:
        linha("Evidência:", evidencia)
    
    if estado == "ENCERRADA":
        linha("Encerrada em:", data_enc, COR_VERDE)
        linha("Encerrada por:", encerrado_por)
        linha("Conclusão:", conclusao)
    
    # Atualizacao de estado
    if estado != "ENCERRADA":
        Label(j, text="Atualizar Estado:", font=("Arial", 12, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))
        
        frame_acao = Frame(j, bg=COR_FUNDO)
        frame_acao.pack(pady=5)
        
        estilo = {"font": ("Arial", 10, "bold"), "width": 18, "height": 2,
                  "bd": 0, "cursor": "hand2", "fg": "white"}
        
        def mudar_estado(novo):
            try:
                if novo == "ENCERRADA":
                    conclusao_nc = simpledialog.askstring(
                        "Conclusão",
                        "Descreva a conclusão / ação tomada:",
                        parent=j)
                    if not conclusao_nc:
                        return
                    atualizar_estado_nc(nc_id, novo, utilizador_logado["nome"], conclusao_nc)
                else:
                    atualizar_estado_nc(nc_id, novo, utilizador_logado["nome"])
                
                registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                    f"NC {novo}", f"{numero}")
                
                messagebox.showinfo("Sucesso", f"Estado alterado para {novo}.")
                j.destroy()
                if callback:
                    callback()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro: {e}")
        
        Button(frame_acao, text="Em Análise", bg=COR_LARANJA,
               command=lambda: mudar_estado("EM_ANALISE"), **estilo).grid(row=0, column=0, padx=5, pady=5)
        
        Button(frame_acao, text="Resolvida", bg=COR_AZUL,
               command=lambda: mudar_estado("RESOLVIDA"), **estilo).grid(row=0, column=1, padx=5, pady=5)
        
        Button(frame_acao, text="Encerrar", bg=COR_VERDE,
               command=lambda: mudar_estado("ENCERRADA"), **estilo).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
    else:
        Label(j, text="✅ Esta não conformidade já foi encerrada.",
              font=("Arial", 12, "bold"), bg=COR_FUNDO, fg=COR_VERDE).pack(pady=20)


# ============================================================
# ============ AREA: HISTORICO DE AUDITORIAS =================
# ============================================================

def ver_historico_auditorias(utilizador_logado):
    """Historico de auditorias realizadas."""
    janela, tree = criar_janela_tabela(
        "Histórico de Auditorias Realizadas",
        ("Data", "Tipo", "Área", "Descrição", "Resultado", "Auditor"),
        [150, 100, 130, 280, 280, 150],
        cor_header=COR_AMARELO
    )
    
    dados = listar_auditorias_realizadas(100)
    
    for a in dados:
        data, tipo, area, desc, resultado, auditor = a
        tree.insert("", END, values=(
            data, tipo, area or "-", desc or "-", resultado or "-", auditor or "-"
        ))
    
    Label(janela, text=f"Total: {len(dados)} auditorias registadas",
          font=("Arial", 11, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=10)