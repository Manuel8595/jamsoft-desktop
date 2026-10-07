import os
from tkinter import *
from tkinter import messagebox, ttk, simpledialog, filedialog
from database import (obter_empresa, guardar_empresa, obter_logo_empresa,
                       guardar_logo_empresa, proximo_numero_factura,
                       criar_factura, adicionar_item_factura, listar_facturas,
                       buscar_factura_por_id, listar_itens_factura, anular_factura,
                       registar_auditoria, conectar,
                       obter_itens_factura_com_desconto)
from moeda import formatar_kz, IVA_ANGOLA
from datetime import datetime

COR_FUNDO = "#fef3c7"
COR_PRIMARIA = "#b45309"
COR_TEXTO = "#78350f"
COR_PERIGO = "#dc2626"
COR_HEADER = "#92400e"
COR_CARD = "#ffffff"
COR_VERDE = "#16a34a"
COR_LARANJA = "#ea580c"
COR_DESCONTO = "#7c3aed"
COR_IVA = "#ea580c"
COR_ALERTA = "#f59e0b"


def abrir_fiscal(utilizador_logado):
    janela = Toplevel()
    janela.title("JAM Soft - Modulo Fiscal")
    janela.geometry("900x700")
    janela.configure(bg=COR_FUNDO)

    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Modulo Fiscal - Facturacao local", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)

    Label(janela,
          text="Este modulo ainda nao esta ligado a AGT. Confirma com a AGT ou contabilista antes de tratar estes documentos como facturas fiscais oficiais.",
          font=("Arial", 10, "bold"), bg="#fef2f2", fg=COR_PERIGO,
          wraplength=850, justify=LEFT).pack(fill=X, padx=20, pady=(12, 0))

    emp = obter_empresa()

    if emp is None or (len(emp) > 1 and not emp[1]):
        card = Frame(janela, bg=COR_CARD, highlightthickness=2, highlightbackground=COR_PERIGO)
        card.pack(fill=X, padx=20, pady=20)
        Label(card, text="EMPRESA NAO CONFIGURADA", font=("Arial", 16, "bold"),
              bg=COR_CARD, fg=COR_PERIGO).pack(pady=(20, 5))
        Label(card, text="Antes de emitir facturas, precisas de configurar os dados da farmacia.",
              font=("Arial", 11), bg=COR_CARD, fg=COR_TEXTO).pack(pady=(0, 20))

        Button(janela, text="Configurar Empresa", font=("Arial", 14, "bold"),
               bg=COR_PRIMARIA, fg="white", width=25, height=3, bd=0, cursor="hand2",
               command=lambda: configurar_empresa(utilizador_logado, janela)).pack(pady=10)
        return

    emp_id, nome, nif, endereco, telefone, email, regime, serie, prox = emp[:9]

    card_emp = Frame(janela, bg=COR_CARD, highlightthickness=2, highlightbackground=COR_VERDE)
    card_emp.pack(fill=X, padx=20, pady=15)

    Label(card_emp, text=nome, font=("Arial", 16, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(pady=(15, 5))
    Label(card_emp, text=f"NIF: {nif or 'Nao definido'} | Regime: {regime}",
          font=("Arial", 10), bg=COR_CARD, fg=COR_TEXTO).pack()
    Label(card_emp, text=f"Serie activa: {serie} | Proximo numero: {serie}{prox:05d}",
          font=("Arial", 10, "bold"), bg=COR_CARD, fg=COR_PRIMARIA).pack(pady=(5, 15))

    Label(janela, text="Facturas emitidas sao numeradas sequencialmente pela serie activa.",
          font=("Arial", 10, "italic"), bg=COR_FUNDO, fg="#6b7280").pack(pady=10)

    frame_botoes = Frame(janela, bg=COR_FUNDO)
    frame_botoes.pack(pady=20)

    estilo = {"font": ("Arial", 12, "bold"), "width": 25, "height": 3,
              "bd": 0, "cursor": "hand2", "fg": "white"}

    Button(frame_botoes, text="Listar Facturas", bg=COR_PRIMARIA,
           command=lambda: listar_facturas_janela(utilizador_logado),
           **estilo).grid(row=0, column=0, padx=8, pady=8)

    Button(frame_botoes, text="Listar Proformas", bg=COR_VERDE,
           command=lambda: listar_proformas_janela(utilizador_logado),
           **estilo).grid(row=0, column=1, padx=8, pady=8)

    Button(frame_botoes, text="Configurar Empresa", bg="#0891b2",
           command=lambda: configurar_empresa(utilizador_logado, janela),
           **estilo).grid(row=1, column=0, padx=8, pady=8)

    Button(frame_botoes, text="📄 Exportar SAF-T (AO)", bg="#7c3aed",
           command=lambda: exportar_saft_janela(utilizador_logado, janela),
           **estilo).grid(row=1, column=1, padx=8, pady=8)
    
    if utilizador_logado.get("perfil") == "admin":
        Button(frame_botoes, text="🔐 Configuração AGT", bg="#be185d",
               command=lambda: abrir_config_agt(utilizador_logado, janela),
               **estilo).grid(row=2, column=0, padx=8, pady=8)

def configurar_empresa(utilizador_logado, parent):
    janela = Toplevel(parent)
    janela.title("Configurar Empresa")
    janela.geometry("600x850")
    janela.configure(bg=COR_FUNDO)

    Label(janela, text="Dados da Farmacia / Empresa", font=("Arial", 16, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=15)

    emp = obter_empresa()

    main_frame = Frame(janela, bg=COR_FUNDO)
    main_frame.pack(fill=BOTH, expand=True)

    canvas = Canvas(main_frame, bg=COR_FUNDO, highlightthickness=0)
    scrollbar = Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas, bg=COR_FUNDO)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=580)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    card = Frame(scrollable_frame, bg=COR_CARD, highlightthickness=1, highlightbackground="#fde68a")
    card.pack(padx=20, pady=10, fill=X)

    frame = Frame(card, bg=COR_CARD)
    frame.pack(padx=20, pady=15, fill=X)

    Label(frame, text="Nome da Farmacia: *", font=("Arial", 11, "bold"), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
    entry_nome = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
    entry_nome.insert(0, emp[1] if emp else "")
    entry_nome.pack(fill=X, ipady=6)

    Label(frame, text="NIF: *", font=("Arial", 11, "bold"), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
    entry_nif = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
    entry_nif.insert(0, emp[2] if emp else "")
    entry_nif.pack(fill=X, ipady=6)

    Label(frame, text="Endereco:", font=("Arial", 11, "bold"), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
    entry_end = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
    entry_end.insert(0, emp[3] if emp else "")
    entry_end.pack(fill=X, ipady=6)

    Label(frame, text="Telefone:", font=("Arial", 11, "bold"), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
    entry_tel = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
    entry_tel.insert(0, emp[4] if emp else "")
    entry_tel.pack(fill=X, ipady=6)

    Label(frame, text="Email:", font=("Arial", 11, "bold"), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
    entry_email = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
    entry_email.insert(0, emp[5] if emp else "")
    entry_email.pack(fill=X, ipady=6)

    Label(frame, text="Regime Fiscal:", font=("Arial", 11, "bold"), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
    regime_var = StringVar(value=emp[6] if emp else "GERAL")
    ttk.Combobox(frame, textvariable=regime_var, values=["GERAL", "SIMPLIFICADO", "EXONERADO"],
                 state="readonly", font=("Arial", 11)).pack(fill=X, ipady=4)

    Label(frame, text="Serie de Facturacao: *", font=("Arial", 11, "bold"), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
    entry_serie = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
    entry_serie.insert(0, emp[7] if emp else "FT 2026/")
    entry_serie.pack(fill=X, ipady=6)

    Label(frame, text="Proximo Numero de Factura:", font=("Arial", 11, "bold"), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
    entry_num = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
    entry_num.insert(0, str(emp[8] if emp else 1))
    entry_num.pack(fill=X, ipady=6)

    Label(frame, text="Exemplo: se proximo = 1, a proxima factura sera FT 2026/00001",
          font=("Arial", 9, "italic"), bg=COR_CARD, fg="#6b7280").pack(anchor=W, pady=(2, 0))

    Label(frame, text="Logotipo da Farmacia:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(15, 3))

    logo_status_var = StringVar(value="Nenhum logotipo carregado")
    logo_atual = obter_logo_empresa()
    if logo_atual:
        try:
            logo_status_var.set(f"Atual: {os.path.basename(logo_atual)}")
        except Exception:
            logo_status_var.set("Logotipo carregado")

    Label(frame, textvariable=logo_status_var, font=("Arial", 9, "italic"),
          bg=COR_CARD, fg="#6b7280").pack(anchor=W, pady=(2, 5))

    def escolher_logo():
        import shutil
        caminho = filedialog.askopenfilename(
            title="Escolher Logotipo",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.PNG *.JPG *.JPEG")]
        )
        if not caminho:
            return

        try:
            os.makedirs("facturas", exist_ok=True)
            destino = os.path.join("facturas", "logo.png")
            shutil.copy2(caminho, destino)

            guardar_logo_empresa(destino)
            logo_status_var.set(f"Novo: {os.path.basename(caminho)}")
            messagebox.showinfo("Sucesso", "Logotipo carregado com sucesso!\n\n"
                                "Guarde a configuracao para aplicar.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao copiar logotipo: {e}")

    Button(frame, text="Escolher Logotipo", font=("Arial", 10, "bold"),
           bg="#0891b2", fg="white", width=20, height=2, bd=0, cursor="hand2",
           command=escolher_logo).pack(anchor=W, pady=5)

    Label(frame, text="Formatos: PNG, JPG, JPEG. Tamanho ideal: ate 500x500px",
          font=("Arial", 9, "italic"), bg=COR_CARD, fg="#6b7280").pack(anchor=W)

    frame_botoes = Frame(janela, bg=COR_FUNDO, height=70)
    frame_botoes.pack(side=BOTTOM, fill=X, pady=5)
    frame_botoes.pack_propagate(False)

    def salvar():
        nome = entry_nome.get().strip()
        nif = entry_nif.get().strip()
        if not nome or not nif:
            messagebox.showwarning("Aviso", "Nome e NIF sao obrigatorios.")
            return

        try:
            prox = int(entry_num.get().strip())
            if prox < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Aviso", "Numero de factura invalido.")
            return

        serie = entry_serie.get().strip() or "FT 2026/"

        guardar_empresa(nome, nif, entry_end.get().strip(), entry_tel.get().strip(),
                         entry_email.get().strip(), regime_var.get(), serie, prox)

        registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                            "CONFIG EMPRESA", f"Configurou '{nome}' | Serie: {serie}")

        messagebox.showinfo("Sucesso", "Empresa configurada com sucesso!")
        janela.destroy()
        parent.destroy()
        abrir_fiscal(utilizador_logado)

    Button(frame_botoes, text="Guardar Configuracao", font=("Arial", 12, "bold"),
           bg=COR_PRIMARIA, fg="white", width=25, height=2, bd=0, cursor="hand2",
           command=salvar).pack(side=LEFT, padx=20, pady=10)

    Button(frame_botoes, text="Cancelar", font=("Arial", 11),
           bg="#6b7280", fg="white", width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, pady=10)


def listar_facturas_janela(utilizador_logado):
    janela = Toplevel()
    janela.title("Lista de Facturas")
    janela.geometry("1100x600")
    janela.configure(bg=COR_FUNDO)

    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Facturas Emitidas", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)

    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(fill=BOTH, expand=True, padx=15, pady=15)

    colunas = ("ID", "Numero", "Tipo", "Data", "Cliente", "Total", "Estado")
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(fill=BOTH, expand=True)

    def carregar():
        for i in tree.get_children():
            tree.delete(i)
        for f in listar_facturas(100):
            fid, numero, tipo, data, cliente, total, estado = f
            tag = ""
            if estado == "ANULADA":
                tag = "anulada"
            tree.insert("", END, values=(fid, numero, tipo, data,
                                          cliente or "Consumidor Final",
                                          formatar_kz(total), estado), tags=(tag,))
        tree.tag_configure("anulada", background="#fee2e2", foreground="#991b1b")

    carregar()

    def ver_factura():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma factura.")
            return
        fid = tree.item(sel[0])["values"][0]
        ver_factura_janela(fid, utilizador_logado, carregar)

    def anular():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma factura.")
            return

        fid = tree.item(sel[0])["values"][0]
        estado = tree.item(sel[0])["values"][6]

        if estado == "ANULADA":
            messagebox.showinfo("Info", "Esta factura ja esta anulada.")
            return

        if not messagebox.askyesno("Confirmar", "Deseja anular esta factura?"):
            return

        motivo = simpledialog.askstring("Motivo", "Motivo da anulacao:", parent=janela)
        if not motivo:
            return

        anular_factura(fid, motivo, utilizador_logado["id"], utilizador_logado["nome"])
        registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                            "ANULAR FACTURA", f"Factura ID {fid} | Motivo: {motivo}")
        messagebox.showinfo("Sucesso", "Factura anulada.")
        carregar()

    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=10)

    estilo = {"font": ("Arial", 11, "bold"), "width": 18, "height": 2,
              "bd": 0, "cursor": "hand2", "fg": "white"}

    Button(frame_btn, text="Ver Detalhes", bg=COR_PRIMARIA, command=ver_factura, **estilo).grid(row=0, column=0, padx=5)
    Button(frame_btn, text="Anular Factura", bg=COR_PERIGO, command=anular, **estilo).grid(row=0, column=1, padx=5)
    Button(frame_btn, text="Actualizar", bg="#0891b2", command=carregar, **estilo).grid(row=0, column=2, padx=5)


def ver_factura_janela(factura_id, utilizador_logado, callback_atualizar=None):
    janela = Toplevel()
    janela.title("Detalhes da Factura")
    janela.geometry("850x750")
    janela.configure(bg=COR_FUNDO)

    f = buscar_factura_por_id(factura_id)
    if not f:
        messagebox.showerror("Erro", "Factura nao encontrada.")
        janela.destroy()
        return

    if len(f) >= 15:
        (fid, numero, serie, tipo, data, cli_nome, cli_nif, cli_end,
         subtotal, iva, total, estado, motivo,
         forma_pagamento, ref_multicaixa) = f[:15]
    else:
        (fid, numero, serie, tipo, data, cli_nome, cli_nif, cli_end,
         subtotal, iva, total, estado, motivo) = f[:13]
        forma_pagamento = None
        ref_multicaixa = None

    header = Frame(janela, bg=COR_HEADER, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text=f"{tipo} - {numero}", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=(15, 0))
    Label(header, text=f"Data: {data}   |   Estado: {estado}",
          font=("Arial", 10, "italic"), bg=COR_HEADER, fg="#fde68a").pack()

    if estado == "ANULADA":
        Label(janela, text=f"FACTURA ANULADA - Motivo: {motivo}",
              font=("Arial", 12, "bold"), bg="#fee2e2", fg=COR_PERIGO).pack(fill=X, pady=5)

    emp = obter_empresa()
    if emp:
        emp_card = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#fde68a")
        emp_card.pack(fill=X, padx=20, pady=10)
        Label(emp_card, text=emp[1], font=("Arial", 13, "bold"),
              bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15, pady=(10, 2))
        Label(emp_card, text=f"NIF: {emp[2] or '-'}",
              font=("Arial", 10), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15)
        Label(emp_card, text=f"{emp[3] or ''} | Tel: {emp[4] or ''}",
              font=("Arial", 10), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15, pady=(0, 10))

    cli_card = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#fde68a")
    cli_card.pack(fill=X, padx=20, pady=5)
    Label(cli_card, text="Cliente:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15, pady=(10, 2))
    Label(cli_card, text=cli_nome or "Consumidor Final",
          font=("Arial", 11), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15)
    Label(cli_card, text=f"NIF: {cli_nif or '-'} | {cli_end or ''}",
          font=("Arial", 10), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15, pady=(0, 5))

    pag_card = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground=COR_VERDE)
    pag_card.pack(fill=X, padx=20, pady=5)
    Label(pag_card, text="Pagamento:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15, pady=(10, 2))
    Label(pag_card, text=forma_pagamento or "Nao registado",
          font=("Arial", 11), bg=COR_CARD, fg=COR_PRIMARIA).pack(anchor=W, padx=15)
    if ref_multicaixa:
        Label(pag_card, text=f"Ref. Multicaixa: ****{ref_multicaixa}",
              font=("Arial", 10, "italic"), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15, pady=(0, 10))
    else:
        Label(pag_card, text="", bg=COR_CARD).pack(pady=(0, 5))

    Label(janela, text="Itens da Factura:", font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, padx=25, pady=(15, 5))

    frame_it = Frame(janela, bg=COR_FUNDO)
    frame_it.pack(fill=BOTH, expand=True, padx=20, pady=5)

    colunas = ("Descricao", "Qtd", "Preco", "Desc.", "IVA", "Valor IVA", "Subtotal")
    tree = ttk.Treeview(frame_it, columns=colunas, show="headings", height=8)
    for col in colunas:
        tree.heading(col, text=col)
    tree.column("Descricao", width=180)
    tree.column("Qtd", width=50)
    tree.column("Preco", width=90)
    tree.column("Desc.", width=60)
    tree.column("IVA", width=60)
    tree.column("Valor IVA", width=80)
    tree.column("Subtotal", width=90)
    tree.pack(fill=BOTH, expand=True)

    total_desconto = 0
    for item in obter_itens_factura_com_desconto(factura_id):
        desc, qtd, preco, isento, taxa, valor_iva, sub, desc_p, desc_v = item
        iva_txt = "Isento" if isento else f"{int(taxa*100)}%"
        desc_txt = f"{desc_p:.0f}%" if desc_p and desc_p > 0 else "-"

        total_desconto += desc_v or 0

        tree.insert("", END, values=(desc, qtd, formatar_kz(preco), desc_txt, iva_txt,
                                       formatar_kz(valor_iva), formatar_kz(sub)))

    tot_frame = Frame(janela, bg=COR_CARD, highlightthickness=2, highlightbackground=COR_PRIMARIA)
    tot_frame.pack(fill=X, padx=20, pady=15)

    Label(tot_frame, text=f"Subtotal: {formatar_kz(subtotal)}", font=("Arial", 11),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=E, padx=20, pady=(10, 2))

    if total_desconto > 0:
        Label(tot_frame, text=f"Descontos: -{formatar_kz(total_desconto)}",
              font=("Arial", 11, "bold"), bg=COR_CARD, fg=COR_DESCONTO).pack(anchor=E, padx=20, pady=2)

    Label(tot_frame, text=f"IVA: {formatar_kz(iva)}", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_PRIMARIA).pack(anchor=E, padx=20, pady=2)
    Label(tot_frame, text=f"TOTAL: {formatar_kz(total)}", font=("Arial", 16, "bold"),
          bg=COR_CARD, fg=COR_PRIMARIA).pack(anchor=E, padx=20, pady=(5, 15))

    Button(janela, text="Gerar PDF", font=("Arial", 11, "bold"),
           bg="#7c3aed", fg="white", width=20, height=2, bd=0, cursor="hand2",
           command=lambda: gerar_pdf_da_factura(factura_id)).pack(pady=10)


def gerar_pdf_da_factura(factura_id):
    try:
        from impressao import gerar_pdf_factura
        import os
        caminho, erro = gerar_pdf_factura(factura_id, formato="A4")
        if erro:
            messagebox.showerror("Erro", erro)
            return
        if os.path.exists(caminho):
            os.startfile(caminho)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro: {e}")


# ============================================================
# ============ PROFORMAS =====================================
# ============================================================

def listar_proformas_janela(utilizador_logado):
    """Lista as proformas emitidas."""
    from database import listar_proformas, anular_proforma

    janela = Toplevel()
    janela.title("Lista de Proformas")
    janela.geometry("1100x600")
    janela.configure(bg=COR_FUNDO)

    header = Frame(janela, bg=COR_VERDE, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Proformas Emitidas (Nao Fiscais)",
          font=("Arial", 18, "bold"),
          bg=COR_VERDE, fg="white").pack(pady=20)

    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(fill=BOTH, expand=True, padx=15, pady=15)

    colunas = ("ID", "Numero", "Data", "Cliente", "Total", "Validade", "Estado")
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=15)

    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=140)

    tree.column("ID", width=50)
    tree.column("Validade", width=110)
    tree.pack(fill=BOTH, expand=True)

    def carregar():
        for i in tree.get_children():
            tree.delete(i)
        try:
            for p in listar_proformas(100):
                pid, numero, data, cliente, total, estado, validade = p
                tag = ""
                if estado == "ANULADA":
                    tag = "anulada"
                tree.insert("", END, values=(pid, numero, data,
                                              cliente or "Consumidor Final",
                                              formatar_kz(total),
                                              validade or "-",
                                              estado), tags=(tag,))
            tree.tag_configure("anulada", background="#fee2e2", foreground="#991b1b")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar: {e}")

    carregar()

    def ver_proforma():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma proforma.")
            return
        pid = tree.item(sel[0])["values"][0]
        ver_proforma_janela(pid, utilizador_logado, carregar)

    def anular():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma proforma.")
            return

        pid = tree.item(sel[0])["values"][0]
        estado = tree.item(sel[0])["values"][6]

        if estado == "ANULADA":
            messagebox.showinfo("Info", "Esta proforma ja esta anulada.")
            return

        if not messagebox.askyesno("Confirmar", "Deseja anular esta proforma?"):
            return

        motivo = simpledialog.askstring("Motivo", "Motivo da anulacao:", parent=janela)
        if not motivo:
            return

        anular_proforma(pid, motivo, utilizador_logado["id"], utilizador_logado["nome"])
        registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                            "ANULAR PROFORMA", f"Proforma ID {pid} | Motivo: {motivo}")
        messagebox.showinfo("Sucesso", "Proforma anulada.")
        carregar()

    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=10)

    estilo = {"font": ("Arial", 11, "bold"), "width": 18, "height": 2,
              "bd": 0, "cursor": "hand2", "fg": "white"}

    Button(frame_btn, text="Ver Detalhes", bg=COR_PRIMARIA,
           command=ver_proforma, **estilo).grid(row=0, column=0, padx=5)
    Button(frame_btn, text="Anular Proforma", bg=COR_PERIGO,
           command=anular, **estilo).grid(row=0, column=1, padx=5)
    Button(frame_btn, text="Actualizar", bg="#0891b2",
           command=carregar, **estilo).grid(row=0, column=2, padx=5)
    Button(frame_btn, text="Fechar", bg="#6b7280",
           command=janela.destroy, **estilo).grid(row=0, column=3, padx=5)


def ver_proforma_janela(proforma_id, utilizador_logado, callback_atualizar=None):
    """Mostra detalhes de uma proforma."""
    from database import (buscar_proforma_por_id, listar_itens_factura,
                            obter_empresa)

    p = buscar_proforma_por_id(proforma_id)
    if not p:
        messagebox.showerror("Erro", "Proforma nao encontrada.")
        return

    (pid, numero, serie, tipo, data, cli_nome, cli_nif, cli_end,
     subtotal, iva, total, estado, motivo, forma_pagamento,
     ref_multicaixa, validade) = p

    janela = Toplevel()
    janela.title(f"Proforma {numero}")
    janela.geometry("850x750")
    janela.configure(bg=COR_FUNDO)

    header = Frame(janela, bg=COR_VERDE, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text=f"FACTURA PROFORMA - {numero}",
          font=("Arial", 18, "bold"), bg=COR_VERDE, fg="white").pack(pady=(15, 0))
    Label(header, text=f"Data: {data}   |   Estado: {estado}   |   Validade: {validade}",
          font=("Arial", 10, "italic"), bg=COR_VERDE, fg="#dcfce7").pack()

    aviso = Frame(janela, bg="#fef3c7", highlightthickness=2,
                   highlightbackground=COR_LARANJA)
    aviso.pack(fill=X, padx=20, pady=10)
    Label(aviso, text="DOCUMENTO NAO FISCAL - Valido por 7 dias",
          font=("Arial", 12, "bold"),
          bg="#fef3c7", fg="#92400e").pack(pady=10)

    if estado == "ANULADA":
        Label(janela, text=f"ANULADA - Motivo: {motivo}",
              font=("Arial", 12, "bold"),
              bg="#fee2e2", fg=COR_PERIGO).pack(fill=X, pady=5)

    emp = obter_empresa()
    if emp:
        emp_card = Frame(janela, bg=COR_CARD, highlightthickness=1,
                          highlightbackground="#fde68a")
        emp_card.pack(fill=X, padx=20, pady=10)
        Label(emp_card, text=emp[1], font=("Arial", 13, "bold"),
              bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15, pady=(10, 2))
        Label(emp_card, text=f"NIF: {emp[2] or '-'}",
              font=("Arial", 10), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15)
        Label(emp_card, text=f"{emp[3] or ''} | Tel: {emp[4] or ''}",
              font=("Arial", 10), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15, pady=(0, 10))

    cli_card = Frame(janela, bg=COR_CARD, highlightthickness=1,
                      highlightbackground="#fde68a")
    cli_card.pack(fill=X, padx=20, pady=5)
    Label(cli_card, text="Cliente:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15, pady=(10, 2))
    Label(cli_card, text=cli_nome or "Consumidor Final",
          font=("Arial", 11), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15)
    Label(cli_card, text=f"NIF: {cli_nif or '-'} | {cli_end or ''}",
          font=("Arial", 10), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, padx=15, pady=(0, 5))

    Label(janela, text="Itens da Proforma:",
          font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, padx=25, pady=(15, 5))

    frame_it = Frame(janela, bg=COR_FUNDO)
    frame_it.pack(fill=BOTH, expand=True, padx=20, pady=5)

    colunas = ("Descricao", "Qtd", "Preco", "IVA", "Valor IVA", "Subtotal")
    tree = ttk.Treeview(frame_it, columns=colunas, show="headings", height=8)
    for col in colunas:
        tree.heading(col, text=col)
    tree.column("Descricao", width=250)
    tree.column("Qtd", width=60)
    tree.column("Preco", width=110)
    tree.column("IVA", width=70)
    tree.column("Valor IVA", width=90)
    tree.column("Subtotal", width=110)
    tree.pack(fill=BOTH, expand=True)

    for item in listar_itens_factura(proforma_id):
        desc, qtd, preco, isento, taxa, valor_iva, sub = item
        iva_txt = "Isento" if isento else f"{int(taxa*100)}%"
        tree.insert("", END, values=(desc, qtd, formatar_kz(preco),
                                       iva_txt, formatar_kz(valor_iva),
                                       formatar_kz(sub)))

    tot_frame = Frame(janela, bg=COR_CARD, highlightthickness=2,
                       highlightbackground=COR_PRIMARIA)
    tot_frame.pack(fill=X, padx=20, pady=15)

    Label(tot_frame, text=f"Subtotal: {formatar_kz(subtotal)}",
          font=("Arial", 11), bg=COR_CARD, fg=COR_TEXTO).pack(anchor=E, padx=20, pady=(10, 2))
    Label(tot_frame, text=f"IVA: {formatar_kz(iva)}",
          font=("Arial", 11, "bold"), bg=COR_CARD, fg=COR_IVA).pack(anchor=E, padx=20, pady=2)
    Label(tot_frame, text=f"TOTAL: {formatar_kz(total)}",
          font=("Arial", 16, "bold"), bg=COR_CARD, fg=COR_PRIMARIA).pack(anchor=E, padx=20, pady=(5, 15))

    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=10)

    def gerar_pdf_prof():
        try:
            from impressao import gerar_pdf_proforma
            caminho, erro = gerar_pdf_proforma(proforma_id, formato="A4")
            if erro:
                messagebox.showerror("Erro", erro)
                return
            import os
            if os.path.exists(caminho):
                os.startfile(caminho)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")

    Button(frame_btn, text="Gerar PDF", font=("Arial", 11, "bold"),
           bg="#7c3aed", fg="white", width=18, height=2, bd=0, cursor="hand2",
           command=gerar_pdf_prof).pack(side=LEFT, padx=5)

    Button(frame_btn, text="Fechar", font=("Arial", 11),
           bg="#6b7280", fg="white", width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=5)


# ============================================================
# ============ EXPORTAR SAF-T (AO) ===========================
# ============================================================

def exportar_saft_janela(utilizador_logado, parent):
    """Janela para exportar SAF-T (AO)."""
    from datetime import datetime as _dt

    janela = Toplevel(parent)
    janela.title("Exportar SAF-T (AO)")
    janela.geometry("550x500")
    janela.configure(bg=COR_FUNDO)
    janela.transient(parent)
    janela.grab_set()

    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 550) // 2
    y = (janela.winfo_screenheight() - 500) // 2
    janela.geometry(f"550x500+{x}+{y}")

    header = Frame(janela, bg=COR_PRIMARIA, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="📄 Exportar SAF-T (AO)",
          font=("Arial", 16, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=20)

    Label(janela,
          text="Ficheiro XML com todas as facturas do período.\n"
               "Serve para auditoria fiscal e entrega à AGT.",
          font=("Arial", 10, "italic"),
          bg=COR_FUNDO, fg=COR_TEXTO,
          justify=CENTER).pack(pady=(15, 10))

    card = Frame(janela, bg=COR_CARD, highlightthickness=1,
                  highlightbackground="#fde68a")
    card.pack(fill=X, padx=25, pady=10)

    frame = Frame(card, bg=COR_CARD)
    frame.pack(padx=20, pady=20, fill=X)

    hoje = _dt.now()
    primeiro_dia = hoje.replace(day=1)

    Label(frame, text="Data início:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
    entry_ini = Entry(frame, font=("Arial", 11), bd=1, relief=SOLID)
    entry_ini.insert(0, primeiro_dia.strftime("%Y-%m-%d"))
    entry_ini.pack(fill=X, ipady=6)

    Label(frame, text="Data fim:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
    entry_fim = Entry(frame, font=("Arial", 11), bd=1, relief=SOLID)
    entry_fim.insert(0, hoje.strftime("%Y-%m-%d"))
    entry_fim.pack(fill=X, ipady=6)

    Label(frame, text="(Formato: AAAA-MM-DD)",
          font=("Arial", 9, "italic"),
          bg=COR_CARD, fg="#6b7280").pack(anchor=W, pady=(3, 10))

    msg_var = StringVar()
    Label(janela, textvariable=msg_var, font=("Arial", 10),
          bg=COR_FUNDO, fg=COR_PERIGO, wraplength=500).pack(pady=5)

    def exportar():
        try:
            d_ini = entry_ini.get().strip()
            d_fim = entry_fim.get().strip()

            _dt.strptime(d_ini, "%Y-%m-%d")
            _dt.strptime(d_fim, "%Y-%m-%d")

            from saft_ao import exportar_saft

            msg_var.set("A gerar ficheiro...")
            janela.update()

            caminho, erro = exportar_saft(d_ini, d_fim)

            if erro:
                msg_var.set(f"❌ Erro: {erro}")
                return

            registar_auditoria(
                utilizador_logado["id"],
                utilizador_logado["nome"],
                "EXPORTAR SAF-T",
                f"Período: {d_ini} a {d_fim} | Ficheiro: {caminho}"
            )

            msg_var.set(f"✅ SAF-T gerado com sucesso!")
            messagebox.showinfo("Sucesso",
                f"SAF-T (AO) gerado com sucesso!\n\n"
                f"Período: {d_ini} a {d_fim}\n\n"
                f"Ficheiro: {caminho}\n\n"
                f"Deseja abrir a pasta?")

            import os
            pasta = os.path.dirname(caminho) or "saft"
            try:
                os.startfile(os.path.abspath(pasta))
            except Exception:
                pass

            janela.destroy()

        except ValueError:
            msg_var.set("❌ Data inválida. Use formato AAAA-MM-DD")
        except Exception as e:
            msg_var.set(f"❌ Erro: {e}")

    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=15)

    Button(frame_btn, text="📄 Exportar",
           font=("Arial", 12, "bold"),
           bg=COR_PRIMARIA, fg="white",
           width=18, height=2, bd=0, cursor="hand2",
           command=exportar).pack(side=LEFT, padx=5)

    Button(frame_btn, text="❌ Cancelar",
           font=("Arial", 11),
           bg="#6b7280", fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=5)

    

# ============================================================
# ============ CONFIGURACAO AGT ==============================
# ============================================================

def abrir_config_agt(utilizador_logado, parent):
    """Janela de Configuração AGT — número de validação + chave RSA."""
    
    # ─── VERIFICACAO DE SEGURANCA ───
    if utilizador_logado.get("perfil") != "admin":
        messagebox.showerror(
            "Acesso Negado",
            "Apenas o administrador pode aceder a Configuracao AGT.\n\n"
            "Esta tentativa foi registada em auditoria."
        )
        try:
            from database import registar_auditoria
            registar_auditoria(
                utilizador_logado.get("id", 0),
                utilizador_logado.get("nome", "?"),
                "TENTATIVA AGT BLOQUEADA",
                f"Perfil: {utilizador_logado.get('perfil', '?')}"
            )
        except Exception:
            pass
        return

    from database import (obter_config_agt, guardar_config_agt,
                            desactivar_config_agt, tem_validacao_agt)

    janela = Toplevel(parent)
    janela.title("Configuração AGT")    
    janela.geometry("650x700")
    janela.configure(bg=COR_FUNDO)
    janela.transient(parent)
    janela.grab_set()

    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 650) // 2
    y = (janela.winfo_screenheight() - 700) // 2
    janela.geometry(f"650x700+{x}+{y}")

    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="🔐 Configuração AGT",
          font=("Arial", 16, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)

    Label(janela,
          text="Coloca aqui os dados que a AGT fornece após aprovar o software.",
          font=("Arial", 10, "italic"),
          bg=COR_FUNDO, fg="#6b7280",
          justify=CENTER).pack(pady=(10, 5))

    # ─── Estado actual ───
    cfg = obter_config_agt()
    estado_frame = Frame(janela, bg=COR_CARD, highlightthickness=2,
    highlightbackground=COR_VERDE if tem_validacao_agt() else COR_ALERTA)
    estado_frame.pack(fill=X, padx=20, pady=10)

    if tem_validacao_agt():
        Label(estado_frame, text="✅ SOFTWARE VALIDADO PELA AGT",
              font=("Arial", 12, "bold"),
              bg=COR_CARD, fg=COR_VERDE).pack(pady=(12, 5))
        Label(estado_frame,
              text=f"Número: {cfg['numero_validacao']}",
              font=("Arial", 11),
              bg=COR_CARD, fg=COR_TEXTO).pack()
        Label(estado_frame,
              text=f"Activado em: {cfg['data_activacao']} por {cfg['ativado_por']}",
              font=("Arial", 9, "italic"),
              bg=COR_CARD, fg="#6b7280").pack(pady=(2, 12))
    else:
        Label(estado_frame, text="⏳ SOFTWARE AINDA NÃO VALIDADO",
              font=("Arial", 12, "bold"),
              bg=COR_CARD, fg=COR_ALERTA).pack(pady=(12, 5))
        Label(estado_frame,
              text="As facturas mostram o aviso 'DOCUMENTO LOCAL - NAO VALIDADO PELA AGT'.",
              font=("Arial", 9, "italic"),
              bg=COR_CARD, fg="#6b7280").pack(pady=(2, 12))

    # ─── Formulário ───
    card = Frame(janela, bg=COR_CARD, highlightthickness=1,
                  highlightbackground="#fde68a")
    card.pack(fill=X, padx=20, pady=10)

    frame = Frame(card, bg=COR_CARD)
    frame.pack(padx=20, pady=20, fill=X)

    Label(frame, text="Número de Validação AGT: *",
          font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))

    entry_numero = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
    if cfg and cfg.get("numero_validacao"):
        entry_numero.insert(0, cfg["numero_validacao"])
    entry_numero.pack(fill=X, ipady=6)

    Label(frame,
          text="Exemplo: 1234/AGT/2026",
          font=("Arial", 9, "italic"),
          bg=COR_CARD, fg="#6b7280").pack(anchor=W, pady=(3, 10))

    Label(frame, text="Ficheiro da Chave RSA (opcional):",
          font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))

    chave_var = StringVar(value=cfg["chave_rsa_path"] if cfg and cfg.get("chave_rsa_path") else "(nenhuma chave carregada)")
    Label(frame, textvariable=chave_var,
          font=("Arial", 9),
          bg=COR_CARD, fg="#6b7280",
          wraplength=550, justify=LEFT).pack(anchor=W, pady=(2, 5))

    chave_selecionada = {"path": cfg["chave_rsa_path"] if cfg else None}

    def escolher_chave():
        caminho = filedialog.askopenfilename(
            title="Escolher Chave RSA",
            filetypes=[("Chaves PEM", "*.pem *.key"), ("Todos", "*.*")]
        )
        if caminho:
            chave_selecionada["path"] = caminho
            chave_var.set(caminho)

    Button(frame, text="📁 Escolher Chave RSA",
           font=("Arial", 10, "bold"),
           bg="#0891b2", fg="white",
           width=25, height=2, bd=0, cursor="hand2",
           command=escolher_chave).pack(anchor=W, pady=5)

    Label(frame,
          text="(A AGT fornece este ficheiro quando o software é certificado)",
          font=("Arial", 9, "italic"),
          bg=COR_CARD, fg="#6b7280").pack(anchor=W, pady=(0, 10))

    Label(frame, text="Observações:",
          font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
    entry_obs = Entry(frame, font=("Arial", 11), bd=1, relief=SOLID)
    if cfg and cfg.get("observacoes"):
        entry_obs.insert(0, cfg["observacoes"])
    entry_obs.pack(fill=X, ipady=6)

    msg_var = StringVar()
    Label(janela, textvariable=msg_var, font=("Arial", 10),
          bg=COR_FUNDO, fg=COR_PERIGO, wraplength=550).pack(pady=5)

    # ─── Botões ───
    def aplicar():
        numero = entry_numero.get().strip()
        if not numero:
            msg_var.set("❌ O número de validação é obrigatório")
            return

        obs = entry_obs.get().strip()

        try:
            guardar_config_agt(
                numero_validacao=numero,
                chave_rsa_path=chave_selecionada["path"],
                ativado_por=utilizador_logado["nome"],
                observacoes=obs,
            )
            registar_auditoria(
                utilizador_logado["id"],
                utilizador_logado["nome"],
                "CONFIG AGT",
                f"Validação activada: {numero}"
            )
            messagebox.showinfo("Sucesso",
                f"✅ Configuração AGT aplicada!\n\n"
                f"Número: {numero}\n\n"
                f"A partir de agora, as facturas mostram:\n"
                f"'Processado por programa validado n.º {numero}'")
            janela.destroy()

            # Abrir novamente para mostrar estado actualizado
            abrir_config_agt(utilizador_logado, parent)

        except Exception as e:
            msg_var.set(f"❌ Erro: {e}")

    def desactivar():
        if not messagebox.askyesno("Confirmar",
            "Desactivar a validação AGT?\n\n"
            "As facturas voltam a mostrar o aviso temporário."):
            return
        try:
            desactivar_config_agt()
            registar_auditoria(
                utilizador_logado["id"],
                utilizador_logado["nome"],
                "DESACTIVAR AGT",
                "Configuração AGT desactivada"
            )
            messagebox.showinfo("Sucesso", "Validação AGT desactivada.")
            janela.destroy()
            abrir_config_agt(utilizador_logado, parent)
        except Exception as e:
            msg_var.set(f"❌ Erro: {e}")

    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=15)

    Button(frame_btn, text="💾 Aplicar Configuração",
           font=("Arial", 12, "bold"),
           bg=COR_VERDE, fg="white",
           width=22, height=2, bd=0, cursor="hand2",
           command=aplicar).pack(side=LEFT, padx=5)

    if tem_validacao_agt():
        Button(frame_btn, text="⏹️ Desactivar",
               font=("Arial", 11),
               bg=COR_PERIGO, fg="white",
               width=15, height=2, bd=0, cursor="hand2",
               command=desactivar).pack(side=LEFT, padx=5)

    Button(frame_btn, text="❌ Fechar",
           font=("Arial", 11),
           bg="#6b7280", fg="white",
           width=12, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=5)