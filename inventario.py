from tkinter import *
from tkinter import messagebox, ttk
from database import (listar_produtos, criar_inventario, adicionar_item_inventario,
                       ajustar_estoque, listar_inventarios, listar_itens_inventario,
                       registar_auditoria)
from datetime import datetime

COR_FUNDO = "#fef3c7"
COR_PRIMARIA = "#d97706"
COR_TEXTO = "#78350f"
COR_PERIGO = "#dc2626"
COR_HEADER = "#b45309"
COR_CARD = "#ffffff"


def abrir_inventario(utilizador_logado):
    """Abre o módulo de Inventário Físico."""
    
    janela = Toplevel()
    janela.title("JAM Soft - Inventário Físico")
    janela.geometry("1100x800")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Contagem de Inventário Físico", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)
    
    # Instruções
    instr = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#fde68a")
    instr.pack(fill=X, padx=15, pady=(15, 5))
    Label(instr, text="Conte fisicamente os produtos nas prateleiras e digite a quantidade real em cada linha.",
          font=("Arial", 10, "italic"), bg=COR_CARD, fg=COR_TEXTO).pack(padx=15, pady=10)
    
    # Tabela de contagem
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=15, pady=10)
    
    colunas = ("ID", "Produto", "Código", "Estoque Sistema", "Estoque Contado", "Diferença", "Justificação")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
    tree.column("ID", width=50)
    tree.column("Produto", width=250)
    tree.column("Código", width=100)
    tree.column("Estoque Sistema", width=120)
    tree.column("Estoque Contado", width=120)
    tree.column("Diferença", width=100)
    tree.column("Justificação", width=200)
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    scrollbar = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=scrollbar.set)
    
    # Carregar produtos
    produtos = listar_produtos()
    contagem = {}  # {produto_id: {"contado": qtd, "justificacao": str}}
    
    def carregar_produtos():
        for i in tree.get_children():
            tree.delete(i)
        for p in produtos:
            # p = (id, nome, codigo, preco_venda, estoque_atual, estoque_minimo, isento_iva)
            contagem[p[0]] = {"contado": p[4], "justificacao": ""}
            tree.insert("", END, values=(p[0], p[1], p[2] or "-", p[4], p[4], 0, ""),
                        tags=(f"p_{p[0]}",))
    
    carregar_produtos()
    
    # Painel de edição (embaixo)
    painel = Frame(janela, bg=COR_CARD, highlightthickness=2, highlightbackground=COR_PRIMARIA)
    painel.pack(fill=X, padx=15, pady=(0, 10))
    
    Label(painel, text="Editar produto selecionado:", font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=0, columnspan=4, pady=(10, 5))
    
    Label(painel, text="Estoque Contado:", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=1, column=0, padx=10, pady=5, sticky=E)
    entry_contado = Entry(painel, font=("Arial", 12), width=10, bd=1, relief=SOLID)
    entry_contado.grid(row=1, column=1, padx=5, pady=5)
    
    Label(painel, text="Justificação:", font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).grid(row=1, column=2, padx=10, pady=5, sticky=E)
    entry_just = Entry(painel, font=("Arial", 11), width=40, bd=1, relief=SOLID)
    entry_just.grid(row=1, column=3, padx=5, pady=5)
    
    # Total
    total_dif_var = StringVar(value="Produtos com diferença: 0")
    Label(painel, textvariable=total_dif_var, font=("Arial", 11, "bold"),
          bg=COR_CARD, fg=COR_PERIGO).grid(row=2, column=0, columnspan=4, pady=(5, 10))
    
    def selecionar_item(event=None):
        sel = tree.selection()
        if not sel:
            return
        valores = tree.item(sel[0])["values"]
        pid = valores[0]
        
        entry_contado.delete(0, END)
        entry_contado.insert(0, str(contagem[pid]["contado"]))
        entry_just.delete(0, END)
        entry_just.insert(0, contagem[pid]["justificacao"])
    
    def aplicar_contagem(event=None):
        sel = tree.selection()
        if not sel:
            return
        
        valores = tree.item(sel[0])["values"]
        pid = valores[0]
        estoque_sistema = valores[3]
        
        try:
            contado = int(entry_contado.get().strip())
            just = entry_just.get().strip()
            
            if contado < 0:
                raise ValueError("Negativo")
            
            diferenca = contado - estoque_sistema
            
            contagem[pid] = {"contado": contado, "justificacao": just}
            
            # Atualizar tabela
            tree.item(sel[0], values=(pid, valores[1], valores[2],
                                       estoque_sistema, contado, diferenca, just))
            
            # Realçar se há diferença
            if diferenca != 0:
                tree.item(sel[0], tags=("diferenca",))
                tree.tag_configure("diferenca", background="#fee2e2", foreground="#991b1b")
            else:
                tree.item(sel[0], tags=("ok",))
                tree.tag_configure("ok", background="#f0fdf4")
            
            atualizar_contador()
            
        except ValueError:
            messagebox.showwarning("Aviso", "Digite um número válido.")
    
    entry_contado.bind('<Return>', aplicar_contagem)
    entry_just.bind('<Return>', aplicar_contagem)
    tree.bind("<<TreeviewSelect>>", selecionar_item)
    
    def atualizar_contador():
        count = sum(1 for p in contagem.values() if p["justificacao"] != "" or True)
        # Conta produtos com diferença
        count = 0
        for item in tree.get_children():
            v = tree.item(item)["values"]
            if v[5] != 0:
                count += 1
        total_dif_var.set(f"Produtos com diferença: {count}")
    
    def finalizar_inventario():
        # Confirmar produtos com diferença e sem justificação
        sem_just = []
        for pid, dados in contagem.items():
            if dados["contado"] != 0 or True:
                pass
        # Verifica se há diferenças sem justificação
        for item in tree.get_children():
            v = tree.item(item)["values"]
            if v[5] != 0 and not v[6]:
                sem_just.append(v[1])
        
        if sem_just:
            msg = "Os seguintes produtos têm diferença e não têm justificação:\n\n"
            msg += "\n".join(sem_just[:10])
            if len(sem_just) > 10:
                msg += f"\n... e mais {len(sem_just)-10}"
            if not messagebox.askyesno("Atenção", msg + "\n\nDeseja continuar mesmo assim?"):
                return
        
        if not messagebox.askyesno("Confirmar", 
            "Deseja finalizar o inventário?\n\n"
            "O estoque será AJUSTADO para os valores contados.\n"
            "Esta ação fica registada em auditoria."):
            return
        
        try:
            # Contar itens com diferença
            total_dif = 0
            for item in tree.get_children():
                v = tree.item(item)["values"]
                if v[5] != 0:
                    total_dif += 1
            
            # Criar inventário
            inv_id = criar_inventario(utilizador_logado["id"], utilizador_logado["nome"],
                                        "", len(produtos), total_dif)
            
            # Adicionar itens e ajustar estoque
            for item in tree.get_children():
                v = tree.item(item)["values"]
                pid = v[0]
                estoque_sistema = v[3]
                estoque_contado = v[4]
                diferenca = v[5]
                just = v[6]
                
                if diferenca != 0:
                    adicionar_item_inventario(inv_id, pid, estoque_sistema, estoque_contado, diferenca, just)
                    ajustar_estoque(pid, estoque_contado)
            
            registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                "INVENTÁRIO", f"Inventário #{inv_id} | {len(produtos)} itens | {total_dif} diferenças")
            
            messagebox.showinfo("Inventário Finalizado",
                                f"Inventário #{inv_id} concluído!\n"
                                f"Total de produtos: {len(produtos)}\n"
                                f"Produtos com diferença: {total_dif}\n\n"
                                f"O estoque foi ajustado.")
            janela.destroy()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao finalizar inventário: {e}")
    
    # Botões
    frame_botoes = Frame(janela, bg=COR_FUNDO)
    frame_botoes.pack(pady=10)
    
    Button(frame_botoes, text="Aplicar Contagem", font=("Arial", 11, "bold"),
           bg="#0891b2", fg="white", width=18, height=2, bd=0, cursor="hand2",
           command=aplicar_contagem).grid(row=0, column=0, padx=5)
    
    Button(frame_botoes, text="Histórico Inventários", font=("Arial", 11, "bold"),
           bg="#7c3aed", fg="white", width=18, height=2, bd=0, cursor="hand2",
           command=lambda: abrir_historico_inventarios()).grid(row=0, column=1, padx=5)
    
    Button(frame_botoes, text="Finalizar Inventário", font=("Arial", 12, "bold"),
           bg=COR_PRIMARIA, fg="white", width=22, height=2, bd=0, cursor="hand2",
           command=finalizar_inventario).grid(row=0, column=2, padx=5)
    
    Button(frame_botoes, text="Cancelar", font=("Arial", 11, "bold"),
           bg=COR_PERIGO, fg="white", width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).grid(row=0, column=3, padx=5)


def abrir_historico_inventarios():
    janela = Toplevel()
    janela.title("Histórico de Inventários")
    janela.geometry("1000x650")
    janela.configure(bg=COR_FUNDO)
    
    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Histórico de Inventários", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)
    
    frame = Frame(janela, bg=COR_FUNDO)
    frame.pack(fill=BOTH, expand=True, padx=15, pady=15)
    
    colunas = ("ID", "Data", "Utilizador", "Total Itens", "Diferenças")
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=10)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=170)
    tree.pack(fill=BOTH, expand=True)
    
    frame_itens = Frame(janela, bg=COR_FUNDO)
    frame_itens.pack(fill=BOTH, expand=True, padx=15, pady=(0, 15))
    
    Label(frame_itens, text="Itens do inventário selecionado:",
          font=("Arial", 11, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(anchor=W, pady=(0, 5))
    
    colunas2 = ("Produto", "Sistema", "Contado", "Diferença", "Justificação")
    tree2 = ttk.Treeview(frame_itens, columns=colunas2, show="headings", height=8)
    for col in colunas2:
        tree2.heading(col, text=col)
        tree2.column(col, width=180)
    tree2.pack(fill=BOTH, expand=True)
    
    def carregar():
        for i in tree.get_children():
            tree.delete(i)
        for inv in listar_inventarios(50):
            tree.insert("", END, values=(inv[0], inv[1], inv[2], inv[3], inv[4]))
    
    def mostrar_itens(event=None):
        sel = tree.selection()
        if not sel:
            return
        inv_id = tree.item(sel[0])["values"][0]
        
        for i in tree2.get_children():
            tree2.delete(i)
        
        for item in listar_itens_inventario(inv_id):
            tree2.insert("", END, values=(item[1], item[2], item[3], item[4], item[5] or "-"))
    
    tree.bind("<<TreeviewSelect>>", mostrar_itens)
    carregar()