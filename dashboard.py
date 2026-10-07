import os
from datetime import datetime, timedelta
from tkinter import *
from tkinter import messagebox, ttk
from database import (conectar, total_vendas_dia, caixa_aberto, registar_auditoria)
from moeda import formatar_kz

COR_FUNDO = "#f8fafc"
COR_PRIMARIA = "#0f172a"
COR_TEXTO = "#1e293b"
COR_CARD = "#ffffff"
COR_VERDE = "#16a34a"
COR_AZUL = "#0891b2"
COR_LARANJA = "#ea580c"
COR_VERMELHO = "#dc2626"
COR_ROXO = "#7c3aed"


def query(sql, params=()):
    """Executa query e retorna resultado."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def query_one(sql, params=()):
    """Executa query e retorna um resultado."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    resultado = cursor.fetchone()
    conn.close()
    return resultado


def obter_dados_dashboard():
    """Retorna todos os dados necessarios para o dashboard."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    mes_atual = datetime.now().strftime("%Y-%m")
    
    dados = {}
    
    # Vendas de hoje
    r = query_one("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM vendas WHERE DATE(data) = DATE(?)", (hoje,))
    dados["vendas_hoje_n"] = r[0] if r else 0
    dados["vendas_hoje_total"] = r[1] if r else 0
    
    # Vendas do mes
    r = query_one("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM vendas WHERE strftime('%Y-%m', data) = ?", (mes_atual,))
    dados["vendas_mes_n"] = r[0] if r else 0
    dados["vendas_mes_total"] = r[1] if r else 0
    
    # Ticket medio do mes
    if dados["vendas_mes_n"] > 0:
        dados["ticket_medio"] = dados["vendas_mes_total"] / dados["vendas_mes_n"]
    else:
        dados["ticket_medio"] = 0
    
    # Valor do estoque
    r = query_one("SELECT COALESCE(SUM(estoque_atual * preco_venda), 0) FROM produtos")
    dados["valor_estoque"] = r[0] if r else 0
    
    # Produtos em stock baixo
    r = query_one("SELECT COUNT(*) FROM produtos WHERE estoque_atual <= estoque_minimo")
    dados["stock_baixo"] = r[0] if r else 0
    
    # Produtos a vencer (30 dias)
    limite = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    r = query_one("""
        SELECT COUNT(*) FROM lotes
        WHERE data_validade <= ? AND data_validade >= ? AND quantidade > 0
    """, (limite, hoje))
    dados["a_vencer"] = r[0] if r else 0
    
    # Vendas ultimos 7 dias
    vendas_7dias = []
    for i in range(6, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        r = query_one("SELECT COALESCE(SUM(total), 0) FROM vendas WHERE DATE(data) = DATE(?)", (d,))
        vendas_7dias.append({
            "data": (datetime.now() - timedelta(days=i)).strftime("%d/%m"),
            "total": r[0] if r else 0
        })
    dados["vendas_7dias"] = vendas_7dias
    
    # Top 5 produtos
    r = query("""
        SELECT p.nome, SUM(iv.quantidade) as qtd
        FROM itens_venda iv
        JOIN produtos p ON p.id = iv.produto_id
        JOIN vendas v ON v.id = iv.venda_id
        WHERE strftime('%Y-%m', v.data) = ?
        GROUP BY p.id
        ORDER BY qtd DESC
        LIMIT 5
    """, (mes_atual,))
    dados["top_produtos"] = r
    
    # Formas de pagamento
    r = query("""
        SELECT forma_pagamento, COUNT(*), COALESCE(SUM(total), 0)
        FROM vendas
        WHERE strftime('%Y-%m', data) = ?
        GROUP BY forma_pagamento
    """, (mes_atual,))
    dados["formas_pagamento"] = r
    
    # Produtos com stock baixo (detalhado)
    r = query("""
        SELECT nome, estoque_atual, estoque_minimo
        FROM produtos
        WHERE estoque_atual <= estoque_minimo
        ORDER BY estoque_atual
        LIMIT 10
    """)
    dados["lista_stock_baixo"] = r
    
    # Produtos a vencer (detalhado)
    r = query("""
        SELECT p.nome, l.numero_lote, l.data_validade, l.quantidade
        FROM lotes l
        JOIN produtos p ON p.id = l.produto_id
        WHERE l.data_validade <= ? AND l.data_validade >= ? AND l.quantidade > 0
        ORDER BY l.data_validade
        LIMIT 10
    """, (limite, hoje))
    dados["lista_a_vencer"] = r
    
    # Caixa aberto?
    cx = caixa_aberto()
    dados["caixa_aberto"] = cx
    
    # Total facturado do mes
    r = query_one("""
        SELECT COUNT(*), COALESCE(SUM(total), 0)
        FROM facturas
        WHERE strftime('%Y-%m', data) = ? AND estado != 'ANULADA'
    """, (mes_atual,))
    dados["facturas_mes_n"] = r[0] if r else 0
    dados["facturas_mes_total"] = r[1] if r else 0
    
    # Clientes novos do mes
    r = query_one("""
        SELECT COUNT(*) FROM clientes
        WHERE strftime('%Y-%m', criado_em) = ?
    """, (mes_atual,))
    dados["clientes_mes"] = r[0] if r else 0
    
    # Produtos com stock
    r = query_one("SELECT COUNT(*) FROM produtos WHERE estoque_atual > 0")
    dados["produtos_stock"] = r[0] if r else 0
    
    # Lucro potencial em stock
    r = query_one("""
        SELECT COALESCE(SUM((preco_venda - preco_custo) * estoque_atual), 0)
        FROM produtos
        WHERE estoque_atual > 0
    """)
    dados["lucro_potencial"] = r[0] if r else 0
    
    return dados


def abrir_dashboard(utilizador_logado):
    """Abre o dashboard principal."""
    
    dados = obter_dados_dashboard()
    
    janela = Toplevel()
    janela.title("JAM Soft - Dashboard")
    janela.geometry("1300x800")
    janela.configure(bg=COR_FUNDO)
    
    # Header
    header = Frame(janela, bg=COR_PRIMARIA, height=100)
    header.pack(fill=X)
    header.pack_propagate(False)
    
    try:
        from PIL import Image, ImageTk
        logo_img = Image.open("logos/JamLogo_transparente.png")
        logo_img = logo_img.resize((80, 80), Image.LANCZOS)
        logo_tk = ImageTk.PhotoImage(logo_img)
        lbl_logo = Label(header, image=logo_tk, bg=COR_PRIMARIA)
        lbl_logo.image = logo_tk
        lbl_logo.pack(side=LEFT, padx=20, pady=10)
    except Exception as e:
        print(f"[AVISO] Logo nao carregado: {e}")
    
    texto_frame = Frame(header, bg=COR_PRIMARIA)
    texto_frame.pack(side=LEFT, fill=BOTH, expand=True, pady=15)
    
    Label(texto_frame, text="📊 Dashboard - Visão Geral", font=("Arial", 20, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(anchor=W)
    
    data_hora = datetime.now().strftime("%d/%m/%Y - %H:%M")
    Label(texto_frame, text=f"Atualizado em: {data_hora}  |  Utilizador: {utilizador_logado['nome']}",
          font=("Arial", 10, "italic"), bg=COR_PRIMARIA, fg="#cbd5e1").pack(anchor=W)

        # ============================================================
    # ================= CARDS DE RESUMO (TOPO) ===================
    # ============================================================
    
    cards_frame = Frame(janela, bg=COR_FUNDO)
    cards_frame.pack(fill=X, padx=20, pady=15)
    
    def criar_card(parent, titulo, valor, cor, subtitulo="", coluna=0, linha=0):
        card = Frame(parent, bg=COR_CARD, highlightthickness=2, highlightbackground=cor, cursor="hand2")
        card.grid(row=linha, column=coluna, padx=8, pady=5, sticky="nsew")
        parent.columnconfigure(coluna, weight=1)
        
        lbl_titulo = Label(card, text=titulo, font=("Arial", 11, "bold"),
              bg=COR_CARD, fg="#6b7280")
        lbl_titulo.pack(pady=(15, 3))
        lbl_valor = Label(card, text=valor, font=("Arial", 22, "bold"),
              bg=COR_CARD, fg=cor)
        lbl_valor.pack()
        widgets_hover = [card, lbl_titulo, lbl_valor]
        if subtitulo:
            lbl_sub = Label(card, text=subtitulo, font=("Arial", 9, "italic"),
                  bg=COR_CARD, fg="#6b7280")
            lbl_sub.pack(pady=(3, 15))
            widgets_hover.append(lbl_sub)
        else:
            lbl_vazio = Label(card, text="", bg=COR_CARD)
            lbl_vazio.pack(pady=(0, 15))
            widgets_hover.append(lbl_vazio)

        # Ligar hover
        def _enter(e, ws=widgets_hover, c=card, co=cor):
            try:
                c.configure(bg=co)
                for w in ws:
                    w.configure(bg=co)
                ws[1].configure(fg="#e5e7eb")
            except Exception:
                pass

        def _leave(e, ws=widgets_hover, c=card, co=cor):
            try:
                c.configure(bg=COR_CARD)
                for w in ws:
                    w.configure(bg=COR_CARD)
                ws[1].configure(fg="#6b7280")
                ws[2].configure(fg=co)
            except Exception:
                pass

        for w in widgets_hover:
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)
    

    criar_card(cards_frame, "📈 Vendas Hoje",
               formatar_kz(dados["vendas_hoje_total"]),
               COR_VERDE,
               f"{dados['vendas_hoje_n']} vendas",
               0)
    
    criar_card(cards_frame, "💵 Vendas do Mês",
               formatar_kz(dados["vendas_mes_total"]),
               COR_AZUL,
               f"{dados['vendas_mes_n']} vendas",
               1)
    
    criar_card(cards_frame, "🎯 Ticket Médio",
               formatar_kz(dados["ticket_medio"]),
               COR_ROXO,
               "por venda",
               2)
    
    criar_card(cards_frame, "📦 Valor do Stock",
               formatar_kz(dados["valor_estoque"]),
               COR_LARANJA,
               "preço de venda",
               3)
    
    criar_card(cards_frame, "🧾 Facturas do Mês",
               str(dados["facturas_mes_n"]),
               COR_PRIMARIA,
               formatar_kz(dados["facturas_mes_total"]),
               4)
    
    criar_card(cards_frame, "👥 Clientes do Mês",
               str(dados["clientes_mes"]),
               "#8b5cf6",
               "novos clientes",
               0, linha=1)
    
    criar_card(cards_frame, "📦 Produtos Stock",
               str(dados["produtos_stock"]),
               "#06b6d4",
               "com stock",
               1, linha=1)
    
    criar_card(cards_frame, "💰 Lucro Potencial",
               formatar_kz(dados["lucro_potencial"]),
               "#10b981",
               "no stock actual",
               2, linha=1)
    
    # ============================================================
    # ================= ALERTAS ==================================
    # ============================================================
    
    alertas_frame = Frame(janela, bg=COR_FUNDO)
    alertas_frame.pack(fill=X, padx=20, pady=(5, 10))
    
    # Caixa
    if dados["caixa_aberto"]:
        cx = dados["caixa_aberto"]
        alerta = Frame(alertas_frame, bg="#dcfce7", highlightthickness=1, highlightbackground=COR_VERDE)
        alerta.pack(fill=X, pady=3)
        Label(alerta, text=f"✅ CAIXA ABERTO #{cx[0]} por {cx[2]} | Valor inicial: {formatar_kz(cx[3])}",
              font=("Arial", 10, "bold"), bg="#dcfce7", fg=COR_VERDE).pack(pady=8, padx=15, anchor=W)
    else:
        alerta = Frame(alertas_frame, bg="#fee2e2", highlightthickness=1, highlightbackground=COR_VERMELHO)
        alerta.pack(fill=X, pady=3)
        Label(alerta, text="⚠️ CAIXA FECHADO - Abra o caixa para comecar a vender",
              font=("Arial", 10, "bold"), bg="#fee2e2", fg=COR_VERMELHO).pack(pady=8, padx=15, anchor=W)
    
    # Stock baixo
    if dados["stock_baixo"] > 0:
        alerta = Frame(alertas_frame, bg="#fef3c7", highlightthickness=1, highlightbackground=COR_LARANJA)
        alerta.pack(fill=X, pady=3)
        Label(alerta, text=f"⚠️ {dados['stock_baixo']} produtos com stock baixo",
              font=("Arial", 10, "bold"), bg="#fef3c7", fg="#92400e").pack(pady=8, padx=15, anchor=W)
    
    # A vencer
    if dados["a_vencer"] > 0:
        alerta = Frame(alertas_frame, bg="#fee2e2", highlightthickness=1, highlightbackground=COR_VERMELHO)
        alerta.pack(fill=X, pady=3)
        Label(alerta, text=f"🚨 {dados['a_vencer']} lotes a vencer nos próximos 30 dias",
              font=("Arial", 10, "bold"), bg="#fee2e2", fg=COR_VERMELHO).pack(pady=8, padx=15, anchor=W)
    
    # ============================================================
    # ================= GRAFICO DE VENDAS 7 DIAS =================
    # ============================================================
    
    graficos_frame = Frame(janela, bg=COR_FUNDO)
    graficos_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
    
    # Grafico 1: Vendas 7 dias
    frame_graf1 = Frame(graficos_frame, bg=COR_CARD, highlightthickness=1, highlightbackground="#cbd5e1")
    frame_graf1.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
    
    Label(frame_graf1, text="📈 Vendas dos Últimos 7 Dias", font=("Arial", 12, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(pady=10)
    
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        fig1 = Figure(figsize=(6, 4), dpi=80, facecolor=COR_CARD)
        ax1 = fig1.add_subplot(111)
        ax1.set_facecolor(COR_CARD)
        
        dias = [v["data"] for v in dados["vendas_7dias"]]
        valores = [v["total"] for v in dados["vendas_7dias"]]
        
        bars = ax1.bar(dias, valores, color=COR_VERDE, edgecolor="#15803d", linewidth=1)
        ax1.set_title("Vendas Diarias (Kz)", fontsize=11, fontweight="bold")
        ax1.set_ylabel("Total (Kz)", fontsize=9)
        ax1.tick_params(axis='x', labelsize=8)
        ax1.tick_params(axis='y', labelsize=8)
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        
        for bar, val in zip(bars, valores):
            height = bar.get_height()
            if height > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:,.0f}', ha='center', va='bottom', fontsize=7)
        
        fig1.tight_layout()
        
        canvas1 = FigureCanvasTkAgg(fig1, master=frame_graf1)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill=BOTH, expand=True, padx=10, pady=10)
    except Exception as e:
        Label(frame_graf1, text=f"Erro ao gerar grafico: {e}",
              bg=COR_CARD, fg=COR_VERMELHO).pack(pady=20)
    
    # Grafico 2: Formas de pagamento
    frame_graf2 = Frame(graficos_frame, bg=COR_CARD, highlightthickness=1, highlightbackground="#cbd5e1")
    frame_graf2.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
    
    Label(frame_graf2, text="💳 Formas de Pagamento (Mes)", font=("Arial", 12, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(pady=10)
    
    try:
        if dados["formas_pagamento"]:
            fig2 = Figure(figsize=(6, 4), dpi=80, facecolor=COR_CARD)
            ax2 = fig2.add_subplot(111)
            ax2.set_facecolor(COR_CARD)
            
            formas = [f[0] or "Outro" for f in dados["formas_pagamento"]]
            valores = [f[2] for f in dados["formas_pagamento"]]
            cores = ["#16a34a", "#0891b2", "#7c3aed", "#f59e0b", "#dc2626", "#6b7280"]
            
            wedges, texts, autotexts = ax2.pie(
                valores, labels=formas, autopct='%1.1f%%',
                colors=cores[:len(formas)], startangle=90,
                textprops={'fontsize': 9}
            )
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(8)
            
            ax2.set_title("Distribuicao por Forma de Pagamento", fontsize=11, fontweight="bold")
            fig2.tight_layout()
            
            canvas2 = FigureCanvasTkAgg(fig2, master=frame_graf2)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill=BOTH, expand=True, padx=10, pady=10)
        else:
            Label(frame_graf2, text="Sem dados de pagamento este mes",
                  font=("Arial", 10, "italic"), bg=COR_CARD, fg="#6b7280").pack(pady=50)
    except Exception as e:
        Label(frame_graf2, text=f"Erro ao gerar grafico: {e}",
              bg=COR_CARD, fg=COR_VERMELHO).pack(pady=20)
    
    # ============================================================
    # ================= TOP PRODUTOS E LISTAS ====================
    # ============================================================
    
    detalhes_frame = Frame(janela, bg=COR_FUNDO)
    detalhes_frame.pack(fill=BOTH, expand=True, padx=20, pady=(0, 15))
    
    # Top 5 produtos
    frame_top = Frame(detalhes_frame, bg=COR_CARD, highlightthickness=1, highlightbackground="#cbd5e1")
    frame_top.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
    
    Label(frame_top, text="🏆 Top 5 Produtos do Mes", font=("Arial", 12, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(pady=10)
    
    tree_top = ttk.Treeview(frame_top, columns=("Produto", "Qtd"), show="headings", height=6)
    tree_top.heading("Produto", text="Produto")
    tree_top.heading("Qtd", text="Qtd")
    tree_top.column("Produto", width=250)
    tree_top.column("Qtd", width=80)
    tree_top.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    for i, p in enumerate(dados["top_produtos"], 1):
        nome, qtd = p
        tree_top.insert("", END, values=(f"{i}. {nome}", qtd))
    
    # Stock baixo detalhado
    frame_stock = Frame(detalhes_frame, bg=COR_CARD, highlightthickness=1, highlightbackground="#fde68a")
    frame_stock.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
    
    Label(frame_stock, text="⚠️ Stock Baixo (Top 10)", font=("Arial", 12, "bold"),
          bg=COR_CARD, fg="#92400e").pack(pady=10)
    
    tree_stock = ttk.Treeview(frame_stock, columns=("Produto", "Atual", "Min"), show="headings", height=6)
    tree_stock.heading("Produto", text="Produto")
    tree_stock.heading("Atual", text="Atual")
    tree_stock.heading("Min", text="Minimo")
    tree_stock.column("Produto", width=200)
    tree_stock.column("Atual", width=70)
    tree_stock.column("Min", width=70)
    tree_stock.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    for p in dados["lista_stock_baixo"]:
        nome, atual, minimo = p
        tree_stock.insert("", END, values=(nome, atual, minimo))
    
    # A vencer detalhado
    frame_vencer = Frame(detalhes_frame, bg=COR_CARD, highlightthickness=1, highlightbackground="#fecaca")
    frame_vencer.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
    
    Label(frame_vencer, text="🚨 A Vencer (30 dias)", font=("Arial", 12, "bold"),
          bg=COR_CARD, fg=COR_VERMELHO).pack(pady=10)
    
    tree_vencer = ttk.Treeview(frame_vencer, columns=("Produto", "Lote", "Validade", "Qtd"),
                                show="headings", height=6)
    tree_vencer.heading("Produto", text="Produto")
    tree_vencer.heading("Lote", text="Lote")
    tree_vencer.heading("Validade", text="Validade")
    tree_vencer.heading("Qtd", text="Qtd")
    tree_vencer.column("Produto", width=150)
    tree_vencer.column("Lote", width=70)
    tree_vencer.column("Validade", width=90)
    tree_vencer.column("Qtd", width=50)
    tree_vencer.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    for l in dados["lista_a_vencer"]:
        nome, lote, validade, qtd = l
        tree_vencer.insert("", END, values=(nome[:20], lote or "-", validade, qtd))
    
    # ============================================================
    # ================= BOTOES DE ACAO ===========================
    # ============================================================
    
    botoes_frame = Frame(janela, bg=COR_FUNDO)
    botoes_frame.pack(fill=X, padx=20, pady=15)
    
    estilo = {"font": ("Arial", 11, "bold"), "width": 20, "height": 2,
              "bd": 0, "cursor": "hand2", "fg": "white"}
    
    def actualizar():
        janela.destroy()
        abrir_dashboard(utilizador_logado)
    
    Button(botoes_frame, text="🔄 Actualizar", bg=COR_AZUL,
           command=actualizar, **estilo).pack(side=LEFT, padx=5)
    
    Button(botoes_frame, text="📊 Relatorios", bg="#7c3aed",
           command=lambda: (janela.destroy(), __import__('relatorios').abrir_relatorios(utilizador_logado)),
           **estilo).pack(side=LEFT, padx=5)
    
    Button(botoes_frame, text="🛒 PDV", bg=COR_VERDE,
           command=lambda: (janela.destroy(), __import__('pdv').abrir_pdv(utilizador_logado)),
           **estilo).pack(side=LEFT, padx=5)
    
    Button(botoes_frame, text="❌ Fechar", bg="#6b7280",
           command=janela.destroy, **estilo).pack(side=LEFT, padx=5)