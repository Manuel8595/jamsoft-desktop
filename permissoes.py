# ============================================================
# ============ SISTEMA DE PERMISSOES - JAM SOFT ==============
# ============================================================
# 
# 4 Perfis:
#   admin          - Administrador (acesso total)
#   gerente        - Gestao comercial/administrativa
#   farmaceutico   - Atividades farmaceuticas (interface minima)
#   auditor        - Verificacao independente (somente leitura)
# 
# ============================================================

PERFIS = ["admin", "gerente", "farmaceutico", "auditor"]

NOMES_PERFIS = {
    "admin": "Administrador",
    "gerente": "Gerente",
    "farmaceutico": "Farmacêutico",
    "auditor": "Auditor",
}

PERMISSOES = {
    # ===== VENDAS =====
    "pdv.abrir": ["admin", "gerente", "farmaceutico"],
    "pdv.vender": ["admin", "gerente", "farmaceutico"],
    "pdv.aplicar_desconto": ["admin", "gerente", "farmaceutico"],
    "pdv.autorizar_desconto": ["admin"],
    "pdv.anular_venda": ["admin", "gerente"],
        
    # ===== DEVOLUCOES =====
    "devolucoes.ver": ["admin", "gerente", "farmaceutico"],
    "devolucoes.criar": ["admin", "gerente", "farmaceutico"],
    "devolucoes.anular": ["admin", "gerente"],
    "devolucoes.autorizar": ["admin", "gerente"],
    
    # ===== CAIXA =====
    "caixa.abrir": ["admin", "gerente", "farmaceutico"],
    "caixa.fechar": ["admin", "gerente", "farmaceutico"],
    "caixa.sangria": ["admin", "gerente"],
    "caixa.reforco": ["admin", "gerente"],
    "caixa.ver_movimentos": ["admin", "gerente", "farmaceutico", "auditor"],
    "caixa.historico": ["admin", "gerente", "farmaceutico", "auditor"],
    "caixa.fecho_dia": ["admin", "gerente"],
    "caixa.lancar_tpa": ["admin", "gerente", "farmaceutico"],
    "caixa.conciliar": ["admin", "gerente"],
    "caixa.ver_conciliacao": ["admin", "gerente", "farmaceutico", "auditor"],
    "caixa.registar_deposito": ["admin", "gerente"],
    
    # ===== FISCAL =====
    "fiscal.configurar": ["admin"],
    "fiscal.emitir_factura": ["admin", "gerente", "farmaceutico"],
    "fiscal.anular_factura": ["admin", "gerente"],
    "fiscal.ver_facturas": ["admin", "gerente", "auditor"],
    "fiscal.gerar_pdf": ["admin", "gerente", "farmaceutico", "auditor"],
    
    # ===== PRODUTOS =====
    "produtos.cadastrar": ["admin", "gerente"],
    "produtos.editar": ["admin", "gerente"],
    "produtos.eliminar": ["admin"],
    "produtos.listar": ["admin", "gerente", "farmaceutico", "auditor"],
    "produtos.ajustar_estoque": ["admin", "gerente"],
    "produtos.ver_validade": ["admin", "gerente", "farmaceutico", "auditor"],
    "produtos.ver_fefo": ["admin", "gerente", "farmaceutico", "auditor"],
    
    # ===== COMPRAS =====
    "compras.criar": ["admin", "gerente"],
    "compras.listar": ["admin", "gerente", "auditor"],
    
    # ===== INVENTARIO =====
    "inventario.criar": ["admin", "gerente"],
    "inventario.ajustar": ["admin", "gerente"],
    "inventario.listar": ["admin", "gerente", "auditor"],
    
    # ===== PERDAS =====
    "perdas.registar": ["admin", "gerente", "farmaceutico"],
    "perdas.listar": ["admin", "gerente", "auditor"],
    "perdas.resumo": ["admin", "gerente", "auditor"],
    
    # ===== FORNECEDORES =====
    "fornecedores.criar": ["admin", "gerente"],
    "fornecedores.editar": ["admin", "gerente"],
    "fornecedores.eliminar": ["admin"],
    "fornecedores.listar": ["admin", "gerente", "auditor"],
    
    # ===== CLIENTES =====
    "clientes.criar": ["admin", "gerente", "farmaceutico"],
    "clientes.editar": ["admin", "gerente"],
    "clientes.eliminar": ["admin"],
    "clientes.listar": ["admin", "gerente", "farmaceutico"],
    
    # ===== CATEGORIAS =====
    "categorias.criar": ["admin", "gerente"],
    "categorias.editar": ["admin", "gerente"],
    "categorias.eliminar": ["admin"],
    "categorias.listar": ["admin", "gerente", "farmaceutico", "auditor"],
    
    # ===== RELATORIOS =====
    "relatorios.ver": ["admin", "gerente", "auditor"],
    "relatorios.vendas": ["admin", "gerente", "auditor"],
    "relatorios.produtos": ["admin", "gerente", "auditor"],
    "relatorios.financeiro": ["admin", "gerente", "auditor"],
    "relatorios.margem_lucro": ["admin", "gerente", "auditor"],
    "relatorios.fiscal": ["admin", "gerente", "auditor"],
    "relatorios.inventario": ["admin", "gerente", "auditor"],
    "relatorios.exportar": ["admin", "gerente", "auditor"],
    
    # ===== BACKUPS =====
    "backup.criar": ["admin"],
    "backup.restaurar": ["admin"],
    "backup.listar": ["admin", "auditor"],
    "backup.apagar": ["admin"],
    
    # ===== UTILIZADORES =====
    "utilizadores.criar": ["admin"],
    "utilizadores.editar": ["admin"],
    "utilizadores.eliminar": ["admin"],
    "utilizadores.listar": ["admin"],
    "utilizadores.alterar_senha": ["admin"],
    
    # ===== AUDITORIA =====
    "auditoria.ver_log": ["admin", "auditor"],
    "auditoria.registar": ["admin", "gerente", "farmaceutico", "auditor"],
    "auditoria.registar_nao_conformidade": ["admin", "auditor"],
    "auditoria.encerrar_nao_conformidade": ["admin"],
    "auditoria.exportar": ["admin", "auditor"],
    
    # ===== DASHBOARD =====
    "dashboard.ver": ["admin", "gerente", "auditor"],
    "dashboard.graficos": ["admin", "gerente", "auditor"],
    
    # ===== CONFIGURACOES =====
    "config.empresa": ["admin"],
    "config.logo": ["admin"],
    "config.series": ["admin"],
    "config.tema": ["admin"],
    
    # ===== NUVEM / SINCRONIZACAO =====
    "nuvem.sincronizar": ["admin", "gerente"],
    "nuvem.ver_fila": ["admin", "gerente", "auditor"],
    "nuvem.limpar_fila": ["admin", "gerente"],
}


def tem_permissao(perfil, acao):
    if perfil not in PERFIS:
        return False
    if acao not in PERMISSOES:
        return False
    return perfil in PERMISSOES[acao]


def verificar_ou_bloquear(perfil, acao, utilizador_logado=None, registar=True):
    from tkinter import messagebox
    
    if tem_permissao(perfil, acao):
        return True
    
    if registar and utilizador_logado:
        try:
            from database import registar_auditoria
            registar_auditoria(
                utilizador_logado["id"], utilizador_logado["nome"],
                "TENTATIVA BLOQUEADA",
                f"Perfil '{perfil}' tentou '{acao}'"
            )
        except Exception:
            pass
    
    msg = f"Acesso negado.\n\nO seu perfil ({NOMES_PERFIS.get(perfil, perfil)}) "
    msg += f"nao tem permissao para esta operacao.\n\n"
    msg += f"Esta tentativa foi registada em auditoria."
    
    messagebox.showerror("Acesso Negado", msg)
    return False


def pode_vender(perfil):
    return tem_permissao(perfil, "pdv.vender")


def pode_alterar_dados(perfil):
    return perfil != "auditor"


def pode_auditar(perfil):
    return tem_permissao(perfil, "auditoria.ver_log")


def pode_admin(perfil):
    return perfil == "admin"


def listar_acoes_perfil(perfil):
    return [acao for acao, perfis in PERMISSOES.items() if perfil in perfis]


def mostrar_matriz_permissoes():
    print("\n" + "="*80)
    print("MATRIZ DE PERMISSOES - JAM SOFT")
    print("="*80)
    print(f"\n{'Acao':<45} | Admin | Gerente | Farmaceutico | Auditor")
    print("-"*80)
    for acao in sorted(PERMISSOES.keys()):
        perfis = PERMISSOES[acao]
        admin = "X" if "admin" in perfis else "-"
        ger = "X" if "gerente" in perfis else "-"
        farm = "X" if "farmaceutico" in perfis else "-"
        aud = "X" if "auditor" in perfis else "-"
        print(f"{acao:<45} |  {admin}   |   {ger}    |      {farm}       |   {aud}")
    print("="*80 + "\n")


if __name__ == "__main__":
    mostrar_matriz_permissoes()