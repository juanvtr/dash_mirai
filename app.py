# -*- coding: utf-8 -*-
"""Mirai Insights v4 - Sidebar fixa, design ultra-limpo."""

import streamlit as st
import pandas as pd
import base64
import os
from datetime import datetime
from io import BytesIO

from config import APP_TITLE, MAILING_CORES, SEGMENTOS_DESC
from styles import (
    get_css, breadcrumb, page_header, kpi_card, kpi_grid,
    section_title, divider, divider_grad, info_box, mailing_card_html,
    segment_card, sidebar_line, footer_html,
)
from data_processing import (
    processar_mapa_parque, processar_parque_movel,
    agregar_parque_movel_por_cnpj, cruzar_mapa_com_movel,
    gerar_mailing_customizado, gerar_todos_mailings,
    processar_deals, get_cnpjs_em_tratativa, filtrar_mailing_sem_deals,
)
from charts import (
    chart_semaforo, chart_segmentacao, chart_categoria_m, chart_posse,
    chart_raio_x, chart_heatmap_segmento_catm, chart_fidelizacao,
    chart_faixa_m_linhas, chart_fidelizacao_linhas, chart_serasa_linhas,
    chart_blindagem, chart_planos_top, chart_m_por_cliente, chart_regua_m,
)
from db import MiraiDB
from mailing_avancados import (
    enriquecer_df_com_propensoes, gerar_mailings_produto,
    get_filtros_disponiveis, gerar_mailing_custom_avancado,
)

# Tenta importar webhook (pode falhar se requests nao instalado)
try:
    from bitrix_webhook import fetch_deals, fetch_users, process_webhook_deals, test_webhook
    HAS_WEBHOOK = True
except ImportError:
    HAS_WEBHOOK = False


# ===== HELPERS =====

def _logo_b64(filename):
    for p in [os.path.join(os.path.dirname(__file__), filename), filename]:
        if os.path.exists(p):
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return ""

def to_csv(df):
    return df.to_csv(sep=";", index=False, encoding="utf-8-sig").encode("utf-8-sig")

def to_excel(d):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for name, df in d.items():
            df.to_excel(w, sheet_name=name[:31], index=False)
    return buf.getvalue()


# ===== CONFIG =====

st.set_page_config(
    page_title="Mirai Insights",
    page_icon="logo_icon.png" if os.path.exists("logo_icon.png") else None,
    layout="wide",
    initial_sidebar_state="expanded",
)

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
theme = st.session_state["theme"]
st.markdown(get_css(theme), unsafe_allow_html=True)

# Init database (Supabase ou SQLite)
@st.cache_resource
def init_db():
    # Streamlit Cloud usa st.secrets, local usa os.environ ou .env
    supa_url = None
    supa_key = None
    try:
        supa_url = st.secrets["SUPABASE_URL"]
        supa_key = st.secrets["SUPABASE_KEY"]
    except:
        pass
    if not supa_url:
        supa_url = os.environ.get("SUPABASE_URL")
    if not supa_key:
        supa_key = os.environ.get("SUPABASE_KEY")
    return MiraiDB(supabase_url=supa_url, supabase_key=supa_key)

db = init_db()


# ===== SIDEBAR =====

logo_b64 = _logo_b64("logo_icon.png")

with st.sidebar:
    # Logo pequena + nome - sem fundo, sem versao
    if logo_b64:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:10px;padding:8px 0 4px;">'
            '<img src="data:image/png;base64,{img}" style="width:28px;height:28px;" />'
            '<span style="font-size:0.95rem;font-weight:600;color:var(--tx);">Mirai Insights</span>'
            '</div>'.format(img=logo_b64), unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="padding:8px 0 4px;font-size:0.95rem;font-weight:600;color:var(--tx);">'
            'Mirai Insights</div>', unsafe_allow_html=True)

    st.markdown(sidebar_line(), unsafe_allow_html=True)

    # Theme toggle - discreto
    if st.button("Light" if theme == "dark" else "Dark", key="t", help="Alternar tema", type="secondary"):
        st.session_state["theme"] = "light" if theme == "dark" else "dark"
        st.rerun()

    st.markdown(sidebar_line(), unsafe_allow_html=True)

    # Fontes de dados
    st.markdown('<div style="font-size:0.72rem;font-weight:600;color:var(--tx3);text-transform:uppercase;'
                'letter-spacing:0.06em;margin-bottom:4px;">Fontes de Dados</div>', unsafe_allow_html=True)

    uploaded_mapa = st.file_uploader("Mapa Parque", type=["csv"], key="up_mapa",
                                     help="MapaParqueVisaoCliente_*.csv", label_visibility="collapsed")
    uploaded_movel = st.file_uploader("Parque Movel", type=["csv"], key="up_movel",
                                      help="ParqueMovel_*.csv", label_visibility="collapsed")

    st.markdown(sidebar_line(), unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.72rem;font-weight:600;color:var(--tx3);text-transform:uppercase;'
                'letter-spacing:0.06em;margin-bottom:4px;">Bitrix24</div>', unsafe_allow_html=True)

    # Webhook sync button (unico meio de carregar deals)
    if HAS_WEBHOOK:
        webhook_url = ""
        try:
            webhook_url = st.secrets["BITRIX_WEBHOOK_URL"]
        except:
            try:
                webhook_url = os.environ.get("BITRIX_WEBHOOK_URL", "")
            except:
                pass
        if not webhook_url:
            webhook_url = db.get_config("bitrix_webhook_url", "")

        if webhook_url:
            if st.button("Sincronizar Deals", key="sync_wh", type="secondary"):
                with st.spinner("Sincronizando com Bitrix24..."):
                    try:
                        df_users_wh = fetch_users(webhook_url)
                        df_raw = fetch_deals(webhook_url)
                        if not df_raw.empty:
                            df_proc = process_webhook_deals(df_raw, df_users_wh)
                            count = db.upsert_deals(df_proc)
                            st.session_state["webhook_synced"] = True
                            st.success("{:,} deals".format(count))
                        else:
                            st.warning("Nenhum deal retornado")
                    except Exception as e:
                        st.error(str(e)[:100])
        else:
            st.markdown('<div style="font-size:0.7rem;color:var(--tx3);">Configure na aba Config</div>',
                       unsafe_allow_html=True)

    # Status
    m_ok = uploaded_mapa is not None or "df_mapa" in st.session_state
    p_ok = uploaded_movel is not None or "df_movel" in st.session_state
    d_ok = st.session_state.get("webhook_synced", False) or db.status().get("total_deals", 0) > 0
    st.markdown(
        '<div style="display:flex;gap:10px;padding:2px 0;font-size:0.72rem;color:var(--tx3);">'
        '<span style="display:flex;align-items:center;gap:4px;">'
        '<span style="width:5px;height:5px;border-radius:50%;background:{mc};"></span>Mapa</span>'
        '<span style="display:flex;align-items:center;gap:4px;">'
        '<span style="width:5px;height:5px;border-radius:50%;background:{pc};"></span>Movel</span>'
        '<span style="display:flex;align-items:center;gap:4px;">'
        '<span style="width:5px;height:5px;border-radius:50%;background:{dc};"></span>Deals</span>'
        '</div>'.format(
            mc="var(--success)" if m_ok else "var(--tx3)",
            pc="var(--success)" if p_ok else "var(--tx3)",
            dc="var(--success)" if d_ok else "var(--tx3)",
        ), unsafe_allow_html=True)

    # Filtros
    if "df_mapa" in st.session_state and st.session_state["df_mapa"] is not None:
        st.markdown(sidebar_line(), unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.72rem;font-weight:600;color:var(--tx3);text-transform:uppercase;'
                    'letter-spacing:0.06em;margin-bottom:4px;">Filtros</div>', unsafe_allow_html=True)

        df_ref = st.session_state["df_mapa"]
        seg_filter = st.selectbox("Segmento", ["Todos"] + sorted(df_ref["SEGMENTO"].dropna().unique().tolist()), key="f_seg")
        catm_col = "CATEGORIA_M_REAL" if "CATEGORIA_M_REAL" in df_ref.columns else "CATEGORIA_M"
        cat_filter = st.selectbox("Categoria M", ["Todos"] + sorted(df_ref[catm_col].dropna().unique().tolist()), key="f_cat")
        sem_filter = st.selectbox("Semaforo", ["Todos"] + sorted(df_ref["SEMAFORO"].dropna().unique().tolist()), key="f_sem")
        mancha_filter = st.checkbox("Apenas mancha FTTH", key="f_mancha")
    else:
        seg_filter = cat_filter = sem_filter = "Todos"
        mancha_filter = False


# ===== DATA =====

if uploaded_mapa is not None:
    if "df_mapa" not in st.session_state or st.session_state.get("mapa_name") != uploaded_mapa.name:
        with st.spinner("Processando Mapa Parque..."):
            st.session_state["df_mapa"] = processar_mapa_parque(uploaded_mapa)
            st.session_state["mapa_name"] = uploaded_mapa.name
            st.session_state.pop("cruzamento_done", None)
df_mapa = st.session_state.get("df_mapa")

if uploaded_movel is not None:
    if "df_movel" not in st.session_state or st.session_state.get("movel_name") != uploaded_movel.name:
        with st.spinner("Processando Parque Movel..."):
            st.session_state["df_movel"] = processar_parque_movel(uploaded_movel)
            st.session_state["df_movel_agg"] = agregar_parque_movel_por_cnpj(st.session_state["df_movel"])
            st.session_state["movel_name"] = uploaded_movel.name
            st.session_state.pop("cruzamento_done", None)
df_movel = st.session_state.get("df_movel")
df_movel_agg = st.session_state.get("df_movel_agg")

if df_mapa is not None and df_movel_agg is not None:
    if "cruzamento_done" not in st.session_state:
        with st.spinner("Cruzando dados..."):
            df_mapa = cruzar_mapa_com_movel(df_mapa, df_movel_agg)
            df_mapa = enriquecer_df_com_propensoes(df_mapa)
            st.session_state["df_mapa"] = df_mapa
            st.session_state["cruzamento_done"] = True

# Enriquecer mesmo sem Parque Movel (so Mapa Parque)
if df_mapa is not None and "TEM_PROP_VVN" not in df_mapa.columns:
    df_mapa = enriquecer_df_com_propensoes(df_mapa)
    st.session_state["df_mapa"] = df_mapa

# Deals - via webhook/banco (sem upload manual)
cnpjs_tratativa, nomes_tratativa = db.get_cnpjs_em_tratativa()


# ===== WELCOME =====

if df_mapa is None and df_movel is None:
    logo_full = _logo_b64("logo_full.png")
    if logo_full:
        st.markdown(
            '<div style="text-align:center;padding:50px 24px 16px;">'
            '<img src="data:image/png;base64,{}" style="width:180px;opacity:0.85;" />'
            '</div>'.format(logo_full), unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center;padding:8px 24px 40px;">'
        '<h2 style="font-size:1.8rem;font-weight:700;margin-bottom:8px;'
        'background:linear-gradient(135deg,{c1},{c2},{c3});'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Mirai Insights</h2>'
        '<p style="color:var(--tx2);font-size:0.9rem;max-width:440px;margin:0 auto;line-height:1.5;">'
        'Carregue o <strong style="color:var(--tx);">Mapa Parque</strong> e o '
        '<strong style="color:var(--tx);">Parque Movel</strong> na barra lateral.</p>'
        '</div>'.format(
            c1="#E879F9" if theme == "dark" else "#D946EF",
            c2="#A78BFA" if theme == "dark" else "#8B5CF6",
            c3="#22D3EE" if theme == "dark" else "#06B6D4",
        ), unsafe_allow_html=True)
    st.stop()


# ===== FILTERS =====

df_f = df_mapa.copy() if df_mapa is not None else None
if df_f is not None:
    if seg_filter != "Todos":
        df_f = df_f[df_f["SEGMENTO"] == seg_filter]
    if cat_filter != "Todos":
        col = "CATEGORIA_M_REAL" if "CATEGORIA_M_REAL" in df_f.columns else "CATEGORIA_M"
        df_f = df_f[df_f[col] == cat_filter]
    if sem_filter != "Todos":
        df_f = df_f[df_f["SEMAFORO"] == sem_filter]
    if mancha_filter:
        df_f = df_f[df_f["NA_MANCHA"]]


# ===== TABS =====

tab_names = []
if df_mapa is not None:
    tab_names += ["Mapa Parque", "Raio X", "Segmentacao"]
if df_movel is not None:
    tab_names += ["Parque Movel", "Regua M"]
if df_mapa is not None:
    tab_names += ["Explorar Cliente", "Mailings", "Vendedores", "Dados Brutos", "Metodologia", "Config"]

tabs = st.tabs(tab_names)
ti = 0


# ===== MAPA PARQUE =====

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Carteira", "Mapa Parque"]), unsafe_allow_html=True)
        st.markdown(page_header("Visao Geral da Carteira",
            "Analise consolidada por CNPJ com classificacao comercial e indicadores."), unsafe_allow_html=True)

        cards = [
            kpi_card("Total Clientes", "{:,}".format(len(df_f)), accent=True),
            kpi_card("Linhas Moveis", "{:,}".format(df_f["QTD_MOVEL"].sum())),
            kpi_card("Banda Larga", "{:,}".format(df_f["QTD_BL"].sum())),
            kpi_card("Vivo Tech", "{:,}".format(df_f["QTD_VTECH"].sum())),
            kpi_card("FTTH", "{:.1f}%".format(df_f["NA_MANCHA"].sum()/max(len(df_f),1)*100)),
            kpi_card("Big Deals", "{:,}".format(df_f["BIG_DEAL"].sum())),
        ]
        st.markdown(kpi_grid(cards), unsafe_allow_html=True)

        if "PM_QTD_LINHAS" in df_f.columns:
            st.markdown(kpi_grid([
                kpi_card("Linhas PM", "{:,}".format(int(df_f["PM_QTD_LINHAS"].sum())), accent=True),
                kpi_card("Fat. Medio", "R$ {:,.0f}".format(df_f["PM_FAT_TOTAL"].sum())),
                kpi_card("Linhas M17+", "{:,}".format(int(df_f["PM_LINHAS_M17_PLUS"].sum()))),
                kpi_card("% Fidelizado", "{:.1f}%".format(
                    df_f["PM_QTD_FIDELIZADAS"].sum()/max(df_f["PM_QTD_LINHAS"].sum(),1)*100)),
            ]), unsafe_allow_html=True)

        st.markdown(divider(), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(chart_categoria_m(df_f, theme), use_container_width=True, config={"displayModeBar": False})
        with c2: st.plotly_chart(chart_semaforo(df_f, theme), use_container_width=True, config={"displayModeBar": False})
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(chart_segmentacao(df_f, theme), use_container_width=True, config={"displayModeBar": False})
        with c2: st.plotly_chart(chart_posse(df_f, theme), use_container_width=True, config={"displayModeBar": False})
        st.markdown(footer_html(), unsafe_allow_html=True)
    ti += 1


# ===== RAIO X =====

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Carteira", "Raio X"]), unsafe_allow_html=True)
        st.markdown(page_header("Raio X da Carteira", "Indicadores cruzados do PDF Raio X."), unsafe_allow_html=True)
        st.plotly_chart(chart_raio_x(df_f, theme), use_container_width=True, config={"displayModeBar": False})
        st.markdown(divider(), unsafe_allow_html=True)
        st.plotly_chart(chart_heatmap_segmento_catm(df_f, theme), use_container_width=True, config={"displayModeBar": False})
        st.markdown(divider(), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(chart_fidelizacao(df_f, theme), use_container_width=True, config={"displayModeBar": False})
        with c2:
            seg_data = [{"Segmento": s, "Clientes": (df_f["SEGMENTO"]==s).sum(), "Desc": SEGMENTOS_DESC.get(s,"")}
                       for s in df_f["SEGMENTO"].value_counts().index]
            if seg_data: st.dataframe(pd.DataFrame(seg_data), use_container_width=True, hide_index=True, height=300)
        st.markdown(footer_html(), unsafe_allow_html=True)
    ti += 1


# ===== SEGMENTACAO =====

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Carteira", "Segmentacao"]), unsafe_allow_html=True)
        st.markdown(page_header("Segmentacao Comercial", "Classificacao por posse e estrategia."), unsafe_allow_html=True)
        cards_html = [segment_card("Segmento", seg, SEGMENTOS_DESC.get(seg,""), "{:,} clientes".format((df_f["SEGMENTO"]==seg).sum()))
                     for seg in df_f["SEGMENTO"].value_counts().index]
        st.markdown('<div class="cg">{}</div>'.format("".join(cards_html)), unsafe_allow_html=True)
        st.markdown(divider(), unsafe_allow_html=True)
        seg_choice = st.selectbox("Segmento", df_f["SEGMENTO"].unique().tolist(), key="seg_d")
        df_seg = df_f[df_f["SEGMENTO"] == seg_choice]
        st.markdown(kpi_grid([
            kpi_card("Clientes", "{:,}".format(len(df_seg)), accent=True),
            kpi_card("Moveis", "{:,}".format(df_seg["QTD_MOVEL"].sum())),
            kpi_card("BL", "{:,}".format(df_seg["QTD_BL"].sum())),
        ]), unsafe_allow_html=True)
        cols = ["NOME_CLIENTE","NR_CNPJ","POSSE_SIMPL","QTD_MOVEL","QTD_BL","SEMAFORO"]
        avail = [c for c in cols if c in df_seg.columns]
        st.dataframe(df_seg[avail].head(100), use_container_width=True, hide_index=True, height=400)
        st.markdown(footer_html(), unsafe_allow_html=True)
    ti += 1


# ===== PARQUE MOVEL =====

if df_movel is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Movel", "Parque Movel"]), unsafe_allow_html=True)
        st.markdown(page_header("Parque Movel", "Visao por linha telefonica."), unsafe_allow_html=True)
        st.markdown(kpi_grid([
            kpi_card("Total Linhas", "{:,}".format(len(df_movel)), accent=True),
            kpi_card("Fidelizadas", "{:,}".format(df_movel["FIDELIZADO_MOVEL"].sum())),
            kpi_card("Fat. Medio", "R$ {:,.0f}".format(df_movel["FAT_MEDIO"].sum())),
            kpi_card("Blindagem", "{:,}".format(df_movel["ELEGIVEL_BLINDAR_FLAG"].sum())),
            kpi_card("Excedente", "{:,}".format(df_movel["EXCEDENTE_DADOS"].sum())),
            kpi_card("CNPJs", "{:,}".format(df_movel["CNPJ_NORM"].nunique())),
        ]), unsafe_allow_html=True)
        st.markdown(divider(), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(chart_faixa_m_linhas(df_movel, theme), use_container_width=True, config={"displayModeBar": False})
        with c2: st.plotly_chart(chart_fidelizacao_linhas(df_movel, theme), use_container_width=True, config={"displayModeBar": False})
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(chart_serasa_linhas(df_movel, theme), use_container_width=True, config={"displayModeBar": False})
        with c2: st.plotly_chart(chart_blindagem(df_movel, theme), use_container_width=True, config={"displayModeBar": False})
        st.markdown(divider(), unsafe_allow_html=True)
        st.plotly_chart(chart_planos_top(df_movel, 10, theme), use_container_width=True, config={"displayModeBar": False})
        st.markdown(divider(), unsafe_allow_html=True)
        st.markdown(section_title("Classificacao M por Cliente"), unsafe_allow_html=True)
        st.plotly_chart(chart_m_por_cliente(df_movel, theme), use_container_width=True, config={"displayModeBar": False})
        faixas = ["M0-M6","M7-M12","M13-M16","M17-M21","M22+"]
        cross = df_movel.groupby("CNPJ_NORM")["FAIXA_M"].value_counts().unstack(fill_value=0)
        cross = cross.reindex(columns=[f for f in faixas if f in cross.columns], fill_value=0)
        cross["TOTAL_FAIXAS"] = (cross > 0).sum(axis=1)
        multi = cross[cross["TOTAL_FAIXAS"] > 1].sort_values("TOTAL_FAIXAS", ascending=False)
        if len(multi) > 0:
            display = multi.reset_index()
            if df_mapa is not None and "CNPJ_NORM" in df_mapa.columns:
                names = df_mapa[["CNPJ_NORM","NOME_CLIENTE"]].drop_duplicates("CNPJ_NORM")
                display = display.merge(names, on="CNPJ_NORM", how="left")
            st.dataframe(display.head(50), use_container_width=True, hide_index=True, height=400)
        st.markdown(footer_html(), unsafe_allow_html=True)
    ti += 1


# ===== REGUA M =====

if df_movel is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Comercial", "Regua M"]), unsafe_allow_html=True)
        st.markdown(page_header("Regua de Relacionamento", "M16-M24+ para disparos automatizados."), unsafe_allow_html=True)
        st.markdown(info_box(
            "<strong>Frequencia:</strong> M16 informativo | M17 semanal | M18-M22 quinzenal | M23 semanal | M24+ mensal"
        ), unsafe_allow_html=True)
        st.plotly_chart(chart_regua_m(df_movel, theme), use_container_width=True, config={"displayModeBar": False})
        st.markdown(divider(), unsafe_allow_html=True)
        m = df_movel["M_INT"]
        regua = []
        for mes in range(16, 25):
            mask = (m >= 24) if mes == 24 else ((m >= mes) & (m < mes + 1))
            label = "M{}{}".format(mes, "+" if mes == 24 else "")
            linhas = mask.sum()
            regua.append({"Mes": label, "Linhas": linhas, "CNPJs": df_movel[mask]["CNPJ_NORM"].nunique(),
                         "Fat.": "R$ {:,.0f}".format(df_movel[mask]["FAT_MEDIO"].sum()),
                         "Freq": "Semanal" if mes in [17,23] else "Info" if mes==16 else "Quinz." if 18<=mes<=22 else "Mensal"})
        st.dataframe(pd.DataFrame(regua), use_container_width=True, hide_index=True)
        st.markdown(divider(), unsafe_allow_html=True)
        mes_sel = st.selectbox("Exportar M", range(16,25), format_func=lambda x: "M{}{}".format(x,"+" if x==24 else ""), key="reg_sel")
        df_r = df_movel[(df_movel["M_INT"]>=24) if mes_sel==24 else ((df_movel["M_INT"]>=mes_sel)&(df_movel["M_INT"]<mes_sel+1))]
        if len(df_r) > 0:
            cols_e = ["CNPJ_NORM","CLIENTE","NR_TELEFONE","PLANO","M_INT","FAIXA_M","FIDELIZADO","FAT_MEDIO","SEMAFORO_SERASA"]
            avail = [c for c in cols_e if c in df_r.columns]
            exp = df_r[avail].copy()
            exp["MES_REGUA"] = "M{}{}".format(mes_sel, "+" if mes_sel==24 else "")
            st.download_button("Baixar ({:,} linhas)".format(len(exp)), data=to_csv(exp),
                              file_name="Regua_M{}_{}.csv".format(mes_sel, datetime.now().strftime("%Y%m%d")), mime="text/csv")
        st.markdown(footer_html(), unsafe_allow_html=True)
    ti += 1


# ===== EXPLORAR CLIENTE =====

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Carteira", "Explorar Cliente"]), unsafe_allow_html=True)
        st.markdown(page_header("Explorar Cliente", "Visao hierarquica: linhas, Ms e indicacoes."), unsafe_allow_html=True)

        search_val = st.text_input("Buscar por nome ou CNPJ", key="ex_s", placeholder="Min. 3 caracteres...")
        if search_val and len(search_val) >= 3:
            mask = (df_f["NOME_CLIENTE"].astype(str).str.contains(search_val, case=False, na=False) |
                    df_f["NR_CNPJ"].astype(str).str.contains(search_val, case=False, na=False))
            results = df_f[mask].head(20)
            if len(results) == 0:
                st.warning("Nenhum cliente encontrado.")
            else:
                opts = results.apply(lambda r: "{} ({})".format(r.get("NOME_CLIENTE","?"), r.get("NR_CNPJ","?")), axis=1).tolist()
                sel = st.selectbox("Cliente", range(len(opts)), format_func=lambda i: opts[i], key="ex_sel")
                cli = results.iloc[sel]
                cnpj = cli.get("CNPJ_NORM", cli.get("NR_CNPJ", ""))

                st.markdown(divider_grad(), unsafe_allow_html=True)
                st.markdown(kpi_grid([
                    kpi_card("CNPJ", str(cli.get("NR_CNPJ","")), accent=True),
                    kpi_card("Segmento", str(cli.get("SEGMENTO",""))),
                    kpi_card("Semaforo", str(cli.get("SEMAFORO",""))),
                    kpi_card("Moveis", str(cli.get("QTD_MOVEL",0))),
                    kpi_card("BL", str(cli.get("QTD_BL",0))),
                    kpi_card("Posse", str(cli.get("POSSE_SIMPL",""))),
                ]), unsafe_allow_html=True)

                # Flags como pills
                flags = []
                for f, n in [("BIG_DEAL","Big Deal"),("MEI","MEI"),("NA_MANCHA","FTTH"),("BIOMETRADO","Biometrado"),("TEM_5G","5G"),("FIDELIZADO","Fidelizado")]:
                    if cli.get(f): flags.append(n)
                if flags:
                    st.markdown('<div style="margin:6px 0 12px;">{}</div>'.format("".join(
                        '<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:0.7rem;'
                        'font-weight:500;margin:2px;background:var(--acc-bg);color:var(--acc);">{}</span>'.format(f) for f in flags
                    )), unsafe_allow_html=True)

                # Arvore de linhas
                if "PM_QTD_LINHAS" in cli.index and pd.notna(cli.get("PM_QTD_LINHAS")) and cli["PM_QTD_LINHAS"] > 0:
                    st.markdown(divider(), unsafe_allow_html=True)
                    st.markdown(kpi_grid([
                        kpi_card("Linhas", "{:.0f}".format(cli["PM_QTD_LINHAS"]), accent=True),
                        kpi_card("M Medio", "{:.1f}".format(cli.get("PM_M_MEDIO",0))),
                        kpi_card("Fat.", "R$ {:,.0f}".format(cli.get("PM_FAT_TOTAL",0))),
                        kpi_card("% Fid.", "{:.0f}%".format(cli.get("PM_PCT_FIDELIZADO",0))),
                    ]), unsafe_allow_html=True)

                    if df_movel is not None:
                        linhas = df_movel[df_movel["CNPJ_NORM"] == cnpj]
                        if len(linhas) > 0:
                            st.markdown(section_title("Linhas por Faixa M"), unsafe_allow_html=True)
                            h = '<div style="font-size:0.82rem;">'
                            for fx in ["M0-M6","M7-M12","M13-M16","M17-M21","M22+"]:
                                fl = linhas[linhas["FAIXA_M"]==fx]
                                if len(fl) == 0: continue
                                urgent = fx in ["M17-M21","M22+"]
                                fc = "var(--acc2)" if urgent else "var(--acc3)"
                                h += '<div style="margin:8px 0 2px;padding:6px 12px;border-radius:6px;background:var(--hover);border-left:2px solid {};">'.format(fc)
                                h += '<span style="font-weight:600;color:{};">{}</span>'.format(fc, fx)
                                h += '<span style="color:var(--tx3);margin-left:6px;font-size:0.76rem;">{} linha{}</span></div>'.format(len(fl), "s" if len(fl)!=1 else "")
                                for _, l in fl.iterrows():
                                    fid = "Fid" if l.get("FIDELIZADO_MOVEL") else "N/Fid"
                                    fc2 = "var(--success)" if fid=="Fid" else "var(--error)"
                                    h += '<div style="margin-left:16px;padding:4px 12px;border-left:1px solid var(--border);font-size:0.78rem;">'
                                    h += '<span style="font-family:monospace;color:var(--tx);">{}</span> '.format(str(l.get("NR_TELEFONE","")))
                                    h += '<span style="color:var(--tx3);">M{:.0f}</span> '.format(l.get("M_INT",0))
                                    h += '<span style="color:{};font-size:0.7rem;">{}</span>'.format(fc2, fid)
                                    if l.get("ELEGIVEL_BLINDAR_FLAG"):
                                        h += ' <span style="font-size:0.66rem;padding:1px 5px;border-radius:8px;background:var(--acc-bg);color:var(--acc);">Blindar</span>'
                                    h += '<div style="color:var(--tx3);font-size:0.72rem;">{}  R$ {:,.0f}</div>'.format(
                                        str(l.get("PLANO",""))[:35], l.get("FAT_MEDIO",0))
                                    h += '</div>'
                            h += '</div>'
                            st.markdown(h, unsafe_allow_html=True)

                # Indicacoes
                st.markdown(divider(), unsafe_allow_html=True)
                st.markdown(section_title("Indicacoes"), unsafe_allow_html=True)
                inds = []
                pm17 = cli.get("PM_LINHAS_M17_PLUS",0) or 0
                pm7 = cli.get("PM_LINHAS_M7_M16",0) or 0
                if pm17 > 0 and not cli.get("TEM_FIXA"):
                    inds.append(("RENOVAR+FTTH", "{:.0f} linhas M17+ sem fixa".format(pm17), "var(--acc)"))
                if pm17 > 0 and cli.get("TEM_FIXA"):
                    inds.append(("RENOVAR", "{:.0f} linhas M17+".format(pm17), "var(--acc)"))
                if pm7 > 0:
                    inds.append(("UP", "{:.0f} linhas M7-M16".format(pm7), "var(--acc3)"))
                if cli.get("CAR_TOTAL",0) > 0:
                    inds.append(("CAR", "R$ {:.0f} pendente".format(cli["CAR_TOTAL"]), "var(--error)"))
                if not cli.get("TEM_MOVEL") and cli.get("TEM_FIXA"):
                    inds.append(("TOTALIZACAO", "Fixa sem movel", "var(--acc2)"))
                if not cli.get("BIOMETRADO"):
                    inds.append(("BIOMETRIA", "Nao biometrado", "var(--warning)"))
                for t, d, c in inds:
                    st.markdown('<div style="padding:8px 14px;border-radius:6px;border-left:2px solid {};background:var(--hover);margin-bottom:6px;">'
                               '<span style="font-weight:600;color:{};font-size:0.82rem;">{}</span>'
                               '<span style="color:var(--tx2);font-size:0.78rem;margin-left:8px;">{}</span></div>'.format(c,c,t,d), unsafe_allow_html=True)
                if not inds:
                    st.markdown(info_box("Sem indicacoes automaticas."), unsafe_allow_html=True)
        else:
            st.markdown(info_box("Digite pelo menos <strong>3 caracteres</strong> para buscar."), unsafe_allow_html=True)
        st.markdown(footer_html(), unsafe_allow_html=True)
    ti += 1


# ===== MAILINGS =====

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Comercial", "Mailings"]), unsafe_allow_html=True)
        st.markdown(page_header("Mailings", "16 mailings automatizados do Raio X."), unsafe_allow_html=True)

        # Filtro de Deals
        filtrar_deals = False
        if cnpjs_tratativa or nomes_tratativa:
            total_trat = len(cnpjs_tratativa | nomes_tratativa) if cnpjs_tratativa and nomes_tratativa else len(cnpjs_tratativa) + len(nomes_tratativa)
            filtrar_deals = st.checkbox(
                "Excluir clientes com deal aberto no Bitrix ({:,} em tratativa)".format(len(nomes_tratativa) or len(cnpjs_tratativa)),
                value=True, key="filtrar_deals")

        all_m = gerar_todos_mailings(df_mapa)

        # Aplicar filtro de deals se ativo
        if filtrar_deals and (cnpjs_tratativa or nomes_tratativa):
            total_antes = sum(len(v) for v in all_m.values())
            for k in all_m:
                if len(all_m[k]) > 0:
                    all_m[k], _ = filtrar_mailing_sem_deals(all_m[k], cnpjs_tratativa, nomes_tratativa)
            total_depois = sum(len(v) for v in all_m.values())
            st.markdown(info_box(
                "Filtro Deals ativo: <strong>{:,}</strong> registros removidos (de {:,} para {:,}).".format(
                    total_antes - total_depois, total_antes, total_depois)
            ), unsafe_allow_html=True)
        if all_m:
            st.download_button("Baixar TODOS ({} mailings)".format(len(all_m)), data=to_excel(all_m),
                              file_name="Mailings_{}.xlsx".format(datetime.now().strftime("%Y%m%d")),
                              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        def _sec(prefix, title):
            st.markdown(section_title(title), unsafe_allow_html=True)
            sec = {k:v for k,v in all_m.items() if k.startswith(prefix)}
            cols = st.columns(2)
            for i,(cod,ml) in enumerate(sec.items()):
                if len(ml)==0: continue
                obj = ml["OBJETIVO"].iloc[0] if "OBJETIVO" in ml.columns else ""
                obs = ml["OBSERVACAO"].iloc[0] if "OBSERVACAO" in ml.columns else ""
                color = "#8B5CF6"
                for key,c in MAILING_CORES.items():
                    if key in obj.upper(): color = c; break
                dn = cod.split("_",1)[1].replace("_"," ") if "_" in cod else cod
                with cols[i%2]:
                    st.markdown(mailing_card_html(cod.split("_")[0], dn, len(ml), obj, obs, color), unsafe_allow_html=True)
                    st.download_button("Baixar {}".format(cod.split("_")[0]), data=to_csv(ml),
                                      file_name="Mailing_{}_{}.csv".format(cod, datetime.now().strftime("%Y%m%d")),
                                      mime="text/csv", key="ml_{}".format(cod))
        _sec("1.", "1. Migracoes")
        st.markdown(divider(), unsafe_allow_html=True)
        _sec("2.", "2. Renovacoes")
        st.markdown(divider(), unsafe_allow_html=True)
        _sec("3.", "3. Cross-Sell e Totalizacao")
        st.markdown(divider(), unsafe_allow_html=True)
        _sec("4.", "4. Indicadores e Relacionamento")

        # ===== MAILINGS POR PRODUTO =====
        st.markdown(divider_grad(), unsafe_allow_html=True)
        st.markdown(section_title("5. Mailings por Produto e Propensao"), unsafe_allow_html=True)
        st.markdown(info_box(
            "Mailings gerados a partir das colunas de oferta (<strong>PRIMEIRA_OFERTA, VVN, DIGITAL_1/2/3, VIVO_TECH, AVANCADOS</strong>) "
            "cruzadas com o nivel de propensao de cada cliente."
        ), unsafe_allow_html=True)

        mailings_prod = gerar_mailings_produto(df_mapa)
        if mailings_prod:
            cols_p = st.columns(2)
            for i, (cod, (df_mp, titulo, desc)) in enumerate(mailings_prod.items()):
                if len(df_mp) == 0:
                    continue
                # Aplicar filtro de deals
                df_mp_filtered = df_mp
                removidos = 0
                if filtrar_deals and (cnpjs_tratativa or nomes_tratativa):
                    df_mp_filtered, removidos = filtrar_mailing_sem_deals(df_mp, cnpjs_tratativa, nomes_tratativa)
                with cols_p[i % 2]:
                    st.markdown(mailing_card_html(cod.split("_")[0], titulo,
                        len(df_mp_filtered), desc,
                        "Removidos deals: {}".format(removidos) if removidos else "",
                        "#06B6D4"), unsafe_allow_html=True)
                    # Montar mailing pra download
                    from data_processing import _montar_mailing
                    ml_export = _montar_mailing(df_mp_filtered, cod, titulo, desc,
                        info_fonte="FONTE: Propensao/Oferta | {}".format(desc))
                    if len(ml_export) > 0:
                        st.download_button("Baixar {} ({:,})".format(cod[:6], len(ml_export)),
                            data=to_csv(ml_export),
                            file_name="Mailing_{}_{}.csv".format(cod, datetime.now().strftime("%Y%m%d")),
                            mime="text/csv", key="mp_{}".format(cod))

        # ===== GERADOR CUSTOMIZADO AVANCADO =====
        st.markdown(divider_grad(), unsafe_allow_html=True)
        st.markdown(section_title("Gerador de Mailing Customizado"), unsafe_allow_html=True)
        st.markdown(info_box(
            "Monte seu mailing combinando filtros. O resultado exclui automaticamente clientes em tratativa no Bitrix."
        ), unsafe_allow_html=True)

        filtros_disp = get_filtros_disponiveis(df_mapa)

        c1, c2 = st.columns(2)
        with c1:
            sel_produtos = st.multiselect("Produtos", filtros_disp.get("produtos", []), key="cust_prod")
            sel_propensao = st.selectbox("Propensao minima", ["Todos", "Muito Alta", "Alta", "Média", "Baixa"], key="cust_prop")
            sel_ofertas = st.multiselect("Contem oferta de", filtros_disp.get("ofertas", []), key="cust_oferta")
            sel_trilha = st.selectbox("Trilha", ["Todos"] + filtros_disp.get("trilhas", []), key="cust_trilha")
        with c2:
            sel_segmento = st.selectbox("Segmento", ["Todos"] + filtros_disp.get("segmentos", []), key="cust_seg")
            sel_semaforo = st.selectbox("Semaforo", ["Todos"] + filtros_disp.get("semaforos", []), key="cust_sem")
            sel_mancha = st.checkbox("Apenas mancha FTTH", key="cust_mancha")
            sel_big = st.checkbox("Apenas Big Deal", key="cust_big")
            sel_nao_fid = st.checkbox("Apenas nao fidelizado", key="cust_nfid")
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                sel_m_min = st.number_input("M minimo", min_value=0, max_value=999, value=0, key="cust_mmin")
            with c_m2:
                sel_m_max = st.number_input("M maximo", min_value=0, max_value=999, value=999, key="cust_mmax")

        nome_custom = st.text_input("Nome do mailing", value="CUSTOM", key="cust_nome")

        if st.button("Gerar Mailing", key="gen_cust_av"):
            filtros_app = {}
            if sel_produtos:
                filtros_app["produtos"] = sel_produtos
            if sel_propensao != "Todos":
                filtros_app["propensao_min"] = sel_propensao
            if sel_ofertas:
                filtros_app["oferta_contem"] = sel_ofertas
            if sel_trilha != "Todos":
                filtros_app["trilha"] = sel_trilha
            if sel_segmento != "Todos":
                filtros_app["segmento"] = sel_segmento
            if sel_semaforo != "Todos":
                filtros_app["semaforo"] = sel_semaforo
            if sel_mancha:
                filtros_app["apenas_mancha"] = True
            if sel_big:
                filtros_app["apenas_big_deal"] = True
            if sel_nao_fid:
                filtros_app["apenas_nao_fidelizado"] = True
            if sel_m_min > 0:
                filtros_app["m_min"] = sel_m_min
            if sel_m_max < 999:
                filtros_app["m_max"] = sel_m_max

            result = gerar_mailing_custom_avancado(df_mapa, filtros_app)

            # Filtrar deals
            removidos = 0
            if cnpjs_tratativa or nomes_tratativa:
                result, removidos = filtrar_mailing_sem_deals(result, cnpjs_tratativa, nomes_tratativa, cnpj_col="NR_CNPJ", nome_col="NOME_CLIENTE")

            if len(result) > 0:
                filtro_desc = " | ".join("{}={}".format(k, v) for k, v in filtros_app.items())
                from data_processing import _montar_mailing
                ml = _montar_mailing(result, nome_custom, "CUSTOM: " + filtro_desc, filtro_desc,
                    info_fonte="CUSTOM | " + filtro_desc)

                st.success("{:,} clientes encontrados{}".format(len(ml),
                    " ({:,} removidos por deals)".format(removidos) if removidos else ""))
                st.download_button("Baixar {} ({:,})".format(nome_custom, len(ml)),
                    data=to_csv(ml),
                    file_name="Mailing_{}_{}.csv".format(nome_custom, datetime.now().strftime("%Y%m%d")),
                    mime="text/csv", key="dl_cust_av")
                # Preview
                preview_cols = ["NR_CNPJ", "NOME_CLIENTE", "SEGMENTO", "CURVA_ABC", "PM_FAT_TOTAL"]
                avail = [c for c in preview_cols if c in result.columns]
                st.dataframe(result[avail].head(20), use_container_width=True, hide_index=True, height=300)
            else:
                st.warning("Nenhum cliente encontrado com esses filtros.")

        st.markdown(footer_html(), unsafe_allow_html=True)
    ti += 1


# ===== VENDEDORES =====

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Comercial", "Vendedores"]), unsafe_allow_html=True)
        st.markdown(page_header("Controle por Vendedor", "Faturamento, deals e performance."), unsafe_allow_html=True)

        # Dados de deals (do banco ou do upload)
        vendor_stats = db.calcular_stats_vendedores()

        if not vendor_stats.empty:
            st.markdown(kpi_grid([
                kpi_card("Vendedores", "{:,}".format(len(vendor_stats)), accent=True),
                kpi_card("Total Deals", "{:,}".format(int(vendor_stats["total_deals"].sum()))),
                kpi_card("Fat. Total", "R$ {:,.0f}".format(vendor_stats["faturamento_total"].sum())),
                kpi_card("Fat. Medio", "R$ {:,.0f}".format(vendor_stats["faturamento_medio"].mean())),
            ]), unsafe_allow_html=True)

            st.markdown(divider(), unsafe_allow_html=True)
            st.markdown(section_title("Ranking por Faturamento"), unsafe_allow_html=True)

            display_stats = vendor_stats.copy()
            display_stats = display_stats.rename(columns={
                "responsavel": "Vendedor",
                "total_deals": "Total Deals",
                "deals_abertos": "Abertos",
                "deals_fechados": "Fechados",
                "faturamento_total": "Fat. Total",
                "faturamento_medio": "Fat. Medio",
                "taxa_conversao": "Conversao %",
            })
            display_stats["Fat. Total"] = display_stats["Fat. Total"].apply(lambda x: "R$ {:,.0f}".format(x))
            display_stats["Fat. Medio"] = display_stats["Fat. Medio"].apply(lambda x: "R$ {:,.0f}".format(x))
            st.dataframe(display_stats, use_container_width=True, hide_index=True, height=500)

            st.markdown(divider(), unsafe_allow_html=True)

            # Detalhamento por vendedor
            st.markdown(section_title("Detalhar Vendedor"), unsafe_allow_html=True)
            vendedor_sel = st.selectbox("Vendedor", vendor_stats["responsavel"].tolist(), key="vend_sel")
            if vendedor_sel:
                deals_vend = db.get_deals_abertos()
                if not deals_vend.empty:
                    deals_vend = deals_vend[deals_vend["responsavel"] == vendedor_sel]
                    st.markdown(kpi_grid([
                        kpi_card("Deals Abertos", "{:,}".format(len(deals_vend)), accent=True),
                        kpi_card("Fat. Aberto", "R$ {:,.0f}".format(deals_vend["renda"].sum())),
                    ]), unsafe_allow_html=True)
                    if len(deals_vend) > 0:
                        cols_show = ["nome", "fase", "renda", "criado"]
                        avail = [c for c in cols_show if c in deals_vend.columns]
                        st.dataframe(deals_vend[avail], use_container_width=True, hide_index=True, height=300)
        else:
            st.markdown(info_box(
                "Nenhum dado de deals disponivel. <strong>Opcoes:</strong><br>"
                "1. Suba o CSV de Deals na sidebar<br>"
                "2. Configure o webhook Bitrix na aba Config e clique em 'Atualizar Deals'"
            ), unsafe_allow_html=True)

        st.markdown(footer_html(), unsafe_allow_html=True)
    ti += 1


# ===== DADOS BRUTOS =====

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Dados", "Dados Brutos"]), unsafe_allow_html=True)
        st.markdown(page_header("Dados Brutos", "Tabela interativa."), unsafe_allow_html=True)
        dcols = ["NOME_CLIENTE","NR_CNPJ","SEGMENTO","CATEGORIA_M_REAL","QTD_MOVEL","QTD_BL","SEMAFORO","CAR_TOTAL","PM_QTD_LINHAS","PM_M_MEDIO"]
        avail = [c for c in dcols if c in df_f.columns]
        sel = st.multiselect("Colunas", df_f.columns.tolist(), default=avail[:8], key="rc")
        if sel:
            dd = df_f[sel].copy()
            for bc in ["NA_MANCHA","MEI","BIG_DEAL","FIDELIZADO","TEM_5G","BIOMETRADO"]:
                if bc in dd.columns: dd[bc] = dd[bc].map({True:"Sim",False:"Nao"})
            s = st.text_input("Buscar", key="sr", placeholder="Nome, CNPJ...")
            if s: dd = dd[dd.astype(str).apply(lambda x: x.str.contains(s, case=False, na=False)).any(axis=1)]
            st.dataframe(dd, use_container_width=True, height=500, hide_index=True)
            st.caption("{:,} / {:,}".format(len(dd), len(df_f)))
            st.download_button("CSV", data=to_csv(dd), file_name="Dados_{}.csv".format(datetime.now().strftime("%Y%m%d")), mime="text/csv", key="dr")
        st.markdown(footer_html(), unsafe_allow_html=True)
    ti += 1


# ===== METODOLOGIA =====

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Dados", "Metodologia"]), unsafe_allow_html=True)
        st.markdown(page_header("Metodologia", "Como os dados sao processados e classificados."), unsafe_allow_html=True)

        st.markdown(section_title("1. Fontes"), unsafe_allow_html=True)
        st.markdown(info_box(
            "<strong>Mapa Parque</strong> — 1 linha por CNPJ, 92 colunas. Posse, CAR, FTTH, biometria, contatos.<br>"
            "<strong>Parque Movel</strong> — 1 linha por telefone, 45 colunas. Plano, M real, fidelizacao, Serasa."
        ), unsafe_allow_html=True)

        st.markdown(section_title("2. Cruzamento"), unsafe_allow_html=True)
        st.markdown(info_box(
            "CNPJ normalizado &rarr; Agrupar Parque Movel por CNPJ &rarr; LEFT JOIN com Mapa Parque.<br>"
            "Resultado: colunas PM_* com M real (mais preciso que MESES_CARTEIRA do Mapa)."
        ), unsafe_allow_html=True)

        st.markdown(section_title("3. Classificacoes"), unsafe_allow_html=True)
        st.markdown(info_box(
            "<strong>CAR:</strong> PRETO 0 | VERDE 1-49 | AMARELO 50-149 | VERMELHO 150+<br>"
            "<strong>M:</strong> M0-6 novo | M7-12 UP | M13-16 pre-renov | M17-21 RENOVACAO | M22+ vencido<br>"
            "<strong>Segmento:</strong> TOTALIZACAO (movel s/ fixa) | MIGRACAO (fixa s/ movel) | BLINDAGEM | CROSS-SELL | AVANCADOS | DIGITAL"
        ), unsafe_allow_html=True)

        st.markdown(section_title("4. Mailings"), unsafe_allow_html=True)
        for cod, nome, filtro in [
            ("1.1","Movel s/ Fixa M17+","TEM_MOVEL + !TEM_FIXA + PM_M17+>0"),
            ("1.2","Movel c/ Fixa M17+","TEM_MOVEL + TEM_FIXA + PM_M17+>0"),
            ("1.3","Excedente M7-16","TEM_MOVEL + PM_M7_M16>0"),
            ("1.4","Credito Aparelho","TEM_MOVEL + PM_M7_M12>0 + APARELHOS"),
            ("1.5","s/ Mancha M17-21","TEM_MOVEL + !MANCHA + PM_M 17-21"),
            ("1.6","Propensao","PORT_POTENCIAL Alto/Medio"),
            ("2.1","Fixa s/ Movel","TEM_FIXA + !TEM_MOVEL"),
            ("2.2","PEN","TEM_PEN"),
            ("2.3","Fixa UP","TEM_FIXA + !MOVEL + !FIDELIZADO"),
            ("2.4","Renov. Fixa","TEM_FIXA + FIDELIZADO"),
            ("3.1","CAR","CAR_TOTAL>0"),
            ("3.2","Biometria","!BIOMETRADO"),
            ("3.3","5G","TEM_5G"),
            ("3.4","VTech","QTD_VTECH>0"),
            ("3.5","VTech Pot.","QTD_VTECH=0 + VIVO_TECH"),
            ("3.6","Digital","DIGITAL_1 preenchido"),
        ]:
            st.markdown('<div style="padding:6px 12px;border-radius:6px;background:var(--hover);margin-bottom:4px;'
                       'display:flex;justify-content:space-between;font-size:0.8rem;">'
                       '<span style="color:var(--tx);font-weight:500;">{} {}</span>'
                       '<span style="color:var(--acc);font-family:monospace;font-size:0.74rem;">{}</span>'
                       '</div>'.format(cod, nome, filtro), unsafe_allow_html=True)

        st.markdown(section_title("5. INFO_FONTE"), unsafe_allow_html=True)
        st.markdown(info_box("Todo CSV exportado tem coluna <strong>INFO_FONTE</strong> com tabela, colunas e filtros usados."), unsafe_allow_html=True)

        st.markdown(section_title("6. Glossario"), unsafe_allow_html=True)
        h = '<div style="display:grid;grid-template-columns:100px 1fr;gap:2px 10px;font-size:0.8rem;">'
        for t,d in [("M","Meses contrato"),("CAR","Conta a Receber"),("BL","Banda Larga"),("FTTH","Fibra optica"),
                    ("PEN","Terminal metalico"),("VVN","PABX virtual"),("Serasa","Score credito"),("PM_*","Dados Parque Movel")]:
            h += '<div style="font-weight:600;color:var(--acc);font-family:monospace;">{}</div><div style="color:var(--tx2);">{}</div>'.format(t,d)
        h += '</div>'
        st.markdown(h, unsafe_allow_html=True)
        st.markdown(footer_html(), unsafe_allow_html=True)
    ti += 1


# ===== CONFIG =====

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Sistema", "Config"]), unsafe_allow_html=True)
        st.markdown(page_header("Configuracoes", "Webhook Bitrix24, banco de dados e integracoes."), unsafe_allow_html=True)

        # Status do banco
        st.markdown(section_title("Banco de Dados"), unsafe_allow_html=True)
        db_status = db.status()
        st.markdown(kpi_grid([
            kpi_card("Backend", db_status.get("backend", "?"), accent=True),
            kpi_card("Total Deals", "{:,}".format(db_status.get("total_deals", 0))),
            kpi_card("Ultima Sync", str(db_status.get("ultima_atualizacao", "nunca"))[:16]),
        ]), unsafe_allow_html=True)

        st.markdown(divider(), unsafe_allow_html=True)

        # Webhook Bitrix
        st.markdown(section_title("Webhook Bitrix24"), unsafe_allow_html=True)
        st.markdown(info_box(
            "Configure o webhook para sincronizar deals automaticamente.<br>"
            "<strong>Como obter:</strong> Bitrix24 > Aplicativos > Webhooks > Adicionar webhook de entrada.<br>"
            "Permissoes necessarias: <strong>crm</strong> e <strong>user</strong>."
        ), unsafe_allow_html=True)

        current_url = db.get_config("bitrix_webhook_url", "")
        try:
            secret_url = st.secrets["BITRIX_WEBHOOK_URL"]
            if secret_url and not current_url:
                current_url = secret_url
        except:
            pass

        # Limpar URL (remover endpoints acidentais como /crm.deal.list.json?...)
        def _clean_webhook_url(u):
            u = u.strip().rstrip("/")
            # Remove qualquer endpoint que tenha sido colado junto
            for suffix in ["/crm.deal.list.json", "/crm.deal.list", "/profile.json", "/profile"]:
                if suffix in u:
                    u = u.split(suffix)[0]
            # Remove query params
            if "?" in u:
                u = u.split("?")[0]
            return u.rstrip("/") + "/"

        if current_url:
            current_url = _clean_webhook_url(current_url)

        new_url = st.text_input("URL do Webhook", value=current_url, key="wh_url",
                               placeholder="https://mirai.bitrix24.com.br/rest/647/abc123/")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Salvar Webhook", key="save_wh"):
                if new_url.strip():
                    clean = _clean_webhook_url(new_url)
                    db.set_config("bitrix_webhook_url", clean)
                    st.success("Salvo: {}".format(clean))
                    st.rerun()
        with c2:
            if st.button("Testar Conexao", key="test_wh"):
                if new_url.strip() and HAS_WEBHOOK:
                    ok, msg = test_webhook(new_url.strip())
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                elif not HAS_WEBHOOK:
                    st.warning("Modulo requests nao instalado. pip install requests")
                else:
                    st.warning("Preencha a URL primeiro.")

        st.markdown(divider(), unsafe_allow_html=True)

        # Supabase
        st.markdown(section_title("Supabase (Cloud)"), unsafe_allow_html=True)
        st.markdown(info_box(
            "Para persistir dados na nuvem, configure as variaveis de ambiente:<br>"
            "<strong>SUPABASE_URL</strong> e <strong>SUPABASE_KEY</strong><br>"
            "Sem Supabase, o sistema usa SQLite local (funciona normalmente)."
        ), unsafe_allow_html=True)

        if db.use_supabase:
            st.markdown('<div style="display:flex;align-items:center;gap:6px;font-size:0.84rem;">'
                       '<span style="width:8px;height:8px;border-radius:50%;background:var(--success);"></span>'
                       '<span style="color:var(--tx2);">Supabase conectado</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="display:flex;align-items:center;gap:6px;font-size:0.84rem;">'
                       '<span style="width:8px;height:8px;border-radius:50%;background:var(--tx3);"></span>'
                       '<span style="color:var(--tx3);">SQLite local ativo</span></div>', unsafe_allow_html=True)

        st.markdown(divider(), unsafe_allow_html=True)

        # Historico de mailings
        st.markdown(section_title("Historico de Mailings"), unsafe_allow_html=True)
        mlog = db.get_mailing_log(20)
        if not mlog.empty:
            st.dataframe(mlog, use_container_width=True, hide_index=True, height=300)
        else:
            st.markdown(info_box("Nenhum mailing gerado ainda."), unsafe_allow_html=True)

        st.markdown(footer_html(), unsafe_allow_html=True)
    ti += 1
