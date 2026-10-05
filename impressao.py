import os
from datetime import datetime
from tkinter import *
from tkinter import messagebox, ttk
from database import (obter_empresa, buscar_factura_por_id, listar_itens_factura,
                       listar_facturas, registar_auditoria, obter_logo_empresa,
                       conectar, obter_itens_factura_com_desconto)
from moeda import formatar_kz

COR_FUNDO = "#fef2f2"
COR_PRIMARIA = "#dc2626"
COR_TEXTO = "#7f1d1d"
COR_PERIGO = "#991b1b"
COR_HEADER = "#b91c1c"
COR_CARD = "#ffffff"
COR_VERDE = "#16a34a"
COR_DESCONTO = "#7c3aed"

PASTA_FACTURAS = "facturas"
AVISO_FISCAL_LOCAL = "DOCUMENTO LOCAL - NAO VALIDADO PELA AGT"
AVISO_AGT_PROVISORIO = "Programa em processo de validacao AGT"


def garantir_pasta():
    if not os.path.exists(PASTA_FACTURAS):
        os.makedirs(PASTA_FACTURAS)


def listar_impressoras():
    impressoras = []
    try:
        import subprocess
        resultado = subprocess.check_output(
            'wmic printer get name', shell=True, text=True
        )
        for linha in resultado.split("\n")[1:]:
            nome = linha.strip()
            if nome and nome != "Name":
                impressoras.append(nome)
    except Exception:
        pass
    return impressoras


def _fmt_sem_kz(valor):
    """Formata um valor SEM o prefixo Kz."""
    try:
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"


def _desenhar_qr(c, qr_url, largura, y, tamanho_mm=25, offset_direita_mm=50):
    """
    Desenha o QR code no canvas.
    Devolve True se desenhou, False se falhou.
    """
    if not qr_url:
        return False

    try:
        import qrcode
        from reportlab.lib.utils import ImageReader
        from reportlab.lib.units import mm
        import io

        qr = qrcode.QRCode(box_size=4, border=1)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        qr_size = tamanho_mm * mm
        qr_x = largura - offset_direita_mm * mm

        c.drawImage(ImageReader(buf), qr_x, y - qr_size,
                     width=qr_size, height=qr_size)
        return True
    except Exception as e:
        print(f"[QR] Erro ao desenhar: {e}")
        return False


# ============================================================
# ============ PDF DE FACTURA ================================
# ============================================================

def gerar_pdf_factura(factura_id, formato="A4", caminho_saida=None,
                        valor_dinheiro=None, valor_segunda=None):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas as pdf_canvas
    except ImportError:
        return None, "reportlab nao instalado."

    f = buscar_factura_por_id(factura_id)
    if not f:
        return None, "Factura nao encontrada."

    if valor_dinheiro is None:
        valor_dinheiro = 0
    if valor_segunda is None:
        valor_segunda = 0

    if len(f) >= 17:
        (fid, numero, serie, tipo, data, cli_nome, cli_nif, cli_end,
         subtotal, iva, total, estado, motivo,
         forma_pagamento, ref_multicaixa,
         val_din_bd, val_seg_bd) = f[:17]
        if valor_dinheiro == 0:
            valor_dinheiro = val_din_bd or 0
        if valor_segunda == 0:
            valor_segunda = val_seg_bd or 0
    elif len(f) >= 15:
        (fid, numero, serie, tipo, data, cli_nome, cli_nif, cli_end,
         subtotal, iva, total, estado, motivo,
         forma_pagamento, ref_multicaixa) = f[:15]
    else:
        (fid, numero, serie, tipo, data, cli_nome, cli_nif, cli_end,
         subtotal, iva, total, estado, motivo) = f[:13]
        forma_pagamento = None
        ref_multicaixa = None

    emp = obter_empresa()
    emp_nome = emp[1] if emp else "Farmacia"
    emp_nif = emp[2] if emp else "-"
    emp_end = emp[3] if emp else "-"
    emp_tel = emp[4] if emp else "-"
    emp_email = emp[5] if emp else "-"

    logo_path = None
    if emp and len(emp) > 9:
        logo_path = emp[9]

    itens = obter_itens_factura_com_desconto(factura_id)

    # ─── Buscar hash + QR da factura (AGT) ───
    hash_doc = None
    qr_url = None
    try:
        from database import obter_hash_factura
        hash_info = obter_hash_factura(factura_id)
        if hash_info:
            hash_doc = hash_info[0]
            qr_url = hash_info[1]
    except Exception:
        pass

    total_desconto = 0
    for item in itens:
        if len(item) >= 9:
            total_desconto += item[8] or 0
        else:
            total_desconto += item[7] if len(item) > 7 else 0

    garantir_pasta()

    if not caminho_saida:
        nome_seguro = numero.replace("/", "_").replace(" ", "_")
        caminho_saida = os.path.join(PASTA_FACTURAS, f"{nome_seguro}.pdf")

    if formato == "TERMICA":
        altura = 180 * mm + (len(itens) * 12 * mm)
        page_size = (80 * mm, altura)
    else:
        page_size = A4

    c = pdf_canvas.Canvas(caminho_saida, pagesize=page_size)
    largura, altura = page_size

    y = altura - 15 * mm

    if formato == "TERMICA":
        # ===== CUPOM TERMICO =====
        if logo_path and os.path.exists(logo_path):
            try:
                from reportlab.lib.utils import ImageReader
                logo_img = ImageReader(logo_path)
                logo_w = 25 * mm
                logo_h = 20 * mm
                c.drawImage(logo_img, (largura - logo_w) / 2, y - logo_h,
                             width=logo_w, height=logo_h,
                             preserveAspectRatio=True, mask='auto')
                y -= logo_h + 3 * mm
            except Exception:
                pass

        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(largura/2, y, emp_nome[:30])
        y -= 5 * mm
        c.setFont("Helvetica", 7)
        c.drawCentredString(largura/2, y, f"NIF: {emp_nif}")
        y -= 4 * mm
        c.drawCentredString(largura/2, y, f"{emp_end[:35]}")
        y -= 4 * mm
        c.drawCentredString(largura/2, y, f"Tel: {emp_tel}")
        y -= 6 * mm

        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(largura/2, y, f"{tipo} {numero}")
        y -= 5 * mm
        c.setFont("Helvetica", 7)
        c.drawCentredString(largura/2, y, f"Data: {data}")
        y -= 3 * mm

        # AGT: Aviso
        c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(largura/2, y, AVISO_FISCAL_LOCAL)
        y -= 3 * mm
        c.setFont("Helvetica", 5)
        c.drawCentredString(largura/2, y, AVISO_AGT_PROVISORIO)
        y -= 4 * mm

        # QR Code (centrado)
        if _desenhar_qr(c, qr_url, largura, y, tamanho_mm=18):
            y -= 20 * mm

        # Hash
        if hash_doc:
            c.setFont("Helvetica", 5)
            c.drawCentredString(largura/2, y, f"Hash: {hash_doc[:32]}...")
            y -= 3 * mm

        c.drawCentredString(largura/2, y, "-" * 40)
        y -= 5 * mm

        c.setFont("Helvetica-Bold", 7)
        c.drawString(3 * mm, y, "Cliente:")
        y -= 4 * mm
        c.setFont("Helvetica", 7)
        c.drawString(3 * mm, y, (cli_nome or "Consumidor Final")[:38])
        y -= 4 * mm
        if cli_nif:
            c.drawString(3 * mm, y, f"NIF: {cli_nif}")
            y -= 4 * mm

        c.drawCentredString(largura/2, y, "-" * 40)
        y -= 5 * mm

        c.setFont("Helvetica-Bold", 7)
        c.drawString(3 * mm, y, "Item")
        c.drawRightString(largura - 3 * mm, y, "Total")
        y -= 4 * mm
        c.setFont("Helvetica", 7)

        for item in itens:
            if len(item) >= 9:
                desc, qtd, preco, isento, taxa, valor_iva, sub, desc_p, desc_v = item
            else:
                desc, qtd, preco, isento, taxa, valor_iva, sub = item
                desc_p, desc_v = 0, 0

            c.drawString(3 * mm, y, str(desc)[:22])
            y -= 3 * mm
            c.drawString(5 * mm, y, f"{qtd} x {formatar_kz(preco)}")
            c.drawRightString(largura - 3 * mm, y, formatar_kz(sub))
            y -= 3 * mm
            if desc_p and desc_p > 0:
                c.setFont("Helvetica-Oblique", 6)
                c.drawString(5 * mm, y, f"   Desc. {desc_p:.0f}%: -{formatar_kz(desc_v)}")
                c.setFont("Helvetica", 7)
                y -= 3 * mm
            y -= 1 * mm

        c.drawCentredString(largura/2, y, "-" * 40)
        y -= 5 * mm

        c.setFont("Helvetica", 7)
        c.drawString(3 * mm, y, "Subtotal:")
        c.drawRightString(largura - 3 * mm, y, _fmt_sem_kz(subtotal))
        y -= 4 * mm

        if total_desconto > 0:
            c.drawString(3 * mm, y, "Descontos:")
            c.drawRightString(largura - 3 * mm, y, f"-{_fmt_sem_kz(total_desconto)}")
            y -= 4 * mm

        if forma_pagamento:
            if forma_pagamento == "Dinheiro":
                c.drawString(3 * mm, y, "Dinheiro:")
                c.drawRightString(largura - 3 * mm, y, _fmt_sem_kz(total))
                y -= 4 * mm
            elif forma_pagamento == "Multicaixa":
                c.drawString(3 * mm, y, "Cartao de debito:")
                c.drawRightString(largura - 3 * mm, y, _fmt_sem_kz(total))
                y -= 4 * mm
                if ref_multicaixa:
                    c.drawString(5 * mm, y, f"Cartao Nr {ref_multicaixa}")
                    y -= 4 * mm
            elif forma_pagamento == "Transferencia":
                c.drawString(3 * mm, y, "Transferencia:")
                c.drawRightString(largura - 3 * mm, y, _fmt_sem_kz(total))
                y -= 4 * mm
                if ref_multicaixa:
                    c.drawString(5 * mm, y, f"Ref. Nr {ref_multicaixa}")
                    y -= 4 * mm
            elif "Misto" in forma_pagamento:
                v_din = valor_dinheiro or 0
                v_seg = valor_segunda or 0
                c.drawString(3 * mm, y, "Dinheiro:")
                c.drawRightString(largura - 3 * mm, y, _fmt_sem_kz(v_din))
                y -= 4 * mm
                if "Multicaixa" in forma_pagamento:
                    c.drawString(3 * mm, y, "Cartao de debito:")
                else:
                    c.drawString(3 * mm, y, "Transferencia:")
                c.drawRightString(largura - 3 * mm, y, _fmt_sem_kz(v_seg))
                y -= 4 * mm
                if ref_multicaixa:
                    c.drawString(5 * mm, y, f"Cartao Nr {ref_multicaixa}")
                    y -= 4 * mm

        c.drawString(3 * mm, y, "IVA:")
        c.drawRightString(largura - 3 * mm, y, _fmt_sem_kz(iva))
        y -= 5 * mm

        c.setFont("Helvetica-Bold", 9)
        c.drawString(3 * mm, y, "TOTAL:")
        c.drawRightString(largura - 3 * mm, y, f"Kz {_fmt_sem_kz(total)}")
        y -= 8 * mm

        c.setFont("Helvetica", 7)
        c.drawCentredString(largura/2, y, "Obrigado pela preferencia!")
        y -= 4 * mm
        c.drawCentredString(largura/2, y, "JAM Soft")

    else:
        # ===== FORMATO A4 =====
        if logo_path and os.path.exists(logo_path):
            try:
                from reportlab.lib.utils import ImageReader
                logo_img = ImageReader(logo_path)
                c.drawImage(logo_img, 20 * mm, y - 22 * mm,
                             width=30 * mm, height=25 * mm,
                             preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

        c.setFont("Helvetica-Bold", 16)
        c.drawString(55 * mm, y, emp_nome)
        y -= 6 * mm
        c.setFont("Helvetica", 9)
        c.drawString(55 * mm, y, f"NIF: {emp_nif}")
        y -= 4 * mm
        c.drawString(55 * mm, y, f"{emp_end}")
        y -= 4 * mm
        c.drawString(55 * mm, y, f"Tel: {emp_tel} | Email: {emp_email}")
        y -= 12 * mm

        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(largura/2, y, f"{tipo}  {numero}")
        y -= 6 * mm
        c.setFont("Helvetica", 9)
        c.drawCentredString(largura/2, y, f"Data: {data}")
        y -= 5 * mm

        # AGT: Aviso
        c.setFont("Helvetica-Bold", 9)
        c.setFillColorRGB(0.65, 0.10, 0.10)
        c.drawCentredString(largura/2, y, AVISO_FISCAL_LOCAL)
        c.setFillColorRGB(0, 0, 0)
        y -= 5 * mm

        c.setFont("Helvetica", 8)
        c.drawCentredString(largura/2, y, AVISO_AGT_PROVISORIO)
        y -= 5 * mm

        # QR Code (debug)
        print(f"[DEBUG-A4] qr_url = {qr_url[:60] if qr_url else 'VAZIO'}")
        print(f"[DEBUG-A4] y = {y:.1f} pontos ({y/2.8346:.1f} mm)")
        resultado_qr = _desenhar_qr(c, qr_url, largura, y + 2 * mm, tamanho_mm=25, offset_direita_mm=50)
        print(f"[DEBUG-A4] QR desenhado? {resultado_qr}")

        # Hash
        if hash_doc:
            c.setFont("Helvetica", 7)
            c.drawString(20 * mm, y, f"Hash: {hash_doc}")
            y -= 5 * mm
        else:
            y -= 5 * mm

        # Cliente
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "Dados do Cliente:")
        y -= 6 * mm
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, f"Nome: {cli_nome or 'Consumidor Final'}")
        y -= 5 * mm
        c.drawString(20 * mm, y, f"NIF: {cli_nif or '-'}")
        y -= 5 * mm
        c.drawString(20 * mm, y, f"Endereco: {cli_end or '-'}")
        y -= 10 * mm

        # Tabela
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20 * mm, y, "Descricao")
        c.drawString(90 * mm, y, "Qtd")
        c.drawString(105 * mm, y, "Preco")
        c.drawString(125 * mm, y, "Desc.")
        c.drawString(145 * mm, y, "IVA")
        c.drawRightString(largura - 20 * mm, y, "Subtotal")
        y -= 3 * mm
        c.line(20 * mm, y, largura - 20 * mm, y)
        y -= 5 * mm

        c.setFont("Helvetica", 9)
        for item in itens:
            if len(item) >= 9:
                desc, qtd, preco, isento, taxa, valor_iva, sub, desc_p, desc_v = item
            else:
                desc, qtd, preco, isento, taxa, valor_iva, sub = item
                desc_p, desc_v = 0, 0

            c.drawString(20 * mm, y, str(desc)[:30])
            c.drawString(90 * mm, y, str(qtd))
            c.drawString(105 * mm, y, formatar_kz(preco))
            c.drawString(125 * mm, y, f"{desc_p:.0f}%" if desc_p and desc_p > 0 else "-")
            c.drawString(145 * mm, y, "Isento" if isento else f"{int(taxa*100)}%")
            c.drawRightString(largura - 20 * mm, y, formatar_kz(sub))
            y -= 5 * mm

        y -= 3 * mm
        c.line(20 * mm, y, largura - 20 * mm, y)
        y -= 8 * mm

        c.setFont("Helvetica", 10)
        c.drawString(120 * mm, y, "Subtotal:")
        c.drawRightString(largura - 20 * mm, y, _fmt_sem_kz(subtotal))
        y -= 5 * mm

        if forma_pagamento:
            if forma_pagamento == "Dinheiro":
                c.drawString(120 * mm, y, "Dinheiro:")
                c.drawRightString(largura - 20 * mm, y, _fmt_sem_kz(total))
                y -= 5 * mm
            elif forma_pagamento == "Multicaixa":
                c.drawString(120 * mm, y, "Cartao de debito:")
                c.drawRightString(largura - 20 * mm, y, _fmt_sem_kz(total))
                y -= 5 * mm
                if ref_multicaixa:
                    c.setFont("Helvetica", 9)
                    c.drawString(120 * mm, y, f"Cartao Nr {ref_multicaixa}")
                    y -= 5 * mm
                    c.setFont("Helvetica", 10)
            elif forma_pagamento == "Transferencia":
                c.drawString(120 * mm, y, "Transferencia:")
                c.drawRightString(largura - 20 * mm, y, _fmt_sem_kz(total))
                y -= 5 * mm
                if ref_multicaixa:
                    c.setFont("Helvetica", 9)
                    c.drawString(120 * mm, y, f"Ref. Nr {ref_multicaixa}")
                    y -= 5 * mm
                    c.setFont("Helvetica", 10)
            elif "Misto" in forma_pagamento:
                v_din = valor_dinheiro or 0
                v_seg = valor_segunda or 0
                c.drawString(120 * mm, y, "Dinheiro:")
                c.drawRightString(largura - 20 * mm, y, _fmt_sem_kz(v_din))
                y -= 5 * mm
                if "Multicaixa" in forma_pagamento:
                    c.drawString(120 * mm, y, "Cartao de debito:")
                else:
                    c.drawString(120 * mm, y, "Transferencia:")
                c.drawRightString(largura - 20 * mm, y, _fmt_sem_kz(v_seg))
                y -= 5 * mm
                if ref_multicaixa:
                    c.setFont("Helvetica", 9)
                    c.drawString(120 * mm, y, f"Cartao Nr {ref_multicaixa}")
                    y -= 5 * mm
                    c.setFont("Helvetica", 10)

        c.drawString(120 * mm, y, "IVA:")
        c.drawRightString(largura - 20 * mm, y, _fmt_sem_kz(iva))
        y -= 8 * mm

        c.setFont("Helvetica-Bold", 13)
        c.drawString(120 * mm, y, "TOTAL:")
        c.drawRightString(largura - 20 * mm, y, f"Kz {_fmt_sem_kz(total)}")
        y -= 15 * mm

        # Rodape
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(largura/2, 20 * mm, "Obrigado pela preferencia!")
        c.drawCentredString(largura/2, 15 * mm, f"{emp_nome} | NIF: {emp_nif}")
        c.drawCentredString(largura/2, 10 * mm, "Processado por JAM Soft")

    c.save()
    return caminho_saida, None


# ============================================================
# ============ PDF DE PROFORMA ===============================
# ============================================================

def gerar_pdf_proforma(proforma_id, formato="A4", caminho_saida=None):
    """Gera o PDF de uma Factura Proforma."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas as pdf_canvas
    except ImportError:
        return None, "reportlab nao instalado."

    from database import (buscar_proforma_por_id, listar_itens_factura,
                           obter_empresa, obter_itens_factura_com_desconto)

    p = buscar_proforma_por_id(proforma_id)
    if not p:
        return None, "Proforma nao encontrada."

    (pid, numero, serie, tipo, data, cli_nome, cli_nif, cli_end,
     subtotal, iva, total, estado, motivo, forma_pagamento,
     ref_multicaixa, validade) = p

    emp = obter_empresa()
    emp_nome = emp[1] if emp else "Farmacia"
    emp_nif = emp[2] if emp else "-"
    emp_end = emp[3] if emp else "-"
    emp_tel = emp[4] if emp else "-"
    emp_email = emp[5] if emp else "-"

    logo_path = None
    if emp and len(emp) > 9:
        logo_path = emp[9]

    try:
        itens = obter_itens_factura_com_desconto(proforma_id)
    except Exception:
        itens = listar_itens_factura(proforma_id)

    garantir_pasta()

    if not caminho_saida:
        nome_seguro = numero.replace("/", "_").replace(" ", "_")
        sufixo = "A4" if formato == "A4" else "TERMICA"
        caminho_saida = os.path.join(PASTA_FACTURAS,
                                       f"proforma_{nome_seguro}_{sufixo}.pdf")

    if formato == "TERMICA":
        altura = 180 * mm + (len(itens) * 12 * mm)
        page_size = (80 * mm, altura)
    else:
        page_size = A4

    c = pdf_canvas.Canvas(caminho_saida, pagesize=page_size)
    largura, altura = page_size

    y = altura - 15 * mm

    if formato == "A4":
        if logo_path and os.path.exists(logo_path):
            try:
                from reportlab.lib.utils import ImageReader
                logo_img = ImageReader(logo_path)
                c.drawImage(logo_img, 20 * mm, y - 22 * mm,
                             width=30 * mm, height=25 * mm,
                             preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

        c.setFont("Helvetica-Bold", 16)
        c.drawString(55 * mm, y, emp_nome)
        y -= 6 * mm
        c.setFont("Helvetica", 9)
        c.drawString(55 * mm, y, f"NIF: {emp_nif}")
        y -= 4 * mm
        c.drawString(55 * mm, y, f"{emp_end}")
        y -= 4 * mm
        c.drawString(55 * mm, y, f"Tel: {emp_tel} | Email: {emp_email}")
        y -= 12 * mm

        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(largura/2, y, f"FACTURA PROFORMA  {numero}")
        y -= 6 * mm
        c.setFont("Helvetica", 9)
        c.drawCentredString(largura/2, y, f"Data: {data}")
        y -= 5 * mm
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(largura/2, y, f"Valido ate: {validade}")
        y -= 10 * mm

        c.setFillColorRGB(0.99, 0.95, 0.78)
        c.rect(20 * mm, y - 6 * mm, largura - 40 * mm, 12 * mm, fill=1, stroke=0)
        c.setFillColorRGB(0.55, 0.25, 0.05)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(largura/2, y - 1 * mm,
                              "DOCUMENTO NAO FISCAL - Valido por 7 dias")
        c.setFillColorRGB(0, 0, 0)
        y -= 18 * mm

        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "Dados do Cliente:")
        y -= 6 * mm
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, f"Nome: {cli_nome or 'Consumidor Final'}")
        y -= 5 * mm
        c.drawString(20 * mm, y, f"NIF: {cli_nif or '-'}")
        y -= 5 * mm
        c.drawString(20 * mm, y, f"Endereco: {cli_end or '-'}")
        y -= 10 * mm

        c.setFont("Helvetica-Bold", 9)
        c.drawString(20 * mm, y, "Descricao")
        c.drawString(90 * mm, y, "Qtd")
        c.drawString(105 * mm, y, "Preco")
        c.drawString(125 * mm, y, "Desc.")
        c.drawString(145 * mm, y, "IVA")
        c.drawRightString(largura - 20 * mm, y, "Subtotal")
        y -= 3 * mm
        c.line(20 * mm, y, largura - 20 * mm, y)
        y -= 5 * mm

        c.setFont("Helvetica", 9)
        for item in itens:
            if len(item) >= 9:
                desc, qtd, preco, isento, taxa, valor_iva, sub, desc_p, desc_v = item
            else:
                desc, qtd, preco, isento, taxa, valor_iva, sub = item
                desc_p, desc_v = 0, 0

            c.drawString(20 * mm, y, str(desc)[:30])
            c.drawString(90 * mm, y, str(qtd))
            c.drawString(105 * mm, y, formatar_kz(preco))
            c.drawString(125 * mm, y, f"{desc_p:.0f}%" if desc_p and desc_p > 0 else "-")
            c.drawString(145 * mm, y, "Isento" if isento else f"{int(taxa*100)}%")
            c.drawRightString(largura - 20 * mm, y, formatar_kz(sub))
            y -= 5 * mm

        y -= 3 * mm
        c.line(20 * mm, y, largura - 20 * mm, y)
        y -= 8 * mm

        c.setFont("Helvetica", 10)
        c.drawString(120 * mm, y, "Subtotal:")
        c.drawRightString(largura - 20 * mm, y, _fmt_sem_kz(subtotal))
        y -= 5 * mm

        c.setFont("Helvetica-Oblique", 10)
        c.drawString(120 * mm, y, "(Sem pagamento associado)")
        y -= 5 * mm
        c.setFont("Helvetica", 10)

        c.drawString(120 * mm, y, "IVA:")
        c.drawRightString(largura - 20 * mm, y, _fmt_sem_kz(iva))
        y -= 8 * mm

        c.setFont("Helvetica-Bold", 13)
        c.drawString(120 * mm, y, "TOTAL:")
        c.drawRightString(largura - 20 * mm, y, f"Kz {_fmt_sem_kz(total)}")
        y -= 15 * mm

        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(largura/2, 20 * mm,
                              "Este documento nao serve como factura fiscal.")
        c.drawCentredString(largura/2, 15 * mm,
                              f"{emp_nome} | NIF: {emp_nif}")
        c.drawCentredString(largura/2, 10 * mm,
                              "Processado por JAM Soft")

    else:
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(largura/2, y, emp_nome[:30])
        y -= 4 * mm
        c.setFont("Helvetica", 7)
        c.drawCentredString(largura/2, y, f"NIF: {emp_nif}")
        y -= 3 * mm
        c.drawCentredString(largura/2, y, f"Tel: {emp_tel}")
        y -= 5 * mm

        c.drawCentredString(largura/2, y, "-" * 40)
        y -= 5 * mm

        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(largura/2, y, "FACTURA PROFORMA")
        y -= 4 * mm
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(largura/2, y, numero)
        y -= 4 * mm
        c.setFont("Helvetica", 7)
        c.drawCentredString(largura/2, y, f"Data: {data}")
        y -= 3 * mm
        c.drawCentredString(largura/2, y, f"Valido ate: {validade}")
        y -= 5 * mm

        c.drawCentredString(largura/2, y, "-" * 40)
        y -= 4 * mm

        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(largura/2, y, "DOCUMENTO NAO FISCAL")
        y -= 5 * mm

        c.drawCentredString(largura/2, y, "-" * 40)
        y -= 5 * mm

        c.setFont("Helvetica-Bold", 7)
        c.drawString(3 * mm, y, "Cliente:")
        y -= 4 * mm
        c.setFont("Helvetica", 7)
        c.drawString(3 * mm, y, (cli_nome or "Consumidor Final")[:38])
        y -= 4 * mm
        if cli_nif:
            c.drawString(3 * mm, y, f"NIF: {cli_nif}")
            y -= 4 * mm

        c.drawCentredString(largura/2, y, "-" * 40)
        y -= 5 * mm

        c.setFont("Helvetica-Bold", 7)
        c.drawString(3 * mm, y, "Item")
        c.drawRightString(largura - 3 * mm, y, "Total")
        y -= 4 * mm
        c.setFont("Helvetica", 7)

        for item in itens:
            if len(item) >= 9:
                desc, qtd, preco, isento, taxa, valor_iva, sub, desc_p, desc_v = item
            else:
                desc, qtd, preco, isento, taxa, valor_iva, sub = item

            c.drawString(3 * mm, y, str(desc)[:22])
            y -= 3 * mm
            c.drawString(5 * mm, y, f"{qtd} x {formatar_kz(preco)}")
            c.drawRightString(largura - 3 * mm, y, formatar_kz(sub))
            y -= 4 * mm

        c.drawCentredString(largura/2, y, "-" * 40)
        y -= 5 * mm

        c.setFont("Helvetica", 7)
        c.drawString(3 * mm, y, "Subtotal:")
        c.drawRightString(largura - 3 * mm, y, _fmt_sem_kz(subtotal))
        y -= 4 * mm

        c.drawString(3 * mm, y, "IVA:")
        c.drawRightString(largura - 3 * mm, y, _fmt_sem_kz(iva))
        y -= 5 * mm

        c.setFont("Helvetica-Bold", 9)
        c.drawString(3 * mm, y, "TOTAL:")
        c.drawRightString(largura - 3 * mm, y, f"Kz {_fmt_sem_kz(total)}")
        y -= 8 * mm

        c.setFont("Helvetica", 7)
        c.drawCentredString(largura/2, y, "(Sem pagamento)")
        y -= 5 * mm
        c.drawCentredString(largura/2, y, "Obrigado!")
        y -= 4 * mm
        c.drawCentredString(largura/2, y, "JAM Soft")

    c.save()
    return caminho_saida, None


# ============================================================
# ============ PDF DE DEVOLUCAO ==============================
# ============================================================

def gerar_pdf_devolucao(devolucao_id, formato="A4", caminho_saida=None):
    """Gera o PDF de uma devolucao de dinheiro."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas as pdf_canvas
    except ImportError:
        return None, "reportlab nao instalado."

    from database import obter_devolucao

    dev = obter_devolucao(devolucao_id)
    if not dev:
        return None, "Devolucao nao encontrada."

    emp = obter_empresa()
    emp_nome = emp[1] if emp else "Farmacia"
    emp_nif = emp[2] if emp else "-"
    emp_end = emp[3] if emp else "-"
    emp_tel = emp[4] if emp else "-"
    emp_email = emp[5] if emp else "-"

    logo_path = None
    if emp and len(emp) > 9:
        logo_path = emp[9]

    pasta = "devolucoes"
    if not os.path.exists(pasta):
        os.makedirs(pasta)

    if not caminho_saida:
        nome_seguro = dev[1].replace("/", "_").replace(" ", "_")
        sufixo = "A4" if formato == "A4" else "TERMICA"
        caminho_saida = os.path.join(pasta, f"{nome_seguro}_{sufixo}.pdf")

    if formato == "TERMICA":
        page_size = (80 * mm, 200 * mm)
    else:
        page_size = A4

    c = pdf_canvas.Canvas(caminho_saida, pagesize=page_size)
    largura, altura = page_size

    y = altura - 15 * mm

    if formato == "TERMICA":
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(largura/2, y, emp_nome[:30])
        y -= 5 * mm
        c.setFont("Helvetica", 7)
        c.drawCentredString(largura/2, y, f"NIF: {emp_nif}")
        y -= 4 * mm
        c.drawCentredString(largura/2, y, emp_end[:35])
        y -= 4 * mm
        c.drawCentredString(largura/2, y, f"Tel: {emp_tel}")
        y -= 6 * mm

        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(largura/2, y, "COMPROVATIVO DE DEVOLUCAO")
        y -= 5 * mm
        c.setFont("Helvetica", 7)
        c.drawCentredString(largura/2, y, f"Data: {dev[2]} {dev[3]}")
        y -= 3 * mm
        c.drawCentredString(largura/2, y, f"{dev[1]}")
        y -= 5 * mm

        c.drawCentredString(largura/2, y, "-" * 40)
        y -= 5 * mm

        c.setFont("Helvetica-Bold", 7)
        c.drawString(3 * mm, y, "PRODUTO:")
        y -= 4 * mm
        c.setFont("Helvetica", 7)
        c.drawString(3 * mm, y, str(dev[7])[:40])
        y -= 4 * mm
        c.drawString(3 * mm, y, f"Qtd: {dev[8]} x {formatar_kz(dev[9])}")
        y -= 4 * mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(3 * mm, y, "TOTAL DEVOLVIDO:")
        c.drawRightString(largura - 3 * mm, y, formatar_kz(dev[10]))
        y -= 5 * mm

        c.setFont("Helvetica", 7)
        c.drawString(3 * mm, y, "MOTIVO:")
        y -= 4 * mm
        c.drawString(3 * mm, y, str(dev[11])[:38])
        y -= 6 * mm

        c.drawString(3 * mm, y, "Factura original:")
        y -= 4 * mm
        c.drawString(3 * mm, y, str(dev[5] or "-")[:38])
        y -= 6 * mm

        c.drawString(3 * mm, y, "Autorizado por:")
        y -= 4 * mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(3 * mm, y, str(dev[12])[:38])
        y -= 6 * mm

        c.setFont("Helvetica", 7)
        c.drawString(3 * mm, y, "Operador:")
        y -= 4 * mm
        c.drawString(3 * mm, y, str(dev[15] or "-")[:38])
        y -= 8 * mm

        c.drawCentredString(largura/2, y, "-" * 40)
        y -= 5 * mm
        c.drawCentredString(largura/2, y, "Assinatura do Cliente:")
        y -= 8 * mm
        c.drawCentredString(largura/2, y, "_______________________")
        y -= 6 * mm
        c.setFont("Helvetica-Oblique", 6)
        c.drawCentredString(largura/2, y, "Documento nao fiscal")
        y -= 4 * mm
        c.drawCentredString(largura/2, y, "Processado por JAM Soft")

    else:
        if logo_path and os.path.exists(logo_path):
            try:
                from reportlab.lib.utils import ImageReader
                logo_img = ImageReader(logo_path)
                c.drawImage(logo_img, 20 * mm, y - 22 * mm,
                             width=30 * mm, height=25 * mm,
                             preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

        c.setFont("Helvetica-Bold", 16)
        c.drawString(55 * mm, y, emp_nome)
        y -= 6 * mm
        c.setFont("Helvetica", 9)
        c.drawString(55 * mm, y, f"NIF: {emp_nif}")
        y -= 4 * mm
        c.drawString(55 * mm, y, emp_end)
        y -= 4 * mm
        c.drawString(55 * mm, y, f"Tel: {emp_tel} | Email: {emp_email}")
        y -= 12 * mm

        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(largura/2, y, "COMPROVATIVO DE DEVOLUCAO")
        y -= 6 * mm
        c.setFont("Helvetica", 9)
        c.drawCentredString(largura/2, y, f"Referencia: {dev[1]}")
        y -= 5 * mm
        c.drawCentredString(largura/2, y, f"Data: {dev[2]} {dev[3]}")
        y -= 5 * mm

        c.setFillColorRGB(0.99, 0.95, 0.78)
        c.rect(20 * mm, y - 6 * mm, largura - 40 * mm, 12 * mm, fill=1, stroke=0)
        c.setFillColorRGB(0.55, 0.25, 0.05)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(largura/2, y - 1 * mm, "DOCUMENTO NAO FISCAL")
        c.setFillColorRGB(0, 0, 0)
        y -= 18 * mm

        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "Produto devolvido:")
        y -= 7 * mm
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, f"Nome: {dev[7]}")
        y -= 5 * mm
        c.drawString(20 * mm, y, f"Quantidade: {dev[8]}")
        y -= 5 * mm
        c.drawString(20 * mm, y, f"Valor unitario: {formatar_kz(dev[9])}")
        y -= 5 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, f"TOTAL DEVOLVIDO: {formatar_kz(dev[10])}")
        y -= 10 * mm

        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "Motivo:")
        y -= 6 * mm
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, f"{dev[11]}")
        y -= 10 * mm

        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "Factura original:")
        y -= 6 * mm
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, f"{dev[5] or '-'}")
        y -= 10 * mm

        y -= 10 * mm
        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, y, "Autorizado por:")
        c.drawString(120 * mm, y, "Operador:")
        y -= 6 * mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20 * mm, y, dev[12])
        c.drawString(120 * mm, y, dev[15] or "-")
        y -= 15 * mm

        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, y, "_______________________")
        c.drawString(120 * mm, y, "_______________________")
        y -= 5 * mm
        c.setFont("Helvetica", 8)
        c.drawString(20 * mm, y, "Assinatura Autorizador")
        c.drawString(120 * mm, y, "Assinatura Operador")
        y -= 20 * mm

        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, y, "Assinatura do Cliente:")
        y -= 15 * mm
        c.drawString(20 * mm, y, "_______________________________________")

        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(largura/2, 20 * mm, "Documento nao fiscal")
        c.drawCentredString(largura/2, 15 * mm, f"{emp_nome} | NIF: {emp_nif}")
        c.drawCentredString(largura/2, 10 * mm, "Processado por JAM Soft")

    c.save()
    return caminho_saida, None


# ============================================================
# ============ ABRIR GAVETA DE DINHEIRO ======================
# ============================================================

def abrir_gaveta():
    """Envia o comando ESC/POS para abrir a gaveta."""
    comando = bytes([0x1B, 0x70, 0x00, 0x19, 0xFA])

    try:
        import win32print
        nome_impressora = win32print.GetDefaultPrinter()
        if not nome_impressora:
            return False, "Sem impressora por omissao"

        hprinter = win32print.OpenPrinter(nome_impressora)
        try:
            win32print.StartDocPrinter(hprinter, 1, ("Abrir Gaveta", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, comando)
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
        finally:
            win32print.ClosePrinter(hprinter)

        print(f"[Gaveta] Comando enviado para: {nome_impressora}")
        return True, f"Gaveta aberta via {nome_impressora}"
    except ImportError:
        pass
    except Exception as e:
        print(f"[Gaveta] Erro win32print: {e}")

    try:
        import serial
        for porta in ["COM1", "COM2", "COM3", "COM4"]:
            try:
                ser = serial.Serial(porta, 9600, timeout=0.5)
                ser.write(comando)
                ser.close()
                print(f"[Gaveta] Comando enviado via {porta}")
                return True, f"Gaveta aberta via {porta}"
            except Exception:
                continue
    except ImportError:
        pass

    return False, "Nao foi possivel abrir a gaveta"


# ============================================================
# ============ JANELA DE IMPRESSAO ===========================
# ============================================================

def abrir_impressao(utilizador_logado):
    janela = Toplevel()
    janela.title("JAM Soft - Impressao de Facturas")
    janela.geometry("1000x700")
    janela.configure(bg=COR_FUNDO)

    header = Frame(janela, bg=COR_HEADER, height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Impressao de Facturas", font=("Arial", 18, "bold"),
          bg=COR_HEADER, fg="white").pack(pady=20)

    info = Frame(janela, bg=COR_CARD, highlightthickness=1, highlightbackground="#fecaca")
    info.pack(fill=X, padx=15, pady=15)
    Label(info, text="Selecione uma factura e escolha o formato (A4 ou Termica 80mm).",
          font=("Arial", 10, "italic"), bg=COR_CARD, fg=COR_TEXTO).pack(padx=15, pady=10)

    frame_tab = Frame(janela, bg=COR_FUNDO)
    frame_tab.pack(fill=BOTH, expand=True, padx=15, pady=10)

    colunas = ("ID", "Numero", "Data", "Cliente", "Total", "Estado")
    tree = ttk.Treeview(frame_tab, columns=colunas, show="headings", height=15)
    for col in colunas:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(fill=BOTH, expand=True, side=LEFT)

    sb = Scrollbar(frame_tab, orient="vertical", command=tree.yview)
    sb.pack(side=RIGHT, fill=Y)
    tree.configure(yscrollcommand=sb.set)

    def carregar():
        for i in tree.get_children():
            tree.delete(i)
        for f in listar_facturas(100):
            fid, numero, tipo, data, cliente, total, estado = f
            tag = "anulada" if estado == "ANULADA" else ""
            tree.insert("", END, values=(fid, numero, data,
                                          cliente or "Consumidor Final",
                                          formatar_kz(total), estado), tags=(tag,))
        tree.tag_configure("anulada", background="#fee2e2", foreground="#991b1b")

    carregar()

    def gerar(formato):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma factura.")
            return

        fid = tree.item(sel[0])["values"][0]

        caminho, erro = gerar_pdf_factura(fid, formato=formato)

        if erro:
            messagebox.showerror("Erro", erro)
            return

        registar_auditoria(utilizador_logado["id"], utilizador_logado["nome"],
                            "GERAR PDF", f"Factura ID {fid} | {formato}")

        if messagebox.askyesno("PDF Gerado",
            f"PDF criado com sucesso:\n\n{os.path.basename(caminho)}\n\n"
            "Abrir o ficheiro agora?"):
            try:
                os.startfile(caminho)
            except Exception:
                messagebox.showinfo("Info", f"Ficheiro guardado em:\n{caminho}")

    def abrir_pasta():
        garantir_pasta()
        caminho_abs = os.path.abspath(PASTA_FACTURAS)
        try:
            os.startfile(caminho_abs)
        except Exception:
            messagebox.showinfo("Info", f"Pasta: {caminho_abs}")

    def ver_impressoras():
        imps = listar_impressoras()
        if imps:
            msg = "Impressoras instaladas no sistema:\n\n"
            for i, imp in enumerate(imps, 1):
                msg += f"{i}. {imp}\n"
            messagebox.showinfo("Impressoras", msg)
        else:
            messagebox.showinfo("Impressoras",
                "Nao foi possivel detectar impressoras.\n\n"
                "O PDF sera sempre gerado e guardado na pasta 'facturas'.")

    frame_btn = Frame(janela, bg=COR_FUNDO)
    frame_btn.pack(pady=10)

    estilo = {"font": ("Arial", 11, "bold"), "width": 22, "height": 2,
              "bd": 0, "cursor": "hand2", "fg": "white"}

    Button(frame_btn, text="Gerar A4", bg=COR_PRIMARIA,
           command=lambda: gerar("A4"), **estilo).grid(row=0, column=0, padx=5, pady=5)
    Button(frame_btn, text="Gerar Termica 80mm", bg=COR_VERDE,
           command=lambda: gerar("TERMICA"), **estilo).grid(row=0, column=1, padx=5, pady=5)
    Button(frame_btn, text="Abrir Pasta Facturas", bg="#0891b2",
           command=abrir_pasta, **estilo).grid(row=1, column=0, padx=5, pady=5)
    Button(frame_btn, text="Ver Impressoras", bg="#7c3aed",
           command=ver_impressoras, **estilo).grid(row=1, column=1, padx=5, pady=5)
    Button(frame_btn, text="Actualizar Lista", bg="#4b5563",
           command=carregar, **estilo).grid(row=2, column=0, padx=5, pady=5)

    

# ============================================================
# ============ COMPROVATIVO DE DEPOSITO ======================
# ============================================================

def gerar_pdf_comprovativo_deposito(deposito_id, formato="A4", caminho_saida=None):
    """
    Gera o PDF do comprovativo de deposito bancario.
    formato: "A4" ou "TERMICA"
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas as pdf_canvas
    except ImportError:
        return None, "reportlab nao instalado."

    # ─── Buscar deposito ───
    from database import obter_deposito, obter_empresa

    d = obter_deposito(deposito_id)
    if not d:
        return None, "Deposito nao encontrado."

    # Ordem: id, referencia, data, hora, valor, banco, comp, obs,
    #        turno_id, ger_id, ger_nome, estado, aprov_por,
    #        data_aprov, criado_em, uuid, terminal_id, farmacia_id, sincronizado
    (did, referencia, data, hora, valor, banco, comp, obs,
     turno_id, ger_id, ger_nome, estado, aprov_por,
     data_aprov, criado_em) = d[:15]

    # ─── Empresa ───
    emp = obter_empresa()
    emp_nome = emp[1] if emp else "Farmacia"
    emp_nif = emp[2] if emp else "-"
    emp_end = emp[3] if emp else "-"
    emp_tel = emp[4] if emp else "-"
    emp_email = emp[5] if emp else "-"

    # ─── Logo ───
    logo_path = None
    try:
        from pathlib import Path
        lp = Path(__file__).parent / "logos" / "logo_horizontal_medio.png"
        if lp.exists():
            logo_path = str(lp)
    except Exception:
        pass

    garantir_pasta()

    if not caminho_saida:
        nome_seguro = referencia.replace("/", "_").replace(" ", "_")
        caminho_saida = os.path.join(PASTA_FACTURAS, f"Comprovativo_{nome_seguro}.pdf")

    # ─── Configuracao de pagina ───
    if formato == "TERMICA":
        altura = 200 * mm
        page_size = (80 * mm, altura)
    else:
        page_size = A4

    c = pdf_canvas.Canvas(caminho_saida, pagesize=page_size)
    largura, altura = page_size

    y = altura - 15 * mm

    # ══════════════════════════════════════════════════════
    # ============ FORMATO TERMICA (80mm) ============
    # ══════════════════════════════════════════════════════
    if formato == "TERMICA":
        # Logo
        if logo_path and os.path.exists(logo_path):
            try:
                from reportlab.lib.utils import ImageReader
                logo_img = ImageReader(logo_path)
                logo_w = 40 * mm
                logo_h = 15 * mm
                c.drawImage(logo_img, (largura - logo_w) / 2, y - logo_h,
                             width=logo_w, height=logo_h,
                             preserveAspectRatio=True, mask='auto')
                y -= logo_h + 3 * mm
            except Exception:
                pass

        # Cabecalho
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(largura / 2, y, emp_nome[:30])
        y -= 4 * mm
        c.setFont("Helvetica", 7)
        c.drawCentredString(largura / 2, y, f"NIF: {emp_nif}")
        y -= 3.5 * mm
        c.drawCentredString(largura / 2, y, emp_end[:40])
        y -= 3.5 * mm
        c.drawCentredString(largura / 2, y, f"Tel: {emp_tel}")
        y -= 5 * mm

        c.drawCentredString(largura / 2, y, "=" * 40)
        y -= 5 * mm

        # Titulo
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(largura / 2, y, "COMPROVATIVO DE DEPOSITO")
        y -= 6 * mm

        # Referencia destacada
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(largura / 2, y, referencia)
        y -= 6 * mm

        c.drawCentredString(largura / 2, y, "-" * 40)
        y -= 5 * mm

        # Dados
        c.setFont("Helvetica", 8)
        c.drawString(4 * mm, y, "Data:")
        c.drawRightString(largura - 4 * mm, y, f"{data} {hora}")
        y -= 4 * mm

        c.drawString(4 * mm, y, "Banco:")
        c.drawRightString(largura - 4 * mm, y, str(banco or "-"))
        y -= 4 * mm

        if comp:
            c.drawString(4 * mm, y, "Comprovante:")
            c.drawRightString(largura - 4 * mm, y, str(comp))
            y -= 4 * mm

        c.drawString(4 * mm, y, "Gerente:")
        c.drawRightString(largura - 4 * mm, y, str(ger_nome or "-")[:20])
        y -= 4 * mm

        c.drawString(4 * mm, y, "Estado:")
        c.drawRightString(largura - 4 * mm, y, str(estado or "-"))
        y -= 5 * mm

        c.drawCentredString(largura / 2, y, "-" * 40)
        y -= 5 * mm

        # Valor em destaque
        c.setFont("Helvetica-Bold", 11)
        c.drawString(4 * mm, y, "VALOR:")
        c.drawRightString(largura - 4 * mm, y, formatar_kz(valor))
        y -= 8 * mm

        # Aviso importante
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(largura / 2, y, "IMPORTANTE:")
        y -= 3.5 * mm
        c.setFont("Helvetica", 6.5)
        c.drawCentredString(largura / 2, y, "Ao depositar no banco, escreva")
        y -= 3 * mm
        c.drawCentredString(largura / 2, y, "a referencia na descricao:")
        y -= 4 * mm
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(largura / 2, y, referencia)
        y -= 8 * mm

        if obs:
            c.setFont("Helvetica-Oblique", 6.5)
            c.drawCentredString(largura / 2, y, f"Obs: {obs[:40]}")
            y -= 6 * mm

        c.setFont("Helvetica", 6.5)
        c.drawCentredString(largura / 2, y, "-" * 40)
        y -= 5 * mm
        c.drawCentredString(largura / 2, y, "Assinatura do gerente:")
        y -= 8 * mm
        c.drawCentredString(largura / 2, y, "_" * 30)
        y -= 6 * mm

        c.setFont("Helvetica", 5.5)
        c.drawCentredString(largura / 2, y, "JAM Soft © 2026")

    # ══════════════════════════════════════════════════════
    # ============ FORMATO A4 ============
    # ══════════════════════════════════════════════════════
    else:
        # Logo horizontal
        if logo_path and os.path.exists(logo_path):
            try:
                from reportlab.lib.utils import ImageReader
                logo_img = ImageReader(logo_path)
                logo_w = 70 * mm
                logo_h = 22 * mm
                c.drawImage(logo_img, (largura - logo_w) / 2, y - logo_h,
                             width=logo_w, height=logo_h,
                             preserveAspectRatio=True, mask='auto')
                y -= logo_h + 5 * mm
            except Exception:
                pass
        else:
            c.setFont("Helvetica-Bold", 20)
            c.drawCentredString(largura / 2, y, "JAM Soft")
            y -= 8 * mm

        # Linha roxa decorativa
        c.setStrokeColorRGB(0.49, 0.23, 0.93)
        c.setLineWidth(2)
        c.line(20 * mm, y, largura - 20 * mm, y)
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1)
        y -= 12 * mm

        # Titulo
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(largura / 2, y, "COMPROVATIVO DE DEPOSITO BANCARIO")
        y -= 10 * mm

        # Referencia grande
        c.setFillColorRGB(0.49, 0.23, 0.93)
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(largura / 2, y, referencia)
        c.setFillColorRGB(0, 0, 0)
        y -= 12 * mm

        # Dados da farmacia
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(largura / 2, y, emp_nome)
        y -= 5 * mm
        c.setFont("Helvetica", 10)
        c.drawCentredString(largura / 2, y, f"NIF: {emp_nif}")
        y -= 4.5 * mm
        c.drawCentredString(largura / 2, y, emp_end)
        y -= 4.5 * mm
        c.drawCentredString(largura / 2, y, f"Tel: {emp_tel}  |  Email: {emp_email}")
        y -= 15 * mm

        # Caixa de dados do deposito
        dados = [
            ("Referencia:", referencia),
            ("Data:", f"{data}  {hora}"),
            ("Banco:", banco or "-"),
            ("Numero do comprovante:", comp or "(nao preenchido)"),
            ("Valor:", formatar_kz(valor)),
            ("Gerente:", ger_nome or "-"),
            ("Estado:", estado or "-"),
        ]
        if obs:
            dados.append(("Observacoes:", obs))

        # Desenhar tabela manual
        linha_h = 10 * mm
        col1_x = 25 * mm
        col2_x = 75 * mm
        tabela_y = y

        for label, valor_txt in dados:
            # Fundo cinza claro
            c.setFillColorRGB(0.95, 0.96, 0.98)
            c.rect(20 * mm, tabela_y - linha_h + 2 * mm, largura - 40 * mm,
                    linha_h - 1 * mm, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)

            # Borda
            c.setStrokeColorRGB(0.8, 0.8, 0.85)
            c.rect(20 * mm, tabela_y - linha_h + 2 * mm, largura - 40 * mm,
                    linha_h - 1 * mm, fill=0, stroke=1)
            c.setStrokeColorRGB(0, 0, 0)

            # Label
            c.setFont("Helvetica-Bold", 10)
            c.drawString(col1_x, tabela_y - linha_h + 5 * mm, label)

            # Valor
            c.setFont("Helvetica", 10)
            c.drawString(col2_x, tabela_y - linha_h + 5 * mm, str(valor_txt))

            tabela_y -= linha_h

        y = tabela_y - 10 * mm

        # Caixa de aviso (dourada)
        c.setFillColorRGB(0.98, 0.75, 0.14)
        c.rect(20 * mm, y - 30 * mm, largura - 40 * mm, 28 * mm, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)

        c.setFont("Helvetica-Bold", 11)
        c.drawString(25 * mm, y - 8 * mm, "IMPORTANTE:")
        c.setFont("Helvetica", 10)
        c.drawString(25 * mm, y - 14 * mm,
                     f"Ao depositar no banco, escreva a referencia abaixo na")
        c.drawString(25 * mm, y - 19 * mm,
                     f"descricao do deposito:")
        c.setFont("Helvetica-Bold", 12)
        c.drawString(25 * mm, y - 26 * mm, referencia)

        y -= 40 * mm

        # Assinatura
        c.setFont("Helvetica", 10)
        c.drawCentredString(largura / 2, y, "_" * 50)
        y -= 6 * mm
        c.setFont("Helvetica", 10)
        c.drawCentredString(largura / 2, y,
                             f"Assinatura do gerente: {ger_nome or '-'}")

        # Rodape
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        agora = datetime.now().strftime("%d/%m/%Y as %H:%M")
        c.drawCentredString(largura / 2, 25 * mm,
                             f"Documento gerado em {agora} pela plataforma JAM Soft")
        c.drawCentredString(largura / 2, 20 * mm,
                             "Este documento nao substitui o comprovativo oficial do banco.")
        c.setFillColorRGB(0, 0, 0)

    c.save()
    return caminho_saida, None