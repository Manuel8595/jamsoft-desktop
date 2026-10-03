from tkinter import *
from tkinter import messagebox, ttk
from database import (listar_utilizadores, criar_utilizador, atualizar_utilizador,
                       alterar_senha, eliminar_utilizador, registar_auditoria)

COR_FUNDO = "#f0fdf4"
COR_PRIMARIA = "#16a34a"
COR_SECUNDARIA = "#22c55e"
COR_TEXTO = "#14532d"
COR_PERIGO = "#dc2626"
COR_CARD = "#ffffff"
COR_ADMIN = "#374151"

# ============================================================
# PERFIS - JAM Soft
# ============================================================
# admin         - Acesso total
# gerente       - Autoriza fechos, faz depositos, gere operacao
# farmaceutico  - Opera o PDV, turnos, vendas
# auditor       - Somente leitura, painel de auditoria
# ============================================================

PERFIS = ["admin", "gerente", "farmaceutico", "auditor"]

DESCRICAO_PERFIS = {
    "admin": "Acesso total ao sistema",
    "gerente": "Autoriza fechos, faz depositos bancarios",
    "farmaceutico": "Opera PDV, turnos, vendas",
    "auditor": "Somente leitura (painel de auditoria)",
}


def abrir_utilizadores(utilizador_logado):
    """Abre o painel de gestao de utilizadores."""
    
    # Verificar permissao
    if utilizador_logado["perfil"] != "admin":
        messagebox.showerror("Sem permissao", "Apenas administradores podem acessar este painel.")
        return
    
    janela = Toplevel()
    janela.title("JAM Soft — Gestao de Utilizadores")
    janela.geometry("900x600")
    janela.configure(bg=COR_FUNDO)
    
    # Header
    header = Frame(janela, bg=COR_ADMIN, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="👥 Gestao de Utilizadores", font=("Arial", 18, "bold"),
          bg=COR_ADMIN, fg="white").pack(pady=20)
    
    # Tabela
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=15, pady=15)
    
    colunas = ("ID", "Nome", "Username", "Perfil", "Estado", "Criado em", "Ultimo login")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=120)
    tree.column("ID", width=50)
    tree.pack(fill=BOTH, expand=True)
    
    def carregar_utilizadores():
        for i in tree.get_children():
            tree.delete(i)
        for u in listar_utilizadores():
            uid, nome, username, perfil, ativo, criado, ultimo = u
            estado = "✅ Ativo" if ativo else "❌ Inativo"
            tree.insert("", END, values=(uid, nome, username, perfil.upper(), estado,
                                          criado or "-", ultimo or "Nunca"))
    
    carregar_utilizadores()
    
    # ===== JANELA DE NOVO UTILIZADOR =====
    def janela_novo():
        j = Toplevel(janela)
        j.title("Novo Utilizador")
        j.geometry("480x580")
        j.configure(bg=COR_FUNDO)
        
        Label(j, text="➕ Novo Utilizador", font=("Arial", 16, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=15)
        
        frame = Frame(j, bg=COR_FUNDO)
        frame.pack(pady=10, padx=30, fill=X)
        
        Label(frame, text="Nome completo:", font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
        entry_nome = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
        entry_nome.pack(fill=X, ipady=6)
        
        Label(frame, text="Username:", font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
        entry_user = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
        entry_user.pack(fill=X, ipady=6)
        
        Label(frame, text="Palavra-passe:", font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
        entry_senha = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID, show="●")
        entry_senha.pack(fill=X, ipady=6)
        
        Label(frame, text="Perfil:", font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
        perfil_var = StringVar(value="farmaceutico")
        combo = ttk.Combobox(frame, textvariable=perfil_var, values=PERFIS, state="readonly",
                              font=("Arial", 12))
        combo.pack(fill=X, ipady=4)
        
        # Descricao do perfil
        desc_var = StringVar(value=DESCRICAO_PERFIS.get("farmaceutico", ""))
        Label(frame, textvariable=desc_var, font=("Arial", 9, "italic"),
              bg=COR_FUNDO, fg="#6b7280").pack(anchor=W, pady=(3, 0))
        
        def atualizar_desc(event=None):
            desc_var.set(DESCRICAO_PERFIS.get(perfil_var.get(), ""))
        
        combo.bind('<<ComboboxSelected>>', atualizar_desc)
        
        def salvar_novo():
            nome = entry_nome.get().strip()
            username = entry_user.get().strip()
            senha = entry_senha.get()
            perfil = perfil_var.get()
            
            if not nome or not username or not senha:
                messagebox.showwarning("Aviso", "Preencha todos os campos!")
                return
            
            if len(senha) < 6:
                messagebox.showwarning("Aviso", "A palavra-passe deve ter pelo menos 6 caracteres.")
                return
            
            if criar_utilizador(nome, username, senha, perfil):
                registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                    "NOVO UTILIZADOR", f"Criou '{username}' como {perfil}")
                messagebox.showinfo("Sucesso", f"Utilizador '{username}' criado!")
                j.destroy()
                carregar_utilizadores()
            else:
                messagebox.showerror("Erro", f"O username '{username}' já existe.")
        
        Button(j, text="💾 Criar Utilizador", font=("Arial", 12, "bold"),
               bg=COR_PRIMARIA, fg="white", bd=0, cursor="hand2",
               command=salvar_novo).pack(pady=20, ipadx=20, ipady=8)
    
    # ===== JANELA DE EDITAR UTILIZADOR =====
    def janela_editar():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um utilizador na lista.")
            return
        
        valores = tree.item(sel[0])["values"]
        uid = valores[0]
        nome_atual = valores[1]
        username_atual = valores[2]
        perfil_atual = valores[3].lower()
        ativo_atual = 1 if "Ativo" in valores[4] else 0
        
        j = Toplevel(janela)
        j.title("Editar Utilizador")
        j.geometry("480x520")
        j.configure(bg=COR_FUNDO)
        
        Label(j, text=f"✏️ Editar: {username_atual}", font=("Arial", 16, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=15)
        
        frame = Frame(j, bg=COR_FUNDO)
        frame.pack(pady=10, padx=30, fill=X)
        
        Label(frame, text="Nome completo:", font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(5, 3))
        entry_nome = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
        entry_nome.insert(0, nome_atual)
        entry_nome.pack(fill=X, ipady=6)
        
        Label(frame, text="Perfil:", font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
        perfil_var = StringVar(value=perfil_atual)
        combo = ttk.Combobox(frame, textvariable=perfil_var, values=PERFIS, state="readonly",
                             font=("Arial", 12))
        combo.pack(fill=X, ipady=4)
        
        # Descricao do perfil
        desc_var = StringVar(value=DESCRICAO_PERFIS.get(perfil_atual, ""))
        Label(frame, textvariable=desc_var, font=("Arial", 9, "italic"),
              bg=COR_FUNDO, fg="#6b7280").pack(anchor=W, pady=(3, 0))
        
        def atualizar_desc(event=None):
            desc_var.set(DESCRICAO_PERFIS.get(perfil_var.get(), ""))
        
        combo.bind('<<ComboboxSelected>>', atualizar_desc)
        
        ativo_var = IntVar(value=ativo_atual)
        Checkbutton(frame, text="Utilizador ativo", variable=ativo_var,
                    bg=COR_FUNDO, fg=COR_TEXTO, font=("Arial", 11),
                    selectcolor=COR_FUNDO, activebackground=COR_FUNDO).pack(anchor=W, pady=10)
        
        def salvar_edicao():
            nome = entry_nome.get().strip()
            perfil = perfil_var.get()
            ativo = ativo_var.get()
            
            if not nome:
                messagebox.showwarning("Aviso", "O nome não pode ficar vazio.")
                return
            
            atualizar_utilizador(uid, nome, perfil, ativo)
            registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                "EDITAR UTILIZADOR", f"Editou '{username_atual}'")
            messagebox.showinfo("Sucesso", "Utilizador atualizado!")
            j.destroy()
            carregar_utilizadores()
        
        Button(j, text="💾 Guardar Alterações", font=("Arial", 12, "bold"),
               bg=COR_PRIMARIA, fg="white", bd=0, cursor="hand2",
               command=salvar_edicao).pack(pady=20, ipadx=20, ipady=8)
    
    # ===== JANELA DE ALTERAR SENHA =====
    def janela_senha():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um utilizador na lista.")
            return
        
        valores = tree.item(sel[0])["values"]
        uid = valores[0]
        username = valores[2]
        
        j = Toplevel(janela)
        j.title("Alterar Palavra-passe")
        j.geometry("400x300")
        j.configure(bg=COR_FUNDO)
        
        Label(j, text=f"🔑 Nova senha para: {username}", font=("Arial", 14, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=20)
        
        frame = Frame(j, bg=COR_FUNDO)
        frame.pack(padx=30, fill=X)
        
        Label(frame, text="Nova palavra-passe:", font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
        entry_senha = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID, show="●")
        entry_senha.pack(fill=X, ipady=6)
        
        Label(frame, text="Confirmar palavra-passe:", font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
        entry_conf = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID, show="●")
        entry_conf.pack(fill=X, ipady=6)
        
        def alterar():
            s1 = entry_senha.get()
            s2 = entry_conf.get()
            
            if not s1 or not s2:
                messagebox.showwarning("Aviso", "Preencha ambas as senhas.")
                return
            if s1 != s2:
                messagebox.showwarning("Aviso", "As senhas não coincidem.")
                return
            if len(s1) < 6:
                messagebox.showwarning("Aviso", "A senha deve ter pelo menos 6 caracteres.")
                return
            
            alterar_senha(uid, s1)
            registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                "ALTERAR SENHA", f"Alterou senha de '{username}'")
            messagebox.showinfo("Sucesso", "Palavra-passe alterada!")
            j.destroy()
        
        Button(j, text="💾 Alterar", font=("Arial", 12, "bold"),
               bg=COR_PRIMARIA, fg="white", bd=0, cursor="hand2",
               command=alterar).pack(pady=20, ipadx=20, ipady=8)
    
    # ===== ELIMINAR =====
    def eliminar():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um utilizador na lista.")
            return
        
        valores = tree.item(sel[0])["values"]
        uid = valores[0]
        username = valores[2]
        
        if uid == utilizador_logado["id"]:
            messagebox.showerror("Erro", "Não pode eliminar o seu próprio utilizador.")
            return
        
        if messagebox.askyesno("Confirmar", f"Eliminar '{username}' permanentemente?"):
            eliminar_utilizador(uid)
            registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                "ELIMINAR UTILIZADOR", f"Removeu '{username}'")
            messagebox.showinfo("Sucesso", "Utilizador eliminado.")
            carregar_utilizadores()
    
    # ===== BARRA DE BOTÕES =====
    frame_botoes = Frame(janela, bg=COR_FUNDO)
    frame_botoes.pack(pady=10)
    
    estilo = {"font": ("Arial", 11, "bold"), "bd": 0, "cursor": "hand2",
              "fg": "white", "width": 18, "height": 2}
    
    Button(frame_botoes, text="➕ Novo", bg=COR_PRIMARIA, command=janela_novo, **estilo).grid(row=0, column=0, padx=4)
    Button(frame_botoes, text="✏️ Editar", bg="#0891b2", command=janela_editar, **estilo).grid(row=0, column=1, padx=4)
    Button(frame_botoes, text="🔑 Alterar Senha", bg="#7c3aed", command=janela_senha, **estilo).grid(row=0, column=2, padx=4)
    Button(frame_botoes, text="🗑️ Eliminar", bg=COR_PERIGO, command=eliminar, **estilo).grid(row=0, column=3, padx=4)