"""
Comprovante de Movimento de Caixa (Saida/Entrada)
"""

import os
from datetime import datetime
from database import conectar, obter_empresa
from moeda import formatar_kz

PASTA_RELATORIOS = "relatorios"


def garantir_pasta():
    if not os.path.exists(PASTA_RELATORIOS):
        os.makedirs(PASTA_RELATORIOS)


def gerar_comprovante_movimento(movimento_id, formato="A4", caminho_saida=None):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.colors import HexColor
    except ImportError:
        return None, "ReportLab nao instalado."

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, caixa_id, data, tipo, valor, descricao,
               utilizador_nome, COALESCE(autorizado_por, ''),
               COALESCE(numero_documento, '')
        FROM movimentos_caixa WHERE id = ?
    """, (movimento_id,))
    mov = cur.fetchone()
    conn.close()

    if not mov:
        return None, f"Movimento #{movimento_id} nao encontrado."

    (mov_id, caixa_id, data, tipo, valor, descricao,
     utilizador, autorizado_por, numero_doc) = mov

    emp = obter_empresa()
    emp_nome = emp[1] if emp else "Farmacia"
    emp_nif = emp[2] if emp else "-"
    emp_end = emp[3] if emp else "-"
    emp_tel = emp[4] if emp else "-"

    garantir_pasta()

    tipo_txt = "saida" if tipo.upper() == "SAIDA" else "entrada"
    data_arquivo = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    sufixo = "A4" if formato == "A4" else "TERMICA"
    nome_ficheiro = f"mov_{tipo_txt}_{numero_doc}_{data_arquivo}_{sufixo}.pdf"
    caminho = os.path.join(PASTA_RELATORIOS, nome_ficheiro)

    if formato == "TERMICA":
        page_size = (80 * mm, 297 * mm)
    else:
        page_size = A4

    c = pdf_canvas.Canvas(caminho, pagesize=page_size)
    largura, altura = page_size

    if formato == "A4":
        _desenhar_a4(c, largura, altura, mov, emp_nome, emp_nif,
                     emp_end, emp_tel, mm, HexColor)
    else:
        _desenhar_termica(c, largura, altura, mov, emp_nome, emp_nif,
                          emp_tel, mm, HexColor)

    c.save()
    return caminho, None


def _desenhar_a4(c, largura, altura, mov, emp_nome, emp_nif,
                  emp_end, emp_tel, mm, HexColor):
    CINZA_ESCURO = HexColor("#1e293b")
    CINZA_MEDIO = HexColor("#64748b")
    CINZA_CLARO = HexColor("#e2e8f0")
    VERMELHO = HexColor("#dc2626")
    VERDE = HexColor("#16a34a")

    (mov_id, caixa_id, data, tipo, valor, descricao,
     utilizador, autorizado_por, numero_doc) = mov

    tipo_txt = "SAIDA" if tipo.upper() == "SAIDA" else "ENTRADA"
    cor_tipo = VERMELHO if tipo_txt == "SAIDA" else VERDE

    margem_esq = 20 * mm
    margem_dir = largura - 20 * mm
    y = altura - 20 * mm

    c.setFillColor(CINZA_ESCURO)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margem_esq, y, emp_nome)
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.setFillColor(CINZA_MEDIO)
    c.drawString(margem_esq, y, f"NIF: {emp_nif}  |  {emp_end}")
    y -= 4 * mm
    c.drawString(margem_esq, y, f"Tel: {emp_tel}")
    y -= 10 * mm

    c.setStrokeColor(CINZA_ESCURO)
    c.setLineWidth(1.5)
    c.line(margem_esq, y, margem_dir, y)

    y -= 15 * mm
    c.setFillColor(cor_tipo)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(largura / 2, y, f"COMPROVANTE DE {tipo_txt} DE CAIXA")

    y -= 10 * mm
    c.setFillColor(CINZA_ESCURO)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(largura / 2, y, f"Documento N. {numero_doc}")

    y -= 20 * mm

    try:
        dt_obj = datetime.strptime(data[:19], "%Y-%m-%d %H:%M:%S")
        data_fmt = dt_obj.strftime("%d/%m/%Y")
        hora_fmt = dt_obj.strftime("%H:%M")
    except Exception:
        data_fmt = data[:10] if data else "-"
        hora_fmt = data[11:16] if data and len(data) > 16 else "-"

    linhas = [("Data:", data_fmt), ("Hora:", hora_fmt),
              ("Caixa N.:", f"#{caixa_id}"), ("Tipo:", tipo_txt)]

    for label, valor_linha in linhas:
        c.setFont("Helvetica", 11)
        c.setFillColor(CINZA_MEDIO)
        c.drawString(margem_esq + 5 * mm, y, label)
        c.setFillColor(CINZA_ESCURO)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margem_esq + 40 * mm, y, valor_linha)
        y -= 7 * mm

    y -= 5 * mm
    c.setStrokeColor(CINZA_CLARO)
    c.setLineWidth(1)
    c.line(margem_esq, y, margem_dir, y)
    y -= 8 * mm

    c.setFont("Helvetica", 11)
    c.setFillColor(CINZA_MEDIO)
    c.drawString(margem_esq + 5 * mm, y, "VALOR:")
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(cor_tipo)
    c.drawString(margem_esq + 40 * mm, y, formatar_kz(valor))

    y -= 15 * mm
    c.setStrokeColor(CINZA_CLARO)
    c.setLineWidth(1)
    c.line(margem_esq, y, margem_dir, y)
    y -= 10 * mm

    c.setFont("Helvetica", 11)
    c.setFillColor(CINZA_MEDIO)
    c.drawString(margem_esq + 5 * mm, y, "Categoria / Motivo:")
    y -= 7 * mm

    c.setFont("Helvetica", 11)
    c.setFillColor(CINZA_ESCURO)

    texto = descricao or "-"
    for i in range(0, len(texto), 75):
        c.drawString(margem_esq + 10 * mm, y, texto[i:i + 75])
        y -= 6 * mm

    y -= 15 * mm
    c.setStrokeColor(CINZA_CLARO)
    c.setLineWidth(1)
    c.line(margem_esq, y, margem_dir, y)
    y -= 10 * mm

    c.setFont("Helvetica", 11)
    c.setFillColor(CINZA_ESCURO)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margem_esq + 5 * mm, y, "Registado por:")
    c.setFont("Helvetica", 11)
    c.drawString(margem_esq + 50 * mm, y, utilizador or "-")
    y -= 7 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margem_esq + 5 * mm, y, "Autorizado por:")
    c.setFont("Helvetica", 11)
    c.drawString(margem_esq + 50 * mm, y, autorizado_por or "-")

    y -= 40 * mm

    c.setStrokeColor(CINZA_ESCURO)
    c.setLineWidth(0.5)
    c.line(margem_esq + 10 * mm, y, margem_esq + 80 * mm, y)
    c.line(margem_dir - 80 * mm, y, margem_dir - 10 * mm, y)

    y -= 6 * mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(CINZA_ESCURO)
    c.drawCentredString(margem_esq + 45 * mm, y, "Assinatura do Operador")
    c.drawCentredString(margem_dir - 45 * mm, y, "Assinatura do Gerente")

    y -= 6 * mm
    c.setFont("Helvetica", 9)
    c.setFillColor(CINZA_MEDIO)
    c.drawCentredString(margem_esq + 45 * mm, y, utilizador or "")
    c.drawCentredString(margem_dir - 45 * mm, y, autorizado_por or "")

    c.setFont("Helvetica-Oblique", 7)
    c.setFillColor(CINZA_MEDIO)
    c.drawCentredString(largura / 2, 15 * mm,
                          f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} - JAM Soft")
    c.drawCentredString(largura / 2, 10 * mm, "Documento processado por computador")


def _desenhar_termica(c, largura, altura, mov, emp_nome, emp_nif,
                       emp_tel, mm, HexColor):
    (mov_id, caixa_id, data, tipo, valor, descricao,
     utilizador, autorizado_por, numero_doc) = mov

    tipo_txt = "SAIDA" if tipo.upper() == "SAIDA" else "ENTRADA"
    y = altura - 10 * mm

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#000000"))
    c.drawCentredString(largura / 2, y, emp_nome[:28])
    y -= 4 * mm
    c.setFont("Helvetica", 7)
    c.drawCentredString(largura / 2, y, f"NIF: {emp_nif}")
    y -= 3 * mm
    c.drawCentredString(largura / 2, y, f"Tel: {emp_tel}")
    y -= 5 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(largura / 2, y, "=" * 34)
    y -= 4 * mm
    c.drawCentredString(largura / 2, y, f"COMPROVANTE DE {tipo_txt}")
    y -= 4 * mm
    c.drawCentredString(largura / 2, y, "=" * 34)
    y -= 5 * mm

    c.setFont("Helvetica-Bold", 8)
    c.drawString(3 * mm, y, f"Doc: {numero_doc}")
    y -= 4 * mm

    c.setFont("Helvetica", 7)
    try:
        dt_obj = datetime.strptime(data[:19], "%Y-%m-%d %H:%M:%S")
        data_fmt = dt_obj.strftime("%d/%m/%Y %H:%M")
    except Exception:
        data_fmt = data or "-"

    c.drawString(3 * mm, y, f"Data: {data_fmt}")
    y -= 3.5 * mm
    c.drawString(3 * mm, y, f"Caixa: #{caixa_id}")
    y -= 4 * mm
    c.drawCentredString(largura / 2, y, "-" * 34)
    y -= 5 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(3 * mm, y, "VALOR:")
    y -= 5 * mm
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(largura / 2, y, formatar_kz(valor))
    y -= 6 * mm

    c.setFont("Helvetica", 7)
    c.drawString(3 * mm, y, "Motivo:")
    y -= 3.5 * mm
    for i in range(0, len(descricao or "-"), 40):
        c.drawString(5 * mm, y, (descricao or "-")[i:i + 40])
        y -= 3.5 * mm

    y -= 5 * mm
    c.setFont("Helvetica", 7)
    c.drawString(3 * mm, y, f"Operador: {(utilizador or '')[:30]}")
    y -= 3.5 * mm
    c.drawString(3 * mm, y, f"Autorizado: {(autorizado_por or '')[:30]}")
    y -= 6 * mm

    c.drawCentredString(largura / 2, y, "-" * 34)
    y -= 8 * mm
    c.setFont("Helvetica", 7)
    c.drawString(3 * mm, y, "Ass: __________________")
    y -= 3 * mm
    c.drawString(3 * mm, y, "      Operador")
    y -= 6 * mm
    c.drawString(3 * mm, y, "Ass: __________________")
    y -= 3 * mm
    c.drawString(3 * mm, y, "      Gerente")

    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(largura / 2, 10 * mm,
                          f"Gerado {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawCentredString(largura / 2, 7 * mm, "JAM Soft")
