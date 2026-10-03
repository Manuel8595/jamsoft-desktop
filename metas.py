# ============================================================
# ============ GESTAO DE METAS E ORCAMENTOS ==================
# ============================================================
# 
# Ecra onde:
#   - Todos veem o orcamento e progresso
#   - So o admin pode definir/alterar o orcamento mensal
#   - Historico de orcamentos anteriores
# 
# ============================================================

from tkinter import *
from tkinter import messagebox, ttk
from datetime import datetime
from database import (obter_orcamento_mes, definir_orcamento_mes,
                       progresso_mes, listar_dias, registar_auditoria,
                       autenticar, conectar)
from moeda import formatar_kz
from seguranca import verificar_acesso


COR_FUNDO = "#0f172a"
COR_CARD = "#1e293b"
COR_CARD_HOVER = "#334155"
COR_PRIMARIA = "#7c3aed"
COR_DOURADO = "#fbbf24"
COR_VERDE = "#10b981"
COR_VERMELHO = "#ef4444"
COR_ALERTA = "#f97316"
COR_AMARELO = "#eab308"
COR_AZUL = "#0ea5e9"
COR_TEXTO = "#f8fafc"
COR_TEXTO_SEC = "#94a3b8"
COR_BORDA = "#334155"


# ============================================================
# ============ HELPER: NOME DO MES ===========================
# ============================================================

MESES_PT = {
    "01": "Janeiro", "02": "Fevereiro", "03": "Marco",
    "04": "Abril", "05": "Maio", "06": "Junho",
    "07": "Julho", "08": "Agosto", "09": "Setembro",
    "10": "Outubro", "11": "Novembro", "12": "Dezembro",
}


def nome_mes(mes_str):
    """Converte '2026-09' em 'Setembro 2026'."""
    try:
        ano, m = mes_str.split("-")
        return f"{MESES_PT.get(m, m)} {ano}"
    except Exception:
        return mes_str


def obter_cor_por_percentagem(percentagem):
    """Retorna cor conforme a percentagem."""
    if percentagem >= 100:
        return COR_VERDE
    elif percentagem >= 80:
        return COR_AMARELO
    elif percentagem >= 50:
        return COR_ALERTA
    elif percentagem >= 25:
        return COR_AZUL
    else:
        return COR_VERMELHO


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
    Label(header, text="CONFIRMACAO NECESSARIA",
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
        
        if sucesso and dados["perfil"] == "admin":
            resultado["ok"] = True
            resultado["nome"] = dados["nome"]
            auth.destroy()
        elif sucesso:
            msg_var.set("Apenas administradores podem autorizar")
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
# ============ CRIAR BARRA DE PROGRESSO ======================
# ============================================================

def criar_barra_progresso(parent, percentagem, cor, largura=380, altura=22):
    """Cria uma barra de progresso visual."""
    visual = min(percentagem, 100)
    
    canvas = Canvas(parent, width=largura, height=altura,
                     bg="#334155", highlightthickness=0)
    canvas.pack(fill=X, pady=5)
    
    largura_preenchida = (visual / 100) * largura
    
    if largura_preenchida > 0:
        canvas.create_rectangle(
            0, 0, largura_preenchida, altura,
            fill=cor, outline=""
        )
    
    canvas.create_text(
        largura / 2, altura / 2,
        text=f"{percentagem:.1f}%",
        fill="white",
        font=("Segoe UI", 11, "bold")
    )
    
    return canvas


# ============================================================
# ============ ECRAN PRINCIPAL ===============================
# ============================================================

def abrir_metas(utilizador_logado, parent=None):
    """Abre o ecra de gestao de metas e orcamentos."""
    
    if parent is None:
        parent = Toplevel()
        parent.withdraw()
    
    janela = Toplevel(parent)
    janela.title("Gestao de Metas e Orcamentos")
    janela.geometry("1000x800")
    janela.configure(bg=COR_FUNDO)
    
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 1000) // 2
    y = (janela.winfo_screenheight() - 800) // 2
    janela.geometry(f"1000x800+{x}+{y}")
    
    # Header
    header = Frame(janela, bg=COR_PRIMARIA, height=90)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Gestao de Metas e Orcamentos",
          font=("Segoe UI", 20, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=(15, 0))
    Label(header, text=f"Utilizador: {utilizador_logado['nome']}  |  "
                        f"Perfil: {utilizador_logado['perfil'].upper()}",
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
    
    mes_atual = datetime.now().strftime("%Y-%m")
    orcamento = obter_orcamento_mes(mes_atual)
    progresso = progresso_mes(mes_atual)
    
    pode_definir = (utilizador_logado["perfil"] == "admin")
    
    # ===== CARD DO MES ATUAL =====
    Label(content, text=f"Orcamento do Mes Atual — {nome_mes(mes_atual)}",
          font=("Segoe UI", 13, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=30, pady=(20, 10))
    
    card = Frame(content, bg=COR_CARD, highlightthickness=2,
                  highlightbackground=COR_PRIMARIA)
    card.pack(fill=X, padx=30, pady=5)
    
    if progresso["orcamento"] <= 0:
        # Sem orcamento definido
        Label(card, text="ORCAMENTO NAO DEFINIDO",
              font=("Segoe UI", 16, "bold"),
              bg=COR_CARD, fg=COR_ALERTA).pack(pady=(25, 10))
        
        Label(card,
              text="Nenhum orcamento foi definido para este mes.\n"
                   "O administrador deve definir o orcamento mensal.",
              font=("Segoe UI", 11),
              bg=COR_CARD, fg=COR_TEXTO,
              justify=CENTER).pack(pady=(0, 15))
        
        Label(card,
              text=f"Vendido ate agora: {formatar_kz(progresso['vendido'])}",
              font=("Segoe UI", 12, "bold"),
              bg=COR_CARD, fg=COR_VERDE).pack(pady=(0, 20))
        
        if pode_definir:
            Button(card, text="DEFINIR ORCAMENTO",
                   font=("Segoe UI", 12, "bold"),
                   bg=COR_PRIMARIA, fg="white",
                   width=25, height=2, bd=0, cursor="hand2",
                   activebackground="#6d28d9",
                   command=lambda: dialogo_definir_orcamento(
                       janela, utilizador_logado, mes_atual, recarregar
                   )).pack(pady=(0, 25))
        else:
            Label(card,
                  text="(Apenas administradores podem definir o orcamento)",
                  font=("Segoe UI", 9, "italic"),
                  bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(0, 20))
    else:
        # Orcamento definido
        frame_info = Frame(card, bg=COR_CARD)
        frame_info.pack(fill=X, padx=30, pady=(20, 10))
        
        # Orcamento
        Label(frame_info, text="Orcamento mensal:",
              font=("Segoe UI", 10),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W)
        Label(frame_info, text=formatar_kz(progresso["orcamento"]),
              font=("Segoe UI", 16, "bold"),
              bg=COR_CARD, fg=COR_DOURADO).pack(anchor=W, pady=(0, 10))
        
        # Vendido
        cor_prog = obter_cor_por_percentagem(progresso["percentagem"])
        
        Label(frame_info, text="Vendido ate hoje:",
              font=("Segoe UI", 10),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W)
        Label(frame_info, text=formatar_kz(progresso["vendido"]),
              font=("Segoe UI", 16, "bold"),
              bg=COR_CARD, fg=cor_prog).pack(anchor=W, pady=(0, 15))
        
        # Barra de progresso
        frame_barra = Frame(card, bg=COR_CARD)
        frame_barra.pack(fill=X, padx=30, pady=(0, 10))
        criar_barra_progresso(frame_barra, progresso["percentagem"], cor_prog)
        
        # Falta / Atingido
        frame_falta = Frame(card, bg=COR_CARD)
        frame_falta.pack(fill=X, padx=30, pady=(5, 5))
        
        if progresso["percentagem"] >= 100:
            Label(frame_falta,
                  text=f"🎉 Meta batida! Excedente: {formatar_kz(progresso['vendido'] - progresso['orcamento'])}",
                  font=("Segoe UI", 12, "bold"),
                  bg=COR_CARD, fg=COR_VERDE).pack(anchor=W)
        else:
            Label(frame_falta,
                  text=f"Faltam: {formatar_kz(progresso['falta'])}",
                  font=("Segoe UI", 12, "bold"),
                  bg=COR_CARD, fg=COR_ALERTA).pack(anchor=W)
        
        # Projeccao
        projecao = calcular_projecao(progresso)
        frame_proj = Frame(card, bg=COR_CARD)
        frame_proj.pack(fill=X, padx=30, pady=(5, 5))
        
        Label(frame_proj,
              text=f"Projeccao de fecho: {formatar_kz(projecao)}",
              font=("Segoe UI", 11, "italic"),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W)
        
        if projecao < progresso["orcamento"]:
            Label(frame_proj,
                  text="(Ritmo abaixo do orcamento)",
                  font=("Segoe UI", 9),
                  bg=COR_CARD, fg=COR_ALERTA).pack(anchor=W)
        else:
            Label(frame_proj,
                  text="(Ritmo acima do orcamento)",
                  font=("Segoe UI", 9),
                  bg=COR_CARD, fg=COR_VERDE).pack(anchor=W)
        
        # Info de quem definiu
        if orcamento:
            frame_meta = Frame(card, bg=COR_CARD)
            frame_meta.pack(fill=X, padx=30, pady=(10, 5))
            
            Label(frame_meta,
                  text=f"Definido por: {orcamento[4] or '-'}",
                  font=("Segoe UI", 9, "italic"),
                  bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W)
            if orcamento[6]:
                Label(frame_meta,
                      text=f"Ultima atualizacao: {orcamento[6]}",
                      font=("Segoe UI", 9, "italic"),
                      bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W)
        
        # Botao DEFINIR/ALTERAR
        if pode_definir:
            Button(card, text="ALTERAR ORCAMENTO",
                   font=("Segoe UI", 12, "bold"),
                   bg=COR_PRIMARIA, fg="white",
                   width=25, height=2, bd=0, cursor="hand2",
                   activebackground="#6d28d9",
                   command=lambda: dialogo_definir_orcamento(
                       janela, utilizador_logado, mes_atual, recarregar
                   )).pack(pady=(15, 25))
        else:
            Label(card,
                  text="(Apenas administradores podem alterar o orcamento)",
                  font=("Segoe UI", 9, "italic"),
                  bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(15, 20))
    
    # ===== HISTORICO =====
    Label(content, text="Historico de Orcamentos",
          font=("Segoe UI", 13, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=30, pady=(25, 10))
    
    frame_tab = Frame(content, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=30, pady=(0, 20))
    
    colunas = ("Mes", "Orcamento", "Vendido", "%", "Estado", "Definido por")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=10)
    
    for col in colunas:
        tree.heading(col, text=col)
    
    tree.column("Mes", width=140)
    tree.column("Orcamento", width=160)
    tree.column("Vendido", width=160)
    tree.column("%", width=90)
    tree.column("Estado", width=120)
    tree.column("Definido por", width=150)
    
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    try:
        historico = obter_historico_orcamentos(12)
        for h in historico:
            mes, orc, vendido, perc, definido_por = h
            
            tag = ""
            if perc >= 100:
                tag = "batida"
                estado = "META BATIDA"
            elif perc >= 80:
                tag = "atencao"
                estado = "Quase la"
            elif perc >= 50:
                tag = "medio"
                estado = "Em curso"
            else:
                tag = "baixo"
                estado = "Abaixo"
            
            tree.insert("", END, values=(
                nome_mes(mes),
                formatar_kz(orc),
                formatar_kz(vendido),
                f"{perc:.1f}%",
                estado,
                definido_por or "-"
            ), tags=(tag,))
        
        tree.tag_configure("batida", foreground=COR_VERDE)
        tree.tag_configure("atencao", foreground=COR_AMARELO)
        tree.tag_configure("medio", foreground=COR_ALERTA)
        tree.tag_configure("baixo", foreground=COR_VERMELHO)
    except Exception as e:
        print(f"[Metas] Erro ao carregar historico: {e}")
    
    # Botoes inferiores
    frame_btns = Frame(content, bg=COR_FUNDO, height=50)
    frame_btns.pack(fill=X, side=BOTTOM)
    frame_btns.pack_propagate(False)
    
    Button(frame_btns, text="Actualizar",
           font=("Segoe UI", 11, "bold"),
           bg=COR_AZUL, fg="white",
           width=18, height=2, bd=0, cursor="hand2",
           activebackground="#0284c7",
           command=recarregar).pack(side=LEFT, padx=20, pady=8)
    
    Button(frame_btns, text="Fechar",
           font=("Segoe UI", 11, "bold"),
           bg=COR_VERMELHO, fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           activebackground="#dc2626",
           command=janela.destroy).pack(side=RIGHT, padx=20, pady=8)


# ============================================================
# ============ CALCULAR PROJECCAO ============================
# ============================================================

def calcular_projecao(progresso):
    """Calcula a projeccao de fecho do mes com base no ritmo actual."""
    hoje = datetime.now()
    dia_atual = hoje.day
    
    try:
        if hoje.month == 12:
            proximo = hoje.replace(year=hoje.year + 1, month=1, day=1)
        else:
            proximo = hoje.replace(month=hoje.month + 1, day=1)
        
        dias_no_mes = (proximo - hoje.replace(day=1)).days
    except Exception:
        dias_no_mes = 30
    
    if dia_atual <= 0:
        return 0
    
    media_diaria = progresso["vendido"] / dia_atual
    return media_diaria * dias_no_mes


# ============================================================
# ============ DIALOGO: DEFINIR ORCAMENTO ====================
# ============================================================

def dialogo_definir_orcamento(parent, utilizador_logado, mes, callback=None):
    """Dialogo para definir ou alterar o orcamento mensal."""
    
    # Verifica se e admin
    if utilizador_logado["perfil"] != "admin":
        messagebox.showerror("Sem permissao",
            "Apenas administradores podem definir o orcamento.")
        return
    
    orcamento_atual = obter_orcamento_mes(mes)
    valor_atual = orcamento_atual[2] if orcamento_atual else 0
    
    janela = Toplevel(parent)
    janela.title("Definir Orcamento Mensal")
    janela.geometry("500x520")
    janela.configure(bg=COR_FUNDO)
    janela.transient(parent)
    janela.grab_set()
    
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 500) // 2
    y = (janela.winfo_screenheight() - 520) // 2
    janela.geometry(f"500x520+{x}+{y}")
    
    header = Frame(janela, bg=COR_PRIMARIA, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Definir Orcamento",
          font=("Segoe UI", 16, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=(15, 0))
    Label(header, text=nome_mes(mes),
          font=("Segoe UI", 11, "italic"),
          bg=COR_PRIMARIA, fg="#e0e7ff").pack()
    
    card = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground=COR_BORDA)
    card.pack(fill=X, padx=25, pady=20)
    
    frame = Frame(card, bg=COR_CARD)
    frame.pack(padx=25, pady=25, fill=X)
    
    Label(frame, text="Orcamento mensal (Kz):",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 5))
    
    e_valor = Entry(frame, font=("Segoe UI", 16), bd=1, relief=SOLID, justify=CENTER)
    e_valor.pack(fill=X, ipady=8)
    if valor_atual > 0:
        e_valor.insert(0, f"{valor_atual:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    e_valor.focus()
    
    Label(frame, text="Ex: 15.000.000,00",
          font=("Segoe UI", 9, "italic"),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W, pady=(3, 15))
    
    Label(frame, text="Observacoes (opcional):",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 5))
    
    text_obs = Text(frame, height=3, font=("Segoe UI", 11), bd=1, relief=SOLID)
    if orcamento_atual and orcamento_atual[3]:
        text_obs.insert("1.0", orcamento_atual[3])
    text_obs.pack(fill=X)
    
    msg_var = StringVar()
    Label(janela, textvariable=msg_var,
          font=("Segoe UI", 10),
          bg=COR_FUNDO, fg=COR_VERMELHO).pack()
    
    def confirmar():
        # 1. Ler valor
        texto = e_valor.get().strip()
        texto = texto.replace(" ", "").replace("Kz", "").strip()
        
        try:
            valor = float(texto.replace(".", "").replace(",", "."))
        except ValueError:
            msg_var.set("Valor invalido. Use formato: 15.000.000,00")
            return
        
        if valor <= 0:
            msg_var.set("O valor tem de ser positivo.")
            return
        
        obs = text_obs.get("1.0", END).strip()
        
        # 2. Pedir senha do admin
        ok, nome_admin = pedir_senha_admin(
            janela,
            f"Esta prestes a definir/alterar o orcamento do mes.\n\n"
            f"Mes: {nome_mes(mes)}\n"
            f"Novo valor: {formatar_kz(valor)}\n\n"
            f"Digite a senha do administrador para confirmar."
        )
        
        if not ok:
            msg_var.set("Operacao cancelada.")
            return
        
        # 3. Gravar
        try:
            definir_orcamento_mes(mes, valor, nome_admin, obs)
            
            registar_auditoria(
                utilizador_logado["id"],
                utilizador_logado["nome"],
                "DEFINIR ORCAMENTO",
                f"Mes: {mes} | Valor: {formatar_kz(valor)} | "
                f"Anterior: {formatar_kz(valor_atual)} | "
                f"Confirmado por: {nome_admin}"
            )
            
            messagebox.showinfo("Sucesso",
                f"Orcamento definido com sucesso!\n\n"
                f"Mes: {nome_mes(mes)}\n"
                f"Valor: {formatar_kz(valor)}")
            
            janela.destroy()
            if callback:
                callback()
        except Exception as e:
            msg_var.set(f"Erro: {e}")
    
    e_valor.bind('<Return>', lambda e: text_obs.focus())
    
    # Botoes
    frame_btns = Frame(janela, bg=COR_FUNDO)
    frame_btns.pack(pady=15)
    
    Button(frame_btns, text="Confirmar",
           font=("Segoe UI", 12, "bold"),
           bg=COR_VERDE, fg="white",
           width=18, height=2, bd=0, cursor="hand2",
           activebackground="#059669",
           command=confirmar).pack(side=LEFT, padx=8)
    
    Button(frame_btns, text="Cancelar",
           font=("Segoe UI", 11),
           bg="#64748b", fg="white",
           width=14, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, padx=8)


# ============================================================
# ============ HELPER: HISTORICO DE ORCAMENTOS ===============
# ============================================================

def obter_historico_orcamentos(limite=12):
    """Retorna historico de orcamentos dos ultimos meses.
    Retorna: [(mes, orcamento, vendido, %, definido_por), ...]
    """
    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT mes, orcamento_mes, definido_por
        FROM metas_farmacia
        ORDER BY mes DESC LIMIT ?
    """, (limite,))
    
    metas = cur.fetchall()
    
    resultado = []
    for mes, orcamento, definido_por in metas:
        # Vendas desse mes
        cur.execute("""
            SELECT COALESCE(SUM(total), 0) FROM vendas
            WHERE strftime('%Y-%m', data) = ?
        """, (mes,))
        vendido = cur.fetchone()[0] or 0
        
        perc = (vendido / orcamento * 100) if orcamento > 0 else 0
        
        resultado.append((mes, orcamento, vendido, perc, definido_por))
    
    conn.close()
    return resultado


# ============================================================
# ============ TESTE DIRETO ==================================
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  TESTE - metas.py")
    print("="*60)
    
    print("\n[1] Nome dos meses:")
    for m in ["2026-01", "2026-06", "2026-09", "2026-12"]:
        print(f"    {m} -> {nome_mes(m)}")
    
    print("\n[2] Orcamento do mes atual:")
    mes = datetime.now().strftime("%Y-%m")
    o = obter_orcamento_mes(mes)
    if o:
        print(f"    Mes: {o[1]}")
        print(f"    Orcamento: {o[2]}")
        print(f"    Definido por: {o[4]}")
    else:
        print("    Nenhum orcamento definido")
    
    print("\n[3] Progresso do mes:")
    p = progresso_mes(mes)
    for k, v in p.items():
        print(f"    {k}: {v}")
    
    print("\n[4] Historico:")
    h = obter_historico_orcamentos(12)
    for item in h:
        print(f"    {item}")
    
    print("\n" + "="*60 + "\n")