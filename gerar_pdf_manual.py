"""
Gera PDF a partir dos ficheiros .md usando reportlab.
"""
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)


def _escapar_html(texto):
    """Escapa caracteres perigosos para o reportlab."""
    return (texto
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def _formatar_inline(texto):
    """Converte markdown inline (bold, italic, code) para HTML do reportlab."""
    texto = _escapar_html(texto)
    # Bold
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    # Italic
    texto = re.sub(r"\*(.+?)\*", r"<i>\1</i>", texto)
    # Code
    texto = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", texto)
    return texto


def md_para_pdf(ficheiro_md, ficheiro_pdf):
    """Converte um ficheiro .md simples para PDF."""
    with open(ficheiro_md, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    doc = SimpleDocTemplate(
        ficheiro_pdf,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=Path(ficheiro_md).stem,
        author="JAM Soft",
    )

    styles = getSampleStyleSheet()

    style_h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"], fontSize=22,
        textColor=colors.HexColor("#7c3aed"),
        spaceAfter=14, spaceBefore=8,
    )
    style_h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"], fontSize=15,
        textColor=colors.HexColor("#7c3aed"),
        spaceAfter=10, spaceBefore=14,
    )
    style_h3 = ParagraphStyle(
        "H3", parent=styles["Heading3"], fontSize=12,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8, spaceBefore=10,
    )
    style_normal = ParagraphStyle(
        "Normal", parent=styles["Normal"], fontSize=10,
        leading=14, spaceAfter=5,
    )
    style_code = ParagraphStyle(
        "Code", parent=styles["Code"], fontSize=7.5,
        leading=9, textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        leftIndent=6, rightIndent=6,
        spaceBefore=4, spaceAfter=6,
    )
    style_citacao = ParagraphStyle(
        "Quote", parent=styles["Normal"], fontSize=10,
        leftIndent=15, textColor=colors.HexColor("#475569"),
        fontName="Helvetica-Oblique", spaceAfter=6,
    )

    elementos = []
    dentro_codigo = False
    codigo_buffer = []
    tabela_buffer = []

    def _fechar_tabela():
        """Processa tabela acumulada."""
        nonlocal tabela_buffer
        if not tabela_buffer:
            return

        linhas_tabela = []
        for linha in tabela_buffer:
            cells = [c.strip() for c in linha.split("|")[1:-1]]
            # Pular linha de separação (---)
            if all(set(c) <= set("-: ") for c in cells):
                continue
            linhas_tabela.append(cells)

        if len(linhas_tabela) >= 1:
            try:
                t = Table(linhas_tabela, hAlign="LEFT")
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                     [colors.white, colors.HexColor("#f8fafc")]),
                ]))
                elementos.append(t)
                elementos.append(Spacer(1, 8))
            except Exception as e:
                print(f"[Tabela] Erro: {e}")
        tabela_buffer = []

    for linha in linhas:
        linha_strip = linha.rstrip()

        # ─── Bloco de código ───
        if linha_strip.startswith("```"):
            if dentro_codigo:
                texto_code = "<br/>".join(codigo_buffer) if codigo_buffer else " "
                try:
                    elementos.append(Paragraph(texto_code, style_code))
                except Exception:
                    # Fallback se falhar
                    pass
                elementos.append(Spacer(1, 6))
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

        # ─── Tabela ───
        if linha_strip.startswith("|"):
            tabela_buffer.append(linha_strip)
            continue
        else:
            _fechar_tabela()

        # ─── Cabeçalhos ───
        if linha_strip.startswith("### "):
            elementos.append(Paragraph(_formatar_inline(linha_strip[4:]), style_h3))
        elif linha_strip.startswith("## "):
            elementos.append(Paragraph(_formatar_inline(linha_strip[3:]), style_h2))
        elif linha_strip.startswith("# "):
            elementos.append(Paragraph(_formatar_inline(linha_strip[2:]), style_h1))
        elif linha_strip.startswith("> "):
            elementos.append(Paragraph(_formatar_inline(linha_strip[2:]), style_citacao))
        elif linha_strip in ("---", "***", "___"):
            elementos.append(Spacer(1, 4))
        elif linha_strip == "":
            elementos.append(Spacer(1, 3))
        elif linha_strip.startswith("- ") or linha_strip.startswith("* "):
            texto = "• " + _formatar_inline(linha_strip[2:])
            elementos.append(Paragraph(texto, style_normal))
        else:
            elementos.append(Paragraph(_formatar_inline(linha_strip), style_normal))

    _fechar_tabela()

    doc.build(elementos)
    print(f"✅ PDF criado: {ficheiro_pdf}")


if __name__ == "__main__":
    print("A gerar PDFs...")
    print()

    if Path("RESUMO_SISTEMA.md").exists():
        md_para_pdf("RESUMO_SISTEMA.md", "RESUMO_SISTEMA.pdf")
    else:
        print("⚠️ RESUMO_SISTEMA.md nao encontrado")

    if Path("MANUAL_UTILIZACAO.md").exists():
        md_para_pdf("MANUAL_UTILIZACAO.md", "MANUAL_UTILIZACAO.pdf")
    else:
        print("⚠️ MANUAL_UTILIZACAO.md nao encontrado")

    print()
    print("Concluido!")