from tkinter import *
from tkinter import messagebox, ttk
from database import (criar_tabelas, listar_produtos, produtos_validade_proxima,
                       produtos_estoque_baixo, listar_vendas, total_vendas_dia,
                       listar_auditoria, listar_utilizadores, lotes_para_relatorio_fefo,
                       caixa_aberto)
from cadastro import abrir_cadastro
from pdv import abrir_pdv
from moeda import formatar_kz
from login import abrir_login, obter_utilizador, terminar_sessao
from utilizadores import abrir_utilizadores
from fornecedores import abrir_fornecedores
from clientes import abrir_clientes
from categorias import abrir_categorias
from compras import abrir_compras
from inventario import abrir_inventario
from fiscal import abrir_fiscal
from relatorios import abrir_relatorios
from backup import abrir_backup, backup_automatico
from impressao import abrir_impressao
from devolucoes import abrir_devolucoes
from produtos import abrir_produtos
from dashboard import abrir_dashboard
from perdas import abrir_perdas
from auditoria_painel import abrir_painel_auditoria
from config_farmacia import abrir_config_farmacia
from ia_assistente import abrir_assistente_ia
from sincronizacao import (sincronizar_tudo, tem_internet, contar_pendentes,
                             obter_ultima_sincronizacao, ha_quanto_tempo,
                             registar_sincronizacao)
from auto_sync import iniciar_auto_sync, parar_auto_sync
from turno_caixa import (abrir_gestao_turnos, abrir_turno_janela,
                          fechar_turno_janela, turno_aberto)
from caixa import abrir_caixa_menu, abrir_historico_caixas
from fecho_dia import abrir_fecho_dia
from metas import abrir_metas
from relatorios_guardados import abrir_relatorios_guardados
from relatorios_avancados import abrir_relatorios_avancados
from ia_orcamento import abrir_ia_orcamento
from painel_metas import criar_painel_metas
from relatorio_z import abrir_escolha_impressao
from database import dia_aberto
from database import migrar_tabela_facturas
import fila_sync
from permissoes import tem_permissao, NOMES_PERFIS
from transferencias import abrir_transferencias
from datetime import datetime

criar_tabelas()

try:
    migrar_tabela_facturas()
except Exception as e:
    print(f"[Migracao] Aviso: {e}")
if not abrir_login():
    print("Login cancelado. A sair...")
    exit()

utilizador = obter_utilizador()
PERFIL = utilizador["perfil"]
print(f"Bem-vindo(a), {utilizador['nome']} ({NOMES_PERFIS.get(PERFIL, PERFIL)})")

# ─── LOGIN SUPABASE (automático com refresh token) ──────────
try:
    from sincronizacao import (login_supabase, renovar_sessao,
                                guardar_sessao, carregar_sessao)
    from tkinter import simpledialog

    # 1. Tentar carregar sessão guardada
    sessao = carregar_sessao()
    logado = False

    if sessao:
        ok_renova, msg = renovar_sessao(sessao)
        if ok_renova:
            print("[Sync] Sessão restaurada automaticamente")
            logado = True
                # Baixar orçamentos do Supabase (web → PC)
    if logado:
        try:
            from sincronizacao import baixar_orcamentos_do_supabase
            n = baixar_orcamentos_do_supabase()
            if n > 0:
                print(f"[Sync] {n} orçamentos sincronizados para o PC")
        except Exception as e_bx:
            print(f"[Sync] Aviso ao baixar orcamentos: {e_bx}")
        else:
            print(f"[Sync] Sessão expirada: {msg}")

    # 2. Se não há sessão, pedir credenciais (só a primeira vez)
    if not logado:
        resposta = messagebox.askyesno(
            "Ativar Sincronização",
            "Queres ligar a sincronização com a nuvem?\n\n"
            "Isto permite que as vendas apareçam na plataforma web.\n\n"
            "Só precisas de fazer isto UMA VEZ."
        )

        if resposta:
            email_sb = simpledialog.askstring("Email Supabase", "Email:")
            if email_sb:
                senha_sb = simpledialog.askstring("Senha Supabase", "Senha:", show="*")
                if senha_sb:
                    ok_sb, dados_sb = login_supabase(email_sb.strip().lower(), senha_sb)
                    if ok_sb:
                        guardar_sessao(dados_sb)
                        messagebox.showinfo("Sincronização", "Ligado à nuvem com sucesso!")
                        logado = True
                    else:
                        messagebox.showwarning("Sincronização", f"Não foi possível ligar:\n{dados_sb}")

except Exception as e_sync:
    print(f"[Sync] Aviso: {e_sync}")

# ────────────────────────────────────────────────────────────
backup_automatico(utilizador)

COR_FUNDO = "#0f172a"
COR_CARD = "#1e293b"
COR_CARD_HOVER = "#334155"
COR_PRIMARIA = "#7c3aed"
COR_PRIMARIA_HOVER = "#6d28d9"
COR_DOURADO = "#fbbf24"
COR_VERDE = "#10b981"
COR_VERDE_HOVER = "#059669"
COR_VERMELHO = "#ef4444"
COR_VERMELHO_HOVER = "#dc2626"
COR_ALERTA = "#f97316"
COR_AZUL = "#0ea5e9"
COR_ROXO_CLARO = "#a78bfa"
COR_TEXTO = "#f8fafc"
COR_TEXTO_SEC = "#94a3b8"
COR_BORDA = "#334155"

CAT_VENDAS = "#7c3aed"
CAT_CADASTROS = "#0ea5e9"
CAT_ESTOQUE = "#f59e0b"
CAT_ANALISE = "#10b981"
CAT_NUVEM = "#06b6d4"
CAT_ADMIN = "#64748b"
CAT_AUDITORIA = "#a78bfa"
CAT_CAIXA = "#10b981"

root = Tk()
root.title("JAM Soft Premium")
root.geometry("1280x800")
root.configure(bg=COR_FUNDO)
root.state("zoomed")

# ─── Ícone da janela (.ico com múltiplos tamanhos) ───
try:
    from pathlib import Path

    caminho_ico = Path(__file__).parent / "logos" / "jamsoft.ico"
    if caminho_ico.exists():
        root.iconbitmap(default=str(caminho_ico))
        print("[Icon] Icone .ico aplicado")
    else:
        # Fallback: PNG
        from PIL import Image, ImageTk
        caminho_png = Path(__file__).parent / "logos" / "icon_192.png"
        if caminho_png.exists():
            _img_icon = Image.open(caminho_png).convert("RGBA")
            _icon_tk = ImageTk.PhotoImage(_img_icon)
            root.iconphoto(True, _icon_tk)
            root._icon_ref = _icon_tk
            print("[Icon] Icone PNG aplicado (fallback)")
        else:
            print("[Icon] Nenhum icone encontrado")
except Exception as e:
    print(f"[Icon] Aviso: {e}")

def com_permissao(acao, func, *args):
    def wrapper():
        if not tem_permissao(PERFIL, acao):
            try:
                from database import registar_auditoria
                registar_auditoria(utilizador["id"], utilizador["nome"],
                                    "TENTATIVA BLOQUEADA",
                                    f"Perfil '{PERFIL}' tentou '{acao}'")
            except Exception:
                pass
            messagebox.showerror("Acesso Negado",
                f"Acesso negado.\n\nO seu perfil ({NOMES_PERFIS.get(PERFIL, PERFIL)}) "
                f"nao tem permissao para esta operacao.\n\n"
                f"Esta tentativa foi registada em auditoria.")
            return
        if args:
            func(*args)
        else:
            func()
    return wrapper


class CardBotao:
    def __init__(self, parent, texto, subtitulo, atalho, cor, comando,
                 largura=230, altura=85):
        self.cor_normal = cor
        self.cor_hover = self._escurecer(cor)
        self.comando = comando
        
        self.outer = Frame(parent, bg=cor, bd=0, width=largura, height=altura)
        self.outer.pack_propagate(False)
        
        self.inner = Frame(self.outer, bg=cor, cursor="hand2")
        self.inner.pack(fill=BOTH, expand=True, padx=2, pady=2)
        
        self.lbl_principal = Label(
            self.inner,
            text=texto,
            font=("Segoe UI", 10, "bold"),
            bg=cor, fg="white", cursor="hand2",
            wraplength=largura - 20,
            justify=CENTER
        )
        self.lbl_principal.pack(pady=(8, 2), padx=5)
        
        self.lbl_atalho = None
        if atalho:
            self.lbl_atalho = Label(
                self.inner, text=f"{atalho}",
                font=("Segoe UI", 8),
                bg=cor, fg="#e0e7ff", cursor="hand2"
            )
            self.lbl_atalho.pack()
        
        self.lbl_sub = None
        if subtitulo:
            self.lbl_sub = Label(
                self.inner, text=subtitulo,
                font=("Segoe UI", 8, "italic"),
                bg=cor, fg="#cbd5e1", cursor="hand2",
                wraplength=largura - 20,
                justify=CENTER
            )
            self.lbl_sub.pack(pady=(2, 6), padx=5)
        
        self.widgets_hover = [self.outer, self.inner, self.lbl_principal]
        if self.lbl_atalho:
            self.widgets_hover.append(self.lbl_atalho)
        if self.lbl_sub:
            self.widgets_hover.append(self.lbl_sub)
        
        for widget in self.widgets_hover:
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<Button-1>", self._on_click)
    
    def _escurecer(self, hex_cor, fator=0.85):
        try:
            hex_cor = hex_cor.lstrip("#")
            r, g, b = (int(hex_cor[i:i+2], 16) for i in (0, 2, 4))
            r, g, b = int(r*fator), int(g*fator), int(b*fator)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_cor
    
    def _on_enter(self, event):
        for w in self.widgets_hover:
            try:
                w.configure(bg=self.cor_hover)
            except Exception:
                pass
    
    def _on_leave(self, event):
        for w in self.widgets_hover:
            try:
                w.configure(bg=self.cor_normal)
            except Exception:
                pass
    
    def _on_click(self, event):
        if self.comando:
            self.comando()
    
    def grid(self, **kwargs):
        self.outer.grid(**kwargs)
        return self


def verificar_dia_aberto_para_pdv():
    try:
        dia = dia_aberto()
        if not dia:
            messagebox.showerror("Dia Nao Aberto",
                "NAO E POSSIVEL VENDER\n\n"
                "O dia de operacao ainda nao foi aberto.\n\n"
                "Peca ao gerente para abrir o dia primeiro "
                "(menu: DIA DE OPERACAO -> Abrir Dia).")
            return False
        return True
    except Exception as e:
        print(f"[Verificar Dia] Erro: {e}")
        return True


def executar_sincronizacao(utilizador_logado, parent_window):
    prog = Toplevel(parent_window)
    prog.title("Sincronizando...")
    prog.geometry("450x220")
    prog.configure(bg=COR_CARD)
    prog.transient(parent_window)
    prog.grab_set()
    
    prog.update_idletasks()
    x = (prog.winfo_screenwidth() - 450) // 2
    y = (prog.winfo_screenheight() - 220) // 2
    prog.geometry(f"450x220+{x}+{y}")
    
    Label(prog, text="A sincronizar com a nuvem...",
          font=("Segoe UI", 14, "bold"), bg=COR_CARD, fg=COR_TEXTO).pack(pady=(40, 10))
    Label(prog, text="Aguarde um momento...",
          font=("Segoe UI", 10, "italic"), bg=COR_CARD, fg=COR_TEXTO_SEC).pack()
    prog.update()
    
    try:
        resultado = sincronizar_tudo()
    except Exception as e:
        prog.destroy()
        messagebox.showerror("Erro", f"Erro na sincronizacao: {e}")
        return
    
    prog.destroy()
    
    if resultado["sucesso"]:
        registar_sincronizacao(True, resultado["total"])
        
        if resultado["total"] > 0:
            messagebox.showinfo("Sincronizacao Concluida",
                f"Sincronizacao concluida com sucesso!\n\n"
                f"Vendas:     {resultado['vendas']}\n"
                f"Compras:    {resultado['compras']}\n"
                f"Perdas:     {resultado['perdas']}\n"
                f"Movimentos: {resultado['movimentos']}\n"
                f"Erros:      {resultado.get('erros', 0)}\n"
                f"Duracao:    {resultado.get('duracao', 0)}s")
        else:
            messagebox.showinfo("Sincronizacao",
                "Tudo ja esta sincronizado.\n\n"
                "Nao ha nada pendente para enviar.")
    else:
        registar_sincronizacao(False, 0)
        messagebox.showwarning("Sem Ligacao",
            f"Nao foi possivel sincronizar.\n\n"
            f"Motivo: {resultado['motivo']}")


def abrir_diagnostico_fila(utilizador_logado, parent_window):
    pode_limpar = tem_permissao(PERFIL, "nuvem.limpar_fila")
    
    janela = Toplevel(parent_window)
    janela.title("Estado da Fila de Sincronizacao")
    janela.geometry("1000x650")
    janela.configure(bg=COR_FUNDO)
    janela.transient(parent_window)
    
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 1000) // 2
    y = (janela.winfo_screenheight() - 650) // 2
    janela.geometry(f"1000x650+{x}+{y}")
    
    header = Frame(janela, bg=CAT_NUVEM, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Estado da Fila de Sincronizacao",
          font=("Segoe UI", 18, "bold"), bg=CAT_NUVEM, fg="white").pack(pady=20)
    
    e = fila_sync.estatisticas()
    
    frame_cards = Frame(janela, bg=COR_FUNDO)
    frame_cards.pack(fill=X, padx=20, pady=20)
    
    def criar_card_stat(parent, titulo, valor, cor, coluna):
        card = Frame(parent, bg=COR_CARD, highlightthickness=2, highlightbackground=cor)
        card.grid(row=0, column=coluna, padx=8, pady=5, sticky="nsew")
        parent.columnconfigure(coluna, weight=1)
        
        Label(card, text=titulo, font=("Segoe UI", 10, "bold"),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(15, 3))
        Label(card, text=str(valor), font=("Segoe UI", 24, "bold"),
              bg=COR_CARD, fg=cor).pack(pady=(0, 15))
    
    criar_card_stat(frame_cards, "Total", e["total"], COR_TEXTO, 0)
    criar_card_stat(frame_cards, "Pendentes", e["pendentes"], COR_ALERTA, 1)
    criar_card_stat(frame_cards, "Enviados", e["enviados"], COR_VERDE, 2)
    criar_card_stat(frame_cards, "Conflitos", e["conflitos"], COR_VERMELHO, 3)
    criar_card_stat(frame_cards, "Abandonados", e["abandonados"], "#7f1d1d", 4)
    
    Label(janela, text="Operacoes com problema:",
          font=("Segoe UI", 12, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, padx=25, pady=(10, 5))
    
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=20, pady=5)
    
    colunas = ("UUID", "Tipo", "Estado", "Tent.", "Ultima Tent.", "Erro")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=12)
    tree.heading("UUID", text="UUID")
    tree.heading("Tipo", text="Tipo")
    tree.heading("Estado", text="Estado")
    tree.heading("Tent.", text="Tent.")
    tree.heading("Ultima Tent.", text="Ultima Tentativa")
    tree.heading("Erro", text="Erro")
    tree.column("UUID", width=150)
    tree.column("Tipo", width=100)
    tree.column("Estado", width=100)
    tree.column("Tent.", width=60)
    tree.column("Ultima Tent.", width=140)
    tree.column("Erro", width=350)
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    for err in fila_sync.detalhes_erros(20):
        uuid_op, tipo, estado, tent, ultima, erro = err
        tag = "conflito" if estado == "CONFLITO" else ("abandonado" if estado == "ABANDONADO" else "erro")
        tree.insert("", END, values=(
            (uuid_op or "")[:20] + "...",
            tipo or "-", estado, tent, ultima or "-",
            (erro or "-")[:60]
        ), tags=(tag,))
    
    tree.tag_configure("erro", background="#3f2a13", foreground=COR_ALERTA)
    tree.tag_configure("conflito", background="#3f1a1a", foreground=COR_VERMELHO)
    tree.tag_configure("abandonado", background="#2a1a1a", foreground="#fca5a5")
    
    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(fill=X, pady=15)
    
    def actualizar():
        janela.destroy()
        abrir_diagnostico_fila(utilizador_logado, parent_window)
    
    def limpar():
        try:
            n = fila_sync.limpar_enviados(30)
            messagebox.showinfo("Limpeza",
                f"{n} registos enviados foram removidos.\n\n"
                f"(Apenas entradas com mais de 30 dias)")
            actualizar()
        except Exception as ex:
            messagebox.showerror("Erro", str(ex))
    
    estilo_btn = {"font": ("Segoe UI", 11, "bold"), "bd": 0, "cursor": "hand2",
                  "fg": "white", "width": 22, "height": 2}
    
    Button(frame_btn, text="Actualizar", bg=CAT_NUVEM,
           command=actualizar, **estilo_btn).pack(side=LEFT, padx=10)
    
    if pode_limpar:
        Button(frame_btn, text="Limpar Enviados (+30d)", bg="#64748b",
               command=limpar, **estilo_btn).pack(side=LEFT, padx=10)
    else:
        Label(frame_btn, text="Somente leitura (Auditor)",
              font=("Segoe UI", 9, "italic"), bg=COR_FUNDO,
              fg=COR_TEXTO_SEC).pack(side=LEFT, padx=10)
    
    Button(frame_btn, text="Fechar", bg=COR_VERMELHO,
           command=janela.destroy, **estilo_btn).pack(side=RIGHT, padx=10)


def abrir_lista_produtos():
    janela = Toplevel(root)
    janela.title("Produtos Cadastrados")
    janela.geometry("1000x500")
    janela.configure(bg=COR_FUNDO)
    Label(janela, text="Produtos Cadastrados", font=("Segoe UI", 16, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=10)
    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    colunas = ("ID", "Nome", "Codigo", "Preco", "Estoque", "Minimo", "IVA", "Status")
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=110)
    tree.pack(fill=BOTH, expand=True)
    for p in listar_produtos():
        status = "Baixo" if p[4] <= p[5] else "OK"
        iva_txt = "Isento" if p[6] else "14%"
        tree.insert("", END, values=(p[0], p[1], p[2], formatar_kz(p[3]), p[4], p[5], iva_txt, status))


def abrir_relatorio_validade():
    janela = Toplevel(root)
    janela.title("Relatorio de Validade")
    janela.geometry("800x500")
    janela.configure(bg=COR_FUNDO)
    Label(janela, text="Produtos com Validade Proxima (90 dias)", font=("Segoe UI", 16, "bold"),
          bg=COR_FUNDO, fg=COR_ALERTA).pack(pady=10)
    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    colunas = ("Produto", "Lote", "Validade", "Quantidade")
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=180)
    tree.pack(fill=BOTH, expand=True)
    for l in produtos_validade_proxima(90):
        tree.insert("", END, values=l)


def abrir_estoque_baixo():
    janela = Toplevel(root)
    janela.title("Estoque Baixo")
    janela.geometry("800x500")
    janela.configure(bg=COR_FUNDO)
    Label(janela, text="Produtos com Estoque Baixo", font=("Segoe UI", 16, "bold"),
          bg=COR_FUNDO, fg=COR_VERMELHO).pack(pady=10)
    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    colunas = ("Produto", "Codigo", "Estoque Atual", "Estoque Minimo")
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=180)
    tree.pack(fill=BOTH, expand=True)
    for p in produtos_estoque_baixo():
        tree.insert("", END, values=p)


def abrir_historico_vendas():
    janela = Toplevel(root)
    janela.title("Historico de Vendas")
    janela.geometry("800x500")
    janela.configure(bg=COR_FUNDO)
    Label(janela, text="Ultimas 100 Vendas", font=("Segoe UI", 16, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=10)
    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    colunas = ("ID", "Data", "Total", "Forma de Pagamento")
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=180)
    tree.pack(fill=BOTH, expand=True)
    for v in listar_vendas():
        tree.insert("", END, values=(v[0], v[1], formatar_kz(v[2]), v[3]))


def abrir_relatorio_fefo():
    janela = Toplevel(root)
    janela.title("Relatorio FEFO")
    janela.geometry("1000x600")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg="#be185d", height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Relatorio FEFO - Primeiro a Vencer",
          font=("Segoe UI", 16, "bold"), bg="#be185d", fg="white").pack(pady=20)
    
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=15, pady=15)
    
    colunas = ("Produto", "Codigo", "Lote", "Validade", "Qtd", "Prioridade")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=18)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(fill=BOTH, expand=True)
    
    from datetime import datetime as dt
    hoje = dt.now().date()
    
    for lote in lotes_para_relatorio_fefo():
        nome, codigo, num_lote, validade, qtd = lote
        try:
            data_v = dt.strptime(validade, "%Y-%m-%d").date()
            dias = (data_v - hoje).days
            
            if dias < 0:
                prio = f"VENCIDO ({abs(dias)}d)"
                tag = "vencido"
            elif dias <= 30:
                prio = f"URGENTE ({dias}d)"
                tag = "urgente"
            elif dias <= 90:
                prio = f"ATENCAO ({dias}d)"
                tag = "atencao"
            else:
                prio = f"OK ({dias}d)"
                tag = "ok"
            
            tree.insert("", END, values=(nome, codigo or "-", num_lote or "-",
                                          validade, qtd, prio), tags=(tag,))
        except Exception:
            tree.insert("", END, values=(nome, codigo or "-", num_lote or "-",
                                          validade or "-", qtd, "?"))
    
    tree.tag_configure("vencido", background="#3f1a1a", foreground="#fca5a5")
    tree.tag_configure("urgente", background="#3f2a13", foreground="#fdba74")
    tree.tag_configure("atencao", background="#3f3a13", foreground="#fde68a")
    tree.tag_configure("ok", background="#132a1a", foreground="#86efac")


def abrir_auditoria():
    janela = Toplevel(root)
    janela.title("Log de Auditoria")
    janela.geometry("900x500")
    janela.configure(bg=COR_FUNDO)
    Label(janela, text="Log de Auditoria - Ultimas 100 acoes", font=("Segoe UI", 16, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=10)
    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    colunas = ("Data", "Utilizador", "Acao", "Detalhes")
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=200)
    tree.pack(fill=BOTH, expand=True)
    for a in listar_auditoria(100):
        tree.insert("", END, values=(a[0], a[1], a[2], a[3]))


def sair_sistema():
    """Termina a sessao e volta ao formulario de login."""

    # Verificar se ha dia aberto (informativo apenas)
    avisos = []
    try:
        dia = dia_aberto()
        if dia:
            avisos.append(
                f"DIA DE OPERACAO ABERTO\n"
                f"Aberto as: {dia[2]}\n"
                f"Por: {dia[3]}"
            )
    except Exception:
        pass

    if avisos:
        corpo = "\n\n".join(avisos)
        msg = (
            f"{corpo}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"O dia continua aberto quando sair.\n"
            f"Pode voltar a entrar a qualquer momento.\n\n"
            f"Deseja terminar a sessao?"
        )
        if not messagebox.askyesno("Terminar Sessao", msg, icon="warning"):
            return
    else:
        if not messagebox.askyesno("Sair", "Deseja terminar a sessao?"):
            return

    # Parar auto-sync
    try:
        parar_auto_sync()
    except Exception:
        pass

    # Parar monitor de inactividade
    try:
        mon = globals().get("monitor_inatividade")
        if mon:
            mon.parar()
    except Exception:
        pass

    # Marcar como nao logado
    terminar_sessao()

    # Fechar TODAS as janelas Toplevel
    try:
        for w in root.winfo_children():
            if isinstance(w, Toplevel):
                w.destroy()
    except Exception:
        pass

    # Limpar conteudo da root
    for w in root.winfo_children():
        w.destroy()

    # Reduzir root
    root.withdraw()

    # Abrir login novamente
    root.after(100, _reiniciar_app)


def _reiniciar_app():
    """Recarrega a app apos logout."""
    import subprocess
    import sys

    try:
        root.destroy()
    except Exception:
        pass

    # Reiniciar o processo Python
    subprocess.Popen([sys.executable] + sys.argv)
    sys.exit(0)

        # ============================================================
# ============ HEADER PREMIUM ================================
# ============================================================

header = Frame(root, bg=COR_CARD, height=90)
header.pack(fill=X)
header.pack_propagate(False)

linha_dourada = Frame(header, bg=COR_DOURADO, height=3)
linha_dourada.pack(fill=X)

header_inner = Frame(header, bg=COR_CARD)
header_inner.pack(fill=BOTH, expand=True)

Label(header_inner, text="JAM Soft",
      font=("Segoe UI", 24, "bold"),
      bg=COR_CARD, fg=COR_DOURADO).pack(side=LEFT, padx=30, pady=15)

Label(header_inner, text="Premium Edition",
      font=("Segoe UI", 10, "italic"),
      bg=COR_CARD, fg=COR_TEXTO_SEC).pack(side=LEFT, pady=(25, 15))

info_frame = Frame(header_inner, bg=COR_CARD)
info_frame.pack(side=RIGHT, padx=30, pady=15)

Label(info_frame, text=f"{utilizador['nome']}",
      font=("Segoe UI", 11, "bold"),
      bg=COR_CARD, fg=COR_TEXTO).pack(anchor=E)
Label(info_frame, text=f"{NOMES_PERFIS.get(PERFIL, PERFIL).upper()}",
      font=("Segoe UI", 9),
      bg=COR_CARD, fg=COR_ROXO_CLARO).pack(anchor=E)


# ============================================================
# ============ PAINEL DE METAS ===============================
# ============================================================

painel_metas_frame = Frame(root, bg=COR_CARD, highlightthickness=1,
                             highlightbackground=COR_DOURADO)
painel_metas_frame.pack(fill=X, padx=20, pady=(5, 3))

criar_painel_metas(painel_metas_frame, utilizador)


# ============================================================
# ============ PAINEL DE KPIs ================================
# ============================================================

kpis_frame = Frame(root, bg=COR_FUNDO)
kpis_frame.pack(fill=X, padx=20, pady=(5, 5))

kpi1 = Frame(kpis_frame, bg=COR_CARD, highlightthickness=2, highlightbackground=CAT_VENDAS)
kpi1.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
kpis_frame.columnconfigure(0, weight=1)

Label(kpi1, text="VENDAS HOJE", font=("Segoe UI", 9, "bold"),
      bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(10, 2))
vendas_hoje = total_vendas_dia()
Label(kpi1, text=formatar_kz(vendas_hoje), font=("Segoe UI", 18, "bold"),
      bg=COR_CARD, fg=COR_VERDE).pack(pady=(0, 10))

kpi2 = Frame(kpis_frame, bg=COR_CARD, highlightthickness=2,
                highlightbackground=COR_VERDE if caixa_aberto() else COR_VERMELHO)
kpi2.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
kpis_frame.columnconfigure(1, weight=1)

Label(kpi2, text="CAIXA", font=("Segoe UI", 9, "bold"),
      bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(10, 2))
cx_info = caixa_aberto()
if cx_info:
    Label(kpi2, text=f"ABERTO #{cx_info[0]}",
          font=("Segoe UI", 14, "bold"),
          bg=COR_CARD, fg=COR_VERDE).pack(pady=(0, 10))
else:
    Label(kpi2, text="FECHADO",
          font=("Segoe UI", 14, "bold"),
          bg=COR_CARD, fg=COR_VERMELHO).pack(pady=(0, 10))

kpi3 = Frame(kpis_frame, bg=COR_CARD, highlightthickness=2, highlightbackground=CAT_CAIXA)
kpi3.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
kpis_frame.columnconfigure(2, weight=1)

Label(kpi3, text="TURNO", font=("Segoe UI", 9, "bold"),
      bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(10, 2))
t_atual_kpi = turno_aberto()
if t_atual_kpi:
    Label(kpi3, text="ABERTO por",
          font=("Segoe UI", 11, "bold"),
          bg=COR_CARD, fg=COR_VERDE).pack()
    Label(kpi3, text=t_atual_kpi[3][:15],
          font=("Segoe UI", 10, "italic"),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(0, 10))
else:
    Label(kpi3, text="SEM TURNO",
          font=("Segoe UI", 12, "bold"),
          bg=COR_CARD, fg=COR_ALERTA).pack(pady=(0, 10))

kpi4 = Frame(kpis_frame, bg=COR_CARD, highlightthickness=2, highlightbackground=CAT_NUVEM)
kpi4.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
kpis_frame.columnconfigure(3, weight=1)

Label(kpi4, text="NUVEM", font=("Segoe UI", 9, "bold"),
      bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(10, 2))

try:
    pendencias_kpi = contar_pendentes()
    if pendencias_kpi["pendentes"] == 0:
        Label(kpi4, text="Sincronizado",
              font=("Segoe UI", 13, "bold"),
              bg=COR_CARD, fg=COR_VERDE).pack(pady=(0, 10))
    else:
        Label(kpi4, text=f"{pendencias_kpi['pendentes']} pend.",
              font=("Segoe UI", 13, "bold"),
              bg=COR_CARD, fg=COR_ALERTA).pack(pady=(0, 10))
except Exception:
    Label(kpi4, text="-", font=("Segoe UI", 13, "bold"),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(0, 10))


# ============================================================
# ============ PERMISSOES ====================================
# ============================================================

pode_dashboard = tem_permissao(PERFIL, "dashboard.ver")
pode_pdv = tem_permissao(PERFIL, "pdv.abrir")
pode_caixa = tem_permissao(PERFIL, "caixa.abrir") or tem_permissao(PERFIL, "caixa.ver_movimentos")
pode_turnos = tem_permissao(PERFIL, "caixa.ver_movimentos")
pode_fiscal = tem_permissao(PERFIL, "fiscal.ver_facturas") or tem_permissao(PERFIL, "fiscal.emitir_factura")
pode_relatorios = tem_permissao(PERFIL, "relatorios.ver")
pode_backup = tem_permissao(PERFIL, "backup.listar")
pode_produtos_gestao = tem_permissao(PERFIL, "produtos.editar")
pode_produtos_cadastrar = tem_permissao(PERFIL, "produtos.cadastrar")
pode_fornecedores = tem_permissao(PERFIL, "fornecedores.listar")
pode_clientes = tem_permissao(PERFIL, "clientes.listar")
pode_categorias = tem_permissao(PERFIL, "categorias.listar")
pode_listar_produtos = tem_permissao(PERFIL, "produtos.listar")
pode_validade = tem_permissao(PERFIL, "produtos.ver_validade")
pode_estoque_baixo = tem_permissao(PERFIL, "produtos.listar")
pode_historico_vendas = tem_permissao(PERFIL, "relatorios.vendas")
pode_compras = tem_permissao(PERFIL, "compras.listar")
pode_inventario = tem_permissao(PERFIL, "inventario.listar")
pode_fefo = tem_permissao(PERFIL, "produtos.ver_fefo")
pode_impressao = tem_permissao(PERFIL, "fiscal.gerar_pdf")
pode_perdas = tem_permissao(PERFIL, "perdas.listar")
pode_auditoria = tem_permissao(PERFIL, "auditoria.ver_log")
pode_utilizadores = tem_permissao(PERFIL, "utilizadores.listar")
pode_painel_auditoria = (PERFIL == "auditor")
pode_config_farmacia = (PERFIL == "admin")
pode_sincronizar = tem_permissao(PERFIL, "nuvem.sincronizar")
pode_ver_fila = tem_permissao(PERFIL, "nuvem.ver_fila")
pode_devolucoes = tem_permissao(PERFIL, "devolucoes.ver")

pode_operar_pdv = PERFIL in ("gerente", "farmaceutico")
pode_gerir_dia = PERFIL in ("gerente",)
pode_gerir_turno = PERFIL in ("gerente", "farmaceutico")


# ============================================================
# ============ MENU ==========================================
# ============================================================

menu_container = Frame(root, bg=COR_FUNDO)
menu_container.pack(fill=BOTH, expand=True, padx=20, pady=10)

canvas = Canvas(menu_container, bg=COR_FUNDO, highlightthickness=0)
scrollbar_menu = Scrollbar(menu_container, orient="vertical", command=canvas.yview)
scrollable = Frame(canvas, bg=COR_FUNDO)

scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable, anchor="nw")
canvas.configure(yscrollcommand=scrollbar_menu.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar_menu.pack(side="right", fill="y")

def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
canvas.bind_all("<MouseWheel>", _on_mousewheel)

def criar_separador(parent, titulo, cor, contador=None):
    sep = Frame(parent, bg=COR_FUNDO)
    sep.pack(fill=X, pady=(18, 8))
    txt = f"  {titulo}  "
    if contador is not None:
        txt = f"  {titulo}  ({contador})  "
    Label(sep, text=txt, font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=cor).pack(side=LEFT)
    linha = Frame(sep, bg=cor, height=1)
    linha.pack(side=LEFT, fill=X, expand=True, padx=(10, 0), pady=8)

def criar_linha_botoes(parent):
    f = Frame(parent, bg=COR_FUNDO)
    f.pack(fill=X, pady=4)
    return f


# ============================================================
# ============ ACAO PRINCIPAL ================================
# ============================================================

if pode_pdv and pode_operar_pdv:
    criar_separador(scrollable, "ACAO PRINCIPAL", COR_DOURADO)
    frame_destaque = Frame(scrollable, bg=COR_FUNDO)
    frame_destaque.pack(fill=X, pady=8)
    btn_grande = Frame(frame_destaque, bg=CAT_VENDAS, cursor="hand2",
                        highlightthickness=3, highlightbackground=COR_DOURADO)
    btn_grande.pack(fill=X, ipady=25)
    Label(btn_grande, text="ABRIR PDV - NOVA VENDA",
          font=("Segoe UI", 20, "bold"),
          bg=CAT_VENDAS, fg="white", cursor="hand2").pack(pady=(5, 0))
    Label(btn_grande, text="Pressione F2 ou clique aqui",
          font=("Segoe UI", 10, "italic"),
          bg=CAT_VENDAS, fg="#e0e7ff", cursor="hand2").pack(pady=(0, 5))
    
    def _click_pdv(event=None):
        if not verificar_dia_aberto_para_pdv():
            return
        com_permissao("pdv.abrir", abrir_pdv, utilizador)()
    
    def _hover_on(event):
        for w in [btn_grande] + list(btn_grande.winfo_children()):
            try: w.configure(bg=COR_PRIMARIA_HOVER)
            except: pass
    
    def _hover_off(event):
        for w in [btn_grande] + list(btn_grande.winfo_children()):
            try: w.configure(bg=CAT_VENDAS)
            except: pass
    
    for w in [btn_grande] + list(btn_grande.winfo_children()):
        w.bind("<Enter>", _hover_on)
        w.bind("<Leave>", _hover_off)
        w.bind("<Button-1>", _click_pdv)


# ============================================================
# ============ DIA DE OPERACAO ===============================
# ============================================================

pode_ver_metas = True
pode_ver_relatorios = PERFIL in ("admin", "gerente", "auditor")

if pode_gerir_dia or pode_ver_metas or pode_ver_relatorios:
    criar_separador(scrollable, "DIA DE OPERACAO", COR_DOURADO)
    linha_dia = criar_linha_botoes(scrollable)
    col_dia = 0
    
    if pode_gerir_dia:
        dia_atual = dia_aberto()
        if dia_atual:
            texto_dia = "Fechar Dia"
            sub_dia = f"Aberto as {dia_atual[2]}"
            cor_dia = COR_ALERTA
        else:
            texto_dia = "Abrir Dia"
            sub_dia = "Iniciar operacao"
            cor_dia = COR_VERDE
        
        CardBotao(linha_dia, texto_dia, sub_dia, "",
                   cor_dia,
                   lambda: abrir_fecho_dia(utilizador, root)
                   ).grid(row=0, column=col_dia, padx=5)
        col_dia += 1
    
    if pode_ver_metas:
        CardBotao(linha_dia, "Metas", "Orcamentos", "",
                   COR_DOURADO,
                   lambda: abrir_metas(utilizador, root)
                   ).grid(row=0, column=col_dia, padx=5)
        col_dia += 1
    
    if pode_gerir_dia:
        CardBotao(linha_dia, "IA Orcamento", "Sugestao inteligente", "",
                   COR_ROXO_CLARO,
                   lambda: abrir_ia_orcamento(utilizador, root)
                   ).grid(row=0, column=col_dia, padx=5)
        col_dia += 1
    
    if pode_ver_relatorios:
        CardBotao(linha_dia, "Relatorios", "Arquivados", "",
                   COR_AZUL,
                   lambda: abrir_relatorios_guardados(utilizador, root)
                   ).grid(row=0, column=col_dia, padx=5)
        col_dia += 1


# ============================================================
# ============ GESTAO DE CAIXA ===============================
# ============================================================

if pode_caixa:
    criar_separador(scrollable, "GESTAO DE CAIXA", CAT_CAIXA)
    linha_cx = criar_linha_botoes(scrollable)

    # Verificar estado do caixa
    cx_atual = caixa_aberto()
    if cx_atual:
        sub_caixa = f"Caixa #{cx_atual[0]} ABERTO"
        cor_caixa = COR_VERDE
    else:
        sub_caixa = "Nenhum caixa aberto"
        cor_caixa = COR_ALERTA

    CardBotao(linha_cx, "Menu Caixa", sub_caixa, "",
               cor_caixa,
               lambda: abrir_caixa_menu(utilizador)
               ).grid(row=0, column=0, padx=5)

    CardBotao(linha_cx, "Historico Caixas", "Ver todos os caixas", "",
               COR_AZUL,
               lambda: abrir_historico_caixas()
               ).grid(row=0, column=1, padx=5)

# ============================================================
# ============ VENDAS ========================================
# ============================================================

tem_vendas = pode_painel_auditoria or pode_dashboard or pode_operar_pdv or pode_fiscal or pode_compras

if tem_vendas:
    itens = []
    if pode_painel_auditoria: itens.append(1)
    if pode_dashboard: itens.append(1)
    if pode_operar_pdv: itens.append(1)
    if pode_fiscal: itens.append(1)
    if pode_compras: itens.append(1)
    if pode_painel_auditoria:
        titulo = "AUDITORIA E CONFORMIDADE"
        cor = CAT_AUDITORIA
    else:
        titulo = "VENDAS E OPERACOES"
        cor = CAT_VENDAS
    criar_separador(scrollable, titulo, cor, len(itens))
    linha_f = criar_linha_botoes(scrollable)
    col = 0
    if pode_painel_auditoria:
        CardBotao(linha_f, "Painel de Auditoria", "F1", CAT_AUDITORIA,
                   com_permissao("auditoria.ver_log", abrir_painel_auditoria, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_dashboard:
        fkey = "F2" if pode_painel_auditoria else "F1"
        CardBotao(linha_f, "Dashboard", "Analise visual", fkey,
                   COR_AZUL,
                   com_permissao("dashboard.ver", abrir_dashboard, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_operar_pdv:
        CardBotao(linha_f, "PDV (Vendas)", "Nova venda", "F2",
                   CAT_VENDAS,
                   lambda: (verificar_dia_aberto_para_pdv() and com_permissao("pdv.abrir", abrir_pdv, utilizador)())
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_fiscal:
        CardBotao(linha_f, "Modulo Fiscal", "Facturas locais", "F4",
                   "#b45309",
                   com_permissao("fiscal.ver_facturas", abrir_fiscal, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1

    if pode_fiscal:
        CardBotao(linha_f, "Impressao Facturas", "A4 / Termica 80mm", "",
                   "#0ea5e9",
                   lambda: abrir_impressao(utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1

    if pode_compras:
        CardBotao(linha_f, "Entrada Compras", "Registar compras", "",
                   "#059669",
                   com_permissao("compras.listar", abrir_compras, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1


# ============================================================
# ============ DEVOLUCOES ====================================
# ============================================================

if pode_devolucoes:
    criar_separador(scrollable, "DEVOLUCOES", "#dc2626")
    linha_dev = criar_linha_botoes(scrollable)
    CardBotao(linha_dev, "Devolucoes", "Devolver dinheiro", "",
               "#dc2626",
               lambda: abrir_devolucoes(utilizador)
               ).grid(row=0, column=0, padx=5)


# ============================================================
# ============ CADASTROS =====================================
# ============================================================

if pode_produtos_cadastrar or pode_produtos_gestao or pode_fornecedores or pode_clientes or pode_categorias:
    itens = []
    if pode_produtos_cadastrar: itens.append(1)
    if pode_produtos_gestao: itens.append(1)
    if pode_fornecedores: itens.append(1)
    if pode_clientes: itens.append(1)
    if pode_categorias: itens.append(1)
    criar_separador(scrollable, "CADASTROS", CAT_CADASTROS, len(itens))
    linha_f = criar_linha_botoes(scrollable)
    col = 0
    if pode_produtos_cadastrar:
        CardBotao(linha_f, "Cadastrar Produto", "Novo produto", "F7",
                   COR_VERDE,
                   com_permissao("produtos.cadastrar", abrir_cadastro, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_produtos_gestao:
        CardBotao(linha_f, "Gestao de Produtos", "Editar/Ajustar", "F8",
                   CAT_CADASTROS,
                   com_permissao("produtos.editar", abrir_produtos, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_fornecedores:
        CardBotao(linha_f, "Fornecedores", "Gerir", "",
                   "#0ea5e9",
                   com_permissao("fornecedores.listar", abrir_fornecedores, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_clientes:
        CardBotao(linha_f, "Clientes", "Consultar", "",
                   COR_PRIMARIA,
                   com_permissao("clientes.listar", abrir_clientes, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_categorias:
        CardBotao(linha_f, "Categorias", "Organizar", "",
                   "#f97316",
                   com_permissao("categorias.listar", abrir_categorias, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1


# ============================================================
# ============ ESTOQUE =======================================
# ============================================================

if pode_listar_produtos or pode_validade or pode_estoque_baixo or pode_inventario or pode_fefo:
    itens = []
    if pode_listar_produtos: itens.append(1)
    if pode_validade: itens.append(1)
    if pode_estoque_baixo: itens.append(1)
    if pode_inventario: itens.append(1)
    if pode_fefo: itens.append(1)
    criar_separador(scrollable, "ESTOQUE E INVENTARIO", CAT_ESTOQUE, len(itens))
    linha_f = criar_linha_botoes(scrollable)
    col = 0
    if pode_listar_produtos:
        CardBotao(linha_f, "Listar Produtos", "Ver tudo", "",
                   "#0891b2",
                   com_permissao("produtos.listar", abrir_lista_produtos)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_validade:
        CardBotao(linha_f, "Validade Proxima", "90 dias", "",
                   COR_ALERTA,
                   com_permissao("produtos.ver_validade", abrir_relatorio_validade)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_estoque_baixo:
        CardBotao(linha_f, "Estoque Baixo", "Alertas", "",
                   COR_VERMELHO,
                   com_permissao("produtos.listar", abrir_estoque_baixo)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_inventario:
        CardBotao(linha_f, "Inventario Fisico", "Contagem", "F10",
                   "#b45309",
                   com_permissao("inventario.listar", abrir_inventario, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_fefo:
        CardBotao(linha_f, "Relatorio FEFO", "Primeiro a vencer", "",
                   "#be185d",
                   com_permissao("produtos.ver_fefo", abrir_relatorio_fefo)
                   ).grid(row=0, column=col, padx=5)
        col += 1


# ============================================================
# ============ ANALISE =======================================
# ============================================================

if pode_relatorios or pode_historico_vendas or pode_perdas or pode_backup:
    itens = []
    if pode_relatorios: itens.append(1)
    if pode_historico_vendas: itens.append(1)
    if pode_perdas: itens.append(1)
    if pode_backup: itens.append(1)
    criar_separador(scrollable, "ANALISE E RELATORIOS", CAT_ANALISE, len(itens))
    linha_f = criar_linha_botoes(scrollable)
    col = 0
    if pode_relatorios:
        CardBotao(linha_f, "Relatorios", "Analise completa", "F5",
                   CAT_ANALISE,
                   com_permissao("relatorios.ver", abrir_relatorios, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_relatorios:
        CardBotao(linha_f, "Relatorios Avancados", "Curva ABC + Projecao", "",
                   COR_PRIMARIA,
                   lambda: abrir_relatorios_avancados(utilizador, root)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_historico_vendas:
        CardBotao(linha_f, "Historico Vendas", "Ultimas 100", "",
                   COR_PRIMARIA,
                   com_permissao("relatorios.vendas", abrir_historico_vendas)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_perdas:
        CardBotao(linha_f, "Controlo Perdas", "Quebras/Furtos", "F6",
                   "#991b1b",
                   com_permissao("perdas.listar", abrir_perdas, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_backup:
        CardBotao(linha_f, "Backups", "Protecao dados", "F11",
                   "#4f46e5",
                   com_permissao("backup.listar", abrir_backup, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1


# ============================================================
# ============ IA ============================================
# ============================================================

if PERFIL in ("admin", "gerente"):
    criar_separador(scrollable, "INTELIGENCIA ARTIFICIAL", COR_ROXO_CLARO)
    linha_ia = criar_linha_botoes(scrollable)
    CardBotao(linha_ia, "Assistente IA", "Perguntas em portugues", "",
               COR_ROXO_CLARO,
               lambda: abrir_assistente_ia(root, utilizador)
               ).grid(row=0, column=0, padx=5)


# ============================================================
# ============ NUVEM =========================================
# ============================================================

if pode_sincronizar or pode_ver_fila:
    itens = []
    if pode_sincronizar: itens.append(1)
    if pode_ver_fila: itens.append(1)
    criar_separador(scrollable, "NUVEM E SINCRONIZACAO", CAT_NUVEM, len(itens))
    linha_f = criar_linha_botoes(scrollable)
    col = 0
    if pode_sincronizar:
        CardBotao(linha_f, "Sincronizar Nuvem", "Enviar agora", "F9",
                   CAT_NUVEM,
                   lambda: executar_sincronizacao(utilizador, root)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_ver_fila:
        CardBotao(linha_f, "Estado da Fila", "Diagnostico", "F10",
                   COR_PRIMARIA,
                   lambda: abrir_diagnostico_fila(utilizador, root)
                   ).grid(row=0, column=col, padx=5)
        col += 1




# ============================================================
# ============ TRANSFERENCIAS ENTRE FILIAIS (IBT) ============
# ============================================================

pode_transferencias = (PERFIL in ("admin", "gerente") or
                        tem_permissao(PERFIL, "transferencias.ver"))

if pode_transferencias:
    criar_separador(scrollable, "TRANSFERENCIAS ENTRE FILIAIS", "#0ea5e9")
    linha_transf = criar_linha_botoes(scrollable)

    CardBotao(linha_transf, "Transferencias (IBT)",
               "Mover stock entre filiais", "",
               "#0ea5e9",
               lambda: abrir_transferencias(utilizador, root)
               ).grid(row=0, column=0, padx=5)

# ============================================================
# ============ ADMINISTRACAO =================================
# ============================================================

if pode_auditoria or pode_utilizadores or pode_config_farmacia:
    itens = []
    if pode_auditoria: itens.append(1)
    if pode_utilizadores: itens.append(1)
    if pode_config_farmacia: itens.append(1)
    criar_separador(scrollable, "ADMINISTRACAO", CAT_ADMIN, len(itens))
    linha_f = criar_linha_botoes(scrollable)
    col = 0
    if pode_auditoria:
        CardBotao(linha_f, "Log de Auditoria", "Ver registos", "",
                   CAT_ADMIN,
                   com_permissao("auditoria.ver_log", abrir_auditoria)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_utilizadores:
        CardBotao(linha_f, "Utilizadores", "Gerir acessos", "",
                   "#374151",
                   com_permissao("utilizadores.listar", abrir_utilizadores, utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1
    if pode_config_farmacia:
        CardBotao(linha_f, "Config. Farmacia", "Identidade", "",
                   COR_PRIMARIA,
                   lambda: abrir_config_farmacia(utilizador)
                   ).grid(row=0, column=col, padx=5)
        col += 1


# ============================================================
# ============ RODAPE ========================================
# ============================================================

rodape = Frame(root, bg=COR_CARD, height=50)
rodape.pack(fill=X, side=BOTTOM)
rodape.pack_propagate(False)

linha_rodape = Frame(rodape, bg=COR_DOURADO, height=2)
linha_rodape.pack(fill=X)

rodape_inner = Frame(rodape, bg=COR_CARD)
rodape_inner.pack(fill=BOTH, expand=True)

estado_label = Label(rodape_inner, text="...", font=("Segoe UI", 10, "bold"),
                       bg=COR_CARD, fg=COR_ALERTA)
estado_label.pack(side=LEFT, padx=20, pady=15)

tempo_label = Label(rodape_inner, text="", font=("Segoe UI", 9),
                     bg=COR_CARD, fg=COR_TEXTO_SEC)
tempo_label.pack(side=LEFT, padx=10)

pendentes_label = Label(rodape_inner, text="", font=("Segoe UI", 9, "bold"),
                          bg=COR_CARD, fg=COR_TEXTO)
pendentes_label.pack(side=LEFT, padx=10)

fila_label = Label(rodape_inner, text="", font=("Segoe UI", 9),
                    bg=COR_CARD, fg=COR_TEXTO_SEC)
fila_label.pack(side=LEFT, padx=10)

btn_sair = Button(rodape_inner, text="Terminar Sessao",
                    font=("Segoe UI", 10, "bold"),
                    bg=COR_VERMELHO, fg="white", bd=0, cursor="hand2",
                    padx=15, pady=5, activebackground=COR_VERMELHO_HOVER,
                    command=sair_sistema)
btn_sair.pack(side=RIGHT, padx=20, pady=10)

def atualizar_rodape():
    try:
        online, _ = tem_internet()
        if online:
            estado_label.config(text="ONLINE", fg=COR_VERDE)
        else:
            estado_label.config(text="OFFLINE", fg=COR_VERMELHO)
        tempo = ha_quanto_tempo()
        if tempo:
            tempo_label.config(text=f"| Ultima sync: {tempo}")
        else:
            tempo_label.config(text="| Nunca sincronizado")
        p = contar_pendentes()
        if p["pendentes"] > 0:
            pendentes_label.config(text=f"| Pendentes: {p['pendentes']}", fg=COR_ALERTA)
        else:
            pendentes_label.config(text="| Sincronizado", fg=COR_VERDE)
        try:
            e = fila_sync.estatisticas()
            if e["conflitos"] > 0:
                fila_label.config(text=f"| Conflitos: {e['conflitos']}", fg=COR_VERMELHO)
            elif e["abandonados"] > 0:
                fila_label.config(text=f"| Abandonados: {e['abandonados']}", fg=COR_VERMELHO)
            elif e["pendentes"] > 0:
                fila_label.config(text=f"| Fila: {e['pendentes']}", fg=COR_ALERTA)
            else:
                fila_label.config(text=f"| Fila: {e['enviados']} enviados", fg=COR_TEXTO_SEC)
        except Exception:
            fila_label.config(text="")
    except Exception:
        pass
    root.after(10000, atualizar_rodape)

atualizar_rodape()

def ao_sincronizar_auto(resultado):
    try:
        if resultado["total"] > 0:
            print(f"[AUTO-SYNC] {resultado['total']} operacoes enviadas")
    except Exception:
        pass

if pode_painel_auditoria:
    root.bind('<F1>', lambda e: com_permissao("auditoria.ver_log", abrir_painel_auditoria, utilizador)())
if pode_dashboard:
    fkey = '<F2>' if pode_painel_auditoria else '<F1>'
    root.bind(fkey, lambda e: com_permissao("dashboard.ver", abrir_dashboard, utilizador)())
if pode_operar_pdv:
    fkey = '<F3>' if pode_painel_auditoria else '<F2>'
    def _abrir_pdv_atalho(event=None):
        if verificar_dia_aberto_para_pdv():
            com_permissao("pdv.abrir", abrir_pdv, utilizador)()
    root.bind(fkey, _abrir_pdv_atalho)
if pode_fiscal:
    fkey = '<F5>' if pode_painel_auditoria else '<F4>'
    root.bind(fkey, lambda e: com_permissao("fiscal.ver_facturas", abrir_fiscal, utilizador)())
if pode_relatorios:
    root.bind('<F5>', lambda e: com_permissao("relatorios.ver", abrir_relatorios, utilizador)())
if pode_perdas:
    root.bind('<F6>', lambda e: com_permissao("perdas.listar", abrir_perdas, utilizador)())
if pode_produtos_cadastrar:
    root.bind('<F7>', lambda e: com_permissao("produtos.cadastrar", abrir_cadastro, utilizador)())
if pode_produtos_gestao:
    root.bind('<F8>', lambda e: com_permissao("produtos.editar", abrir_produtos, utilizador)())
if pode_sincronizar:
    root.bind('<F9>', lambda e: executar_sincronizacao(utilizador, root))
elif pode_compras:
    root.bind('<F9>', lambda e: com_permissao("compras.listar", abrir_compras, utilizador)())
if pode_ver_fila:
    root.bind('<F10>', lambda e: abrir_diagnostico_fila(utilizador, root))
elif pode_inventario:
    root.bind('<F10>', lambda e: com_permissao("inventario.listar", abrir_inventario, utilizador)())
if pode_backup:
    root.bind('<F11>', lambda e: com_permissao("backup.listar", abrir_backup, utilizador)())

root.bind('<F12>', lambda e: sair_sistema())

def _fechar_ultima(event=None):
    try:
        for w in root.winfo_children():
            if isinstance(w, Toplevel) and w.winfo_viewable():
                w.destroy()
                return
    except Exception:
        pass

root.bind('<Escape>', _fechar_ultima)

iniciar_auto_sync(callback=ao_sincronizar_auto)

# ══════════════════════════════════════════════════════
# MONITOR DE INACTIVIDADE
# ══════════════════════════════════════════════════════
try:
    from monitor_inatividade import MonitorInatividade
    from database import obter_config_financeira

    timeout_txt = obter_config_financeira("timeout_inatividade", "15")
    try:
        timeout_min = int(timeout_txt)
    except Exception:
        timeout_min = 15

    monitor_inatividade = MonitorInatividade(
        root, utilizador, timeout_min=timeout_min
    )
    print(f"[Monitor] Iniciado - timeout: {timeout_min} min")
except Exception as e:
    print(f"[Monitor] Aviso - nao iniciado: {e}")
    monitor_inatividade = None

root.mainloop()
