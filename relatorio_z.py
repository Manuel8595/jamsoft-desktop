# ============================================================
# ============ RELATORIO Z - CONCILIACAO GERAL ===============
# ============================================================
#
# Gera o Relatorio Z do dia:
#   - Versao A4 (para arquivar)
#   - Versao Termica 80mm (para imprimir na farmacia)
#
# ============================================================

import os
from datetime import datetime
from tkinter import *
from tkinter import messagebox, ttk

from database import (obter_dia, consolidar_dia, obter_orcamento_mes,
                       calcular_orcamento_dia, guardar_relatorio,
                       marcar_relatorio_z_gerado, registar_auditoria,
                       conectar)
from moeda import formatar_kz


PASTA_RELATORIOS = "relatorios"


def garantir_pasta():
    if not os.path.exists(PASTA_RELATORIOS):
        os.makedirs(PASTA_RELATORIOS)


# ============================================================
# ============ OBTER DADOS ===================================
# ============================================================

def obter_turnos_do_dia(data_ref):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, data_abertura, data_fecho, utilizador_nome,
               total_vendas, total_dinheiro, total_tpa, total_pix,
               total_contado, total_sistema, diferenca,
               COALESCE(dinheiro_contado, 0), COALESCE(tpa_contado, 0),
               COALESCE(observacoes, '')
        FROM turnos_caixa
        WHERE DATE(data_abertura) = DATE(?)
          AND estado = 'FECHADO'
        ORDER BY id ASC
    """, (data_ref,))
    resultado = cur.fetchall()
    conn.close()
    return resultado


def obter_num_clientes_turno(data_ref, turno_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM vendas
        WHERE caixa_id = (SELECT caixa_id FROM turnos_caixa WHERE id = ?)
        AND data >= (SELECT data_abertura FROM turnos_caixa WHERE id = ?)
        AND data <= (SELECT COALESCE(data_fecho, datetime('now')) FROM turnos_caixa WHERE id = ?)
    """, (turno_id, turno_id, turno_id))
    total = cur.fetchone()[0] or 0
    conn.close()
    return total


def obter_movimentos_caixa_dia(data_ref):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.data, m.tipo, m.valor, m.descricao, m.utilizador_nome
        FROM movimentos_caixa m
        WHERE DATE(m.data) = DATE(?)
        ORDER BY m.data ASC, m.id ASC
    """, (data_ref,))
    resultado = cur.fetchall()
    conn.close()
    return resultado


# ============================================================
# ============ GERAR PDF =====================================
# ============================================================

def gerar_relatorio_z(data_ref=None, formato="A4", caminho_saida=None):
    if not data_ref:
        data_ref = datetime.now().strftime("%Y-%m-%d")

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.colors import HexColor
    except ImportError:
        return None, "ReportLab nao instalado."

    dia = obter_dia(data_ref)
    dados = consolidar_dia(data_ref)
    turnos = obter_turnos_do_dia(data_ref)

    if not turnos:
        return None, "Nao existem turnos fechados neste dia."

    orcamento_dia = calcular_orcamento_dia(data_ref)
    percentagem = 0
    if orcamento_dia > 0:
        percentagem = (dados["total_vendas"] / orcamento_dia) * 100

    from database import obter_empresa
    empresa = obter_empresa()
    emp_nome = empresa[1] if empresa else "Farmacia"
    emp_nif = empresa[2] if empresa else "-"
    emp_end = empresa[3] if empresa else "-"
    emp_tel = empresa[4] if empresa else "-"
    logo_path = empresa[9] if (empresa and len(empresa) > 9) else None

    garantir_pasta()

    if not caminho_saida:
        nome_seguro = data_ref.replace("-", "_")
        sufixo = "A4" if formato == "A4" else "TERMICA"
        caminho_saida = os.path.join(
            PASTA_RELATORIOS,
            f"relatorio_z_{nome_seguro}_{sufixo}.pdf"
        )

    if formato == "TERMICA":
        page_size = (80 * mm, 297 * mm)
    else:
        page_size = A4

    c = pdf_canvas.Canvas(caminho_saida, pagesize=page_size)
    largura, altura = page_size

    if formato == "A4":
        _desenhar_a4(c, largura, altura, data_ref, dia, dados, turnos,
                      orcamento_dia, percentagem, emp_nome, emp_nif,
                      emp_end, emp_tel, logo_path, mm, HexColor)
    else:
        _desenhar_termica(c, largura, altura, data_ref, dia, dados, turnos,
                            orcamento_dia, percentagem, emp_nome, emp_nif,
                            emp_tel, mm, HexColor)

    c.save()
    return caminho_saida, None


# ============================================================
# ============ DESENHAR A4 (DESIGN LIMPO) ====================
# ============================================================

def _desenhar_a4(c, largura, altura, data_ref, dia, dados, turnos,
                  orcamento_dia, percentagem, emp_nome, emp_nif,
                  emp_end, emp_tel, logo_path, mm, HexColor):
    """Desenha a versao A4 - design profissional e limpo."""

    # Cores sobrias
    CINZA_ESCURO = HexColor("#1e293b")
    CINZA_MEDIO = HexColor("#64748b")
    CINZA_CLARO = HexColor("#e2e8f0")
    VERDE = HexColor("#16a34a")
    VERMELHO = HexColor("#dc2626")
    LARANJA = HexColor("#ea580c")

    # Margens
    margem_esq = 20 * mm
    margem_dir = largura - 20 * mm
    largura_util = margem_dir - margem_esq

    y = altura - 20 * mm

    # ─── CABECALHO ──────────────────────────────────────
    if logo_path and os.path.exists(logo_path):
        try:
            from reportlab.lib.utils import ImageReader
            logo = ImageReader(logo_path)
            c.drawImage(logo, margem_esq, y - 12 * mm,
                         width=18 * mm, height=14 * mm,
                         preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c.setFillColor(CINZA_ESCURO)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margem_esq, y, emp_nome)

    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.setFillColor(CINZA_MEDIO)
    c.drawString(margem_esq, y, f"NIF: {emp_nif}  |  {emp_end}")

    y -= 4 * mm
    c.drawString(margem_esq, y, f"Tel: {emp_tel}")

    y -= 8 * mm

    # Linha separadora
    c.setStrokeColor(CINZA_ESCURO)
    c.setLineWidth(1.5)
    c.line(margem_esq, y, margem_dir, y)

    # ─── TITULO ─────────────────────────────────────────
    y -= 12 * mm
    c.setFillColor(CINZA_ESCURO)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(largura / 2, y, "RELATORIO Z")

    y -= 6 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(CINZA_MEDIO)
    c.drawCentredString(largura / 2, y, "Conciliacao Geral do Dia")

    y -= 12 * mm

    # ─── INFO DO DIA ────────────────────────────────────
    c.setFont("Helvetica", 9)
    c.setFillColor(CINZA_ESCURO)

    # Coluna esquerda
    try:
        dt_obj = datetime.strptime(data_ref, "%Y-%m-%d")
        data_fmt = dt_obj.strftime("%d/%m/%Y")
    except Exception:
        data_fmt = data_ref

    c.drawString(margem_esq, y, f"Data: {data_fmt}")

    if dia:
        c.drawString(margem_esq + largura_util * 0.5, y,
                      f"Abertura: {dia[2] or '-'} ({dia[4] or '-'})")
        y -= 5 * mm
        c.drawString(margem_esq + largura_util * 0.5, y,
                      f"Fecho: {dia[3] or '-'} ({dia[5] or '-'})")

    y -= 12 * mm

    # ─── RESUMO DOS TURNOS ──────────────────────────────
    y = _cabecalho_seccao(c, margem_esq, margem_dir, y, "RESUMO DOS TURNOS",
                            CINZA_ESCURO, CINZA_CLARO, mm)

    # Cabecalho da tabela
    c.setFillColor(CINZA_CLARO)
    c.rect(margem_esq, y - 1.5 * mm, largura_util, 6 * mm, fill=1, stroke=0)

    c.setFillColor(CINZA_ESCURO)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margem_esq + 3 * mm, y, "Turno")
    c.drawString(margem_esq + 22 * mm, y, "Operador")
    c.drawString(margem_esq + 65 * mm, y, "Vendas")
    c.drawString(margem_esq + 100 * mm, y, "Contado")
    c.drawString(margem_esq + 135 * mm, y, "Diferenca")

    y -= 7 * mm

    # Linhas
    c.setFont("Helvetica", 9)
    for t in turnos:
        (tid, dt_ab, dt_fc, utilizador, total_vendas, total_dinheiro,
         total_tpa, total_pix, total_contado, total_sistema, dif,
         din_cont, tpa_cont, obs) = t

        c.setFillColor(CINZA_ESCURO)
        c.drawString(margem_esq + 3 * mm, y, f"#{tid}")
        c.drawString(margem_esq + 22 * mm, y, (utilizador or "-")[:22])
        c.drawString(margem_esq + 65 * mm, y, formatar_kz(total_vendas or 0))
        c.drawString(margem_esq + 100 * mm, y, formatar_kz(total_contado or 0))

        if abs(dif or 0) < 0.01:
            c.setFillColor(VERDE)
            c.drawString(margem_esq + 135 * mm, y, "OK")
        elif dif > 0:
            c.setFillColor(LARANJA)
            c.drawString(margem_esq + 135 * mm, y, f"+{formatar_kz(dif)}")
        else:
            c.setFillColor(VERMELHO)
            c.drawString(margem_esq + 135 * mm, y, f"-{formatar_kz(abs(dif))}")

        # Linha subtil
        c.setStrokeColor(CINZA_CLARO)
        c.setLineWidth(0.3)
        c.line(margem_esq, y - 1.5 * mm, margem_dir, y - 1.5 * mm)

        y -= 6 * mm

    y -= 8 * mm

    # ─── TOTAIS ─────────────────────────────────────────
    y = _cabecalho_seccao(c, margem_esq, margem_dir, y, "TOTAIS",
                            CINZA_ESCURO, CINZA_CLARO, mm)

    c.setFont("Helvetica", 10)
    c.setFillColor(CINZA_ESCURO)

    linhas = [
        ("Turnos fechados:", str(dados["num_turnos"]), False),
        ("Clientes atendidos:", str(dados["total_clientes"]), False),
        ("Ticket medio:", formatar_kz(dados["ticket_medio"]), False),
        ("", "", False),
        ("Total vendido:", formatar_kz(dados["total_vendas"]), True),
        ("  Dinheiro fisico:", formatar_kz(dados["total_dinheiro"]), False),
        ("  TPA (Multicaixa):", formatar_kz(dados["total_tpa"]), False),
        ("  PIX/Transferencia:", formatar_kz(dados["total_pix"]), False),
        ("", "", False),
        ("Faltas:", formatar_kz(dados["total_faltas"]), False),
        ("Sobras:", formatar_kz(dados["total_sobras"]), False),
        ("Diferenca final:", formatar_kz(dados["diferenca_total"]), True),
    ]

    for label, valor, destaque in linhas:
        if label == "" and valor == "":
            y -= 3 * mm
            continue

        if destaque:
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(CINZA_ESCURO)
        elif label.startswith("  "):
            c.setFont("Helvetica", 9)
            c.setFillColor(CINZA_MEDIO)
        else:
            c.setFont("Helvetica", 10)
            c.setFillColor(CINZA_ESCURO)

        c.drawString(margem_esq + 5 * mm, y, label.strip() if label.startswith("  ") else label)
        c.drawRightString(margem_dir - 5 * mm, y, valor)
        y -= 5.5 * mm

    y -= 5 * mm

    # ─── VALOR A DEPOSITAR (linha simples, sem banner) ──
    c.setStrokeColor(CINZA_ESCURO)
    c.setLineWidth(1)
    c.line(margem_esq, y, margem_dir, y)
    y -= 6 * mm

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(CINZA_ESCURO)
    c.drawString(margem_esq, y, "VALOR A DEPOSITAR:")
    c.drawRightString(margem_dir, y, formatar_kz(dados["valor_depositar"]))

    c.setStrokeColor(CINZA_ESCURO)
    c.setLineWidth(1)
    c.line(margem_esq, y - 2 * mm, margem_dir, y - 2 * mm)

    y -= 12 * mm

    # ─── META DO DIA ────────────────────────────────────
    if orcamento_dia > 0:
        y = _cabecalho_seccao(c, margem_esq, margem_dir, y, "META DO DIA",
                                CINZA_ESCURO, CINZA_CLARO, mm)

        c.setFont("Helvetica", 10)
        c.setFillColor(CINZA_ESCURO)
        c.drawString(margem_esq + 5 * mm, y,
                      f"Orcamento: {formatar_kz(orcamento_dia)}")
        c.drawString(margem_esq + 90 * mm, y,
                      f"Vendido: {formatar_kz(dados['total_vendas'])}")
        y -= 6 * mm

        if percentagem >= 100:
            c.setFillColor(VERDE)
        else:
            c.setFillColor(LARANJA)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margem_esq + 5 * mm, y, f"Atingimento: {percentagem:.1f}%")

        y -= 15 * mm

    # ─── MOVIMENTOS DE CAIXA (se existirem) ─────────────
    movimentos = obter_movimentos_caixa_dia(data_ref)

    if movimentos:
        if y < 60 * mm:
            c.showPage()
            y = altura - 20 * mm

        y = _cabecalho_seccao(c, margem_esq, margem_dir, y, "MOVIMENTOS DE CAIXA",
                                CINZA_ESCURO, CINZA_CLARO, mm)

        c.setFillColor(CINZA_CLARO)
        c.rect(margem_esq, y - 1.5 * mm, largura_util, 6 * mm, fill=1, stroke=0)

        c.setFillColor(CINZA_ESCURO)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(margem_esq + 3 * mm, y, "Hora")
        c.drawString(margem_esq + 22 * mm, y, "Tipo")
        c.drawString(margem_esq + 55 * mm, y, "Valor")
        c.drawString(margem_esq + 90 * mm, y, "Descricao")
        c.drawString(margem_esq + 140 * mm, y, "Utilizador")

        y -= 7 * mm

        c.setFont("Helvetica", 8)
        total_ent = 0
        total_sai = 0

        for m in movimentos:
            if y < 30 * mm:
                c.showPage()
                y = altura - 20 * mm

            dt, tipo, valor, desc, user = m[:5]

            hora = (dt or "")[-8:] if dt else "-"
            tipo_txt = (tipo or "-")[:12]

            c.setFillColor(CINZA_ESCURO)
            c.drawString(margem_esq + 3 * mm, y, hora)
            c.drawString(margem_esq + 22 * mm, y, tipo_txt)

            if tipo in ("ENTRADA", "REFORCO"):
                c.setFillColor(VERDE)
                c.drawString(margem_esq + 55 * mm, y, f"+{formatar_kz(abs(valor or 0))}")
                total_ent += valor or 0
            elif tipo in ("SAIDA", "SANGRIA"):
                c.setFillColor(VERMELHO)
                c.drawString(margem_esq + 55 * mm, y, f"-{formatar_kz(abs(valor or 0))}")
                total_sai += valor or 0
            else:
                c.drawString(margem_esq + 55 * mm, y, formatar_kz(valor or 0))

            c.setFillColor(CINZA_ESCURO)
            c.drawString(margem_esq + 90 * mm, y, (desc or "-")[:30])
            c.drawString(margem_esq + 140 * mm, y, (user or "-")[:15])

            c.setStrokeColor(CINZA_CLARO)
            c.setLineWidth(0.3)
            c.line(margem_esq, y - 1.5 * mm, margem_dir, y - 1.5 * mm)

            y -= 6 * mm

        y -= 3 * mm
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(VERDE)
        c.drawString(margem_esq + 5 * mm, y, "Total entradas:")
        c.drawRightString(margem_dir - 5 * mm, y, f"+{formatar_kz(total_ent)}")
        y -= 5 * mm
        c.setFillColor(VERMELHO)
        c.drawString(margem_esq + 5 * mm, y, "Total saidas:")
        c.drawRightString(margem_dir - 5 * mm, y, f"-{formatar_kz(total_sai)}")
        y -= 5 * mm
        c.setFillColor(CINZA_ESCURO)
        c.drawString(margem_esq + 5 * mm, y, "Saldo:")
        c.drawRightString(margem_dir - 5 * mm, y, formatar_kz(total_ent - total_sai))
        y -= 10 * mm

    # ─── ASSINATURAS (sempre na mesma pagina se possivel) ──
    if y < 45 * mm:
        c.showPage()
        y = altura - 50 * mm
    else:
        y -= 10 * mm

    c.setStrokeColor(CINZA_ESCURO)
    c.setLineWidth(0.5)

    linha_y = y
    c.line(margem_esq + 10 * mm, linha_y, margem_esq + 70 * mm, linha_y)
    c.line(margem_dir - 70 * mm, linha_y, margem_dir - 10 * mm, linha_y)

    y -= 5 * mm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(CINZA_ESCURO)
    c.drawCentredString(margem_esq + 40 * mm, y, "Assinatura do Gerente")
    c.drawCentredString(margem_dir - 40 * mm, y, "Assinatura do Farmaceutico")

    # ─── RODAPE ─────────────────────────────────────────
    c.setFont("Helvetica-Oblique", 7)
    c.setFillColor(CINZA_MEDIO)
    c.drawCentredString(largura / 2, 15 * mm,
                          f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} - JAM Soft")
    c.drawCentredString(largura / 2, 10 * mm,
                          "Documento processado por computador")


def _cabecalho_seccao(c, margem_esq, margem_dir, y, titulo, cor, cor_linha, mm):
    """Desenha cabecalho de seccao limpo."""
    c.setFillColor(cor)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margem_esq, y, titulo)

    y -= 3 * mm
    c.setStrokeColor(cor_linha)
    c.setLineWidth(0.5)
    c.line(margem_esq, y, margem_dir, y)

    return y - 7 * mm


# ============================================================
# ============ DESENHAR TERMICA 80mm =========================
# ============================================================

def _desenhar_termica(c, largura, altura, data_ref, dia, dados, turnos,
                       orcamento_dia, percentagem, emp_nome, emp_nif,
                       emp_tel, mm, HexColor):
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
    c.drawCentredString(largura / 2, y, "-" * 34)
    y -= 4 * mm
    c.drawCentredString(largura / 2, y, "RELATORIO Z")
    y -= 4 * mm
    c.drawCentredString(largura / 2, y, "-" * 34)
    y -= 5 * mm

    c.setFont("Helvetica", 7)
    c.drawString(3 * mm, y, f"Data: {data_ref}")
    y -= 3.5 * mm

    if dia:
        c.drawString(3 * mm, y, f"Aberto: {dia[2] or '-'} por {dia[4] or '-'}")
        y -= 3 * mm
        c.drawString(3 * mm, y, f"Fechado: {dia[3] or '-'} por {dia[5] or '-'}")
        y -= 4 * mm

    c.drawCentredString(largura / 2, y, "-" * 34)
    y -= 4 * mm

    c.setFont("Helvetica-Bold", 8)
    c.drawString(3 * mm, y, "TURNOS")
    y -= 4 * mm

    c.setFont("Helvetica", 7)
    for t in turnos:
        (tid, dt_ab, dt_fc, utilizador, total_vendas, *_resto) = t
        dif = t[10] if len(t) > 10 else 0

        c.drawString(3 * mm, y, f"#{tid} {(utilizador or '')[:20]}")
        y -= 3 * mm
        c.drawString(5 * mm, y, f"Vendas: {formatar_kz(total_vendas or 0)}")
        y -= 3 * mm

        if abs(dif or 0) < 0.01:
            c.drawString(5 * mm, y, "Dif: OK")
        elif dif > 0:
            c.drawString(5 * mm, y, f"Dif: +{formatar_kz(dif)}")
        else:
            c.drawString(5 * mm, y, f"Dif: -{formatar_kz(abs(dif))}")
        y -= 4 * mm

    c.drawCentredString(largura / 2, y, "-" * 34)
    y -= 4 * mm

    c.setFont("Helvetica-Bold", 8)
    c.drawString(3 * mm, y, "TOTAIS")
    y -= 4 * mm

    c.setFont("Helvetica", 7)
    c.drawString(3 * mm, y, f"Turnos: {dados['num_turnos']}")
    y -= 3.5 * mm
    c.drawString(3 * mm, y, f"Clientes: {dados['total_clientes']}")
    y -= 3.5 * mm
    c.drawString(3 * mm, y, f"Ticket: {formatar_kz(dados['ticket_medio'])}")
    y -= 5 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(3 * mm, y, f"TOTAL: {formatar_kz(dados['total_vendas'])}")
    y -= 5 * mm

    c.setFont("Helvetica", 7)
    c.drawString(3 * mm, y, f"  Dinheiro: {formatar_kz(dados['total_dinheiro'])}")
    y -= 3.5 * mm
    c.drawString(3 * mm, y, f"  TPA: {formatar_kz(dados['total_tpa'])}")
    y -= 3.5 * mm
    c.drawString(3 * mm, y, f"  PIX: {formatar_kz(dados['total_pix'])}")
    y -= 4 * mm
    c.drawString(3 * mm, y, f"Faltas: {formatar_kz(dados['total_faltas'])}")
    y -= 3.5 * mm
    c.drawString(3 * mm, y, f"Sobras: {formatar_kz(dados['total_sobras'])}")
    y -= 5 * mm

    c.drawCentredString(largura / 2, y, "-" * 34)
    y -= 5 * mm

    c.setFont("Helvetica-Bold", 8)
    c.drawString(3 * mm, y, "A DEPOSITAR:")
    y -= 5 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura / 2, y, formatar_kz(dados['valor_depositar']))
    y -= 6 * mm

    if orcamento_dia > 0:
        c.setFont("Helvetica", 7)
        c.drawString(3 * mm, y, f"Orcamento: {formatar_kz(orcamento_dia)}")
        y -= 3.5 * mm
        c.drawString(3 * mm, y, f"Atingimento: {percentagem:.1f}%")
        y -= 4 * mm

    c.drawCentredString(largura / 2, y, "-" * 34)
    y -= 6 * mm
    c.setFont("Helvetica", 7)
    c.drawString(3 * mm, y, "Ass: __________________")
    y -= 8 * mm
    c.drawString(3 * mm, y, "Ass: __________________")

    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(largura / 2, 10 * mm,
                          f"Gerado {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawCentredString(largura / 2, 7 * mm, "JAM Soft")


# ============================================================
# ============ PERGUNTAR IMPRESSAO ===========================
# ============================================================

def perguntar_impressao(data_ref, utilizador_logado=None, parent=None):
    resultado = {"formato": None}

    if parent is None:
        parent = Toplevel()
        parent.withdraw()

    janela = Toplevel(parent)
    janela.title("Imprimir Relatorio Z")
    janela.geometry("500x420")
    janela.configure(bg="#0f172a")
    janela.transient(parent)
    janela.grab_set()

    janela.update_idletasks()
    x = (janela.winfo_screenwidth() - 500) // 2
    y = (janela.winfo_screenheight() - 420) // 2
    janela.geometry(f"500x420+{x}+{y}")

    header = Frame(janela, bg="#0ea5e9", height=70)
    header.pack(fill=X)
    header.pack_propagate(False)
    Label(header, text="Imprimir Relatorio Z",
          font=("Segoe UI", 15, "bold"),
          bg="#0ea5e9", fg="white").pack(pady=18)

    Label(janela, text=f"Data: {data_ref}",
          font=("Segoe UI", 11, "bold"),
          bg="#0f172a", fg="#94a3b8").pack(pady=(20, 5))

    Label(janela, text="Escolha o formato:",
          font=("Segoe UI", 11),
          bg="#0f172a", fg="#f8fafc").pack(pady=(10, 20))

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
    return resultado["formato"]


# ============================================================
# ============ ABRIR ESCOLHA + GERAR =========================
# ============================================================

def abrir_escolha_impressao(data_ref, utilizador_logado=None, parent=None,
                              auto=False):
    formato = perguntar_impressao(data_ref, utilizador_logado, parent)

    if not formato:
        return None

    caminho, erro = gerar_relatorio_z(data_ref, formato=formato)

    if erro:
        messagebox.showerror("Erro", erro)
        return None

    try:
        guardar_relatorio(
            tipo="RELATORIO_Z",
            referencia=data_ref,
            gerado_por=utilizador_logado["nome"] if utilizador_logado else "Sistema",
            caminho_pdf=caminho
        )
        marcar_relatorio_z_gerado(data_ref)

        if utilizador_logado:
            registar_auditoria(
                utilizador_logado["id"],
                utilizador_logado["nome"],
                "RELATORIO Z",
                f"Data: {data_ref} | Formato: {formato} | Ficheiro: {os.path.basename(caminho)}"
            )
    except Exception as e:
        print(f"[RelatorioZ] Aviso: {e}")

    if messagebox.askyesno("Relatorio Z Gerado",
        f"Relatorio Z gerado!\n\n"
        f"Formato: {formato}\n"
        f"Ficheiro: {os.path.basename(caminho)}\n\n"
        f"Abrir agora?"):
        try:
            os.startfile(caminho)
        except Exception:
            pass

    return caminho


# ============================================================
# ============ TESTE DIRETO ==================================
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  TESTE - relatorio_z.py")
    print("="*60)

    hoje = datetime.now().strftime("%Y-%m-%d")

    print(f"\n[1] A4 para {hoje}...")
    caminho, erro = gerar_relatorio_z(hoje, formato="A4")
    print(f"    {caminho}" if not erro else f"    ERRO: {erro}")

    print(f"\n[2] TERMICA para {hoje}...")
    caminho2, erro2 = gerar_relatorio_z(hoje, formato="TERMICA")
    print(f"    {caminho2}" if not erro2 else f"    ERRO: {erro2}")

    print("\n" + "="*60 + "\n")