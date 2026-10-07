# ============================================================
# ============ GESTAO DO DIA DE OPERACAO =====================
# ============================================================

from tkinter import *
from tkinter import messagebox, ttk
from datetime import datetime
from database import (dia_aberto, abrir_dia, fechar_dia, obter_dia,
                       consolidar_dia, verificar_turnos_abertos,
                       listar_dias, registar_auditoria, autenticar,
                       obter_config_financeira, conectar)
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
COR_AZUL = "#0ea5e9"
COR_TEXTO = "#f8fafc"
COR_TEXTO_SEC = "#94a3b8"
COR_BORDA = "#334155"


def pedir_senha_gerente(parent, motivo):
    """Pede senha do gerente ou admin."""
    resultado = {"ok": False, "nome": None}

    auth = Toplevel(parent)
    auth.title("Autorizacao do Gerente")
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
    Label(header, text="AUTORIZACAO NECESSARIA",
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

    Button(auth, text="Autorizar",
           font=("Segoe UI", 12, "bold"),
           bg=COR_VERDE, fg="white",
           width=20, height=2, bd=0, cursor="hand2",
           activebackground="#059669",
           command=confirmar).pack(pady=20)

    auth.wait_window()
    return resultado["ok"], resultado["nome"]


def obter_dias_abertos_antigos():
    """Retorna dias ABERTOS em datas anteriores a hoje."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, data, hora_abertura, gerente_abertura_nome
        FROM dias_operacao
        WHERE estado = 'ABERTO' AND data < ?
        ORDER BY data ASC
    """, (hoje,))
    resultado = cur.fetchall()
    conn.close()
    return resultado


def abrir_fecho_dia(utilizador_logado, parent=None):
    """Abre o ecra de gestao do dia."""
    if not verificar_acesso(utilizador_logado, "caixa.fecho_dia", "Gestao do Dia"):
        return

    if parent is None:
        parent = Toplevel()
        parent.withdraw()

    janela = Toplevel(parent)
    janela.title("Gestao do Dia de Operacao")
    janela.geometry("950x850")
    janela.configure(bg=COR_FUNDO)

    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 950) // 2
    y = (janela.winfo_screenheight() - 850) // 2
    janela.geometry(f"950x850+{x}+{y}")

    header = Frame(janela, bg=COR_PRIMARIA, height=90)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Gestao do Dia de Operacao",
          font=("Segoe UI", 20, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=(15, 0))
    Label(header, text=f"Operador: {utilizador_logado['nome']}  |  "
                        f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
          font=("Segoe UI", 10, "italic"),
          bg=COR_PRIMARIA, fg="#e0e7ff").pack()

    content = Frame(janela, bg=COR_FUNDO)
    content.pack(fill=BOTH, expand=True)

    def recarregar():
        for w in content.winfo_children():
            w.destroy()
        construir_conteudo(content, utilizador_logado, janela, recarregar)

    construir_conteudo(content, utilizador_logado, janela, recarregar)


def construir_conteudo(content, utilizador_logado, janela, recarregar):
    """Constroi o conteudo."""

    hoje = datetime.now().strftime("%Y-%m-%d")
    dia = dia_aberto()

    # ===== ALERTA: DIAS ANTIGOS ABERTOS =====
    dias_antigos = obter_dias_abertos_antigos()

    if dias_antigos:
        card_aviso = Frame(content, bg="#3f1a1a",
                            highlightthickness=2, highlightbackground=COR_VERMELHO)
        card_aviso.pack(fill=X, padx=25, pady=(15, 5))

        Label(card_aviso,
              text=f"⚠️  EXISTEM {len(dias_antigos)} DIA(S) ANTIGO(S) AINDA ABERTO(S)",
              font=("Segoe UI", 13, "bold"),
              bg="#3f1a1a", fg=COR_VERMELHO).pack(pady=(12, 5))

        for d in dias_antigos:
            did, data, hora, gerente = d
            linha = Frame(card_aviso, bg="#3f1a1a")
            linha.pack(fill=X, padx=20, pady=3)

            Label(linha, text=f"  • {data} (aberto às {hora} por {gerente})",
                  font=("Segoe UI", 10),
                  bg="#3f1a1a", fg=COR_TEXTO).pack(side=LEFT)

            Button(linha, text="Fechar Este Dia",
                   font=("Segoe UI", 9, "bold"),
                   bg=COR_VERMELHO, fg="white",
                   bd=0, cursor="hand2", padx=10, pady=3,
                   command=lambda d=did, dt=data: executar_fecho_dia_completo(
                       d, dt, utilizador_logado, janela, recarregar
                   )).pack(side=RIGHT)

        Label(card_aviso,
              text="Feche estes dias antes de abrir o dia de hoje.",
              font=("Segoe UI", 9, "italic"),
              bg="#3f1a1a", fg=COR_TEXTO_SEC).pack(pady=(5, 12))

    # ===== ESTADO ATUAL =====
    if dia:
        card_estado = Frame(content, bg=COR_CARD, highlightthickness=2,
                             highlightbackground=COR_VERDE)
        card_estado.pack(fill=X, padx=25, pady=20)

        Label(card_estado, text="DIA ABERTO",
              font=("Segoe UI", 18, "bold"),
              bg=COR_CARD, fg=COR_VERDE).pack(pady=(15, 5))

        Label(card_estado,
              text=f"Aberto as {dia[2]} por {dia[3]}",
              font=("Segoe UI", 12),
              bg=COR_CARD, fg=COR_TEXTO).pack()

        Label(card_estado, text=f"Data: {hoje}",
              font=("Segoe UI", 11, "italic"),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(5, 15))

        dados = consolidar_dia(hoje)
        turnos_abertos = verificar_turnos_abertos(hoje)

        resumo_frame = Frame(card_estado, bg=COR_CARD)
        resumo_frame.pack(pady=(0, 15), padx=20, fill=X)

        col1 = Frame(resumo_frame, bg=COR_CARD)
        col1.pack(side=LEFT, expand=True, fill=X)

        def linha_info(parent, label, valor, cor=COR_TEXTO):
            f = Frame(parent, bg=COR_CARD)
            f.pack(fill=X, pady=2)
            Label(f, text=label, font=("Segoe UI", 10),
                  bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W)
            Label(f, text=valor, font=("Segoe UI", 12, "bold"),
                  bg=COR_CARD, fg=cor).pack(anchor=W)

        linha_info(col1, "Turnos fechados:", str(dados["num_turnos"]), COR_AZUL)
        linha_info(col1, "Turnos abertos:", str(len(turnos_abertos)),
                    COR_VERMELHO if turnos_abertos else COR_VERDE)
        linha_info(col1, "Total vendido:", formatar_kz(dados["total_vendas"]), COR_VERDE)

        col2 = Frame(resumo_frame, bg=COR_CARD)
        col2.pack(side=LEFT, expand=True, fill=X)

        linha_info(col2, "Clientes atendidos:", str(dados["total_clientes"]), COR_DOURADO)
        linha_info(col2, "Ticket medio:", formatar_kz(dados["ticket_medio"]), COR_DOURADO)
        linha_info(col2, "Dinheiro fisico:", formatar_kz(dados["total_dinheiro"]), COR_VERDE)

        if turnos_abertos:
            aviso = Frame(card_estado, bg="#3f2a13", highlightthickness=1,
                           highlightbackground=COR_ALERTA)
            aviso.pack(fill=X, padx=20, pady=(0, 10))
            Label(aviso, text=f"ATENCAO: {len(turnos_abertos)} turno(s) aberto(s) — "
                              f"feche antes de fechar o dia",
                  font=("Segoe UI", 10, "bold"),
                  bg="#3f2a13", fg=COR_ALERTA).pack(pady=8, padx=15)

        btn_frame = Frame(card_estado, bg=COR_CARD)
        btn_frame.pack(pady=(5, 20))

        Button(btn_frame, text="FECHAR O DIA",
               font=("Segoe UI", 13, "bold"),
               bg=COR_ALERTA, fg="white",
               width=28, height=2, bd=0, cursor="hand2",
               activebackground="#ea580c",
               command=lambda: executar_fecho_dia_completo(
                   None, hoje, utilizador_logado, janela, recarregar
               )).pack()

        Label(btn_frame, text="(Pede senha do gerente ou administrador)",
              font=("Segoe UI", 9, "italic"),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(5, 0))

    else:
        card_estado = Frame(content, bg=COR_CARD, highlightthickness=2,
                             highlightbackground=COR_ALERTA)
        card_estado.pack(fill=X, padx=25, pady=20)

        Label(card_estado, text="NENHUM DIA ABERTO",
              font=("Segoe UI", 18, "bold"),
              bg=COR_CARD, fg=COR_ALERTA).pack(pady=(15, 5))

        Label(card_estado,
              text="Para comecar a operar (vendas, PDV), e necessario\n"
                   "abrir o dia primeiro.",
              font=("Segoe UI", 11),
              bg=COR_CARD, fg=COR_TEXTO,
              justify=CENTER).pack(pady=(5, 15))

        Label(card_estado, text=f"Data de hoje: {hoje}",
              font=("Segoe UI", 10, "italic"),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(0, 10))

        Button(card_estado, text="ABRIR O DIA",
               font=("Segoe UI", 13, "bold"),
               bg=COR_VERDE, fg="white",
               width=28, height=2, bd=0, cursor="hand2",
               activebackground="#059669",
               command=lambda: executar_abertura_dia(utilizador_logado, janela,
                                                       recarregar)
               ).pack(pady=(5, 20))

    # ===== HISTORICO =====
    Label(content, text="Historico dos Ultimos Dias",
          font=("Segoe UI", 13, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=30, pady=(20, 10))

    frame_tab = Frame(content, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=25, pady=(0, 20))

    colunas = ("Data", "Abertura", "Fecho", "Aberto por", "Fechado por",
               "Vendas", "Clientes", "Estado")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=10)

    for col in colunas:
        tree.heading(col, text=col)

    tree.column("Data", width=100)
    tree.column("Abertura", width=80)
    tree.column("Fecho", width=80)
    tree.column("Aberto por", width=130)
    tree.column("Fechado por", width=130)
    tree.column("Vendas", width=120)
    tree.column("Clientes", width=80)
    tree.column("Estado", width=100)

    tree.pack(fill=BOTH, expand=True, side=LEFT)

    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)

    try:
        dias = listar_dias(30)
        for d in dias:
            (did, data, hr_ab, hr_fc, ger_ab, ger_fc,
             total_vend, total_cli, total_din, perc, estado) = d

            tag = "aberto" if estado == "ABERTO" else "fechado"

            tree.insert("", END, values=(
                data or "-",
                hr_ab or "-",
                hr_fc or "-",
                (ger_ab or "-")[:18],
                (ger_fc or "-")[:18],
                formatar_kz(total_vend or 0),
                str(total_cli or 0),
                estado
            ), tags=(tag,))

        tree.tag_configure("aberto", foreground=COR_VERDE)
        tree.tag_configure("fechado", foreground=COR_TEXTO_SEC)
    except Exception as e:
        print(f"[FechoDia] Erro ao carregar historico: {e}")

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


def obter_resumo_dia_antigo(data):
    """Calcula o resumo de um dia antigo (turnos, vendas, etc)."""
    conn = conectar()
    cur = conn.cursor()

    # Turnos fechados desse dia
    cur.execute("""
        SELECT COUNT(*), COALESCE(SUM(total_vendas), 0),
               COALESCE(SUM(total_dinheiro), 0),
               COALESCE(SUM(total_tpa), 0),
               COALESCE(SUM(diferenca), 0)
        FROM turnos_caixa
        WHERE DATE(data_abertura) = DATE(?) AND estado = 'FECHADO'
    """, (data,))
    r = cur.fetchone()
    num_turnos = r[0] or 0
    total_vendas = r[1] or 0
    total_dinheiro = r[2] or 0
    total_tpa = r[3] or 0
    total_diferenca = r[4] or 0

    # Turnos AINDA abertos nesse dia
    cur.execute("""
        SELECT COUNT(*) FROM turnos_caixa
        WHERE DATE(data_abertura) = DATE(?) AND estado = 'ABERTO'
    """, (data,))
    turnos_abertos = cur.fetchone()[0] or 0

    # Clientes atendidos
    cur.execute("""
        SELECT COUNT(*) FROM vendas WHERE DATE(data) = DATE(?)
    """, (data,))
    total_clientes = cur.fetchone()[0] or 0

    conn.close()

    ticket_medio = (total_vendas / total_clientes) if total_clientes > 0 else 0

    return {
        "num_turnos": num_turnos,
        "turnos_abertos": turnos_abertos,
        "total_vendas": total_vendas,
        "total_dinheiro": total_dinheiro,
        "total_tpa": total_tpa,
        "total_clientes": total_clientes,
        "ticket_medio": ticket_medio,
        "diferenca": total_diferenca,
    }


def executar_fecho_dia_completo(dia_id, data, utilizador_logado, parent, callback=None):
    """
    Fecho completo de um dia (actual ou antigo) com o mesmo padrão:
    1. Verifica turnos abertos
    2. Mostra resumo
    3. Pede senha
    4. Fecha
    """
    from datetime import datetime as _dt
    hoje = _dt.now().strftime("%Y-%m-%d")
    eh_dia_antigo = (dia_id is not None) or (data != hoje)

    # 1. Verificar turnos abertos
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, utilizador_nome, data_abertura
        FROM turnos_caixa
        WHERE DATE(data_abertura) = DATE(?) AND estado = 'ABERTO'
        ORDER BY data_abertura ASC
    """, (data,))
    turnos_abertos = cur.fetchall()
    conn.close()

    if turnos_abertos:
        nomes = "\n".join([f"  - {t[1]} (aberto às {t[2][11:16]})"
                            for t in turnos_abertos])
        messagebox.showerror("Não Pode Fechar",
            f"NÃO É POSSÍVEL FECHAR O DIA {data}\n\n"
            f"Existem {len(turnos_abertos)} turno(s) AINDA ABERTO(S):\n\n"
            f"{nomes}\n\n"
            f"Feche primeiro estes turnos (contagem de notas +\n"
            f"autorização do gerente), e só depois poderá fechar o dia.")
        return

    # 2. Calcular resumo
    if eh_dia_antigo:
        resumo_dados = obter_resumo_dia_antigo(data)
    else:
        resumo_dados = consolidar_dia(data)
        resumo_dados["turnos_abertos"] = 0

    # 3. Mostrar resumo + confirmar
    resumo = (
        f"RESUMO DO DIA\n"
        f"{'='*40}\n\n"
        f"Data: {data}\n"
        f"Turnos fechados: {resumo_dados['num_turnos']}\n"
        f"Clientes atendidos: {resumo_dados['total_clientes']}\n"
        f"Ticket médio: {formatar_kz(resumo_dados['ticket_medio'])}\n\n"
        f"Total vendido: {formatar_kz(resumo_dados['total_vendas'])}\n"
        f"  Dinheiro: {formatar_kz(resumo_dados['total_dinheiro'])}\n"
        f"  TPA:      {formatar_kz(resumo_dados['total_tpa'])}\n\n"
    )

    if eh_dia_antigo:
        resumo += "⚠️  Este é um DIA ANTIGO que ficou aberto.\n\n"

    resumo += "Deseja fechar o dia?"

    if not messagebox.askyesno("Confirmar Fecho", resumo):
        return

    # 4. Pedir senha
    ok, nome_gerente = pedir_senha_gerente(
        parent,
        f"Fechar o dia {data}.\n\n"
        f"Digite a senha do gerente ou administrador para autorizar."
    )

    if not ok:
        messagebox.showwarning("Cancelado", "Fecho não autorizado.")
        return

    # 5. Executar fecho
    try:
        if eh_dia_antigo and dia_id:
            # Fecho manual de dia antigo
            conn = conectar()
            cur = conn.cursor()
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cur.execute("""
                UPDATE dias_operacao
                SET estado = 'FECHADO',
                    hora_fecho = ?,
                    gerente_fecho_nome = ?,
                    observacoes = COALESCE(observacoes, '') || ?
                WHERE id = ?
            """, (agora, nome_gerente,
                  f" | Fechado por {nome_gerente}", dia_id))

            conn.commit()
            conn.close()

            registar_auditoria(
                utilizador_logado["id"],
                utilizador_logado["nome"],
                "FECHO DIA ANTIGO",
                (f"Dia {data} fechado | "
                 f"Vendas: {formatar_kz(resumo_dados['total_vendas'])} | "
                 f"Clientes: {resumo_dados['total_clientes']} | "
                 f"Autorizado por: {nome_gerente}")
            )

            messagebox.showinfo("Dia Fechado",
                f"DIA {data} FECHADO COM SUCESSO\n\n"
                f"Total vendido: {formatar_kz(resumo_dados['total_vendas'])}\n"
                f"Clientes: {resumo_dados['total_clientes']}\n\n"
                f"Autorizado por: {nome_gerente}")

        else:
            # Fecho normal do dia de hoje
            sucesso, mensagem, dados_finais = fechar_dia(
                utilizador_logado["id"],
                utilizador_logado["nome"],
                f"Autorizado por: {nome_gerente}"
            )

            if sucesso:
                registar_auditoria(
                    utilizador_logado["id"],
                    utilizador_logado["nome"],
                    "FECHO DIA",
                    (f"Dia {data} fechado | "
                     f"Vendas: {formatar_kz(dados_finais['total_vendas'])} | "
                     f"Autorizado por: {nome_gerente}")
                )

                messagebox.showinfo("Dia Fechado",
                    f"DIA FECHADO COM SUCESSO\n\n"
                    f"Total vendido: {formatar_kz(dados_finais['total_vendas'])}\n"
                    f"Clientes: {dados_finais['total_clientes']}\n\n"
                    f"Autorizado por: {nome_gerente}")

                # ─── PERGUNTAR SOBRE DEPOSITO ───
                try:
                    dinheiro_caixa = dados_finais.get("total_dinheiro", 0) or 0
                    if dinheiro_caixa > 0:
                        resposta = messagebox.askyesno(
                            "Fazer Deposito?",
                            f"DINHEIRO EM CAIXA\n"
                            f"{'='*40}\n\n"
                            f"Total vendido: {formatar_kz(dados_finais['total_vendas'])}\n"
                            f"Dinheiro fisico: {formatar_kz(dinheiro_caixa)}\n\n"
                            f"Queres registar o deposito agora?\n\n"
                            f"Sim  ->  Abre o formulario de deposito\n"
                            f"Nao  ->  Podes faze-lo mais tarde\n"
                            f"          (menu: DEPOSITOS BANCARIOS)"
                        )
                        if resposta:
                            from depositos import dialogo_novo_deposito
                            dialogo_novo_deposito(
                                utilizador_logado, parent,
                                callback=callback
                            )
                except Exception as e_dep:
                    print(f"[FechoDia] Aviso ao abrir deposito: {e_dep}")

                # Gerar Relatório Z
                try:
                    from relatorio_z import abrir_escolha_impressao
                    abrir_escolha_impressao(data, utilizador_logado, parent)
                except Exception as e_rel:
                    print(f"[FechoDia] Aviso Relatório Z: {e_rel}")
            else:
                messagebox.showerror("Erro", mensagem)
                return

        if callback:
            callback()

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao fechar o dia: {e}")


def executar_abertura_dia(utilizador_logado, parent, callback_sucesso=None):
    """Executa a abertura do dia."""

    if not messagebox.askyesno("Abrir o Dia",
        f"Confirmar a abertura do dia?\n\n"
        f"Data: {datetime.now().strftime('%d/%m/%Y')}\n"
        f"Hora: {datetime.now().strftime('%H:%M')}\n\n"
        f"A partir deste momento, sera possivel efetuar vendas."):
        return

    try:
        sucesso, mensagem = abrir_dia(
            utilizador_logado["id"],
            utilizador_logado["nome"],
            ""
        )

        if sucesso:
            registar_auditoria(
                utilizador_logado["id"],
                utilizador_logado["nome"],
                "ABERTURA DIA",
                f"Dia {datetime.now().strftime('%Y-%m-%d')} aberto"
            )
            messagebox.showinfo("Dia Aberto", mensagem)
            if callback_sucesso:
                callback_sucesso()
        else:
            messagebox.showwarning("Aviso", mensagem)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir o dia: {e}")


# ============================================================
# TESTE DIRETO
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  TESTE - Modulo fecho_dia.py")
    print("="*60)

    from database import dia_aberto, consolidar_dia, verificar_turnos_abertos

    print("\n[1] Estado atual do dia:")
    d = dia_aberto()
    if d:
        print(f"    DIA ABERTO: {d[1]} (desde {d[2]} por {d[3]})")
    else:
        print("    Nenhum dia aberto")

    print("\n[2] Consolidacao do dia:")
    c = consolidar_dia()
    print(f"    Turnos fechados: {c['num_turnos']}")
    print(f"    Total vendido:   {c['total_vendas']}")

    print("\n[3] Turnos abertos:")
    t = verificar_turnos_abertos()
    if t:
        for turno in t:
            print(f"    - {turno[1]} (aberto as {turno[2]})")
    else:
        print("    Nenhum turno aberto")

    print("\n" + "="*60 + "\n")