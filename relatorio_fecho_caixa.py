"""
Relatorio Fecho de Caixa - PDF A4 ou Termico 80mm
"""

import os
from datetime import datetime

from database import obter_turno, conectar
from moeda import formatar_kz

PASTA_RELATORIOS = "relatorios"


def garantir_pasta():
    if not os.path.exists(PASTA_RELATORIOS):
        os.makedirs(PASTA_RELATORIOS)


def gerar_fecho_caixa(caixa_id, resultado, observacoes, utilizador, formato="TERMICA"):
    """
    Gera PDF do fecho de caixa.

    caixa_id: ID do caixa
    resultado: dict com esperado, contado, diferenca
    observacoes: str
    utilizador: dict com id, nome
    formato: "A4" ou "TERMICA"

    Retorna (caminho, erro)
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.colors import HexColor
    except ImportError:
        return None, "ReportLab nao instalado."

    # Buscar dados do caixa
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, data_abertura, data_fecho, utilizador_abertura_nome,
               utilizador_fecho_nome, valor_inicial, total_vendas_dinheiro,
               total_sangrias, total_reforcos, valor_esperado, valor_contado,
               diferenca, observacoes
        FROM caixas WHERE id = ?
    """, (caixa_id,))
    caixa = cur.fetchone()

    if not caixa:
        conn.close()
        return None, f"Caixa #{caixa_id} nao encontrado."

    # Buscar movimentos
    cur.execute("""
        SELECT data, tipo, valor, descricao, utilizador_nome
        FROM movimentos_caixa WHERE caixa_id = ?
        ORDER BY id
    """, (caixa_id,))
    movimentos = cur.fetchall()
    conn.close()

    # Empresa
    from database import obter_empresa
    emp = obter_empresa()
    emp_nome = emp[1] if emp else "Farmacia"
    emp_nif = emp[2] if emp else "-"
    emp_tel = emp[4] if emp else "-"

    garantir_pasta()
    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    sufixo = "A4" if formato == "A4" else "TERMICA"
    caminho = os.path.join(
        PASTA_RELATORIOS,
        f"fecho_caixa_{caixa_id}_{agora}_{sufixo}.pdf"
    )

    if formato == "TERMICA":
        page_size = (80 * mm, 297 * mm)
    else:
        page_size = A4

    c = pdf_canvas.Canvas(caminho, pagesize=page_size)
    largura, altura = page_size

    if formato == "TERMICA":
        _desenhar_termica(c, largura, altura, caixa, movimentos, resultado,
                          observacoes, utilizador, emp_nome, emp_nif, emp_tel,
                          mm, HexColor)
    else:
        _desenhar_a4(c, largura, altura, caixa, movimentos, resultado,
                     observacoes, utilizador, emp_nome, emp_nif, emp_tel,
                     mm, HexColor)

    c.save()
    return caminho, None


def _desenhar_a4(c, largura, altura, caixa, movimentos, resultado,
                  observacoes, utilizador, emp_nome, emp_nif, emp_tel,
                  mm, HexColor):
    y = altura - 20 * mm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, y, emp_nome)
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, y, f"NIF: {emp_nif}  |  Tel: {emp_tel}")
    y -= 15 * mm

    c.setFillColor(HexColor("#be185d"))
    c.rect(15 * mm, y - 3 * mm, largura - 30 * mm, 14 * mm, fill=1, stroke=0)
    c.setFillColor(HexColor("#ffffff"))
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(largura / 2, y + 3 * mm, "FECHO DE CAIXA")
    c.setFillColor(HexColor("#000000"))
    y -= 20 * mm

    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Caixa #: {caixa[0]}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"Abertura: {caixa[1] or '-'}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"Fecho:    {caixa[2] or '-'}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"Operador abertura: {caixa[3] or '-'}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"Operador fecho:    {caixa[4] or '-'}")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(HexColor("#7c3aed"))
    c.drawString(20 * mm, y, "RESUMO FINANCEIRO")
    c.setFillColor(HexColor("#000000"))
    y -= 7 * mm

    c.setFont("Helvetica", 11)
    linhas = [
        ("VALOR ESPERADO:", formatar_kz(resultado.get("esperado", 0))),
        ("VALOR CONTADO:", formatar_kz(resultado.get("contado", 0))),
    ]

    for label, valor in linhas:
        c.drawString(25 * mm, y, label)
        if valor:
            c.drawRightString(largura - 25 * mm, y, valor)
        y -= 6 * mm

    y -= 3 * mm

    dif = resultado.get("diferenca", 0)
    c.setFont("Helvetica-Bold", 12)
    if abs(dif) < 0.01:
        c.setFillColor(HexColor("#16a34a"))
        c.drawString(25 * mm, y, "DIFERENCA: OK (sem diferencas)")
    elif dif > 0:
        c.setFillColor(HexColor("#f97316"))
        c.drawString(25 * mm, y, f"DIFERENCA: SOBRA {formatar_kz(dif)}")
    else:
        c.setFillColor(HexColor("#dc2626"))
        c.drawString(25 * mm, y, f"DIFERENCA: FALTA {formatar_kz(abs(dif))}")
    c.setFillColor(HexColor("#000000"))
    y -= 12 * mm

    if movimentos:
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(HexColor("#7c3aed"))
        c.drawString(20 * mm, y, "MOVIMENTOS")
        c.setFillColor(HexColor("#000000"))
        y -= 7 * mm

        c.setFont("Helvetica", 9)
        for m in movimentos:
            dt, tipo, valor, desc, user = m
            c.drawString(20 * mm, y, f"{(dt or '-')[:16]} | {tipo or '-'} | {formatar_kz(valor or 0)} | {(desc or '-')[:40]}")
            y -= 5 * mm

    if observacoes:
        y -= 10 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "Observacoes:")
        y -= 6 * mm
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, observacoes[:80])

    y = 40 * mm
    c.setFont("Helvetica", 10)
    c.drawString(30 * mm, y, "_" * 35)
    c.drawString(largura - 100 * mm, y, "_" * 35)
    y -= 5 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(40 * mm, y, "Operador")
    c.drawString(largura - 90 * mm, y, "Gerente")

    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(HexColor("#6b7280"))
    c.drawCentredString(largura / 2, 15 * mm,
                         f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} - JAM Soft")


def _desenhar_termica(c, largura, altura, caixa, movimentos, resultado,
                       observacoes, utilizador, emp_nome, emp_nif, emp_tel,
                       mm, HexColor):
    y = altura - 10 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura / 2, y, emp_nome[:30])
    y -= 4 * mm
    c.setFont("Helvetica", 7)
    c.drawCentredString(largura / 2, y, f"NIF: {emp_nif}")
    y -= 3 * mm
    c.drawCentredString(largura / 2, y, f"Tel: {emp_tel}")
    y -= 5 * mm

    c.drawCentredString(largura / 2, y, "-" * 40)
    y -= 5 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura / 2, y, "FECHO DE CAIXA")
    y -= 5 * mm

    c.drawCentredString(largura / 2, y, "-" * 40)
    y -= 5 * mm

    c.setFont("Helvetica", 8)
    c.drawString(3 * mm, y, f"Caixa: #{caixa[0]}")
    y -= 3.5 * mm
    c.drawString(3 * mm, y, f"Abertura: {(caixa[1] or '')[-16:]}")
    y -= 3.5 * mm
    c.drawString(3 * mm, y, f"Fecho: {(caixa[2] or '')[-16:]}")
    y -= 3.5 * mm
    c.drawString(3 * mm, y, f"Operador: {(caixa[4] or '-')[:25]}")
    y -= 4 * mm

    c.drawCentredString(largura / 2, y, "-" * 40)
    y -= 5 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(3 * mm, y, "RESUMO")
    y -= 4 * mm

    c.setFont("Helvetica", 8)
    c.drawString(3 * mm, y, "Esperado:")
    c.drawRightString(largura - 3 * mm, y, formatar_kz(resultado.get("esperado", 0)))
    y -= 4 * mm
    c.drawString(3 * mm, y, "Contado:")
    c.drawRightString(largura - 3 * mm, y, formatar_kz(resultado.get("contado", 0)))
    y -= 4 * mm

    dif = resultado.get("diferenca", 0)
    c.setFont("Helvetica-Bold", 9)
    if abs(dif) < 0.01:
        c.drawString(3 * mm, y, "Dif: OK")
    elif dif > 0:
        c.drawString(3 * mm, y, f"Dif: SOBRA {formatar_kz(dif)}")
    else:
        c.drawString(3 * mm, y, f"Dif: FALTA {formatar_kz(abs(dif))}")
    y -= 5 * mm

    if observacoes:
        y -= 3 * mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(3 * mm, y, "Obs:")
        y -= 3.5 * mm
        c.setFont("Helvetica", 7)
        c.drawString(3 * mm, y, observacoes[:40])
        y -= 3.5 * mm

    y -= 5 * mm
    c.setFont("Helvetica", 7)
    c.drawString(3 * mm, y, "Ass: __________________")
    y -= 8 * mm
    c.drawString(3 * mm, y, "Ass: __________________")

    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(largura / 2, 10 * mm,
                         f"Gerado {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawCentredString(largura / 2, 7 * mm, "JAM Soft")