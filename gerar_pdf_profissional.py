"""
Gera PDFs profissionais (A4) a partir dos ficheiros .md
Layout: capa + índice + corpo com cabeçalho/rodapé.
"""
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    Table, TableStyle, PageBreak, NextPageTemplate, KeepTogether
)


# ============================================================
# CORES JAM SOFT
# ============================================================
COR_PRIMARIA = colors.HexColor("#7c3aed")     # Roxo
COR_DOURADO = colors.HexColor("#fbbf24")      # Dourado
COR_ESCURA = colors.HexColor("#0f172a")       # Azul escuro
COR_CINZA = colors.HexColor("#64748b")        # Cinza
COR_CINZA_CLARO = colors.HexColor("#f1f5f9")  # Fundo claro
COR_BRANCA = colors.white


# ============================================================
# ESTILOS
# ============================================================
def _criar_estilos():
    styles = getSampleStyleSheet()

    return {
        "capa_titulo": ParagraphStyle(
            "capa_titulo", parent=styles["Heading1"],
            fontSize=36, leading=42, textColor=COR_BRANCA,
            alignment=TA_CENTER, fontName="Helvetica-Bold",
            spaceAfter=8,
        ),
        "capa_subtitulo": ParagraphStyle(
            "capa_subtitulo", parent=styles["Heading2"],
            fontSize=16, leading=22, textColor=COR_DOURADO,
            alignment=TA_CENTER, fontName="Helvetica",
            spaceAfter=20,
        ),
        "capa_info": ParagraphStyle(
            "capa_info", parent=styles["Normal"],
            fontSize=11, leading=16, textColor=COR_BRANCA,
            alignment=TA_CENTER, fontName="Helvetica",
        ),
        "h1": ParagraphStyle(
            "h1", parent=styles["Heading1"],
            fontSize=18, leading=24, textColor=COR_PRIMARIA,
            fontName="Helvetica-Bold",
            spaceBefore=16, spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2", parent=styles["Heading2"],
            fontSize=14, leading=19, textColor=COR_PRIMARIA,
            fontName="Helvetica-Bold",
            spaceBefore=12, spaceAfter=8,
        ),
        "h3": ParagraphStyle(
            "h3", parent=styles["Heading3"],
            fontSize=11.5, leading=16, textColor=COR_ESCURA,
            fontName="Helvetica-Bold",
            spaceBefore=10, spaceAfter=6,
        ),
        "normal": ParagraphStyle(
            "normal", parent=styles["Normal"],
            fontSize=10, leading=14.5, textColor=COR_ESCURA,
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=styles["Normal"],
            fontSize=10, leading=14.5, textColor=COR_ESCURA,
            leftIndent=15, bulletIndent=5, spaceAfter=3,
        ),
        "code": ParagraphStyle(
            "code", parent=styles["Code"],
            fontSize=8.5, leading=11, textColor=COR_ESCURA,
            fontName="Courier", backColor=COR_CINZA_CLARO,
            leftIndent=8, rightIndent=8,
            spaceBefore=6, spaceAfter=8,
        ),
        "citacao": ParagraphStyle(
            "citacao", parent=styles["Normal"],
            fontSize=10, leading=14, textColor=COR_CINZA,
            fontName="Helvetica-Oblique",
            leftIndent=15, spaceAfter=6,
        ),
        "rodape": ParagraphStyle(
            "rodape", parent=styles["Normal"],
            fontSize=8, textColor=COR_CINZA,
            alignment=TA_CENTER, fontName="Helvetica",
        ),
    }


# ============================================================
# CABEÇALHO E RODAPÉ
# ============================================================
def _desenhar_cabecalho_rodape(canvas, doc, titulo_doc):
    """Desenha cabeçalho e rodapé em todas as páginas (excepto capa)."""
    canvas.saveState()

    largura, altura = A4

    # Cabeçalho
    canvas.setFillColor(COR_PRIMARIA)
    canvas.rect(0, altura - 15 * mm, largura, 15 * mm, fill=1, stroke=0)

    canvas.setFillColor(COR_BRANCA)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(20 * mm, altura - 10 * mm, "JAM Soft")

    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(largura - 20 * mm, altura - 10 * mm, titulo_doc)

    # Rodapé
    canvas.setStrokeColor(COR_CINZA_CLARO)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, 15 * mm, largura - 20 * mm, 15 * mm)

    canvas.setFillColor(COR_CINZA)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(20 * mm, 10 * mm, f"JAM Soft © {datetime.now().year}")

    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(largura / 2, 10 * mm, f"Página {doc.page}")

    canvas.drawRightString(largura - 20 * mm, 10 * mm, "Versão 1.0.0")

    canvas.restoreState()


def _desenhar_capa(canvas, doc, titulo_doc, subtitulo):
    """Desenha a capa do documento."""
    canvas.saveState()

    largura, altura = A4

    # Fundo roxo escuro (metade superior)
    canvas.setFillColor(COR_ESCURA)
    canvas.rect(0, altura * 0.4, largura, altura * 0.6, fill=1, stroke=0)

    # Faixa dourada
    canvas.setFillColor(COR_DOURADO)
    canvas.rect(0, altura * 0.4 - 5 * mm, largura, 5 * mm, fill=1, stroke=0)

    # Fundo branco (metade inferior)
    canvas.setFillColor(COR_BRANCA)
    canvas.rect(0, 0, largura, altura * 0.4 - 5 * mm, fill=1, stroke=0)

    # Logotipo / Marca
    canvas.setFillColor(COR_DOURADO)
    canvas.setFont("Helvetica-Bold", 60)
    canvas.drawCentredString(largura / 2, altura * 0.65, "JAM")

    canvas.setFillColor(COR_BRANCA)
    canvas.setFont("Helvetica", 32)
    canvas.drawCentredString(largura / 2, altura * 0.55, "Soft")

    # Título do documento
    canvas.setFillColor(COR_BRANCA)
    canvas.setFont("Helvetica-Bold", 24)
    canvas.drawCentredString(largura / 2, altura * 0.45, titulo_doc)

    # Subtítulo dourado
    canvas.setFillColor(COR_DOURADO)
    canvas.setFont("Helvetica-Oblique", 14)
    canvas.drawCentredString(largura / 2, altura * 0.42, subtitulo)

    # Informações na metade inferior
    canvas.setFillColor(COR_ESCURA)
    canvas.setFont("Helvetica-Bold", 12)

    y = altura * 0.30
    canvas.drawCentredString(largura / 2, y, "Sistema de Gestão de Farmácias")

    canvas.setFont("Helvetica", 11)
    canvas.setFillColor(COR_CINZA)
    y -= 30
    canvas.drawCentredString(largura / 2, y, "Angola")

    y -= 40
    canvas.setFillColor(COR_ESCURA)
    canvas.setFont("Helvetica", 10)
    canvas.drawCentredString(largura / 2, y, f"Versão 1.0.0")

    y -= 15
    canvas.drawCentredString(
        largura / 2, y,
        f"{datetime.now().strftime('%d/%m/%Y')}"
    )

    canvas.restoreState()


# ============================================================
# CONVERSÃO MARKDOWN → ELEMENTOS
# ============================================================
def _escapar_html(texto):
    return (texto
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def _formatar_inline(texto):
    """Bold, itálico, code."""
    texto = _escapar_html(texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"\*(.+?)\*", r"<i>\1</i>", texto)
    texto = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", texto)
    return texto


import re


def _construir_elementos(ficheiro_md, estilos):
    """Lê o .md e devolve a lista de elementos reportlab."""
    with open(ficheiro_md, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    elementos = []
    dentro_codigo = False
    codigo_buffer = []
    tabela_buffer = []

    def _fechar_tabela():
        nonlocal tabela_buffer
        if not tabela_buffer:
            return

        linhas_tabela = []
        for linha in tabela_buffer:
            cells = [c.strip() for c in linha.split("|")[1:-1]]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            linhas_tabela.append([_formatar_inline(c) for c in cells])

        if linhas_tabela:
            try:
                # Calcular larguras
                n_cols = len(linhas_tabela[0])
                largura_util = 170 * mm
                largura_col = largura_util / n_cols

                t = Table(
                    linhas_tabela,
                    colWidths=[largura_col] * n_cols,
                    hAlign="LEFT",
                )
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), COR_PRIMARIA),
                    ("TEXTCOLOR", (0, 0), (-1, 0), COR_BRANCA),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.3,
                     colors.HexColor("#cbd5e1")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                     [COR_BRANCA, colors.HexColor("#f8fafc")]),
                ]))
                elementos.append(t)
                elementos.append(Spacer(1, 8))
            except Exception as e:
                print(f"[Tabela] Erro: {e}")
        tabela_buffer = []

    for linha in linhas:
        linha_strip = linha.rstrip()

        # Bloco de código
        if linha_strip.startswith("```"):
            if dentro_codigo:
                texto = "<br/>".join(codigo_buffer) if codigo_buffer else " "
                try:
                    elementos.append(Paragraph(texto, estilos["code"]))
                except Exception:
                    pass
                elementos.append(Spacer(1, 4))
                codigo_buffer = []
                dentro_codigo = False
            else:
                _fechar_tabela()
                dentro_codigo = True
            continue

        if dentro_codigo:
            linha_esc = _escapar_html(linha_strip).replace(" ", "&nbsp;")
            codigo_buffer.append(linha_esc)
            continue

        # Tabela
        if linha_strip.startswith("|"):
            tabela_buffer.append(linha_strip)
            continue
        else:
            _fechar_tabela()

        # Cabeçalhos
        if linha_strip.startswith("### "):
            elementos.append(Paragraph(
                _formatar_inline(linha_strip[4:]), estilos["h3"]))
        elif linha_strip.startswith("## "):
            elementos.append(Paragraph(
                _formatar_inline(linha_strip[3:]), estilos["h2"]))
        elif linha_strip.startswith("# "):
            elementos.append(Paragraph(
                _formatar_inline(linha_strip[2:]), estilos["h1"]))
        elif linha_strip.startswith("> "):
            elementos.append(Paragraph(
                _formatar_inline(linha_strip[2:]), estilos["citacao"]))
        elif linha_strip in ("---", "***", "___"):
            elementos.append(Spacer(1, 4))
        elif linha_strip == "":
            elementos.append(Spacer(1, 3))
        elif linha_strip.startswith("- ") or linha_strip.startswith("* "):
            texto = "• " + _formatar_inline(linha_strip[2:])
            elementos.append(Paragraph(texto, estilos["bullet"]))
        else:
            elementos.append(Paragraph(
                _formatar_inline(linha_strip), estilos["normal"]))

    _fechar_tabela()
    return elementos


# ============================================================
# GERAR PDF
# ============================================================
def gerar_pdf_profissional(ficheiro_md, ficheiro_pdf, titulo_doc, subtitulo):
    """Gera PDF profissional com capa + cabeçalho + rodapé."""
    estilos = _criar_estilos()

    # Doc
    doc = BaseDocTemplate(
        ficheiro_pdf,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=25 * mm,
        bottomMargin=20 * mm,
        title=titulo_doc,
        author="JAM Soft",
        subject=subtitulo,
    )

    # Frame da capa (sem cabeçalho/rodapé)
    frame_capa = Frame(
        0, 0, A4[0], A4[1],
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id="capa",
    )

    # Frame do conteúdo
    frame_conteudo = Frame(
        20 * mm, 20 * mm,
        A4[0] - 40 * mm,
        A4[1] - 45 * mm,
        id="conteudo",
    )

    def _capa(canvas, doc):
        _desenhar_capa(canvas, doc, titulo_doc, subtitulo)

    def _conteudo(canvas, doc):
        _desenhar_cabecalho_rodape(canvas, doc, titulo_doc)

    # Templates
    doc.addPageTemplates([
        PageTemplate(id="capa", frames=[frame_capa], onPage=_capa),
        PageTemplate(id="conteudo", frames=[frame_conteudo], onPage=_conteudo),
    ])

    # Construir
    elementos = _construir_elementos(ficheiro_md, estilos)

    story = [
        NextPageTemplate("conteudo"),  # Capa é renderizada pelo onPage
        PageBreak(),
    ] + elementos

    doc.build(story)
    print(f"✅ PDF criado: {ficheiro_pdf}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  GERADOR DE PDFs PROFISSIONAIS — JAM Soft")
    print("=" * 60)
    print()

    docs = [
        ("RESUMO_SISTEMA.md", "RESUMO_SISTEMA.pdf",
         "Resumo do Sistema", "Documentação Técnica"),
        ("MANUAL_UTILIZACAO.md", "MANUAL_UTILIZACAO.pdf",
         "Manual de Utilização", "Guia do Utilizador"),
    ]

    for md, pdf, titulo, sub in docs:
        if Path(md).exists():
            gerar_pdf_profissional(md, pdf, titulo, sub)
        else:
            print(f"⚠️  {md} não encontrado")

    print()
    print("=" * 60)
    print("  Concluído!")
    print("=" * 60)
    print()