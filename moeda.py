# Taxa de IVA em Angola
IVA_ANGOLA = 0.14  # 14% para produtos não isentos

def formatar_kz(valor):
    """Formata um número como moeda angolana.
    Exemplo: 5500.5 -> 'Kz 5.500,50'
    """
    try:
        formatado = f"{valor:,.2f}"
        formatado = formatado.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"Kz {formatado}"
    except (ValueError, TypeError):
        return "Kz 0,00"

def calcular_iva(subtotal, aplica_iva=False):
    """Calcula o valor do IVA sobre um subtotal.
    Se aplica_iva for False (padrão para medicamentos), retorna 0.
    """
    if aplica_iva:
        return subtotal * IVA_ANGOLA
    return 0.0

def total_com_iva(subtotal, aplica_iva=False):
    """Retorna o total já com IVA (se aplicável)."""
    return subtotal + calcular_iva(subtotal, aplica_iva)