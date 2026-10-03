# ============================================================
# ============ RELATORIOS AVANCADOS ==========================
# ============================================================
# 
# Ecrã com 5 relatorios avancados:
#   1. Curva ABC (classificacao de produtos)
#   2. Vendas por hora
#   3. Top clientes
#   4. Projecao de fecho do mes
#   5. Produtos em queda
# 
# ============================================================

from tkinter import *
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
from database import (curva_abc, resumo_curva_abc, vendas_por_hora,
                       top_clientes, projecao_fecho_mes, produtos_em_queda)
from moeda import formatar_kz


# ============================================================
# ============ CORES =========================================
# ============================================================

COR_FUNDO = "#0f172a"
COR_CARD = "#1e293b"
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


# ============================================================
# ============ ECRAN PRINCIPAL ===============================
# ============================================================

def abrir_relatorios_avancados(utilizador_logado, parent=None):
    """Abre o ecra de relatorios avancados."""
    
    if parent is None:
        parent = Toplevel()
        parent.withdraw()
    
    janela = Toplevel(parent)
    janela.title("Relatorios Avancados")
    janela.geometry("1200x800")
    janela.configure(bg=COR_FUNDO)
    
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 1200) // 2
    y = (janela.winfo_screenheight() - 800) // 2
    janela.geometry(f"1200x800+{x}+{y}")
    
    # Header
    header = Frame(janela, bg=COR_PRIMARIA, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="📊 Relatorios Avancados",
          font=("Segoe UI", 20, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=(15, 0))
    Label(header, text=f"Utilizador: {utilizador_logado['nome']}  |  "
                        f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
          font=("Segoe UI", 10, "italic"),
          bg=COR_PRIMARIA, fg="#e0e7ff").pack()
    
    # Filtro de periodo (comum a todos)
    frame_filtro = Frame(janela, bg=COR_CARD, highlightthickness=1,
                           highlightbackground=COR_BORDA)
    frame_filtro.pack(fill=X, padx=20, pady=(15, 5))
    
    inner = Frame(frame_filtro, bg=COR_CARD)
    inner.pack(padx=20, pady=12, fill=X)
    
    # Periodo por omissao: mes atual
    hoje = datetime.now()
    primeiro_dia = hoje.replace(day=1)
    
    Label(inner, text="Periodo:",
          font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=(0, 10))
    
    Label(inner, text="De:",
          font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=(0, 5))
    entry_de = Entry(inner, font=("Segoe UI", 10), width=12, bd=1, relief=SOLID)
    entry_de.insert(0, primeiro_dia.strftime("%Y-%m-%d"))
    entry_de.pack(side=LEFT, padx=(0, 15), ipady=4)
    
    Label(inner, text="Ate:",
          font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=(0, 5))
    entry_ate = Entry(inner, font=("Segoe UI", 10), width=12, bd=1, relief=SOLID)
    entry_ate.insert(0, hoje.strftime("%Y-%m-%d"))
    entry_ate.pack(side=LEFT, padx=(0, 15), ipady=4)
    
    Label(inner, text="(AAAA-MM-DD)",
          font=("Segoe UI", 8, "italic"),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(side=LEFT, padx=(0, 15))
    
    # Content area (recarregavel)
    content = Frame(janela, bg=COR_FUNDO)
    content.pack(fill=BOTH, expand=True)
    
    def obter_periodo():
        try:
            d1 = entry_de.get().strip()
            d2 = entry_ate.get().strip()
            datetime.strptime(d1, "%Y-%m-%d")
            datetime.strptime(d2, "%Y-%m-%d")
            return d1, d2
        except ValueError:
            messagebox.showerror("Erro", "Datas invalidas. Use AAAA-MM-DD.")
            return None, None
    
    def limpar():
        for w in content.winfo_children():
            w.destroy()
    
    def mostrar_menu():
        limpar()
        construir_menu(content, utilizador_logado, janela,
                        obter_periodo, limpar)
    
    # Botao "Voltar ao menu" (aparece em cada ecra)
    def botao_voltar(parent):
        Button(parent, text="◄ Voltar ao Menu",
               font=("Segoe UI", 10, "bold"),
               bg="#64748b", fg="white",
               bd=0, cursor="hand2", padx=15, pady=6,
               command=mostrar_menu).pack(side=LEFT, padx=(20, 5), pady=8)
    
    # Guardar referencias
    janela._botao_voltar = botao_voltar
    janela._mostrar_menu = mostrar_menu
    janela._obter_periodo = obter_periodo
    janela._limpar = limpar
    janela._utilizador = utilizador_logado
    janela._content = content
    
    # Mostrar menu inicial
    mostrar_menu()


# ============================================================
# ============ MENU INICIAL ==================================
# ============================================================

def construir_menu(content, utilizador, janela, obter_periodo, limpar):
    """Mostra o menu com os 5 relatorios."""
    
    Label(content, text="Escolhe o relatorio:",
          font=("Segoe UI", 14, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=30, pady=(20, 15))
    
    # Container de cards
    cards = Frame(content, bg=COR_FUNDO)
    cards.pack(fill=X, padx=30, pady=10)
    
    # Card 1 - Curva ABC
    criar_card_relatorio(cards, "📈 Curva ABC",
                          "Classifica produtos em A/B/C",
                          COR_PRIMARIA,
                          lambda: mostrar_curva_abc(content, janela, utilizador,
                                                     obter_periodo, limpar),
                          0)
    
    # Card 2 - Vendas por Hora
    criar_card_relatorio(cards, "🕐 Vendas por Hora",
                          "A que horas se vende mais",
                          COR_AZUL,
                          lambda: mostrar_vendas_hora(content, janela, utilizador,
                                                       obter_periodo, limpar),
                          1)
    
    # Card 3 - Top Clientes
    criar_card_relatorio(cards, "👥 Top Clientes",
                          "Os que mais compram",
                          COR_VERDE,
                          lambda: mostrar_top_clientes(content, janela, utilizador,
                                                        obter_periodo, limpar),
                          2)
    
    # Card 4 - Projecao
    criar_card_relatorio(cards, "🎯 Projecao do Mes",
                          "Vai bater o orcamento?",
                          COR_DOURADO,
                          lambda: mostrar_projecao(content, janela),
                          3)
    
    # Card 5 - Produtos em Queda
    criar_card_relatorio(cards, "📉 Produtos em Queda",
                          "Vendas a diminuir",
                          COR_VERMELHO,
                          lambda: mostrar_produtos_queda(content, janela),
                          4)


def criar_card_relatorio(parent, titulo, subtitulo, cor, comando, coluna):
    """Cria um card de botao."""
    card = Frame(parent, bg=cor, cursor="hand2", width=220, height=110)
    card.grid(row=0, column=coluna, padx=6, pady=6, sticky="nsew")
    card.pack_propagate(False)
    parent.columnconfigure(coluna, weight=1)
    
    lbl1 = Label(card, text=titulo,
                  font=("Segoe UI", 12, "bold"),
                  bg=cor, fg="white", cursor="hand2",
                  wraplength=200, justify=CENTER)
    lbl1.pack(pady=(25, 5))
    
    lbl2 = Label(card, text=subtitulo,
                  font=("Segoe UI", 9, "italic"),
                  bg=cor, fg="#e0e7ff", cursor="hand2",
                  wraplength=200, justify=CENTER)
    lbl2.pack()
    
    for w in [card, lbl1, lbl2]:
        w.bind("<Button-1>", lambda e: comando())


# ============================================================
# ============ HEADER SECUNDARIO (para cada ecra) ============
# ============================================================

def criar_header_voltar(content, janela, titulo, cor):
    """Cria header com botao Voltar."""
    header = Frame(content, bg=cor, height=60)
    header.pack(fill=X)
    header.pack_propagate(False)
    
    Label(header, text=titulo,
          font=("Segoe UI", 14, "bold"),
          bg=cor, fg="white").pack(side=LEFT, padx=20, pady=15)
    
    Button(header, text="◄ Voltar",
           font=("Segoe UI", 10, "bold"),
           bg="#374151", fg="white",
           bd=0, cursor="hand2", padx=15, pady=6,
           command=janela._mostrar_menu).pack(side=RIGHT, padx=20, pady=12)


# ============================================================
# ============ 1. CURVA ABC ==================================
# ============================================================

def mostrar_curva_abc(content, janela, utilizador, obter_periodo, limpar):
    limpar()
    
    d1, d2 = obter_periodo()
    if not d1:
        janela._mostrar_menu()
        return
    
    criar_header_voltar(content, janela,
                         f"Curva ABC ({d1} a {d2})", COR_PRIMARIA)
    
    try:
        dados = curva_abc(d1, d2)
        resumo = resumo_curva_abc(d1, d2)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao calcular: {e}")
        janela._mostrar_menu()
        return
    
    if not dados:
        Label(content, text="Sem vendas no periodo selecionado.",
              font=("Segoe UI", 12, "italic"),
              bg=COR_FUNDO, fg=COR_TEXTO_SEC).pack(pady=50)
        return
    
    # ===== RESUMO POR CLASSE =====
    cards = Frame(content, bg=COR_FUNDO)
    cards.pack(fill=X, padx=20, pady=15)
    
    for i, classe in enumerate(["A", "B", "C"]):
        cor = {"A": COR_VERDE, "B": COR_DOURADO, "C": COR_VERMELHO}[classe]
        info = resumo[classe]
        perc = (info["receita"] / resumo["total_receita"] * 100) if resumo["total_receita"] > 0 else 0
        
        card = Frame(cards, bg=COR_CARD, highlightthickness=2,
                       highlightbackground=cor)
        card.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
        cards.columnconfigure(i, weight=1)
        
        Label(card, text=f"CLASSE {classe}",
              font=("Segoe UI", 12, "bold"),
              bg=COR_CARD, fg=cor).pack(pady=(10, 3))
        Label(card, text=f"{info['produtos']} produtos",
              font=("Segoe UI", 10),
              bg=COR_CARD, fg=COR_TEXTO).pack()
        Label(card, text=formatar_kz(info['receita']),
              font=("Segoe UI", 13, "bold"),
              bg=COR_CARD, fg=cor).pack(pady=(5, 3))
        Label(card, text=f"{perc:.1f}% da receita",
              font=("Segoe UI", 9, "italic"),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(0, 10))
    
    # ===== GRAFICO =====
    frame_graf = Frame(content, bg=COR_CARD, highlightthickness=1,
                        highlightbackground=COR_BORDA)
    frame_graf.pack(fill=X, padx=20, pady=10)
    
    Label(frame_graf, text="Distribuicao da Receita",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(pady=8)
    
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        fig = Figure(figsize=(6, 3), dpi=80, facecolor=COR_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(COR_CARD)
        
        valores = [resumo["A"]["receita"], resumo["B"]["receita"], resumo["C"]["receita"]]
        labels = ["A (80%)", "B (15%)", "C (5%)"]
        cores = [COR_VERDE, COR_DOURADO, COR_VERMELHO]
        
        bars = ax.bar(labels, valores, color=cores, edgecolor="#1e293b")
        ax.set_title("Receita por Classe", fontsize=11, fontweight="bold", color=COR_TEXTO)
        ax.set_ylabel("Kz", fontsize=9, color=COR_TEXTO)
        ax.tick_params(colors=COR_TEXTO, labelsize=9)
        
        for bar, val in zip(bars, valores):
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                    f'{val:,.0f}', ha='center', va='bottom', fontsize=9, color=COR_TEXTO)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame_graf)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=10, pady=10)
    except Exception as e:
        Label(frame_graf, text=f"Erro ao gerar grafico: {e}",
              bg=COR_CARD, fg=COR_VERMELHO).pack(pady=10)
    
    # ===== TABELA =====
    Label(content, text="Detalhe de Produtos",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=30, pady=(15, 5))
    
    frame_tab = Frame(content, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=20, pady=(0, 15))
    
    colunas = ("Classe", "Produto", "Codigo", "Qtd", "Receita", "% Individual", "% Acumulado")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=12)
    
    for c in colunas:
        tree.heading(c, text=c)
    
    tree.column("Classe", width=60)
    tree.column("Produto", width=280)
    tree.column("Codigo", width=120)
    tree.column("Qtd", width=70)
    tree.column("Receita", width=130)
    tree.column("% Individual", width=100)
    tree.column("% Acumulado", width=110)
    
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    # Tags de cor por classe
    tree.tag_configure("A", background="#132a1a", foreground=COR_VERDE)
    tree.tag_configure("B", background="#3f3a13", foreground=COR_DOURADO)
    tree.tag_configure("C", background="#3f1a1a", foreground="#fca5a5")
    
    for d in dados:
        tree.insert("", END, values=(
            d["classe"],
            d["nome"][:40],
            d["codigo"] or "-",
            d["quantidade"],
            formatar_kz(d["receita"]),
            f"{d['percentagem']:.2f}%",
            f"{d['acumulado']:.2f}%"
        ), tags=(d["classe"],))


# ============================================================
# ============ 2. VENDAS POR HORA ============================
# ============================================================

def mostrar_vendas_hora(content, janela, utilizador, obter_periodo, limpar):
    limpar()
    
    d1, d2 = obter_periodo()
    if not d1:
        janela._mostrar_menu()
        return
    
    criar_header_voltar(content, janela,
                         f"Vendas por Hora ({d1} a {d2})", COR_AZUL)
    
    try:
        dados = vendas_por_hora(d1, d2)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro: {e}")
        janela._mostrar_menu()
        return
    
    total_vendas = sum(d["num_vendas"] for d in dados)
    total_receita = sum(d["total"] for d in dados)
    
    if total_vendas == 0:
        Label(content, text="Sem vendas no periodo.",
              font=("Segoe UI", 12, "italic"),
              bg=COR_FUNDO, fg=COR_TEXTO_SEC).pack(pady=50)
        return
    
    # Resumo
    card = Frame(content, bg=COR_CARD, highlightthickness=1,
                   highlightbackground=COR_AZUL)
    card.pack(fill=X, padx=20, pady=15)
    
    Label(card, text=f"Total: {total_vendas} vendas | Receita: {formatar_kz(total_receita)}",
          font=("Segoe UI", 12, "bold"),
          bg=COR_CARD, fg=COR_AZUL).pack(pady=10)
    
    # Grafico
    frame_graf = Frame(content, bg=COR_CARD, highlightthickness=1,
                        highlightbackground=COR_BORDA)
    frame_graf.pack(fill=BOTH, expand=True, padx=20, pady=10)
    
    Label(frame_graf, text="Distribuicao das Vendas por Hora",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(pady=8)
    
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        fig = Figure(figsize=(10, 4), dpi=80, facecolor=COR_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(COR_CARD)
        
        horas = [d["hora"] for d in dados]
        valores = [d["total"] for d in dados]
        
        bars = ax.bar(horas, valores, color=COR_AZUL, edgecolor="#0284c7")
        ax.set_title("Receita por Hora", fontsize=11, fontweight="bold", color=COR_TEXTO)
        ax.set_ylabel("Kz", fontsize=9, color=COR_TEXTO)
        ax.tick_params(colors=COR_TEXTO, labelsize=8)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        for bar, val in zip(bars, valores):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                        f'{val:,.0f}', ha='center', va='bottom', fontsize=7, color=COR_TEXTO)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame_graf)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=10, pady=10)
    except Exception as e:
        Label(frame_graf, text=f"Erro: {e}",
              bg=COR_CARD, fg=COR_VERMELHO).pack(pady=10)


# ============================================================
# ============ 3. TOP CLIENTES ===============================
# ============================================================

def mostrar_top_clientes(content, janela, utilizador, obter_periodo, limpar):
    limpar()
    
    d1, d2 = obter_periodo()
    if not d1:
        janela._mostrar_menu()
        return
    
    criar_header_voltar(content, janela,
                         f"Top Clientes ({d1} a {d2})", COR_VERDE)
    
    try:
        dados = top_clientes(d1, d2, 20)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro: {e}")
        janela._mostrar_menu()
        return
    
    if not dados:
        Label(content, text="Sem clientes registados no periodo.",
              font=("Segoe UI", 12, "italic"),
              bg=COR_FUNDO, fg=COR_TEXTO_SEC).pack(pady=50)
        return
    
    Label(content, text="Top 20 Clientes",
          font=("Segoe UI", 12, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=30, pady=(15, 5))
    
    frame_tab = Frame(content, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=20, pady=(0, 15))
    
    colunas = ("#", "Cliente", "NIF", "Telefone", "Compras", "Total", "Ticket Medio")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=18)
    
    for c in colunas:
        tree.heading(c, text=c)
    
    tree.column("#", width=40)
    tree.column("Cliente", width=250)
    tree.column("NIF", width=120)
    tree.column("Telefone", width=130)
    tree.column("Compras", width=90)
    tree.column("Total", width=130)
    tree.column("Ticket Medio", width=130)
    
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    tree.tag_configure("top3", background="#3f3a13", foreground=COR_DOURADO)
    
    for i, c in enumerate(dados, 1):
        tag = "top3" if i <= 3 else ""
        tree.insert("", END, values=(
            i,
            c["nome"][:35],
            c["nif"] or "-",
            c["telefone"] or "-",
            c["num_compras"],
            formatar_kz(c["total"]),
            formatar_kz(c["ticket_medio"])
        ), tags=(tag,))


# ============================================================
# ============ 4. PROJECAO DO MES ============================
# ============================================================

def mostrar_projecao(content, janela):
    content_master = janela._content
    janela._limpar()
    
    criar_header_voltar(content_master, janela,
                         "Projecao de Fecho do Mes", COR_DOURADO)
    
    try:
        dados = projecao_fecho_mes()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro: {e}")
        janela._mostrar_menu()
        return
    
    # Card principal
    card = Frame(content_master, bg=COR_CARD, highlightthickness=2,
                   highlightbackground=COR_DOURADO)
    card.pack(fill=X, padx=30, pady=20)
    
    Label(card, text=f"Mes: {dados['mes']}",
          font=("Segoe UI", 14, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(pady=(15, 5))
    
    Label(card, text=f"Dia {dados['dia_atual']} de {dados['dias_no_mes']}",
          font=("Segoe UI", 10, "italic"),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(0, 15))
    
    # Grid de informacoes
    grid = Frame(card, bg=COR_CARD)
    grid.pack(pady=10, padx=30, fill=X)
    
    def linha_info(parent, linha, label, valor, cor):
        Label(parent, text=label,
              font=("Segoe UI", 10, "bold"),
              bg=COR_CARD, fg=COR_TEXTO_SEC).grid(row=linha, column=0, sticky=W, padx=10, pady=5)
        Label(parent, text=valor,
              font=("Segoe UI", 13, "bold"),
              bg=COR_CARD, fg=cor).grid(row=linha, column=1, sticky=E, padx=10, pady=5)
    
    grid.columnconfigure(0, weight=1)
    grid.columnconfigure(1, weight=1)
    
    linha_info(grid, 0, "Orcamento do mes:", formatar_kz(dados["orcamento"]), COR_DOURADO)
    linha_info(grid, 1, "Vendido ate hoje:", formatar_kz(dados["vendido_ate_hoje"]), COR_VERDE)
    linha_info(grid, 2, "% Atingida:", f"{dados['percentagem_atual']:.1f}%", COR_AZUL)
    linha_info(grid, 3, "Media diaria (7d):", formatar_kz(dados["media_diaria"]), COR_ROXO)
    linha_info(grid, 4, "Projecao de fecho:", formatar_kz(dados["projecao"]),
                COR_VERDE if dados["vai_bater"] else COR_ALERTA)
    linha_info(grid, 5, "% Projetada:", f"{dados['percentagem_projetada']:.1f}%",
                COR_VERDE if dados["vai_bater"] else COR_ALERTA)
    
    # Veredicto
    veredicto = Frame(card, bg=COR_CARD)
    veredicto.pack(pady=20, padx=30, fill=X)
    
    if dados["orcamento"] <= 0:
        msg = "Nenhum orcamento definido para este mes."
        cor = COR_TEXTO_SEC
        emoji = "ℹ️"
    elif dados["vai_bater"]:
        msg = f"Vai bater a meta! Projecao +{formatar_kz(dados['projecao'] - dados['orcamento'])}"
        cor = COR_VERDE
        emoji = "🎉"
    else:
        falta = dados["orcamento"] - dados["projecao"]
        msg = (f"Atencao: projecao abaixo do orcamento em {formatar_kz(falta)}.\n"
               f"Necessario vender {formatar_kz(dados['necessario_por_dia'])}/dia "
               f"nos {dados['dias_restantes']} dias restantes.")
        cor = COR_ALERTA
        emoji = "⚠️"
    
    Label(veredicto, text=f"{emoji} {msg}",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=cor,
          wraplength=700, justify=CENTER).pack(pady=10)


# ============================================================
# ============ 5. PRODUTOS EM QUEDA ==========================
# ============================================================

def mostrar_produtos_queda(content, janela):
    janela._limpar()
    
    criar_header_voltar(janela._content, janela,
                         "Produtos em Queda (ultimos 30 dias vs 30 anteriores)", COR_VERMELHO)
    
    try:
        dados = produtos_em_queda(20)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro: {e}")
        janela._mostrar_menu()
        return
    
    if not dados:
        Label(janela._content, text="Nenhum produto em queda significativa.",
              font=("Segoe UI", 12, "italic"),
              bg=COR_FUNDO, fg=COR_TEXTO_SEC).pack(pady=50)
        return
    
    Label(janela._content,
          text=f"⚠️ {len(dados)} produtos com queda superior a 30%",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_ALERTA).pack(anchor=W, padx=30, pady=(15, 5))
    
    frame_tab = Frame(janela._content, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=20, pady=(0, 15))
    
    colunas = ("Produto", "Codigo", "30d Antes", "30d Agora", "Variacao", "%")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=18)
    
    for c in colunas:
        tree.heading(c, text=c)
    
    tree.column("Produto", width=300)
    tree.column("Codigo", width=130)
    tree.column("30d Antes", width=110)
    tree.column("30d Agora", width=110)
    tree.column("Variacao", width=110)
    tree.column("%", width=90)
    
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    tree.tag_configure("queda_alta", background="#3f1a1a", foreground="#fca5a5")
    tree.tag_configure("queda_media", background="#3f2a13", foreground="#fdba74")
    
    for d in dados:
        tag = "queda_alta" if d["percentagem"] < -50 else "queda_media"
        tree.insert("", END, values=(
            d["nome"][:40],
            d["codigo"] or "-",
            d["qtd_antes"],
            d["qtd_agora"],
            d["variacao"],
            f"{d['percentagem']:.1f}%"
        ), tags=(tag,))


# ============================================================
# ============ TESTE DIRETO ==================================
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  TESTE - relatorios_avancados.py")
    print("="*60)
    
    from datetime import datetime as dt
    
    hoje = dt.now()
    d1 = hoje.replace(day=1).strftime("%Y-%m-%d")
    d2 = hoje.strftime("%Y-%m-%d")
    
    print(f"\n[1] Curva ABC ({d1} a {d2}):")
    from database import curva_abc
    dados = curva_abc(d1, d2)
    print(f"    {len(dados)} produtos classificados")
    
    print(f"\n[2] Vendas por hora:")
    from database import vendas_por_hora
    dados2 = vendas_por_hora(d1, d2)
    total = sum(d["num_vendas"] for d in dados2)
    print(f"    {total} vendas no periodo")
    
    print(f"\n[3] Top clientes:")
    from database import top_clientes
    dados3 = top_clientes(d1, d2, 20)
    print(f"    {len(dados3)} clientes")
    
    print(f"\n[4] Projecao do mes:")
    from database import projecao_fecho_mes
    dados4 = projecao_fecho_mes()
    print(f"    Projecao: {dados4['projecao']:.0f}")
    print(f"    Vai bater: {dados4['vai_bater']}")
    
    print(f"\n[5] Produtos em queda:")
    from database import produtos_em_queda
    dados5 = produtos_em_queda(20)
    print(f"    {len(dados5)} produtos em queda")
    
    print("\n[6] Abrir janela de teste...")
    
    root = Tk()
    root.withdraw()
    
    utilizador = {"id": 1, "nome": "Teste", "perfil": "admin"}
    
    abrir_relatorios_avancados(utilizador, root)
    
    root.mainloop()
    
    print("\n" + "="*60 + "\n")