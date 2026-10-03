# ============================================================
# ============ IA - DISTRIBUICAO DE ORCAMENTO ================
# ============================================================
# 
# Ecrã que mostra a sugestao da IA:
#   - Distribuicao dia-a-dia do orcamento mensal
#   - Grafico de barras com padrao detectado
#   - Comparacao com historico
#   - Botoes: Guardar / Ajustar / Fechar
# 
# ============================================================

from tkinter import *
from tkinter import messagebox, ttk
from datetime import datetime
from database import (distribuir_orcamento_mes, obter_orcamento_mes,
                       obter_config_ia, gravar_config_ia,
                       definir_orcamento_mes, registar_auditoria,
                       conectar)
from moeda import formatar_kz


# ============================================================
# ============ CORES =========================================
# ============================================================

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


DIAS_SEMANA = ["Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado", "Domingo"]


def nome_mes_pt(mes_str):
    """Converte '2026-09' em 'Setembro 2026'."""
    meses = {
        "01": "Janeiro", "02": "Fevereiro", "03": "Marco",
        "04": "Abril", "05": "Maio", "06": "Junho",
        "07": "Julho", "08": "Agosto", "09": "Setembro",
        "10": "Outubro", "11": "Novembro", "12": "Dezembro",
    }
    try:
        ano, m = mes_str.split("-")
        return f"{meses.get(m, m)} {ano}"
    except Exception:
        return mes_str


# ============================================================
# ============ ECRAN PRINCIPAL ===============================
# ============================================================

def abrir_ia_orcamento(utilizador_logado, parent=None, mes=None):
    """Abre o ecra de IA para distribuicao de orcamento."""
    
    if parent is None:
        parent = Toplevel()
        parent.withdraw()
    
    if not mes:
        mes = datetime.now().strftime("%Y-%m")
    
    janela = Toplevel(parent)
    janela.title(f"IA - Distribuicao de Orcamento - {nome_mes_pt(mes)}")
    janela.geometry("1200x850")
    janela.configure(bg=COR_FUNDO)
    
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 1200) // 2
    y = (janela.winfo_screenheight() - 850) // 2
    janela.geometry(f"1200x850+{x}+{y}")
    
    # Header
    header = Frame(janela, bg=COR_PRIMARIA, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text=f"🤖 IA - Distribuicao de Orcamento",
          font=("Segoe UI", 18, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=(12, 0))
    Label(header, text=f"{nome_mes_pt(mes)}  |  Utilizador: {utilizador_logado['nome']}",
          font=("Segoe UI", 10, "italic"),
          bg=COR_PRIMARIA, fg="#e0e7ff").pack()
    
    # Content area (recarregavel)
    content = Frame(janela, bg=COR_FUNDO)
    content.pack(fill=BOTH, expand=True)
    
    def recarregar():
        for w in content.winfo_children():
            w.destroy()
        construir_conteudo(content, utilizador_logado, janela, mes, recarregar)
    
    construir_conteudo(content, utilizador_logado, janela, mes, recarregar)


def construir_conteudo(content, utilizador_logado, janela, mes, recarregar):
    """Constroi o conteudo do ecra."""
    
    # Obter sugestoes da IA
    try:
        dados = distribuir_orcamento_mes(mes)
    except Exception as e:
        Label(content, text=f"Erro ao calcular: {e}",
              font=("Segoe UI", 12, "italic"),
              bg=COR_FUNDO, fg=COR_VERMELHO).pack(pady=50)
        return
    
    if not dados:
        Label(content, text=f"Nao ha orcamento definido para {nome_mes_pt(mes)}.",
              font=("Segoe UI", 13, "italic"),
              bg=COR_FUNDO, fg=COR_ALERTA).pack(pady=30)
        Label(content, text="Defina primeiro um orcamento mensal no ecra 'Metas'.",
              font=("Segoe UI", 11),
              bg=COR_FUNDO, fg=COR_TEXTO_SEC).pack()
        Button(content, text="Fechar",
               font=("Segoe UI", 11),
               bg="#64748b", fg="white",
               bd=0, cursor="hand2", padx=20, pady=6,
               command=janela.destroy).pack(pady=30)
        return
    
    sugestoes = dados["sugestoes"]
    orcamento_mes = dados["orcamento_mes"]
    
    # ===== CARDS DE RESUMO =====
    cards = Frame(content, bg=COR_FUNDO)
    cards.pack(fill=X, padx=20, pady=15)
    
    def card_resumo(parent, titulo, valor, cor, coluna):
        card = Frame(parent, bg=COR_CARD, highlightthickness=2, highlightbackground=cor)
        card.grid(row=0, column=coluna, padx=5, pady=5, sticky="nsew")
        parent.columnconfigure(coluna, weight=1)
        
        Label(card, text=titulo, font=("Segoe UI", 9, "bold"),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(10, 3))
        Label(card, text=valor, font=("Segoe UI", 14, "bold"),
              bg=COR_CARD, fg=cor).pack(pady=(0, 10))
    
    # Estatisticas
    total_sugerido = sum(s["sugestao"] for s in sugestoes)
    media = total_sugerido / len(sugestoes) if sugestoes else 0
    maximo = max(sugestoes, key=lambda x: x["sugestao"]) if sugestoes else None
    minimo = min(sugestoes, key=lambda x: x["sugestao"]) if sugestoes else None
    
    card_resumo(cards, "ORCAMENTO MENSAL", formatar_kz(orcamento_mes), COR_DOURADO, 0)
    card_resumo(cards, "MEDIA DIARIA", formatar_kz(media), COR_AZUL, 1)
    card_resumo(cards, "DIA MAIS FORTE", formatar_kz(maximo["sugestao"]) if maximo else "-", COR_VERDE, 2)
    card_resumo(cards, "DIA MAIS FRACO", formatar_kz(minimo["sugestao"]) if minimo else "-", COR_VERMELHO, 3)
    
    # ===== CONFIGURACOES IA =====
    Label(content, text="Configuracoes IA",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=30, pady=(15, 5))
    
    config_frame = Frame(content, bg=COR_CARD, highlightthickness=1, highlightbackground=COR_BORDA)
    config_frame.pack(fill=X, padx=30, pady=5)
    
    inner_config = Frame(config_frame, bg=COR_CARD)
    inner_config.pack(padx=20, pady=10, fill=X)
    
    crescimento = obter_config_ia("crescimento_anual_percentual", "20")
    inflacao = obter_config_ia("inflacao_anual_percentual", "15")
    usar_auto = obter_config_ia("usar_crescimento_automatico", "1")
    
    Label(inner_config, text=f"• Crescimento anual: {crescimento}%  ({'automatico' if usar_auto == '1' else 'configurado'})",
          font=("Segoe UI", 10),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=2)
    Label(inner_config, text=f"• Inflacao anual: {inflacao}%",
          font=("Segoe UI", 10),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=2)
    
    # ===== GRAFICO =====
    Label(content, text="Distribuicao Visual",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=30, pady=(15, 5))
    
    frame_graf = Frame(content, bg=COR_CARD, highlightthickness=1, highlightbackground=COR_BORDA)
    frame_graf.pack(fill=X, padx=30, pady=5)
    
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        fig = Figure(figsize=(11, 3.5), dpi=80, facecolor=COR_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(COR_CARD)
        
        dias = [s["data"][-2:] for s in sugestoes]
        valores = [s["sugestao"] for s in sugestoes]
        
        # Cor conforme dia da semana
        cores = []
        for s in sugestoes:
            try:
                dt = datetime.strptime(s["data"], "%Y-%m-%d")
                if dt.weekday() >= 5:
                    cores.append(COR_VERDE)
                else:
                    cores.append(COR_AZUL)
            except Exception:
                cores.append(COR_AZUL)
        
        bars = ax.bar(dias, valores, color=cores, edgecolor="#1e293b")
        ax.set_title("Sugestao IA por Dia (Verde = Fim de Semana)",
                      fontsize=11, fontweight="bold", color=COR_TEXTO)
        ax.set_ylabel("Kz", fontsize=9, color=COR_TEXTO)
        ax.tick_params(colors=COR_TEXTO, labelsize=7)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame_graf)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True, padx=10, pady=10)
    except Exception as e:
        Label(frame_graf, text=f"Erro ao gerar grafico: {e}",
              bg=COR_CARD, fg=COR_VERMELHO).pack(pady=10)
    
    # ===== TABELA DETALHADA =====
    Label(content, text="Detalhe Dia-a-Dia",
          font=("Segoe UI", 11, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(anchor=W, padx=30, pady=(15, 5))
    
    frame_tab = Frame(content, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=30, pady=(0, 10))
    
    colunas = ("Data", "Dia", "Sugestao IA", "Crescimento", "Inflacao", "Historico")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=10)
    
    for c in colunas:
        tree.heading(c, text=c)
    
    tree.column("Data", width=100)
    tree.column("Dia", width=100)
    tree.column("Sugestao IA", width=140)
    tree.column("Crescimento", width=120)
    tree.column("Inflacao", width=100)
    tree.column("Historico", width=300)
    
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    tree.tag_configure("fim_semana", background="#132a1a", foreground=COR_VERDE)
    tree.tag_configure("semana", background="#13253a", foreground=COR_AZUL)
    
    for s in sugestoes:
        data_str = s["data"]
        try:
            dt = datetime.strptime(data_str, "%Y-%m-%d")
            dia_semana_nome = DIAS_SEMANA[dt.weekday()]
            tag = "fim_semana" if dt.weekday() >= 5 else "semana"
        except Exception:
            dia_semana_nome = "-"
            tag = "semana"
        
        hist_str = "-"
        if s.get("historico_anos"):
            partes = [f"{h['ano']}: {formatar_kz(h['total'])}" for h in s["historico_anos"]]
            hist_str = " | ".join(partes)
        
        cres = s.get("crescimento_percentual", 0)
        infl = s.get("inflacao_percentual", 0)
        
        tree.insert("", END, values=(
            data_str,
            dia_semana_nome,
            formatar_kz(s["sugestao"]),
            f"+{cres:.1f}%",
            f"+{infl:.1f}%",
            hist_str
        ), tags=(tag,))
    
    # ===== BOTOES =====
    frame_btn = Frame(content, bg=COR_FUNDO)
    frame_btn.pack(fill=X, pady=15)
    
    Button(frame_btn, text="Actualizar Sugestao",
           font=("Segoe UI", 11, "bold"),
           bg=COR_AZUL, fg="white",
           width=20, height=2, bd=0, cursor="hand2",
           activebackground="#0284c7",
           command=recarregar).pack(side=LEFT, padx=20)
    
    Button(frame_btn, text="Fechar",
           font=("Segoe UI", 11, "bold"),
           bg="#64748b", fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=RIGHT, padx=20)


# ============================================================
# ============ TESTE DIRETO ==================================
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  TESTE - ia_orcamento.py")
    print("="*60)
    
    print("\n[1] A calcular distribuicao...")
    from database import distribuir_orcamento_mes
    d = distribuir_orcamento_mes()
    if d:
        print(f"    Mes: {d['mes']}")
        print(f"    Orcamento: {d['orcamento_mes']}")
        print(f"    Dias: {d['dias_no_mes']}")
        print(f"    Total sugerido: {sum(s['sugestao'] for s in d['sugestoes']):.2f}")
    else:
        print("    Sem orcamento definido")
    
    print("\n[2] Abrir janela...")
    
    root = Tk()
    root.withdraw()
    
    utilizador = {"id": 1, "nome": "Teste", "perfil": "admin"}
    
    abrir_ia_orcamento(utilizador, root)
    
    root.mainloop()
    
    print("\n" + "="*60 + "\n")