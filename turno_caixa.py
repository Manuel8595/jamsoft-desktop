# ============================================================
# ============ TURNO DE CAIXA - ABRIR / FECHAR ===============
# ============================================================

import os
from tkinter import *
from tkinter import messagebox, ttk
from datetime import datetime
from database import (abrir_turno, fechar_turno, turno_aberto, obter_turno,
                       calcular_totais_turno, obter_detalhe_notas,
                       registar_auditoria, conectar, autenticar)
from moeda import formatar_kz
from seguranca import verificar_acesso

# Cores Premium
COR_FUNDO = "#0f172a"
COR_CARD = "#1e293b"
COR_CARD_HOVER = "#334155"
COR_PRIMARIA = "#7c3aed"
COR_DOURADO = "#fbbf24"
COR_VERDE = "#10b981"
COR_VERMELHO = "#ef4444"
COR_ALERTA = "#f97316"
COR_AZUL = "#0ea5e9"
COR_TEXTO = "#f8fafc"
COR_TEXTO_SEC = "#94a3b8"
COR_BORDA = "#334155"

NOTAS = [5000, 2000, 1000, 500, 200, 100, 50, 20, 10]


# ============================================================
# ============ JANELA DE CONTAGEM DE NOTAS ===================
# ============================================================

def abrir_contagem_notas(parent, titulo, callback, notas_iniciais=None):
    """Abre janela de contagem de notas.
    
    callback recebe dict {5000: 10, ...} e total.
    notas_iniciais: dict opcional para pré-preencher
    """
    janela = Toplevel(parent)
    janela.title(titulo)
    janela.geometry("550x720")
    janela.configure(bg=COR_FUNDO)
    janela.transient(parent)
    janela.grab_set()
    
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 550) // 2
    y = (janela.winfo_screenheight() - 720) // 2
    janela.geometry(f"550x720+{x}+{y}")
    
    header = Frame(janela, bg=COR_PRIMARIA, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text=titulo,
          font=("Segoe UI", 15, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=20)
    
    Label(janela, text="Preencha o número de notas de cada valor:",
          font=("Segoe UI", 10, "italic"),
          bg=COR_FUNDO, fg=COR_TEXTO_SEC).pack(pady=(15, 10))
    
    card = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground=COR_BORDA)
    card.pack(padx=25, pady=5, fill=X)
    
    frame_notas = Frame(card, bg=COR_CARD)
    frame_notas.pack(padx=20, pady=15, fill=X)
    
    entradas = {}
    labels_subtotais = {}
    total_var = StringVar(value="Kz 0,00")
    
    Label(frame_notas, text="Nota",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=0, padx=10, pady=8, sticky=W)
    Label(frame_notas, text="Quantidade",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=1, padx=10, pady=8)
    Label(frame_notas, text="Subtotal",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=2, padx=10, pady=8, sticky=E)
    
    def atualizar_total(event=None):
        total = 0
        for valor in NOTAS:
            try:
                qtd = int(entradas[valor].get() or 0)
            except ValueError:
                qtd = 0
            sub = qtd * valor
            labels_subtotais[valor].config(text=formatar_kz(sub))
            total += sub
        total_var.set(formatar_kz(total))
    
    for i, valor in enumerate(NOTAS, start=1):
        Label(frame_notas, text=f"Kz {valor:,}".replace(",", "."),
              font=("Segoe UI", 11, "bold"),
              bg=COR_CARD, fg=COR_DOURADO).grid(row=i, column=0, padx=10, pady=5, sticky=W)
        
        e = Entry(frame_notas, font=("Segoe UI", 12),
                   width=8, justify=CENTER, bd=1, relief=SOLID)
        e.grid(row=i, column=1, padx=10, pady=5, ipady=4)
        e.bind('<KeyRelease>', atualizar_total)
        
        if notas_iniciais and valor in notas_iniciais:
            qtd_ini = notas_iniciais[valor]
            if qtd_ini > 0:
                e.insert(0, str(qtd_ini))
        
        entradas[valor] = e
        
        lbl = Label(frame_notas, text="Kz 0,00",
                     font=("Segoe UI", 11),
                     bg=COR_CARD, fg=COR_TEXTO)
        lbl.grid(row=i, column=2, padx=10, pady=5, sticky=E)
        labels_subtotais[valor] = lbl
    
    Frame(frame_notas, bg=COR_BORDA, height=2).grid(
        row=len(NOTAS)+1, column=0, columnspan=3, sticky="ew", pady=(10, 5))
    
    Label(frame_notas, text="TOTAL:",
          font=("Segoe UI", 14, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=len(NOTAS)+2, column=0, columnspan=2,
                                            padx=10, pady=10, sticky=W)
    Label(frame_notas, textvariable=total_var,
          font=("Segoe UI", 16, "bold"),
          bg=COR_CARD, fg=COR_VERDE).grid(row=len(NOTAS)+2, column=2,
                                            padx=10, pady=10, sticky=E)
    
    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=20)
    
    def confirmar():
        total = 0
        notas_dict = {}
        for valor in NOTAS:
            try:
                qtd = int(entradas[valor].get() or 0)
            except ValueError:
                qtd = 0
            notas_dict[valor] = qtd
            total += qtd * valor
        
        if total <= 0:
            messagebox.showwarning("Aviso", "O total não pode ser zero.")
            return
        
        janela.destroy()
        callback(notas_dict, total)
    
    Button(frame_btn, text="✅ Confirmar Contagem",
           font=("Segoe UI", 12, "bold"),
           bg=COR_VERDE, fg="white",
           width=25, height=2, bd=0, cursor="hand2",
           activebackground="#059669",
           command=confirmar).pack(side=LEFT, padx=5)
    
    Button(frame_btn, text="❌ Cancelar",
           font=("Segoe UI", 11),
           bg="#64748b", fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=5)
    
    atualizar_total()
    entradas[5000].focus()


# ============================================================
# ============ JANELA: PEDIR SENHA DO GERENTE ================
# ============================================================

def pedir_autorizacao_gerente(parent, motivo):
    """Pede senha do gerente. Retorna (sucesso, nome_gerente)."""
    resultado = {"ok": False, "nome": None}
    
    auth = Toplevel(parent)
    auth.title("Autorização do Gerente")
    auth.geometry("480x420")
    auth.configure(bg=COR_FUNDO)
    auth.transient(parent)
    auth.grab_set()
    
    auth.update_idletasks()
    x = (auth.winfo_screenwidth() - 480) // 2
    y = (auth.winfo_screenheight() - 420) // 2
    auth.geometry(f"480x420+{x}+{y}")
    
    header = Frame(auth, bg=COR_ALERTA, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="🔐 AUTORIZAÇÃO NECESSÁRIA",
          font=("Segoe UI", 14, "bold"),
          bg=COR_ALERTA, fg="white").pack(pady=20)
    
    Label(auth, text=motivo,
          font=("Segoe UI", 11),
          bg=COR_FUNDO, fg=COR_TEXTO,
          wraplength=440, justify=CENTER).pack(pady=(20, 15), padx=20)
    
    card = Frame(auth, bg=COR_CARD, highlightthickness=1, highlightbackground=COR_BORDA)
    card.pack(padx=30, fill=X)
    
    frame = Frame(card, bg=COR_CARD)
    frame.pack(padx=20, pady=20, fill=X)
    
    Label(frame, text="Utilizador:",
          font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=0, sticky=W, padx=5, pady=5)
    e_user = Entry(frame, font=("Segoe UI", 11), width=22, bd=1, relief=SOLID)
    e_user.grid(row=0, column=1, padx=5, pady=5, ipady=4)
    e_user.focus()
    
    Label(frame, text="Senha:",
          font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=1, column=0, sticky=W, padx=5, pady=5)
    e_pass = Entry(frame, font=("Segoe UI", 11), width=22, bd=1, relief=SOLID, show="*")
    e_pass.grid(row=1, column=1, padx=5, pady=5, ipady=4)
    
    msg_var = StringVar()
    Label(auth, textvariable=msg_var, font=("Segoe UI", 10),
          bg=COR_FUNDO, fg=COR_VERMELHO).pack(pady=5)
    
    def confirmar(event=None):
        u = e_user.get().strip()
        p = e_pass.get()
        
        if not u or not p:
            msg_var.set("Preencha utilizador e senha")
            return
        
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
            e_pass.focus()
    
    e_user.bind('<Return>', lambda e: e_pass.focus())
    e_pass.bind('<Return>', confirmar)
    
    Button(auth, text="🔓 Autorizar",
           font=("Segoe UI", 12, "bold"),
           bg=COR_VERDE, fg="white",
           width=20, height=2, bd=0, cursor="hand2",
           activebackground="#059669",
           command=confirmar).pack(pady=20)
    
    auth.wait_window()
    return resultado["ok"], resultado["nome"]

# ============================================================
# ============ JANELA: ABRIR TURNO ===========================
# ============================================================

def abrir_turno_janela(utilizador_logado, parent, callback_sucesso=None):
    """Abre o ecra para abrir um novo turno (com autorizacao do gerente)."""
    
    if not verificar_acesso(utilizador_logado, "caixa.abrir", "Abrir Turno"):
        return
    
    ja_aberto = turno_aberto()
    if ja_aberto:
        messagebox.showwarning("Turno Aberto",
            f"Ja existe um turno aberto por {ja_aberto[3]}.\n\n"
            f"Feche o turno atual antes de abrir outro.")
        return
    
    # Verificar se ha caixa aberto (tabela caixas)
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id FROM caixas WHERE estado = 'ABERTO' LIMIT 1")
    cx = cur.fetchone()
    conn.close()
    
    if not cx:
        # Se nao existe caixa aberto, abrir automaticamente um
        try:
            from database import abrir_caixa
            cx_id = abrir_caixa(utilizador_logado["id"], utilizador_logado["nome"], 0)
        except Exception as e:
            messagebox.showerror("Erro", f"Nao foi possivel abrir o caixa: {e}")
            return
    else:
        cx_id = cx[0]
    
    # Callback depois da contagem
    def apos_contagem(notas_dict, valor_inicial):
        # Pedir autorizacao do gerente
        ok, nome_gerente = pedir_autorizacao_gerente(
            parent,
            f"O farmaceutico {utilizador_logado['nome']} esta a abrir um turno.\n\n"
            f"Fundo de troco: {formatar_kz(valor_inicial)}\n\n"
            f"Digite a senha do gerente para autorizar."
        )
        
        if not ok:
            messagebox.showwarning("Cancelado", "Abertura nao autorizada pelo gerente.")
            return
        
        try:
            turno_id = abrir_turno(
                cx_id,
                utilizador_logado["id"],
                utilizador_logado["nome"],
                valor_inicial,
                notas_dict,
                f"Autorizado por: {nome_gerente}"
            )
            
            registar_auditoria(
                utilizador_logado["id"],
                utilizador_logado["nome"],
                "ABERTURA TURNO",
                f"Turno #{turno_id} | Fundo: {formatar_kz(valor_inicial)} | Autorizado por: {nome_gerente}"
            )
            
            messagebox.showinfo("✅ Turno Aberto",
                f"Turno #{turno_id} aberto com sucesso!\n\n"
                f"Fundo de troco: {formatar_kz(valor_inicial)}\n"
                f"Operador: {utilizador_logado['nome']}\n"
                f"Autorizado por: {nome_gerente}")
            
            if callback_sucesso:
                callback_sucesso()
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir turno: {e}")
    
    abrir_contagem_notas(parent, "Contagem Inicial - Abrir Turno", apos_contagem)


# ============================================================
# ============ JANELA: FECHAR TURNO ==========================
# ============================================================

def fechar_turno_janela(utilizador_logado, parent, callback_sucesso=None):
    """Fecha o turno com todas as regras (falta bloqueia, sobra aceita)."""
    
    if not verificar_acesso(utilizador_logado, "caixa.fechar", "Fechar Turno"):
        return
    
    turno = turno_aberto()
    if not turno:
        messagebox.showwarning("Sem Turno", "Nao existe nenhum turno aberto.")
        return
    
    turno_id = turno[0]
    caixa_id = turno[1]
    data_abertura = turno[2]
    utilizador_nome = turno[3]
    valor_inicial = turno[4]
    
    # Calcular totais atuais
    totais = calcular_totais_turno(turno_id)
    
    # ===== JANELA PRINCIPAL =====
    janela = Toplevel(parent)
    janela.title("Fechar Turno")
    janela.geometry("800x900")
    janela.configure(bg=COR_FUNDO)
    janela.transient(parent)
    janela.grab_set()
    
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 800) // 2
    y = (janela.winfo_screenheight() - 900) // 2
    janela.geometry(f"800x900+{x}+{y}")
    
    header = Frame(janela, bg=COR_ALERTA, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="🌙 Fechar Turno de Caixa",
          font=("Segoe UI", 18, "bold"),
          bg=COR_ALERTA, fg="white").pack(pady=(15, 0))
    Label(header, text=f"Turno #{turno_id}  |  {utilizador_nome}  |  Iniciado: {data_abertura}",
          font=("Segoe UI", 10, "italic"),
          bg=COR_ALERTA, fg="#fff7ed").pack()
    
    # Scroll
    main_frame = Frame(janela, bg=COR_FUNDO)
    main_frame.pack(fill=BOTH, expand=True)
    
    canvas = Canvas(main_frame, bg=COR_FUNDO, highlightthickness=0)
    sb = Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable = Frame(canvas, bg=COR_FUNDO)
    
    scrollable.bind("<Configure>",
                     lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable, anchor="nw", width=780)
    canvas.configure(yscrollcommand=sb.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    
    # ===== RESUMO DO SISTEMA =====
    Label(scrollable, text="📊 Resumo do Sistema",
          font=("Segoe UI", 13, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=20, pady=(15, 5))
    
    card_resumo = Frame(scrollable, bg=COR_CARD, highlightthickness=1, highlightbackground=COR_BORDA)
    card_resumo.pack(fill=X, padx=20, pady=5)
    
    frame_resumo = Frame(card_resumo, bg=COR_CARD)
    frame_resumo.pack(padx=20, pady=15, fill=X)
    
    def linha_resumo(parent, label, valor, cor=COR_TEXTO, bold=False):
        f = Frame(parent, bg=COR_CARD)
        f.pack(fill=X, pady=3)
        fonte = ("Segoe UI", 11, "bold") if bold else ("Segoe UI", 11)
        Label(f, text=label, font=fonte, bg=COR_CARD, fg=COR_TEXTO_SEC).pack(side=LEFT)
        Label(f, text=valor, font=fonte, bg=COR_CARD, fg=cor).pack(side=RIGHT)
    
    linha_resumo(frame_resumo, "Total de Vendas:", formatar_kz(totais["total_geral"]))
    linha_resumo(frame_resumo, "💵 Dinheiro (sistema):", formatar_kz(totais["dinheiro"]), COR_VERDE)
    linha_resumo(frame_resumo, "💳 TPA (sistema):", formatar_kz(totais["tpa"]), COR_AZUL)
    linha_resumo(frame_resumo, "📱 PIX:", formatar_kz(totais["pix"]), COR_PRIMARIA)
    
    Frame(frame_resumo, bg=COR_BORDA, height=1).pack(fill=X, pady=8)
    
    linha_resumo(frame_resumo, "Fundo Inicial (troco):", formatar_kz(valor_inicial), COR_TEXTO_SEC)
    linha_resumo(frame_resumo, "ESPERADO EM CAIXA:",
                  formatar_kz(valor_inicial + totais["dinheiro"]),
                  COR_DOURADO, bold=True)
    
    # ===== CONTAGEM DE NOTAS =====
    Label(scrollable, text="💵 Contagem de Dinheiro (notas finais)",
          font=("Segoe UI", 13, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=20, pady=(20, 5))
    
    card_notas = Frame(scrollable, bg=COR_CARD, highlightthickness=1, highlightbackground=COR_BORDA)
    card_notas.pack(fill=X, padx=20, pady=5)
    
    frame_notas = Frame(card_notas, bg=COR_CARD)
    frame_notas.pack(padx=20, pady=15, fill=X)
    
    entradas_notas = {}
    subtotais_labels = {}
    total_dinheiro_var = StringVar(value="Kz 0,00")
    
    Label(frame_notas, text="Nota",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=0, padx=10, pady=5, sticky=W)
    Label(frame_notas, text="Qtd",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=1, padx=10, pady=5)
    Label(frame_notas, text="Subtotal",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=2, padx=10, pady=5, sticky=E)
    
    def atualizar_total_dinheiro(event=None):
        total = 0
        for valor in NOTAS:
            try:
                qtd = int(entradas_notas[valor].get() or 0)
            except ValueError:
                qtd = 0
            sub = qtd * valor
            subtotais_labels[valor].config(text=formatar_kz(sub))
            total += sub
        total_dinheiro_var.set(formatar_kz(total))
        atualizar_conciliacao()
    
    for i, valor in enumerate(NOTAS, start=1):
        Label(frame_notas, text=f"Kz {valor:,}".replace(",", "."),
              font=("Segoe UI", 11, "bold"),
              bg=COR_CARD, fg=COR_DOURADO).grid(row=i, column=0, padx=10, pady=4, sticky=W)
        
        e = Entry(frame_notas, font=("Segoe UI", 12),
                   width=8, justify=CENTER, bd=1, relief=SOLID)
        e.grid(row=i, column=1, padx=10, pady=4, ipady=3)
        e.bind('<KeyRelease>', atualizar_total_dinheiro)
        entradas_notas[valor] = e
        
        lbl = Label(frame_notas, text="Kz 0,00",
                     font=("Segoe UI", 11),
                     bg=COR_CARD, fg=COR_TEXTO)
        lbl.grid(row=i, column=2, padx=10, pady=4, sticky=E)
        subtotais_labels[valor] = lbl
    
    Frame(frame_notas, bg=COR_BORDA, height=2).grid(
        row=len(NOTAS)+1, column=0, columnspan=3, sticky="ew", pady=(8, 5))
    
    Label(frame_notas, text="TOTAL DINHEIRO:",
          font=("Segoe UI", 13, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=len(NOTAS)+2, column=0, columnspan=2,
                                            padx=10, pady=10, sticky=W)
    Label(frame_notas, textvariable=total_dinheiro_var,
          font=("Segoe UI", 15, "bold"),
          bg=COR_CARD, fg=COR_VERDE).grid(row=len(NOTAS)+2, column=2,
                                            padx=10, pady=10, sticky=E)
    
    # ===== TPA =====
    Label(scrollable, text="💳 Talões TPA (Multicaixa)",
          font=("Segoe UI", 13, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=20, pady=(20, 5))
    
    card_tpa = Frame(scrollable, bg=COR_CARD, highlightthickness=1, highlightbackground=COR_BORDA)
    card_tpa.pack(fill=X, padx=20, pady=5)
    
    frame_tpa = Frame(card_tpa, bg=COR_CARD)
    frame_tpa.pack(padx=20, pady=15, fill=X)
    
    Label(frame_tpa, text="Nº de Talões:",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
    e_num_taloes = Entry(frame_tpa, font=("Segoe UI", 14),
                           width=20, justify=CENTER, bd=1, relief=SOLID)
    e_num_taloes.pack(anchor=W, ipady=6)
    
    Label(frame_tpa, text="Total dos Talões (Kz):",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(15, 3))
    e_tpa = Entry(frame_tpa, font=("Segoe UI", 14),
                    width=20, justify=CENTER, bd=1, relief=SOLID)
    e_tpa.pack(anchor=W, ipady=6)
    e_tpa.bind('<KeyRelease>', lambda e: atualizar_conciliacao())
    
    # ===== CONCILIACAO =====
    Label(scrollable, text="📊 Conciliação em Tempo Real",
          font=("Segoe UI", 13, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=20, pady=(20, 5))
    
    card_conc = Frame(scrollable, bg=COR_CARD, highlightthickness=2, highlightbackground=COR_BORDA)
    card_conc.pack(fill=X, padx=20, pady=5)
    
    frame_conc = Frame(card_conc, bg=COR_CARD)
    frame_conc.pack(padx=20, pady=15, fill=X)
    
    conciliacao_var = StringVar(value="Aguardando contagem...")
    resultado_var = StringVar(value="")
    
    def obter_valor(entry):
        try:
            txt = entry.get().replace(".", "").replace(",", ".").strip()
            return float(txt) if txt else 0.0
        except ValueError:
            return 0.0
    
    def atualizar_conciliacao():
        dinheiro_contado = 0
        for valor in NOTAS:
            try:
                qtd = int(entradas_notas[valor].get() or 0)
            except ValueError:
                qtd = 0
            dinheiro_contado += qtd * valor
        
        tpa_contado = obter_valor(e_tpa)
        total_contado = dinheiro_contado + tpa_contado
        
        total_esperado = valor_inicial + totais["dinheiro"] + totais["tpa"]
        diferenca = total_contado - total_esperado
        
        conciliacao_var.set(
            f"Contado: {formatar_kz(total_contado)}\n"
            f"Esperado: {formatar_kz(total_esperado)}\n"
            f"Diferença: {formatar_kz(diferenca)}"
        )
        
        if abs(diferenca) < 0.01:
            resultado_var.set("✅ OK - Sem diferenças")
            resultado_lbl.config(fg=COR_VERDE)
        elif diferenca < 0:
            resultado_var.set(f"⚠️ FALTA: {formatar_kz(abs(diferenca))}")
            resultado_lbl.config(fg=COR_VERMELHO)
        else:
            resultado_var.set(f"💰 SOBRA: {formatar_kz(diferenca)}")
            resultado_lbl.config(fg=COR_ALERTA)
    
    Label(frame_conc, textvariable=conciliacao_var,
          font=("Segoe UI", 12),
          bg=COR_CARD, fg=COR_TEXTO, justify=LEFT).pack(pady=5, anchor=W)
    
    resultado_lbl = Label(frame_conc, textvariable=resultado_var,
                            font=("Segoe UI", 16, "bold"),
                            bg=COR_CARD, fg=COR_TEXTO)
    resultado_lbl.pack(pady=(10, 5))
    
    # ===== OBSERVACOES =====
    Label(scrollable, text="📝 Observações:",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, padx=20, pady=(20, 5))
    
    text_obs = Text(scrollable, height=3, font=("Segoe UI", 11),
                     bg=COR_CARD, fg=COR_TEXTO, insertbackground=COR_TEXTO,
                     bd=1, relief=SOLID)
    text_obs.pack(fill=X, padx=20, pady=5)
    
    # ===== BOTOES =====
    frame_btn = Frame(janela, bg=COR_FUNDO, height=80)
    frame_btn.pack(fill=X, side=BOTTOM)
    frame_btn.pack_propagate(False)
    
    def confirmar_fecho():
        # 1. Validar notas
        notas_dict = {}
        dinheiro_total = 0
        for valor in NOTAS:
            try:
                qtd = int(entradas_notas[valor].get() or 0)
            except ValueError:
                qtd = 0
            notas_dict[valor] = qtd
            dinheiro_total += qtd * valor
        
        tpa_total = obter_valor(e_tpa)
        
        if dinheiro_total == 0 and tpa_total == 0:
            messagebox.showwarning("Aviso",
                "Preencha pelo menos o dinheiro ou o TPA.")
            return
        
        # 2. Verificar DIFERENÇA
        total_contado = dinheiro_total + tpa_total
        total_esperado = valor_inicial + totais["dinheiro"] + totais["tpa"]
        diferenca = total_contado - total_esperado
        
        # 3. Se FALTA -> bloquear
        if diferenca < -0.01:
            messagebox.showerror("❌ NÃO PODE FECHAR",
                f"FALTA dinheiro no caixa!\n\n"
                f"Diferença: {formatar_kz(abs(diferenca))}\n\n"
                f"O farmacêutico deve REPOR este valor antes de fechar o turno.\n\n"
                f"1. Coloque {formatar_kz(abs(diferenca))} no caixa\n"
                f"2. Volte a fazer a contagem\n"
                f"3. Confirme novamente")
            return
        
        # 4. Se OK ou SOBRA -> pedir autorizacao do gerente
        msg_gerente = (
            f"O farmaceutico {utilizador_logado['nome']} esta a fechar o turno #{turno_id}.\n\n"
        )
        if abs(diferenca) < 0.01:
            msg_gerente += "Situacao: OK (sem diferencas)\n\n"
        else:
            msg_gerente += f"Situacao: SOBRA de {formatar_kz(diferenca)}\n\n"
        
        msg_gerente += "Digite a senha do gerente para autorizar o fecho."
        
        ok, nome_gerente = pedir_autorizacao_gerente(parent, msg_gerente)
        if not ok:
            messagebox.showwarning("Cancelado", "Fecho nao autorizado.")
            return
        
        # 5. Executar fecho
        try:
            resultado = fechar_turno(
                turno_id,
                dinheiro_total,
                tpa_total,
                notas_dict,
                text_obs.get("1.0", END).strip() + f"\nAutorizado por: {nome_gerente}"
            )
            
            # 6. Registar auditoria detalhada
            registar_auditoria(
                utilizador_logado["id"],
                utilizador_logado["nome"],
                "FECHO TURNO",
                (f"Turno #{turno_id} | "
                 f"Vendas: {formatar_kz(resultado['total_vendas'])} | "
                 f"Contado: {formatar_kz(resultado['total_contado'])} | "
                 f"Esperado: {formatar_kz(resultado['total_sistema'])} | "
                 f"Diferenca: {formatar_kz(resultado['diferenca'])} | "
                 f"Estado: {resultado['estado']} | "
                 f"Autorizado por: {nome_gerente}")
            )
            
            # 7. Se SOBRA, registar no log
            if resultado["estado"] == "SOBRA":
                registar_auditoria(
                    utilizador_logado["id"],
                    utilizador_logado["nome"],
                    "SOBRA REGISTADA",
                    f"Turno #{turno_id} | Sobra: {formatar_kz(resultado['diferenca'])} | Pendente deposito"
                )
            
            # 8. Mensagem final
            msg = (f"✅ Turno #{turno_id} fechado!\n\n"
                   f"Total de Vendas: {formatar_kz(resultado['total_vendas'])}\n"
                   f"Dinheiro (sistema): {formatar_kz(resultado['dinheiro_sistema'])}\n"
                   f"TPA (sistema): {formatar_kz(resultado['tpa_sistema'])}\n"
                   f"PIX (sistema): {formatar_kz(resultado['pix_sistema'])}\n\n"
                   f"Contado: {formatar_kz(resultado['total_contado'])}\n"
                   f"Esperado: {formatar_kz(resultado['total_sistema'])}\n\n")
            
            if resultado["estado"] == "OK":
                msg += "✅ PERFEITO - Sem diferenças!"
            elif resultado["estado"] == "SOBRA":
                msg += f"💰 SOBRA de {formatar_kz(resultado['diferenca'])}\n"
                msg += f"→ O valor será entregue ao gerente."
            
            msg += f"\n\nAutorizado por: {nome_gerente}"
            
            messagebox.showinfo("Turno Fechado", msg)
            janela.destroy()
            
            if callback_sucesso:
                callback_sucesso()
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao fechar turno: {e}")
    
    Button(frame_btn, text="🌙 CONFIRMAR FECHO DO TURNO",
           font=("Segoe UI", 13, "bold"),
           bg=COR_ALERTA, fg="white",
           width=30, height=2, bd=0, cursor="hand2",
           activebackground="#ea580c",
           command=confirmar_fecho).pack(side=LEFT, padx=20, pady=15)
    
    Button(frame_btn, text="❌ Cancelar",
           font=("Segoe UI", 11),
           bg="#64748b", fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=5, pady=15)
    
    entradas_notas[5000].focus()
    atualizar_total_dinheiro()

    # ============================================================
# ============ JANELA PRINCIPAL: GESTAO DE TURNOS ============
# ============================================================

def abrir_gestao_turnos(utilizador_logado, parent=None):
    """Abre o ecra principal de gestao de turnos."""
    
    if not verificar_acesso(utilizador_logado, "caixa.ver_movimentos", "Gestao de Turnos"):
        return
    
    if parent is None:
        parent = Toplevel()
        parent.withdraw()
    
    janela = Toplevel(parent)
    janela.title("Gestao de Turnos de Caixa")
    janela.geometry("1000x700")
    janela.configure(bg=COR_FUNDO)
    
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 1000) // 2
    y = (janela.winfo_screenheight() - 700) // 2
    janela.geometry(f"1000x700+{x}+{y}")
    
    # Header
    header = Frame(janela, bg=COR_PRIMARIA, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="💼 Gestao de Turnos de Caixa",
          font=("Segoe UI", 18, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=(15, 0))
    Label(header, text=f"Operador: {utilizador_logado['nome']}",
          font=("Segoe UI", 10, "italic"),
          bg=COR_PRIMARIA, fg="#e0e7ff").pack()
    
    # Verificar estado
    turno_atual = turno_aberto()
    
    # ===== CARD DE ESTADO ATUAL =====
    card_estado = Frame(janela, bg=COR_CARD, highlightthickness=2,
                         highlightbackground=COR_VERDE if turno_atual else COR_ALERTA)
    card_estado.pack(fill=X, padx=25, pady=20)
    
    if turno_atual:
        turno_id, caixa_id, data_abertura, utilizador_nome, valor_inicial = turno_atual
        
        Label(card_estado, text="🟢 TURNO ABERTO",
              font=("Segoe UI", 16, "bold"),
              bg=COR_CARD, fg=COR_VERDE).pack(pady=(15, 5))
        
        Label(card_estado,
              text=f"Turno #{turno_id}  |  Operador: {utilizador_nome}  |  Inicio: {data_abertura}",
              font=("Segoe UI", 11),
              bg=COR_CARD, fg=COR_TEXTO).pack()
        
        Label(card_estado,
              text=f"Fundo de troco: {formatar_kz(valor_inicial)}",
              font=("Segoe UI", 11, "bold"),
              bg=COR_CARD, fg=COR_DOURADO).pack(pady=(5, 15))
        
        Button(card_estado, text="🌙 FECHAR TURNO ATUAL",
               font=("Segoe UI", 12, "bold"),
               bg=COR_ALERTA, fg="white",
               width=25, height=2, bd=0, cursor="hand2",
               activebackground="#ea580c",
               command=lambda: fechar_turno_janela(utilizador_logado, janela,
                                                     callback_sucesso=lambda: recarregar())).pack(pady=(0, 15))
    else:
        Label(card_estado, text="🔴 NENHUM TURNO ABERTO",
              font=("Segoe UI", 16, "bold"),
              bg=COR_CARD, fg=COR_ALERTA).pack(pady=(15, 5))
        
        Label(card_estado,
              text="Para iniciar as vendas, e preciso abrir um turno.",
              font=("Segoe UI", 11),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(5, 15))
        
        Button(card_estado, text="▶️ ABRIR NOVO TURNO",
               font=("Segoe UI", 12, "bold"),
               bg=COR_VERDE, fg="white",
               width=25, height=2, bd=0, cursor="hand2",
               activebackground="#059669",
               command=lambda: abrir_turno_janela(utilizador_logado, janela,
                                                    callback_sucesso=lambda: recarregar())).pack(pady=(0, 15))
    
    # ===== HISTORICO =====
    Label(janela, text="📋 Historico de Turnos",
          font=("Segoe UI", 13, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=30, pady=(20, 10))
    
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=25, pady=(0, 20))
    
    colunas = ("ID", "Abertura", "Fecho", "Operador", "Vendas",
               "Dinheiro", "TPA", "Contado", "Dif.", "Estado")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=14)
    
    for col in colunas:
        tree.heading(col, text=col)
    
    tree.column("ID", width=50)
    tree.column("Abertura", width=130)
    tree.column("Fecho", width=130)
    tree.column("Operador", width=130)
    tree.column("Vendas", width=100)
    tree.column("Dinheiro", width=100)
    tree.column("TPA", width=100)
    tree.column("Contado", width=100)
    tree.column("Dif.", width=80)
    tree.column("Estado", width=90)
    
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    def carregar_historico():
        for i in tree.get_children():
            tree.delete(i)
        
        try:
            from database import listar_turnos_historico
            turnos = listar_turnos_historico(100)
            
            for t in turnos:
                (tid, dt_ab, dt_fc, user, vendas, dinh, tpa, pix,
                 contado, sistema, dif, estado) = t
                
                dif_txt = formatar_kz(dif or 0)
                
                if estado == "CONCILIADO":
                    tag = "conciliado"
                elif estado == "FECHADO":
                    if dif and abs(dif) > 0.01:
                        tag = "diferenca"
                    else:
                        tag = "ok"
                else:
                    tag = ""
                
                tree.insert("", END, values=(
                    tid,
                    (dt_ab or "")[:16],
                    (dt_fc or "")[:16] if dt_fc else "-",
                    (user or "")[:15],
                    formatar_kz(vendas or 0),
                    formatar_kz(dinh or 0),
                    formatar_kz(tpa or 0),
                    formatar_kz(contado or 0),
                    dif_txt,
                    estado
                ), tags=(tag,))
        
        except Exception as e:
            print(f"Erro ao carregar historico: {e}")
    
    tree.tag_configure("ok", foreground=COR_VERDE)
    tree.tag_configure("diferenca", foreground=COR_ALERTA)
    tree.tag_configure("conciliado", foreground=COR_AZUL)
    
    def recarregar():
        janela.destroy()
        abrir_gestao_turnos(utilizador_logado, parent)
    
    carregar_historico()
    
    # ===== BOTOES =====
    frame_btns = Frame(janela, bg=COR_FUNDO, height=60)
    frame_btns.pack(fill=X, side=BOTTOM)
    frame_btns.pack_propagate(False)
    
    Button(frame_btns, text="🔄 Actualizar",
           font=("Segoe UI", 11, "bold"),
           bg=COR_AZUL, fg="white",
           width=18, height=2, bd=0, cursor="hand2",
           activebackground="#0284c7",
           command=recarregar).pack(side=LEFT, padx=15, pady=10)
    
    Button(frame_btns, text="❌ Fechar",
           font=("Segoe UI", 11, "bold"),
           bg=COR_VERMELHO, fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           activebackground="#dc2626",
           command=janela.destroy).pack(side=RIGHT, padx=15, pady=10)


# ============================================================
# ============ TESTE DIRETO ==================================
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  TESTE - Modulo turno_caixa.py")
    print("="*60)
    
    print("\n[1] A carregar funcoes...")
    from database import (abrir_turno, fechar_turno, turno_aberto,
                            calcular_totais_turno)
    print("    OK")
    
    print("\n[2] Estado atual...")
    t = turno_aberto()
    if t:
        print(f"    Turno ABERTO: #{t[0]} por {t[3]}")
        print(f"    Fundo inicial: {t[4]}")
    else:
        print("    Nenhum turno aberto")
    
    print("\n[3] Funcoes novas adicionadas:")
    print("    - pedir_autorizacao_gerente()")
    print("    - abrir_turno_janela()  (com senha do gerente)")
    print("    - fechar_turno_janela() (falta bloqueia, sobra aceita)")
    print("    - abrir_gestao_turnos()")
    
    print("\n" + "="*60 + "\n")