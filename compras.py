from tkinter import *
from tkinter import messagebox, ttk
from database import (listar_fornecedores, listar_produtos_completos, criar_compra,
                       adicionar_item_compra, listar_compras, listar_itens_compra,
                       registar_auditoria)
from moeda import formatar_kz
from datetime import datetime

COR_FUNDO = "#ecfdf5"
COR_PRIMARIA = "#059669"
COR_TEXTO = "#064e3b"
COR_PERIGO = "#dc2626"
COR_HEADER = "#047857"
COR_CARD = "#ffffff"


def abrir_compras(utilizador_logado):
    janela = Toplevel()
    janela.title("JAM Soft - Entrada de Compras")
    janela.geometry("1000x800")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Entrada de Compras", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)
    
    carrinho = []
    total_var = StringVar(value="TOTAL: Kz 0,00")
    
    card_dados = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#a7f3d0")
    card_dados.pack(fill=X, padx=15, pady=(15, 5))
    
    frame_dados = Frame(card_dados, bg=COR_CARD)
    frame_dados.pack(padx=15, pady=12, fill=X)
    
    Label(frame_dados, text="Fornecedor: *", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=0, sticky=W, padx=(0, 5))
    
    fornecedor_var = StringVar()
    combo_forn = ttk.Combobox(frame_dados, textvariable=fornecedor_var, state="readonly",
                                font=("Arial", 10), width=35)
    combo_forn.grid(row=0, column=1, padx=(0, 20))
    
    fornecedores = listar_fornecedores()
    lista_forn = [f"{f[0]} - {f[1]}" for f in fornecedores]
    combo_forn["values"] = lista_forn
    if lista_forn:
        combo_forn.current(0)
    
    Label(frame_dados, text="N Fatura: *", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=2, sticky=W, padx=(0, 5))
    entry_fatura = Entry(frame_dados, font=("Arial", 11), width=20, bd=1, relief=SOLID)
    entry_fatura.grid(row=0, column=3)
    
    Label(janela, text="Adicionar Produto a Compra", font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))
    
    card_item = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#a7f3d0")
    card_item.pack(fill=X, padx=15, pady=5)
    
    frame_item = Frame(card_item, bg=COR_CARD)
    frame_item.pack(padx=15, pady=12, fill=X)
    
    Label(frame_item, text="Produto: *", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=0, sticky=W, padx=(0, 5))
    
    produto_var = StringVar()
    combo_prod = ttk.Combobox(frame_item, textvariable=produto_var, state="readonly",
                                font=("Arial", 10), width=40)
    combo_prod.grid(row=0, column=1, padx=(0, 20))
    
    produtos = listar_produtos_completos()
    lista_prod = [f"{p[0]} - {p[1]} (Est: {p[5]})" for p in produtos]
    combo_prod["values"] = lista_prod
    if lista_prod:
        combo_prod.current(0)
    
    Label(frame_item, text="Qtd: *", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=2, sticky=W, padx=(0, 5))
    entry_qtd = Entry(frame_item, font=("Arial", 11), width=8, bd=1, relief=SOLID)
    entry_qtd.grid(row=0, column=3, padx=(0, 20))
    
    Label(frame_item, text="Preco Custo (Kz): *", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=1, column=0, sticky=W, padx=(0, 5), pady=(10, 0))
    entry_custo = Entry(frame_item, font=("Arial", 11), width=15, bd=1, relief=SOLID)
    entry_custo.grid(row=1, column=1, sticky=W, padx=(0, 20), pady=(10, 0))
    
    Label(frame_item, text="Lote: *", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=1, column=2, sticky=W, padx=(0, 5), pady=(10, 0))
    entry_lote = Entry(frame_item, font=("Arial", 11), width=10, bd=1, relief=SOLID)
    entry_lote.grid(row=1, column=3, sticky=W, padx=(0, 20), pady=(10, 0))
    
    Label(frame_item, text="Validade (AAAA-MM-DD): *", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=2, column=0, sticky=W, padx=(0, 5), pady=(10, 0))
    entry_validade = Entry(frame_item, font=("Arial", 11), width=15, bd=1, relief=SOLID)
    entry_validade.grid(row=2, column=1, sticky=W, padx=(0, 20), pady=(10, 0))
    entry_validade.insert(0, datetime.now().strftime("%Y-%m-%d"))
    
    Label(janela, text="Itens da Compra", font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))
    
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=15, pady=5)
    
    colunas = ("Produto", "Qtd", "Custo Unit.", "Lote", "Validade", "Subtotal")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=8)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(fill=BOTH, expand=True)
    
    total_frame = Frame(janela, bg=COR_CARD, highlightthickness=2, highlightbackground=COR_PRIMARIA)
    total_frame.pack(pady=10, padx=15, fill=X)
    Label(total_frame, textvariable=total_var, font=("Arial", 18, "bold"),
          bg=COR_CARD, fg=COR_PRIMARIA).pack(pady=12)
    
    def atualizar_total():
        t = sum(item["subtotal"] for item in carrinho)
        total_var.set(f"TOTAL: {formatar_kz(t)}")
    
    def atualizar_tabela():
        for i in tree.get_children():
            tree.delete(i)
        for item in carrinho:
            tree.insert("", END, values=(item["nome"], item["qtd"],
                                          formatar_kz(item["custo"]),
                                          item["lote"], item["validade"],
                                          formatar_kz(item["subtotal"])))
        atualizar_total()
    
    def adicionar_item():
        if not combo_prod.get():
            messagebox.showwarning("Aviso", "Selecione um produto.")
            return
        
        try:
            pid = int(combo_prod.get().split(" - ")[0])
            p = [x for x in produtos if x[0] == pid][0]
            nome = p[1]
            
            qtd = int(entry_qtd.get().strip())
            if qtd <= 0:
                raise ValueError("Quantidade positiva")
            
            custo = float(entry_custo.get().replace(".", "").replace(",", ".").strip())
            lote = entry_lote.get().strip()
            validade = entry_validade.get().strip()
            
            if not lote or not validade:
                messagebox.showwarning("Aviso", "Preencha lote e validade.")
                return
            
            subtotal = qtd * custo
            
            encontrado = False
            for item in carrinho:
                if item["pid"] == pid and item["lote"] == lote and item["validade"] == validade:
                    item["qtd"] += qtd
                    item["subtotal"] = item["qtd"] * item["custo"]
                    encontrado = True
                    break
            
            if not encontrado:
                carrinho.append({
                    "pid": pid, "nome": nome, "qtd": qtd, "custo": custo,
                    "lote": lote, "validade": validade, "subtotal": subtotal
                })
            
            atualizar_tabela()
            
            entry_qtd.delete(0, END)
            entry_custo.delete(0, END)
            entry_lote.delete(0, END)
            entry_validade.delete(0, END)
            entry_validade.insert(0, datetime.now().strftime("%Y-%m-%d"))
            
        except (ValueError, IndexError) as e:
            messagebox.showerror("Erro", f"Verifique os dados: {e}")
    
    def remover_item():
        sel = tree.selection()
        if not sel:
            return
        idx = tree.index(sel[0])
        carrinho.pop(idx)
        atualizar_tabela()
    
    def finalizar_compra():
        if not carrinho:
            messagebox.showwarning("Aviso", "Adicione pelo menos um produto.")
            return
        
        if not combo_forn.get():
            messagebox.showwarning("Aviso", "Selecione um fornecedor.")
            return
        
        fatura = entry_fatura.get().strip()
        if not fatura:
            messagebox.showwarning("Aviso", "Digite o numero da fatura.")
            return
        
        try:
            fornecedor_id = int(combo_forn.get().split(" - ")[0])
            total = sum(item["subtotal"] for item in carrinho)
            
            compra_id = criar_compra(fornecedor_id, fatura, total, "", utilizador_logado["id"])
            
            for item in carrinho:
                adicionar_item_compra(compra_id, item["pid"], item["qtd"], item["custo"],
                                       item["lote"], item["validade"])
            
            registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                "NOVA COMPRA", f"Compra #{compra_id} | Fat: {fatura} | Total: {formatar_kz(total)}")
            
            messagebox.showinfo("Compra Registada",
                                f"Compra #{compra_id} registada!\n"
                                f"Fatura: {fatura}\n"
                                f"Total: {formatar_kz(total)}\n\n"
                                f"Estoque atualizado automaticamente.")
            janela.destroy()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao registar compra: {e}")
    
    frame_botoes = Frame(janela, bg=COR_FUNDO)
    frame_botoes.pack(pady=10)
    
    Button(frame_botoes, text="Remover Item", font=("Arial", 11, "bold"),
           bg=COR_PERIGO, fg="white", width=18, height=2, bd=0, cursor="hand2",
           command=remover_item).grid(row=0, column=0, padx=5)
    
    Button(frame_botoes, text="Finalizar Compra", font=("Arial", 12, "bold"),
           bg=COR_PRIMARIA, fg="white", width=22, height=2, bd=0, cursor="hand2",
           command=finalizar_compra).grid(row=0, column=1, padx=5)
    
    Button(frame_botoes, text="Historico", font=("Arial", 11, "bold"),
           bg="#0891b2", fg="white", width=18, height=2, bd=0, cursor="hand2",
           command=lambda: abrir_historico_compras()).grid(row=0, column=2, padx=5)
    
    Button(frame_item, text="Adicionar ao Carrinho", font=("Arial", 10, "bold"),
           bg=COR_PRIMARIA, fg="white", bd=0, cursor="hand2", width=22,
           command=adicionar_item).grid(row=2, column=2, columnspan=2, pady=(10, 0))


def abrir_historico_compras():
    janela = Toplevel()
    janela.title("Historico de Compras")
    janela.geometry("1000x650")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Historico de Compras", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)
    
    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(fill=BOTH, expand=True, padx=15, pady=15)
    
    colunas = ("ID", "Data", "Fornecedor", "N Fatura", "Total")
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=12)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=180)
    tree.pack(fill=BOTH, expand=True)
    
    frame_itens = Frame(janela, bg=COR_FUNDO)
    frame_itens.pack(fill=BOTH, expand=True, padx=15, pady=(0, 15))
    
    Label(frame_itens, text="Itens da compra selecionada:",
          font=("Arial", 11, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(0, 5))
    
    colunas2 = ("Produto", "Qtd", "Custo", "Lote", "Validade", "Subtotal")
    tree2 = ttk.Treeview(frame_itens, columns=colunas2, show="headings", height=8)
    for col in colunas2:
        tree2.heading(col, text=col)
        tree2.column(col, width=150)
    tree2.pack(fill=BOTH, expand=True)
    
    def carregar_compras():
        for i in tree.get_children():
            tree.delete(i)
        for c in listar_compras(100):
            tree.insert("", END, values=(c[0], c[1], c[2] or "-", c[3] or "-", formatar_kz(c[4])))
    
    def mostrar_itens(event=None):
        sel = tree.selection()
        if not sel:
            return
        compra_id = tree.item(sel[0])["values"][0]
        
        for i in tree2.get_children():
            tree2.delete(i)
        
        for item in listar_itens_compra(compra_id):
            tree2.insert("", END, values=(item[1], item[2], formatar_kz(item[3]),
                                            item[4], item[5], formatar_kz(item[6])))
    
    tree.bind("<<TreeviewSelect>>", mostrar_itens)
    carregar_compras()