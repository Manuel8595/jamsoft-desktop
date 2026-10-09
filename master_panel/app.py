# -*- coding: utf-8 -*-
import streamlit as st

st.set_page_config(
    page_title="JAM Soft - Painel Master",
    page_icon=":material/dashboard:",
    layout="wide",
    initial_sidebar_state="expanded",
)

from services.auth import login_supabase, logout, esta_logado

st.markdown("""
<style>
    .stApp { background: #0f172a; }
    h1, h2, h3 { color: #f8fafc; }
    .login-container {
        max-width: 400px; margin: 80px auto; padding: 40px;
        background: #1e293b; border-radius: 15px;
        border: 2px solid #7c3aed;
    }
    .login-title {
        text-align: center; color: #f8fafc; font-size: 28px;
        font-weight: bold; margin-bottom: 10px;
    }
    .login-sub {
        text-align: center; color: #94a3b8; font-size: 14px;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)


def mostrar_login():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Painel Master</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-sub">JAM Soft - Gestao de Chaves</div>', unsafe_allow_html=True)
    email = st.text_input("Email", key="login_email")
    senha = st.text_input("Senha", type="password", key="login_senha")
    if st.button("Entrar", use_container_width=True, type="primary"):
        if not email or not senha:
            st.error("Preenche email e senha")
        else:
            sucesso, dados = login_supabase(email, senha)
            if sucesso:
                st.session_state["logado"] = True
                st.session_state["utilizador"] = dados["user"]
                st.session_state["token"] = dados["access_token"]
                st.rerun()
            else:
                st.error(dados)
    st.markdown('</div>', unsafe_allow_html=True)


if not esta_logado():
    mostrar_login()
else:
    with st.sidebar:
        st.markdown("### Painel Master")
        st.markdown("---")
        user = st.session_state.get("utilizador", {})
        st.markdown("**Utilizador:**")
        st.markdown(user.get("email", "?"))
        st.markdown("---")
        st.markdown("**Menu:**")
        st.markdown("- Inicio")
        st.markdown("- Chaves")
        st.markdown("- Criar Chave")
        st.markdown("- Estatisticas")
        st.markdown("---")
        if st.button("Terminar Sessao", use_container_width=True):
            logout()
            st.rerun()

    st.title("Painel Master JAM Soft")
    st.markdown("Bem-vindo ao centro de gestao de chaves de activacao.")
    st.markdown("---")
    st.markdown("""
    ### O que podes fazer aqui:

    - **Chaves** - Ver, activar, revogar todas as chaves
    - **Criar Chave** - Gerar nova chave para uma farmacia
    - **Estatisticas** - Ver metricas e graficos

    Usa o menu lateral para navegar.
    """)