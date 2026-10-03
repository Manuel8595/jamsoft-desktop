from tkinter import *
from tkinter import messagebox, ttk
from database import (listar_clientes, criar_cliente, atualizar_cliente,
                       eliminar_cliente, buscar_cliente_por_id, registar_auditoria)

COR_FUNDO = "#f5f3ff"
COR_PRIMARIA = "#7c3aed"
COR_TEXTO = "#3b0764"
COR_PERIGO = "#dc2626"
COR_HEADER = "#6d28d9"


def abrir_clientes(utilizador_logado):
    """Abre o painel de gestão de clientes."""
    
    janela = Toplevel()
    janela.title("JAM Soft — Gestão de Clientes")
    janela.geometry("1000x600")
    janela.configure(bg=COR_FUNDO)
    
    # Header
    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="👥 Gestão de Clientes", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)
    
    # Barra de busca
    frame_busca = Frame(janela, bg=COR_FUNDO)
    frame_busca.pack(fill=X, padx=15, pady=(15, 5))
    
    Label(frame_busca, text="🔍 Buscar:", font=("Arial", 11, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(side=LEFT, padx=5)
    
    entry_busca = Entry(frame_busca, font=("Arial", 11), width=40, bd=1, relief=SOLID)
    entry_busca.pack(side=LEFT, padx=5, ipady=5)
    
    # Tabela
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=15, pady=10)
    
    colunas = ("ID", "Nome", "NIF", "Telefone", "Email", "Data Nasc.")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.column("ID", width=50)
    tree.pack(fill=BOTH, expand=True)
    
    def carregar(busca=""):
        for i in tree.get_children():
            tree.delete(i)
        for c in listar_clientes():
            if busca.lower() in c[1].lower() or busca in (c[2] or "") or busca in (c[3] or ""):
                tree.insert("", END, values=(c[0], c[1], c[2] or "-", c[3] or "-",
                                              c[4] or "-", c[5] or "-"))
    
    entry_busca.bind('<KeyRelease>', lambda e: carregar(entry_busca.get()))
    carregar()
    
    def abrir_form(cliente_id=None):
        if cliente_id:
            dados = buscar_cliente_por_id(cliente_id)
            titulo = f"✏️ Editar: {dados[1]}"
        else:
            dados = None
            titulo = "➕ Novo Cliente"
        
        j = Toplevel(janela)
        j.title(titulo)
        j.geometry("500x700")
        j.configure(bg=COR_FUNDO)
        
        Label(j, text=titulo, font=("Arial", 16, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=15)
        
        frame = Frame(j, bg=COR_FUNDO)
        frame.pack(pady=10, padx=30, fill=X)
        
        def campo(label, valor_inicial=""):
            Label(frame, text=label, font=("Arial", 11, "bold"),
                  bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
            e = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
            e.insert(0, valor_inicial or "")
            e.pack(fill=X, ipady=6)
            return e
        
        entry_nome = campo("Nome completo: *", dados[1] if dados else "")
        entry_nif = campo("NIF:", dados[2] if dados else "")
        entry_tel = campo("Telefone:", dados[3] if dados else "")
        entry_email = campo("Email:", dados[4] if dados else "")
        entry_end = campo("Endereço:", dados[5] if dados else "")
        entry_nasc = campo("Data de Nascimento (AAAA-MM-DD):", dados[6] if dados else "")
        
        Label(frame, text="Observações:", font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
        text_obs = Text(frame, height=3, font=("Arial", 11), bd=1, relief=SOLID)
        if dados:
            text_obs.insert("1.0", dados[7] or "")
        text_obs.pack(fill=X)
        
        def salvar():
            nome = entry_nome.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "O nome é obrigatório!")
                return
            
            nif = entry_nif.get().strip()
            tel = entry_tel.get().strip()
            email = entry_email.get().strip()
            end = entry_end.get().strip()
            nasc = entry_nasc.get().strip()
            obs = text_obs.get("1.0", END).strip()
            
            if cliente_id:
                atualizar_cliente(cliente_id, nome, nif, tel, email, end, nasc, obs)
                registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                    "EDITAR CLIENTE", f"Editou '{nome}'")
                messagebox.showinfo("Sucesso", "Cliente atualizado!")
            else:
                if criar_cliente(nome, nif, tel, email, end, nasc, obs):
                    registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                        "NOVO CLIENTE", f"Criou '{nome}'")
                    messagebox.showinfo("Sucesso", "Cliente criado!")
                else:
                    messagebox.showerror("Erro", "Este NIF já está registado.")
                    return
            
            j.destroy()
            carregar()
        
        Button(j, text="💾 Guardar", font=("Arial", 12, "bold"),
               bg=COR_PRIMARIA, fg="white", bd=0, cursor="hand2",
               command=salvar).pack(pady=20, ipadx=30, ipady=8)
    
    def editar():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um cliente na lista.")
            return
        cid = tree.item(sel[0])["values"][0]
        abrir_form(cid)
    
    def eliminar():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um cliente na lista.")
            return
        
        cid = tree.item(sel[0])["values"][0]
        nome = tree.item(sel[0])["values"][1]
        
        if messagebox.askyesno("Confirmar", f"Eliminar '{nome}' permanentemente?"):
            try:
                eliminar_cliente(cid)
                registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                    "ELIMINAR CLIENTE", f"Removeu '{nome}'")
                messagebox.showinfo("Sucesso", "Cliente eliminado.")
                carregar()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro: {e}")
    
    # Barra de botões
    frame_botoes = Frame(janela, bg=COR_FUNDO)
    frame_botoes.pack(pady=10)
    
    estilo = {"font": ("Arial", 11, "bold"), "bd": 0, "cursor": "hand2",
              "fg": "white", "width": 18, "height": 2}
    
    Button(frame_botoes, text="➕ Novo", bg=COR_PRIMARIA, command=lambda: abrir_form(), **estilo).grid(row=0, column=0, padx=4)
    Button(frame_botoes, text="✏️ Editar", bg="#0891b2", command=editar, **estilo).grid(row=0, column=1, padx=4)
    Button(frame_botoes, text="🗑️ Eliminar", bg=COR_PERIGO, command=eliminar, **estilo).grid(row=0, column=2, padx=4)