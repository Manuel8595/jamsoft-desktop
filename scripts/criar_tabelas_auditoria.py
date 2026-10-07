try:
    from database import (criar_nao_conformidade, listar_nao_conformidades,
                           buscar_nao_conformidade, atualizar_estado_nc,
                           aud_vendas_com_desconto, aud_sangrias,
                           aud_anulacoes, aud_perdas_recentes, aud_lotes_vencidos)
    print("OK - Todas as funcoes de auditoria existem!")
except ImportError as e:
    print(f"ERRO - Falta: {e}")