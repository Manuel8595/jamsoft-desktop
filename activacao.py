# -*- coding: utf-8 -*-
"""Wizard de activacao JAM Soft (usa requests puro)."""
import os
import requests
from datetime import datetime
from tkinter import *
from tkinter import messagebox

from config_activacao import guardar_activacao

COR_FUNDO = "#0f172a"
COR_CARD = "#1e293b"
COR_ROXO = "#7c3aed"
COR_DOURADO = "#fbbf24"
COR_TEXTO = "#f8fafc"
COR_ERRO = "#ef4444"
COR_SUCESSO = "#10b981"


def validar_chave_online(chave):
    """Valida a chave via Supabase REST API (usa requests)."""
    from config_cloud import SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, CLOUD_ACCESS_ENABLED

    if not CLOUD_ACCESS_ENABLED:
        return False, "Cloud desligada no .env", None

    if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
        return False, "Supabase nao configurado no .env", None

    chave = chave.strip().upper()
    url = f"{SUPABASE_URL}/rest/v1/activacoes?chave=eq.{chave}&select=*"
    headers = {
        "apikey": SUPABASE_PUBLISHABLE_KEY,
        "Authorization": f"Bearer {SUPABASE_PUBLISHABLE_KEY}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return False, f"Erro HTTP {r.status_code}", None
        dados_lista = r.json()
        if not dados_lista:
            return False, "Chave nao encontrada.", None
        dados = dados_lista[0]
        if not dados.get("activa"):
            return False, "Esta chave foi desactivada.", None

        # Actualizar ultima_validacao (best-effort)
        try:
            url_upd = f"{SUPABASE_URL}/rest/v1/activacoes?chave=eq.{chave}"
            requests.patch(url_upd, headers=headers, json={
                "ultima_validacao": datetime.now().isoformat()
            }, timeout=5)
        except Exception:
            pass

        return True, "Chave valida!", dados
    except requests.exceptions.RequestException as e:
        return False, f"Erro de ligacao: {e}", None


def mostrar_wizard_activacao():
    resultado = {"activado": False}

    janela = Tk()
    janela.title("JAM Soft - Activacao")
    janela.geometry("520x420")
    janela.configure(bg=COR_FUNDO)
    janela.resizable(False, False)

    header = Frame(janela, bg=COR_ROXO, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)

    Label(header, text="JAM Soft", font=("Arial", 18, "bold"),
          bg=COR_ROXO, fg="white").pack(pady=(15, 0))
    Label(header, text="Activacao Inicial", font=("Arial", 11),
          bg=COR_ROXO, fg="#e0d5ff").pack()

    corpo = Frame(janela, bg=COR_FUNDO, padx=30, pady=20)
    corpo.pack(fill=BOTH, expand=True)

    Label(corpo, text="Bem-vindo ao JAM Soft!",
          font=("Arial", 14, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(10, 5))

    Label(corpo, text="Esta e a primeira vez que a app corre neste computador.\nIntroduza a chave de activacao fornecida pelo administrador.",
          font=("Arial", 10), bg=COR_FUNDO, fg="#94a3b8", justify=LEFT).pack(anchor=W, pady=(0, 20))

    Label(corpo, text="Chave de activacao:",
          font=("Arial", 11, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(0, 5))

    entry_chave = Entry(corpo, font=("Consolas", 13), bg=COR_CARD, fg=COR_TEXTO,
                        insertbackground=COR_TEXTO, bd=0, relief=FLAT,
                        highlightthickness=2, highlightbackground=COR_ROXO,
                        highlightcolor=COR_DOURADO)
    entry_chave.pack(fill=X, ipady=10, pady=(0, 15))
    entry_chave.focus()

    status_var = StringVar(value="")
    lbl_status = Label(corpo, textvariable=status_var, font=("Arial", 10, "bold"),
                       bg=COR_FUNDO, fg=COR_DOURADO, wraplength=440, justify=LEFT)
    lbl_status.pack(anchor=W, pady=(5, 15))

    def activar():
        chave = entry_chave.get().strip().upper()
        if not chave:
            status_var.set("Introduza uma chave.")
            lbl_status.configure(fg=COR_ERRO)
            return
        status_var.set("A validar...")
        lbl_status.configure(fg=COR_DOURADO)
        janela.update()
        sucesso, msg, dados = validar_chave_online(chave)
        if sucesso and dados:
            from config_cloud import SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY
            guardar_activacao(
                chave=chave,
                farmacia_nome=dados.get("farmacia_nome", ""),
                farmacia_nif=dados.get("farmacia_nif", ""),
                serie=dados.get("serie_padrao", "FT2026/"),
                supabase_url=SUPABASE_URL,
                supabase_key=SUPABASE_PUBLISHABLE_KEY,
            )
            status_var.set("OK - " + msg)
            lbl_status.configure(fg=COR_SUCESSO)
            janela.update()
            messagebox.showinfo("Activacao Concluida",
                "JAM Soft activado!\n\nFarmacia: " + str(dados.get("farmacia_nome", "")) + 
                "\nNIF: " + str(dados.get("farmacia_nif", "")) + 
                "\nSerie: " + str(dados.get("serie_padrao", "")) + 
                "\n\nA app vai agora sincronizar automaticamente.")
            resultado["activado"] = True
            janela.destroy()
        else:
            status_var.set("ERRO - " + msg)
            lbl_status.configure(fg=COR_ERRO)

    def continuar_offline():
        if messagebox.askyesno("Continuar Offline",
            "A app vai funcionar SEM sincronizacao com a nuvem.\n\nPode activar mais tarde nas Configuracoes.\n\nContinuar?"):
            resultado["activado"] = False
            janela.destroy()

    frame_btn = Frame(corpo, bg=COR_FUNDO)
    frame_btn.pack(fill=X, pady=(10, 0))

    Button(frame_btn, text="Activar", font=("Arial", 12, "bold"),
           bg=COR_SUCESSO, fg="white", bd=0, cursor="hand2",
           activebackground="#059669", activeforeground="white",
           command=activar).pack(side=LEFT, fill=X, expand=True, ipady=12, padx=(0, 5))

    Button(frame_btn, text="Continuar Offline", font=("Arial", 12),
           bg=COR_CARD, fg=COR_TEXTO, bd=0, cursor="hand2",
           activebackground="#334155", activeforeground="white",
           command=continuar_offline).pack(side=LEFT, fill=X, expand=True, ipady=12, padx=(5, 0))

    entry_chave.bind("<Return>", lambda e: activar())

    janela.mainloop()
    return resultado["activado"]


if __name__ == "__main__":
    mostrar_wizard_activacao()
