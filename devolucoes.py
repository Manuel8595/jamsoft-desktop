import os
import csv
from datetime import datetime
from tkinter import *
from tkinter import messagebox, ttk, filedialog
from database import (
    listar_devolucoes, obter_devolucao, anular_devolucao,
    buscar_factura_por_id, obter_itens_factura_com_desconto,
    criar_devolucao, registar_auditoria,
    obter_produto_com_lotes, aumentar_estoque_produto,
    aumentar_lote, buscar_produto_por_id, estatisticas_devolucoes,
    listar_lotes_fefo, conectar
)
from moeda import formatar_kz

COR_FUNDO = "#fef2f2"
COR_PRIMARIA = "#dc2626"
COR_TEXTO = "#7f1d1d"
COR_PERIGO = "#991b1b"
COR_HEADER = "#b91c1c"
COR_CARD = "#ffffff"
COR_VERDE = "#16a34a"
COR_AZUL = "#0891b2"
COR_ROXO = "#7c3aed"
COR_AMARELO = "#f59e0b"


def abrir_devolucoes(utilizador_logado):
    """Abre a janela principal de devolucoes."""
    janela = Toplevel()
    janela.title("JAM Soft - Devolucoes")
    janela.geometry("1200x700")
    janela.configure(bg=COR_FUNDO)
    
    # ===== HEADER =====
    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(
        header, text="💰 Devolucoes de Dinheiro",
        font=("Arial", 18, "bold"),
        bg=COR_HEADER, fg="white"
    ).pack(pady=20)
    
    # ===== INFO =====
    info = Frame(janela, bg=COR_CARD,
                 highlightthickness=1,
                 highlightbackground="#fecaca")
    info.pack(fill=X, padx=15, pady=15)
    Label(
        info,
        text="Gerir devolucoes de produtos. Cada devolucao precisa de autorizacao do gerente/admin.",
        font=("Arial", 10, "italic"),
        bg=COR_CARD, fg=COR_TEXTO
    ).pack(padx=15, pady=10)
    
    # ===== FILTROS =====
    frame_filtros = Frame(janela, bg=COR_FUNDO)
    frame_filtros.pack(fill=X, padx=15, pady=(0, 10))
    
    Label(frame_filtros, text="Pesquisar:",
          font=("Arial", 10, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(side=LEFT, padx=5)
    
    var_pesquisa = StringVar()
    entry_pesquisa = Entry(frame_filtros, textvariable=var_pesquisa,
                            font=("Arial", 11), width=30)
    entry_pesquisa.pack(side=LEFT, padx=5)
    
    Label(frame_filtros, text="  Estado:",
          font=("Arial", 10, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(side=LEFT, padx=5)
    
    var_estado = StringVar(value="TODAS")
    combo_estado = ttk.Combobox(frame_filtros, textvariable=var_estado,
                                  state="readonly", font=("Arial", 10), width=15)
    combo_estado["values"] = ["TODAS", "REGISTADA", "ANULADA"]
    combo_estado.pack(side=LEFT, padx=5)
    
    Label(frame_filtros, text="  Periodo:",
          font=("Arial", 10, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(side=LEFT, padx=5)
    
    var_periodo = StringVar(value="TODAS")
    combo_periodo = ttk.Combobox(frame_filtros, textvariable=var_periodo,
                                   state="readonly", font=("Arial", 10), width=15)
    combo_periodo["values"] = ["TODAS", "HOJE", "ULTIMOS 7 DIAS", "ESTE MES"]
    combo_periodo.pack(side=LEFT, padx=5)
    
    # ===== TABELA =====
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=15, pady=10)
    
    colunas = ("ID", "Referencia", "Data", "Hora", "Factura",
               "Produto", "Qtd", "Valor", "Motivo",
               "Autorizado por", "Utilizador", "Estado")
    
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=15)
    
    larguras = {
        "ID": 40, "Referencia": 110, "Data": 90, "Hora": 60,
        "Factura": 100, "Produto": 180, "Qtd": 50, "Valor": 90,
        "Motivo": 150, "Autorizado por": 110, "Utilizador": 100, "Estado": 80
    }
    
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=larguras.get(col, 100))
    
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    tree.tag_configure("anulada", background="#fee2e2", foreground="#991b1b")
    tree.tag_configure("par", background="#f8fafc")
    tree.tag_configure("impar", background="#ffffff")
    
    # ===== RODAPE =====
    frame_rodape = Frame(janela, bg=COR_FUNDO)
    frame_rodape.pack(fill=X, padx=15, pady=5)
    
    label_total = Label(
        frame_rodape, text="Total devolvido: Kz 0,00",
        font=("Arial", 12, "bold"),
        bg=COR_FUNDO, fg=COR_PERIGO
    )
    label_total.pack(side=LEFT, padx=5)
    
    # ===== FUNCOES =====
    def carregar_devolucoes():
        """Carrega a lista de devolucoes na tree."""
        for i in tree.get_children():
            tree.delete(i)
        
        try:
            devolucoes = listar_devolucoes(500)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar: {e}")
            return
        
        total_geral = 0
        termo = var_pesquisa.get().strip().lower()
        estado_filtro = var_estado.get()
        periodo = var_periodo.get()
        
        hoje = datetime.now().strftime("%Y-%m-%d")
        agora = datetime.now()
        
        linha = 0
        for d in devolucoes:
            did, ref, data, hora, factura, produto, qtd, valor, motivo, \
                autorizado, utilizador, estado = d
            
            if estado_filtro != "TODAS" and estado != estado_filtro:
                continue
            
            if periodo == "HOJE" and data != hoje:
                continue
            elif periodo == "ULTIMOS 7 DIAS":
                try:
                    dt = datetime.strptime(data, "%Y-%m-%d")
                    if (agora - dt).days > 7:
                        continue
                except Exception:
                    pass
            elif periodo == "ESTE MES":
                mes_atual = agora.strftime("%Y-%m")
                if not data.startswith(mes_atual):
                    continue
            
            if termo:
                texto = f"{ref} {factura} {produto} {motivo} {utilizador} {autorizado}".lower()
                if termo not in texto:
                    continue
            
            tag_estado = "anulada" if estado == "ANULADA" else ("par" if linha % 2 == 0 else "impar")
            tree.insert("", END, values=(
                did, ref, data, hora, factura or "-",
                produto, qtd, formatar_kz(valor), motivo,
                autorizado, utilizador or "-", estado
            ), tags=(tag_estado,))
            
            linha += 1
            
            if estado != "ANULADA":
                total_geral += valor or 0
        
        label_total.config(text=f"Total devolvido: {formatar_kz(total_geral)}")
    
    def ver_detalhes():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma devolucao.")
            return
        
        did = tree.item(sel[0])["values"][0]
        dev = obter_devolucao(did)
        
        if not dev:
            messagebox.showerror("Erro", "Devolucao nao encontrada.")
            return
        
        msg = (
            f"REFERENCIA: {dev[1]}\n"
            f"{'='*40}\n\n"
            f"Data: {dev[2]} {dev[3]}\n"
            f"Factura original: {dev[5] or '-'}\n\n"
            f"PRODUTO:\n"
            f"  Nome: {dev[7]}\n"
            f"  Quantidade: {dev[8]}\n"
            f"  Valor unitario: {formatar_kz(dev[9])}\n"
            f"  Valor total: {formatar_kz(dev[10])}\n\n"
            f"MOTIVO:\n  {dev[11]}\n\n"
            f"AUTORIZADO POR: {dev[12]}\n"
            f"UTILIZADOR: {dev[15] or '-'}\n\n"
            f"Estado: {dev[16]}\n"
        )
        
        messagebox.showinfo(f"Detalhes - {dev[1]}", msg)
    
    def anular():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma devolucao.")
            return
        
        valores = tree.item(sel[0])["values"]
        did = valores[0]
        ref = valores[1]
        estado = valores[11]
        
        if estado == "ANULADA":
            messagebox.showinfo("Info", "Esta devolucao ja esta anulada.")
            return
        
        if utilizador_logado["perfil"] not in ("admin", "gerente"):
            messagebox.showerror("Erro", "So admin/gerente pode anular.")
            return
        
        if not messagebox.askyesno(
            "Confirmar",
            f"Anular a devolucao {ref}?\n\n"
            "O stock NAO sera revertido automaticamente.\n"
            "Use esta opcao apenas para corrigir erros de registo."
        ):
            return
        
        try:
            anular_devolucao(did, utilizador_logado["nome"],
                             utilizador_logado["id"])
            registar_auditoria(
                utilizador_logado["id"], utilizador_logado["nome"],
                "ANULAR DEVOLUCAO", f"{ref} (ID {did})"
            )
            messagebox.showinfo("OK", f"Devolucao {ref} anulada.")
            carregar_devolucoes()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao anular: {e}")
    
    def exportar_csv():
        """Exporta lista actual para CSV."""
        try:
            ficheiro = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV", "*.csv")],
                initialfile=f"devolucoes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            )
            if not ficheiro:
                return
            
            with open(ficheiro, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["ID", "Referencia", "Data", "Hora", "Factura",
                                  "Produto", "Qtd", "Valor", "Motivo",
                                  "Autorizado por", "Utilizador", "Estado"])
                
                for item_id in tree.get_children():
                    valores = tree.item(item_id)["values"]
                    writer.writerow(valores)
            
            messagebox.showinfo("OK", f"CSV exportado:\n{ficheiro}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {e}")
    
    def ver_estatisticas():
        """Mostra estatisticas do mes actual."""
        try:
            stats = estatisticas_devolucoes()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")
            return
        
        msg = (
            f"ESTATISTICAS DO MES {stats['mes']}\n"
            f"{'='*40}\n\n"
            f"Total devolvido: {stats['total_n']} devolucoes\n"
            f"Valor: {formatar_kz(stats['total_valor'])}\n\n"
            f"Anuladas: {stats['anuladas_n']}\n"
            f"Valor anulado: {formatar_kz(stats['anuladas_valor'])}\n\n"
            f"TOP MOTIVOS:\n"
        )
        
        for motivo, qtd, valor in stats["por_motivo"]:
            msg += f"  {motivo[:40]}: {qtd}x — {formatar_kz(valor)}\n"
        
        messagebox.showinfo("Estatisticas", msg)
    
    def nova_devolucao():
        abrir_nova_devolucao(utilizador_logado, ao_gravar=carregar_devolucoes)
    
    # ===== BOTOES =====
    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=10)
    
    estilo = {"font": ("Arial", 11, "bold"), "width": 20, "height": 2,
              "bd": 0, "cursor": "hand2", "fg": "white"}
    
    Button(frame_btn, text="➕ Nova Devolucao", bg=COR_VERDE,
           command=nova_devolucao, **estilo).grid(row=0, column=0, padx=5, pady=5)
    Button(frame_btn, text="🔍 Ver Detalhes", bg=COR_AZUL,
           command=ver_detalhes, **estilo).grid(row=0, column=1, padx=5, pady=5)
    Button(frame_btn, text="❌ Anular", bg=COR_ROXO,
           command=anular, **estilo).grid(row=0, column=2, padx=5, pady=5)
    Button(frame_btn, text="📊 Estatisticas", bg=COR_AMARELO,
           command=ver_estatisticas, **estilo).grid(row=0, column=3, padx=5, pady=5)
    Button(frame_btn, text="📥 Exportar CSV", bg="#4b5563",
           command=exportar_csv, **estilo).grid(row=0, column=4, padx=5, pady=5)
    Button(frame_btn, text="🔄 Atualizar", bg="#0891b2",
           command=carregar_devolucoes, **estilo).grid(row=1, column=1, padx=5, pady=5)
    
    entry_pesquisa.bind("<KeyRelease>", lambda e: carregar_devolucoes())
    combo_estado.bind("<<ComboboxSelected>>", lambda e: carregar_devolucoes())
    combo_periodo.bind("<<ComboboxSelected>>", lambda e: carregar_devolucoes())
    
    carregar_devolucoes()


# ============================================================
# ============ NOVA DEVOLUCAO ================================
# ============================================================

def abrir_nova_devolucao(utilizador_logado, ao_gravar=None):
    """Abre a janela de nova devolucao."""
    janela = Toplevel()
    janela.title("Nova Devolucao")
    janela.geometry("900x800")
    janela.configure(bg=COR_FUNDO)
    janela.transient()
    janela.grab_set()
    
    # ===== HEADER =====
    header = Frame(janela, bg=COR_HEADER, height=60)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(
        header, text="💰 Nova Devolucao de Dinheiro",
        font=("Arial", 16, "bold"),
        bg=COR_HEADER, fg="white"
    ).pack(pady=15)
    
    # ===== CORPO =====
    frame_corpo = Frame(janela, bg=COR_FUNDO)
    frame_corpo.pack(fill=BOTH, expand=True, padx=15, pady=10)
    
    # SECCAO 1 — FACTURA
    frame_fact = LabelFrame(
        frame_corpo, text=" 1. Factura Original ",
        font=("Arial", 11, "bold"),
        bg=COR_CARD, fg=COR_PERIGO,
        padx=10, pady=10
    )
    frame_fact.pack(fill=X, pady=5)
    
    frame_proc = Frame(frame_fact, bg=COR_CARD)
    frame_proc.pack(fill=X, pady=5)
    
    Label(frame_proc, text="Nº da factura:",
          font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=5)
    
    var_factura = StringVar()
    entry_factura = Entry(frame_proc, textvariable=var_factura,
                           font=("Arial", 11), width=25)
    entry_factura.pack(side=LEFT, padx=5)
    entry_factura.focus_set()
    
    label_info_factura = Label(
        frame_proc, text="",
        font=("Arial", 10),
        bg=COR_CARD, fg=COR_TEXTO
    )
    label_info_factura.pack(side=LEFT, padx=15)
    
    factura_selecionada = {"id": None, "numero": None, "itens": []}
    
    # SECCAO 2 — ITENS
    frame_itens = LabelFrame(
        frame_corpo, text=" 2. Itens a Devolver ",
        font=("Arial", 11, "bold"),
        bg=COR_CARD, fg=COR_PERIGO,
        padx=10, pady=10
    )
    frame_itens.pack(fill=BOTH, expand=True, pady=5)
    
    colunas = ("sel", "produto", "qtd_vendida", "preco", "qtd_devolver", "subtotal")
    tree_itens = ttk.Treeview(frame_itens, columns=colunas, show="headings", height=8)
    
    tree_itens.heading("sel", text="✓")
    tree_itens.heading("produto", text="Produto")
    tree_itens.heading("qtd_vendida", text="Qtd Vendida")
    tree_itens.heading("preco", text="Preço Unit.")
    tree_itens.heading("qtd_devolver", text="Qtd a Devolver")
    tree_itens.heading("subtotal", text="Subtotal")
    
    tree_itens.column("sel", width=40, anchor=CENTER)
    tree_itens.column("produto", width=300)
    tree_itens.column("qtd_vendida", width=100, anchor=CENTER)
    tree_itens.column("preco", width=120, anchor=E)
    tree_itens.column("qtd_devolver", width=120, anchor=CENTER)
    tree_itens.column("subtotal", width=120, anchor=E)
    
    tree_itens.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb_itens = Scrollbar(frame_itens, orient="vertical", command=tree_itens.yview)
    sb_itens.pack(side=RIGHT, fill=Y)
    tree_itens.configure(yscrollcommand=sb_itens.set)
    
    itens_dict = {}
    
    # SECCAO 3 — MOTIVO
    frame_motivo = LabelFrame(
        frame_corpo, text=" 3. Motivo da Devolução ",
        font=("Arial", 11, "bold"),
        bg=COR_CARD, fg=COR_PERIGO,
        padx=10, pady=10
    )
    frame_motivo.pack(fill=X, pady=5)
    
    var_motivo = StringVar()
    entry_motivo = Entry(frame_motivo, textvariable=var_motivo,
                          font=("Arial", 11))
    entry_motivo.pack(fill=X, padx=5, pady=5)
    
    Label(frame_motivo,
          text="Ex: Cliente devolveu por engano, produto com defeito, etc.",
          font=("Arial", 9, "italic"),
          bg=COR_CARD, fg="#6b7280").pack(anchor=W, padx=5)
    
    # SECCAO 4 — AUTORIZACAO
    frame_auth = LabelFrame(
        frame_corpo, text=" 4. Autorização (Gerente/Admin) ",
        font=("Arial", 11, "bold"),
        bg=COR_CARD, fg=COR_PERIGO,
        padx=10, pady=10
    )
    frame_auth.pack(fill=X, pady=5)
    
    frame_auth_row = Frame(frame_auth, bg=COR_CARD)
    frame_auth_row.pack(fill=X, pady=5)
    
    Label(frame_auth_row, text="Username:",
          font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=5)
    
    var_auth_user = StringVar()
    entry_auth_user = Entry(frame_auth_row, textvariable=var_auth_user,
                             font=("Arial", 11), width=20)
    entry_auth_user.pack(side=LEFT, padx=5)
    
    Label(frame_auth_row, text="Senha:",
          font=("Arial", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=(20, 5))
    
    var_auth_pass = StringVar()
    entry_auth_pass = Entry(frame_auth_row, textvariable=var_auth_pass,
                             font=("Arial", 11), width=20, show="*")
    entry_auth_pass.pack(side=LEFT, padx=5)
    
    # RODAPE
    frame_rodape = Frame(janela, bg=COR_FUNDO)
    frame_rodape.pack(fill=X, padx=15, pady=10)
    
    label_total = Label(
        frame_rodape, text="Total a devolver: Kz 0,00",
        font=("Arial", 14, "bold"),
        bg=COR_FUNDO, fg=COR_PERIGO
    )
    label_total.pack(side=LEFT, padx=5)
    
    # ============================================================
    # ==== FUNCOES ===============================================
    # ============================================================
    
    def calcular_total():
        total = 0
        for iid in itens_dict:
            if itens_dict[iid]["selecionado"]:
                total += itens_dict[iid]["subtotal"]
        label_total.config(text=f"Total a devolver: {formatar_kz(total)}")
    
    def toggle_selecao(event):
        iid = tree_itens.identify_row(event.y)
        col = tree_itens.identify_column(event.x)
        
        if not iid:
            return
        
        if col == "#1":
            dados = itens_dict.get(iid)
            if not dados:
                return
            
            dados["selecionado"] = not dados["selecionado"]
            
            if dados["selecionado"]:
                dados["qtd_devolver"] = dados["qtd_vendida"]
                dados["subtotal"] = dados["qtd_vendida"] * dados["preco"]
            else:
                dados["qtd_devolver"] = 0
                dados["subtotal"] = 0
            
            atualizar_linha(iid)
            calcular_total()
    
    def atualizar_linha(iid):
        dados = itens_dict[iid]
        
        check = "☑" if dados["selecionado"] else "☐"
        qtd_str = str(dados["qtd_devolver"]) if dados["selecionado"] else "-"
        sub_str = formatar_kz(dados["subtotal"]) if dados["selecionado"] else "-"
        
        tree_itens.item(iid, values=(
            check,
            dados["produto"],
            dados["qtd_vendida"],
            formatar_kz(dados["preco"]),
            qtd_str,
            sub_str
        ))
    
    def editar_qtd(event):
        iid = tree_itens.identify_row(event.y)
        col = tree_itens.identify_column(event.x)
        
        if not iid or col != "#5":
            return
        
        dados = itens_dict.get(iid)
        if not dados or not dados["selecionado"]:
            return
        
        from tkinter import simpledialog
        nova = simpledialog.askinteger(
            "Quantidade a devolver",
            f"Produto: {dados['produto']}\n"
            f"Qtd vendida: {dados['qtd_vendida']}\n\n"
            "Quantidade a devolver:",
            initialvalue=dados["qtd_devolver"],
            minvalue=1,
            maxvalue=dados["qtd_vendida"],
            parent=janela
        )
        
        if nova:
            dados["qtd_devolver"] = nova
            dados["subtotal"] = nova * dados["preco"]
            atualizar_linha(iid)
            calcular_total()
    
    def procurar_factura(event=None):
        numero = var_factura.get().strip()
        if not numero:
            messagebox.showwarning("Aviso", "Digite o numero da factura.")
            return
        
        for iid in tree_itens.get_children():
            tree_itens.delete(iid)
        itens_dict.clear()
        
        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, numero, cliente_nome, total, estado, data
                FROM facturas
                WHERE numero = ? AND (tipo = 'FT' OR tipo IS NULL OR tipo = '')
            """, (numero,))
            row = cur.fetchone()
            conn.close()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao procurar: {e}")
            return
        
        if not row:
            label_info_factura.config(
                text=f"❌ Factura '{numero}' nao encontrada.",
                fg=COR_PERIGO
            )
            return
        
        fid, num, cli, total, estado, data = row
        
        if estado == "ANULADA":
            label_info_factura.config(
                text=f"❌ Factura ANULADA — nao pode ser devolvida.",
                fg=COR_PERIGO
            )
            return
        
        factura_selecionada["id"] = fid
        factura_selecionada["numero"] = num
        
        label_info_factura.config(
            text=f"✅ Cliente: {cli or 'Consumidor Final'} | Total: {formatar_kz(total)}",
            fg=COR_VERDE
        )
        
        try:
            from database import obter_itens_factura_com_desconto
            itens = obter_itens_factura_com_desconto(fid)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar itens: {e}")
            return
        
        for item in itens:
            desc, qtd, preco, isento, taxa, viva, sub, dperc, dval = item
            
            preco_final = preco
            if dperc and dperc > 0:
                preco_final = preco * (1 - dperc / 100)
            
            iid = tree_itens.insert("", END, values=(
                "☐", desc, qtd, formatar_kz(preco_final), "-", "-"
            ))
            
            itens_dict[iid] = {
                "produto": desc,
                "qtd_vendida": qtd,
                "preco": preco_final,
                "qtd_devolver": 0,
                "subtotal": 0,
                "selecionado": False,
            }
    
    def gravar_devolucao():
        if not factura_selecionada["id"]:
            messagebox.showwarning("Aviso", "Procure uma factura primeiro.")
            return
        
        selecionados = [
            (iid, dados) for iid, dados in itens_dict.items()
            if dados["selecionado"] and dados["qtd_devolver"] > 0
        ]
        
        if not selecionados:
            messagebox.showwarning("Aviso", "Selecione pelo menos um item.")
            return
        
        motivo = var_motivo.get().strip()
        if not motivo:
            messagebox.showwarning("Aviso", "Digite o motivo da devolucao.")
            return
        
        auth_user = var_auth_user.get().strip()
        auth_pass = var_auth_pass.get().strip()
        
        if not auth_user or not auth_pass:
            messagebox.showwarning("Aviso", "Preencha as credenciais de autorizacao.")
            return
        
        try:
            from database import autenticar
            ok, auth_info = autenticar(auth_user, auth_pass)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao autenticar: {e}")
            return
        
        if not ok or auth_info is None:
            messagebox.showerror("Erro", "Credenciais invalidas.")
            var_auth_pass.set("")
            return
        
        perfil = auth_info.get("perfil", "")
        if perfil not in ("admin", "gerente"):
            messagebox.showerror(
                "Erro",
                f"O utilizador '{auth_user}' nao tem permissao para autorizar.\n"
                "Apenas admin ou gerente."
            )
            return
        
        total_geral = sum(d["subtotal"] for _, d in selecionados)
        
        if not messagebox.askyesno(
            "Confirmar Devolucao",
            f"Confirma a devolucao de {len(selecionados)} item(s)?\n\n"
            f"Total a devolver: {formatar_kz(total_geral)}\n"
            f"Autorizado por: {auth_info['nome']} ({perfil})\n\n"
            "O stock sera reposto."
        ):
            return
        
        erros = []
        sucessos = 0
        
        for iid, dados in selecionados:
            try:
                # Tentar encontrar o produto_id
                produto_id = 0
                lote_id = None
                
                try:
                    conn = conectar()
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT produto_id FROM itens_factura
                        WHERE factura_id = ? AND descricao = ?
                        LIMIT 1
                    """, (factura_selecionada["id"], dados["produto"]))
                    r = cur.fetchone()
                    conn.close()
                    
                    if r and r[0]:
                        produto_id = r[0]
                        
                        # Encontrar o primeiro lote com stock
                        lotes = listar_lotes_fefo(produto_id)
                        if lotes:
                            lote_id = lotes[0][0]
                except Exception as e_pid:
                    print(f"[Devolucao] Aviso ao buscar produto_id: {e_pid}")
                
                dev_id = criar_devolucao(
                    venda_original_id=None,
                    factura_original=factura_selecionada["numero"],
                    produto_id=produto_id,
                    produto_nome=dados["produto"],
                    quantidade=dados["qtd_devolver"],
                    valor_unitario=dados["preco"],
                    motivo=motivo,
                    autorizado_por=auth_info["nome"],
                    autorizado_por_id=auth_info["id"],
                    utilizador_id=utilizador_logado["id"],
                    utilizador_nome=utilizador_logado["nome"],
                    lote_id=lote_id,
                )
                
                # ===== REPOR STOCK =====
                if produto_id > 0:
                    try:
                        aumentar_estoque_produto(produto_id, dados["qtd_devolver"])
                        
                        if lote_id:
                            aumentar_lote(lote_id, dados["qtd_devolver"])
                        
                        registar_auditoria(
                            utilizador_logado["id"], utilizador_logado["nome"],
                            "DEVOLUCAO STOCK",
                            f"Dev {dev_id} | {dados['produto']} +{dados['qtd_devolver']} unidades"
                        )
                    except Exception as e_stock:
                        print(f"[Devolucao] Erro stock: {e_stock}")
                
                registar_auditoria(
                    utilizador_logado["id"], utilizador_logado["nome"],
                    "DEVOLUCAO",
                    f"Dev {dev_id} | {dados['produto']} x{dados['qtd_devolver']} | "
                    f"Total {formatar_kz(dados['subtotal'])} | "
                    f"Auth: {auth_info['nome']} | Motivo: {motivo}"
                )
                
                sucessos += 1
            except Exception as e:
                erros.append(f"{dados['produto']}: {e}")
        
        if erros:
            messagebox.showerror(
                "Erro parcial",
                f"{sucessos} devolucoes gravadas.\n\n"
                f"Erros:\n" + "\n".join(erros)
            )
        else:
            messagebox.showinfo(
                "OK",
                f"✅ {sucessos} devolucao(oes) registada(s) com sucesso!\n\n"
                f"Total: {formatar_kz(total_geral)}\n"
                f"Autorizado por: {auth_info['nome']}\n"
                f"Stock reposto."
            )
        
        if ao_gravar:
            ao_gravar()
        
        janela.destroy()
    
    # ===== BOTOES =====
    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=10)
    
    estilo_btn = {"font": ("Arial", 11, "bold"), "width": 18, "height": 2,
                  "bd": 0, "cursor": "hand2", "fg": "white"}
    
    Button(frame_btn, text="🔍 Procurar Factura", bg=COR_AZUL,
           command=procurar_factura,
           **estilo_btn).grid(row=0, column=0, padx=5)
    
    Button(frame_btn, text="💾 Gravar Devolucao", bg=COR_VERDE,
           command=gravar_devolucao,
           **estilo_btn).grid(row=0, column=1, padx=5)
    
    Button(frame_btn, text="❌ Cancelar", bg=COR_PRIMARIA,
           command=janela.destroy,
           **estilo_btn).grid(row=0, column=2, padx=5)
    
    entry_factura.bind("<Return>", procurar_factura)
    tree_itens.bind("<Button-1>", toggle_selecao)
    tree_itens.bind("<Double-Button-1>", editar_qtd)
    
    entry_factura.focus_set()