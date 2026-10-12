# -*- coding: utf-8 -*-
"""Historico de validacoes de chaves."""
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
    if st.button("Terminar Sessao", use_container_width=True, key="logout_hist"):
        logout()
        st.rerun()

st.title("Historico")
st.markdown("Ultimas validacoes das chaves (consultas online).")
st.markdown("---")

chaves = listar_activacoes()
if not chaves:
    st.info("Ainda nao existem chaves.")
    st.stop()

# Filtrar as que tem validacao
validadas = [c for c in chaves if c.get("ultima_validacao")]
validadas.sort(key=lambda x: x.get("ultima_validacao", ""), reverse=True)

st.metric("Total de Validacoes", len(validadas))

if not validadas:
    st.info("Ainda nao ha validacoes registadas.")
    st.stop()

st.markdown("---")

# Filtros
col1, col2 = st.columns([3, 1])
with col1:
    filtro = st.text_input("Buscar (chave, farmacia, NIF)", "").strip().lower()
with col2:
    limite = st.selectbox("Mostrar", [10, 25, 50, 100], index=1)

validadas_filtradas = []
for c in validadas:
    chave = (c.get("chave") or "").lower()
    nome = (c.get("farmacia_nome") or "").lower()
    nif = (c.get("farmacia_nif") or "").lower()
    if filtro and filtro not in chave and filtro not in nome and filtro not in nif:
        continue
    validadas_filtradas.append(c)

st.markdown(f"**A mostrar:** {min(limite, len(validadas_filtradas))} de {len(validadas_filtradas)}")

# Tabela
df = pd.DataFrame([
    {
        "Data/Hora": (c.get("ultima_validacao") or "")[:19].replace("T", " "),
        "Chave": c.get("chave", ""),
        "Farmacia": c.get("farmacia_nome", ""),
        "NIF": c.get("farmacia_nif", ""),
        "Estado": "Activa" if c.get("activa") else "Revogada",
    }
    for c in validadas_filtradas[:limite]
])
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("### Detalhes")

# Selector para ver detalhes
if validadas_filtradas:
    chave_sel = st.selectbox(
        "Escolhe uma chave para ver detalhes",
        [c.get("chave", "") for c in validadas_filtradas[:limite]],
    )
    
    for c in validadas_filtradas:
        if c.get("chave") == chave_sel:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Chave:**")
                st.code(c.get("chave", ""))
                st.markdown("**Farmacia:**")
                st.markdown(c.get("farmacia_nome", ""))
                st.markdown("**NIF:**")
                st.markdown(c.get("farmacia_nif", ""))
            with col2:
                st.markdown("**Serie:**")
                st.markdown(c.get("serie_padrao", ""))
                st.markdown("**Criada em:**")
                st.markdown((c.get("criada_em") or "")[:19].replace("T", " "))
                st.markdown("**Ultima validacao:**")
                st.markdown((c.get("ultima_validacao") or "")[:19].replace("T", " "))
            
            if c.get("notas"):
                st.markdown("**Notas:**")
                st.info(c["notas"])
            break