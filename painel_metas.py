# ============================================================
# ============ PAINEL DE METAS (compacto) ====================
# ============================================================

from tkinter import *
from datetime import datetime
from database import progresso_mes, progresso_dia
from moeda import formatar_kz


COR_FUNDO_PAINEL = "#1e293b"
COR_CARD = "#0f172a"
COR_TEXTO = "#f8fafc"
COR_TEXTO_SEC = "#94a3b8"
COR_DOURADO = "#fbbf24"
COR_VERDE = "#10b981"
COR_VERMELHO = "#ef4444"
COR_ALERTA = "#f97316"
COR_AMARELO = "#eab308"
COR_AZUL = "#0ea5e9"


def obter_cor_e_mensagem(percentagem):
    if percentagem >= 100:
        return COR_VERDE, "🎉", "Meta batida! Excelente trabalho!"
    elif percentagem >= 80:
        return COR_AMARELO, "🔥", "Quase la! Falta pouco."
    elif percentagem >= 50:
        return COR_ALERTA, "⚡", "A caminho — bom ritmo."
    elif percentagem >= 25:
        return COR_AZUL, "📈", "A acelerar — vamos la!"
    else:
        return COR_VERMELHO, "⚠️", "Atencao — precisa acelerar."


def criar_barra_progresso(parent, percentagem, cor, largura=260, altura=14):
    visual = min(percentagem, 100)
    
    canvas = Canvas(parent, width=largura, height=altura,
                     bg="#334155", highlightthickness=0)
    canvas.pack(fill=X, pady=2)
    
    largura_preenchida = (visual / 100) * largura
    
    if largura_preenchida > 0:
        canvas.create_rectangle(
            0, 0, largura_preenchida, altura,
            fill=cor, outline=""
        )
    
    canvas.create_text(
        largura / 2, altura / 2,
        text=f"{percentagem:.0f}%",
        fill="white",
        font=("Segoe UI", 8, "bold")
    )
    
    return canvas


def criar_painel_metas(parent, utilizador_logado=None):
    """Painel compacto de metas."""
    
    try:
        # ===== CABECALHO COM DATA/HORA =====
        header = Frame(parent, bg=COR_FUNDO_PAINEL)
        header.pack(fill=X, padx=10, pady=(6, 3))
        
        Label(header, text="🎯 METAS",
              font=("Segoe UI", 11, "bold"),
              bg=COR_FUNDO_PAINEL, fg=COR_DOURADO).pack(side=LEFT, padx=(3, 0))
        
        # Relogio em tempo real
        relogio_var = StringVar(value="")
        relogio_label = Label(header,
                                textvariable=relogio_var,
                                font=("Segoe UI", 9, "italic"),
                                bg=COR_FUNDO_PAINEL, fg=COR_TEXTO_SEC)
        relogio_label.pack(side=RIGHT, padx=3)
        
        def atualizar_relogio():
            try:
                agora = datetime.now()
                # Verifica se ainda existe (pode ter sido destruido)
                if relogio_label.winfo_exists():
                    relogio_var.set(f"🕐 {agora.strftime('%d/%m/%Y  %H:%M:%S')}")
                    relogio_label.after(1000, atualizar_relogio)
            except Exception:
                pass
        
        atualizar_relogio()
        
        # ===== CONTAINER DE CARDS =====
        cards_container = Frame(parent, bg=COR_FUNDO_PAINEL)
        cards_container.pack(fill=X, padx=10, pady=(0, 6))
        
        criar_card_mes(cards_container)
        criar_card_dia(cards_container)
        
        # ===== MENSAGEM MOTIVACIONAL =====
        criar_mensagem_motivacional(parent)
    
    except Exception as e:
        Label(parent, text=f"[Painel de metas indisponivel: {e}]",
              font=("Segoe UI", 9, "italic"),
              bg=COR_FUNDO_PAINEL, fg=COR_VERMELHO).pack(pady=8)


def criar_card_mes(parent):
    """Card do progresso do mes (compacto)."""
    
    dados = progresso_mes()
    
    card = Frame(parent, bg=COR_CARD, highlightthickness=1,
                  highlightbackground="#334155")
    card.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
    
    # Cabecalho
    cab = Frame(card, bg=COR_CARD)
    cab.pack(fill=X, padx=10, pady=(6, 3))
    
    mes_str = dados["mes"]
    try:
        dt = datetime.strptime(mes_str + "-01", "%Y-%m-%d")
        mes_nome = dt.strftime("%B %Y").capitalize()
    except Exception:
        mes_nome = mes_str
    
    Label(cab, text=f"📅 MES ({mes_nome})",
          font=("Segoe UI", 8, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W)
    
    if dados["orcamento"] <= 0:
        Label(card, text="Orcamento nao definido",
              font=("Segoe UI", 9, "italic"),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(3, 6), padx=10, anchor=W)
        return
    
    cor, _, _ = obter_cor_e_mensagem(dados["percentagem"])
    
    # Info compacta (2 colunas)
    info = Frame(card, bg=COR_CARD)
    info.pack(fill=X, padx=10, pady=(2, 0))
    
    col1 = Frame(info, bg=COR_CARD)
    col1.pack(side=LEFT, expand=True, fill=X)
    Label(col1, text="Orcamento:", font=("Segoe UI", 7),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W)
    Label(col1, text=formatar_kz(dados["orcamento"]),
          font=("Segoe UI", 9, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W)
    
    col2 = Frame(info, bg=COR_CARD)
    col2.pack(side=LEFT, expand=True, fill=X)
    Label(col2, text="Vendido:", font=("Segoe UI", 7),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W)
    Label(col2, text=formatar_kz(dados["vendido"]),
          font=("Segoe UI", 9, "bold"),
          bg=COR_CARD, fg=cor).pack(anchor=W)
    
    # Barra
    barra = Frame(card, bg=COR_CARD)
    barra.pack(fill=X, padx=10, pady=(4, 1))
    criar_barra_progresso(barra, dados["percentagem"], cor)
    
    # Falta
    Label(card, text=f"Faltam: {formatar_kz(dados['falta'])}",
          font=("Segoe UI", 7, "italic"),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(1, 5), padx=10, anchor=W)


def criar_card_dia(parent):
    """Card do progresso do dia (compacto)."""
    
    dados = progresso_dia()
    
    card = Frame(parent, bg=COR_CARD, highlightthickness=1,
                  highlightbackground="#334155")
    card.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0))
    
    cab = Frame(card, bg=COR_CARD)
    cab.pack(fill=X, padx=10, pady=(6, 3))
    
    try:
        dt = datetime.strptime(dados["data"], "%Y-%m-%d")
        data_str = dt.strftime("%d/%m/%Y")
    except Exception:
        data_str = dados["data"]
    
    Label(cab, text=f"📆 DIA ({data_str})",
          font=("Segoe UI", 8, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W)
    
    if dados["orcamento"] <= 0:
        Label(card, text="Orcamento nao definido",
              font=("Segoe UI", 9, "italic"),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(3, 6), padx=10, anchor=W)
        return
    
    cor, _, _ = obter_cor_e_mensagem(dados["percentagem"])
    
    info = Frame(card, bg=COR_CARD)
    info.pack(fill=X, padx=10, pady=(2, 0))
    
    col1 = Frame(info, bg=COR_CARD)
    col1.pack(side=LEFT, expand=True, fill=X)
    Label(col1, text="Orcamento:", font=("Segoe UI", 7),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W)
    Label(col1, text=formatar_kz(dados["orcamento"]),
          font=("Segoe UI", 9, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W)
    
    col2 = Frame(info, bg=COR_CARD)
    col2.pack(side=LEFT, expand=True, fill=X)
    Label(col2, text="Vendido:", font=("Segoe UI", 7),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor=W)
    Label(col2, text=formatar_kz(dados["vendido"]),
          font=("Segoe UI", 9, "bold"),
          bg=COR_CARD, fg=cor).pack(anchor=W)
    
    barra = Frame(card, bg=COR_CARD)
    barra.pack(fill=X, padx=10, pady=(4, 1))
    criar_barra_progresso(barra, dados["percentagem"], cor)
    
    if dados["percentagem"] >= 100:
        Label(card,
              text=f"🎉 Meta batida! (+{formatar_kz(dados['vendido'] - dados['orcamento'])})",
              font=("Segoe UI", 7, "bold"),
              bg=COR_CARD, fg=COR_VERDE).pack(pady=(1, 5), padx=10, anchor=W)
    else:
        Label(card, text=f"Faltam: {formatar_kz(dados['falta'])}",
              font=("Segoe UI", 7, "italic"),
              bg=COR_CARD, fg=COR_TEXTO_SEC).pack(pady=(1, 5), padx=10, anchor=W)


def criar_mensagem_motivacional(parent):
    """Mensagem motivacional (compacta)."""
    
    dados_dia = progresso_dia()
    dados_mes = progresso_mes()
    
    if dados_dia["orcamento"] > 0:
        cor, emoji, msg = obter_cor_e_mensagem(dados_dia["percentagem"])
        texto = f"{emoji} {msg}"
    elif dados_mes["orcamento"] > 0:
        cor, emoji, msg = obter_cor_e_mensagem(dados_mes["percentagem"])
        texto = f"{emoji} {msg}"
    else:
        cor = COR_TEXTO_SEC
        texto = "💡 O administrador ainda nao definiu o orcamento mensal."
    
    frame_msg = Frame(parent, bg=COR_FUNDO_PAINEL)
    frame_msg.pack(fill=X, padx=10, pady=(0, 6))
    
    Label(frame_msg, text=texto,
          font=("Segoe UI", 8, "bold"),
          bg=COR_FUNDO_PAINEL, fg=cor).pack(anchor=W)


# ============================================================
# ============ TESTE DIRETO ==================================
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  TESTE - painel_metas.py (compacto)")
    print("="*60)
    
    print("\n[1] Dados do mes:")
    pm = progresso_mes()
    for k, v in pm.items():
        print(f"    {k}: {v}")
    
    print("\n[2] Dados do dia:")
    pd = progresso_dia()
    for k, v in pd.items():
        print(f"    {k}: {v}")
    
    print("\n[3] Abrir janela de teste...")
    
    root = Tk()
    root.title("Teste - Painel de Metas")
    root.geometry("700x300")
    root.configure(bg="#1e293b")
    
    frame = Frame(root, bg="#1e293b")
    frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    criar_painel_metas(frame)
    
    root.mainloop()
    
    print("\n" + "="*60 + "\n")