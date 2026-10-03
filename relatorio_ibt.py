"""
Relatorio de Transferencia entre Filiais (IBT)
Gera PDF A4 ou Termico 80mm com 2 assinaturas.
"""

import os
from datetime import datetime

from database import conectar, obter_empresa
from moeda import formatar_kz


PASTA_RELATORIOS = "relatorios"


def garantir_pasta():
    if not os.path.exists(PASTA_RELATORIOS):
        os.makedirs(PASTA_RELATORIOS)


def gerar_pdf_ibt(trans_id, formato="A4", caminho_saida=None):
    """Gera o PDF do comprovativo IBT. Retorna (caminho, erro)."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.colors import HexColor
    except ImportError:
        return None, "ReportLab nao instalado."

    # Buscar dados da IBT
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, referencia, data_criacao, data_envio, data_recepcao,
               farmacia_origem_nome, farmacia_origem_codigo,
               farmacia_destino_nome, farmacia_destino_codigo,
               utilizador_criou_nome, autorizado_por,
               estado, total_itens, total_quantidade, valor_estimado,
               observacoes
        FROM transferencias_filiais WHERE id = ?
    """, (trans_id,))
    trans = cur.fetchone()

    if not trans:
        conn.close()
        return None, "IBT nao encontrada."

    cur.execute("""
        SELECT produto_nome, codigo_barras,
               quantidade_enviada, quantidade_recebida, diferenca,
               lote, validade, preco_custo, subtotal, justificacao
        FROM itens_transferencia WHERE transferencia_id = ?
        ORDER BY id
    """, (trans_id,))
    itens = cur.fetchall()

    cur.execute("""
        SELECT data, acao, utilizador_nome, detalhes
        FROM historico_ibt WHERE transferencia_id = ?
        ORDER BY id ASC
    """, (trans_id,))
    historico = cur.fetchall()
    conn.close()

    # Empresa
    emp = obter_empresa()
    emp_nome = emp[1] if emp else "Farmacia"
    emp_nif = emp[2] if emp else "-"
    emp_end = emp[3] if emp else "-"
    emp_tel = emp[4] if emp else "-"

    garantir_pasta()

    (tid, ref, dt_c, dt_e, dt_r, o_nome, o_cod, d_nome, d_cod,
     uc_nome, aut, estado, n_itens, qtd, valor, obs) = trans

    data_arquivo = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    sufixo = "A4" if formato == "A4" else "TERMICA"
    nome_ficheiro = f"IBT_{ref.replace('/', '_')}_{data_arquivo}_{sufixo}.pdf"

    if not caminho_saida:
        caminho_saida = os.path.join(PASTA_RELATORIOS, nome_ficheiro)

    if formato == "TERMICA":
        page_size = (80 * mm, 297 * mm)
    else:
        page_size = A4

    c = pdf_canvas.Canvas(caminho_saida, pagesize=page_size)
    largura, altura = page_size

    if formato == "A4":
        _desenhar_a4(c, largura, altura, emp_nome, emp_nif, emp_end, emp_tel,
                      trans, itens, historico, mm, HexColor)
    else:
        _desenhar_termica(c, largura, altura, emp_nome, emp_nif, emp_tel,
                            trans, itens, mm, HexColor)

    c.save()
    return caminho_saida, None


def _desenhar_a4(c, largura, altura, emp_nome, emp_nif, emp_end, emp_tel,
                  trans, itens, historico, mm, HexColor):
    """Desenha A4 - layout profissional."""

    CINZA_ESCURO = HexColor("#1e293b")
    CINZA_MEDIO = HexColor("#64748b")
    CINZA_CLARO = HexColor("#e2e8f0")
    AZUL = HexColor("#0ea5e9")
    VERDE = HexColor("#16a34a")
    DOURADO = HexColor("#d97706")
    VERMELHO = HexColor("#dc2626")

    (tid, ref, dt_c, dt_e, dt_r, o_nome, o_cod, d_nome, d_cod,
     uc_nome, aut, estado, n_itens, qtd, valor, obs) = trans

    margem = 20 * mm
    y = altura - 20 * mm

    # Cabecalho
    c.setFillColor(CINZA_ESCURO)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margem, y, emp_nome)
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.setFillColor(CINZA_MEDIO)
    c.drawString(margem, y, f"NIF: {emp_nif} | {emp_end} | Tel: {emp_tel}")

    y -= 10 * mm
    c.setStrokeColor(CINZA_ESCURO)
    c.setLineWidth(1.5)
    c.line(margem, y, largura - margem, y)

    # Titulo
    y -= 12 * mm
    c.setFillColor(AZUL)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(largura / 2, y, "TRANSFERENCIA ENTRE FILIAIS")

    y -= 7 * mm
    c.setFillColor(CINZA_ESCURO)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(largura / 2, y, f"IBT  {ref}")

    # Estado (colorido)
    y -= 7 * mm
    cor_est = {
        "RASCUNHO": CINZA_MEDIO,
        "EM_TRANSITO": DOURADO,
        "RECEBIDA_PARCIAL": DOURADO,
        "CONCLUIDA": VERDE,
        "CANCELADA": VERMELHO,
        "DIVERGENCIA": VERMELHO,
    }.get(estado, CINZA_ESCURO)
    c.setFillColor(cor_est)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura / 2, y, f"Estado: {estado}")

    y -= 15 * mm

    # Info
    c.setFont("Helvetica", 10)
    c.setFillColor(CINZA_ESCURO)
    c.drawString(margem, y, f"Origem:  {o_nome} ({o_cod})")
    y -= 6 * mm
    c.drawString(margem, y, f"Destino: {d_nome} ({d_cod})")
    y -= 6 * mm
    c.drawString(margem, y, f"Criada:  {dt_c}")
    y -= 6 * mm
    if dt_e:
        c.drawString(margem, y, f"Enviada: {dt_e}")
        y -= 6 * mm
    if dt_r:
        c.drawString(margem, y, f"Recebida: {dt_r}")
        y -= 6 * mm
    c.drawString(margem, y, f"Criada por: {uc_nome}")
    y -= 6 * mm
    if aut:
        c.drawString(margem, y, f"Autorizada por: {aut}")
        y -= 6 * mm

    y -= 5 * mm

    # Cabecalho tabela
    c.setFillColor(CINZA_CLARO)
    c.rect(margem, y - 2 * mm, largura - 2 * margem, 7 * mm, fill=1, stroke=0)
    c.setFillColor(CINZA_ESCURO)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margem + 2 * mm, y, "Produto")
    c.drawString(margem + 80 * mm, y, "Codigo")
    c.drawString(margem + 110 * mm, y, "Enviado")
    c.drawString(margem + 130 * mm, y, "Recebido")
    c.drawString(margem + 150 * mm, y, "Dif.")
    c.drawRightString(largura - margem - 2 * mm, y, "Subtotal")

    y -= 7 * mm

    # Linhas
    c.setFont("Helvetica", 8)
    for it in itens:
        (nome, cod, qtd_env, qtd_rec, dif, lote, val,
         custo, sub, just) = it

        c.setFillColor(CINZA_ESCURO)
        c.drawString(margem + 2 * mm, y, str(nome)[:38])
        c.drawString(margem + 80 * mm, y, str(cod or "-")[:20])
        c.drawString(margem + 110 * mm, y, str(qtd_env))
        c.drawString(margem + 130 * mm, y, str(qtd_rec))
        if dif and dif != 0:
            c.setFillColor(VERMELHO)
            c.drawString(margem + 150 * mm, y, str(dif))
        else:
            c.drawString(margem + 150 * mm, y, "0")
        c.setFillColor(CINZA_ESCURO)
        c.drawRightString(largura - margem - 2 * mm, y, formatar_kz(sub or 0))

        c.setStrokeColor(CINZA_CLARO)
        c.setLineWidth(0.3)
        c.line(margem, y - 2 * mm, largura - margem, y - 2 * mm)
        y -= 6 * mm

    y -= 5 * mm

    # Totais
    c.setFillColor(CINZA_ESCURO)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margem, y, f"Total itens: {n_itens}  |  Unidades: {qtd}")
    y -= 7 * mm

    c.setFillColor(VERDE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margem, y, f"VALOR ESTIMADO: {formatar_kz(valor or 0)}")

    y -= 10 * mm

    if obs:
        c.setFillColor(CINZA_MEDIO)
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(margem, y, f"Observacoes: {obs}")
        y -= 10 * mm

    # Historico (se couber)
    if historico and y > 80 * mm:
        c.setFillColor(CINZA_ESCURO)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margem, y, "Historico:")
        y -= 5 * mm
        c.setFont("Helvetica", 8)
        for h in historico:
            data, acao, user, det = h
            c.setFillColor(CINZA_MEDIO)
            hora = (data or "")[-8:] if data else ""
            c.drawString(margem + 2 * mm, y, f"{hora}  {acao}  por {user or '-'}")
            y -= 5 * mm

    # Assinaturas
    y = 50 * mm
    c.setStrokeColor(CINZA_ESCURO)
    c.setLineWidth(0.5)

    c.line(margem + 10 * mm, y, margem + 70 * mm, y)
    c.line(largura - margem - 70 * mm, y, largura - margem - 10 * mm, y)

    y -= 5 * mm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(CINZA_ESCURO)
    c.drawCentredString(margem + 40 * mm, y, "Assinatura da Origem")
    c.drawCentredString(largura - margem - 40 * mm, y, "Assinatura do Destino")

    # Rodape
    c.setFont("Helvetica-Oblique", 7)
    c.setFillColor(CINZA_MEDIO)
    c.drawCentredString(largura / 2, 15 * mm,
                          f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} - JAM Soft")
    c.drawCentredString(largura / 2, 10 * mm,
                          "Documento processado por computador")


def _desenhar_termica(c, largura, altura, emp_nome, emp_nif, emp_tel,
                        trans, itens, mm, HexColor):
    """Termico 80mm."""

    (tid, ref, dt_c, dt_e, dt_r, o_nome, o_cod, d_nome, d_cod,
     uc_nome, aut, estado, n_itens, qtd, valor, obs) = trans

    y = altura - 10 * mm

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawCentredString(largura / 2, y, emp_nome[:28])
    y -= 4 * mm
    c.setFont("Helvetica", 7)
    c.drawCentredString(largura / 2, y, f"NIF: {emp_nif}")
    y -= 5 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(largura / 2, y, "-" * 34)
    y -= 4 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(largura / 2, y, "TRANSFERENCIA IBT")
    y -= 4 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(largura / 2, y, ref)
    y -= 4 * mm
    c.setFont("Helvetica", 7)
    c.drawCentredString(largura / 2, y, f"Estado: {estado}")
    y -= 4 * mm
    c.drawCentredString(largura / 2, y, "-" * 34)
    y -= 5 * mm

    c.setFont("Helvetica", 7)
    c.drawString(3 * mm, y, f"Origem: {o_nome[:30]}")
    y -= 3.5 * mm
    c.drawString(3 * mm, y, f"Destino: {d_nome[:30]}")
    y -= 3.5 * mm
    c.drawString(3 * mm, y, f"Criada: {(dt_c or '')[:16]}")
    y -= 3.5 * mm
    if aut:
        c.drawString(3 * mm, y, f"Autoriz: {aut[:25]}")
        y -= 3.5 * mm

    c.drawCentredString(largura / 2, y, "-" * 34)
    y -= 4 * mm

    c.setFont("Helvetica-Bold", 7)
    c.drawString(3 * mm, y, "Produto")
    c.drawRightString(largura - 3 * mm, y, "Qtd")
    y -= 4 * mm

    c.setFont("Helvetica", 7)
    for it in itens:
        nome, cod, qtd_env, qtd_rec, dif, lote, val, custo, sub, just = it
        c.drawString(3 * mm, y, str(nome)[:32])
        c.drawRightString(largura - 3 * mm, y, str(qtd_env))
        y -= 3.5 * mm

    c.drawCentredString(largura / 2, y, "-" * 34)
    y -= 4 * mm

    c.setFont("Helvetica-Bold", 8)
    c.drawString(3 * mm, y, f"Total: {n_itens} itens | {qtd} un")
    y -= 5 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(largura / 2, y, formatar_kz(valor or 0))
    y -= 8 * mm

    c.setFont("Helvetica", 7)
    c.drawString(3 * mm, y, "Ass: __________________")
    y -= 3 * mm
    c.drawString(3 * mm, y, "      Origem")
    y -= 6 * mm
    c.drawString(3 * mm, y, "Ass: __________________")
    y -= 3 * mm
    c.drawString(3 * mm, y, "      Destino")

    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(largura / 2, 10 * mm,
                          f"Gerado {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawCentredString(largura / 2, 7 * mm, "JAM Soft")


def abrir_escolha_impressao_ibt(trans_id, parent=None):
    """Abre dialogo para escolher formato e imprime."""
    if parent is None:
        from tkinter import Tk
        parent = Tk()
        parent.withdraw()

    from tkinter import Toplevel, Label, Button, Frame

    resultado = {"formato": None}

    janela = Toplevel(parent)
    janela.title("Imprimir Comprovativo IBT")
    janela.geometry("500x400")
    janela.configure(bg="#0f172a")
    janela.transient(parent)
    janela.grab_set()

    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 500) // 2
    y = (janela.winfo_screenheight() - 400) // 2
    janela.geometry(f"500x400+{x}+{y}")

    header = Frame(janela, bg="#0ea5e9", height=70)
    header.pack(fill="x")
    header.pack_propagate(False)
    Label(header, text="Imprimir Comprovativo IBT",
          font=("Segoe UI", 15, "bold"),
          bg="#0ea5e9", fg="white").pack(pady=20)

    Label(janela, text="Escolha o formato:",
          font=("Segoe UI", 11),
          bg="#0f172a", fg="#f8fafc").pack(pady=20)

    def escolher(fmt):
        resultado["formato"] = fmt
        janela.destroy()

    Button(janela, text="Impressora A4\n(escritorio)",
           font=("Segoe UI", 12, "bold"),
           bg="#0ea5e9", fg="white",
           width=25, height=3, bd=0, cursor="hand2",
           command=lambda: escolher("A4")).pack(pady=8)

    Button(janela, text="Rolo Termico 80mm\n(farmacia)",
           font=("Segoe UI", 12, "bold"),
           bg="#10b981", fg="white",
           width=25, height=3, bd=0, cursor="hand2",
           command=lambda: escolher("TERMICA")).pack(pady=8)

    Button(janela, text="Cancelar",
           font=("Segoe UI", 10),
           bg="#64748b", fg="white",
           width=15, height=1, bd=0, cursor="hand2",
           command=janela.destroy).pack(pady=10)

    janela.wait_window()

    fmt = resultado["formato"]
    if not fmt:
        return None

    caminho, erro = gerar_pdf_ibt(trans_id, formato=fmt)
    if erro:
        from tkinter import messagebox
        messagebox.showerror("Erro", erro)
        return None

    import os
    if caminho and os.path.exists(caminho):
        try:
            os.startfile(caminho)
        except Exception:
            pass

    return caminho


if __name__ == "__main__":
    print("\n=== Teste relatorio_ibt.py ===\n")
    from database import conectar
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id, referencia FROM transferencias_filiais ORDER BY id DESC LIMIT 1")
    r = cur.fetchone()
    conn.close()

    if r:
        print(f"A gerar PDF para {r[1]}...")
        caminho, erro = gerar_pdf_ibt(r[0], formato="A4")
        if erro:
            print(f"ERRO: {erro}")
        else:
            print(f"OK - {caminho}")
    else:
        print("Sem IBTs para testar.")