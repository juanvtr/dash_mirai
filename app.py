"""
╔══════════════════════════════════════════════════════════════════════╗
║  MIRAI TELECOM - DASHBOARD PRINCIPAL                                ║
║  Raio X Carteira + Análise de Deals + Geração de Mailings          ║
║                                                                      ║
║  Uso: streamlit run app.py                                           ║
║  Upload: Mapa Parque (CSV ;) + Deals Bitrix (CSV ;)                ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

from config import (
    CORES, SEGMENTOS_ORDEM, SEGMENTOS_ICONS, SEGMENTOS_DESC,
    APP_TITLE, APP_SUBTITLE, APP_ICON, APP_VERSION,
)
from styles import CUSTOM_CSS, render_kpi_card, render_header
from data_processing import (
    processar_mapa_parque, processar_deals, cruzar_dados,
    gerar_mailing_customizado, gerar_todos_mailings,
)
from charts import (
    chart_semaforo, chart_segmentacao, chart_categoria_m, chart_posse,
    chart_raio_x, chart_heatmap_segmento_catm, chart_fidelizacao,
    chart_deals_por_fase, chart_deals_por_tipo,
    chart_deals_por_gerencia, chart_deals_por_consultor,
    chart_penetracao_deals, chart_penetracao_por_segmento,
    chart_portabilidade_potencial_vs_real,
)

from data_processing import analisar_performance_vendedores


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
# HELPER: CSV para download
# ══════════════════════════════════════════════════════════════════════

def df_to_csv_bytes(df):
    """Converte DataFrame para bytes CSV (utf-8-sig com ;)."""
    return df.to_csv(sep=";", index=False, encoding="utf-8-sig").encode("utf-8-sig")


def df_to_excel_bytes(mailings_dict):
    """Converte dict de DataFrames para Excel multi-aba."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for nome, df in mailings_dict.items():
            sheet_name = nome[:31]  # Excel max 31 chars
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR - UPLOAD E FILTROS
# ══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 20px 0;">
        <span style="font-size: 2.5rem;"></span><br>
        <span style="font-size: 1.3rem; font-weight: 700; color: #660099;">MIRAI</span>
        <span style="font-size: 1.3rem; font-weight: 700; color: #2F5496;"> INSIGHTS</span>
        <br><span style="font-size: 0.75rem; color: #999;">v{ver}</span>
    </div>
    """.format(ver=APP_VERSION), unsafe_allow_html=True)

    st.markdown("---")

    # ── Upload: Mapa Parque ──
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #F0E6FA 0%, #E8EEF7 100%);
        border: 1px solid #D4C5E2; border-radius: 10px;
        padding: 12px 14px; margin-bottom: 10px;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <span style="font-size: 1.3rem;">🗺️</span>
            <span style="font-weight: 700; color: #660099; font-size: 0.9rem;">Mapa Parque</span>
        </div>
        <div style="font-size: 0.72rem; color: #666; line-height: 1.4;">
            <code style="background:#fff; padding:1px 4px; border-radius:3px; font-size:0.7rem;">RelatorioInfoB2B_MapaParqueVisaoCliente_*.csv</code><br>
            CSV separado por <b>;</b> · Encoding automático
        </div>
    </div>
    """, unsafe_allow_html=True)
    uploaded_mapa = st.file_uploader(
        "mapa_upload", type=["csv"], key="mapa", label_visibility="collapsed",
    )

    # ── Upload: Deals ──
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #E8EEF7 0%, #E1F5FE 100%);
        border: 1px solid #B8CCE4; border-radius: 10px;
        padding: 12px 14px; margin-bottom: 10px;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <span style="font-size: 1.3rem;"></span>
            <span style="font-weight: 700; color: #2F5496; font-size: 0.9rem;">Deals Bitrix</span>
        </div>
        <div style="font-size: 0.72rem; color: #666; line-height: 1.4;">
            <code style="background:#fff; padding:1px 4px; border-radius:3px; font-size:0.7rem;">DEAL_*.csv</code><br>
            CSV exportado do Bitrix · Separador <b>;</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    uploaded_deals = st.file_uploader(
        "deals_upload", type=["csv"], key="deals", label_visibility="collapsed",
    )

    # Status dos uploads
    mapa_ok = uploaded_mapa is not None or "df_mapa" in st.session_state
    deals_ok = uploaded_deals is not None or "df_deals" in st.session_state
    st.markdown(f"""
    <div style="display: flex; gap: 6px; justify-content: center; margin: 8px 0 4px 0;">
        <span style="font-size: 0.75rem; padding: 2px 8px; border-radius: 10px;
            background: {'#E8F5E9' if mapa_ok else '#FFF3E0'}; color: {'#2E7D32' if mapa_ok else '#E65100'};">
            {'✓' if mapa_ok else '○'} Mapa
        </span>
        <span style="font-size: 0.75rem; padding: 2px 8px; border-radius: 10px;
            background: {'#E8F5E9' if deals_ok else '#FFF3E0'}; color: {'#2E7D32' if deals_ok else '#E65100'};">
            {'✓' if deals_ok else '○'} Deals
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Filtros (aparecem quando dados carregados)
    if "df_mapa" in st.session_state and st.session_state["df_mapa"] is not None:
        st.markdown("## 🔍 Filtros")
        df_ref = st.session_state["df_mapa"]

        segmentos_opts = ["Todos"] + sorted(df_ref["SEGMENTO"].unique().tolist())
        seg_filter = st.selectbox("Segmento", segmentos_opts)

        cat_opts = ["Todos"] + sorted(df_ref["CATEGORIA_M"].unique().tolist())
        cat_filter = st.selectbox("Categoria M", cat_opts)

        sem_opts = ["Todos"] + sorted(df_ref["SEMAFORO"].unique().tolist())
        sem_filter = st.selectbox("Semáforo", sem_opts)

        mancha_filter = st.checkbox("Apenas na mancha FTTH")

        st.markdown("---")
    else:
        seg_filter = "Todos"
        cat_filter = "Todos"
        sem_filter = "Todos"
        mancha_filter = False

    st.markdown(f"""
    <div style="text-align:center; padding:20px 0; color: #999; font-size: 0.75rem;">
        Mirai Telecom © {datetime.now().year}<br>
        Data Analytics
    </div>
    """, unsafe_allow_html=True)

if "df_deals" in st.session_state and st.session_state["df_deals"] is not None:
    st.markdown("### 📅 Periodo do Bitrix")
    df_d = st.session_state["df_deals"]
    
    # Define os limites do calendário baseado nos dados reais
    min_date = df_d['Criado'].min().date()
    max_date = df_d['Criado'].max().date()
    
    # Widget de range de data
    data_range = st.date_input(
        "Selecione o intervalo",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY"
    )
    
    # Filtro de Gerencia (Multiselect para analise comparativa)
    st.markdown("### 🏢 Gerencias")
    gerencias_opts = sorted(df_d['Gerência'].unique().tolist())
    gerencias_sel = st.multiselect("Filtrar Times", gerencias_opts, default=gerencias_opts)

# ══════════════════════════════════════════════════════════════════════
# PROCESSAMENTO DOS DADOS
# ══════════════════════════════════════════════════════════════════════

# Processar Mapa Parque
if uploaded_mapa is not None:
    if "df_mapa" not in st.session_state or st.session_state.get("mapa_name") != uploaded_mapa.name:
        with st.spinner("Processando Mapa Parque..."):
            df_mapa = processar_mapa_parque(uploaded_mapa)
            st.session_state["df_mapa"] = df_mapa
            st.session_state["mapa_name"] = uploaded_mapa.name
    df_mapa = st.session_state["df_mapa"]
else:
    df_mapa = st.session_state.get("df_mapa", None)

# Processar Deals
if uploaded_deals is not None:
    if "df_deals" not in st.session_state or st.session_state.get("deals_name") != uploaded_deals.name:
        with st.spinner("Processando Deals..."):
            df_deals = processar_deals(uploaded_deals)
            st.session_state["df_deals"] = df_deals
            st.session_state["deals_name"] = uploaded_deals.name
    df_deals = st.session_state["df_deals"]
else:
    df_deals = st.session_state.get("df_deals", None)

# Cruzamento
if df_mapa is not None and df_deals is not None:
    if "cruzamento_done" not in st.session_state:
        df_mapa, df_deals, cnpjs_mapa, cnpjs_deal, cnpjs_comum = cruzar_dados(df_mapa, df_deals)
        st.session_state["df_mapa"] = df_mapa
        st.session_state["df_deals"] = df_deals
        st.session_state["cnpjs_comum"] = cnpjs_comum
        st.session_state["cruzamento_done"] = True
    cnpjs_comum = st.session_state.get("cnpjs_comum", set())


# ══════════════════════════════════════════════════════════════════════
# HEADER PRINCIPAL
# ══════════════════════════════════════════════════════════════════════

st.markdown(render_header(APP_TITLE, APP_SUBTITLE), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# SEM DADOS? TELA DE BOAS-VINDAS
# ══════════════════════════════════════════════════════════════════════

if df_mapa is None and df_deals is None:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #F8F5FC, #E8EEF7);
        padding: 3rem; border-radius: 16px; text-align: center;
        margin: 2rem 0; box-shadow: 0 4px 20px rgba(0,0,0,0.05);">
        <span style="font-size: 4rem;">📂</span>
        <h3 style="color: #660099; margin-top: 1rem;">Bem-vindo ao Mirai Insights</h3>
        <p style="color: #666; max-width: 500px; margin: 0 auto;">
            Carregue o <b>Mapa Parque</b> e/ou os <b>Deals do Bitrix</b>
            na barra lateral para iniciar as análises.
        </p>
        <div style="margin-top: 2rem; display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
            <div style="background: white; padding: 1rem 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <b style="color: #660099;">1.</b> Upload Mapa Parque (CSV)
            </div>
            <div style="background: white; padding: 1rem 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <b style="color: #660099;">2.</b> Upload Deals Bitrix (CSV)
            </div>
            <div style="background: white; padding: 1rem 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <b style="color: #660099;">3.</b> Explore & Gere Mailings
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ══════════════════════════════════════════════════════════════════════
# APLICAR FILTROS NO MAPA PARQUE
# ══════════════════════════════════════════════════════════════════════

df_filtered = df_mapa.copy() if df_mapa is not None else None

if df_filtered is not None:
    if seg_filter != "Todos":
        df_filtered = df_filtered[df_filtered["SEGMENTO"] == seg_filter]
    if cat_filter != "Todos":
        df_filtered = df_filtered[df_filtered["CATEGORIA_M"] == cat_filter]
    if sem_filter != "Todos":
        df_filtered = df_filtered[df_filtered["SEMAFORO"] == sem_filter]
    if mancha_filter:
        df_filtered = df_filtered[df_filtered["NA_MANCHA"]]


# ══════════════════════════════════════════════════════════════════════
# HELPER: Renderizar seção de mailings com cards estilo PDF
# ══════════════════════════════════════════════════════════════════════

_OBJETIVO_CORES = {
    "RENOVAR": "#9B59B6", "UP": "#3498DB", "VENDA": "#2F5496",
    "RELACIONAMENTO": "#F39C12", "TROCA": "#1ABC9C", "DIGITALIZAR": "#E74C3C",
}

def _get_obj_color(objetivo):
    for key, color in _OBJETIVO_CORES.items():
        if key in objetivo.upper():
            return color
    return "#660099"

def _render_mailing_section(secao_dict):
    """Renderiza cards de mailing para uma seção (1/2/3) do Raio X."""
    cols = st.columns(2)
    for i, (codigo, mailing_df) in enumerate(secao_dict.items()):
        if len(mailing_df) == 0:
            continue
        col = cols[i % 2]
        with col:
            objetivo = mailing_df["OBJETIVO"].iloc[0] if "OBJETIVO" in mailing_df.columns else ""
            obs = mailing_df["OBSERVACAO"].iloc[0] if "OBSERVACAO" in mailing_df.columns else ""
            cor = _get_obj_color(objetivo)
            display_name = codigo.split("_", 1)[1].replace("_", " ") if "_" in codigo else codigo

            st.markdown(f"""
            <div style="
                background: white; border-radius: 10px; padding: 14px;
                border-left: 5px solid {cor}; margin-bottom: 12px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.08);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; color: #333; font-size: 0.9rem;">
                        {codigo.split('_')[0]} {display_name}
                    </span>
                    <span style="background: {cor}; color: white; padding: 2px 10px;
                        border-radius: 12px; font-size: 0.7rem; font-weight: 600;">
                        {len(mailing_df):,} clientes
                    </span>
                </div>
                <div style="color: white; background: {cor}; padding: 4px 10px;
                    border-radius: 6px; margin: 6px 0; font-size: 0.78rem; font-weight: 600;">
                    Objetivo: {objetivo}
                </div>
                <div style="font-size: 0.72rem; color: #666; line-height: 1.5;">
                    {obs}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.download_button(
                label=f"⬇️ Baixar {codigo.split('_')[0]}",
                data=df_to_csv_bytes(mailing_df),
                file_name=f"Mailing_{codigo}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key=f"ml_{codigo}",
            )


# ══════════════════════════════════════════════════════════════════════
# TABS PRINCIPAIS
# ══════════════════════════════════════════════════════════════════════

tab_names = []
if df_deals is not None:
    tab_names += ["👥 Performance Comercial"]
if df_mapa is not None:
    tab_names += ["🗺️ Mapa Parque", "🎯 Raio X", "📈 Segmentação"]
if df_deals is not None:
    tab_names += [" Deals"]
if df_mapa is not None and df_deals is not None:
    tab_names += ["🔄 Cruzamento"]
if df_mapa is not None:
    tab_names += ["📥 Mailings", "📋 Dados Brutos"]

tabs = st.tabs(tab_names)
tab_idx = 0

# ══════════════════════════════════════════════════════════════════════
# TAB: PERFORMANCE COMERCIAL X
# ══════════════════════════════════════════════════════════════════════
if "👥 Performance Comercial" in tab_names:
    with tabs[tab_idx]:
        st.markdown('<h2 class="section-header">Análise de Vendas por Time e Esteira</h2>', unsafe_allow_html=True)
        
        perf_df = analisar_performance_vendedores(df_deals)
        
        if not perf_df.empty:
            # Filtro por Time (Gerência)
            times = ["Todos"] + sorted(perf_df["Gerência"].unique().tolist())
            time_sel = st.selectbox("Filtrar por Time (Gerência)", times)
            
            view_df = perf_df if time_sel == "Todos" else perf_df[perf_df["Gerência"] == time_sel]
            
            # KPIs do Time
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(render_kpi_card("💰", "Faturamento Est. (R$)", f"{view_df['Faturamento'].sum():,.2f}"), unsafe_allow_html=True)
            with c2:
                st.markdown(render_kpi_card("📈", "Total Linhas", f"{view_df['Linhas_Totais'].sum():,}"), unsafe_allow_html=True)
            with c3:
                st.markdown(render_kpi_card("🎯", "Conversão Portab.", f"{view_df['Portabilidades'].sum():,}"), unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Gráfico de Faturamento por Consultor
            import plotly.express as px
            fig_perf = px.bar(
                view_df.head(15), 
                x="Nome do Consultor", 
                y="Faturamento",
                color="Gerência",
                title="Top 15 Consultores por Faturamento",
                text_auto='.2s'
            )
            st.plotly_chart(fig_perf, use_container_width=True)
            
            # Tabela Detalhada
            st.markdown("#### Detalhamento por Vendedor")
            st.dataframe(view_df, use_container_width=True, hide_index=True)
        else:
            st.warning("Dados de Deals insuficientes para análise de performance.")
    tab_idx += 1

# ══════════════════════════════════════════════════════════════════════
# TAB: MAPA PARQUE - VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════

if df_mapa is not None:
    with tabs[tab_idx]:
        st.markdown('<h2 class="section-header">Visão Geral da Carteira</h2>', unsafe_allow_html=True)

        # KPIs
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1:
            st.markdown(render_kpi_card("👥", "Total Clientes", f"{len(df_filtered):,}"), unsafe_allow_html=True)
        with c2:
            st.markdown(render_kpi_card("📱", "Linhas Móveis", f"{df_filtered['QTD_MOVEL'].sum():,}"), unsafe_allow_html=True)
        with c3:
            st.markdown(render_kpi_card("🌐", "Banda Larga", f"{df_filtered['QTD_BL'].sum():,}"), unsafe_allow_html=True)
        with c4:
            st.markdown(render_kpi_card("💳", "Vivo Tech", f"{df_filtered['QTD_VTECH'].sum():,}"), unsafe_allow_html=True)
        with c5:
            ftth_pct = df_filtered["NA_MANCHA"].sum() / max(len(df_filtered), 1) * 100
            st.markdown(render_kpi_card("📶", "Penetração FTTH", f"{ftth_pct:.1f}%"), unsafe_allow_html=True)
        with c6:
            st.markdown(render_kpi_card("⭐", "Big Deals", f"{df_filtered['BIG_DEAL'].sum():,}"), unsafe_allow_html=True)

        st.markdown('<hr class="purple-divider">', unsafe_allow_html=True)

        # Gráficos
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_categoria_m(df_filtered), use_container_width=True)
        with col2:
            st.plotly_chart(chart_semaforo(df_filtered), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_segmentacao(df_filtered), use_container_width=True)
        with col2:
            st.plotly_chart(chart_posse(df_filtered), use_container_width=True)

    tab_idx += 1


# ══════════════════════════════════════════════════════════════════════
# TAB: RAIO X
# ══════════════════════════════════════════════════════════════════════

if df_mapa is not None:
    with tabs[tab_idx]:
        st.markdown('<h2 class="section-header">Raio X Completo da Carteira</h2>', unsafe_allow_html=True)

        st.plotly_chart(chart_raio_x(df_filtered), use_container_width=True)

        st.markdown('<hr class="purple-divider">', unsafe_allow_html=True)

        # Tabela detalhada do Raio X
        st.markdown("####  Detalhamento com Semáforo")

        raio_x_items = [
            ("Móvel s/ Fixa M17+", df_filtered[(df_filtered["TEM_MOVEL"]) & (~df_filtered["TEM_FIXA"]) & (df_filtered["MESES_CARTEIRA"] >= 17)]),
            ("Móvel c/ Fixa M17+", df_filtered[(df_filtered["TEM_MOVEL"]) & (df_filtered["TEM_FIXA"]) & (df_filtered["MESES_CARTEIRA"] >= 17)]),
            ("Excedente Dados M7-M16", df_filtered[(df_filtered["TEM_MOVEL"]) & (df_filtered["MESES_CARTEIRA"].between(7, 16))]),
            ("Fixa s/ Móvel", df_filtered[(df_filtered["TEM_FIXA"]) & (~df_filtered["TEM_MOVEL"])]),
            ("Clientes PEN", df_filtered[df_filtered["TEM_PEN"]]),
            ("CAR > 0", df_filtered[df_filtered["CAR_TOTAL"] > 0]),
            ("Cobertura 5G", df_filtered[df_filtered["TEM_5G"]]),
            ("Vivo Tech Atual", df_filtered[df_filtered["QTD_VTECH"] > 0]),
        ]

        rows = []
        for nome, subset in raio_x_items:
            rows.append({
                "Categoria": nome,
                "Clientes": len(subset),
                "VERDE": (subset["SEMAFORO"] == "VERDE").sum(),
                "AMARELO": (subset["SEMAFORO"] == "AMARELO").sum(),
                "VERMELHO": (subset["SEMAFORO"] == "VERMELHO").sum(),
                "PRETO/CINZA": (subset["SEMAFORO"] == "PRETO/CINZA").sum(),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Heatmap
        st.markdown('<hr class="purple-divider">', unsafe_allow_html=True)
        st.plotly_chart(chart_heatmap_segmento_catm(df_filtered), use_container_width=True)

    tab_idx += 1


# ══════════════════════════════════════════════════════════════════════
# TAB: SEGMENTAÇÃO
# ══════════════════════════════════════════════════════════════════════

if df_mapa is not None:
    with tabs[tab_idx]:
        st.markdown('<h2 class="section-header">Análise de Segmentação</h2>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_fidelizacao(df_filtered), use_container_width=True)
        with col2:
            # MEI por segmento
            mei_seg = df_filtered.groupby("SEGMENTO")["MEI"].sum().reset_index()
            mei_seg.columns = ["Segmento", "Qtd MEI"]
            import plotly.express as px
            fig = px.bar(mei_seg, x="Segmento", y="Qtd MEI",
                         color="Qtd MEI", color_continuous_scale=["#F0E6FA", "#660099"],
                         text="Qtd MEI")
            fig.update_traces(texttemplate="%{text:,}", textposition="outside")
            fig.update_xaxes(tickangle=45)
            fig.update_layout(showlegend=False, coloraxis_showscale=False,
                              title=dict(text="MEI por Segmento", font=dict(size=16, color="#2F5496")),
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        # Tabela de segmentos
        st.markdown("#### 📋 Resumo por Segmento")
        seg_summary = []
        for seg in SEGMENTOS_ORDEM:
            s = df_filtered[df_filtered["SEGMENTO"] == seg]
            seg_summary.append({
                "": SEGMENTOS_ICONS.get(seg, ""),
                "Segmento": seg,
                "Clientes": len(s),
                "% Base": f"{len(s)/max(len(df_filtered),1)*100:.1f}%",
                "Linhas Móveis": s["QTD_MOVEL"].sum(),
                "Banda Larga": s["QTD_BL"].sum(),
                "MEI": s["MEI"].sum(),
                "Big Deal": s["BIG_DEAL"].sum(),
                "Descrição": SEGMENTOS_DESC.get(seg, ""),
            })
        st.dataframe(pd.DataFrame(seg_summary), use_container_width=True, hide_index=True)

    tab_idx += 1


# ══════════════════════════════════════════════════════════════════════
# TAB: DEALS
# ══════════════════════════════════════════════════════════════════════

if df_deals is not None:
    with tabs[tab_idx]:
        st.markdown('<h2 class="section-header">Análise de Deals (Bitrix)</h2>', unsafe_allow_html=True)

        # KPIs
        concluidos = df_deals[df_deals["Fase"] == "Pedido Concluído"] if "Fase" in df_deals.columns else pd.DataFrame()
        em_andamento = df_deals[df_deals["Fase"] != "Pedido Concluído"] if "Fase" in df_deals.columns else pd.DataFrame()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(render_kpi_card("📝", "Total Deals", f"{len(df_deals):,}"), unsafe_allow_html=True)
        with c2:
            st.markdown(render_kpi_card("✅", "Concluídos", f"{len(concluidos):,}"), unsafe_allow_html=True)
        with c3:
            st.markdown(render_kpi_card("⏳", "Em Andamento", f"{len(em_andamento):,}"), unsafe_allow_html=True)
        with c4:
            total_linhas = concluidos["QTD_LINHAS"].sum() if "QTD_LINHAS" in concluidos.columns else 0
            st.markdown(render_kpi_card("📞", "Linhas (Concl.)", f"{total_linhas:,}"), unsafe_allow_html=True)

        st.markdown('<hr class="purple-divider">', unsafe_allow_html=True)

        # Gráficos
        col1, col2 = st.columns(2)
        with col1:
            fig = chart_deals_por_fase(df_deals)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if len(concluidos) > 0:
                fig = chart_deals_por_tipo(concluidos)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            if len(concluidos) > 0:
                fig = chart_deals_por_gerencia(concluidos)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        with col2:
            if len(concluidos) > 0:
                fig = chart_deals_por_consultor(concluidos)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

        # Tabela de portabilidade
        if "Tipo de Solicitação" in df_deals.columns:
            st.markdown('<hr class="purple-divider">', unsafe_allow_html=True)
            st.markdown("####  Pedidos Concluídos por Tipo")

            if len(concluidos) > 0 and "TIPO_AGRUPADO" in concluidos.columns:
                tipo_stats = concluidos.groupby(["Tipo de Solicitação", "TIPO_AGRUPADO"]).agg(
                    Pedidos=("TIPO_AGRUPADO", "count"),
                    Linhas=("QTD_LINHAS", "sum") if "QTD_LINHAS" in concluidos.columns else ("TIPO_AGRUPADO", "count"),
                ).sort_values("Pedidos", ascending=False).reset_index()
                tipo_stats["% Total"] = (tipo_stats["Pedidos"] / tipo_stats["Pedidos"].sum() * 100).round(1).astype(str) + "%"
                st.dataframe(tipo_stats, use_container_width=True, hide_index=True)

    tab_idx += 1


# ══════════════════════════════════════════════════════════════════════
# TAB: CRUZAMENTO
# ══════════════════════════════════════════════════════════════════════

if df_mapa is not None and df_deals is not None:
    with tabs[tab_idx]:
        st.markdown('<h2 class="section-header">Cruzamento: Mapa Parque × Deals</h2>', unsafe_allow_html=True)

        if "TEM_DEAL" in df_mapa.columns:
            com_deal = df_filtered["TEM_DEAL"].sum()
            sem_deal = len(df_filtered) - com_deal

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(render_kpi_card("📋", "Total no Mapa", f"{len(df_filtered):,}"), unsafe_allow_html=True)
            with c2:
                st.markdown(render_kpi_card("✅", "Com Deal", f"{com_deal:,}"), unsafe_allow_html=True)
            with c3:
                st.markdown(render_kpi_card("🎯", "Sem Deal (Potencial)", f"{sem_deal:,}"), unsafe_allow_html=True)

            st.markdown('<hr class="purple-divider">', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(chart_penetracao_deals(df_filtered), use_container_width=True)
            with col2:
                st.plotly_chart(chart_penetracao_por_segmento(df_filtered), use_container_width=True)

            # Portabilidade potencial vs real
            fig = chart_portabilidade_potencial_vs_real(df_filtered)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

            # Penetração por segmento - tabela
            st.markdown("####  Penetração por Segmento")
            seg_pen = []
            for seg in SEGMENTOS_ORDEM:
                s = df_filtered[df_filtered["SEGMENTO"] == seg]
                com = s["TEM_DEAL"].sum()
                total = len(s)
                seg_pen.append({
                    "Segmento": seg,
                    "Total": total,
                    "Com Deal": com,
                    "Sem Deal": total - com,
                    "Penetração": f"{com/max(total,1)*100:.1f}%",
                })
            st.dataframe(pd.DataFrame(seg_pen), use_container_width=True, hide_index=True)
        else:
            st.info("Cruze os dados carregando ambos os arquivos.")

    tab_idx += 1


# ══════════════════════════════════════════════════════════════════════
# TAB: MAILINGS
# ══════════════════════════════════════════════════════════════════════

if df_mapa is not None:
    with tabs[tab_idx]:
        st.markdown('<h2 class="section-header">Geração de Mailings — Raio X Carteira</h2>', unsafe_allow_html=True)

        st.markdown("""
        <div class="info-box">
            📬 Mailings gerados conforme a estrutura do <b>Raio X Carteira Mirai Telecom</b>.<br>
            Cada mailing segue <b>exatamente</b> os filtros e objetivos do PDF oficial (seções 1, 2 e 3).
        </div>
        """, unsafe_allow_html=True)

        # Gerar todos os mailings
        all_mailings = gerar_todos_mailings(df_mapa)

        # Botão para baixar tudo em Excel
        if all_mailings:
            excel_bytes = df_to_excel_bytes(all_mailings)
            st.download_button(
                label=f"📦 Baixar TODOS os Mailings ({len(all_mailings)} abas em Excel)",
                data=excel_bytes,
                file_name=f"Mailings_RaioX_Mirai_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        st.markdown('<hr class="purple-divider">', unsafe_allow_html=True)

        # ── SEÇÃO 1: MÓVEL ──
        st.markdown("### 📱 1. MÓVEL")
        secao1 = {k: v for k, v in all_mailings.items() if k.startswith("1.")}
        _render_mailing_section(secao1)

        st.markdown('<hr class="purple-divider">', unsafe_allow_html=True)

        # ── SEÇÃO 2: FIXA ──
        st.markdown("### 🌐 2. FIXA")
        secao2 = {k: v for k, v in all_mailings.items() if k.startswith("2.")}
        _render_mailing_section(secao2)

        st.markdown('<hr class="purple-divider">', unsafe_allow_html=True)

        # ── SEÇÃO 3: INDICADORES ──
        st.markdown("###  3. INDICADORES DA CARTEIRA")
        secao3 = {k: v for k, v in all_mailings.items() if k.startswith("3.")}
        _render_mailing_section(secao3)

        st.markdown('<hr class="purple-divider">', unsafe_allow_html=True)

        # Mailing customizado com filtros
        st.markdown("### 🔧 Mailing Customizado (com filtros aplicados)")
        st.markdown(f'<div class="info-box-blue">Base filtrada: <b>{len(df_filtered):,}</b> clientes</div>', unsafe_allow_html=True)

        custom_name = st.text_input("Nome do mailing", value="CUSTOM")
        if st.button("🚀 Gerar Mailing Customizado"):
            custom_mailing = gerar_mailing_customizado(df_filtered, custom_name)
            st.success(f"✅ Mailing gerado: {len(custom_mailing)} clientes")
            st.download_button(
                label=f"⬇️ Baixar Mailing {custom_name}",
                data=df_to_csv_bytes(custom_mailing),
                file_name=f"Mailing_{custom_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="custom_mailing_dl",
            )

    tab_idx += 1


# ══════════════════════════════════════════════════════════════════════
# TAB: DADOS BRUTOS
# ══════════════════════════════════════════════════════════════════════

if df_mapa is not None:
    with tabs[tab_idx]:
        st.markdown('<h2 class="section-header">Dados Brutos</h2>', unsafe_allow_html=True)

        # Seletor de colunas
        display_cols = ["NOME_CLIENTE", "NR_CNPJ", "SEGMENTO", "CATEGORIA_M",
                        "QTD_MOVEL", "QTD_BL", "SEMAFORO", "NA_MANCHA",
                        "MEI", "BIG_DEAL", "POSSE_SIMPL", "PORT_POTENCIAL",
                        "CAR_TOTAL", "FIDELIZADO", "TEM_5G"]
        available_cols = [c for c in display_cols if c in df_filtered.columns]

        selected_cols = st.multiselect(
            "Colunas a exibir", options=available_cols, default=available_cols[:8],
        )

        if selected_cols:
            df_display = df_filtered[selected_cols].copy()

            # Formatar booleanos
            bool_cols = ["NA_MANCHA", "MEI", "BIG_DEAL", "FIDELIZADO", "TEM_5G"]
            for bc in bool_cols:
                if bc in df_display.columns:
                    df_display[bc] = df_display[bc].map({True: "Sim", False: "Não"})

            # Busca
            search = st.text_input("🔍 Buscar por nome ou CNPJ")
            if search:
                mask = df_display.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
                df_display = df_display[mask]

            st.dataframe(df_display, use_container_width=True, height=500, hide_index=True)
            st.caption(f"Mostrando {len(df_display):,} de {len(df_filtered):,} clientes")

            # Download da tabela filtrada
            st.download_button(
                label="⬇️ Baixar Tabela Atual (CSV)",
                data=df_to_csv_bytes(df_display),
                file_name=f"Dados_Filtrados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )

    tab_idx += 1


# ══════════════════════════════════════════════════════════════════════
# RODAPÉ
# ══════════════════════════════════════════════════════════════════════

st.markdown(f"""
<hr class="purple-divider">
<div style="display: flex; justify-content: space-between; padding: 0 1rem; color: #999; font-size: 0.8rem;">
    <span> Mirai Insights v{APP_VERSION}</span>
    <span>Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
    <span>Desenvolvido por Data Analytics Mirai</span>
</div>
""", unsafe_allow_html=True)