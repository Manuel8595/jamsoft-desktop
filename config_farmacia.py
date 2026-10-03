import os
from tkinter import *
from tkinter import messagebox, ttk
from database import conectar, registar_auditoria
from seguranca import verificar_acesso
from identidade import (configurar_farmacia, configurar_terminal,
                          obter_farmacia_codigo, obter_farmacia_nome,
                          obter_terminal_codigo, esta_configurada,
                          obter_config, gerar_uuid)
from datetime import datetime

COR_FUNDO = "#eff6ff"
COR_PRIMARIA = "#2563eb"
COR_TEXTO = "#1e3a8a"
COR_PERIGO = "#dc2626"
COR_HEADER = "#1e40af"
COR_CARD = "#ffffff"
COR_VERDE = "#16a34a"
COR_CINZA = "#64748b"


def abrir_config_farmacia(utilizador_logado):
    """Abre o ecra de Configuracao da Farmacia."""
    
    if not verificar_acesso(utilizador_logado, "config.empresa", "Configuracao da Farmacia"):
        return
    
    janela = Toplevel()
    janela.title("JAM Soft - Configuração da Farmácia")
    janela.geometry("700x800")
    janela.configure(bg=COR_FUNDO)
    janela.transient()
    janela.grab_set()
    
    # Header
    header = Frame(janela, bg=COR_HEADER, height=80)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="🏢 Configuração da Farmácia",
          font=("Arial", 18, "bold"), bg=COR_HEADER, fg="white").pack(pady=(15, 0))
    Label(header, text="Identificação única para a rede multi-farmácia",
          font=("Arial", 10, "italic"), bg=COR_HEADER, fg="#bfdbfe").pack()
    
    # Estado atual
    estado_card = Frame(janela, bg=COR_CARD, highlightthickness=2,
                          highlightbackground=COR_VERDE if esta_configurada() else COR_PERIGO)
    estado_card.pack(fill=X, padx=20, pady=15)
    
    if esta_configurada():
        Label(estado_card, text="✅ FARMÁCIA CONFIGURADA",
              font=("Arial", 12, "bold"), bg=COR_CARD, fg=COR_VERDE).pack(pady=(10, 5))
        Label(estado_card, text=f"Código: {obter_farmacia_codigo()}  |  "
                                f"Nome: {obter_farmacia_nome()}  |  "
                                f"Terminal: {obter_terminal_codigo()}",
              font=("Arial", 10), bg=COR_CARD, fg=COR_TEXTO).pack(pady=(0, 10))
    else:
        Label(estado_card, text="⚠️ FARMÁCIA NÃO CONFIGURADA",
              font=("Arial", 12, "bold"), bg=COR_CARD, fg=COR_PERIGO).pack(pady=(10, 5))
        Label(estado_card, text="Preenche os dados abaixo e grava.",
              font=("Arial", 10, "italic"), bg=COR_CARD, fg=COR_CINZA).pack(pady=(0, 10))
    
    # Scroll
    main_frame = Frame(janela, bg=COR_FUNDO)
    main_frame.pack(fill=BOTH, expand=True)
    
    canvas = Canvas(main_frame, bg=COR_FUNDO, highlightthickness=0)
    scrollbar = Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable = Frame(canvas, bg=COR_FUNDO)
    
    scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable, anchor="nw", width=660)
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # --- Dados da farmacia ---
    Label(scrollable, text="📋 Dados da Farmácia",
          font=("Arial", 13, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, padx=20, pady=(15, 5))
    
    card1 = Frame(scrollable, bg=COR_CARD, highlightthickness=1, highlightbackground="#bfdbfe")
    card1.pack(fill=X, padx=20, pady=5)
    
    frame1 = Frame(card1, bg=COR_CARD)
    frame1.pack(padx=20, pady=15, fill=X)
    
    def campo(parent, label, valor_inicial="", obrigatorio=False):
        txt = label + (" *" if obrigatorio else "")
        Label(parent, text=txt, font=("Arial", 10, "bold"),
              bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
        e = Entry(parent, font=("Arial", 12), bd=1, relief=SOLID)
        e.insert(0, valor_inicial or "")
        e.pack(fill=X, ipady=5)
        return e
    
    # Codigo
    Label(frame1, text="Código da Farmácia: *", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
    entry_codigo = Entry(frame1, font=("Arial", 12), bd=1, relief=SOLID)
    entry_codigo.insert(0, obter_farmacia_codigo() if esta_configurada() else "")
    entry_codigo.pack(fill=X, ipady=5)
    Label(frame1, text="Ex: FARM-LDA-001 (único em todas as farmácias)",
          font=("Arial", 9, "italic"), bg=COR_CARD, fg=COR_CINZA).pack(anchor=W)
    
    entry_nome = campo(frame1, "Nome da Farmácia", obter_farmacia_nome() if esta_configurada() else "", True)
    entry_nif = campo(frame1, "NIF")
    entry_endereco = campo(frame1, "Endereço")
    entry_telefone = campo(frame1, "Telefone")
    entry_email = campo(frame1, "Email")
    entry_responsavel = campo(frame1, "Responsável / Gerente")
    
    Label(frame1, text="Notas:", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
    text_notas = Text(frame1, height=3, font=("Arial", 11), bd=1, relief=SOLID)
    text_notas.pack(fill=X)
    
    # --- Terminal ---
    Label(scrollable, text="💻 Identificação deste Terminal",
          font=("Arial", 13, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, padx=20, pady=(20, 5))
    
    card2 = Frame(scrollable, bg=COR_CARD, highlightthickness=1, highlightbackground="#bfdbfe")
    card2.pack(fill=X, padx=20, pady=5)
    
    frame2 = Frame(card2, bg=COR_CARD)
    frame2.pack(padx=20, pady=15, fill=X)
    
    Label(frame2, text="Código deste Terminal: *", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
    entry_terminal = Entry(frame2, font=("Arial", 12), bd=1, relief=SOLID)
    entry_terminal.insert(0, obter_terminal_codigo())
    entry_terminal.pack(fill=X, ipady=5)
    Label(frame2, text="Ex: TERM-01, TERM-02 (cada PC tem um código diferente)",
          font=("Arial", 9, "italic"), bg=COR_CARD, fg=COR_CINZA).pack(anchor=W)
    
    Label(frame2, text="Nome do Terminal:", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
    entry_terminal_nome = Entry(frame2, font=("Arial", 12), bd=1, relief=SOLID)
    entry_terminal_nome.insert(0, f"Terminal {obter_terminal_codigo()}")
    entry_terminal_nome.pack(fill=X, ipady=5)
    
    # --- Botoes ---
    def gravar():
        codigo = entry_codigo.get().strip().upper()
        nome = entry_nome.get().strip()
        nif = entry_nif.get().strip()
        endereco = entry_endereco.get().strip()
        telefone = entry_telefone.get().strip()
        email = entry_email.get().strip()
        responsavel = entry_responsavel.get().strip()
        notas = text_notas.get("1.0", END).strip()
        
        term_codigo = entry_terminal.get().strip().upper()
        term_nome = entry_terminal_nome.get().strip()
        
        # Validacoes
        if not codigo:
            messagebox.showwarning("Aviso", "O código da farmácia é obrigatório.")
            return
        
        if not nome:
            messagebox.showwarning("Aviso", "O nome da farmácia é obrigatório.")
            return
        
        if not term_codigo:
            messagebox.showwarning("Aviso", "O código do terminal é obrigatório.")
            return
        
        try:
            # Configurar farmacia
            fid = configurar_farmacia(codigo, nome, nif, endereco, telefone,
                                        email, responsavel, notas)
            
            # Configurar terminal
            configurar_terminal(term_codigo, term_nome)
            
            # Registar na nuvem (Supabase)
            sucesso_nuvem, msg_nuvem = _registar_farmacia_na_nuvem(
                codigo, nome, nif, endereco, telefone,
                email, responsavel, notas
            )
            
            # Auditoria
            registar_auditoria(
                utilizador_logado["id"], utilizador_logado["nome"],
                "CONFIG FARMACIA",
                f"{codigo} | {nome} | Terminal: {term_codigo}"
            )
            
            msg_extra = ""
            if sucesso_nuvem:
                msg_extra = f"\n\n☁️ {msg_nuvem}"
            else:
                msg_extra = f"\n\n⚠️ Nuvem: {msg_nuvem}\n(Vai tentar novamente no próximo sync)"
            
            messagebox.showinfo("Sucesso",
                f"Farmácia configurada!\n\n"
                f"Código: {codigo}\n"
                f"Nome: {nome}\n"
                f"Terminal: {term_codigo}\n"
                f"Esta configuração é única em toda a rede."
                f"{msg_extra}")
            
            janela.destroy()
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gravar: {e}")
    
    frame_btns = Frame(janela, bg=COR_FUNDO, height=70)
    frame_btns.pack(fill=X, side=BOTTOM, pady=5)
    frame_btns.pack_propagate(False)
    
    Button(frame_btns, text="💾 Gravar Configuração",
           font=("Arial", 12, "bold"), bg=COR_PRIMARIA, fg="white",
           width=25, height=2, bd=0, cursor="hand2",
           command=gravar).pack(side=LEFT, padx=20, pady=10)
    
    Button(frame_btns, text="❌ Cancelar",
           font=("Arial", 11), bg=COR_CINZA, fg="white",
           width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).pack(side=LEFT, pady=10)

# ============================================================
# ============ REGISTAR FARMACIA NA NUVEM ====================
# ============================================================

def _registar_farmacia_na_nuvem(codigo, nome, nif, endereco,
                                   telefone, email, responsavel, notas):
    """
    Regista a farmacia no Supabase (tabela `farmacias`).
    Retorna (sucesso, mensagem).
    """
    try:
        import requests
        from config_cloud import (SUPABASE_URL,
                                    SUPABASE_PUBLISHABLE_KEY,
                                    CLOUD_ACCESS_ENABLED,
                                    SYNC_TIMEOUT)
        if not CLOUD_ACCESS_ENABLED:
            return False, "A ligação à nuvem está temporariamente desactivada por segurança."
        from datetime import datetime
        from identidade import gerar_uuid

        headers = {
            "apikey": SUPABASE_PUBLISHABLE_KEY,
            "Authorization": f"Bearer {SUPABASE_PUBLISHABLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        }

        # Verificar se ja existe (pelo codigo)
        url_get = f"{SUPABASE_URL}/rest/v1/farmacias?codigo=eq.{codigo}&select=id,uuid"
        r = requests.get(url_get, headers=headers, timeout=SYNC_TIMEOUT)

        if r.status_code == 200:
            existentes = r.json()
            if existentes:
                # Ja existe - so actualizar
                farm_uuid = existentes[0].get("uuid") or gerar_uuid()
                payload = {
                    "uuid": farm_uuid,
                    "codigo": codigo,
                    "nome": nome,
                    "nif": nif,
                    "endereco": endereco,
                    "telefone": telefone,
                    "email": email,
                    "responsavel": responsavel,
                    "notas": notas,
                    "activo": True,
                }
                url_upd = f"{SUPABASE_URL}/rest/v1/farmacias?codigo=eq.{codigo}"
                r2 = requests.patch(url_upd, headers=headers, json=payload,
                                      timeout=SYNC_TIMEOUT)
                if 200 <= r2.status_code < 300:
                    return True, f"Farmácia '{nome}' actualizada na nuvem."
                else:
                    return False, f"Erro a actualizar: HTTP {r2.status_code}"

        # Nao existe - criar nova
        farm_uuid = gerar_uuid()
        payload = {
            "uuid": farm_uuid,
            "codigo": codigo,
            "nome": nome,
            "nif": nif,
            "endereco": endereco,
            "telefone": telefone,
            "email": email,
            "responsavel": responsavel,
            "notas": notas,
            "activo": True,
            "criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        url_post = f"{SUPABASE_URL}/rest/v1/farmacias"
        headers_post = dict(headers)
        headers_post["Prefer"] = "return=minimal"

        r3 = requests.post(url_post, headers=headers_post, json=payload,
                             timeout=SYNC_TIMEOUT)

        if 200 <= r3.status_code < 300:
            return True, f"Farmácia '{nome}' registada na nuvem."
        elif r3.status_code == 409:
            return True, f"Farmácia '{nome}' ja existia na nuvem."
        else:
            return False, f"HTTP {r3.status_code}: {r3.text[:100]}"

    except ImportError as e:
        return False, f"Modulo em falta: {e}"
    except Exception as e:
        return False, f"Erro: {e}"
