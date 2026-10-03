from tkinter import *
from tkinter import messagebox, ttk
from database import (listar_categorias, criar_categoria, atualizar_categoria,
                       eliminar_categoria, buscar_categoria_por_id, registar_auditoria)

COR_FUNDO = "#fff7ed"
COR_PRIMARIA = "#ea580c"
COR_TEXTO = "#7c2d12"
COR_PERIGO = "#dc2626"
COR_HEADER = "#c2410c"


def abrir_categorias(utilizador_logado):
    janela = Toplevel()
    janela.title("JAM Soft — Gestão de Categorias")
    janela.geometry("800x600")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="🗂️ Gestão de Categorias", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)
    
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=15, pady=15)
    
    colunas = ("ID", "Nome", "Descrição")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
    tree.column("ID", width=50)
    tree.column("Nome", width=250)
    tree.column("Descrição", width=450)
    tree.pack(fill=BOTH, expand=True)
    
    def carregar():
        for i in tree.get_children():
            tree.delete(i)
        for c in listar_categorias():
            tree.insert("", END, values=(c[0], c[1], c[2] or "-"))
    
    carregar()
    
    def abrir_form(cat_id=None):
        if cat_id:
            dados = buscar_categoria_por_id(cat_id)
            titulo = f"✏️ Editar: {dados[1]}"
        else:
            dados = None
            titulo = "➕ Nova Categoria"
        
        j = Toplevel(janela)
        j.title(titulo)
        j.geometry("450x350")
        j.configure(bg=COR_FUNDO)
        
        Label(j, text=titulo, font=("Arial", 16, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=15)
        
        frame = Frame(j, bg=COR_FUNDO)
        frame.pack(pady=10, padx=30, fill=X)
        
        Label(frame, text="Nome da categoria: *", font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(8, 3))
        entry_nome = Entry(frame, font=("Arial", 12), bd=1, relief=SOLID)
        if dados:
            entry_nome.insert(0, dados[1])
        entry_nome.pack(fill=X, ipady=6)
        
        Label(frame, text="Descrição:", font=("Arial", 11, "bold"),
              bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(10, 3))
        text_desc = Text(frame, height=4, font=("Arial", 11), bd=1, relief=SOLID)
        if dados:
            text_desc.insert("1.0", dados[2] or "")
        text_desc.pack(fill=X)
        
        def salvar():
            nome = entry_nome.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "O nome é obrigatório!")
                return
            desc = text_desc.get("1.0", END).strip()
            
            if cat_id:
                atualizar_categoria(cat_id, nome, desc)
                registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                    "EDITAR CATEGORIA", f"Editou '{nome}'")
                messagebox.showinfo("Sucesso", "Categoria atualizada!")
            else:
                if criar_categoria(nome, desc):
                    registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                        "NOVA CATEGORIA", f"Criou '{nome}'")
                    messagebox.showinfo("Sucesso", "Categoria criada!")
                else:
                    messagebox.showerror("Erro", "Esta categoria já existe.")
                    return
            j.destroy()
            carregar()
        
        Button(j, text="💾 Guardar", font=("Arial", 12, "bold"),
               bg=COR_PRIMARIA, fg="white", bd=0, cursor="hand2",
               command=salvar).pack(pady=20, ipadx=30, ipady=8)
    
    def editar():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma categoria.")
            return
        cid = tree.item(sel[0])["values"][0]
        abrir_form(cid)
    
    def eliminar():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma categoria.")
            return
        cid = tree.item(sel[0])["values"][0]
        nome = tree.item(sel[0])["values"][1]
        
        if messagebox.askyesno("Confirmar", f"Eliminar '{nome}'?"):
            try:
                eliminar_categoria(cid)
                registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                    "ELIMINAR CATEGORIA", f"Removeu '{nome}'")
                messagebox.showinfo("Sucesso", "Categoria eliminada.")
                carregar()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro: {e}\n(Pode ter produtos associados)")
    
    frame_botoes = Frame(janela, bg=COR_FUNDO)
    frame_botoes.pack(pady=10)
    
    estilo = {"font": ("Arial", 11, "bold"), "bd": 0, "cursor": "hand2",
              "fg": "white", "width": 18, "height": 2}
    
    Button(frame_botoes, text="➕ Nova", bg=COR_PRIMARIA, command=lambda: abrir_form(), **estilo).grid(row=0, column=0, padx=4)
    Button(frame_botoes, text="✏️ Editar", bg="#0891b2", command=editar, **estilo).grid(row=0, column=1, padx=4)
    Button(frame_botoes, text="🗑️ Eliminar", bg=COR_PERIGO, command=eliminar, **estilo).grid(row=0, column=2, padx=4)