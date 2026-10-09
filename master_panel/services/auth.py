# -*- coding: utf-8 -*-
"""Autenticacao Supabase Auth para o Painel Master."""
import requests
import streamlit as st
from .supabase_client import SUPABASE_URL, SUPABASE_KEY


def login_supabase(email, password):
    """Faz login no Supabase Auth.
    Retorna (sucesso, dados_ou_erro).
    """
    url = SUPABASE_URL + "/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
    }
    dados = {"email": email, "password": password}
    try:
        r = requests.post(url, headers=headers, json=dados, timeout=10)
    except Exception as e:
        return False, "Sem ligacao: " + str(e)
    if r.status_code != 200:
        return False, "Login falhou (" + str(r.status_code) + ")"
    resposta = r.json()
    token = resposta.get("access_token", "")
    if not token:
        return False, "Token invalido"
    return True, {
        "access_token": token,
        "refresh_token": resposta.get("refresh_token", ""),
        "user": resposta.get("user", {}),
    }


def logout():
    """Limpa a sessao."""
    for key in list(st.session_state.keys()):
        if key in ("logado", "utilizador", "token"):
            del st.session_state[key]


def esta_logado():
    """Verifica se ha sessao activa."""
    return st.session_state.get("logado", False)
