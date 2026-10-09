# -*- coding: utf-8 -*-
"""Listagem de chaves de activacao."""
import streamlit as st
import pandas as pd
from services.supabase_client import (
    listar_activacoes,
    revogar_activacao,
    reactivar_activacao,
    apagar_activacao,
)
from services.auth import esta_logado, logout

if not esta_logado():
    st.warning("Sessao expirada. Faz login novamente.")
    st.stop()

with st.sidebar:
    st.markdown("### Painel Master")
    st.markdown("---")
    user = st.session_state.get("utilizador", {})
    st.markdown("**Utilizador:**")
    st.markdown(user.get("email", "?"))
    st.markdown("---")
    if st.button("Terminar Sessao", use_container_width=True, key="logout_chaves"):
        logout()
        st.rerun()

st.title("Chaves de Activacao")
st.markdown("Gerir todas as chaves registadas.")
st.markdown("---")

if st.button("Actualizar", key="refresh_chaves"):
    st.rerun()

chaves = listar_activacoes()

if chaves is None:
    st.error("Erro ao carregar chaves. Verifica a ligacao ao Supabase.")
    st.stop()

if not chaves:
    st.info("Ainda nao existem chaves registadas.")
    st.stop()

col1, col2 = st.columns([3, 1])
with col1:
    filtro = st.text_input("Buscar (chave, farmacia, NIF)", "").strip().lower()
with col2:
    estado_filtro = st.selectbox("Estado", ["Todas", "Activas", "Revogadas"])

chaves_filtradas = []
for c in chaves:
    chave = (c.get("chave") or "").lower()
    nome = (c.get("farmacia_nome") or "").lower()
    nif = (c.get("farmacia_nif") or "").lower()
    activa = c.get("activa", False)
    if filtro and filtro not in chave and filtro not in nome and filtro not in nif:
        continue
    if estado_filtro == "Activas" and not activa:
        continue
    if estado_filtro == "Revogadas" and activa:
        continue
    chaves_filtradas.append(c)

st.markdown("**Total:** " + str(len(chaves_filtradas)) + " chave(s)")

if chaves_filtradas:
    df = pd.DataFrame([
        {
            "Chave": c.get("chave", ""),
            "Farmacia": c.get("farmacia_nome", ""),
            "NIF": c.get("farmacia_nif", ""),
            "Serie": c.get("serie_padrao", ""),
            "Estado": "Activa" if c.get("activa") else "Revogada",
            "Criada": (c.get("criada_em") or "")[:10],
            "Ultima validacao": (c.get("ultima_validacao") or "-")[:16],
        }
        for c in chaves_filtradas
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Accoes")
    chave_sel = st.selectbox(
        "Escolhe uma chave",
        [c.get("chave", "") for c in chaves_filtradas],
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Revogar", use_container_width=True):
            if revogar_activacao(chave_sel):
                st.success("Chave revogada: " + chave_sel)
                st.rerun()
            else:
                st.error("Erro ao revogar")
    with col2:
        if st.button("Reactivar", use_container_width=True):
            if reactivar_activacao(chave_sel):
                st.success("Chave reactivada: " + chave_sel)
                st.rerun()
            else:
                st.error("Erro ao reactivar")
    with col3:
        if st.button("Apagar", use_container_width=True, type="primary"):
            if apagar_activacao(chave_sel):
                st.success("Chave apagada: " + chave_sel)
                st.rerun()
            else:
                st.error("Erro ao apagar")