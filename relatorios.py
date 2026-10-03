from tkinter import *
from tkinter import messagebox, ttk
from database import (relatorio_vendas_periodo, resumo_vendas_periodo,
                       produtos_mais_vendidos, vendas_por_forma_pagamento,
                       vendas_por_utilizador, margem_produtos,
                       resumo_facturacao_periodo, inventario_valorizado)
from moeda import formatar_kz
from datetime import datetime, timedelta

COR_FUNDO = "#eff6ff"
COR_PRIMARIA = "#2563eb"
COR_TEXTO = "#1e3a8a"
COR_PERIGO = "#dc2626"
COR_HEADER = "#1e40af"
COR_CARD = "#ffffff"
COR_VERDE = "#16a34a"


def abrir_relatorios(utilizador_logado):
    janela = Toplevel()
    janela.title("JAM Soft - Relatorios")
    janela.geometry("900x750")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Relatorios e Estatisticas", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)
    
    Label(janela, text="Escolhe o relatorio que queres ver:",
          font=("Arial", 12, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(25, 15))
    
    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(pady=10)
    
    estilo = {"font": ("Arial", 11, "bold"), "width": 28, "height": 3,
              "bd": 0, "cursor": "hand2", "fg": "white"}
    
    botoes = [
        ("Vendas por Periodo", COR_PRIMARIA, rel_vendas_periodo, 0, 0),
        ("Produtos Mais Vendidos", COR_VERDE, rel_produtos_vendidos, 0, 1),
        ("Vendas por Pagamento", "#0891b2", rel_forma_pagamento, 1, 0),
        ("Vendas por Operador", "#7c3aed", rel_por_utilizador, 1, 1),
        ("Margem de Lucro", "#ea580c", rel_margem, 2, 0),
        ("Resumo Fiscal", "#b45309", rel_fiscal, 2, 1),
        ("Inventario Valorizado", "#059669", rel_inventario, 3, 0),
        ("Resumo do Dia", "#be185d", rel_resumo_dia, 3, 1),
    ]
    
    for texto, cor, cmd, linha, coluna in botoes:
        Button(frame, text=texto, bg=cor, command=cmd, **estilo).grid(
            row=linha, column=coluna, padx=6, pady=6)


def abrir_janela_relatorio(titulo):
    janela = Toplevel()
    janela.title(f"JAM Soft - {titulo}")
    janela.geometry("1000x600")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_HEADER, height=60)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text=titulo, font=("Arial", 16, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=15)
    
    return janela


def frame_periodo(parent, callback):
    frame = Frame(parent, bg=COR_CARD, highlightthickness=1, highlightbackground="#bfdbfe")
    frame.pack(fill=X, padx=15, pady=10)
    
    Label(frame, text="De (AAAA-MM-DD):", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=10, pady=10)
    
    hoje = datetime.now().date()
    e_ini = Entry(frame, font=("Arial", 11), width=12, bd=1, relief=SOLID)
    e_ini.insert(0, (hoje - timedelta(days=30)).strftime("%Y-%m-%d"))
    e_ini.pack(side=LEFT, padx=5, pady=10, ipady=4)
    
    Label(frame, text="Ate:", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=10, pady=10)
    
    e_fim = Entry(frame, font=("Arial", 11), width=12, bd=1, relief=SOLID)
    e_fim.insert(0, hoje.strftime("%Y-%m-%d"))
    e_fim.pack(side=LEFT, padx=5, pady=10, ipady=4)
    
    def aplicar():
        d1 = e_ini.get().strip()
        d2 = e_fim.get().strip()
        try:
            datetime.strptime(d1, "%Y-%m-%d")
            datetime.strptime(d2, "%Y-%m-%d")
            callback(d1, d2)
        except ValueError:
            messagebox.showerror("Erro", "Formato de data invalido. Use AAAA-MM-DD.")
    
    e_ini.bind('<Return>', lambda e: e_fim.focus())
    e_fim.bind('<Return>', lambda e: aplicar())
    
    Button(frame, text="Aplicar", font=("Arial", 10, "bold"),
           bg=COR_PRIMARIA, fg="white", bd=0, cursor="hand2", padx=15, pady=5,
           command=aplicar).pack(side=LEFT, padx=15, pady=10)


def criar_tree(parent, colunas, widths=None):
    frame = Frame(parent, bg=COR_FUNDO)
    frame.pack(fill=BOTH, expand=True, padx=15, pady=10)
    
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=18)
    for i, col in enumerate(colunas):
        tree.heading(col, text=col)
        w = widths[i] if widths else 140
        tree.column(col, width=w)
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    return tree


def rel_vendas_periodo():
    janela = abrir_janela_relatorio("Vendas por Periodo")
    
    resumo_var = StringVar(value="")
    Label(janela, textvariable=resumo_var, font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_PRIMARIA).pack(pady=5)
    
    colunas = ("Data", "Total", "Forma", "Operador")
    tree = criar_tree(janela, colunas, [180, 150, 150, 200])
    
    def atualizar(d1, d2):
        for i in tree.get_children():
            tree.delete(i)
        n, total, media = resumo_vendas_periodo(d1, d2)
        resumo_var.set(f"Vendas: {n}  |  Total: {formatar_kz(total)}  |  Ticket medio: {formatar_kz(media)}")
        for v in relatorio_vendas_periodo(d1, d2):
            data, tot, forma, user = v
            tree.insert("", END, values=(data, formatar_kz(tot), forma or "-", user or "-"))
    
    frame_periodo(janela, atualizar)


def rel_produtos_vendidos():
    janela = abrir_janela_relatorio("Produtos Mais Vendidos")
    
    colunas = ("#", "Produto", "Codigo", "Qtd Vendida", "Receita")
    tree = criar_tree(janela, colunas, [50, 300, 120, 120, 150])
    
    def atualizar(d1, d2):
        for i in tree.get_children():
            tree.delete(i)
        prods = produtos_mais_vendidos(d1, d2, 50)
        for i, p in enumerate(prods, 1):
            nome, codigo, qtd, receita = p
            tree.insert("", END, values=(i, nome, codigo or "-", qtd, formatar_kz(receita)))
    
    frame_periodo(janela, atualizar)


def rel_forma_pagamento():
    janela = abrir_janela_relatorio("Vendas por Forma de Pagamento")
    
    colunas = ("Forma de Pagamento", "N Vendas", "Total")
    tree = criar_tree(janela, colunas, [300, 150, 200])
    
    def atualizar(d1, d2):
        for i in tree.get_children():
            tree.delete(i)
        for f in vendas_por_forma_pagamento(d1, d2):
            forma, n, total = f
            tree.insert("", END, values=(forma or "-", n, formatar_kz(total)))
    
    frame_periodo(janela, atualizar)


def rel_por_utilizador():
    janela = abrir_janela_relatorio("Vendas por Operador")
    
    colunas = ("Operador", "N Vendas", "Total")
    tree = criar_tree(janela, colunas, [300, 150, 200])
    
    def atualizar(d1, d2):
        for i in tree.get_children():
            tree.delete(i)
        for u in vendas_por_utilizador(d1, d2):
            nome, n, total = u
            tree.insert("", END, values=(nome or "Desconhecido", n, formatar_kz(total)))
    
    frame_periodo(janela, atualizar)


def rel_margem():
    janela = abrir_janela_relatorio("Margem de Lucro por Produto")
    
    colunas = ("Produto", "Qtd", "Receita", "Custo", "Lucro", "Margem %")
    tree = criar_tree(janela, colunas, [280, 70, 130, 130, 130, 90])
    
    def atualizar(d1, d2):
        for i in tree.get_children():
            tree.delete(i)
        for m in margem_produtos(d1, d2):
            nome, pc, pv, qtd, receita, custo, lucro = m
            margem = (lucro / receita * 100) if receita else 0
            tree.insert("", END, values=(nome, qtd, formatar_kz(receita),
                                          formatar_kz(custo), formatar_kz(lucro),
                                          f"{margem:.1f}%"))
    
    frame_periodo(janela, atualizar)


def rel_fiscal():
    janela = abrir_janela_relatorio("Resumo Fiscal")
    
    resumo_var = StringVar(value="")
    Label(janela, textvariable=resumo_var, font=("Arial", 13, "bold"),
          bg=COR_FUNDO, fg=COR_PRIMARIA).pack(pady=15)
    
    def atualizar(d1, d2):
        n, sub, iva, total = resumo_facturacao_periodo(d1, d2)
        resumo_var.set(
            f"Facturas: {n}   |   "
            f"Subtotal: {formatar_kz(sub)}   |   "
            f"IVA: {formatar_kz(iva)}   |   "
            f"TOTAL: {formatar_kz(total)}"
        )
    
    frame_periodo(janela, atualizar)


def rel_inventario():
    janela = abrir_janela_relatorio("Inventario Valorizado")
    
    Label(janela, text="Valor total do estoque atual:",
          font=("Arial", 12, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=20)
    
    frame = Frame(janela, bg=COR_CARD, highlightthickness=2, highlightbackground=COR_PRIMARIA)
    frame.pack(padx=40, pady=20, fill=X)
    
    dados = inventario_valorizado()
    valor_custo, valor_venda, n_produtos, total_uni = dados
    
    linhas = [
        ("Numero de Produtos:", str(n_produtos)),
        ("Total de Unidades em Stock:", str(total_uni)),
        ("Valor de Custo (investimento):", formatar_kz(valor_custo)),
        ("Valor de Venda (potencial):", formatar_kz(valor_venda)),
        ("Lucro Potencial:", formatar_kz(valor_venda - valor_custo)),
    ]
    
    for i, (label, valor) in enumerate(linhas):
        Label(frame, text=label, font=("Arial", 11, "bold"),
              bg=COR_CARD, fg=COR_TEXTO).grid(row=i, column=0, sticky=W, padx=20, pady=8)
        Label(frame, text=valor, font=("Arial", 12, "bold"),
              bg=COR_CARD, fg=COR_PRIMARIA).grid(row=i, column=1, sticky=E, padx=20, pady=8)


def rel_resumo_dia():
    janela = abrir_janela_relatorio("Resumo do Dia")
    
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    Label(janela, text=f"Data: {hoje}", font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=15)
    
    n, total, media = resumo_vendas_periodo(hoje, hoje)
    
    frame = Frame(janela, bg=COR_CARD, highlightthickness=2, highlightbackground=COR_PRIMARIA)
    frame.pack(padx=40, pady=15, fill=X)
    
    linhas = [
        ("Numero de Vendas:", str(n)),
        ("Total Facturado:", formatar_kz(total)),
        ("Ticket Medio:", formatar_kz(media)),
    ]
    
    for i, (label, valor) in enumerate(linhas):
        Label(frame, text=label, font=("Arial", 11, "bold"),
              bg=COR_CARD, fg=COR_TEXTO).grid(row=i, column=0, sticky=W, padx=20, pady=8)
        Label(frame, text=valor, font=("Arial", 12, "bold"),
              bg=COR_CARD, fg=COR_PRIMARIA).grid(row=i, column=1, sticky=E, padx=20, pady=8)
    
    Label(janela, text="Top 5 Produtos do Dia:",
          font=("Arial", 12, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(20, 5))
    
    colunas = ("Produto", "Qtd", "Receita")
    tree = criar_tree(janela, colunas, [300, 100, 150])
    
    for p in produtos_mais_vendidos(hoje, hoje, 5):
        nome, codigo, qtd, receita = p
        tree.insert("", END, values=(nome, qtd, formatar_kz(receita)))