from tkinter import *
from tkinter import messagebox
from database import (autenticar, registar_auditoria,
                       esta_bloqueado, tentativas_restantes,
                       tempo_restante_bloqueio)

COR_FUNDO = "#f0fdf4"
COR_PRIMARIA = "#16a34a"
COR_TEXTO = "#14532d"
COR_CARD = "#ffffff"
COR_PERIGO = "#dc2626"
COR_ALERTA = "#f97316"

# Variavel global que guarda o utilizador autenticado
utilizador_logado = None


def abrir_login():
    """Abre a tela de login. Retorna True se autenticou, False se cancelou."""
    global utilizador_logado
    
    janela = Tk()
    janela.title("JAM Soft — Login")
    janela.geometry("450x550")
    janela.configure(bg=COR_FUNDO)
    janela.resizable(False, False)
    
    # Centraliza a janela
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 450) // 2
    y = (janela.winfo_screenheight() - 550) // 2
    janela.geometry(f"450x550+{x}+{y}")
    
    # Cabecalho
    header = Frame(janela, bg=COR_PRIMARIA, height=140)
    header.pack(fill=X)
    header.pack_propagate(False)
    
    Label(header, text="💊", font=("Arial", 40), bg=COR_PRIMARIA, fg="white").pack(pady=(20, 0))
    Label(header, text="JAM Soft", font=("Arial", 22, "bold"),
          bg=COR_PRIMARIA, fg="white").pack()
    Label(header, text="Sistema de Farmacia", font=("Arial", 11, "italic"),
          bg=COR_PRIMARIA, fg="#dcfce7").pack()
    
    # Corpo
    corpo = Frame(janela, bg=COR_FUNDO)
    corpo.pack(pady=30, padx=40, fill=X)
    
    Label(corpo, text="Iniciar Sessao", font=("Arial", 16, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(0, 20))
    
    Label(corpo, text="Nome de utilizador:", font=("Arial", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(0, 5))
    
    entry_user = Entry(corpo, font=("Arial", 13), bd=1, relief=SOLID)
    entry_user.pack(fill=X, pady=(0, 15), ipady=8)
    entry_user.focus()
    
    Label(corpo, text="Palavra-passe:", font=("Arial", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(0, 5))
    
    entry_pass = Entry(corpo, font=("Arial", 13), bd=1, relief=SOLID, show="●")
    entry_pass.pack(fill=X, pady=(0, 15), ipady=8)
    
    # Mensagem (erro ou aviso)
    msg_var = StringVar()
    msg_label = Label(corpo, textvariable=msg_var, font=("Arial", 10),
                       bg=COR_FUNDO, fg=COR_PERIGO,
                       wraplength=350, justify=CENTER)
    msg_label.pack(pady=(0, 5))
    
    # Aviso de tentativas (linha separada)
    aviso_var = StringVar()
    aviso_label = Label(corpo, textvariable=aviso_var, font=("Arial", 9, "italic"),
                         bg=COR_FUNDO, fg=COR_ALERTA,
                         wraplength=350, justify=CENTER)
    aviso_label.pack(pady=(0, 10))
    
    def fazer_login(event=None):
        global utilizador_logado
        username = entry_user.get().strip()
        senha = entry_pass.get()
        
        # Limpa mensagens antigas
        msg_var.set("")
        aviso_var.set("")
        
        if not username or not senha:
            msg_var.set("⚠️ Preencha utilizador e palavra-passe")
            return
        
        # 1. Verificar se esta bloqueado ANTES de tentar
        try:
            if esta_bloqueado(username):
                minutos = tempo_restante_bloqueio(username)
                msg_label.config(fg=COR_PERIGO)
                msg_var.set("🚫 CONTA TEMPORARIAMENTE BLOQUEADA")
                aviso_var.set(
                    f"Demasiadas tentativas falhadas.\n"
                    f"Tente novamente em {minutos} minuto(s).\n\n"
                    f"Por seguranca, esta tentativa foi registada."
                )
                # Registar auditoria
                try:
                    registar_auditoria(0, username, "LOGIN BLOQUEADO",
                                        f"Tentativa de login numa conta bloqueada")
                except Exception:
                    pass
                entry_pass.delete(0, END)
                return
        except Exception as e:
            print(f"[Login] Aviso ao verificar bloqueio: {e}")
        
        # 2. Tentar autenticar
        sucesso, dados = autenticar(username, senha)
        
        if sucesso:
            # Login bem-sucedido
            utilizador_logado = dados
            registar_auditoria(dados["id"], dados["nome"], "LOGIN",
                                f"Sessao iniciada")
            janela.destroy()
        else:
            # Login falhou
            msg_label.config(fg=COR_PERIGO)
            
            # Verificar se a falha anterior bloqueou
            try:
                if esta_bloqueado(username):
                    minutos = tempo_restante_bloqueio(username)
                    msg_var.set("🚫 CONTA BLOQUEADA")
                    aviso_var.set(
                        f"Atingiu o limite de {3} tentativas falhadas.\n"
                        f"Tente novamente em {minutos} minuto(s)."
                    )
                else:
                    restantes = tentativas_restantes(username)
                    msg_var.set("❌ Utilizador ou palavra-passe incorretos")
                    if restantes > 0:
                        aviso_var.set(
                            f"⚠️ Tentativas restantes: {restantes} de 3"
                        )
                    else:
                        aviso_var.set("⚠️ A proxima tentativa bloqueara a conta.")
            except Exception:
                # Se der erro, mostra mensagem padrao
                msg_var.set("❌ Utilizador ou palavra-passe incorretos")
            
            entry_pass.delete(0, END)
            entry_pass.focus()
    
    entry_user.bind('<Return>', lambda e: entry_pass.focus())
    entry_pass.bind('<Return>', fazer_login)
    
    Button(corpo, text="🔓 Entrar", font=("Arial", 13, "bold"),
           bg=COR_PRIMARIA, fg="white", bd=0, cursor="hand2", height=2,
           command=fazer_login).pack(fill=X, pady=(20, 10))
    
    Button(corpo, text="Sair", font=("Arial", 10),
           bg=COR_FUNDO, fg=COR_PERIGO, bd=0, cursor="hand2",
           command=janela.destroy).pack()
    
    Label(janela, text="JAM Soft © 2026 — Todos os direitos reservados",
          font=("Arial", 8), bg=COR_FUNDO, fg="#9ca3af").pack(side=BOTTOM, pady=10)
    
    janela.mainloop()
    
    return utilizador_logado is not None


def obter_utilizador():
    """Retorna o utilizador autenticado."""
    return utilizador_logado


def terminar_sessao():
    """Termina a sessao do utilizador."""
    global utilizador_logado
    if utilizador_logado:
        registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                            "LOGOUT", "Sessao terminada")
    utilizador_logado = None