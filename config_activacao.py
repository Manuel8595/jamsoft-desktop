# -*- coding: utf-8 -*-
"""Gestao de activacao local do JAM Soft.

Guarda as credenciais em ficheiro JSON local depois da activacao.
"""
import json
import os
from pathlib import Path
from datetime import datetime

FICHEIRO_ACTIVACAO = Path(__file__).parent / "config_activacao.json"


def existe_activacao():
    """Verifica se ja esta activado localmente."""
    return FICHEIRO_ACTIVACAO.exists()


def ler_activacao():
    """Le os dados de activacao (ou None)."""
    if not FICHEIRO_ACTIVACAO.exists():
        return None
    try:
        with open(FICHEIRO_ACTIVACAO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def guardar_activacao(chave, farmacia_nome, farmacia_nif, serie, supabase_url, supabase_key):
    """Guarda a activacao localmente."""
    dados = {
        "chave": chave,
        "farmacia_nome": farmacia_nome,
        "farmacia_nif": farmacia_nif,
        "serie_padrao": serie,
        "supabase_url": supabase_url,
        "supabase_key": supabase_key,
        "activada_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(FICHEIRO_ACTIVACAO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    return dados


def apagar_activacao():
    """Remove a activacao local."""
    if FICHEIRO_ACTIVACAO.exists():
        FICHEIRO_ACTIVACAO.unlink()
