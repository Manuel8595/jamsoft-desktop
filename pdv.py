from datetime import datetime
from tkinter import *
from tkinter import messagebox, ttk
from database import (buscar_por_codigo, dar_baixa_estoque_fefo, registrar_venda,
                       registrar_item_venda, registar_auditoria, listar_clientes,
                       caixa_aberto, obter_empresa, proximo_numero_factura,
                       criar_factura, adicionar_item_factura, autenticar, conectar,
                       abrir_caixa, listar_facturas, dia_aberto)
from moeda import formatar_kz, IVA_ANGOLA
from seguranca import verificar_acesso

COR_FUNDO = "#f0fdf4"
COR_PRIMARIA = "#16a34a"
COR_TEXTO = "#14532d"
COR_PERIGO = "#dc2626"
COR_CARD = "#ffffff"
COR_IVA = "#ea580c"
COR_MISTO = "#f59e0b"
COR_DESCONTO = "#7c3aed"

LIMITE_DESCONTO = 10


def abrir_pdv(utilizador_logado=None):
    if not verificar_acesso(utilizador_logado, "pdv.abrir", "Modulo PDV"):
        return

    utilizador_id = utilizador_logado["id"] if utilizador_logado else None

    # ══════════════════════════════════════════════════════
    # VERIFICAR DIA ABERTO
    # ══════════════════════════════════════════════════════
    dia = dia_aberto()
    if not dia:
        messagebox.showerror("Dia Fechado",
            "O DIA DE OPERACAO NAO ESTA ABERTO.\n\n"
            "Peca ao gerente para abrir o dia primeiro\n"
            "(menu: DIA DE OPERACAO -> Abrir Dia).")
        return

    # ══════════════════════════════════════════════════════
    # VERIFICAR / ABRIR CAIXA
    # ══════════════════════════════════════════════════════
    cx = caixa_aberto()

    if cx is None:
        if not messagebox.askyesno("Abrir Caixa",
            "NAO HA CAIXA ABERTO\n\n"
            "Para vender, tem de declarar o fundo de troco\n"
            "que recebeu do gerente.\n\n"
            "Deseja abrir o caixa agora?"):
            return

        temp = Toplevel()
        temp.withdraw()

        resultado_caixa = {"ok": False}

        def _cb():
            resultado_caixa["ok"] = True
            temp.destroy()

        _janela_fundo_troco_pdv(utilizador_logado, temp, _cb)
        temp.wait_window()

        if not resultado_caixa["ok"]:
            return

        cx = caixa_aberto()
        if not cx:
            messagebox.showerror("Erro", "Caixa nao foi aberto.")
            return

    caixa_id = cx[0]
    fundo_inicial = cx[3] if len(cx) > 3 else 0

    janela = Toplevel()
    janela.title("JAM Soft - PDV")
    janela.geometry("900x920")
    janela.configure(bg=COR_FUNDO)
    
    carrinho = []
    subtotal_var = StringVar(value="Subtotal: Kz 0,00")
    desconto_var = StringVar(value="")
    iva_var = StringVar(value="IVA (14%): Kz 0,00")
    total_var = StringVar(value="TOTAL: Kz 0,00")
    total_itens_var = StringVar(value="0 itens")
    ultima_venda_var = StringVar(value="")
    
    Label(janela, text="PDV - Ponto de Venda", font=("Arial", 18, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(12, 5))
    
    hora_agora = datetime.now().strftime("%H:%M")
    
    Label(janela,
          text=f"Operador: {utilizador_logado['nome']}  |  Caixa #{caixa_id}  |  {hora_agora}  |  Fundo: {formatar_kz(fundo_inicial)}  |  Limite desconto: {LIMITE_DESCONTO}%",
          font=("Arial", 9, "italic"), bg=COR_FUNDO, fg="#6b7280").pack(pady=(0, 8))
    
    frame_cli = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#a7f3d0")
    frame_cli.pack(pady=5, padx=20, fill=X)
    
    Label(frame_cli, text="Cliente:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=15, pady=10)
    
    cliente_var = StringVar()
    clientes = listar_clientes()
    lista_cli = ["(Sem cliente)"] + [f"{c[0]} - {c[1]}" for c in clientes]
    combo_cli = ttk.Combobox(frame_cli, textvariable=cliente_var, state="readonly",
                                font=("Arial", 10), width=45)
    combo_cli["values"] = lista_cli
    combo_cli.current(0)
    combo_cli.pack(side=LEFT, padx=5, pady=10)
    
    frame_cod = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#d1fae5")
    frame_cod.pack(pady=8, padx=20, fill=X)
    
    Label(frame_cod, text="Codigo de Barras:", font=("Arial", 12, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=15, pady=12)
    
    entry_codigo = Entry(frame_cod, font=("Arial", 14), width=25, bd=1, relief=SOLID)
    entry_codigo.pack(side=LEFT, padx=5, pady=12)
    entry_codigo.focus()
    
    janela.bind('<F2>', lambda e: entry_codigo.focus())
    
    Label(frame_cod, text="(Enter ou leitor)", font=("Arial", 9, "italic"),
          bg=COR_CARD, fg="#6b7280").pack(side=LEFT, padx=5)
    
    preview_var = StringVar(value="")
    preview_lbl = Label(frame_cod, textvariable=preview_var,
                        font=("Arial", 10, "bold"),
                        bg=COR_CARD, fg=COR_PRIMARIA)
    preview_lbl.pack(side=LEFT, padx=10)
    
    def preview_produto(event=None):
        codigo = entry_codigo.get().strip()
        if not codigo:
            preview_var.set("")
            return
        
        try:
            produto = buscar_por_codigo(codigo)
            if produto:
                pid, nome, preco, estoque, isento = produto
                stock_txt = f"Stock: {estoque}"
                iva_txt = "Isento" if isento else "IVA 14%"
                preview_var.set(f"{nome}  |  {formatar_kz(preco)}  |  {stock_txt}  |  {iva_txt}")
                preview_lbl.config(fg=COR_PRIMARIA)
            else:
                preview_var.set("(codigo nao encontrado)")
                preview_lbl.config(fg=COR_PERIGO)
        except Exception:
            preview_var.set("")
    
    entry_codigo.bind('<KeyRelease>', preview_produto)
    
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=20, pady=8)
    
    colunas = ("Produto", "Qtd", "Preco", "Desc.", "Subtotal", "IVA")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=10)
    for col in colunas:
        tree.heading(col, text=col)
    tree.column("Produto", width=250)
    tree.column("Qtd", width=60)
    tree.column("Preco", width=110)
    tree.column("Desc.", width=80)
    tree.column("Subtotal", width=120)
    tree.column("IVA", width=70)
    tree.pack(fill=BOTH, expand=True)
    
    tree.tag_configure("par", background="#f8fafc")
    tree.tag_configure("impar", background="#ffffff")
    
    totais_frame = Frame(janela, bg=COR_CARD, highlightthickness=2, highlightbackground=COR_PRIMARIA)
    totais_frame.pack(pady=10, padx=20, fill=X)
    
    Label(totais_frame, textvariable=subtotal_var, font=("Arial", 12),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=E, padx=20, pady=(10, 2))
    Label(totais_frame, textvariable=desconto_var, font=("Arial", 12, "bold"),
          bg=COR_CARD, fg=COR_DESCONTO).pack(anchor=E, padx=20, pady=2)
    Label(totais_frame, textvariable=iva_var, font=("Arial", 12, "bold"),
          bg=COR_CARD, fg=COR_IVA).pack(anchor=E, padx=20, pady=2)
    Label(totais_frame, text="-" * 50, bg=COR_CARD, fg="#d1d5db").pack(pady=2)
    Label(totais_frame, textvariable=total_var, font=("Arial", 22, "bold"),
          bg=COR_CARD, fg=COR_PRIMARIA).pack(anchor=E, padx=20, pady=(2, 2))
    Label(totais_frame, textvariable=total_itens_var, font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=E, padx=20, pady=(2, 2))
    Label(totais_frame, textvariable=ultima_venda_var, font=("Arial", 9, "italic"),
          bg=COR_CARD, fg="#6b7280").pack(anchor=E, padx=20, pady=(0, 10))
    
    def calc_sub_original():
        return sum(item["preco"] * item["qtd"] for item in carrinho)
    
    def calc_sub_com_desc():
        total = 0
        for item in carrinho:
            sub = item["preco"] * item["qtd"]
            if item["desconto_percent"] > 0:
                sub -= sub * (item["desconto_percent"] / 100)
            total += sub
        return total
    
    def calc_desc():
        return calc_sub_original() - calc_sub_com_desc()
    
    def calc_iva():
        total_iva = 0
        for item in carrinho:
            sub = item["preco"] * item["qtd"]
            if item["desconto_percent"] > 0:
                sub -= sub * (item["desconto_percent"] / 100)
            if not item["isento"]:
                total_iva += sub * IVA_ANGOLA
        return total_iva
    
    def atualizar_totais():
        sub_o = calc_sub_original()
        desc = calc_desc()
        iva = calc_iva()
        total = calc_sub_com_desc() + iva
        num_itens = sum(i["qtd"] for i in carrinho)
        
        subtotal_var.set(f"Subtotal: {formatar_kz(sub_o)}")
        desconto_var.set(f"Desconto itens: -{formatar_kz(desc)}" if desc > 0 else "")
        iva_var.set(f"IVA (14%): {formatar_kz(iva)}")
        total_var.set(f"TOTAL: {formatar_kz(total)}")
        total_itens_var.set(f"{num_itens} iten{'s' if num_itens != 1 else ''}")
    
    def atualizar_tabela():
        for i in tree.get_children():
            tree.delete(i)
        for idx, item in enumerate(carrinho):
            sub = item["preco"] * item["qtd"]
            if item["desconto_percent"] > 0:
                sub -= sub * (item["desconto_percent"] / 100)
            iva_txt = "Isento" if item["isento"] else "14%"
            desc_txt = f"{item['desconto_percent']:.0f}%" if item["desconto_percent"] > 0 else "-"
            tag = "par" if idx % 2 == 0 else "impar"
            tree.insert("", END, values=(item["nome"], item["qtd"],
                                          formatar_kz(item["preco"]),
                                          desc_txt, formatar_kz(sub), iva_txt),
                        tags=(tag,))
        atualizar_totais()
    
    def carregar_ultima_venda():
        try:
            hoje = datetime.now().strftime("%Y-%m-%d")
            facturas = listar_facturas(50)
            
            ultima = None
            for f in facturas:
                data_factura = f[3][:10] if f[3] else ""
                if data_factura == hoje and f[6] != "ANULADA":
                    ultima = f
                    break
            
            if ultima:
                hora_v = ultima[3][11:16] if len(ultima[3]) > 16 else ""
                ultima_venda_var.set(
                    f"Ultima venda: {ultima[1]}  —  {formatar_kz(ultima[5])}  —  {hora_v}"
                )
            else:
                ultima_venda_var.set("Sem vendas registadas hoje")
        except Exception as e:
            print(f"[PDV] Erro ao carregar ultima venda: {e}")
            ultima_venda_var.set("")
    
    def adicionar_item(event=None):
        codigo = entry_codigo.get().strip()
        if not codigo:
            return
        
        produto = buscar_por_codigo(codigo)
        if not produto:
            messagebox.showwarning("Nao encontrado", f"Codigo '{codigo}' nao existe.")
            entry_codigo.delete(0, END)
            preview_var.set("")
            entry_codigo.focus()
            return
        
        pid, nome, preco, estoque, isento = produto
        
        if estoque <= 0:
            messagebox.showwarning("Sem estoque", f"'{nome}' esta sem estoque!")
            entry_codigo.delete(0, END)
            preview_var.set("")
            entry_codigo.focus()
            return
        
        for item in carrinho:
            if item["id"] == pid:
                if item["qtd"] >= estoque:
                    messagebox.showwarning("Estoque", f"So ha {estoque} unidades.")
                    entry_codigo.delete(0, END)
                    preview_var.set("")
                    entry_codigo.focus()
                    return
                item["qtd"] += 1
                break
        else:
            carrinho.append({"id": pid, "nome": nome, "preco": preco, "qtd": 1,
                             "isento": bool(isento), "desconto_percent": 0.0})
        
        atualizar_tabela()
        entry_codigo.delete(0, END)
        preview_var.set("")
        entry_codigo.focus()
    
    entry_codigo.bind('<Return>', adicionar_item)
    
    def pedir_autorizacao(percent):
        if utilizador_logado and utilizador_logado["perfil"] == "admin":
            return True, utilizador_logado["nome"]
        
        auth = Toplevel(janela)
        auth.title("Autorizacao")
        auth.geometry("450x380")
        auth.configure(bg=COR_FUNDO)
        auth.transient(janela)
        auth.grab_set()
        
        resultado = {"ok": False, "admin": None}
        
        Label(auth, text="AUTORIZACAO NECESSARIA", font=("Arial", 14, "bold"),
              bg=COR_FUNDO, fg=COR_PERIGO).pack(pady=(25, 10))
        Label(auth, text=f"Desconto de {percent:.0f}% excede o limite de {LIMITE_DESCONTO}%",
              font=("Arial", 11), bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=5)
        Label(auth, text="Senha do administrador:",
              font=("Arial", 10, "italic"), bg=COR_FUNDO, fg="#6b7280").pack(pady=(15, 5))
        
        f = Frame(auth, bg=COR_FUNDO)
        f.pack(pady=10)
        
        Label(f, text="Utilizador:", font=("Arial", 10, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).grid(row=0, column=0, sticky=W, padx=5, pady=5)
        e_user = Entry(f, font=("Arial", 11), width=20)
        e_user.grid(row=0, column=1, padx=5, pady=5, ipady=4)
        e_user.focus()
        
        Label(f, text="Senha:", font=("Arial", 10, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).grid(row=1, column=0, sticky=W, padx=5, pady=5)
        e_pass = Entry(f, font=("Arial", 11), width=20, show="*")
        e_pass.grid(row=1, column=1, padx=5, pady=5, ipady=4)
        
        msg_var = StringVar()
        Label(auth, textvariable=msg_var, font=("Arial", 10), bg=COR_FUNDO, fg=COR_PERIGO).pack()
        
        def confirmar(event=None):
            sucesso, dados = autenticar(e_user.get().strip(), e_pass.get())
            if sucesso and dados["perfil"] == "admin":
                resultado["ok"] = True
                resultado["admin"] = dados["nome"]
                auth.destroy()
            else:
                msg_var.set("Credenciais invalidas")
                e_pass.delete(0, END)
        
        e_pass.bind('<Return>', confirmar)
        
        Button(auth, text="Autorizar", font=("Arial", 12, "bold"),
               bg=COR_PRIMARIA, fg="white", width=20, height=2, bd=0, cursor="hand2",
               command=confirmar).pack(pady=15)
        
        auth.wait_window()
        return resultado["ok"], resultado["admin"]
    
    def aplicar_desconto():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um produto.")
            return
        
        idx = tree.index(sel[0])
        item = carrinho[idx]
        
        desc = Toplevel(janela)
        desc.title("Desconto")
        desc.geometry("450x400")
        desc.configure(bg=COR_FUNDO)
        desc.transient(janela)
        desc.grab_set()
        
        Label(desc, text=f"Desconto: {item['nome']}", font=("Arial", 14, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(20, 5))
        
        total_item = item["preco"] * item["qtd"]
        Label(desc, text=f"Subtotal: {formatar_kz(total_item)}",
              font=("Arial", 11), bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=5)
        
        Label(desc, text="Desconto (%):", font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))
        
        e_desc = Entry(desc, font=("Arial", 16), width=10, justify=CENTER)
        e_desc.pack(pady=5, ipady=6)
        e_desc.insert(0, str(int(item["desconto_percent"])))
        e_desc.focus()
        
        prev_var = StringVar()
        Label(desc, textvariable=prev_var, font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_PRIMARIA).pack(pady=10)
        
        def atualizar(event=None):
            try:
                p = float(e_desc.get().replace(",", "."))
                if 0 <= p <= 100:
                    vd = total_item * (p / 100)
                    prev_var.set(f"Desconto: -{formatar_kz(vd)}")
            except ValueError:
                prev_var.set("")
        
        e_desc.bind('<KeyRelease>', atualizar)
        atualizar()
        
        def confirmar():
            try:
                p = float(e_desc.get().replace(",", "."))
            except ValueError:
                messagebox.showerror("Erro", "Valor invalido.")
                return
            
            if p < 0 or p > 100:
                messagebox.showwarning("Aviso", "Entre 0 e 100%")
                return
            
            if p == 0:
                item["desconto_percent"] = 0
                desc.destroy()
                atualizar_tabela()
                return
            
            if p > LIMITE_DESCONTO:
                desc.destroy()
                ok, admin = pedir_autorizacao(p)
                if not ok:
                    messagebox.showwarning("Cancelado", "Nao autorizado.")
                    return
                item["desconto_percent"] = p
                registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                    "DESCONTO AUTORIZADO",
                                    f"{item['nome']} | {p}% | Por: {admin}")
            else:
                item["desconto_percent"] = p
                registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                    "DESCONTO ITEM", f"{item['nome']} | {p}%")
                desc.destroy()
            
            atualizar_tabela()
        
        e_desc.bind('<Return>', lambda e: confirmar())
        
        Button(desc, text="Aplicar", font=("Arial", 12, "bold"),
               bg=COR_DESCONTO, fg="white", width=20, height=2, bd=0, cursor="hand2",
               command=confirmar).pack(pady=15)
    
    def remover_item():
        sel = tree.selection()
        if not sel:
            return
        idx = tree.index(sel[0])
        carrinho.pop(idx)
        atualizar_tabela()
    
    def finalizar():
        if not carrinho:
            messagebox.showwarning("Vazio", "Adicione produtos.")
            return
        
        sub_o = calc_sub_original()
        desc = calc_desc()
        iva = calc_iva()
        total = calc_sub_com_desc() + iva
        
        cli_sel = cliente_var.get()
        cliente_id = None if cli_sel.startswith("(Sem") else int(cli_sel.split(" - ")[0])
        
        pg = Toplevel(janela)
        pg.title("Finalizar Venda")
        pg.geometry("450x750")
        pg.configure(bg=COR_FUNDO)
        
        Label(pg, text="Resumo da Venda", font=("Arial", 16, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(20, 10))
        
        card = Frame(pg, bg=COR_CARD, highlightthickness=2, highlightbackground=COR_PRIMARIA)
        card.pack(padx=20, pady=10, fill=X)
        
        Label(card, text=f"Subtotal: {formatar_kz(sub_o)}", font=("Arial", 11),
              bg=COR_CARD, fg=COR_TEXTO).pack(anchor=E, padx=20, pady=(10, 2))
        
        if desc > 0:
            Label(card, text=f"Desconto: -{formatar_kz(desc)}", font=("Arial", 11, "bold"),
                  bg=COR_CARD, fg=COR_DESCONTO).pack(anchor=E, padx=20, pady=2)
        
        Label(card, text=f"IVA: {formatar_kz(iva)}", font=("Arial", 11, "bold"),
              bg=COR_CARD, fg=COR_IVA).pack(anchor=E, padx=20, pady=2)
        Label(card, text=f"TOTAL: {formatar_kz(total)}", font=("Arial", 18, "bold"),
              bg=COR_CARD, fg=COR_PRIMARIA).pack(anchor=E, padx=20, pady=(5, 15))
        
        Label(pg, text="Forma de Pagamento:", font=("Arial", 12, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))
        
        def pagar(forma):
            pg.destroy()
            if forma == "Dinheiro":
                pedir_troco(total, forma, cliente_id, sub_o, desc)
            elif forma == "MISTO":
                pag_misto(total, cliente_id, sub_o, desc)
            else:
                pedir_ref(forma, total, cliente_id, sub_o, desc)
        
        Button(pg, text="Dinheiro", font=("Arial", 12, "bold"), bg=COR_PRIMARIA, fg="white",
               width=24, height=2, bd=0, cursor="hand2",
               command=lambda: pagar("Dinheiro")).pack(pady=6)
        Button(pg, text="Multicaixa", font=("Arial", 12, "bold"), bg="#0891b2", fg="white",
               width=24, height=2, bd=0, cursor="hand2",
               command=lambda: pagar("Multicaixa")).pack(pady=6)
        Button(pg, text="Transferencia", font=("Arial", 12, "bold"), bg="#7c3aed", fg="white",
               width=24, height=2, bd=0, cursor="hand2",
               command=lambda: pagar("Transferencia")).pack(pady=6)
        Button(pg, text="Pagamento Misto", font=("Arial", 12, "bold"), bg=COR_MISTO, fg="white",
               width=24, height=2, bd=0, cursor="hand2",
               command=lambda: pagar("MISTO")).pack(pady=6)
        
        Label(pg, text="─" * 40, bg=COR_FUNDO, fg="#6b7280").pack(pady=(15, 5))
        
        Button(pg, text="📄 Emitir PROFORMA", font=("Arial", 12, "bold"),
               bg="#7c3aed", fg="white",
               width=24, height=2, bd=0, cursor="hand2",
               command=lambda: emitir_proforma(total, cliente_id, sub_o, desc)
               ).pack(pady=6)
        
        Label(pg, text="(Documento não fiscal - válido 7 dias)",
              font=("Arial", 9, "italic"), bg=COR_FUNDO, fg="#6b7280").pack()
    
    def emitir_proforma(total, cliente_id, sub_o, desc):
        from database import (proximo_numero_proforma, criar_proforma,
                                buscar_cliente_por_id, adicionar_item_factura)
        
        try:
            r = proximo_numero_proforma()
            if not r or not r[0]:
                messagebox.showerror("Erro",
                    "Nao foi possivel gerar numero de proforma.\n\n"
                    "Verifique a configuracao da empresa.")
                return
            
            serie, numero = r
            
            cli_nome = "Consumidor Final"
            cli_nif = ""
            cli_end = ""
            
            if cliente_id:
                cli = buscar_cliente_por_id(cliente_id)
                if cli:
                    cli_nome = cli[1]
                    cli_nif = cli[2] or ""
                    cli_end = cli[4] or ""
            
            subtotal = sum(i["preco"] * i["qtd"] for i in carrinho)
            sub_desc = subtotal - (desc or 0)
            
            total_iva = 0
            for item in carrinho:
                s = item["preco"] * item["qtd"]
                if item["desconto_percent"] > 0:
                    s -= s * (item["desconto_percent"] / 100)
                if not item["isento"]:
                    total_iva += s * IVA_ANGOLA
            
            total_final = sub_desc + total_iva
            
            uid = utilizador_logado["id"] if utilizador_logado else None
            unome = utilizador_logado["nome"] if utilizador_logado else "Sistema"
            
            fid = criar_proforma(
                serie, numero, None, cliente_id,
                cli_nome, cli_nif, cli_end,
                subtotal, total_iva, total_final,
                uid, unome, None, None
            )
            
            if not fid:
                messagebox.showerror("Erro", "Falha ao criar proforma.")
                return
            
            for item in carrinho:
                isento = 1 if item["isento"] else 0
                taxa = 0.0 if item["isento"] else IVA_ANGOLA
                si = item["preco"] * item["qtd"]
                dv = 0.0
                if item["desconto_percent"] > 0:
                    dv = si * (item["desconto_percent"] / 100)
                    si -= dv
                
                vi = 0.0 if item["isento"] else si * IVA_ANGOLA
                
                adicionar_item_factura(fid, item["id"], item["nome"],
                                        item["qtd"], item["preco"],
                                        isento, taxa, vi, si)
                
                if item["desconto_percent"] > 0:
                    try:
                        conn = conectar()
                        cur = conn.cursor()
                        cur.execute("""UPDATE itens_factura 
                                       SET desconto_percent=?, desconto_valor=?
                                       WHERE id=(SELECT MAX(id) FROM itens_factura 
                                                 WHERE factura_id=?)""",
                                    (item["desconto_percent"], dv, fid))
                        conn.commit()
                        conn.close()
                    except Exception:
                        pass
            
            if utilizador_logado:
                registar_auditoria(
                    uid, unome, "EMISSAO PROFORMA",
                    f"{numero} | {formatar_kz(total_final)} | Cliente: {cli_nome}"
                )
            
            janela.destroy()
            perguntar_impressao_proforma(numero, fid)
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"Erro ao emitir proforma: {e}")
    
    def perguntar_impressao_proforma(numero, fid):
        pg = Toplevel()
        pg.title("Imprimir Proforma")
        pg.geometry("500x400")
        pg.configure(bg=COR_FUNDO)
        
        Label(pg, text="Proforma Emitida!", font=("Arial", 20, "bold"),
              bg=COR_FUNDO, fg="#7c3aed").pack(pady=(30, 10))
        Label(pg, text=f"Documento: {numero}",
              font=("Arial", 14, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=5)
        Label(pg, text="(Documento nao fiscal - valido 7 dias)",
              font=("Arial", 10, "italic"), bg=COR_FUNDO, fg="#6b7280").pack(pady=(5, 15))
        Label(pg, text="Deseja imprimir?", font=("Arial", 12),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 15))
        
        def imprimir(tipo):
            pg.destroy()
            try:
                from impressao import gerar_pdf_proforma
                caminho, erro = gerar_pdf_proforma(fid, formato=tipo)
                if erro:
                    messagebox.showerror("Erro", erro)
                    return
                import os
                if os.path.exists(caminho):
                    os.startfile(caminho)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro: {e}")
        
        Button(pg, text="Cupom Termico 80mm", font=("Arial", 12, "bold"),
               bg="#16a34a", fg="white", width=35, height=2, bd=0, cursor="hand2",
               command=lambda: imprimir("TERMICA")).pack(pady=5)
        Button(pg, text="Factura A4", font=("Arial", 12, "bold"),
               bg="#0891b2", fg="white", width=35, height=2, bd=0, cursor="hand2",
               command=lambda: imprimir("A4")).pack(pady=5)
        Button(pg, text="Fechar sem imprimir", font=("Arial", 11),
               bg="#6b7280", fg="white", width=35, height=2, bd=0, cursor="hand2",
               command=pg.destroy).pack(pady=10)
    
    def pedir_ref(forma, total, cliente_id, sub_o, desc):
        rj = Toplevel(janela)
        rj.title("Referencia")
        rj.geometry("450x450")
        rj.configure(bg=COR_FUNDO)
        
        Label(rj, text=forma, font=("Arial", 18, "bold"),
              bg=COR_FUNDO, fg="#0891b2").pack(pady=(20, 5))
        Label(rj, text=f"TOTAL: {formatar_kz(total)}", font=("Arial", 20, "bold"),
              bg=COR_FUNDO, fg=COR_PRIMARIA).pack(pady=10)
        
        if forma == "Multicaixa":
            Label(rj, text="Ultimos 4 digitos do talao:", font=("Arial", 12, "bold"),
                  bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(20, 5))
        else:
            Label(rj, text="Ultimos 4 digitos da transferencia:", font=("Arial", 12, "bold"),
                  bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(20, 5))
        
        e_ref = Entry(rj, font=("Arial", 24, "bold"), width=8, justify=CENTER)
        e_ref.pack(pady=10, ipady=10)
        e_ref.focus()
        
        def confirmar(event=None):
            ref = e_ref.get().strip()
            if len(ref) != 4 or not ref.isdigit():
                messagebox.showwarning("Aviso", "Digite 4 digitos.")
                e_ref.delete(0, END)
                return
            rj.destroy()
            concluir(forma, total, cliente_id, None, ref, sub_o, desc)
        
        e_ref.bind('<Return>', confirmar)
        
        Button(rj, text="Confirmar", font=("Arial", 12, "bold"),
               bg="#0891b2", fg="white", width=20, height=2, bd=0, cursor="hand2",
               command=confirmar).pack(pady=20)
    
    def pag_misto(total, cliente_id, sub_o, desc):
        pm = Toplevel(janela)
        pm.title("Pagamento Misto")
        pm.geometry("500x700")
        pm.configure(bg=COR_FUNDO)
        
        Label(pm, text="Pagamento Misto", font=("Arial", 18, "bold"),
              bg=COR_FUNDO, fg=COR_MISTO).pack(pady=(20, 5))
        Label(pm, text=f"TOTAL: {formatar_kz(total)}", font=("Arial", 20, "bold"),
              bg=COR_FUNDO, fg=COR_PRIMARIA).pack(pady=10)
        
        segunda_var = StringVar(value="Multicaixa")
        f = Frame(pm, bg=COR_FUNDO)
        f.pack(pady=5)
        Radiobutton(f, text="Multicaixa", variable=segunda_var, value="Multicaixa",
                    bg=COR_FUNDO, font=("Arial", 11), selectcolor=COR_FUNDO).pack(side=LEFT, padx=15)
        Radiobutton(f, text="Transferencia", variable=segunda_var, value="Transferencia",
                    bg=COR_FUNDO, font=("Arial", 11), selectcolor=COR_FUNDO).pack(side=LEFT, padx=15)
        
        Label(pm, text="Valor em DINHEIRO (Kz):", font=("Arial", 12, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))
        e_din = Entry(pm, font=("Arial", 16), width=15, justify=CENTER)
        e_din.pack(pady=5, ipady=6)
        e_din.focus()
        
        Label(pm, text="Valor na segunda forma (Kz):", font=("Arial", 12, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))
        e_seg = Entry(pm, font=("Arial", 16), width=15, justify=CENTER)
        e_seg.pack(pady=5, ipady=6)
        
        Label(pm, text="Ultimos 4 digitos:", font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))
        e_ref = Entry(pm, font=("Arial", 16, "bold"), width=8, justify=CENTER)
        e_ref.pack(pady=5, ipady=6)
        
        prev_var = StringVar()
        Label(pm, textvariable=prev_var, font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_PRIMARIA).pack(pady=10)
        
        def atualizar(event=None):
            try:
                d = float(e_din.get().replace(".", "").replace(",", ".") or 0)
                s = float(e_seg.get().replace(".", "").replace(",", ".") or 0)
                soma = d + s
                if abs(soma - total) < 0.01:
                    prev_var.set(f"OK: {formatar_kz(soma)}")
                elif soma < total:
                    prev_var.set(f"Falta: {formatar_kz(total - soma)}")
                else:
                    prev_var.set(f"Troco: {formatar_kz(soma - total)}")
            except ValueError:
                prev_var.set("")
        
        e_din.bind('<KeyRelease>', atualizar)
        e_seg.bind('<KeyRelease>', atualizar)
        
        def confirmar():
            try:
                d = float(e_din.get().replace(".", "").replace(",", ".") or 0)
                s = float(e_seg.get().replace(".", "").replace(",", ".") or 0)
            except ValueError:
                messagebox.showerror("Erro", "Valores invalidos.")
                return

            if d < 0 or s < 0 or s > total + 0.01:
                messagebox.showwarning(
                    "Aviso", "Os valores de cada meio de pagamento sao invalidos.")
                return
            
            ref = e_ref.get().strip()
            if len(ref) != 4 or not ref.isdigit():
                messagebox.showwarning("Aviso", "4 digitos obrigatorios.")
                return
            
            if d + s < total - 0.01:
                messagebox.showwarning("Aviso", "Falta valor.")
                return

            if d < total - s - 0.01:
                messagebox.showwarning("Aviso", "O valor em dinheiro e insuficiente.")
                return
            
            segunda = segunda_var.get()
            pm.destroy()
            concluir(f"Misto: Dinheiro + {segunda}", total, cliente_id,
                     d, ref, sub_o, desc, valor_segunda=s)
        
        e_ref.bind('<Return>', lambda e: confirmar())
        
        Button(pm, text="Confirmar", font=("Arial", 12, "bold"),
               bg=COR_MISTO, fg="white", width=20, height=2, bd=0, cursor="hand2",
               command=confirmar).pack(pady=15)
    
    def pedir_troco(total, forma, cliente_id, sub_o, desc):
        tj = Toplevel(janela)
        tj.title("Troco")
        tj.geometry("420x450")
        tj.configure(bg=COR_FUNDO)
        
        Label(tj, text=f"TOTAL: {formatar_kz(total)}", font=("Arial", 16, "bold"),
              bg=COR_FUNDO, fg=COR_PRIMARIA).pack(pady=20)
        Label(tj, text="Valor recebido:", font=("Arial", 12, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=5)
        
        e_rec = Entry(tj, font=("Arial", 18), width=15, justify=CENTER)
        e_rec.pack(pady=10, ipady=6)
        e_rec.focus()
        
        tv = StringVar()
        tl = Label(tj, textvariable=tv, font=("Arial", 18, "bold"),
                   bg=COR_FUNDO, fg=COR_PRIMARIA)
        tl.pack(pady=15)
        
        def calc(event=None):
            try:
                r = float(e_rec.get().replace(".", "").replace(",", "."))
                if r < total:
                    tv.set(f"Falta {formatar_kz(total - r)}")
                    tl.config(fg=COR_PERIGO)
                else:
                    tv.set(f"Troco: {formatar_kz(r - total)}")
                    tl.config(fg=COR_PRIMARIA)
            except ValueError:
                tv.set("")
        
        e_rec.bind('<KeyRelease>', calc)
        
        def confirmar():
            try:
                r = float(e_rec.get().replace(".", "").replace(",", "."))
                if r < total:
                    messagebox.showwarning("Aviso", "Valor insuficiente.")
                    return
                tj.destroy()
                concluir(forma, total, cliente_id, r, None, sub_o, desc)
            except ValueError:
                messagebox.showerror("Erro", "Valor invalido.")
        
        e_rec.bind('<Return>', lambda e: confirmar())
        
        Button(tj, text="Confirmar", font=("Arial", 12, "bold"),
               bg=COR_PRIMARIA, fg="white", width=20, height=2, bd=0, cursor="hand2",
               command=confirmar).pack(pady=15)
    
    def concluir(forma, total, cliente_id, dinheiro=None, ref=None, sub_o=None,
                 desc=0, valor_segunda=None):
        """Transaccao atomica: ou grava tudo, ou nada."""
        try:
            uid = utilizador_logado["id"] if utilizador_logado else None
            unome = utilizador_logado["nome"] if utilizador_logado else "Sistema"

            itens_para_tx = []
            for item in carrinho:
                itens_para_tx.append({
                    "produto_id": item["id"],
                    "nome": item["nome"],
                    "quantidade": item["qtd"],
                    "preco_unitario": item["preco"],
                    "isento_iva": item["isento"],
                    "desconto_percent": item.get("desconto_percent", 0),
                })

            cliente_info = None
            if cliente_id:
                from database import buscar_cliente_por_id
                cli = buscar_cliente_por_id(cliente_id)
                if cli:
                    cliente_info = {
                        "nome": cli[1],
                        "nif": cli[2] or "",
                        "endereco": cli[4] or "",
                    }

            utilizador_dict = {
                "id": uid,
                "nome": unome,
            }

            if forma == "Dinheiro":
                valores_pagamento = {"dinheiro": total}
            elif forma == "Multicaixa":
                valores_pagamento = {"tpa": total}
            elif forma == "Transferencia":
                valores_pagamento = {"transferencia": total}
            elif forma.startswith("Misto: Dinheiro + "):
                try:
                    valor_segunda = round(float(valor_segunda), 2)
                except (TypeError, ValueError):
                    messagebox.showerror("Erro", "Indique o valor do segundo meio de pagamento.")
                    return
                valor_dinheiro = round(float(total) - valor_segunda, 2)
                segundo_meio = forma.rsplit("+", 1)[-1].strip()
                valores_pagamento = {"dinheiro": valor_dinheiro}
                if segundo_meio == "Multicaixa":
                    valores_pagamento["tpa"] = valor_segunda
                elif segundo_meio == "Transferencia":
                    valores_pagamento["transferencia"] = valor_segunda
                else:
                    messagebox.showerror("Erro", "Segundo meio de pagamento desconhecido.")
                    return
            else:
                valores_pagamento = None

            from database import finalizar_venda

            sucesso, resultado = finalizar_venda(
                itens=itens_para_tx,
                forma_pagamento=forma,
                utilizador=utilizador_dict,
                cliente_id=cliente_id,
                caixa_id=caixa_id,
                cliente_info=cliente_info,
                desconto_global=desc or 0,
                autorizado_por=ref,
                valores_pagamento=valores_pagamento,
            )

            if not sucesso:
                messagebox.showerror("Erro na Venda",
                    f"A venda foi CANCELADA.\n\n"
                    f"Motivo: {resultado}\n\n"
                    f"Nada foi gravado. Pode tentar novamente.")
                return

            venda_id = resultado["venda_id"]
            numero = resultado["factura_numero"]

            if "Dinheiro" in forma:
                try:
                    from impressao import abrir_gaveta
                    abrir_gaveta()
                except Exception as e_gav:
                    print(f"[PDV] Aviso ao abrir gaveta: {e_gav}")

            janela.destroy()

            if numero:
                perguntar_impressao(numero)

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"Erro inesperado: {e}")
    
    def perguntar_impressao(numero_factura):
        pg = Toplevel()
        pg.title("Imprimir?")
        pg.geometry("500x400")
        pg.configure(bg=COR_FUNDO)
        
        Label(pg, text="Venda Concluida!", font=("Arial", 20, "bold"),
              bg=COR_FUNDO, fg=COR_PRIMARIA).pack(pady=(30, 10))
        Label(pg, text=f"Factura: {numero_factura}",
              font=("Arial", 14, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=5)
        Label(pg, text="Deseja imprimir?", font=("Arial", 12),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(20, 15))
        
        def imprimir(tipo):
            pg.destroy()
            try:
                from impressao import gerar_pdf_factura
                conn = conectar()
                cur = conn.cursor()
                cur.execute("SELECT id FROM facturas WHERE numero = ?", (numero_factura,))
                r = cur.fetchone()
                conn.close()
                if not r:
                    messagebox.showerror("Erro", "Factura nao encontrada.")
                    return
                caminho, erro = gerar_pdf_factura(r[0], formato=tipo)
                if erro:
                    messagebox.showerror("Erro", erro)
                    return
                import os
                if os.path.exists(caminho):
                    os.startfile(caminho)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro: {e}")
        
        Button(pg, text="Cupom Termico 80mm", font=("Arial", 12, "bold"),
               bg="#16a34a", fg="white", width=35, height=2, bd=0, cursor="hand2",
               command=lambda: imprimir("TERMICA")).pack(pady=5)
        Button(pg, text="Factura A4", font=("Arial", 12, "bold"),
               bg="#0891b2", fg="white", width=35, height=2, bd=0, cursor="hand2",
               command=lambda: imprimir("A4")).pack(pady=5)
        Button(pg, text="Fechar", font=("Arial", 11),
               bg="#6b7280", fg="white", width=35, height=2, bd=0, cursor="hand2",
               command=pg.destroy).pack(pady=10)
    
    fb = Frame(janela, bg=COR_FUNDO)
    fb.pack(pady=10)
    
    Button(fb, text="🟣 Aplicar Desconto", font=("Arial", 11, "bold"),
           bg=COR_DESCONTO, fg="white", width=22, height=2, bd=0, cursor="hand2",
           command=aplicar_desconto).pack(side=LEFT, padx=5)
    Button(fb, text="🔴 Remover Item", font=("Arial", 11, "bold"),
           bg=COR_PERIGO, fg="white", width=20, height=2, bd=0, cursor="hand2",
           command=remover_item).pack(side=LEFT, padx=5)
    Button(fb, text="🟢 Finalizar Venda", font=("Arial", 12, "bold"),
           bg=COR_PRIMARIA, fg="white", width=22, height=2, bd=0, cursor="hand2",
           command=finalizar).pack(side=LEFT, padx=5)
    
    janela.bind('<F4>', lambda e: aplicar_desconto())
    janela.bind('<F8>', lambda e: remover_item())
    janela.bind('<F12>', lambda e: finalizar())
    
    carregar_ultima_venda()


# ============================================================
# ============ JANELA: FUNDO DE TROCO (PDV) =================
# ============================================================

def _janela_fundo_troco_pdv(utilizador_logado, parent, callback_sucesso=None):
    """Pedir fundo de troco + senha do gerente para abrir caixa."""

    janela = Toplevel(parent)
    janela.title("Abrir Caixa - Fundo de Troco")
    janela.geometry("550x650")
    janela.configure(bg=COR_FUNDO)
    janela.transient(parent)
    janela.grab_set()

    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 550) // 2
    y = (janela.winfo_screenheight() - 650) // 2
    janela.geometry(f"550x650+{x}+{y}")

    header = Frame(janela, bg="#16a34a", height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="ABRIR CAIXA",
          font=("Segoe UI", 18, "bold"),
          bg="#16a34a", fg="white").pack(pady=(15, 0))
    Label(header, text="Declarar fundo de troco recebido do gerente",
          font=("Segoe UI", 10, "italic"),
          bg="#16a34a", fg="#dcfce7").pack()

    body = Frame(janela, bg=COR_FUNDO)
    body.pack(fill=BOTH, expand=True, padx=30, pady=20)

    Label(body, text="Fundo de troco (Kz):",
          font=("Segoe UI", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(10, 5))

    entry_valor = Entry(body, font=("Segoe UI", 18), width=18,
                         justify=CENTER, bd=2, relief=SOLID)
    entry_valor.pack(pady=10, ipady=10)
    entry_valor.insert(0, "0")
    entry_valor.focus()

    Label(body, text="(Dinheiro recebido do gerente para dar troco)",
          font=("Segoe UI", 9, "italic"),
          bg=COR_FUNDO, fg="#6b7280").pack()

    aviso_frame = Frame(body, bg="#fef3c7",
                          highlightthickness=1, highlightbackground="#f59e0b")
    aviso_frame.pack(fill=X, pady=(20, 10))
    Label(aviso_frame,
          text="SERA NECESSARIA A SENHA DO GERENTE\nPARA AUTORIZAR A ABERTURA",
          font=("Segoe UI", 10, "bold"),
          bg="#fef3c7", fg="#92400e",
          justify=CENTER).pack(pady=12, padx=10)

    def confirmar():
        try:
            valor_txt = entry_valor.get().replace(".", "").replace(",", ".")
            valor = float(valor_txt)
            if valor < 0:
                messagebox.showwarning("Aviso", "O valor deve ser positivo.")
                return

            from caixa import _pedir_autorizacao_gerente
            ok, nome_gerente = _pedir_autorizacao_gerente(
                janela,
                f"Abertura de caixa com fundo {formatar_kz(valor)}",
                utilizador_logado
            )
            if not ok:
                return

            from database import abrir_caixa, registar_auditoria
            cx_id = abrir_caixa(utilizador_logado["id"],
                                 utilizador_logado["nome"], valor)

            registar_auditoria(
                utilizador_logado["id"], utilizador_logado["nome"],
                "ABERTURA CAIXA",
                f"Caixa #{cx_id} | Fundo: {formatar_kz(valor)} | "
                f"Autorizado por: {nome_gerente}"
            )

            messagebox.showinfo("Caixa Aberto",
                f"CAIXA #{cx_id} ABERTO!\n\n"
                f"Fundo de troco: {formatar_kz(valor)}\n"
                f"Autorizado por: {nome_gerente}\n\n"
                f"Pode comecar a vender.")

            janela.destroy()
            if callback_sucesso:
                callback_sucesso()

        except ValueError:
            messagebox.showerror("Erro", "Digite um valor valido.")

    entry_valor.bind('<Return>', lambda e: confirmar())

    frame_btn = Frame(body, bg=COR_FUNDO)
    frame_btn.pack(pady=20)

    Button(frame_btn, text="Confirmar e Abrir Caixa",
           font=("Segoe UI", 12, "bold"),
           bg="#16a34a", fg="white",
           width=25, height=2, bd=0, cursor="hand2",
           command=confirmar).pack(side=LEFT, padx=5)

    Button(frame_btn, text="Cancelar",
           font=("Segoe UI", 11),
           bg="#6b7280", fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=5)
