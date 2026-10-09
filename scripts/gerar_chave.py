# -*- coding: utf-8 -*-
"""
Gestor de chaves de activacao JAM Soft.
Uso:
  python scripts/gerar_chave.py               -> modo interactivo
  python scripts/gerar_chave.py --listar      -> lista chaves
  python scripts/gerar_chave.py --revogar CHAVE -> revoga
  python scripts/gerar_chave.py "Nome" "NIF" "Serie" -> cria directo
"""
import sys
import os
import secrets
import string
from datetime import datetime
from pathlib import Path

# Adicionar pasta raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests


def gerar_chave():
    """Gera chave no formato JAM-XXXX-XXXX-XXXX-XXXX"""
    chars = string.ascii_uppercase + string.digits
    partes = []
    for _ in range(4):
        parte = "".join(secrets.choice(chars) for _ in range(4))
        partes.append(parte)
    return "JAM-" + "-".join(partes)


def obter_credenciais():
    """Le do .env via config_cloud."""
    try:
        from config_cloud import SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY
        return SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY
    except Exception as e:
        print(f"ERRO: Nao foi possivel ler .env: {e}")
        return None, None


def headers_api(key):
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def inserir_chave(url, key, dados):
    """Insere chave no Supabase."""
    endpoint = f"{url}/rest/v1/activacoes"
    r = requests.post(endpoint, headers=headers_api(key), json=dados, timeout=10)
    if r.status_code in (200, 201):
        return True, r.json()
    return False, f"HTTP {r.status_code}: {r.text[:200]}"


def listar_chaves(url, key):
    """Lista todas as chaves."""
    endpoint = f"{url}/rest/v1/activacoes?select=*&order=criada_em.desc"
    r = requests.get(endpoint, headers=headers_api(key), timeout=10)
    if r.status_code != 200:
        return None
    return r.json()


def revogar_chave(url, key, chave):
    """Marca chave como inactiva."""
    endpoint = f"{url}/rest/v1/activacoes?chave=eq.{chave}"
    r = requests.patch(endpoint, headers=headers_api(key), json={"activa": False}, timeout=10)
    return r.status_code in (200, 204)


def activar_chave(url, key, chave):
    """Marca chave como activa."""
    endpoint = f"{url}/rest/v1/activacoes?chave=eq.{chave}"
    r = requests.patch(endpoint, headers=headers_api(key), json={"activa": True}, timeout=10)
    return r.status_code in (200, 204)


def criar_interactivo(url, key):
    """Modo interactivo para criar chave."""
    print()
    print("=" * 60)
    print("  CRIAR NOVA CHAVE - JAM Soft")
    print("=" * 60)
    print()
    
    nome = input("  Nome da farmacia: ").strip()
    if not nome:
        print("  Cancelado.")
        return
    nif = input("  NIF (opcional): ").strip()
    serie = input("  Serie (default FT2026/): ").strip() or "FT2026/"
    notas = input("  Notas (opcional): ").strip()
    
    chave = gerar_chave()
    dados = {
        "chave": chave,
        "farmacia_nome": nome,
        "farmacia_nif": nif,
        "serie_padrao": serie,
        "notas": notas,
        "activa": True,
    }
    
    sucesso, resp = inserir_chave(url, key, dados)
    
    print()
    if sucesso:
        print("=" * 60)
        print("  ✅ CHAVE CRIADA E REGISTADA!")
        print("=" * 60)
        print(f"  Chave:    {chave}")
        print(f"  Farmacia: {nome}")
        print(f"  NIF:      {nif}")
        print(f"  Serie:    {serie}")
        print(f"  Data:     {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print("=" * 60)
        print()
        print("  📋 Copia a CHAVE e usa no wizard de activacao.")
        print()
    else:
        print("=" * 60)
        print("  ❌ ERRO AO CRIAR CHAVE")
        print("=" * 60)
        print(f"  {resp}")
        print()


def listar_interactivo(url, key):
    """Lista todas as chaves formatadas."""
    print()
    print("=" * 90)
    print("  CHAVES REGISTADAS - JAM Soft")
    print("=" * 90)
    
    chaves = listar_chaves(url, key)
    if not chaves:
        print("  Nenhuma chave encontrada.")
        print()
        return
    
    print(f"  {'Chave':<25} {'Farmácia':<25} {'NIF':<12} {'Série':<12} {'Activa'}")
    print("  " + "-" * 85)
    for c in chaves:
        activa = "✅" if c.get("activa") else "❌"
        chave = c.get("chave", "")[:24]
        nome = c.get("farmacia_nome", "")[:24]
        nif = c.get("farmacia_nif", "")[:11]
        serie = c.get("serie_padrao", "")[:11]
        print(f"  {chave:<25} {nome:<25} {nif:<12} {serie:<12} {activa}")
    
    print()
    print(f"  Total: {len(chaves)} chave(s)")
    print()


def main():
    url, key = obter_credenciais()
    if not url or not key:
        print("ERRO: .env nao configurado.")
        return
    
    args = sys.argv[1:]
    
    # Modo linha de comando
    if args:
        if args[0] == "--listar" or args[0] == "-l":
            listar_interactivo(url, key)
            return
        
        if args[0] == "--revogar" and len(args) >= 2:
            chave = args[1]
            if revogar_chave(url, key, chave):
                print(f"✅ Chave revogada: {chave}")
            else:
                print(f"❌ Erro ao revogar: {chave}")
            return
        
        if args[0] == "--activar" and len(args) >= 2:
            chave = args[1]
            if activar_chave(url, key, chave):
                print(f"✅ Chave activada: {chave}")
            else:
                print(f"❌ Erro ao activar: {chave}")
            return
        
        # Modo directo (nome, nif, serie)
        nome = args[0]
        nif = args[1] if len(args) > 1 else ""
        serie = args[2] if len(args) > 2 else "FT2026/"
        
        chave = gerar_chave()
        dados = {
            "chave": chave,
            "farmacia_nome": nome,
            "farmacia_nif": nif,
            "serie_padrao": serie,
            "activa": True,
        }
        
        sucesso, resp = inserir_chave(url, key, dados)
        if sucesso:
            print(f"✅ Chave criada: {chave}")
            print(f"   Farmácia: {nome} | NIF: {nif} | Série: {serie}")
        else:
            print(f"❌ Erro: {resp}")
        return
    
    # Modo interactivo (menu)
    print()
    print("=" * 60)
    print("  GESTOR DE CHAVES - JAM Soft")
    print("=" * 60)
    print()
    print("  1) Criar nova chave")
    print("  2) Listar chaves existentes")
    print("  3) Revogar chave")
    print("  4) Activar chave")
    print("  0) Sair")
    print()
    
    opcao = input("  Escolhe uma opcao: ").strip()
    
    if opcao == "1":
        criar_interactivo(url, key)
    elif opcao == "2":
        listar_interactivo(url, key)
    elif opcao == "3":
        chave = input("  Chave a revogar: ").strip().upper()
        if revogar_chave(url, key, chave):
            print(f"✅ Chave revogada: {chave}")
        else:
            print(f"❌ Erro ao revogar: {chave}")
    elif opcao == "4":
        chave = input("  Chave a activar: ").strip().upper()
        if activar_chave(url, key, chave):
            print(f"✅ Chave activada: {chave}")
        else:
            print(f"❌ Erro ao activar: {chave}")
    else:
        print("  A sair...")


if __name__ == "__main__":
    main()
