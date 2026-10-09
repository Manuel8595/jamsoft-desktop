# -*- coding: utf-8 -*-
"""Estatisticas e graficos das chaves."""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
    if st.button("Terminar Sessao", use_container_width=True, key="logout_estat"):
        logout()
        st.rerun()

st.title("Estatisticas")
st.markdown("Metricas e visao geral das chaves de activacao.")
st.markdown("---")

chaves = listar_activacoes()

if chaves is None:
    st.error("Erro ao carregar chaves.")
    st.stop()

if not chaves:
    st.info("Ainda nao existem chaves registadas.")
    st.stop()

# KPIs
total = len(chaves)
activas = sum(1 for c in chaves if c.get("activa"))
revogadas = total - activas

# Chaves com validacao recente (ultimos 7 dias)
agora = datetime.now()
limite = agora - timedelta(days=7)
validadas_recentes = 0
for c in chaves:
    uv = c.get("ultima_validacao")
    if uv:
        try:
            dt = datetime.fromisoformat(uv.replace("Z", "").split(".")[0])
            if dt >= limite:
                validadas_recentes += 1
        except Exception:
            pass

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Chaves", total)
with col2:
    st.metric("Activas", activas)
with col3:
    st.metric("Revogadas", revogadas)
with col4:
    st.metric("Validadas (7 dias)", validadas_recentes)

st.markdown("---")

# Grafico: chaves por farmacia
st.markdown("### Chaves por Farmacia")
contagem = {}
for c in chaves:
    nome = c.get("farmacia_nome") or "(sem nome)"
    contagem[nome] = contagem.get(nome, 0) + 1

if contagem:
    df_graf = pd.DataFrame([
        {"Farmacia": k, "Chaves": v}
        for k, v in sorted(contagem.items(), key=lambda x: -x[1])
    ])
    st.bar_chart(df_graf, x="Farmacia", y="Chaves")

st.markdown("---")

# Grafico: criacoes por mes
st.markdown("### Criacoes por Mes")
meses = {}
for c in chaves:
    criada = c.get("criada_em")
    if criada:
        mes = criada[:7]  # YYYY-MM
        meses[mes] = meses.get(mes, 0) + 1

if meses:
    df_meses = pd.DataFrame([
        {"Mes": k, "Chaves": v}
        for k, v in sorted(meses.items())
    ])
    st.bar_chart(df_meses, x="Mes", y="Chaves")

st.markdown("---")

# Tabela: ultimas validacoes
st.markdown("### Ultimas Validacoes")
validadas = [
    c for c in chaves if c.get("ultima_validacao")
]
validadas.sort(key=lambda x: x.get("ultima_validacao", ""), reverse=True)

if validadas:
    df_val = pd.DataFrame([
        {
            "Chave": c.get("chave", ""),
            "Farmacia": c.get("farmacia_nome", ""),
            "Ultima validacao": (c.get("ultima_validacao") or "")[:16],
        }
        for c in validadas[:10]
    ])
    st.dataframe(df_val, use_container_width=True, hide_index=True)
else:
    st.info("Ainda nao ha validacoes registadas.")