"""
╔══════════════════════════════════════════════════════════════════════╗
║  MIRAI TELECOM - DASHBOARD PRINCIPAL                                 ║
║  Raio X Carteira + Análise de Deals + Geração de Mailings            ║
╚══════════════════════════════════════════════════════════════════════╝
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

from config import *
from styles import CUSTOM_CSS, render_kpi_card, render_header
from data_processing import (
    carregar_dados_locais,
    cruzar_dados,
    gerar_mailing_customizado,
    gerar_todos_mailings,
    calcular_ranking_comercial,
    calcular_eficiencia_conversao
)
from charts import *

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title=f"{APP_TITLE} v{APP_VERSION}",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════════

@st.cache_data
def load_data():
    """Carrega e processa todos os dados locais."""
    df_mapa, df_deals, df_users = carregar_dados_locais()
    if df_mapa is not None and df_deals is not None:
        df_mapa, df_deals, _, _, _ = cruzar_dados(df_mapa, df_deals)
    return df_mapa, df_deals, df_users

df_mapa, df_deals, df_users = load_data()

# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 10px 0 20px 0;">
        <span style="font-size: 1.3rem; font-weight: 700; color: #660099;">MIRAI</span>
        <span style="font-size: 1.3rem; font-weight: 700; color: #2F5496;"> INSIGHTS</span>
        <br><span style="font-size: 0.75rem; color: #999;">v{APP_VERSION}</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### Status dos Dados")
    mapa_ok = df_mapa is not None
    deals_ok = df_deals is not None
    users_ok = df_users is not None
    st.markdown(f"""
    <div style="display: flex; gap: 6px; justify-content: center; margin: 8px 0 4px 0;">
        <span style="font-size: 0.75rem; padding: 2px 8px; border-radius: 10px;
            background: {'#E8F5E9' if mapa_ok else '#FFEBEE'}; color: {'#2E7D32' if mapa_ok else '#C62828'};">
            {'✓' if mapa_ok else '✗'} Mapa
        </span>
        <span style="font-size: 0.75rem; padding: 2px 8px; border-radius: 10px;
            background: {'#E8F5E9' if deals_ok else '#FFEBEE'}; color: {'#2E7D32' if deals_ok else '#C62828'};">
            {'✓' if deals_ok else '✗'} Deals
        </span>
        <span style="font-size: 0.75rem; padding: 2px 8px; border-radius: 10px;
            background: {'#E8F5E9' if users_ok else '#FFEBEE'}; color: {'#2E7D32' if users_ok else '#C62828'};">
            {'✓' if users_ok else '✗'} Users
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    if df_mapa is not None:
        st.markdown("## Filtros da Carteira")
        seg_filter = st.selectbox("Segmento", ["Todos"] + sorted(df_mapa["SEGMENTO"].unique().tolist()))
        cat_filter = st.selectbox("Categoria M", ["Todos"] + sorted(df_mapa["CATEGORIA_M"].unique().tolist()))
        sem_filter = st.selectbox("Semáforo", ["Todos"] + sorted(df_mapa["SEMAFORO"].unique().tolist()))
        mancha_filter = st.checkbox("Apenas na mancha FTTH", value=True)
    else:
        seg_filter, cat_filter, sem_filter, mancha_filter = "Todos", "Todos", "Todos", False

    st.markdown(f"""
    <div style="text-align:center; padding:20px 0; color: #999; font-size: 0.75rem; position: absolute; bottom: 0; left: 0; right: 0;">
        Mirai Telecom © {datetime.now().year}
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════
st.markdown(render_header(APP_TITLE, APP_SUBTITLE), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# WELCOME SCREEN
# ══════════════════════════════════════════════════════════════════════
if df_mapa is None and df_deals is None:
    st.warning("Nenhum dado carregado. Verifique se os arquivos 'Relatorio...MapaParque...', 'DEAL_*.csv' e 'users.xls' estão no diretório do projeto.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════
# DATA FILTERING
# ══════════════════════════════════════════════════════════════════════
df_filtered = df_mapa.copy() if df_mapa is not None else None
if df_filtered is not None:
    if seg_filter != "Todos": df_filtered = df_filtered[df_filtered["SEGMENTO"] == seg_filter]
    if cat_filter != "Todos": df_filtered = df_filtered[df_filtered["CATEGORIA_M"] == cat_filter]
    if sem_filter != "Todos": df_filtered = df_filtered[df_filtered["SEMAFORO"] == sem_filter]
    if mancha_filter: df_filtered = df_filtered[df_filtered["NA_MANCHA"]]

# ══════════════════════════════════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════════════════════════════════
tab_names = []
if df_mapa is not None: tab_names.extend(["Visão Geral", "Raio X", "Segmentação"])
if df_deals is not None and df_users is not None: tab_names.append("Performance Comercial")
if df_deals is not None: tab_names.append("Deals")
if df_mapa is not None and df_deals is not None: tab_names.append("Cruzamento")
if df_mapa is not None: tab_names.extend(["Mailings", "Dados Brutos"])

if not tab_names:
    st.error("Não há dados suficientes para exibir nenhuma aba.")
    st.stop()

tabs = st.tabs(tab_names)
tab_idx = 0

# ══════════════════════════════════════════════════════════════════════
# TAB: VISAO GERAL
# ══════════════════════════════════════════════════════════════════════
if "Visão Geral" in tab_names:
    with tabs[tab_idx]:
        st.markdown('<h2 class="section-header">Visão Geral da Carteira</h2>', unsafe_allow_html=True)
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.markdown(render_kpi_card("", "Total Clientes", f"{len(df_filtered):,}"))
        # ... more KPIs
    tab_idx += 1

# ══════════════════════════════════════════════════════════════════════
# TAB: RAIO X
# ══════════════════════════════════════════════════════════════════════
if "Raio X" in tab_names:
    with tabs[tab_idx]:
        st.markdown('<h2 class="section-header">Raio X Completo da Carteira</h2>', unsafe_allow_html=True)
        st.plotly_chart(chart_raio_x(df_filtered), use_container_width=True)
        # ... more content
    tab_idx += 1

# ══════════════════════════════════════════════════════════════════════
# TAB: SEGMENTACAO
# ══════════════════════════════════════════════════════════════════════
if "Segmentação" in tab_names:
    with tabs[tab_idx]:
        st.markdown('<h2 class="section-header">Análise de Segmentação</h2>', unsafe_allow_html=True)
        # ... content
    tab_idx += 1

# ══════════════════════════════════════════════════════════════════════
# TAB: PERFORMANCE COMERCIAL
# ══════════════════════════════════════════════════════════════════════
if "Performance Comercial" in tab_names:
    with tabs[tab_idx]:
        st.markdown('<h2 class="section-header">Análise de Performance Comercial</h2>', unsafe_allow_html=True)
        
        ranking_gerente, ranking_time, ranking_vendedor = calcular_ranking_comercial(df_deals, df_users)
        eficiencia = calcular_eficiencia_conversao(df_mapa, df_deals, df_users)

        st.subheader("Ranking por Gerente")
        st.dataframe(ranking_gerente.sort_values("Faturamento_Total", ascending=False), use_container_width=True)

        st.subheader("Ranking por Time")
        st.dataframe(ranking_time.sort_values("Faturamento_Total", ascending=False), use_container_width=True)
        
        st.subheader("Ranking por Vendedor")
        st.dataframe(ranking_vendedor.sort_values("Faturamento_Total", ascending=False), use_container_width=True)

        st.subheader("Eficiência de Conversão (Penetração na Carteira)")
        if not eficiencia.empty:
            st.dataframe(eficiencia, use_container_width=True)
        else:
            st.info("Não foi possível calcular a eficiência. Verifique se a coluna 'Consultor' existe no Mapa Parque.")

    tab_idx += 1

# ══════════════════════════════════════════════════════════════════════
# TAB: DEALS
# ══════════════════════════════════════════════════════════════════════
if "Deals" in tab_names:
    with tabs[tab_idx]:
        st.markdown('<h2 class="section-header">Análise de Deals (Bitrix)</h2>', unsafe_allow_html=True)
        # ... content
    tab_idx += 1

# ... and so on for the rest of the tabs.