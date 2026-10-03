"""
Helper de versão — lê a versão do ficheiro VERSION.
"""
import os
from pathlib import Path


VERSION_FILE = Path(__file__).parent / "VERSION"


def obter_versao():
    """Devolve a versão actual (ex: '1.0.0')."""
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "desconhecida"


def obter_versao_completa():
    """Devolve 'JAM Soft v1.0.0'."""
    return f"JAM Soft v{obter_versao()}"


def obter_assinatura():
    """Devolve 'JAM Soft/1.0.0' para SAF-T / AGT."""
    return f"JAM Soft/{obter_versao()}"


# Teste rápido
if __name__ == "__main__":
    print(f"Versão: {obter_versao()}")
    print(f"Completa: {obter_versao_completa()}")
    print(f"Assinatura: {obter_assinatura()}")