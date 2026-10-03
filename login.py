"""
Ecrã de login — JAM Soft
Cores alinhadas com o logotipo (roxo + dourado).
Modo fullscreen com card centralizado.
"""
from tkinter import *
from tkinter import messagebox
from pathlib import Path

from PIL import Image, ImageTk

from database import (autenticar, registar_auditoria,
                       esta_bloqueado, tentativas_restantes,
                       tempo_restante_bloqueio)


# ============================================================
# CORES — alinhadas com o logotipo JAM Soft
# ============================================================
COR_PRIMARIA = "#7c3aed"      # Roxo (JAM)
COR_DOURADO = "#fbbf24"        # Dourado (Soft)
COR_ESCURA = "#0f172a"         # Azul escuro (contraste)
COR_FUNDO = "#0f172a"          # Fundo escuro
COR_CARD = "#1e293b"           # Card escuro
COR_TEXTO = "#f8fafc"          # Texto claro
COR_TEXTO_SEC = "#94a3b8"      # Texto secundário
COR_PERIGO = "#ef4444"         # Vermelho
COR_ALERTA = "#f97316"         # Laranja
COR_SUCESSO = "#10b981"        # Verde


# Variável global que guarda o utilizador autenticado
utilizador_logado = None


def abrir_login():
    """Abre a tela de login em fullscreen. Retorna True se autenticou."""
    global utilizador_logado

    janela = Tk()
    janela.title("JAM Soft — Login")
    janela.configure(bg=COR_FUNDO)

    # Fullscreen
    janela.state("zoomed")

    # Ícone da janela
    try:
        _caminho_ico = Path(__file__).parent / "logos" / "jamsoft.ico"
        if _caminho_ico.exists():
            janela.iconbitmap(default=str(_caminho_ico))
    except Exception:
        pass

    # ─── Container centralizado no meio do ecrã ───
    container = Frame(janela, bg=COR_FUNDO)
    container.place(relx=0.5, rely=0.5, anchor=CENTER)

    # ─── Card principal ───
    card = Frame(container, bg=COR_FUNDO, padx=60, pady=40)
    card.pack()

    # ─── Logo ───
    try:
        caminho_logo = Path(__file__).parent / "logos" / "logo_app.png"
        if not caminho_logo.exists():
            caminho_logo = Path(__file__).parent / "logos" / "icon_192.png"

        if caminho_logo.exists():
            img_pil = Image.open(caminho_logo).convert("RGBA")
            img_pil = img_pil.resize((160, 160), Image.LANCZOS)
            _logo_img = ImageTk.PhotoImage(img_pil)

            lbl_logo = Label(card, image=_logo_img, bg=COR_FUNDO)
            lbl_logo.image = _logo_img
            lbl_logo.pack(pady=(0, 15))
        else:
            Label(card, text="💊", font=("Arial", 60),
                  bg=COR_FUNDO, fg=COR_PRIMARIA).pack(pady=(0, 15))
    except Exception as e:
        print(f"[Login] Erro ao carregar logo: {e}")
        Label(card, text="💊", font=("Arial", 60),
              bg=COR_FUNDO, fg=COR_PRIMARIA).pack(pady=(0, 15))

    # ─── Subtítulo ───
    Label(card, text="Sistema de Farmácia",
          font=("Arial", 12, "italic"),
          bg=COR_FUNDO, fg=COR_TEXTO_SEC).pack(pady=(0, 30))

    # ─── Formulário ───
    form = Frame(card, bg=COR_FUNDO)
    form.pack(fill=X)

    Label(form, text="Iniciar Sessão",
          font=("Arial", 18, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(0, 25))

    # Campo utilizador
    Label(form, text="Nome de utilizador:",
          font=("Arial", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO_SEC).pack(anchor=W, pady=(0, 6))

    entry_user = Entry(form, font=("Arial", 13),
                        bg=COR_CARD, fg=COR_TEXTO,
                        insertbackground=COR_TEXTO,
                        width=30, bd=0, relief=FLAT)
    entry_user.pack(fill=X, pady=(0, 18), ipady=12)
    entry_user.focus()

    # Campo senha
    Label(form, text="Palavra-passe:",
          font=("Arial", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO_SEC).pack(anchor=W, pady=(0, 6))

    entry_pass = Entry(form, font=("Arial", 13), show="●",
                        bg=COR_CARD, fg=COR_TEXTO,
                        insertbackground=COR_TEXTO,
                        width=30, bd=0, relief=FLAT)
    entry_pass.pack(fill=X, pady=(0, 18), ipady=12)

    # Mensagens
    msg_var = StringVar()
    msg_label = Label(form, textvariable=msg_var,
                       font=("Arial", 10), bg=COR_FUNDO, fg=COR_PERIGO,
                       wraplength=400, justify=CENTER)
    msg_label.pack(pady=(0, 5))

    aviso_var = StringVar()
    aviso_label = Label(form, textvariable=aviso_var,
                         font=("Arial", 9, "italic"),
                         bg=COR_FUNDO, fg=COR_ALERTA,
                         wraplength=400, justify=CENTER)
    aviso_label.pack(pady=(0, 15))

    # ─── Função de login ───
    def fazer_login(event=None):
        global utilizador_logado
        username = entry_user.get().strip()
        senha = entry_pass.get()

        msg_var.set("")
        aviso_var.set("")

        if not username or not senha:
            msg_var.set("⚠️ Preencha utilizador e palavra-passe")
            return

        # Verificar bloqueio
        try:
            if esta_bloqueado(username):
                minutos = tempo_restante_bloqueio(username)
                msg_label.config(fg=COR_PERIGO)
                msg_var.set("🚫 CONTA TEMPORARIAMENTE BLOQUEADA")
                aviso_var.set(
                    f"Demasiadas tentativas falhadas.\n"
                    f"Tente novamente em {minutos} minuto(s)."
                )
                try:
                    registar_auditoria(0, username, "LOGIN BLOQUEADO",
                                        "Tentativa numa conta bloqueada")
                except Exception:
                    pass
                entry_pass.delete(0, END)
                return
        except Exception as e:
            print(f"[Login] Aviso: {e}")

        # Autenticar
        sucesso, dados = autenticar(username, senha)

        if sucesso:
            utilizador_logado = dados
            registar_auditoria(dados["id"], dados["nome"], "LOGIN",
                                "Sessão iniciada")
            janela.destroy()
        else:
            msg_label.config(fg=COR_PERIGO)
            try:
                if esta_bloqueado(username):
                    minutos = tempo_restante_bloqueio(username)
                    msg_var.set("🚫 CONTA BLOQUEADA")
                    aviso_var.set(
                        f"Atingiu o limite de 3 tentativas.\n"
                        f"Tente novamente em {minutos} minuto(s)."
                    )
                else:
                    restantes = tentativas_restantes(username)
                    msg_var.set("❌ Utilizador ou palavra-passe incorretos")
                    if restantes > 0:
                        aviso_var.set(f"⚠️ Tentativas restantes: {restantes} de 3")
                    else:
                        aviso_var.set("⚠️ A próxima tentativa bloqueará a conta.")
            except Exception:
                msg_var.set("❌ Utilizador ou palavra-passe incorretos")

            entry_pass.delete(0, END)
            entry_pass.focus()

    entry_user.bind('<Return>', lambda e: entry_pass.focus())
    entry_pass.bind('<Return>', fazer_login)

    # ─── Botão Entrar ───
    btn_entrar = Button(
        form,
        text="🔓  Entrar",
        font=("Arial", 14, "bold"),
        bg=COR_PRIMARIA,
        fg="white",
        activebackground="#6d28d9",
        activeforeground="white",
        bd=0,
        relief=FLAT,
        cursor="hand2",
        height=2,
        command=fazer_login,
    )
    btn_entrar.pack(fill=X, pady=(10, 12))

    # ─── Botão Sair ───
    btn_sair = Button(
        form,
        text="Sair",
        font=("Arial", 11),
        bg=COR_FUNDO,
        fg=COR_TEXTO_SEC,
        activebackground=COR_FUNDO,
        activeforeground=COR_PERIGO,
        bd=0,
        relief=FLAT,
        cursor="hand2",
        command=janela.destroy,
    )
    btn_sair.pack()

    # ─── Rodapé fixo no fundo ───
    Label(janela, text="JAM Soft © 2026 — Todos os direitos reservados",
          font=("Arial", 9), bg=COR_FUNDO, fg=COR_TEXTO_SEC).pack(
              side=BOTTOM, pady=20)

    janela.mainloop()

    return utilizador_logado is not None


def obter_utilizador():
    """Retorna o utilizador autenticado."""
    return utilizador_logado


def terminar_sessao():
    """Termina a sessão do utilizador."""
    global utilizador_logado
    if utilizador_logado:
        registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                            "LOGOUT", "Sessão terminada")
    utilizador_logado = None