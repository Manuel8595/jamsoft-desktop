from tkinter import *
from tkinter import messagebox, ttk
from database import (caixa_aberto, abrir_caixa, fechar_caixa, registar_movimento_caixa,
                       atualizar_totais_caixa, listar_caixas, listar_movimentos_caixa,
                       registar_auditoria, autenticar, conectar,
                       proximo_numero_saida, proximo_numero_entrada,
                       registar_movimento_caixa_completo)
from moeda import formatar_kz
from datetime import datetime

COR_FUNDO = "#ecfeff"
COR_PRIMARIA = "#0891b2"
COR_TEXTO = "#164e63"
COR_PERIGO = "#dc2626"
COR_HEADER = "#0e7490"
COR_CARD = "#ffffff"
COR_VERDE = "#16a34a"
COR_ALERTA = "#f97316"


# ============================================================
# ============ MENU PRINCIPAL ================================
# ============================================================

def abrir_caixa_menu(utilizador_logado):
    janela = Toplevel()
    janela.title("JAM Soft - Caixa")
    janela.geometry("900x700")
    janela.configure(bg=COR_FUNDO)

    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Modulo de Caixa", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)

    cx = caixa_aberto()

    if cx is None:
        card_status = Frame(janela, bg=COR_CARD, highlightthickness=2,
                             highlightbackground=COR_PERIGO)
        card_status.pack(fill=X, padx=20, pady=20)
        Label(card_status, text="CAIXA FECHADO", font=("Arial", 16, "bold"),
              bg=COR_CARD, fg=COR_PERIGO).pack(pady=(20, 5))
        Label(card_status,
              text="O caixa esta fechado. E necessario abrir o caixa para comecar a operar.",
              font=("Arial", 11), bg=COR_CARD, fg=COR_TEXTO).pack(pady=(0, 20))
        Button(janela, text="Abrir Caixa", font=("Arial", 14, "bold"),
               bg=COR_VERDE, fg="white", width=25, height=3, bd=0, cursor="hand2",
               command=lambda: abrir_caixa_janela(utilizador_logado, janela)
               ).pack(pady=10)
    else:
        cx_id, data_abertura, user_nome, valor_inicial = cx

        card_status = Frame(janela, bg=COR_CARD, highlightthickness=2,
                             highlightbackground=COR_VERDE)
        card_status.pack(fill=X, padx=20, pady=20)
        Label(card_status, text="CAIXA ABERTO", font=("Arial", 16, "bold"),
              bg=COR_CARD, fg=COR_VERDE).pack(pady=(20, 5))
        Label(card_status, text=f"Aberto por: {user_nome}",
              font=("Arial", 11), bg=COR_CARD, fg=COR_TEXTO).pack()
        Label(card_status, text=f"Data: {data_abertura}",
              font=("Arial", 11), bg=COR_CARD, fg=COR_TEXTO).pack()
        Label(card_status, text=f"Valor inicial: {formatar_kz(valor_inicial)}",
              font=("Arial", 11, "bold"), bg=COR_CARD, fg=COR_TEXTO
              ).pack(pady=(5, 15))

        dados = atualizar_totais_caixa(cx_id)

        totais = Frame(card_status, bg=COR_CARD)
        totais.pack(pady=(0, 20))

        Label(totais, text="Vendas (Dinheiro):", font=("Arial", 10),
              bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=0, sticky=W, padx=10, pady=2)
        Label(totais, text=formatar_kz(dados["total_vendas"]),
              font=("Arial", 10, "bold"),
              bg=COR_CARD, fg=COR_VERDE).grid(row=0, column=1, sticky=E, padx=10, pady=2)
        Label(totais, text="Reforcos (+):", font=("Arial", 10),
              bg=COR_CARD, fg=COR_TEXTO).grid(row=1, column=0, sticky=W, padx=10, pady=2)
        Label(totais, text=formatar_kz(dados["total_reforcos"]),
              font=("Arial", 10, "bold"),
              bg=COR_CARD, fg=COR_VERDE).grid(row=1, column=1, sticky=E, padx=10, pady=2)
        Label(totais, text="Sangrias (-):", font=("Arial", 10),
              bg=COR_CARD, fg=COR_TEXTO).grid(row=2, column=0, sticky=W, padx=10, pady=2)
        Label(totais, text=formatar_kz(dados["total_sangrias"]),
              font=("Arial", 10, "bold"),
              bg=COR_CARD, fg=COR_PERIGO).grid(row=2, column=1, sticky=E, padx=10, pady=2)
        Label(totais, text="Esperado em Caixa:", font=("Arial", 11, "bold"),
              bg=COR_CARD, fg=COR_TEXTO).grid(row=3, column=0, sticky=W, padx=10, pady=(8, 2))
        Label(totais, text=formatar_kz(dados["valor_esperado"]),
              font=("Arial", 13, "bold"),
              bg=COR_CARD, fg=COR_PRIMARIA).grid(row=3, column=1, sticky=E, padx=10, pady=(8, 2))

        frame_botoes = Frame(janela, bg=COR_FUNDO)
        frame_botoes.pack(pady=20)

        estilo = {"font": ("Arial", 11, "bold"), "width": 22, "height": 2,
                  "bd": 0, "cursor": "hand2", "fg": "white"}

        Button(frame_botoes, text="Saida de Caixa", bg=COR_PERIGO,
               command=lambda: saida_caixa(cx_id, utilizador_logado, janela),
               **estilo).grid(row=0, column=0, padx=5, pady=5)

        Button(frame_botoes, text="Entrada de Caixa", bg=COR_VERDE,
               command=lambda: entrada_caixa(cx_id, utilizador_logado, janela),
               **estilo).grid(row=0, column=1, padx=5, pady=5)

        Button(frame_botoes, text="Ver Movimentos", bg="#7c3aed",
               command=lambda: ver_movimentos(cx_id),
               **estilo).grid(row=1, column=0, padx=5, pady=5)

        Button(frame_botoes, text="Fechar Caixa", bg="#be185d",
               command=lambda: fechar_caixa_janela(cx_id, utilizador_logado, janela),
               **estilo).grid(row=1, column=1, padx=5, pady=5)

    Button(janela, text="Historico de Caixas", font=("Arial", 11, "bold"),
           bg="#4b5563", fg="white", width=25, height=2, bd=0, cursor="hand2",
           command=abrir_historico_caixas).pack(pady=10)


# ============================================================
# ============ ABRIR CAIXA ==================================
# ============================================================

def abrir_caixa_janela(utilizador_logado, parent):
    janela = Toplevel(parent)
    janela.title("Abrir Caixa")
    janela.geometry("450x400")
    janela.configure(bg=COR_FUNDO)

    Label(janela, text="Abrir Caixa", font=("Arial", 16, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=20)
    Label(janela, text="Valor inicial em caixa (Kz):",
          font=("Arial", 11, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(10, 5))

    entry_valor = Entry(janela, font=("Arial", 16), width=15,
                         justify=CENTER, bd=1, relief=SOLID)
    entry_valor.pack(pady=10, ipady=8)
    entry_valor.insert(0, "0")
    entry_valor.focus()

    Label(janela, text="(Dinheiro que tens no caixa para troco)",
          font=("Arial", 9, "italic"), bg=COR_FUNDO, fg="#6b7280").pack()

    def confirmar():
        try:
            valor_txt = entry_valor.get().replace(".", "").replace(",", ".")
            valor = float(valor_txt)
            if valor < 0:
                messagebox.showwarning("Aviso", "O valor deve ser positivo.")
                return
            cx_id = abrir_caixa(utilizador_logado["id"], utilizador_logado["nome"], valor)
            registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                "ABERTURA CAIXA",
                                f"Caixa #{cx_id} | Inicial: {formatar_kz(valor)}")
            messagebox.showinfo("Sucesso", f"Caixa aberto com {formatar_kz(valor)}!")
            janela.destroy()
            parent.destroy()
            abrir_caixa_menu(utilizador_logado)
        except ValueError:
            messagebox.showerror("Erro", "Digite um valor valido.")

    entry_valor.bind('<Return>', lambda e: confirmar())

    Button(janela, text="Confirmar Abertura", font=("Arial", 12, "bold"),
           bg=COR_VERDE, fg="white", width=22, height=2, bd=0, cursor="hand2",
           command=confirmar).pack(pady=20)


# ============================================================
# ============ SAIDA DE CAIXA (DESPESA) =====================
# ============================================================

def saida_caixa(cx_id, utilizador_logado, parent):
    janela = Toplevel(parent)
    janela.title("Saida de Caixa")
    janela.geometry("550x700")
    janela.configure(bg=COR_FUNDO)
    janela.transient(parent)
    janela.grab_set()
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 550) // 2
    y = (janela.winfo_screenheight() - 700) // 2
    janela.geometry(f"550x700+{x}+{y}")

    header = Frame(janela, bg=COR_PERIGO, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="SAIDA DE CAIXA", font=("Arial", 18, "bold"),
          bg=COR_PERIGO, fg="white").pack(pady=(15, 0))
    Label(header, text="Registar saida de dinheiro (despesa)",
          font=("Arial", 10, "italic"),
          bg=COR_PERIGO, fg="#ffe4e6").pack()

    body = Frame(janela, bg=COR_FUNDO)
    body.pack(fill=BOTH, expand=True, padx=30, pady=20)

    Label(body, text="Valor (Kz):", font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(10, 5))
    entry_valor = Entry(body, font=("Arial", 16), width=20,
                         justify=CENTER, bd=2, relief=SOLID)
    entry_valor.pack(pady=5, ipady=8)
    entry_valor.focus()

    Label(body, text="Categoria:", font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(15, 5))
    CATEGORIAS_SAIDA = ["Compra de material", "Agua/Luz/Internet",
                        "Combustivel", "Pagamento fornecedor",
                        "Manutencao", "Outro"]
    categoria_var = StringVar(value=CATEGORIAS_SAIDA[0])
    ttk.Combobox(body, textvariable=categoria_var, values=CATEGORIAS_SAIDA,
                  state="readonly", font=("Arial", 11), width=40).pack(pady=5, ipady=4)

    Label(body, text="Motivo / Descricao: (obrigatorio)",
          font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(15, 5))
    entry_desc = Entry(body, font=("Arial", 11), width=45, bd=2, relief=SOLID)
    entry_desc.pack(pady=5, ipady=6)

    Label(body, text="Sera necessaria autorizacao do GERENTE",
          font=("Arial", 10, "bold"), bg=COR_FUNDO, fg=COR_ALERTA).pack(pady=(15, 5))

    def confirmar():
        try:
            valor_txt = entry_valor.get().replace(".", "").replace(",", ".")
            valor = float(valor_txt)
            if valor <= 0:
                messagebox.showwarning("Aviso", "O valor deve ser positivo.")
                return
            descricao = entry_desc.get().strip()
            if not descricao:
                messagebox.showwarning("Aviso", "Escreva o motivo da saida.")
                return

            categoria = categoria_var.get()
            texto_desc = f"[{categoria}] {descricao}"

            ok, nome_gerente = _pedir_autorizacao_gerente(
                parent,
                f"Saida de {formatar_kz(valor)}",
                utilizador_logado
            )
            if not ok:
                return

            numero_doc = proximo_numero_saida()

            mov_id = registar_movimento_caixa_completo(
                cx_id, "SAIDA", valor, texto_desc,
                utilizador_logado["id"], utilizador_logado["nome"],
                nome_gerente, numero_doc
            )

            registar_auditoria(
                utilizador_logado["id"], utilizador_logado["nome"],
                "SAIDA CAIXA",
                f"Doc {numero_doc} | {formatar_kz(valor)} | {categoria} | "
                f"Autorizado por: {nome_gerente}"
            )

            _gerar_comprovante(mov_id, utilizador_logado)

            messagebox.showinfo("Sucesso",
                f"Saida registada!\n\n"
                f"Documento: {numero_doc}\n"
                f"Valor: {formatar_kz(valor)}\n"
                f"Categoria: {categoria}\n"
                f"Autorizado por: {nome_gerente}")

            janela.destroy()
            parent.destroy()
            abrir_caixa_menu(utilizador_logado)

        except ValueError:
            messagebox.showerror("Erro", "Digite um valor valido.")

    entry_valor.bind('<Return>', lambda e: entry_desc.focus())
    entry_desc.bind('<Return>', lambda e: confirmar())

    frame_btn = Frame(body, bg=COR_FUNDO)
    frame_btn.pack(pady=25)
    Button(frame_btn, text="Confirmar Saida",
           font=("Arial", 13, "bold"), bg=COR_PERIGO, fg="white",
           width=20, height=2, bd=0, cursor="hand2",
           command=confirmar).pack(side=LEFT, padx=5)
    Button(frame_btn, text="Cancelar", font=("Arial", 11),
           bg="#6b7280", fg="white", width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=5)


# ============================================================
# ============ ENTRADA DE CAIXA =============================
# ============================================================

def entrada_caixa(cx_id, utilizador_logado, parent):
    janela = Toplevel(parent)
    janela.title("Entrada de Caixa")
    janela.geometry("550x680")
    janela.configure(bg=COR_FUNDO)
    janela.transient(parent)
    janela.grab_set()
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 550) // 2
    y = (janela.winfo_screenheight() - 680) // 2
    janela.geometry(f"550x680+{x}+{y}")

    header = Frame(janela, bg=COR_VERDE, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="ENTRADA DE CAIXA", font=("Arial", 18, "bold"),
          bg=COR_VERDE, fg="white").pack(pady=(15, 0))
    Label(header, text="Registar entrada de dinheiro",
          font=("Arial", 10, "italic"),
          bg=COR_VERDE, fg="#dcfce7").pack()

    body = Frame(janela, bg=COR_FUNDO)
    body.pack(fill=BOTH, expand=True, padx=30, pady=20)

    Label(body, text="Valor (Kz):", font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(10, 5))
    entry_valor = Entry(body, font=("Arial", 16), width=20,
                         justify=CENTER, bd=2, relief=SOLID)
    entry_valor.pack(pady=5, ipady=8)
    entry_valor.focus()

    Label(body, text="Categoria:", font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(15, 5))
    CATEGORIAS_ENTRADA = ["Aporte do gerente", "Devolucao de fornecedor",
                          "Troco extra", "Venda externa", "Outro"]
    categoria_var = StringVar(value=CATEGORIAS_ENTRADA[0])
    ttk.Combobox(body, textvariable=categoria_var, values=CATEGORIAS_ENTRADA,
                  state="readonly", font=("Arial", 11), width=40).pack(pady=5, ipady=4)

    Label(body, text="Motivo / Descricao: (obrigatorio)",
          font=("Arial", 12, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(15, 5))
    entry_desc = Entry(body, font=("Arial", 11), width=45, bd=2, relief=SOLID)
    entry_desc.pack(pady=5, ipady=6)

    Label(body, text="Sera necessaria autorizacao do GERENTE",
          font=("Arial", 10, "bold"), bg=COR_FUNDO, fg=COR_ALERTA).pack(pady=(15, 5))

    def confirmar():
        try:
            valor_txt = entry_valor.get().replace(".", "").replace(",", ".")
            valor = float(valor_txt)
            if valor <= 0:
                messagebox.showwarning("Aviso", "O valor deve ser positivo.")
                return
            descricao = entry_desc.get().strip()
            if not descricao:
                messagebox.showwarning("Aviso", "Escreva o motivo da entrada.")
                return

            categoria = categoria_var.get()
            texto_desc = f"[{categoria}] {descricao}"

            ok, nome_gerente = _pedir_autorizacao_gerente(
                parent,
                f"Entrada de {formatar_kz(valor)}",
                utilizador_logado
            )
            if not ok:
                return

            numero_doc = proximo_numero_entrada()

            mov_id = registar_movimento_caixa_completo(
                cx_id, "ENTRADA", valor, texto_desc,
                utilizador_logado["id"], utilizador_logado["nome"],
                nome_gerente, numero_doc
            )

            registar_auditoria(
                utilizador_logado["id"], utilizador_logado["nome"],
                "ENTRADA CAIXA",
                f"Doc {numero_doc} | {formatar_kz(valor)} | {categoria} | "
                f"Autorizado por: {nome_gerente}"
            )

            _gerar_comprovante(mov_id, utilizador_logado)

            messagebox.showinfo("Sucesso",
                f"Entrada registada!\n\n"
                f"Documento: {numero_doc}\n"
                f"Valor: {formatar_kz(valor)}\n"
                f"Categoria: {categoria}\n"
                f"Autorizado por: {nome_gerente}")

            janela.destroy()
            parent.destroy()
            abrir_caixa_menu(utilizador_logado)

        except ValueError:
            messagebox.showerror("Erro", "Digite um valor valido.")

    entry_valor.bind('<Return>', lambda e: entry_desc.focus())
    entry_desc.bind('<Return>', lambda e: confirmar())

    frame_btn = Frame(body, bg=COR_FUNDO)
    frame_btn.pack(pady=25)
    Button(frame_btn, text="Confirmar Entrada",
           font=("Arial", 13, "bold"), bg=COR_VERDE, fg="white",
           width=20, height=2, bd=0, cursor="hand2",
           command=confirmar).pack(side=LEFT, padx=5)
    Button(frame_btn, text="Cancelar", font=("Arial", 11),
           bg="#6b7280", fg="white", width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=5)


# ============================================================
# ============ AUTORIZACAO DO GERENTE =======================
# ============================================================

def _pedir_autorizacao_gerente(parent, motivo, utilizador_logado):
    """Pede senha do gerente. Bloqueia se for o proprio utilizador."""
    resultado = {"ok": False, "nome": None}

    auth = Toplevel(parent)
    auth.title("Autorizacao do Gerente")
    auth.geometry("500x480")
    auth.configure(bg=COR_FUNDO)
    auth.transient(parent)
    auth.grab_set()
    auth.update_idletasks()
    x = (auth.winfo_screenwidth() - 500) // 2
    y = (auth.winfo_screenheight() - 480) // 2
    auth.geometry(f"500x480+{x}+{y}")

    header = Frame(auth, bg="#ea580c", height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="AUTORIZACAO NECESSARIA",
          font=("Arial", 15, "bold"), bg="#ea580c", fg="white").pack(pady=20)

    Label(auth, text=motivo, font=("Arial", 11),
          bg=COR_FUNDO, fg=COR_TEXTO,
          wraplength=460, justify=CENTER).pack(pady=(15, 5), padx=20)

    Label(auth, text="(O gerente NAO pode autorizar a si proprio)",
          font=("Arial", 9, "italic"),
          bg=COR_FUNDO, fg="#6b7280").pack(pady=(0, 15))

    card = Frame(auth, bg=COR_CARD, highlightthickness=1, highlightbackground="#334155")
    card.pack(padx=30, fill=X)
    frame = Frame(card, bg=COR_CARD)
    frame.pack(padx=20, pady=20, fill=X)

    Label(frame, text="Utilizador:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=0, sticky=W, padx=5, pady=8)
    e_user = Entry(frame, font=("Arial", 12), width=22, bd=1, relief=SOLID)
    e_user.grid(row=0, column=1, padx=5, pady=8, ipady=6)
    e_user.focus()

    Label(frame, text="Senha:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=1, column=0, sticky=W, padx=5, pady=8)
    e_pass = Entry(frame, font=("Arial", 12), width=22, bd=1, relief=SOLID, show="*")
    e_pass.grid(row=1, column=1, padx=5, pady=8, ipady=6)

    msg_var = StringVar()
    Label(auth, textvariable=msg_var, font=("Arial", 10),
          bg=COR_FUNDO, fg=COR_PERIGO).pack(pady=5)

    def confirmar_auth(event=None):
        u = e_user.get().strip().lower()
        p = e_pass.get()

        if not u or not p:
            msg_var.set("Preencha utilizador e senha")
            return

        if u == (utilizador_logado.get("username") or "").lower():
            msg_var.set("Nao pode autorizar a si proprio!")
            e_pass.delete(0, END)
            return

        try:
            sucesso, dados = autenticar(u, p)

            if sucesso and dados["perfil"] in ("admin", "gerente"):
                resultado["ok"] = True
                resultado["nome"] = dados["nome"]
                auth.destroy()
            elif sucesso:
                msg_var.set("Utilizador nao e gerente ou admin")
                e_pass.delete(0, END)
            else:
                msg_var.set("Credenciais invalidas")
                e_pass.delete(0, END)
        except Exception as e:
            msg_var.set(f"Erro: {e}")

    e_user.bind('<Return>', lambda e: e_pass.focus())
    e_pass.bind('<Return>', confirmar_auth)

    Button(auth, text="Autorizar",
           font=("Arial", 13, "bold"), bg=COR_VERDE, fg="white",
           width=25, height=2, bd=0, cursor="hand2",
           command=confirmar_auth).pack(pady=20)

    auth.wait_window()
    return resultado["ok"], resultado["nome"]


# ============================================================
# ============ GERAR COMPROVANTE PDF ========================
# ============================================================

def _gerar_comprovante(mov_id, utilizador_logado):
    """Gera comprovante PDF e guarda em relatorios arquivados."""
    try:
        from relatorio_movimento_caixa import gerar_comprovante_movimento
        from database import guardar_relatorio

        resultado = {"formato": None}

        fmt_win = Toplevel()
        fmt_win.title("Formato do Comprovante")
        fmt_win.geometry("500x400")
        fmt_win.configure(bg=COR_FUNDO)
        fmt_win.grab_set()

        fmt_win.update_idletasks()
        x = (fmt_win.winfo_screenwidth() - 500) // 2
        y = (fmt_win.winfo_screenheight() - 400) // 2
        fmt_win.geometry(f"500x400+{x}+{y}")

        Label(fmt_win, text="Formato do Comprovante",
              font=("Arial", 16, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=25)

        Label(fmt_win, text="Escolha o formato de impressao:",
              font=("Arial", 11),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=10)

        def escolher(fmt):
            resultado["formato"] = fmt
            fmt_win.destroy()

        Button(fmt_win, text="A4 (para arquivo)",
               font=("Arial", 12, "bold"),
               bg="#0891b2", fg="white",
               width=25, height=2, bd=0, cursor="hand2",
               command=lambda: escolher("A4")).pack(pady=10)

        Button(fmt_win, text="Termico 80mm",
               font=("Arial", 12, "bold"),
               bg=COR_VERDE, fg="white",
               width=25, height=2, bd=0, cursor="hand2",
               command=lambda: escolher("TERMICA")).pack(pady=10)

        fmt_win.wait_window()

        formato = resultado["formato"]
        if not formato:
            return

        caminho, erro = gerar_comprovante_movimento(mov_id, formato=formato)

        if erro:
            messagebox.showerror("Erro", erro)
            return

        try:
            guardar_relatorio(
                tipo="MOVIMENTO_CAIXA",
                referencia=f"MOV-{mov_id}",
                gerado_por=utilizador_logado["nome"],
                caminho_pdf=caminho
            )
        except Exception as e:
            print(f"[Comprovante] Aviso ao guardar: {e}")

        messagebox.showinfo("Comprovante Gerado",
            f"COMPROVANTE GERADO!\n\n"
            f"Ficheiro: {caminho}\n\n"
            f"IMPRIME PARA ASSINATURA!\n\n"
            f"(Operador + Gerente)")

        try:
            import os
            if os.path.exists(caminho):
                os.startfile(caminho)
        except Exception:
            pass

    except Exception as e:
        print(f"[Comprovante] Erro: {e}")


# ============================================================
# ============ VER MOVIMENTOS ===============================
# ============================================================

def ver_movimentos(cx_id):
    janela = Toplevel()
    janela.title("Movimentos do Caixa")
    janela.geometry("1000x500")
    janela.configure(bg=COR_FUNDO)

    Label(janela, text="Movimentos do Caixa", font=("Arial", 16, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=10)

    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(fill=BOTH, expand=True, padx=15, pady=10)

    colunas = ("Data", "Tipo", "Valor", "Descricao", "Utilizador")
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=180)
    tree.pack(fill=BOTH, expand=True)

    for m in listar_movimentos_caixa(cx_id):
        data, tipo, valor, desc, user = m
        tree.insert("", END, values=(data, tipo, formatar_kz(valor),
                                       desc or "-", user))


# ============================================================
# ============ FECHAR CAIXA =================================
# ============================================================

def fechar_caixa_janela(cx_id, utilizador_logado, parent):
    """Fecho de caixa com contagem de notas + TPA + senha gerente (2 colunas)."""

    from database import conectar, listar_movimentos_caixa

    dados = atualizar_totais_caixa(cx_id)
    esperado_cash = dados["valor_esperado"]
    esperado_tpa = dados.get("total_tpa", 0) or 0
    fundo_inicial = dados["valor_inicial"]

    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT data_abertura, utilizador_abertura_nome,
                   (SELECT COUNT(*) FROM vendas WHERE caixa_id = ?) as num_vendas,
                   (SELECT COALESCE(SUM(total), 0) FROM vendas WHERE caixa_id = ?) as total_vendas
            FROM caixas WHERE id = ?
        """, (cx_id, cx_id, cx_id))
        info_caixa = cur.fetchone()
        conn.close()
    except Exception:
        info_caixa = (None, "-", 0, 0)

    try:
        movimentos = listar_movimentos_caixa(cx_id) or []
        movimentos = list(movimentos)[-5:]
    except Exception:
        movimentos = []

    janela = Toplevel(parent)
    janela.title("Fechar Caixa - Contagem")
    janela.state("zoomed")
    janela.configure(bg=COR_FUNDO)
    janela.transient(parent)
    janela.grab_set()

    header = Frame(janela, bg="#be185d", height=60)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="FECHO DE CAIXA - CONTAGEM",
          font=("Segoe UI", 16, "bold"),
          bg="#be185d", fg="white").pack(pady=15)

    main = Frame(janela, bg=COR_FUNDO)
    main.pack(fill=BOTH, expand=True, padx=15, pady=10)

    col_esq = Frame(main, bg=COR_FUNDO)
    col_esq.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 8))

    col_dir = Frame(main, bg=COR_FUNDO)
    col_dir.pack(side=RIGHT, fill=BOTH, expand=True, padx=(8, 0))

    # ═══════════ COLUNA ESQUERDA ═══════════

    Label(col_esq, text="📊 RESUMO DO SISTEMA",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO, anchor=W).pack(fill=X)

    card_res = Frame(col_esq, bg=COR_CARD, highlightthickness=1,
                      highlightbackground="#cbd5e1")
    card_res.pack(fill=X, pady=(3, 8))

    def _linha(parent, label, valor, cor=COR_TEXTO):
        f = Frame(parent, bg=COR_CARD)
        f.pack(fill=X, padx=10, pady=1)
        Label(f, text=label, font=("Segoe UI", 9),
              bg=COR_CARD, fg="#64748b").pack(side=LEFT)
        Label(f, text=valor, font=("Segoe UI", 10, "bold"),
              bg=COR_CARD, fg=cor).pack(side=RIGHT)

    _linha(card_res, "Fundo inicial:", formatar_kz(fundo_inicial))
    _linha(card_res, "+ Vendas Dinheiro:",
           formatar_kz(dados["total_vendas"]), COR_VERDE)
    _linha(card_res, "+ Reforços:",
           formatar_kz(dados["total_reforcos"]), COR_VERDE)
    _linha(card_res, "- Sangrias:",
           formatar_kz(dados["total_sangrias"]), COR_PERIGO)
    _linha(card_res, "ESPERADO CASH:",
           formatar_kz(esperado_cash), COR_PRIMARIA)
    _linha(card_res, "ESPERADO TPA:",
           formatar_kz(esperado_tpa), "#0891b2")

    # CONTAGEM DE NOTAS
    Label(col_esq, text="💵 CONTAGEM DE DINHEIRO (CASH)",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO, anchor=W).pack(fill=X)

    card_notas = Frame(col_esq, bg=COR_CARD, highlightthickness=1,
                        highlightbackground="#cbd5e1")
    card_notas.pack(fill=X, pady=(3, 8))

    notas_esq = Frame(card_notas, bg=COR_CARD)
    notas_esq.pack(side=LEFT, fill=BOTH, expand=True, padx=8, pady=8)

    notas_dir = Frame(card_notas, bg=COR_CARD)
    notas_dir.pack(side=RIGHT, fill=BOTH, expand=True, padx=8, pady=8)

    NOTAS_ESQ = [5000, 2000, 1000, 500, 200]
    NOTAS_DIR = [100, 50, 20, 10]

    entries_notas = {}
    total_contado_var = StringVar(value="Kz 0,00")
    diff_cash_var = StringVar(value="—")

    def _atualizar_total_cash(*args):
        total = 0
        for nota, entry in entries_notas.items():
            try:
                qtd = int(entry.get() or 0)
                total += qtd * nota
            except ValueError:
                pass
        total_contado_var.set(formatar_kz(total))

        dif = total - esperado_cash
        if abs(dif) < 0.01:
            diff_cash_var.set("OK")
        elif dif > 0:
            diff_cash_var.set(f"SOBRA: +{formatar_kz(dif)}")
        else:
            diff_cash_var.set(f"FALTA: -{formatar_kz(abs(dif))}")

    def _criar_linha_nota(parent, nota):
        f = Frame(parent, bg=COR_CARD)
        f.pack(fill=X, pady=1)

        Label(f, text=f"Kz {nota:,.0f}".replace(",", "."),
              font=("Segoe UI", 9, "bold"),
              bg=COR_CARD, fg=COR_TEXTO, width=8, anchor=W).pack(side=LEFT)

        e = Entry(f, font=("Segoe UI", 10), width=6,
                   justify=CENTER, bd=1, relief=SOLID)
        e.pack(side=LEFT, padx=3, ipady=2)
        e.insert(0, "0")
        e.bind("<KeyRelease>", _atualizar_total_cash)
        entries_notas[nota] = e

        sub_var = StringVar(value="Kz 0,00")
        Label(f, textvariable=sub_var,
               font=("Segoe UI", 9, "bold"),
               bg=COR_CARD, fg=COR_PRIMARIA,
               width=12, anchor=E).pack(side=RIGHT)

        def _cb(nota_ref, entry_ref, sub_var_ref):
            def _fn(*args):
                try:
                    qtd = int(entry_ref.get() or 0)
                    sub_var_ref.set(formatar_kz(qtd * nota_ref))
                except ValueError:
                    sub_var_ref.set("Kz 0,00")
                _atualizar_total_cash()
            return _fn

        e.bind("<KeyRelease>", _cb(nota, e, sub_var), add="+")

    for n in NOTAS_ESQ:
        _criar_linha_nota(notas_esq, n)
    for n in NOTAS_DIR:
        _criar_linha_nota(notas_dir, n)

    total_frame = Frame(card_notas, bg="#f1f5f9")
    total_frame.pack(fill=X, padx=8, pady=(0, 8))

    Label(total_frame, text="TOTAL CASH:",
          font=("Segoe UI", 10, "bold"),
          bg="#f1f5f9", fg=COR_TEXTO).pack(side=LEFT, padx=8, pady=6)
    Label(total_frame, textvariable=total_contado_var,
          font=("Segoe UI", 12, "bold"),
          bg="#f1f5f9", fg=COR_PRIMARIA).pack(side=LEFT)

    Label(total_frame, text="  DIF:",
          font=("Segoe UI", 10, "bold"),
          bg="#f1f5f9", fg=COR_TEXTO).pack(side=LEFT, padx=(15, 3))
    diff_lbl = Label(total_frame, textvariable=diff_cash_var,
                      font=("Segoe UI", 10, "bold"),
                      bg="#f1f5f9", fg=COR_ALERTA)
    diff_lbl.pack(side=LEFT)

    def _colorir(*args):
        t = diff_cash_var.get()
        if "OK" in t:
            diff_lbl.config(fg=COR_VERDE)
        elif "SOBRA" in t:
            diff_lbl.config(fg=COR_ALERTA)
        else:
            diff_lbl.config(fg=COR_PERIGO)

    diff_cash_var.trace("w", _colorir)

    # TPA
    Label(col_esq, text="💳 CONTAGEM TPA (CARTAO)",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO, anchor=W).pack(fill=X)

    card_tpa = Frame(col_esq, bg=COR_CARD, highlightthickness=1,
                      highlightbackground="#cbd5e1")
    card_tpa.pack(fill=X, pady=(3, 8))

    f1 = Frame(card_tpa, bg=COR_CARD)
    f1.pack(fill=X, padx=10, pady=4)
    Label(f1, text="Nº talões:", font=("Segoe UI", 9, "bold"),
          bg=COR_CARD, fg=COR_TEXTO, width=10, anchor=W).pack(side=LEFT)
    entry_taloes = Entry(f1, font=("Segoe UI", 10), width=6,
                          justify=CENTER, bd=1, relief=SOLID)
    entry_taloes.pack(side=LEFT, padx=5, ipady=2)
    entry_taloes.insert(0, "0")

    Label(f1, text="  Valor:", font=("Segoe UI", 9, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=(10, 3))
    entry_tpa_valor = Entry(f1, font=("Segoe UI", 10), width=14,
                             justify=CENTER, bd=1, relief=SOLID)
    entry_tpa_valor.pack(side=LEFT, padx=3, ipady=2)

    diff_tpa_var = StringVar(value="—")

    def _calc_diff_tpa(*args):
        try:
            txt = entry_tpa_valor.get().replace(".", "").replace(",", ".")
            valor = float(txt or 0)
            dif = valor - esperado_tpa
            if abs(dif) < 0.01:
                diff_tpa_var.set("OK")
            elif dif > 0:
                diff_tpa_var.set(f"SOBRA: +{formatar_kz(dif)}")
            else:
                diff_tpa_var.set(f"FALTA: -{formatar_kz(abs(dif))}")
        except ValueError:
            diff_tpa_var.set("—")

    entry_tpa_valor.bind("<KeyRelease>", _calc_diff_tpa)

    f2 = Frame(card_tpa, bg=COR_CARD)
    f2.pack(fill=X, padx=10, pady=(0, 8))
    Label(f2, text=f"Esperado: {formatar_kz(esperado_tpa)}",
          font=("Segoe UI", 9), bg=COR_CARD, fg="#64748b").pack(side=LEFT)
    Label(f2, text="  Dif: ", font=("Segoe UI", 9, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT)
    Label(f2, textvariable=diff_tpa_var,
          font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_ALERTA).pack(side=LEFT)

    # DEPOSITO
    Label(col_esq, text="💰 VALOR A DEPOSITAR",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO, anchor=W).pack(fill=X)

    card_dep = Frame(col_esq, bg="#dcfce7", highlightthickness=1,
                      highlightbackground="#16a34a")
    card_dep.pack(fill=X, pady=(3, 8))

    valor_depositar_var = StringVar(value="Kz 0,00")

    def _calc_dep(*args):
        try:
            txt = total_contado_var.get().replace("Kz", "").replace(".", "").replace(",", ".").strip()
            total = float(txt or 0)
            dep = total - fundo_inicial
            valor_depositar_var.set(formatar_kz(dep) if dep > 0 else "Kz 0,00")
        except ValueError:
            valor_depositar_var.set("Kz 0,00")

    total_contado_var.trace("w", _calc_dep)

    f_dep = Frame(card_dep, bg="#dcfce7")
    f_dep.pack(fill=X, padx=10, pady=6)
    Label(f_dep, text="Total contado - Fundo:",
          font=("Segoe UI", 9), bg="#dcfce7", fg="#166534").pack(side=LEFT)
    Label(f_dep, textvariable=valor_depositar_var,
          font=("Segoe UI", 12, "bold"),
          bg="#dcfce7", fg=COR_VERDE).pack(side=RIGHT)

    # OBSERVAÇÕES
    Label(col_esq, text="📝 OBSERVAÇÕES (obrigatório se SOBRA):",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO, anchor=W).pack(fill=X)

    entry_obs = Entry(col_esq, font=("Segoe UI", 10),
                       bd=1, relief=SOLID)
    entry_obs.pack(fill=X, pady=3, ipady=5)

    frame_btn = Frame(col_esq, bg=COR_FUNDO)
    frame_btn.pack(fill=X, pady=10)

    # ═══════════ COLUNA DIREITA ═══════════

    Label(col_dir, text="🔵 PAINEL DE VALIDAÇÃO",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO, anchor=W).pack(fill=X)

    card_val = Frame(col_dir, bg=COR_CARD, highlightthickness=2,
                      highlightbackground=COR_PRIMARIA)
    card_val.pack(fill=X, pady=(3, 10))

    val_cash_var = StringVar(value="Esperando...")
    val_tpa_var = StringVar(value="Esperando...")

    def _atualizar_painel(*args):
        try:
            txt = total_contado_var.get().replace("Kz", "").replace(".", "").replace(",", ".").strip()
            cash = float(txt or 0)
            dif = cash - esperado_cash
            if abs(dif) < 0.01:
                val_cash_var.set(f"🟢 OK     (contado: {formatar_kz(cash)})")
            elif dif > 0:
                val_cash_var.set(f"🟡 SOBRA  +{formatar_kz(dif)}")
            else:
                val_cash_var.set(f"🔴 FALTA  -{formatar_kz(abs(dif))}")
        except Exception:
            val_cash_var.set("Esperando...")

        try:
            txt = entry_tpa_valor.get().replace(".", "").replace(",", ".")
            tpa = float(txt or 0)
            dif = tpa - esperado_tpa
            if abs(dif) < 0.01:
                val_tpa_var.set(f"🟢 OK     (contado: {formatar_kz(tpa)})")
            elif dif > 0:
                val_tpa_var.set(f"🟡 SOBRA  +{formatar_kz(dif)}")
            else:
                val_tpa_var.set(f"🔴 FALTA  -{formatar_kz(abs(dif))}")
        except Exception:
            val_tpa_var.set("Esperando...")

    total_contado_var.trace("w", _atualizar_painel)
    diff_tpa_var.trace("w", _atualizar_painel)

    f_cash = Frame(card_val, bg=COR_CARD)
    f_cash.pack(fill=X, padx=12, pady=(10, 5))
    Label(f_cash, text="💵 CASH:",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W)
    Label(f_cash, textvariable=val_cash_var,
          font=("Segoe UI", 12, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(3, 0))

    f_tpa = Frame(card_val, bg=COR_CARD)
    f_tpa.pack(fill=X, padx=12, pady=(5, 10))
    Label(f_tpa, text="💳 TPA:",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W)
    Label(f_tpa, textvariable=val_tpa_var,
          font=("Segoe UI", 12, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(3, 0))

    Label(col_dir, text="🏦 FUNDO AO GERENTE",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO, anchor=W).pack(fill=X)

    card_fundo = Frame(col_dir, bg="#fef3c7", highlightthickness=1,
                        highlightbackground="#f59e0b")
    card_fundo.pack(fill=X, pady=(3, 10))
    Label(card_fundo, text=formatar_kz(fundo_inicial),
          font=("Segoe UI", 14, "bold"),
          bg="#fef3c7", fg="#92400e").pack(pady=8)

    Label(col_dir, text=f"📋 MOVIMENTOS DO DIA ({len(movimentos)})",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO, anchor=W).pack(fill=X)

    card_mov = Frame(col_dir, bg=COR_CARD, highlightthickness=1,
                      highlightbackground="#cbd5e1")
    card_mov.pack(fill=X, pady=(3, 10))

    if movimentos:
        for m in movimentos:
            try:
                data_m, tipo_m, valor_m, desc_m, user_m = m[:5]
                hora = (data_m or "")[-8:] if data_m else "-"
                cor = COR_VERDE if tipo_m in ("ENTRADA", "REFORCO") else COR_PERIGO
                sinal = "+" if tipo_m in ("ENTRADA", "REFORCO") else "-"
                fm = Frame(card_mov, bg=COR_CARD)
                fm.pack(fill=X, padx=10, pady=2)
                Label(fm, text=f"{hora} {tipo_m[:12]}",
                      font=("Segoe UI", 9),
                      bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT)
                Label(fm, text=f"{sinal}{formatar_kz(abs(valor_m or 0))}",
                      font=("Segoe UI", 9, "bold"),
                      bg=COR_CARD, fg=cor).pack(side=RIGHT)
            except Exception:
                pass
    else:
        Label(card_mov, text="Sem movimentos",
              font=("Segoe UI", 9, "italic"),
              bg=COR_CARD, fg="#94a3b8").pack(pady=8)

    Label(col_dir, text="📊 INFO DO CAIXA",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO, anchor=W).pack(fill=X)

    card_info = Frame(col_dir, bg=COR_CARD, highlightthickness=1,
                       highlightbackground="#cbd5e1")
    card_info.pack(fill=X, pady=(3, 10))

    def _info(parent, label, valor):
        f = Frame(parent, bg=COR_CARD)
        f.pack(fill=X, padx=10, pady=2)
        Label(f, text=label, font=("Segoe UI", 9),
              bg=COR_CARD, fg="#64748b").pack(side=LEFT)
        Label(f, text=str(valor), font=("Segoe UI", 10, "bold"),
              bg=COR_CARD, fg=COR_TEXTO).pack(side=RIGHT)

    _info(card_info, "Caixa:", f"#{cx_id}")
    _info(card_info, "Aberto:", (info_caixa[0] or "-")[:16])
    _info(card_info, "Operador:", info_caixa[1] or "-")
    _info(card_info, "Nº vendas:", info_caixa[2] or 0)
    _info(card_info, "Total vendas:", formatar_kz(info_caixa[3] or 0))

    # ═══════════ CONFIRMAR ═══════════

    def confirmar():
        try:
            txt = total_contado_var.get().replace("Kz", "").replace(".", "").replace(",", ".").strip()
            total_cash = float(txt or 0)
        except ValueError:
            messagebox.showerror("Erro", "Valor contado cash invalido.")
            return

        try:
            tpa_txt = entry_tpa_valor.get().replace(".", "").replace(",", ".")
            total_tpa = float(tpa_txt or 0)
        except ValueError:
            messagebox.showerror("Erro", "Valor TPA invalido.")
            return

        try:
            num_taloes = int(entry_taloes.get() or 0)
        except ValueError:
            num_taloes = 0

        diff_cash = total_cash - esperado_cash
        observacoes = entry_obs.get().strip()

        if diff_cash < -0.01:
            messagebox.showerror("FALTA em Cash",
                f"Nao e possivel fechar!\n\n"
                f"FALTA: {formatar_kz(abs(diff_cash))}\n\n"
                f"Reconte o dinheiro antes de fechar.")
            return

        if diff_cash > 0.01 and not observacoes:
            messagebox.showwarning("Observação obrigatória",
                f"Ha sobra no caixa.\n\n"
                f"Tem de escrever o motivo.")
            return

        if not messagebox.askyesno("Confirmar Fecho",
            f"Fechar o caixa?\n\n"
            f"Cash: {formatar_kz(total_cash)}\n"
            f"TPA:  {formatar_kz(total_tpa)} ({num_taloes} taloes)\n"
            f"Depositar: {valor_depositar_var.get()}"):
            return

        ok, nome_gerente = _pedir_autorizacao_gerente(
            janela,
            f"Fecho do caixa #{cx_id}",
            utilizador_logado
        )
        if not ok:
            return

        detalhe = {}
        for nota, entry in entries_notas.items():
            try:
                qtd = int(entry.get() or 0)
                if qtd > 0:
                    detalhe[str(nota)] = qtd
            except ValueError:
                pass

        try:
            resultado = fechar_caixa(
                cx_id, utilizador_logado["id"], utilizador_logado["nome"],
                total_cash, observacoes,
                contado_tpa=total_tpa,
                num_taloes_tpa=num_taloes,
                detalhe_notas=detalhe
            )

            registar_auditoria(
                utilizador_logado["id"], utilizador_logado["nome"],
                "FECHO CAIXA",
                f"Caixa #{cx_id} | Cash: {formatar_kz(total_cash)} | "
                f"TPA: {formatar_kz(total_tpa)} | "
                f"Autorizado por: {nome_gerente}"
            )

            messagebox.showinfo("Caixa Fechado",
                f"CAIXA #{cx_id} FECHADO!\n\n"
                f"Cash: {formatar_kz(total_cash)}\n"
                f"TPA:  {formatar_kz(total_tpa)}\n"
                f"Depositar: {valor_depositar_var.get()}\n"
                f"Fundo ao gerente: {formatar_kz(fundo_inicial)}\n\n"
                f"Autorizado por: {nome_gerente}")

            janela.destroy()
            parent.destroy()
            abrir_caixa_menu(utilizador_logado)

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"Erro ao fechar caixa: {e}")

    Button(frame_btn, text="✅ Confirmar Fecho",
           font=("Segoe UI", 12, "bold"),
           bg="#be185d", fg="white",
           width=20, height=2, bd=0, cursor="hand2",
           command=confirmar).pack(side=LEFT, padx=3)

    Button(frame_btn, text="❌ Cancelar",
           font=("Segoe UI", 11),
           bg="#6b7280", fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=3)


def abrir_historico_caixas():
    janela = Toplevel()
    janela.title("Historico de Caixas")
    janela.geometry("1000x600")
    janela.configure(bg=COR_FUNDO)

    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Historico de Caixas", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)

    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(fill=BOTH, expand=True, padx=15, pady=15)

    colunas = ("ID", "Abertura", "Fecho", "Utilizador", "Inicial",
               "Esperado", "Contado", "Diferenca", "Estado")
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=110)
    tree.pack(fill=BOTH, expand=True)

    for cx in listar_caixas(50):
        cx_id, dt_ab, dt_fc, user, v_ini, v_esp, v_con, dif, estado = cx
        tree.insert("", END, values=(cx_id, dt_ab or "-", dt_fc or "-", user,
                                       formatar_kz(v_ini), formatar_kz(v_esp),
                                       formatar_kz(v_con), formatar_kz(dif), estado))