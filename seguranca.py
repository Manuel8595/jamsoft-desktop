# ============================================================
# ============ SEGURANCA - JAM SOFT ==========================
# ============================================================

from tkinter import messagebox


def verificar_acesso(utilizador_logado, acao, contexto=""):
    """Verifica se o utilizador tem permissao para uma acao."""
    
    if not utilizador_logado:
        messagebox.showerror("Sessao Invalida",
            "Nenhum utilizador autenticado.\n\n"
            "Faca login novamente.")
        return False
    
    perfil = utilizador_logado.get("perfil", "")
    
    from permissoes import tem_permissao, NOMES_PERFIS
    
    if tem_permissao(perfil, acao):
        return True
    
    try:
        from database import registar_auditoria
        detalhe = f"Perfil '{perfil}' tentou '{acao}'"
        if contexto:
            detalhe += f" | {contexto}"
        
        registar_auditoria(
            utilizador_logado.get("id"),
            utilizador_logado.get("nome", "Desconhecido"),
            "TENTATIVA BLOQUEADA",
            detalhe
        )
    except Exception:
        pass
    
    nome_perfil = NOMES_PERFIS.get(perfil, perfil)
    
    msg = f"ACESSO NEGADO\n\n"
    msg += f"O seu perfil ({nome_perfil}) nao tem permissao\n"
    msg += f"para esta operacao.\n\n"
    msg += f"Operacao: {acao}"
    if contexto:
        msg += f"\nDetalhe: {contexto}"
    msg += f"\n\nEsta tentativa foi registada em auditoria."
    
    messagebox.showerror("Acesso Negado", msg)
    return False


def verificar_multiplas(utilizador_logado, acoes):
    for acao in acoes:
        if not verificar_acesso(utilizador_logado, acao):
            return False
    return True


def verificar_qualquer(utilizador_logado, acoes):
    from permissoes import tem_permissao
    perfil = utilizador_logado.get("perfil", "") if utilizador_logado else ""
    
    for acao in acoes:
        if tem_permissao(perfil, acao):
            return True
    
    if utilizador_logado and acoes:
        try:
            from database import registar_auditoria
            registar_auditoria(
                utilizador_logado.get("id"),
                utilizador_logado.get("nome", "Desconhecido"),
                "TENTATIVA BLOQUEADA",
                f"Perfil '{perfil}' tentou qualquer de: {', '.join(acoes)}"
            )
        except Exception:
            pass
        messagebox.showerror("Acesso Negado",
            f"ACESSO NEGADO\n\n"
            f"O seu perfil nao tem permissao para esta operacao.\n\n"
            f"Tentativa registada em auditoria.")
    
    return False


def registar_tentativa(utilizador_logado, acao, contexto=""):
    if not utilizador_logado:
        return
    
    try:
        from database import registar_auditoria
        detalhe = f"'{acao}'"
        if contexto:
            detalhe += f" | {contexto}"
        
        registar_auditoria(
            utilizador_logado["id"],
            utilizador_logado["nome"],
            "ACESSO SENSIVEL",
            detalhe
        )
    except Exception:
        pass
