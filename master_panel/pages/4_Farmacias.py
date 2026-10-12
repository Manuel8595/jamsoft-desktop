# -*- coding: utf-8 -*-
"""Vista agrupada de farmacias (chaves agrupadas por NIF)."""
import streamlit as st
import pandas as pd
from services.supabase_client import listar_activacoes
from services.auth import esta_logado, logout

if not esta_logado():
    st.warning("Sessao expirada.")
    st.stop()

with st.sidebar:
    st.markdown("### Painel Master")
    st.markdown("---")
    user = st.session_state.get("utilizador", {})
    st.markdown("**Utilizador:**")
    st.markdown(user.get("email", "?"))
    st.markdown("---")
    if st.button("Terminar Sessao", use_container_width=True, key="logout_farm"):
        logout()
        st.rerun()

st.title("Farmacias")
st.markdown("Vista agrupada — chaves por empresa (NIF).")
st.markdown("---")

chaves = listar_activacoes()
if not chaves:
    st.info("Ainda nao existem chaves.")
    st.stop()

# Agrupar por NIF
grupos = {}
for c in chaves:
    nif = c.get("farmacia_nif") or "(sem NIF)"
    nome = c.get("farmacia_nome") or "(sem nome)"
    chave_activa = c.get("activa", False)
    
    if nif not in grupos:
        grupos[nif] = {
            "nif": nif,
            "nomes": set(),
            "total_chaves": 0,
            "activas": 0,
            "inactivas": 0,
            "chaves": [],
            "ultima_validacao": None,
        }
    
    g = grupos[nif]
    g["nomes"].add(nome)
    g["total_chaves"] += 1
    if chave_activa:
        g["activas"] += 1
    else:
        g["inactivas"] += 1
    g["chaves"].append(c)
    
    # Data ultima validacao
    uv = c.get("ultima_validacao")
    if uv:
        if not g["ultima_validacao"] or uv > g["ultima_validacao"]:
            g["ultima_validacao"] = uv

# KPIs globais
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Empresas", len(grupos))
with col2:
    st.metric("Total de Chaves", len(chaves))
with col3:
    activas = sum(1 for c in chaves if c.get("activa"))
    st.metric("Chaves Activas", activas)
with col4:
    inactivas = len(chaves) - activas
    st.metric("Chaves Revogadas", inactivas)

st.markdown("---")

# Lista agrupada
for nif in sorted(grupos.keys()):
    g = grupos[nif]
    nome_principal = list(g["nomes"])[0] if g["nomes"] else "(sem nome)"
    
    with st.expander(f"**{nome_principal}** — NIF {nif} ({g['activas']} activas)", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Chaves", g["total_chaves"])
        with col2:
            st.metric("Activas", g["activas"])
        with col3:
            st.metric("Revogadas", g["inactivas"])
        with col4:
            uv = g["ultima_validacao"]
            if uv:
                st.metric("Ultima Validacao", uv[:10])
            else:
                st.metric("Ultima Validacao", "-")
        
        st.markdown("---")
        
        # Tabela de chaves
        df = pd.DataFrame([
            {
                "Chave": c.get("chave", ""),
                "Nome": c.get("farmacia_nome", ""),
                "Serie": c.get("serie_padrao", ""),
                "Estado": "Activa" if c.get("activa") else "Revogada",
                "Criada": (c.get("criada_em") or "")[:10],
            }
            for c in g["chaves"]
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)