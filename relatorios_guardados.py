# ============================================================
# ============ RELATORIOS ARQUIVADOS =========================
# ============================================================
# 
# Ecra para:
#   - Ver todos os relatorios arquivados
#   - Filtrar por tipo e data
#   - Reimprimir (abre o PDF guardado)
#   - Eliminar (so admin)
#   - Abrir pasta de relatorios
# 
# ============================================================

import os
from datetime import datetime
from tkinter import *
from tkinter import messagebox, ttk

from database import (listar_relatorios_guardados, obter_relatorio,
                       registar_auditoria, conectar)
from seguranca import verificar_acesso


COR_FUNDO = "#0f172a"
COR_CARD = "#1e293b"
COR_CARD_HOVER = "#334155"
COR_PRIMARIA = "#7c3aed"
COR_DOURADO = "#fbbf24"
COR_VERDE = "#10b981"
COR_VERMELHO = "#ef4444"
COR_ALERTA = "#f97316"
COR_AZUL = "#0ea5e9"
COR_TEXTO = "#f8fafc"
COR_TEXTO_SEC = "#94a3b8"
COR_BORDA = "#334155"

PASTA_RELATORIOS = "relatorios"


# ============================================================
# ============ TIPOS DE RELATORIO ============================
# ============================================================

TIPOS_RELATORIO = [
    "TODOS",
    "RELATORIO_Z",
    "VENDAS",
    "VENDAS_MES",
    "VENDAS_SEMANA",
    "INVENTARIO",
    "PERDAS",
    "FECHO_CAIXA",
]


# ============================================================
# ============ GARANTIR PASTA ================================
# ============================================================

def garantir_pasta():
    if not os.path.exists(PASTA_RELATORIOS):
        os.makedirs(PASTA_RELATORIOS)


# ============================================================
# ============ ECRAN PRINCIPAL ===============================
# ============================================================

def abrir_relatorios_guardados(utilizador_logado, parent=None):
    """Abre o ecra de relatorios arquivados."""
    
    # Verificar permissao
    if not verificar_acesso(utilizador_logado, "relatorios.ver",
                              "Relatorios Arquivados"):
        return
    
    if parent is None:
        parent = Toplevel()
        parent.withdraw()
    
    janela = Toplevel(parent)
    janela.title("Relatorios Arquivados")
    janela.geometry("1100x700")
    janela.configure(bg=COR_FUNDO)
    
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 1100) // 2
    y = (janela.winfo_screenheight() - 700) // 2
    janela.geometry(f"1100x700+{x}+{y}")
    
    # Header
    header = Frame(janela, bg=COR_PRIMARIA, height=90)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Relatorios Arquivados",
          font=("Segoe UI", 20, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=(15, 0))
    Label(header, text=f"Utilizador: {utilizador_logado['nome']}  |  "
                        f"Pasta: {os.path.abspath(PASTA_RELATORIOS)}",
          font=("Segoe UI", 10, "italic"),
          bg=COR_PRIMARIA, fg="#e0e7ff").pack()
    
    # ===== FILTROS =====
    frame_filtros = Frame(janela, bg=COR_CARD, highlightthickness=1,
                            highlightbackground=COR_BORDA)
    frame_filtros.pack(fill=X, padx=20, pady=(15, 5))
    
    inner_filtros = Frame(frame_filtros, bg=COR_CARD)
    inner_filtros.pack(padx=20, pady=12, fill=X)
    
    # Filtro por tipo
    Label(inner_filtros, text="Tipo:",
          font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=(0, 8))
    
    tipo_var = StringVar(value="TODOS")
    combo_tipo = ttk.Combobox(inner_filtros, textvariable=tipo_var,
                                values=TIPOS_RELATORIO, state="readonly",
                                font=("Segoe UI", 10), width=18)
    combo_tipo.pack(side=LEFT, padx=(0, 20))
    
    # Filtro por data inicio
    Label(inner_filtros, text="De:",
          font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=(0, 8))
    
    entry_de = Entry(inner_filtros, font=("Segoe UI", 10),
                      width=12, bd=1, relief=SOLID)
    entry_de.pack(side=LEFT, padx=(0, 15), ipady=4)
    
    # Filtro por data fim
    Label(inner_filtros, text="Ate:",
          font=("Segoe UI", 10, "bold"),
          bg=COR_CARD, fg=COR_TEXTO).pack(side=LEFT, padx=(0, 8))
    
    entry_ate = Entry(inner_filtros, font=("Segoe UI", 10),
                       width=12, bd=1, relief=SOLID)
    entry_ate.pack(side=LEFT, padx=(0, 15), ipady=4)
    
    Label(inner_filtros, text="(AAAA-MM-DD)",
          font=("Segoe UI", 8, "italic"),
          bg=COR_CARD, fg=COR_TEXTO_SEC).pack(side=LEFT, padx=(0, 15))
    
    # ===== TABELA =====
    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=20, pady=10)
    
    colunas = ("ID", "Tipo", "Referencia", "Data Geracao", "Gerado por",
               "Ficheiro")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=15)
    
    tree.heading("ID", text="ID")
    tree.heading("Tipo", text="Tipo")
    tree.heading("Referencia", text="Referencia")
    tree.heading("Data Geracao", text="Data Geracao")
    tree.heading("Gerado por", text="Gerado por")
    tree.heading("Ficheiro", text="Ficheiro")
    
    tree.column("ID", width=50)
    tree.column("Tipo", width=140)
    tree.column("Referencia", width=150)
    tree.column("Data Geracao", width=160)
    tree.column("Gerado por", width=180)
    tree.column("Ficheiro", width=350)
    
    tree.pack(fill=BOTH, expand=True, side=LEFT)
    
    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)
    
    # Label de contagem
    count_var = StringVar(value="Total: 0 relatorios")
    Label(janela, textvariable=count_var,
          font=("Segoe UI", 10, "bold"),
          bg=COR_FUNDO, fg=COR_DOURADO).pack(pady=(0, 5))
    
    # ===== FUNCAO DE CARREGAR =====
    def carregar(filtro_tipo=None, filtro_de=None, filtro_ate=None):
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            # Buscar da BD
            tipo_db = None if (not filtro_tipo or filtro_tipo == "TODOS") else filtro_tipo
            relatorios = listar_relatorios_guardados(200, tipo_db)
            
            total_exibidos = 0
            
            for r in relatorios:
                rel_id, tipo, referencia, data_ger, gerado_por, caminho = r
                
                # Filtro de datas
                if filtro_de and data_ger:
                    if data_ger[:10] < filtro_de:
                        continue
                if filtro_ate and data_ger:
                    if data_ger[:10] > filtro_ate:
                        continue
                
                # Nome do ficheiro (so o basename)
                nome_ficheiro = "-"
                if caminho:
                    nome_ficheiro = os.path.basename(caminho)
                
                # Tag para cores
                tag = ""
                if tipo == "RELATORIO_Z":
                    tag = "z"
                elif tipo.startswith("VENDAS"):
                    tag = "vendas"
                elif tipo == "INVENTARIO":
                    tag = "inventario"
                elif tipo == "PERDAS":
                    tag = "perdas"
                
                tree.insert("", END, values=(
                    rel_id,
                    tipo or "-",
                    referencia or "-",
                    data_ger or "-",
                    (gerado_por or "-")[:25],
                    nome_ficheiro
                ), tags=(tag,))
                
                total_exibidos += 1
            
            count_var.set(f"Total: {total_exibidos} relatorios")
        
        except Exception as e:
            count_var.set(f"Erro ao carregar: {e}")
        
        tree.tag_configure("z", foreground=COR_DOURADO)
        tree.tag_configure("vendas", foreground=COR_VERDE)
        tree.tag_configure("inventario", foreground=COR_AZUL)
        tree.tag_configure("perdas", foreground=COR_VERMELHO)
    
    def aplicar_filtros():
        f_de = entry_de.get().strip()
        f_ate = entry_ate.get().strip()
        
        # Validar datas (se preenchidas)
        if f_de:
            try:
                datetime.strptime(f_de, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Erro", "Data 'De' invalida. Use AAAA-MM-DD.")
                return
        
        if f_ate:
            try:
                datetime.strptime(f_ate, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Erro", "Data 'Ate' invalida. Use AAAA-MM-DD.")
                return
        
        carregar(tipo_var.get(), f_de or None, f_ate or None)
    
    def limpar_filtros():
        tipo_var.set("TODOS")
        entry_de.delete(0, END)
        entry_ate.delete(0, END)
        carregar()
    
    # Bind Enter nos campos
    entry_de.bind('<Return>', lambda e: entry_ate.focus())
    entry_ate.bind('<Return>', lambda e: aplicar_filtros())
    
    # Botoes de filtro
    Button(inner_filtros, text="Filtrar",
           font=("Segoe UI", 10, "bold"),
           bg=COR_AZUL, fg="white",
           bd=0, cursor="hand2", padx=15, pady=4,
           activebackground="#0284c7",
           command=aplicar_filtros).pack(side=LEFT, padx=(0, 8))
    
    Button(inner_filtros, text="Limpar",
           font=("Segoe UI", 10),
           bg="#64748b", fg="white",
           bd=0, cursor="hand2", padx=15, pady=4,
           command=limpar_filtros).pack(side=LEFT)
    
    # ===== ACCOES =====
    def obter_selecionado():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um relatorio na lista.")
            return None
        return tree.item(sel[0])["values"]
    
    def reimprimir():
        valores = obter_selecionado()
        if not valores:
            return
        
        rel_id = valores[0]
        relatorio = obter_relatorio(rel_id)
        
        if not relatorio:
            messagebox.showerror("Erro", "Relatorio nao encontrado.")
            return
        
        caminho = relatorio[5]
        
        if not caminho or not os.path.exists(caminho):
            messagebox.showerror("Erro",
                f"O ficheiro PDF nao existe:\n\n{caminho}\n\n"
                f"Pode ter sido movido ou eliminado.")
            return
        
        try:
            os.startfile(caminho)
            
            registar_auditoria(
                utilizador_logado["id"],
                utilizador_logado["nome"],
                "REIMPRIMIR RELATORIO",
                f"ID: {rel_id} | {valores[1]} | {valores[2]} | "
                f"{os.path.basename(caminho)}"
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir o ficheiro: {e}")
    
    def eliminar():
        # Verificar permissao
        if utilizador_logado["perfil"] != "admin":
            messagebox.showerror("Sem permissao",
                "Apenas administradores podem eliminar relatorios.")
            return
        
        valores = obter_selecionado()
        if not valores:
            return
        
        rel_id = valores[0]
        relatorio = obter_relatorio(rel_id)
        
        if not relatorio:
            return
        
        caminho = relatorio[5]
        nome = os.path.basename(caminho) if caminho else "-"
        
        if not messagebox.askyesno("Confirmar Eliminacao",
            f"Eliminar o relatorio?\n\n"
            f"ID: {rel_id}\n"
            f"Tipo: {valores[1]}\n"
            f"Referencia: {valores[2]}\n"
            f"Ficheiro: {nome}\n\n"
            f"AVISO: Esta accao nao pode ser revertida."):
            return
        
        try:
            # Apagar ficheiro
            if caminho and os.path.exists(caminho):
                os.remove(caminho)
            
            # Apagar registo da BD
            conn = conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM relatorios_guardados WHERE id = ?", (rel_id,))
            conn.commit()
            conn.close()
            
            registar_auditoria(
                utilizador_logado["id"],
                utilizador_logado["nome"],
                "ELIMINAR RELATORIO",
                f"ID: {rel_id} | {valores[1]} | {valores[2]}"
            )
            
            messagebox.showinfo("Sucesso", "Relatorio eliminado.")
            carregar(tipo_var.get())
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao eliminar: {e}")
    
    def abrir_pasta():
        garantir_pasta()
        caminho_abs = os.path.abspath(PASTA_RELATORIOS)
        try:
            os.startfile(caminho_abs)
        except Exception:
            messagebox.showinfo("Info", f"Pasta: {caminho_abs}")
    
    # ===== BOTOES INFERIORES =====
    frame_btns = Frame(janela, bg=COR_FUNDO, height=60)
    frame_btns.pack(fill=X, side=BOTTOM)
    frame_btns.pack_propagate(False)
    
    estilo_btn = {
        "font": ("Segoe UI", 11, "bold"),
        "bd": 0, "cursor": "hand2",
        "fg": "white", "height": 2,
    }
    
    Button(frame_btns, text="Reimprimir",
           bg=COR_VERDE, width=18,
           command=reimprimir, **estilo_btn).pack(side=LEFT, padx=(20, 5), pady=8)
    
    Button(frame_btns, text="Abrir Pasta",
           bg=COR_AZUL, width=18,
           command=abrir_pasta, **estilo_btn).pack(side=LEFT, padx=5, pady=8)
    
    if utilizador_logado["perfil"] == "admin":
        Button(frame_btns, text="Eliminar",
               bg=COR_VERMELHO, width=18,
               command=eliminar, **estilo_btn).pack(side=LEFT, padx=5, pady=8)
    
    Button(frame_btns, text="Actualizar",
           bg="#64748b", width=18,
           command=lambda: carregar(tipo_var.get()),
           **estilo_btn).pack(side=LEFT, padx=5, pady=8)
    
    Button(frame_btns, text="Fechar",
           bg="#374151", width=15,
           command=janela.destroy,
           **estilo_btn).pack(side=RIGHT, padx=(5, 20), pady=8)
    
    # Carregar inicial
    carregar()


# ============================================================
# ============ TESTE DIRETO ==================================
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  TESTE - relatorios_guardados.py")
    print("="*60)
    
    print("\n[1] Pasta de relatorios:")
    garantir_pasta()
    caminho_abs = os.path.abspath(PASTA_RELATORIOS)
    print(f"    {caminho_abs}")
    
    if os.path.exists(PASTA_RELATORIOS):
        ficheiros = [f for f in os.listdir(PASTA_RELATORIOS) if f.endswith(".pdf")]
        print(f"    {len(ficheiros)} ficheiros PDF")
        for f in ficheiros[:5]:
            print(f"      - {f}")
    else:
        print("    (pasta ainda vazia)")
    
    print("\n[2] Relatorios guardados na BD:")
    relatorios = listar_relatorios_guardados(20)
    if relatorios:
        for r in relatorios:
            print(f"    ID {r[0]} | {r[1]} | {r[2]} | {r[3]}")
    else:
        print("    (nenhum relatorio guardado ainda)")
    
    print("\n" + "="*60 + "\n")