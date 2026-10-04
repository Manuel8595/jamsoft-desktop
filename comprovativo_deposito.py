"""
Gera o PDF (A4) do comprovativo de deposito bancario.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                  Table, TableStyle)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from pathlib import Path


# Cores JAM Soft
ROXO = HexColor("#7c3aed")
DOURADO = HexColor("#fbbf24")
ESCURO = HexColor("#0f172a")
CINZA = HexColor("#64748b")
VERDE = HexColor("#10b981")
VERDE_CLARO = HexColor("#ecfdf5")
CINZA_CLARO = HexColor("#f1f5f9")


def _fmt_kz(valor):
    try:
        return f"Kz {float(valor):,.0f}".replace(",", ".")
    except Exception:
        return "Kz 0"


def gerar_comprovativo_deposito(deposito, farmacia=None, pasta_saida=None):
    """
    Gera o PDF do comprovativo.

    deposito: dict com keys:
        referencia, data, hora, valor, banco, numero_comprovante,
        observacoes, gerente_nome, estado

    farmacia: dict com keys (opcional):
        nome, nif, endereco, telefone

    pasta_saida: Path ou str (default: pasta actual)

    Devolve: caminho do PDF gerado.
    """
    if pasta_saida is None:
        pasta_saida = Path(__file__).parent / "facturas"
    else:
        pasta_saida = Path(pasta_saida)

    pasta_saida.mkdir(parents=True, exist_ok=True)

    referencia = deposito.get("referencia", "DEP-XXXX")
    nome_ficheiro = pasta_saida / f"Comprovativo_{referencia}.pdf"

    # ─── Documento ───
    doc = SimpleDocTemplate(
        str(nome_ficheiro),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm,
        title=f"Comprovativo de Deposito {referencia}",
        author="JAM Soft",
    )

    styles = getSampleStyleSheet()

    # ─── Estilos ───
    marca = ParagraphStyle(
        "marca", parent=styles["Normal"],
        fontSize=20, textColor=ROXO,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    subtitulo_marca = ParagraphStyle(
        "subtitulo", parent=styles["Normal"],
        fontSize=9, textColor=CINZA,
        alignment=TA_CENTER, fontName="Helvetica-Oblique",
        spaceBefore=8,
    )
    titulo = ParagraphStyle(
        "titulo", parent=styles["Heading1"],
        fontSize=16, textColor=ESCURO,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
        spaceBefore=10, spaceAfter=4,
    )
    ref_grande = ParagraphStyle(
        "ref", parent=styles["Normal"],
        fontSize=22, textColor=ROXO,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
        spaceAfter=15,
    )
    legenda = ParagraphStyle(
        "legenda", parent=styles["Normal"],
        fontSize=10, textColor=CINZA,
        alignment=TA_CENTER,
    )
    aviso = ParagraphStyle(
        "aviso", parent=styles["Normal"],
        fontSize=11, textColor=ESCURO,
        alignment=TA_CENTER,
        backColor=DOURADO,
        borderPadding=12,
        spaceBefore=15, spaceAfter=10,
    )
    assinatura = ParagraphStyle(
        "assinatura", parent=styles["Normal"],
        fontSize=10, textColor=CINZA,
        alignment=TA_CENTER,
        spaceBefore=20,
    )
    rodape = ParagraphStyle(
        "rodape", parent=styles["Normal"],
        fontSize=8, textColor=CINZA,
        alignment=TA_CENTER,
    )

    elementos = []

    # ─── Cabeçalho ───
    try:
        from reportlab.platypus import Image as RLImage
        caminho_logo = Path(__file__).parent / "logos" / "logo_horizontal_medio.png"
        if caminho_logo.exists():
            img_logo = RLImage(str(caminho_logo), width=8 * cm, height=2.7 * cm)
            img_logo.hAlign = "CENTER"
            elementos.append(img_logo)
        else:
            elementos.append(Paragraph("JAM Soft", marca))
            elementos.append(Paragraph("Sistema de Gestao de Farmacias", subtitulo_marca))
    except Exception:
        elementos.append(Paragraph("JAM Soft", marca))
        elementos.append(Paragraph("Sistema de Gestao de Farmacias", subtitulo_marca))

    elementos.append(Spacer(1, 0.3 * cm))

    # Linha decorativa
    linha = Table([[""]], colWidths=[17 * cm], rowHeights=[3])
    linha.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ROXO),
    ]))
    elementos.append(linha)
    elementos.append(Spacer(1, 0.5 * cm))

    # ─── Título ───
    elementos.append(Paragraph("COMPROVATIVO DE DEPOSITO BANCARIO", titulo))
    elementos.append(Paragraph(referencia, ref_grande))

    # ─── Info farmácia ───
    if farmacia:
        nome_f = farmacia.get("nome", "-")
        nif_f = farmacia.get("nif", "-")
        end_f = farmacia.get("endereco", "-")
        tel_f = farmacia.get("telefone", "-")

        # Nome da farmácia em destaque
        nome_style = ParagraphStyle(
            "nome_farm", parent=styles["Normal"],
            fontSize=13, textColor=ESCURO,
            alignment=TA_CENTER, fontName="Helvetica-Bold",
        )
        info_style = ParagraphStyle(
            "info_farm", parent=styles["Normal"],
            fontSize=10, textColor=CINZA,
            alignment=TA_CENTER,
        )
        elementos.append(Paragraph(nome_f, nome_style))
        elementos.append(Paragraph(f"NIF: {nif_f}", info_style))
        elementos.append(Paragraph(end_f, info_style))
        elementos.append(Paragraph(f"Tel: {tel_f}", info_style))
    else:
        elementos.append(Paragraph("Farmacia nao identificada", legenda))

    elementos.append(Spacer(1, 1 * cm))

    # ─── Dados do depósito ───
    dados = [
        ["Referencia:", deposito.get("referencia", "-")],
        ["Data:", f"{deposito.get('data', '-')}  {deposito.get('hora', '')}"],
        ["Banco:", deposito.get("banco", "-")],
        ["Numero do comprovante:", deposito.get("numero_comprovante", "-")],
        ["Valor:", _fmt_kz(deposito.get("valor", 0))],
        ["Gerente:", deposito.get("gerente_nome", "-")],
        ["Estado:", deposito.get("estado", "-")],
    ]

    if deposito.get("observacoes"):
        dados.append(["Observacoes:", deposito.get("observacoes")])

    t_dados = Table(dados, colWidths=[5 * cm, 12 * cm])
    t_dados.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (0, 0), (0, -1), CINZA),
        ("TEXTCOLOR", (1, 0), (1, -1), ESCURO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, -1), CINZA_CLARO),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elementos.append(t_dados)

    # ─── Aviso importante ───
    elementos.append(Paragraph(
        f"<b>IMPORTANTE:</b> Ao depositar no banco, escreva a referencia "
        f"<b>{referencia}</b> na descricao do deposito.<br/>"
        f"Isto permite ao CEO confirmar o deposito mais tarde.",
        aviso,
    ))

    # ─── Assinatura ───
    elementos.append(Spacer(1, 1.5 * cm))
    elementos.append(Paragraph("_" * 40, assinatura))
    elementos.append(Paragraph(
        f"Assinatura do gerente: {deposito.get('gerente_nome', '-')}",
        assinatura,
    ))

    # ─── Rodapé ───
    agora = datetime.now().strftime("%d/%m/%Y as %H:%M")
    elementos.append(Spacer(1, 1.5 * cm))
    elementos.append(Paragraph(
        f"Documento gerado em {agora} pela plataforma JAM Soft",
        rodape,
    ))
    elementos.append(Paragraph(
        "Este documento nao substitui o comprovativo oficial do banco.",
        rodape,
    ))

    # ─── Construir ───
    doc.build(elementos)

    print(f"[PDF] Comprovativo gerado: {nome_ficheiro}")
    return str(nome_ficheiro)


if __name__ == "__main__":
    # Teste
    deposito_teste = {
        "referencia": "DEP-2026-TESTE",
        "data": "2026-10-04",
        "hora": "22:13",
        "valor": 350000,
        "banco": "BAI",
        "numero_comprovante": "1234567",
        "observacoes": "Teste de geracao de PDF",
        "gerente_nome": "Aguinaldo Morais",
        "estado": "REGISTADO",
    }
    farmacia_teste = {
        "nome": "TRI JAM FARMA",
        "nif": "541234567",
        "endereco": "Rua da Liberdade, 45, Luanda",
        "telefone": "+244 923 111 222",
    }
    caminho = gerar_comprovativo_deposito(deposito_teste, farmacia_teste)
    print(f"Ficheiro: {caminho}")