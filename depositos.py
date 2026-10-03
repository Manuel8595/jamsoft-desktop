# ============================================================
# ============ DEPOSITOS BANCARIOS ===========================
# ============================================================
# 
# Ecrã para o gerente registar os depositos do dinheiro do dia.
# 
# Regras:
#   - So gerente e admin podem fazer depositos
#   - Acima de limite (500.000 Kz) precisa aprovacao admin
#   - Auditor ve tudo mas nao mexe
#   - Cada deposito gera referencia DEP-AAAA-NNNN
#   - Comprovante obrigatorio
# 
# ============================================================

from tkinter import *
from tkinter import messagebox, ttk
from datetime import datetime
from database import (criar_deposito, listar_depositos, obter_deposito,
                       aprovar_deposito, cancelar_deposito,
                       saldo_atual_farmacia, listar_bancos_ativos,
                       obter_config_financeira, registar_auditoria,
                       autenticar, listar_movimentos_saldo)
from moeda import formatar_kz
from seguranca import verificar_acesso


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
# ============ PEDIR SENHA DO ADMIN ==========================
# ============================================================

def pedir_senha_admin(parent, motivo):
    """Pede senha do admin. Retorna (sucesso, nome)."""
    resultado = {"ok": False, "nome": None}
    
    auth = Toplevel(parent)
    auth.title("Confirmacao do Administrador")
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
    Label(header, text="APROVACAO DO ADMINISTRADOR",
          font=("Segoe UI", 13, "bold"),
          bg=COR_ALERTA, fg="white").pack(pady=20)
    
    Label(auth, text=motivo,
          font=("Segoe UI", 10),
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
        
        if sucesso and dados["perfil"] == "admin":
            resultado["ok"] = True
            resultado["nome"] = dados["nome"]
            auth.destroy()
        elif sucesso:
            msg_var.set("Apenas administradores podem aprovar")
            e_pass.delete(0, END)
        else:
            msg_var.set("Credenciais invalidas")
            e_pass.delete(0, END)
            e_pass.focus()
    
    e_user.bind('<Return>', lambda e: e_pass.focus())
    e_pass.bind('<Return>', confirmar)
    
    Button(auth, text="Confirmar",
           font=("Segoe UI", 12, "bold"),
           bg=COR_VERDE, fg="white",
           width=20, height=2, bd=0, cursor="hand2",
           activebackground="#059669",
           command=confirmar).pack(pady=20)
    
    auth.wait_window()
    return resultado["ok"], resultado["nome"]


# ============================================================
# ============ ECRAN PRINCIPAL ===============================
# ============================================================

def abrir_depositos(utilizador_logado, parent=None):
    """Abre o ecra de depositos bancarios."""
    
    if not verificar_acesso(utilizador_logado, "caixa.registar_deposito",
                              "Depositos Bancarios"):
        return
    
    if parent is None:
        parent = Toplevel()
        parent.withdraw()
    
    janela = Toplevel(parent)
    janela.title("Depositos Bancarios")
    janela.geometry("1100x700")
    janela.configure(bg=COR_FUNDO)
    
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 1100) // 2
    y = (janela.winfo_screenheight() - 700) // 2
    janela.geometry(f"1100x700+{x}+{y}")
    
    # Header
    header = Frame(janela, bg=COR_PRIMARIA, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="🏦 Depositos Bancarios",
          font=("Segoe UI", 20, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=(12, 0))
    Label(header, text=f"Utilizador: {utilizador_logado['nome']}  |  "
                        f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
          font=("Segoe UI", 10, "italic"),
          bg=COR_PRIMARIA, fg="#e0e7ff").pack()
    
    # Content area (recarregavel)
    content = Frame(janela, bg=COR_FUNDO)
    content.pack(fill=BOTH, expand=True)
    
    def recarregar():
        for w in content.winfo_children():
            w.destroy()
        construir_conteudo(content, utilizador_logado, janela, recarregar)
    
    construir_conteudo(content, utilizador_logado, janela, recarregar)


def construir_conteudo(content, utilizador_logado, janela, recarregar):
    """Constroi o conteudo do ecra."""
    
    # ===== CARD DE SALDO =====
    saldo = saldo_atual_farmacia()
    
    card_saldo = Frame(content, bg=COR_CARD, highlightthickness=2,
                        highlightbackground=COR_VERDE)
    card_saldo.pack(fill=X, padx=20, pady=15)
    
    inner = Frame(card_saldo, bg=COR_CARD)
    inner.pack(padx=30, pady=15, fill=X)
    
    Label(inner, text="SALDO ACTUAL DA FARMACIA",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W)
    
    Label(inner, text=formatar_kz(saldo),
          font=("Segoe UI", 26, "bold"),
          bg=COR_CARD, fg=COR_VERDE).pack(anchor=W, pady=(5, 0))
    
    # ===== FILTROS =====
    frame_filtro = Frame(content, bg=COR_CARD, highlightthickness=1,
                           highlightbackground=COR_BORDA)
    frame_filtro.pack(fill=X, padx=20, pady=(0, 10))
    
    inner_filtro = Frame(frame_filtro, bg=COR_CARD)
    inner_filtro.pack(padx=20, pady=10, fill=X)
    
    Label(inner_filtro, text="Filtrar por estado:",
          font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=(0, 8))
    
    filtro_var = StringVar(value="TODOS")
    combo = ttk.Combobox(inner_filtro, textvariable=filtro_var,
                           values=["TODOS", "REGISTADO", "PENDENTE_APROVACAO",
                                   "APROVADO", "CANCELADO"],
                           state="readonly", font=("Segoe UI", 10), width=20)
    combo.pack(side=LEFT, padx=(0, 15))
    
    # ===== TABELA =====
    frame_tab = Frame(content, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=20, pady=(0, 10))
    
    colunas = ("ID", "Referencia", "Data", "Hora", "Banco", "Valor",
               "Comprovante", "Gerente", "Estado")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=12)
    
    tree.heading("ID", text="ID")
    tree.heading("Referencia", text="Referencia")
    tree.heading("Data", text="Data")
    tree.heading("Hora", text="Hora")
    tree.heading("Banco", text="Banco")
    tree.heading("Valor", text="Valor")
    tree.heading("Comprovante", text="Comprovante")
    tree.heading("Gerente", text="Gerente")
    tree.heading("Estado", text="Estado")
    
    tree.column("ID", width=45)
    tree.column("Referencia", width=120)
    tree.column("Data", width=90)
    tree.column("Hora", width=70)
    tree.column("Banco", width=130)
    tree.column("Valor", width=120)
    tree.column("Comprovante", width=110)
    tree.column("Gerente", width=140)
    tree.column("Estado", width=130)
    
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    tree.tag_configure("pendente", background="#3f2a13", foreground=COR_ALERTA)
    tree.tag_configure("aprovado", background="#132a1a", foreground=COR_VERDE)
    tree.tag_configure("cancelado", background="#3f1a1a", foreground=COR_VERMELHO)
    tree.tag_configure("registado", background="#0f2a3f", foreground=COR_AZUL)
    
    def carregar():
        for i in tree.get_children():
            tree.delete(i)
        
        estado = filtro_var.get()
        filtro = None if estado == "TODOS" else estado
        
        try:
            depositos = listar_depositos(100, estado=filtro)
            for d in depositos:
                # d = (id, referencia, data, hora, valor, banco, comp,
                #      obs, gerente_nome, estado, aprov_por, data_aprov,
                #      criado_em)
                did = d[0]
                referencia = d[1]
                data = d[2]
                hora = d[3]
                valor = d[4]
                banco = d[5]
                comp = d[6]
                gerente = d[8]
                estado_d = d[9]
                
                tag = estado_d.lower().replace("_", "")[:10]
                if estado_d == "PENDENTE_APROVACAO":
                    tag = "pendente"
                elif estado_d == "APROVADO":
                    tag = "aprovado"
                elif estado_d == "CANCELADO":
                    tag = "cancelado"
                else:
                    tag = "registado"
                
                tree.insert("", END, values=(
                    did, referencia, data, hora, banco,
                    formatar_kz(valor), comp or "-",
                    (gerente or "-")[:18], estado_d
                ), tags=(tag,))
        except Exception as e:
            print(f"[Depositos] Erro ao carregar: {e}")
    
    combo.bind('<<ComboboxSelected>>', lambda e: carregar())
    
    # ===== BOTOES =====
    frame_btn = Frame(content, bg=COR_FUNDO)
    frame_btn.pack(fill=X, pady=10)
    
    estilo_btn = {
        "font": ("Segoe UI", 11, "bold"),
        "bd": 0, "cursor": "hand2",
        "fg": "white", "height": 2,
    }
    
    # Novo Deposito (só gerente/admin)
    if utilizador_logado["perfil"] in ("admin", "gerente"):
        Button(frame_btn, text="➕ Novo Deposito",
               bg=COR_VERDE, width=20,
               command=lambda: dialogo_novo_deposito(
                   utilizador_logado, janela, carregar
               ),
               **estilo_btn).pack(side=LEFT, padx=(20, 5), pady=8)
    
    # Detalhes
    def ver_detalhes():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um deposito.")
            return
        dep_id = tree.item(sel[0])["values"][0]
        dialogo_detalhes(dep_id, utilizador_logado, janela, carregar)
    
    Button(frame_btn, text="👁️ Detalhes",
           bg=COR_AZUL, width=18,
           command=ver_detalhes,
           **estilo_btn).pack(side=LEFT, padx=5, pady=8)
    
    # Aprovar (só admin)
    if utilizador_logado["perfil"] == "admin":
        def aprovar():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Aviso", "Selecione um deposito.")
                return
            
            estado = tree.item(sel[0])["values"][8]
            if estado != "PENDENTE_APROVACAO":
                messagebox.showinfo("Info",
                    "Este deposito nao esta pendente de aprovacao.")
                return
            
            dep_id = tree.item(sel[0])["values"][0]
            referencia = tree.item(sel[0])["values"][1]
            valor = tree.item(sel[0])["values"][5]
            
            ok, nome = pedir_senha_admin(
                janela,
                f"Aprovar o deposito:\n\n"
                f"Referencia: {referencia}\n"
                f"Valor: {valor}\n\n"
                f"Digite a senha do administrador para aprovar."
            )
            
            if not ok:
                return
            
            if aprovar_deposito(dep_id, nome):
                registar_auditoria(
                    utilizador_logado["id"], utilizador_logado["nome"],
                    "APROVAR DEPOSITO",
                    f"{referencia} | {valor} | Aprovado por: {nome}"
                )
                messagebox.showinfo("Sucesso",
                    f"Deposito {referencia} aprovado por {nome}.")
                carregar()
            else:
                messagebox.showerror("Erro", "Erro ao aprovar.")
        
        Button(frame_btn, text="✅ Aprovar",
               bg=COR_ALERTA, width=18,
               command=aprovar,
               **estilo_btn).pack(side=LEFT, padx=5, pady=8)
    
    # Actualizar + Fechar
    Button(frame_btn, text="🔄 Actualizar",
           bg="#64748b", width=15,
           command=carregar,
           **estilo_btn).pack(side=LEFT, padx=5, pady=8)
    
    Button(frame_btn, text="❌ Fechar",
           bg=COR_VERMELHO, width=15,
           command=janela.destroy,
           **estilo_btn).pack(side=RIGHT, padx=(5, 20), pady=8)
    
    # Carregar inicial
    carregar()


# ============================================================
# ============ NOVO DEPOSITO =================================
# ============================================================

def dialogo_novo_deposito(utilizador_logado, parent, callback=None):
    """Dialogo para criar um novo deposito."""
    
    janela = Toplevel(parent)
    janela.title("Novo Deposito")
    janela.geometry("600x750")
    janela.configure(bg=COR_FUNDO)
    janela.transient(parent)
    janela.grab_set()
    
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 600) // 2
    y = (janela.winfo_screenheight() - 750) // 2
    janela.geometry(f"600x750+{x}+{y}")
    
    # Header
    header = Frame(janela, bg=COR_VERDE, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="➕ Novo Deposito Bancario",
          font=("Segoe UI", 16, "bold"),
          bg=COR_VERDE, fg="white").pack(pady=20)
    
    # Info topo
    limite = obter_config_financeira("limite_deposito_gerente", "500000")
    try:
        limite_val = float(limite)
    except Exception:
        limite_val = 500000.0
    
    info = Frame(janela, bg=COR_CARD, highlightthickness=1,
                  highlightbackground=COR_DOURADO)
    info.pack(fill=X, padx=20, pady=15)
    
    Label(info, text=f"Limite sem aprovacao: {formatar_kz(limite_val)}",
          font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_DOURADO).pack(pady=10)
    Label(info, text=f"Acima deste valor, precisa aprovacao do administrador.",
          font=("Segoe UI", 9, "italic"),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(0, 10))
    
    # Formulario
    frame = Frame(janela, bg=COR_CARD, highlightthickness=1,
                   highlightbackground=COR_BORDA)
    frame.pack(padx=20, pady=10, fill=X)
    
    inner = Frame(frame, bg=COR_CARD)
    inner.pack(padx=25, pady=20, fill=X)
    
    # Valor
    Label(inner, text="Valor depositado (Kz): *",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
    e_valor = Entry(inner, font=("Segoe UI", 14), bd=1, relief=SOLID, justify=CENTER)
    e_valor.pack(fill=X, ipady=8)
    e_valor.focus()
    
    Label(inner, text="Ex: 500.000,00 ou 500000",
          font=("Segoe UI", 9, "italic"),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W, pady=(3, 10))
    
    # Banco
    Label(inner, text="Banco: *",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
    bancos = listar_bancos_ativos()
    banco_var = StringVar(value=bancos[0] if bancos else "BAI")
    combo_banco = ttk.Combobox(inner, textvariable=banco_var,
                                 values=bancos, state="readonly",
                                 font=("Segoe UI", 11))
    combo_banco.pack(fill=X, ipady=5)
    
    # Comprovante
    Label(inner, text="Numero do Comprovante: *",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(15, 3))
    e_comp = Entry(inner, font=("Segoe UI", 12), bd=1, relief=SOLID)
    e_comp.pack(fill=X, ipady=6)
    Label(inner, text="Numero impresso no comprovante do banco",
          font=("Segoe UI", 9, "italic"),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W, pady=(3, 10))
    
    # Observacoes
    Label(inner, text="Observacoes (opcional):",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
    text_obs = Text(inner, height=3, font=("Segoe UI", 11), bd=1, relief=SOLID)
    text_obs.pack(fill=X)
    
    # Aviso
    aviso_var = StringVar(value="")
    aviso_label = Label(janela, textvariable=aviso_var,
                          font=("Segoe UI", 10, "bold"),
                          bg=COR_FUNDO, fg=COR_ALERTA,
                          wraplength=500, justify=CENTER)
    aviso_label.pack(pady=10, padx=20)
    
    def confirmar():
        # 1. Ler valores
        valor_txt = e_valor.get().replace(".", "").replace(",", ".").strip()
        try:
            valor = float(valor_txt)
            if valor <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Aviso", "Valor invalido.")
            return
        
        banco = banco_var.get().strip()
        if not banco:
            messagebox.showwarning("Aviso", "Escolha o banco.")
            return
        
        comp = e_comp.get().strip()
        if not comp:
            messagebox.showwarning("Aviso", "O numero do comprovante e obrigatorio.")
            return
        
        obs = text_obs.get("1.0", END).strip()
        
        # 2. Se valor > limite -> pedir aprovacao admin ANTES
        precisa_aprovacao = valor > limite_val
        
        nome_aprovador = None
        if precisa_aprovacao:
            if utilizador_logado["perfil"] == "admin":
                # O admin pode aprovar-se a si proprio
                nome_aprovador = utilizador_logado["nome"]
            else:
                # Gerente precisa de admin
                ok, nome = pedir_senha_admin(
                    janela,
                    f"O valor {formatar_kz(valor)} excede o limite de "
                    f"{formatar_kz(limite_val)}.\n\n"
                    f"E necessaria aprovacao do administrador."
                )
                if not ok:
                    messagebox.showwarning("Cancelado",
                        "Deposito nao autorizado.")
                    return
                nome_aprovador = nome
        
        # 3. Criar deposito
        try:
            referencia, estado, precisa_apr = criar_deposito(
                valor, banco, comp, obs,
                utilizador_logado["id"],
                utilizador_logado["nome"]
            )
            
            # Se foi necessaria aprovacao, aprovar imediatamente
            if precisa_apr and nome_aprovador:
                # Buscar o ID do deposito recem-criado
                conn = __import__('database').conectar()
                cur = conn.cursor()
                cur.execute("SELECT id FROM depositos WHERE referencia = ?",
                              (referencia,))
                r = cur.fetchone()
                conn.close()
                
                if r:
                    aprovar_deposito(r[0], nome_aprovador)
                    estado = "APROVADO"
            
            registar_auditoria(
                utilizador_logado["id"], utilizador_logado["nome"],
                "NOVO DEPOSITO",
                f"{referencia} | {formatar_kz(valor)} | {banco} | "
                f"Comp: {comp} | Estado: {estado}"
            )
            
            msg = (
                f"Deposito registado com sucesso!\n\n"
                f"Referencia: {referencia}\n"
                f"Valor: {formatar_kz(valor)}\n"
                f"Banco: {banco}\n"
                f"Comprovante: {comp}\n"
                f"Estado: {estado}"
            )
            
            if precisa_apr:
                msg += f"\n\nAprovado por: {nome_aprovador}"
            
            messagebox.showinfo("Deposito Criado", msg)
            
            janela.destroy()
            if callback:
                callback()
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar deposito: {e}")
    
    # Preview do valor
    def atualizar_preview(event=None):
        valor_txt = e_valor.get().replace(".", "").replace(",", ".").strip()
        try:
            valor = float(valor_txt)
            if valor > limite_val:
                aviso_var.set(
                    f"⚠️ Valor {formatar_kz(valor)} acima do limite — "
                    f"precisa aprovacao do admin"
                )
                aviso_label.config(fg=COR_ALERTA)
            elif valor > 0:
                aviso_var.set(f"Valor: {formatar_kz(valor)} — dentro do limite")
                aviso_label.config(fg=COR_VERDE)
            else:
                aviso_var.set("")
        except ValueError:
            aviso_var.set("")
    
    e_valor.bind('<KeyRelease>', atualizar_preview)
    e_comp.bind('<Return>', lambda e: confirmar())
    
    # Botoes
    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=15)
    
    Button(frame_btn, text="💾 Confirmar Deposito",
           font=("Segoe UI", 12, "bold"),
           bg=COR_VERDE, fg="white",
           width=22, height=2, bd=0, cursor="hand2",
           activebackground="#059669",
           command=confirmar).pack(side=LEFT, padx=5)
    
    Button(frame_btn, text="❌ Cancelar",
           font=("Segoe UI", 11),
           bg="#64748b", fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=5)


# ============================================================
# ============ DETALHES ======================================
# ============================================================

def dialogo_detalhes(dep_id, utilizador_logado, parent, callback=None):
    """Mostra os detalhes de um deposito."""
    
    d = obter_deposito(dep_id)
    if not d:
        messagebox.showerror("Erro", "Deposito nao encontrado.")
        return
    
    # d = (id, referencia, data, hora, valor, banco, comp, obs,
    #      turno_id, gerente_id, gerente_nome, estado, aprov_por,
    #      data_aprov, criado_em)
    (did, referencia, data, hora, valor, banco, comp, obs, turno_id,
     ger_id, ger_nome, estado, aprov_por, data_aprov, criado_em) = d
    
    janela = Toplevel(parent)
    janela.title(f"Deposito {referencia}")
    janela.geometry("600x650")
    janela.configure(bg=COR_FUNDO)
    janela.transient(parent)
    janela.grab_set()
    
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 600) // 2
    y = (janela.winfo_screenheight() - 650) // 2
    janela.geometry(f"600x650+{x}+{y}")
    
    # Header
    header = Frame(janela, bg=COR_PRIMARIA, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text=f"📋 {referencia}",
          font=("Segoe UI", 16, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=20)
    
    # Card
    card = Frame(janela, bg=COR_CARD, highlightthickness=1,
                   highlightbackground=COR_BORDA)
    card.pack(padx=20, pady=15, fill=X)
    
    def linha(label, valor, cor=COR_TEXTO):
        f = Frame(card, bg=COR_CARD)
        f.pack(fill=X, padx=20, pady=5)
        Label(f, text=label,
              font=("Segoe UI", 10, "bold"),
              bg=COR_CARD, fg=COR_TEXTO_SEC, width=18, anchor=W).pack(side=LEFT)
        Label(f, text=valor or "-",
              font=("Segoe UI", 10),
              bg=COR_CARD, fg=cor, anchor=W,
              wraplength=350, justify=LEFT).pack(side=LEFT, fill=X, expand=True)
    
    linha("Referencia:", referencia)
    linha("Data:", f"{data} {hora}")
    linha("Banco:", banco)
    linha("Valor:", formatar_kz(valor), COR_VERDE)
    linha("Comprovante:", comp)
    linha("Gerente:", ger_nome)
    linha("Estado:", estado,
          COR_VERDE if estado in ("REGISTADO", "APROVADO") else
          COR_ALERTA if estado == "PENDENTE_APROVACAO" else COR_VERMELHO)
    
    if aprov_por:
        linha("Aprovado por:", aprov_por, COR_VERDE)
    if data_aprov:
        linha("Data aprovacao:", data_aprov)
    if turno_id:
        linha("Turno:", f"#{turno_id}")
    if obs:
        linha("Observacoes:", obs)
    
    # Botoes
    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=15)
    
    def cancelar_dep():
        if utilizador_logado["perfil"] != "admin":
            messagebox.showerror("Sem permissao",
                "Apenas administradores podem cancelar depositos.")
            return
        
        if estado == "CANCELADO":
            messagebox.showinfo("Info", "Ja esta cancelado.")
            return
        
        motivo = __import__('tkinter.simpledialog', fromlist=['askstring'])
        motivo = motivo.askstring("Motivo", "Motivo do cancelamento:", parent=janela)
        if not motivo:
            return
        
        if cancelar_deposito(did, motivo, utilizador_logado["nome"]):
            registar_auditoria(
                utilizador_logado["id"], utilizador_logado["nome"],
                "CANCELAR DEPOSITO",
                f"{referencia} | Motivo: {motivo}"
            )
            messagebox.showinfo("Sucesso", "Deposito cancelado.")
            janela.destroy()
            if callback:
                callback()
    
    if (utilizador_logado["perfil"] == "admin" and
            estado != "CANCELADO"):
        Button(frame_btn, text="🚫 Cancelar Deposito",
               font=("Segoe UI", 10, "bold"),
               bg=COR_VERMELHO, fg="white",
               width=20, height=2, bd=0, cursor="hand2",
               command=cancelar_dep).pack(side=LEFT, padx=5)
    
    Button(frame_btn, text="Fechar",
           font=("Segoe UI", 11),
           bg="#64748b", fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=5)


# ============================================================
# ============ TESTE DIRETO ==================================
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  TESTE - depositos.py")
    print("="*60)
    
    print("\n[1] Bancos disponiveis:")
    for b in listar_bancos_ativos():
        print(f"    - {b}")
    
    print("\n[2] Saldo actual:")
    print(f"    {formatar_kz(saldo_atual_farmacia())}")
    
    print("\n[3] Depositos existentes:")
    deps = listar_depositos(10)
    if deps:
        for d in deps:
            print(f"    {d[1]} | {d[2]} | {d[5]} | {formatar_kz(d[4])} | {d[9]}")
    else:
        print("    (nenhum)")
    
    print("\n" + "="*60 + "\n")