from tkinter import *
from tkinter import messagebox, ttk
from database import (listar_produtos, listar_fornecedores, listar_categorias,
                       buscar_produto_por_id, inserir_produto_completo,
                       ajustar_estoque, registar_auditoria, conectar)
from moeda import formatar_kz

COR_FUNDO = "#eef2ff"
COR_PRIMARIA = "#4f46e5"
COR_TEXTO = "#1e1b4b"
COR_PERIGO = "#dc2626"
COR_HEADER = "#3730a3"
COR_CARD = "#ffffff"
COR_VERDE = "#16a34a"


def abrir_produtos(utilizador_logado):
    janela = Toplevel()
    janela.title("JAM Soft - Gestao de Produtos")
    janela.geometry("1200x700")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Gestao de Produtos", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)
    
    frame_busca = Frame(janela, bg=COR_FUNDO)
    frame_busca.pack(fill=X, padx=15, pady=(15, 5))
    
    Label(frame_busca, text="Buscar:", font=("Arial", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(side=LEFT, padx=5)
    
    entry_busca = Entry(frame_busca, font=("Arial", 11), width=40, bd=1, relief=SOLID)
    entry_busca.pack(side=LEFT, padx=5, ipady=5)
    
    Label(frame_busca, text="(por nome ou codigo)", font=("Arial", 9, "italic"),
          bg=COR_FUNDO, fg="#6b7280").pack(side=LEFT, padx=5)
    
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=15, pady=10)
    
    colunas = ("ID", "Nome", "Codigo", "Preco Venda", "Estoque", "Minimo", "IVA", "Status")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=20)
    for col in colunas:
        tree.heading(col, text=col)
    tree.column("ID", width=50)
    tree.column("Nome", width=280)
    tree.column("Codigo", width=120)
    tree.column("Preco Venda", width=120)
    tree.column("Estoque", width=80)
    tree.column("Minimo", width=80)
    tree.column("IVA", width=80)
    tree.column("Status", width=100)
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    def carregar(busca=""):
        for i in tree.get_children():
            tree.delete(i)
        for p in listar_produtos():
            pid, nome, codigo, preco, estoque, minimo, isento = p
            if busca:
                busca_lower = busca.lower()
                if busca_lower not in nome.lower() and busca_lower not in (codigo or "").lower():
                    continue
            
            status = "BAIXO" if estoque <= minimo else "OK"
            iva_txt = "Isento" if isento else "14%"
            
            tag = ""
            if estoque == 0:
                tag = "zerado"
            elif estoque <= minimo:
                tag = "baixo"
            
            tree.insert("", END, values=(pid, nome, codigo or "-", formatar_kz(preco),
                                          estoque, minimo, iva_txt, status), tags=(tag,))
        
        tree.tag_configure("baixo", background="#fef3c7", foreground="#78350f")
        tree.tag_configure("zerado", background="#fee2e2", foreground="#991b1b")
    
    entry_busca.bind('<KeyRelease>', lambda e: carregar(entry_busca.get()))
    carregar()
    
    def obter_selecionado():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um produto na lista.")
            return None
        return tree.item(sel[0])["values"][0]
    
    def editar():
        pid = obter_selecionado()
        if pid:
            abrir_form_edicao(pid, utilizador_logado, carregar)
    
    def ajustar():
        pid = obter_selecionado()
        if pid:
            abrir_ajuste_estoque(pid, utilizador_logado, carregar)
    
    def eliminar():
        pid = obter_selecionado()
        if not pid:
            return
        
        valores = tree.item(tree.selection()[0])["values"]
        nome = valores[1]
        
        if not messagebox.askyesno("Confirmar", 
            f"Eliminar '{nome}' permanentemente?\n\n"
            "AVISO: Esta accao nao pode ser revertida."):
            return
        
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM produtos WHERE id = ?", (pid,))
            conn.commit()
            conn.close()
            
            registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                "ELIMINAR PRODUTO", f"Removeu '{nome}' (ID {pid})")
            messagebox.showinfo("Sucesso", "Produto eliminado.")
            carregar()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}\n\n(O produto pode ter vendas associadas)")
    
    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=10)
    
    estilo = {"font": ("Arial", 11, "bold"), "width": 20, "height": 2,
              "bd": 0, "cursor": "hand2", "fg": "white"}
    
    Button(frame_btn, text="Editar Produto", bg="#0891b2",
           command=editar, **estilo).grid(row=0, column=0, padx=5, pady=5)
    Button(frame_btn, text="Ajustar Estoque", bg=COR_VERDE,
           command=ajustar, **estilo).grid(row=0, column=1, padx=5, pady=5)
    Button(frame_btn, text="Eliminar", bg=COR_PERIGO,
           command=eliminar, **estilo).grid(row=0, column=2, padx=5, pady=5)
    Button(frame_btn, text="Actualizar", bg="#4b5563",
           command=carregar, **estilo).grid(row=0, column=3, padx=5, pady=5)


def abrir_form_edicao(produto_id, utilizador_logado, callback_atualizar=None):
    p = buscar_produto_por_id(produto_id)
    if not p:
        messagebox.showerror("Erro", "Produto nao encontrado.")
        return
    
    pid, nome, codigo, preco_custo, preco_venda, estoque = p
    
    janela = Toplevel()
    janela.title(f"Editar Produto: {nome}")
    janela.geometry("600x750")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_HEADER, height=60)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text=f"Editar: {nome}", font=("Arial", 16, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=15)
    
    card = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#c7d2fe")
    card.pack(padx=20, pady=15, fill=X)
    
    frame = Frame(card, bg=COR_CARD)
    frame.pack(padx=20, pady=15, fill=X)
    
    Label(frame, text="Nome do Produto: *", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
    entry_nome = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
    entry_nome.insert(0, nome)
    entry_nome.pack(fill=X, ipady=6)
    
    Label(frame, text="Codigo de Barras:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
    entry_codigo = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
    entry_codigo.insert(0, codigo or "")
    entry_codigo.pack(fill=X, ipady=6)
    
    Label(frame, text="Preco de Custo (Kz):", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
    entry_custo = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
    entry_custo.insert(0, str(preco_custo or 0))
    entry_custo.pack(fill=X, ipady=6)
    
    Label(frame, text="Preco de Venda (Kz): *", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
    entry_venda = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
    entry_venda.insert(0, str(preco_venda or 0))
    entry_venda.pack(fill=X, ipady=6)
    
    Label(frame, text="Estoque Atual:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
    Label(frame, text="(Para alterar, use 'Ajustar Estoque')",
          font=("Arial", 9, "italic"), bg=COR_CARD, fg="#6b7280").pack(anchor=W)
    entry_estoque = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID, state="readonly")
    entry_estoque.insert(0, str(estoque))
    entry_estoque.pack(fill=X, ipady=6)
    
    def salvar():
        novo_nome = entry_nome.get().strip()
        novo_codigo = entry_codigo.get().strip()
        
        if not novo_nome:
            messagebox.showwarning("Aviso", "O nome e obrigatorio.")
            return
        
        try:
            custo = float(entry_custo.get().replace(".", "").replace(",", ".") or 0)
            venda = float(entry_venda.get().replace(".", "").replace(",", ".") or 0)
        except ValueError:
            messagebox.showerror("Erro", "Precos invalidos.")
            return
        
        try:
            conn = conectar()
            cursor = conn.cursor()
            
            if novo_codigo:
                cursor.execute("SELECT id FROM produtos WHERE codigo_barras = ? AND id != ?",
                               (novo_codigo, produto_id))
                if cursor.fetchone():
                    messagebox.showerror("Erro", "Este codigo de barras ja existe noutro produto.")
                    conn.close()
                    return
            
            cursor.execute('''
                UPDATE produtos SET nome = ?, codigo_barras = ?, preco_custo = ?, preco_venda = ?
                WHERE id = ?
            ''', (novo_nome, novo_codigo or None, custo, venda, produto_id))
            conn.commit()
            conn.close()
            
            registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                "EDITAR PRODUTO", f"Editou '{novo_nome}' (ID {produto_id})")
            
            messagebox.showinfo("Sucesso", "Produto atualizado!")
            if callback_atualizar:
                callback_atualizar()
            janela.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")
    
    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=15)
    
    Button(frame_btn, text="Guardar Alteracoes", font=("Arial", 12, "bold"),
           bg=COR_PRIMARIA, fg="white", width=22, height=2, bd=0, cursor="hand2",
           command=salvar).grid(row=0, column=0, padx=5)
    
    Button(frame_btn, text="Cancelar", font=("Arial", 12, "bold"),
           bg="#6b7280", fg="white", width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).grid(row=0, column=1, padx=5)


def abrir_ajuste_estoque(produto_id, utilizador_logado, callback_atualizar=None):
    p = buscar_produto_por_id(produto_id)
    if not p:
        messagebox.showerror("Erro", "Produto nao encontrado.")
        return
    
    pid, nome, codigo, preco_custo, preco_venda, estoque_atual = p
    
    janela = Toplevel()
    janela.title(f"Ajustar Estoque: {nome}")
    janela.geometry("550x550")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_VERDE, height=60)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Ajustar Estoque Manualmente", font=("Arial", 16, "bold"),
          bg=COR_VERDE, fg="white").pack(pady=15)
    
    info = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#86efac")
    info.pack(fill=X, padx=20, pady=15)
    
    Label(info, text=nome, font=("Arial", 14, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(pady=(15, 5))
    Label(info, text=f"Codigo: {codigo or '-'}",
          font=("Arial", 10), bg=COR_CARD, fg=COR_TEXTO).pack()
    Label(info, text=f"Estoque Atual: {estoque_atual} unidades",
          font=("Arial", 12, "bold"), bg=COR_CARD, fg=COR_VERDE).pack(pady=(5, 15))
    
    Label(janela, text="Tipo de Ajuste:", font=("Arial", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))
    
    tipo_var = StringVar(value="ENTRADA")
    
    frame_tipo = Frame(janela, bg=COR_FUNDO)
    frame_tipo.pack(pady=5)
    
    Radiobutton(frame_tipo, text="Entrada (adicionar)", variable=tipo_var,
                value="ENTRADA", bg=COR_FUNDO, fg=COR_TEXTO,
                font=("Arial", 11), selectcolor=COR_FUNDO).pack(side=LEFT, padx=15)
    Radiobutton(frame_tipo, text="Saida (remover)", variable=tipo_var,
                value="SAIDA", bg=COR_FUNDO, fg=COR_TEXTO,
                font=("Arial", 11), selectcolor=COR_FUNDO).pack(side=LEFT, padx=15)
    
    Label(janela, text="Quantidade:", font=("Arial", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))
    entry_qtd = Entry(janela, font=("Arial", 14), width=15, justify=CENTER, bd=1, relief=SOLID)
    entry_qtd.pack(pady=5, ipady=6)
    entry_qtd.focus()
    
    Label(janela, text="Justificacao (obrigatoria):", font=("Arial", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))
    entry_just = Entry(janela, font=("Arial", 11), width=40, bd=1, relief=SOLID)
    entry_just.pack(pady=5, ipady=6)
    
    Label(janela, text="Ex: Ajuste de inventario, Quebra, Devolucao, Correcao de erro",
          font=("Arial", 9, "italic"), bg=COR_FUNDO, fg="#6b7280").pack()
    
    preview_var = StringVar(value=f"Estoque resultante: {estoque_atual}")
    Label(janela, textvariable=preview_var, font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_PRIMARIA).pack(pady=15)
    
    def atualizar_preview(event=None):
        try:
            qtd = int(entry_qtd.get() or 0)
            tipo = tipo_var.get()
            if tipo == "ENTRADA":
                novo = estoque_atual + qtd
            else:
                novo = estoque_atual - qtd
            
            if novo < 0:
                preview_var.set(f"ERRO: Estoque ficaria negativo ({novo})")
            else:
                preview_var.set(f"Estoque resultante: {novo} unidades")
        except ValueError:
            preview_var.set(f"Estoque resultante: {estoque_atual}")
    
    entry_qtd.bind('<KeyRelease>', atualizar_preview)
    
    def confirmar():
        try:
            qtd = int(entry_qtd.get().strip())
            if qtd <= 0:
                messagebox.showwarning("Aviso", "A quantidade deve ser positiva.")
                return
        except ValueError:
            messagebox.showerror("Erro", "Digite uma quantidade valida.")
            return
        
        just = entry_just.get().strip()
        if not just:
            messagebox.showwarning("Aviso", "A justificacao e obrigatoria.")
            return
        
        tipo = tipo_var.get()
        
        if tipo == "ENTRADA":
            novo_estoque = estoque_atual + qtd
            acao = "ENTRADA MANUAL"
        else:
            novo_estoque = estoque_atual - qtd
            acao = "SAIDA MANUAL"
            if novo_estoque < 0:
                messagebox.showerror("Erro", "Estoque ficaria negativo!")
                return
        
        if not messagebox.askyesno("Confirmar",
            f"Confirma o ajuste?\n\n"
            f"Tipo: {tipo}\n"
            f"Quantidade: {qtd}\n"
            f"Estoque: {estoque_atual} -> {novo_estoque}\n"
            f"Justificacao: {just}"):
            return
        
        ajustar_estoque(produto_id, novo_estoque)
        
        registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                            acao, f"'{nome}' | {estoque_atual} -> {novo_estoque} | {just}")
        
        messagebox.showinfo("Sucesso",
            f"Estoque ajustado!\n\n"
            f"Novo estoque: {novo_estoque} unidades")
        
        if callback_atualizar:
            callback_atualizar()
        janela.destroy()
    
    entry_just.bind('<Return>', lambda e: confirmar())
    
    Button(janela, text="Confirmar Ajuste", font=("Arial", 13, "bold"),
           bg=COR_VERDE, fg="white", width=25, height=2, bd=0, cursor="hand2",
           command=confirmar).pack(pady=20)