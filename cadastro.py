from tkinter import *
from tkinter import messagebox, ttk
from database import (inserir_produto_completo, adicionar_lote, listar_produtos,
                       listar_fornecedores, listar_categorias, registar_auditoria)
from datetime import datetime

COR_FUNDO = "#f0fdf4"
COR_PRIMARIA = "#16a34a"
COR_TEXTO = "#14532d"
COR_CARD = "#ffffff"
COR_PERIGO = "#dc2626"


def abrir_cadastro(utilizador_logado=None):
    janela = Toplevel()
    janela.title("JAM Soft — Cadastrar Produto")
    janela.geometry("700x780")
    janela.configure(bg=COR_FUNDO)
    janela.resizable(False, False)

    # Cabeçalho
    header = Frame(janela, bg=COR_PRIMARIA, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="➕ Cadastrar Novo Produto", font=("Arial", 18, "bold"),
          bg=COR_PRIMARIA, fg="white").pack(pady=20)

    # ===== DADOS DO PRODUTO =====
    Label(janela, text="📦 Dados do Produto", font=("Arial", 13, "bold"),
          bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=(15, 5))

    card = Frame(janela, bg=COR_CARD, bd=0, highlightthickness=1, highlightbackground="#d1fae5")
    card.pack(padx=20, pady=5, fill=X)

    frame = Frame(card, bg=COR_CARD)
    frame.pack(padx=20, pady=15, fill=X)

    # Grid de 2 colunas
    def campo_grid(label, linha, coluna, width=28):
        Label(frame, text=label, font=("Arial", 10, "bold"), bg=COR_CARD, fg=COR_TEXTO).grid(
            row=linha, column=coluna*2, sticky=W, padx=(0, 8), pady=6)
        e = Entry(frame, font=("Arial", 11), width=width, bd=1, relief=SOLID)
        e.grid(row=linha, column=coluna*2+1, padx=(0, 15), pady=6)
        return e

    entry_nome = campo_grid("Nome do Produto: *", 0, 0, 28)
    entry_codigo = campo_grid("Código de Barras: *", 0, 1, 28)
    entry_principio = campo_grid("Princípio Ativo:", 1, 0, 28)
    entry_laboratorio = campo_grid("Laboratório:", 1, 1, 28)
    entry_preco_custo = campo_grid("Preço Custo (Kz):", 2, 0, 28)
    entry_preco_venda = campo_grid("Preço Venda (Kz): *", 2, 1, 28)
    entry_estoque_min = campo_grid("Estoque Mínimo:", 3, 0, 28)

    # Estoque mínimo com valor padrão
    entry_estoque_min.insert(0, "5")

    # === FOCO INICIAL NO CÓDIGO DE BARRAS ===
    # Assim o leitor USB escreve logo no campo certo
    entry_codigo.focus()

    # === ENTER NAVEGA ENTRE CAMPOS ===
    entry_codigo.bind('<Return>', lambda e: entry_nome.focus())
    entry_nome.bind('<Return>', lambda e: entry_principio.focus())
    entry_principio.bind('<Return>', lambda e: entry_laboratorio.focus())
    entry_laboratorio.bind('<Return>', lambda e: entry_preco_custo.focus())
    entry_preco_custo.bind('<Return>', lambda e: entry_preco_venda.focus())
    entry_preco_venda.bind('<Return>', lambda e: entry_estoque_min.focus())

    # ===== FORNECEDOR E CATEGORIA =====
    Label(frame, text="Fornecedor:", font=("Arial", 10, "bold"), bg=COR_CARD, fg=COR_TEXTO).grid(
        row=4, column=0, sticky=W, padx=(0, 8), pady=6)
    fornecedor_var = StringVar()
    combo_forn = ttk.Combobox(frame, textvariable=fornecedor_var, state="readonly",
                                font=("Arial", 10), width=26)
    combo_forn.grid(row=4, column=1, padx=(0, 15), pady=6)

    Label(frame, text="Categoria:", font=("Arial", 10, "bold"), bg=COR_CARD, fg=COR_TEXTO).grid(
        row=4, column=2, sticky=W, padx=(0, 8), pady=6)
    categoria_var = StringVar()
    combo_cat = ttk.Combobox(frame, textvariable=categoria_var, state="readonly",
                               font=("Arial", 10), width=26)
    combo_cat.grid(row=4, column=3, padx=(0, 15), pady=6)

    # Carregar fornecedores e categorias
    fornecedores = listar_fornecedores()
    categorias = listar_categorias()

    lista_forn = ["(Sem fornecedor)"] + [f"{f[0]} - {f[1]}" for f in fornecedores]
    lista_cat = ["(Sem categoria)"] + [f"{c[0]} - {c[1]}" for c in categorias]

    combo_forn["values"] = lista_forn
    combo_cat["values"] = lista_cat
    combo_forn.current(0)
    combo_cat.current(0)

    # Checkbox IVA
    isento_var = IntVar(value=0)
    check_frame = Frame(card, bg=COR_CARD)
    check_frame.pack(padx=20, pady=(0, 15), fill=X)
    Checkbutton(check_frame, text="Medicamento legalmente isento de IVA", variable=isento_var,
                bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 10, "bold"),
                selectcolor=COR_CARD, activebackground=COR_CARD).pack(anchor=W)
    Label(check_frame, text="Assinale apenas para medicamentos destinados exclusivamente a fins terapêuticos ou profilácticos. Os outros produtos ficam sujeitos ao IVA aplicável.",
          font=("Arial", 8, "italic"), bg=COR_CARD, fg="#6b7280").pack(anchor=W)

    # ===== LOTE INICIAL =====
    Label(janela, text="📅 Lote Inicial (opcional)", font=("Arial", 13, "bold"),
          bg=COR_FUNDO, fg=COR_PRIMARIA).pack(pady=(15, 5))

    card_lote = Frame(janela, bg=COR_CARD, bd=0, highlightthickness=1, highlightbackground="#d1fae5")
    card_lote.pack(padx=20, pady=5, fill=X)

    frame_lote = Frame(card_lote, bg=COR_CARD)
    frame_lote.pack(padx=20, pady=15, fill=X)

    def campo_lote(label, linha, coluna):
        Label(frame_lote, text=label, font=("Arial", 10, "bold"), bg=COR_CARD, fg=COR_TEXTO).grid(
            row=linha, column=coluna*2, sticky=W, padx=(0, 8), pady=6)
        e = Entry(frame_lote, font=("Arial", 11), width=20, bd=1, relief=SOLID)
        e.grid(row=linha, column=coluna*2+1, padx=(0, 15), pady=6)
        return e

    entry_lote_num = campo_lote("Número do Lote:", 0, 0)
    entry_validade = campo_lote("Validade (AAAA-MM-DD):", 0, 1)
    entry_qtd_lote = campo_lote("Quantidade:", 1, 0)

    entry_validade.insert(0, datetime.now().strftime("%Y-%m-%d"))

    # ===== FUNÇÕES =====
    def salvar():
        nome = entry_nome.get().strip()
        codigo = entry_codigo.get().strip()
        principio = entry_principio.get().strip()
        laboratorio = entry_laboratorio.get().strip()
        preco_custo = entry_preco_custo.get().strip() or "0"
        preco_venda = entry_preco_venda.get().strip()
        estoque_min = entry_estoque_min.get().strip() or "5"

        # 1. Campos obrigatórios
        if not nome or not codigo or not preco_venda:
            messagebox.showwarning("Aviso",
                "Preencha os campos obrigatórios:\n"
                "  • Nome do Produto\n"
                "  • Código de Barras\n"
                "  • Preço de Venda")
            if not codigo:
                entry_codigo.focus()
            elif not nome:
                entry_nome.focus()
            else:
                entry_preco_venda.focus()
            return

        # 2. Validar formato do código de barras
        if not codigo.isdigit():
            messagebox.showwarning("Código Inválido",
                f"O código de barras deve conter apenas NÚMEROS.\n\n"
                f"Código introduzido: {codigo}\n\n"
                f"Formatos aceites: EAN-13, EAN-8, UPC-A")
            entry_codigo.delete(0, END)
            entry_codigo.focus()
            return

        if len(codigo) < 8 or len(codigo) > 14:
            messagebox.showwarning("Código Inválido",
                f"O código de barras deve ter entre 8 e 14 dígitos.\n\n"
                f"Código introduzido: {codigo} ({len(codigo)} dígitos)\n\n"
                f"Formatos típicos:\n"
                f"  • EAN-13: 13 dígitos\n"
                f"  • EAN-8: 8 dígitos\n"
                f"  • UPC-A: 12 dígitos")
            entry_codigo.delete(0, END)
            entry_codigo.focus()
            return

        # 3. Verificar código duplicado
        try:
            produtos = listar_produtos()
            for p in produtos:
                if p[2] == codigo:
                    messagebox.showerror("Código Duplicado",
                        f"Este código de barras já está registado!\n\n"
                        f"Código: {codigo}\n"
                        f"Produto existente: {p[1]}\n\n"
                        f"Use o leitor para um código diferente.")
                    entry_codigo.delete(0, END)
                    entry_codigo.focus()
                    return
        except Exception as e:
            print(f"[Cadastro] Aviso na validação de duplicado: {e}")

        # 4. Gravar produto
        try:
            # Preço: aceita 5500 ou 5.500,00
            preco_custo_num = float(preco_custo.replace(".", "").replace(",", "."))
            preco_venda_num = float(preco_venda.replace(".", "").replace(",", "."))

            # Extrair IDs dos dropdowns
            forn_sel = fornecedor_var.get()
            cat_sel = categoria_var.get()
            fornecedor_id = None if forn_sel.startswith("(Sem") else int(forn_sel.split(" - ")[0])
            categoria_id = None if cat_sel.startswith("(Sem") else int(cat_sel.split(" - ")[0])

            inserir_produto_completo(nome, codigo, principio, laboratorio,
                                     preco_custo_num, preco_venda_num, int(estoque_min),
                                     isento_var.get(), fornecedor_id, categoria_id)

            # Auditoria
            if utilizador_logado:
                registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                                    "NOVO PRODUTO", f"Criou '{nome}' (cód: {codigo})")

            # Lote (se preenchido)
            num_lote = entry_lote_num.get().strip()
            validade = entry_validade.get().strip()
            qtd_lote = entry_qtd_lote.get().strip()

            if num_lote and validade and qtd_lote:
                produtos = listar_produtos()
                produto_id = None
                for p in produtos:
                    if p[2] == codigo:
                        produto_id = p[0]
                        break
                if produto_id:
                    adicionar_lote(produto_id, num_lote, validade, int(qtd_lote))

            messagebox.showinfo("✅ Sucesso", f"'{nome}' cadastrado com sucesso!")
            janela.destroy()

        except ValueError:
            messagebox.showerror("Erro", "Preço inválido. Use formato: 5500 ou 5.500,00")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")

    # Botões
    frame_botoes = Frame(janela, bg=COR_FUNDO)
    frame_botoes.pack(pady=20)

    Button(frame_botoes, text="💾 Salvar Produto", font=("Arial", 13, "bold"),
           bg=COR_PRIMARIA, fg="white", width=22, height=2, bd=0, cursor="hand2",
           command=salvar).grid(row=0, column=0, padx=5)

    Button(frame_botoes, text="❌ Cancelar", font=("Arial", 13, "bold"),
           bg=COR_PERIGO, fg="white", width=15, height=2, bd=0, cursor="hand2",
           command=janela.destroy).grid(row=0, column=1, padx=5)