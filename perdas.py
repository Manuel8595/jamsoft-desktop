from tkinter import *
from tkinter import messagebox, ttk
from database import (registar_perda, listar_perdas, resumo_perdas_mes,
                       listar_perdas_mes, listar_perdas_tipo, dar_baixa_lote,
                       obter_produto_com_lotes, obter_produto_por_codigo_com_id,
                       aumentar_estoque_produto, aumentar_lote, registar_auditoria,
                       listar_produtos)
from moeda import formatar_kz
from datetime import datetime

COR_FUNDO = "#fef2f2"
COR_PRIMARIA = "#dc2626"
COR_TEXTO = "#7f1d1d"
COR_PERIGO = "#991b1b"
COR_HEADER = "#b91c1c"
COR_CARD = "#ffffff"
COR_VERDE = "#16a34a"
COR_LARANJA = "#ea580c"
COR_ROXO = "#7c3aed"


def abrir_perdas(utilizador_logado):
    janela = Toplevel()
    janela.title("JAM Soft - Controlo de Perdas (Anti-Quebra)")
    janela.geometry("1000x750")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Controlo de Perdas (Anti-Quebra)", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)
    
    resumo = resumo_perdas_mes()
    
    card_resumo = Frame(janela, bg=COR_CARD, highlightthickness=2, highlightbackground=COR_PERIGO)
    card_resumo.pack(fill=X, padx=20, pady=15)
    
    Label(card_resumo, text=f"Resumo de {resumo['mes']}", font=("Arial", 14, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(pady=(15, 5))
    
    frame_totais = Frame(card_resumo, bg=COR_CARD)
    frame_totais.pack(pady=10)
    
    Label(frame_totais, text="Total de registos:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=0, padx=15, sticky=E)
    Label(frame_totais, text=str(resumo["total_n"]), font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_PERIGO).grid(row=0, column=1, padx=15, sticky=W)
    
    Label(frame_totais, text="Valor perdido:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=1, column=0, padx=15, sticky=E)
    Label(frame_totais, text=formatar_kz(resumo["total_valor"]), font=("Arial", 14, "bold"),
          bg=COR_CARD, fg=COR_PERIGO).grid(row=1, column=1, padx=15, sticky=W)
    
    if resumo["por_tipo"]:
        frame_detalhe = Frame(card_resumo, bg=COR_CARD)
        frame_detalhe.pack(pady=(10, 15))
        
        Label(frame_detalhe, text="Detalhe por tipo:", font=("Arial", 10, "italic"),
              bg=COR_CARD, fg="#6b7280").pack()
        
        for tipo, n, valor in resumo["por_tipo"]:
            Label(frame_detalhe, text=f"  - {tipo}: {n} registos - {formatar_kz(valor)}",
                  font=("Arial", 10), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W)
    else:
        Label(card_resumo, text="Sem perdas registadas este mes.",
              font=("Arial", 10, "italic"), bg=COR_CARD, fg=COR_VERDE).pack(pady=(10, 15))
    
    Label(janela, text="Escolhe o tipo de registo:", font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))
    
    frame_botoes = Frame(janela, bg=COR_FUNDO)
    frame_botoes.pack(pady=10)
    
    estilo = {"font": ("Arial", 11, "bold"), "width": 24, "height": 3,
              "bd": 0, "cursor": "hand2", "fg": "white"}
    
    Button(frame_botoes, text="Registar Quebra", bg=COR_PERIGO,
           command=lambda: registar_tipo("QUEBRA", utilizador_logado, janela),
           **estilo).grid(row=0, column=0, padx=6, pady=6)
    
    Button(frame_botoes, text="Registar Furto", bg="#7f1d1d",
           command=lambda: registar_tipo("FURTO", utilizador_logado, janela),
           **estilo).grid(row=0, column=1, padx=6, pady=6)
    
    Button(frame_botoes, text="Vencimento", bg=COR_LARANJA,
           command=lambda: registar_tipo("VENCIMENTO", utilizador_logado, janela),
           **estilo).grid(row=1, column=0, padx=6, pady=6)
    
    Button(frame_botoes, text="Devolucao Cliente", bg=COR_ROXO,
           command=lambda: registar_tipo("DEVOLUCAO", utilizador_logado, janela),
           **estilo).grid(row=1, column=1, padx=6, pady=6)
    
    Button(frame_botoes, text="Ver Historico", bg="#0891b2",
           command=lambda: ver_historico(janela),
           **estilo).grid(row=2, column=0, padx=6, pady=6)
    
    Button(frame_botoes, text="Ver Resumo Anual", bg="#059669",
           command=lambda: ver_resumo_anual(janela),
           **estilo).grid(row=2, column=1, padx=6, pady=6)
    
    Label(janela, text="Ultimas 10 perdas registadas:", font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(20, 5))
    
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=20, pady=10)
    
    colunas = ("Data", "Tipo", "Produto", "Qtd", "Valor", "Motivo", "Utilizador")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=8)
    for col in colunas:
        tree.heading(col, text=col)
    tree.column("Data", width=140)
    tree.column("Tipo", width=100)
    tree.column("Produto", width=200)
    tree.column("Qtd", width=60)
    tree.column("Valor", width=100)
    tree.column("Motivo", width=180)
    tree.column("Utilizador", width=120)
    tree.pack(fill=BOTH, expand=True)
    
    def carregar_ultimas():
        for i in tree.get_children():
            tree.delete(i)
        for p in listar_perdas(10):
            pid, data, tipo, nome, qtd, valor, motivo, user = p
            tag = ""
            if tipo == "QUEBRA":
                tag = "quebra"
            elif tipo == "FURTO":
                tag = "furto"
            elif tipo == "VENCIMENTO":
                tag = "vencimento"
            elif tipo == "DEVOLUCAO":
                tag = "devolucao"
            
            tree.insert("", END, values=(data, tipo, nome or "-", qtd,
                                          formatar_kz(valor or 0), motivo or "-",
                                          user or "-"), tags=(tag,))
        
        tree.tag_configure("quebra", foreground=COR_PERIGO)
        tree.tag_configure("furto", foreground="#7f1d1d")
        tree.tag_configure("vencimento", foreground=COR_LARANJA)
        tree.tag_configure("devolucao", foreground=COR_ROXO)
    
    carregar_ultimas()


def registar_tipo(tipo, utilizador_logado, parent):
    config = {
        "QUEBRA": (COR_PERIGO, "Registar Quebra", "Produto danificado, derrame, etc."),
        "FURTO": ("#7f1d1d", "Registar Furto", "Produto furtado ou desaparecido"),
        "VENCIMENTO": (COR_LARANJA, "Registar Vencimento", "Produto vencido (baixa de lote)"),
        "DEVOLUCAO": (COR_ROXO, "Devolucao de Cliente", "Produto devolvido - volta ao estoque"),
    }
    
    cor, titulo, subtitulo = config[tipo]
    
    janela = Toplevel(parent)
    janela.title(titulo)
    janela.geometry("650x750")
    janela.configure(bg=COR_FUNDO)
    janela.transient(parent)
    janela.grab_set()
    
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 650) // 2
    y = (janela.winfo_screenheight() - 750) // 2
    janela.geometry(f"650x750+{x}+{y}")
    
    header = Frame(janela, bg=cor, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text=titulo, font=("Arial", 16, "bold"),
          bg=cor, fg="white").pack(pady=15)
    
    Label(janela, text=subtitulo, font=("Arial", 10, "italic"),
          bg=COR_FUNDO, fg="#6b7280").pack(pady=(10, 15))
    
    card = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#fecaca")
    card.pack(padx=20, fill=X)
    
    frame = Frame(card, bg=COR_CARD)
    frame.pack(padx=20, pady=15, fill=X)
    
    Label(frame, text="Codigo de Barras do Produto:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
    
    entry_codigo = Entry(frame, font=("Arial", 14), width=25, bd=1, relief=SOLID)
    entry_codigo.pack(fill=X, ipady=6)
    entry_codigo.focus()
    
    produto_atual = {"id": None, "nome": None, "custo": 0, "venda": 0, "estoque": 0, "lotes": []}
    
    info_var = StringVar(value="Digite o codigo e aperte Enter")
    info_label = Label(frame, textvariable=info_var, font=("Arial", 10),
                        bg=COR_CARD, fg="#6b7280", wraplength=550, justify=LEFT)
    info_label.pack(anchor=W, pady=5)
    
    def buscar_produto(event=None):
        codigo = entry_codigo.get().strip()
        if not codigo:
            return
        
        produto = obter_produto_por_codigo_com_id(codigo)
        
        if not produto:
            info_var.set(f"Produto '{codigo}' nao encontrado!")
            info_label.config(fg=COR_PERIGO)
            produto_atual["id"] = None
            return
        
        pid, nome, custo, venda, estoque = produto
        produto_atual["id"] = pid
        produto_atual["nome"] = nome
        produto_atual["custo"] = custo or 0
        produto_atual["venda"] = venda or 0
        produto_atual["estoque"] = estoque or 0
        
        if tipo == "VENCIMENTO":
            _, lotes = obter_produto_com_lotes(pid)
            produto_atual["lotes"] = lotes
            
            if lotes:
                info_var.set(f"{nome}\nEstoque atual: {estoque} un.\n{len(lotes)} lote(s) disponivel(is)")
            else:
                info_var.set(f"{nome}\nEstoque atual: {estoque} un.\nSem lotes disponiveis")
        else:
            info_var.set(f"{nome}\nEstoque atual: {estoque} un.")
        
        info_label.config(fg=COR_VERDE)
    
    entry_codigo.bind('<Return>', buscar_produto)
    
    lote_var = StringVar()
    combo_lote = None
    
    if tipo == "VENCIMENTO":
        Label(frame, text="Selecione o Lote Vencido:", font=("Arial", 11, "bold"),
              bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
        
        combo_lote = ttk.Combobox(frame, textvariable=lote_var, state="readonly",
                                    font=("Arial", 11))
        combo_lote.pack(fill=X, ipady=4)
        
        def atualizar_lotes(event=None):
            if produto_atual["id"]:
                _, lotes = obter_produto_com_lotes(produto_atual["id"])
                produto_atual["lotes"] = lotes
                lista = [f"{l[0]} - Lote {l[1] or '?'} | Validade: {l[2]} | Qtd: {l[3]}" for l in lotes]
                combo_lote["values"] = lista
                if lista:
                    combo_lote.current(0)
        
        entry_codigo.bind('<FocusOut>', atualizar_lotes)
        
        Label(frame, text="Quantidade a dar baixa:", font=("Arial", 11, "bold"),
              bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
        entry_qtd = Entry(frame, font=("Arial", 14), width=15, bd=1, relief=SOLID)
        entry_qtd.pack(anchor=W, ipady=6)
    else:
        Label(frame, text="Quantidade:", font=("Arial", 11, "bold"),
              bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
        entry_qtd = Entry(frame, font=("Arial", 14), width=15, bd=1, relief=SOLID)
        entry_qtd.pack(anchor=W, ipady=6)
    
    Label(frame, text="Motivo / Descricao:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
    entry_motivo = Entry(frame, font=("Arial", 11), bd=1, relief=SOLID)
    entry_motivo.pack(fill=X, ipady=6)
    
    motivos_default = {
        "QUEBRA": "Produto danificado",
        "FURTO": "Furto identificado",
        "VENCIMENTO": "Produto vencido",
        "DEVOLUCAO": "Devolucao de cliente",
    }
    entry_motivo.insert(0, motivos_default[tipo])
    
    preview_var = StringVar(value="")
    preview_label = Label(janela, textvariable=preview_var, font=("Arial", 13, "bold"),
                          bg=COR_FUNDO, fg=COR_PERIGO)
    preview_label.pack(pady=15)
    
    def atualizar_preview(event=None):
        try:
            qtd = int(entry_qtd.get().strip() or 0)
            if qtd <= 0:
                preview_var.set("")
                return
            
            if tipo == "DEVOLUCAO":
                preview_var.set(f"{qtd} un. voltam ao estoque")
                preview_label.config(fg=COR_ROXO)
            else:
                valor = produto_atual["custo"] * qtd
                preview_var.set(f"Perda estimada: {formatar_kz(valor)}")
                preview_label.config(fg=cor)
        except ValueError:
            preview_var.set("")
    
    entry_qtd.bind('<KeyRelease>', atualizar_preview)
    
    def confirmar():
        if not produto_atual["id"]:
            messagebox.showwarning("Aviso", "Busque o produto primeiro.")
            return
        
        try:
            qtd = int(entry_qtd.get().strip())
            if qtd <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Aviso", "Quantidade invalida.")
            return
        
        if tipo != "DEVOLUCAO" and qtd > produto_atual["estoque"]:
            messagebox.showwarning("Aviso",
                f"Estoque insuficiente!\n\n"
                f"Produto: {produto_atual['nome']}\n"
                f"Disponivel: {produto_atual['estoque']} un.\n"
                f"Pedido: {qtd} un.")
            return
        
        motivo = entry_motivo.get().strip() or tipo.capitalize()
        
        lote_id = None
        if tipo == "VENCIMENTO":
            if not combo_lote.get():
                messagebox.showwarning("Aviso", "Selecione um lote.")
                return
            
            try:
                lote_id = int(combo_lote.get().split(" - ")[0])
                dar_baixa_lote(lote_id, qtd)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao baixar lote: {e}")
                return
        
        if tipo == "DEVOLUCAO":
            valor_perdido = 0
        else:
            valor_perdido = produto_atual["custo"] * qtd
        
        # Dar baixa no estoque geral (exceto devolucao)
        if tipo != "DEVOLUCAO":
            from database import conectar
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("UPDATE produtos SET estoque_atual = estoque_atual - ? WHERE id = ?",
                           (qtd, produto_atual["id"]))
            conn.commit()
            conn.close()
        
        # Se for DEVOLUCAO, AUMENTAR o estoque
        if tipo == "DEVOLUCAO":
            aumentar_estoque_produto(produto_atual["id"], qtd)
            if produto_atual["lotes"]:
                primeiro_lote = produto_atual["lotes"][0][0]
                aumentar_lote(primeiro_lote, qtd)
        
        registar_perda(tipo, produto_atual["id"], lote_id, qtd, valor_perdido,
                        motivo, utilizador_logado["id"], utilizador_logado["nome"])
        
        registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                            f"REGISTO {tipo}",
                            f"Produto: {produto_atual['nome']} | Qtd: {qtd} | Valor: {formatar_kz(valor_perdido)} | Motivo: {motivo}")
        
        if tipo == "DEVOLUCAO":
            messagebox.showinfo("Sucesso",
                f"Devolucao registada!\n\n"
                f"Produto: {produto_atual['nome']}\n"
                f"Quantidade: {qtd} un.\n"
                f"Voltou ao estoque.")
        else:
            messagebox.showinfo("Sucesso",
                f"Perda registada!\n\n"
                f"Tipo: {tipo}\n"
                f"Produto: {produto_atual['nome']}\n"
                f"Quantidade: {qtd} un.\n"
                f"Valor perdido: {formatar_kz(valor_perdido)}")
        
        janela.destroy()
        parent.destroy()
        abrir_perdas(utilizador_logado)
    
    entry_motivo.bind('<Return>', lambda e: confirmar())
    
    frame_botoes = Frame(janela, bg=COR_FUNDO)
    frame_botoes.pack(pady=15)
    
    Button(frame_botoes, text="Confirmar Registo", font=("Arial", 13, "bold"),
           bg=cor, fg="white", width=25, height=2, bd=0, cursor="hand2",
           command=confirmar).pack(pady=5)
    
    Button(frame_botoes, text="Cancelar", font=("Arial", 11),
           bg="#6b7280", fg="white", width=20, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack()


def ver_historico(parent):
    janela = Toplevel(parent)
    janela.title("Historico de Perdas")
    janela.geometry("1100x650")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Historico de Perdas - Ultimas 100", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)
    
    frame_filtro = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#fecaca")
    frame_filtro.pack(fill=X, padx=15, pady=10)
    
    Label(frame_filtro, text="Filtrar por mes (AAAA-MM):", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=15, pady=10)
    
    entry_mes = Entry(frame_filtro, font=("Arial", 11), width=12, bd=1, relief=SOLID)
    entry_mes.insert(0, datetime.now().strftime("%Y-%m"))
    entry_mes.pack(side=LEFT, padx=5, pady=10, ipady=4)
    
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=15, pady=10)
    
    colunas = ("Data", "Tipo", "Produto", "Qtd", "Valor", "Motivo", "Utilizador")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=18)
    for col in colunas:
        tree.heading(col, text=col)
    tree.column("Data", width=140)
    tree.column("Tipo", width=100)
    tree.column("Produto", width=200)
    tree.column("Qtd", width=60)
    tree.column("Valor", width=100)
    tree.column("Motivo", width=200)
    tree.column("Utilizador", width=120)
    tree.pack(fill=BOTH, expand=True)
    
    total_var = StringVar(value="")
    Label(janela, textvariable=total_var, font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_PERIGO).pack(pady=5)
    
    def carregar():
        for i in tree.get_children():
            tree.delete(i)
        
        mes = entry_mes.get().strip()
        
        try:
            dados = listar_perdas_mes(mes)
        except Exception:
            dados = listar_perdas(100)
        
        total_valor = 0
        for p in dados:
            data, tipo, nome, qtd, valor, motivo, user = p
            total_valor += valor or 0
            
            tag = tipo.lower() if tipo else ""
            tree.insert("", END, values=(data, tipo, nome or "-", qtd,
                                          formatar_kz(valor or 0), motivo or "-",
                                          user or "-"), tags=(tag,))
        
        tree.tag_configure("quebra", foreground=COR_PERIGO)
        tree.tag_configure("furto", foreground="#7f1d1d")
        tree.tag_configure("vencimento", foreground=COR_LARANJA)
        tree.tag_configure("devolucao", foreground=COR_ROXO)
        
        total_var.set(f"Total: {len(dados)} registos | Valor perdido: {formatar_kz(total_valor)}")
    
    entry_mes.bind('<Return>', lambda e: carregar())
    
    Button(frame_filtro, text="Filtrar", font=("Arial", 10, "bold"),
           bg=COR_PRIMARIA, fg="white", bd=0, cursor="hand2", padx=15, pady=5,
           command=carregar).pack(side=LEFT, padx=10, pady=10)
    
    carregar()


def ver_resumo_anual(parent):
    janela = Toplevel(parent)
    janela.title("Resumo Anual de Perdas")
    janela.geometry("1000x700")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Resumo Anual de Perdas", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)
    
    ano_atual = datetime.now().strftime("%Y")
    
    from database import conectar
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT strftime('%m', data) as mes, COUNT(*), COALESCE(SUM(valor_perdido), 0)
        FROM perdas
        WHERE strftime('%Y', data) = ?
        GROUP BY mes
        ORDER BY mes
    ''', (ano_atual,))
    dados_mes = cursor.fetchall()
    
    cursor.execute('''
        SELECT tipo, COUNT(*), COALESCE(SUM(valor_perdido), 0)
        FROM perdas
        WHERE strftime('%Y', data) = ?
        GROUP BY tipo
        ORDER BY SUM(valor_perdido) DESC
    ''', (ano_atual,))
    dados_tipo = cursor.fetchall()
    
    cursor.execute('''
        SELECT COUNT(*), COALESCE(SUM(valor_perdido), 0)
        FROM perdas
        WHERE strftime('%Y', data) = ?
    ''', (ano_atual,))
    total_anual = cursor.fetchone()
    
    conn.close()
    
    card_total = Frame(janela, bg=COR_CARD, highlightthickness=2, highlightbackground=COR_PERIGO)
    card_total.pack(fill=X, padx=20, pady=15)
    
    Label(card_total, text=f"Total Anual {ano_atual}", font=("Arial", 14, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(pady=(15, 5))
    
    Label(card_total, text=formatar_kz(total_anual[1] or 0),
          font=("Arial", 28, "bold"), bg=COR_CARD, fg=COR_PERIGO).pack()
    
    Label(card_total, text=f"{total_anual[0]} registos no total",
          font=("Arial", 10, "italic"), bg=COR_CARD, fg="#6b7280").pack(pady=(5, 15))
    
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        frame_graf = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#cbd5e1")
        frame_graf.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        Label(frame_graf, text="Perdas por Mes", font=("Arial", 12, "bold"),
              bg=COR_CARD, fg=COR_TEXTO).pack(pady=10)
        
        fig = Figure(figsize=(10, 4), dpi=80, facecolor=COR_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(COR_CARD)
        
        meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                        "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        
        valores_mes = [0] * 12
        for m, n, val in dados_mes:
            idx = int(m) - 1
            valores_mes[idx] = val or 0
        
        bars = ax.bar(meses_nomes, valores_mes, color=COR_PERIGO, edgecolor="#7f1d1d")
        ax.set_title("Valor Perdido por Mes (Kz)", fontsize=11, fontweight="bold")
        ax.set_ylabel("Kz", fontsize=9)
        ax.tick_params(axis='x', labelsize=9)
        ax.tick_params(axis='y', labelsize=8)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        for bar, val in zip(bars, valores_mes):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                        f'{val:,.0f}', ha='center', va='bottom', fontsize=7)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame_graf)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=10, pady=10)
    except Exception as e:
        Label(janela, text=f"Erro ao gerar grafico: {e}",
              bg=COR_FUNDO, fg=COR_PERIGO).pack(pady=20)
    
    Label(janela, text="Detalhe por Tipo:", font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))
    
    frame_tipo = Frame(janela, bg=COR_FUNDO)
    frame_tipo.pack(fill=X, padx=20, pady=(0, 15))
    
    for tipo, n, valor in dados_tipo:
        frame_t = Frame(frame_tipo, bg=COR_CARD, highlightthickness=1, highlightbackground="#fecaca")
        frame_t.pack(fill=X, pady=2)
        Label(frame_t, text=tipo, font=("Arial", 11, "bold"),
              bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=15, pady=8)
        Label(frame_t, text=f"{n} registos", font=("Arial", 10),
              bg=COR_CARD, fg="#6b7280").pack(side=LEFT, padx=15)
        Label(frame_t, text=formatar_kz(valor), font=("Arial", 11, "bold"),
              bg=COR_CARD, fg=COR_PERIGO).pack(side=RIGHT, padx=15, pady=8)