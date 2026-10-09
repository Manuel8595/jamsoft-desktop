# -*- coding: utf-8 -*-
import os
import requests
import streamlit as st

_URL_PADRAO = "https://bkbeedknuunjpuvbpgxr.supabase.co"
_KEY_PADRAO = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJrYmVlZGtudXVuanB1dmJwZ3hyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAxNzQ3MzAsImV4cCI6MjEwNTc1MDczMH0.pS4c4DMOPFHyNT-GgGWdt88LQVp9IrtGc8ZwpovnIcU"


def _obter_credenciais():
    url = ""
    key = ""
    try:
        url = st.secrets.get("SUPABASE_URL", "") or url
        key = st.secrets.get("SUPABASE_KEY", "") or key
    except Exception:
        pass
    url = os.environ.get("SUPABASE_URL", "") or url
    key = os.environ.get("SUPABASE_KEY", "") or key
    url = url or _URL_PADRAO
    key = key or _KEY_PADRAO
    return url.strip().rstrip("/"), key.strip()


SUPABASE_URL, SUPABASE_KEY = _obter_credenciais()


def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def listar_activacoes():
    url = SUPABASE_URL + "/rest/v1/activacoes?select=*&order=criada_em.desc"
    r = requests.get(url, headers=get_headers(), timeout=10)
    if r.status_code != 200:
        return None
    return r.json()


def criar_activacao(chave, farmacia_nome, farmacia_nif, serie_padrao, notas=""):
    url = SUPABASE_URL + "/rest/v1/activacoes"
    dados = {"chave": chave, "farmacia_nome": farmacia_nome, "farmacia_nif": farmacia_nif, "serie_padrao": serie_padrao, "notas": notas, "activa": True}
    r = requests.post(url, headers=get_headers(), json=dados, timeout=10)
    if r.status_code in (200, 201):
        return True, r.json()
    return False, r.text[:300]


def actualizar_activacao(chave, campos):
    url = SUPABASE_URL + "/rest/v1/activacoes?chave=eq." + chave
    r = requests.patch(url, headers=get_headers(), json=campos, timeout=10)
    return r.status_code in (200, 204)


def revogar_activacao(chave):
    return actualizar_activacao(chave, {"activa": False})


def reactivar_activacao(chave):
    return actualizar_activacao(chave, {"activa": True})


def apagar_activacao(chave):
    url = SUPABASE_URL + "/rest/v1/activacoes?chave=eq." + chave
    r = requests.delete(url, headers=get_headers(), timeout=10)
    return r.status_code in (200, 204)
