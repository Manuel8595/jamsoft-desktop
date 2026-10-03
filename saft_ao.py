"""
Exportação SAF-T (AO) - Standard Audit File for Tax Purposes
Formato XML para a AGT (Angola)

Versão simplificada com os campos essenciais.
Quando a AGT fornecer o esquema completo, adicionar campos em falta.
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from database import conectar, obter_empresa


PASTA_SAFT = "saft"


def _criar_elemento(parent, tag, texto=None, **atributos):
    """Cria um elemento XML com atributos e/ou texto."""
    elem = ET.SubElement(parent, tag)
    for k, v in atributos.items():
        elem.set(k, str(v) if v is not None else "")
    if texto is not None:
        elem.text = str(texto)
    return elem


def _formatar_data_saft(data_str):
    """Converte data para formato SAF-T (YYYY-MM-DD)."""
    if not data_str:
        return ""
    return str(data_str)[:10]


def _formatar_decimal(valor):
    """Formata número decimal (2 casas, ponto como separador)."""
    try:
        return f"{float(valor):.2f}"
    except Exception:
        return "0.00"


def exportar_saft(data_inicio=None, data_fim=None, caminho_saida=None):
    """
    Exporta o SAF-T (AO) para um ficheiro XML.

    data_inicio e data_fim: strings 'YYYY-MM-DD'
    Se não forem dadas, exporta o mês actual.

    Retorna (caminho, erro).
    """
    if not data_inicio:
        hoje = datetime.now()
        data_inicio = hoje.replace(day=1).strftime("%Y-%m-%d")

    if not data_fim:
        data_fim = datetime.now().strftime("%Y-%m-%d")

    # ─── Pasta destino ───
    if not os.path.exists(PASTA_SAFT):
        os.makedirs(PASTA_SAFT)

    if not caminho_saida:
        nome = f"SAFT_AO_{data_inicio}_{data_fim}.xml".replace("-", "")
        caminho_saida = os.path.join(PASTA_SAFT, nome)

    # ─── Dados da empresa ───
    emp = obter_empresa()
    if not emp:
        return None, "Empresa nao configurada. Configure primeiro o modulo fiscal."

    emp_nome = emp[1] or "Farmacia"
    emp_nif = emp[2] or "-"
    emp_end = emp[3] or "-"
    emp_tel = emp[4] or "-"
    emp_email = emp[5] or "-"

    # ─── Conectar à BD ───
    conn = conectar()
    cur = conn.cursor()

    try:
        # ─── Cabeçalho SAF-T ───
        raiz = ET.Element("AuditFile")
        raiz.set("xmlns", "urn:OECD:StandardAuditFile-Tax:AO_1.00_01")

        cabecalho = _criar_elemento(raiz, "Header")

        # Versão
        _criar_elemento(cabecalho, "AuditFileVersion", "1.00_01")
        _criar_elemento(cabecalho, "CompanyName", emp_nome)
        _criar_elemento(cabecalho, "CompanyTaxID", emp_nif)
        _criar_elemento(cabecalho, "CompanyAddress", emp_end)
        _criar_elemento(cabecalho, "CompanyPhone", emp_tel)
        _criar_elemento(cabecalho, "CompanyEmail", emp_email)

        # Período
        _criar_elemento(cabecalho, "TaxRegistrationNumber", emp_nif)
        _criar_elemento(cabecalho, "TaxAccountingBasis", "F")
        _criar_elemento(cabecalho, "TaxEntity", "Global")
        _criar_elemento(cabecalho, "ProductCompanyTaxID", "JAM Soft")
        _criar_elemento(cabecalho, "SoftwareValidationNumber", "")  # Vazio até AGT
        _criar_elemento(cabecalho, "ProductID", "JAMSoft/FT")
        _criar_elemento(cabecalho, "ProductVersion", "1.0")
        _criar_elemento(cabecalho, "DateCreated", datetime.now().strftime("%Y-%m-%d"))
        _criar_elemento(cabecalho, "StartDate", data_inicio)
        _criar_elemento(cabecalho, "EndDate", data_fim)
        _criar_elemento(cabecalho, "CurrencyCode", "AOA")

        # ─── Tabela de Clientes ───
        master_files = _criar_elemento(raiz, "MasterFiles")

        clientes_elem = _criar_elemento(master_files, "Customer")

        cur.execute("""
            SELECT id, nome, nif, endereco, telefone, email
            FROM clientes
            ORDER BY id
        """)
        clientes = cur.fetchall()

        for c in clientes:
            cid, nome, nif, end, tel, email = c

            cust = _criar_elemento(clientes_elem, "Customer")
            _criar_elemento(cust, "CustomerID", str(cid))
            _criar_elemento(cust, "AccountID", "Desconhecido")
            _criar_elemento(cust, "CustomerTaxID", nif or "999999999")
            _criar_elemento(cust, "CompanyName", nome or "Consumidor Final")

            # Morada
            morada = _criar_elemento(cust, "BillingAddress")
            _criar_elemento(morada, "AddressDetail", end or "Desconhecido")
            _criar_elemento(morada, "City", "Desconhecido")
            _criar_elemento(morada, "PostalCode", "0000")
            _criar_elemento(morada, "Country", "AO")

            _criar_elemento(cust, "Telephone", tel or "")
            _criar_elemento(cust, "Email", email or "")
            _criar_elemento(cust, "SelfBillingIndicator", "0")

        # ─── Tabela de Produtos ───
        produtos_elem = _criar_elemento(master_files, "Product")

        cur.execute("""
            SELECT id, nome, codigo_barras, preco_venda, isento_iva
            FROM produtos
            ORDER BY id
        """)
        produtos = cur.fetchall()

        for p in produtos:
            pid, nome, codigo, preco, isento = p

            prod = _criar_elemento(produtos_elem, "Product")
            _criar_elemento(prod, "ProductType", "P")
            _criar_elemento(prod, "ProductCode", codigo or str(pid))
            _criar_elemento(prod, "ProductDescription", nome)
            _criar_elemento(prod, "ProductNumberCode", codigo or str(pid))
            _criar_elemento(prod, "UnitPrice", _formatar_decimal(preco))

        # ─── Documentos Comerciais (Facturas) ───
        source_docs = _criar_elemento(raiz, "SourceDocuments")

        vendas_elem = _criar_elemento(source_docs, "SalesInvoices")

        # Número total de documentos
        cur.execute("""
            SELECT COUNT(*) FROM facturas
            WHERE DATE(data) >= DATE(?) AND DATE(data) <= DATE(?)
              AND tipo = 'FT'
        """, (data_inicio, data_fim))
        num_docs = cur.fetchone()[0] or 0
        _criar_elemento(vendas_elem, "NumberOfEntries", str(num_docs))

        # Total (a calcular no fim)
        total_debito = 0.0
        total_credito = 0.0

        # Buscar facturas
        cur.execute("""
            SELECT id, numero, data, cliente_id, cliente_nome, cliente_nif,
                   cliente_endereco, subtotal, total_iva, total, estado,
                   forma_pagamento, utilizador_nome,
                   COALESCE(hash_documento, '')
            FROM facturas
            WHERE DATE(data) >= DATE(?) AND DATE(data) <= DATE(?)
              AND tipo = 'FT'
            ORDER BY id
        """, (data_inicio, data_fim))
        facturas = cur.fetchall()

        for f in facturas:
            (fid, numero, data_f, cliente_id, cli_nome, cli_nif,
             cli_end, subtotal, iva, total, estado, forma_pag,
             user_nome, hash_doc) = f

            inv = _criar_elemento(vendas_elem, "Invoice")

            _criar_elemento(inv, "InvoiceNo", numero)
            _criar_elemento(inv, "DocumentStatus")
            # Sub-elementos do DocumentStatus
            status = inv.find("DocumentStatus")
            _criar_elemento(status, "InvoiceStatus", "N" if estado == "EMITIDA" else "A")
            _criar_elemento(status, "InvoiceStatusDate", _formatar_data_saft(data_f))
            _criar_elemento(status, "SourceID", user_nome or "Sistema")
            _criar_elemento(status, "SourceBilling", "P")

            _criar_elemento(inv, "Hash", hash_doc or "0" * 172)
            _criar_elemento(inv, "HashControl", "1")

            _criar_elemento(inv, "Period", str(datetime.now().month))
            _criar_elemento(inv, "InvoiceDate", _formatar_data_saft(data_f))
            _criar_elemento(inv, "InvoiceType", "FT")
            _criar_elemento(inv, "SourceID", "JAM Soft")
            _criar_elemento(inv, "SystemEntryDate", _formatar_data_saft(data_f))
            _criar_elemento(inv, "CustomerID", str(cliente_id or 0))

            # Linhas de factura
            cur.execute("""
                SELECT descricao, quantidade, preco_unitario, isento_iva,
                       taxa_iva, valor_iva, subtotal
                FROM itens_factura
                WHERE factura_id = ?
                ORDER BY id
            """, (fid,))
            linhas = cur.fetchall()

            for idx, linha in enumerate(linhas, start=1):
                (desc, qtd, preco, isento, taxa, v_iva, sub) = linha

                line = _criar_elemento(inv, "Line")
                _criar_elemento(line, "LineNumber", str(idx))
                _criar_elemento(line, "ProductCode", desc[:40])
                _criar_elemento(line, "ProductDescription", desc)
                _criar_elemento(line, "Quantity", _formatar_decimal(qtd))
                _criar_elemento(line, "UnitOfMeasure", "UN")
                _criar_elemento(line, "UnitPrice", _formatar_decimal(preco))
                _criar_elemento(line, "TaxPointDate", _formatar_data_saft(data_f))

                _criar_elemento(line, "Description", desc)

                # Crédito/Débito
                _criar_elemento(line, "CreditAmount", "0.00")

                # Taxa de IVA
                taxa_elem = _criar_elemento(line, "Tax")
                _criar_elemento(taxa_elem, "TaxType", "IVA")
                _criar_elemento(taxa_elem, "TaxCountryRegion", "AO")
                _criar_elemento(taxa_elem, "TaxCode", "ISE" if isento else "NOR")
                if isento:
                    _criar_elemento(taxa_elem, "TaxPercentage", "0.00")
                else:
                    _criar_elemento(taxa_elem, "TaxPercentage", _formatar_decimal((taxa or 0.14) * 100))

                # Valor
                _criar_elemento(line, "SettlementAmount", "0.00")

            # Totais do documento
            doc_totals = _criar_elemento(inv, "DocumentTotals")
            _criar_elemento(doc_totals, "TaxPayable", _formatar_decimal(iva))
            _criar_elemento(doc_totals, "NetTotal", _formatar_decimal(subtotal))
            _criar_elemento(doc_totals, "GrossTotal", _formatar_decimal(total))

            total_debito += float(total or 0)

        # Total do documento
        _criar_elemento(vendas_elem, "TotalDebit", _formatar_decimal(total_debito))
        _criar_elemento(vendas_elem, "TotalCredit", "0.00")

        # ─── Guardar XML ───
        # Primeiro gerar string
        xml_str = ET.tostring(raiz, encoding="utf-8")

        # Depois formatar com indentação
        dom = minidom.parseString(xml_str)
        xml_formatado = dom.toprettyxml(indent="  ", encoding="utf-8")

        with open(caminho_saida, "wb") as fp:
            fp.write(xml_formatado)

        return caminho_saida, None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Erro ao gerar SAF-T: {e}"
    finally:
        conn.close()


def testar_exportacao():
    """Testa a exportação e mostra resultado."""
    print("\n" + "="*60)
    print("  TESTE — Exportação SAF-T (AO)")
    print("="*60 + "\n")

    caminho, erro = exportar_saft()

    if erro:
        print(f"❌ ERRO: {erro}")
    else:
        print(f"✅ SAF-T gerado: {caminho}")
        tamanho = os.path.getsize(caminho) / 1024
        print(f"   Tamanho: {tamanho:.1f} KB")

    print("\n" + "="*60 + "\n")
    return caminho, erro


if __name__ == "__main__":
    testar_exportacao()