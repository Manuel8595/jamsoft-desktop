# -*- coding: utf-8 -*-
"""
Gera chaves de activacao JAM Soft para farmacias.
Uso: python scripts/gerar_chave.py "Nome da Farmacia" "NIF" "SERIE"
"""
import sys
import secrets
import string
import os
from datetime import datetime

def gerar_chave():
    """Gera chave no formato JAM-XXXX-XXXX-XXXX-XXXX"""
    chars = string.ascii_uppercase + string.digits
    partes = []
    for _ in range(4):
        parte = "".join(secrets.choice(chars) for _ in range(4))
        partes.append(parte)
    return "JAM-" + "-".join(partes)


def main():
    if len(sys.argv) < 2:
        print("Uso: python gerar_chave.py \"Nome Farmacia\" \"NIF\" \"Serie\"")
        print("Exemplo: python gerar_chave.py \"TRI JAM Luanda\" \"5003507920\" \"FT2026/LDA/\"")
        return
    
    nome = sys.argv[1]
    nif = sys.argv[2] if len(sys.argv) > 2 else ""
    serie = sys.argv[3] if len(sys.argv) > 3 else "FT2026/"
    
    chave = gerar_chave()
    
    print()
    print("=" * 60)
    print("  CHAVE DE ACTIVACAO JAM SOFT")
    print("=" * 60)
    print(f"  Chave:    {chave}")
    print(f"  Farmacia: {nome}")
    print(f"  NIF:      {nif}")
    print(f"  Serie:    {serie}")
    print(f"  Data:     {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 60)
    print()
    print("  Copia esta chave e adiciona-a ao Supabase:")
    print()
    print(f"  INSERT INTO activacoes (chave, farmacia_nome, farmacia_nif, serie_padrao)")
    print(f"  VALUES ('{chave}', '{nome}', '{nif}', '{serie}');")
    print()


if __name__ == "__main__":
    main()
