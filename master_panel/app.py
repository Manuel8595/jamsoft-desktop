# -*- coding: utf-8 -*-
import streamlit as st
import base64
from pathlib import Path

st.set_page_config(
    page_title="JAM Soft - Painel Master",
    page_icon="🎛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from services.auth import login_supabase, logout, esta_logado

def carregar_logo_base64():
    caminho = Path(__file__).parent.parent / "logos" / "JamLogo_transparente.png"
    if not caminho.exists():
        caminho = Path(__file__).parent / "logos" / "JamLogo_transparente.png"
    if caminho.exists():
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = carregar_logo_base64()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp {
        background: radial-gradient(ellipse at top, #1e1b4b 0%, #0f172a 50%, #020617 100%);
    }
    header[data-testid="stHeader"] { background: transparent; }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid #334155;
    }
    .login-wrapper {
        display: flex; justify-content: center; align-items: flex-start;
        min-height: 70vh; padding: 40px 20px;
        padding-top: 5vh;
    }
    .login-card {
        max-width: 420px; width: 100%; padding: 50px 40px;
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95));
        border-radius: 24px;
        border: 1px solid rgba(124, 58, 237, 0.3);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 100px -20px rgba(124, 58, 237, 0.3);
        backdrop-filter: blur(10px);
        animation: fadeIn 0.6s ease-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .login-logo { text-align: center; margin-bottom: 10px; }
    .login-logo img { max-width: 160px; }
    .login-logo img {
        max-width: 200px; height: auto;
        filter: drop-shadow(0 0 30px rgba(124, 58, 237, 0.5));
        animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
    }
    .login-title {
        text-align: center; font-size: 28px; font-weight: 700;
        color: #f8fafc; margin-bottom: 8px; letter-spacing: -0.5px;
    }
    .login-title span {
        background: linear-gradient(135deg, #a78bfa 0%, #fbbf24 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .login-subtitle {
        text-align: center; font-size: 14px;
        color: #94a3b8; margin-bottom: 35px;
    }
    div[data-testid="stTextInput"] input {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 2px solid #334155 !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        font-size: 15px !important;
        padding: 12px 16px !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.15) !important;
    }
    div[data-testid="stTextInput"] label {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        padding: 14px !important;
        box-shadow: 0 10px 30px -10px rgba(124, 58, 237, 0.5) !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
    }
    div[data-testid="stMetricValue"] {
        color: #a78bfa !important;
        font-weight: 700 !important;
    }
    h1, h2, h3 { color: #f8fafc !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .footer-login {
        text-align: center; color: #64748b;
        font-size: 12px; margin-top: 25px;
    }
</style>
""", unsafe_allow_html=True)


def mostrar_login():
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    if LOGO_B64:
        st.markdown(
            '<div class="login-logo"><img src="data:image/png;base64,' + LOGO_B64 + '" /></div>',
            unsafe_allow_html=True
        )
    st.markdown('<div class="login-title">🎛️ <span>Painel Master</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">JAM Soft — Gestão de Chaves</div>', unsafe_allow_html=True)
    email = st.text_input("📧 Email", key="login_email", placeholder="admin@jamsoft.ao")
    senha = st.text_input("🔒 Senha", type="password", key="login_senha", placeholder="••••••••")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Entrar no Painel", use_container_width=True, type="primary"):
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
    st.markdown('<div class="footer-login">🔒 Ligação segura · JAM Soft v1.0.3</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


if not esta_logado():
    mostrar_login()
else:
    with st.sidebar:
        st.markdown("### 🎛️ Painel Master")
        st.markdown("---")
        user = st.session_state.get("utilizador", {})
        st.markdown("**Utilizador:**")
        st.markdown(user.get("email", "?"))
        st.markdown("---")
        st.markdown("**Menu:**")
        st.markdown("- Início")
        st.markdown("- Chaves")
        st.markdown("- Criar Chave")
        st.markdown("- Estatísticas")
        st.markdown("---")
        if st.button("🚪 Terminar Sessão", use_container_width=True, key="logout_main"):
            logout()
            st.rerun()

    st.title("🎛️ Painel Master JAM Soft")
    st.markdown("Bem-vindo ao centro de gestão de chaves de activação.")
    st.markdown("---")
    st.markdown("""
    ### 📋 O que podes fazer aqui:

    - **🔑 Chaves** — Ver, activar, revogar todas as chaves
    - **➕ Criar Chave** — Gerar nova chave para uma farmácia
    - **📊 Estatísticas** — Ver métricas e gráficos

    Usa o menu lateral para navegar.
    """)