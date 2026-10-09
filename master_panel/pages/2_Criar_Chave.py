# -*- coding: utf-8 -*-
"""Formulario para criar nova chave."""
import streamlit as st
import secrets
import string
from services.supabase_client import criar_activacao
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
    if st.button("Terminar Sessao", use_container_width=True, key="logout_criar"):
        logout()
        st.rerun()

st.title("Criar Nova Chave")
st.markdown("Gera uma nova chave de activacao para uma farmacia.")
st.markdown("---")


def gerar_chave():
    chars = string.ascii_uppercase + string.digits
    partes = []
    for _ in range(4):
        parte = "".join(secrets.choice(chars) for _ in range(4))
        partes.append(parte)
    return "JAM-" + "-".join(partes)


with st.form("form_criar_chave"):
    nome = st.text_input("Nome da Farmacia *", placeholder="TRI JAM Luanda")
    nif = st.text_input("NIF", placeholder="5003507920")
    serie = st.text_input("Serie de facturacao", value="FT2026/")
    notas = st.text_area("Notas (opcional)", placeholder="Farmácia principal")
    
    submitted = st.form_submit_button("Criar Chave", use_container_width=True, type="primary")

if submitted:
    if not nome:
        st.error("Preenche o nome da farmacia.")
    else:
        chave = gerar_chave()
        sucesso, resp = criar_activacao(
            chave=chave,
            farmacia_nome=nome,
            farmacia_nif=nif,
            serie_padrao=serie,
            notas=notas,
        )
        
        if sucesso:
            st.success("Chave criada com sucesso!")
            st.markdown("---")
            st.markdown("### Chave de Activacao")
            st.code(chave, language=None)
            st.info("Copia esta chave e usa-a no wizard de activacao da app desktop.")
        else:
            st.error("Erro: " + str(resp))