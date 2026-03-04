# -*- coding: utf-8 -*-
"""
Mirai Insights v4.0 - Dashboard B2B Vivo
Paleta derivada da logo Mirai Telecom (magenta/roxo/ciano).
Logos: logo_icon.png (favicon + sidebar) / logo_full.png (welcome).
"""

import streamlit as st
import pandas as pd
import base64
import os
from datetime import datetime
from io import BytesIO
from collections import OrderedDict

from config import APP_TITLE, APP_VERSION, MAILING_CORES, SEGMENTOS_DESC
from styles import (
    get_css, breadcrumb, page_header, kpi_card, kpi_grid,
    section_title, divider, divider_grad, info_box, mailing_card_html,
    segment_card, footer_html,
)
from data_processing import (
    processar_mapa_parque, processar_parque_movel, processar_users,
    agregar_parque_movel_por_cnpj, cruzar_mapa_com_movel,
    gerar_mailing_customizado, gerar_todos_mailings,
)
from charts import (
    chart_semaforo, chart_segmentacao, chart_categoria_m, chart_posse,
    chart_raio_x, chart_heatmap_segmento_catm, chart_fidelizacao,
    chart_faixa_m_linhas, chart_fidelizacao_linhas, chart_serasa_linhas,
    chart_blindagem, chart_planos_top, chart_m_por_cliente,
    chart_regua_m,
)


# ==========================================================
# HELPERS
# ==========================================================

def _logo_b64(filename):
    """Carrega logo como base64 para usar em HTML."""
    # Tenta varios caminhos possiveis
    for path in [
        os.path.join(os.path.dirname(__file__), filename),
        filename,
        os.path.join("/app", filename),
    ]:
        if os.path.exists(path):
            with open(path, "rb") as f:
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


# ==========================================================
# PAGE CONFIG (usa logo como favicon)
# ==========================================================

st.set_page_config(
    page_title="Mirai Insights",
    page_icon="logo_icon.png" if os.path.exists("logo_icon.png") else None,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================================
# THEME
# ==========================================================

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

theme = st.session_state["theme"]
st.markdown(get_css(theme), unsafe_allow_html=True)


# ==========================================================
# SIDEBAR
# ==========================================================

logo_icon_b64 = _logo_b64("logo_icon.png")

with st.sidebar:
    # Logo + Theme toggle
    if logo_icon_b64:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:12px;padding:12px 0 6px;">'
            '<img src="data:image/png;base64,{img}" style="width:38px;height:38px;border-radius:8px;background-color:transparent;" />'
            '<div>'
            '<div style="font-size:1.15rem;font-weight:700;letter-spacing:-0.02em;">MIRAI INSIGHTS</div>'
            '<div style="font-size:0.68rem;color:{tx3};letter-spacing:0.04em;">v{ver}</div>'
            '</div>'
            '</div>'.format(
                img=logo_icon_b64,
                c1="#E879F9" if theme == "dark" else "#D946EF",
                c2="#A78BFA" if theme == "dark" else "#8B5CF6",
                c3="#22D3EE" if theme == "dark" else "#06B6D4",
                tx3="#5C586E" if theme == "dark" else "#A0A0AB",
                ver=APP_VERSION,
            ), unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="padding:12px 0 6px;">'
            '<div style="font-size:1.15rem;font-weight:700;'
            'background:linear-gradient(135deg,#D946EF,#8B5CF6,#06B6D4);'
            '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">MIRAI INSIGHTS</div>'
            '<div style="font-size:0.68rem;color:#A0A0AB;">v{}</div>'
            '</div>'.format(APP_VERSION), unsafe_allow_html=True)

    # Theme toggle
    tc1, tc2 = st.columns([3, 1])
    with tc2:
        icon = "Light" if theme == "dark" else "Dark"
        if st.button(icon, key="theme_btn", help="Alternar tema"):
            st.session_state["theme"] = "light" if theme == "dark" else "dark"
            st.rerun()

    st.markdown('<hr style="margin:8px 0;border-color:{}">'
                .format("#252533" if theme == "dark" else "#E9E5F0"),
                unsafe_allow_html=True)

    # -- Data Sources --
    with st.expander("Fontes de Dados", expanded=True):
        uploaded_mapa = st.file_uploader(
            "Mapa Parque", type=["csv"], key="up_mapa",
            help="RelatorioInfoB2B_MapaParqueVisaoCliente_*.csv")
        uploaded_movel = st.file_uploader(
            "Parque Movel", type=["csv"], key="up_movel",
            help="RelatorioInfoB2B_ParqueMovel_*.csv")

    # Status dots
    m_ok = uploaded_mapa is not None or "df_mapa" in st.session_state
    p_ok = uploaded_movel is not None or "df_movel" in st.session_state

    dot_on = "#22C55E" if theme == "dark" else "#16A34A"
    dot_off = "#EAB308" if theme == "dark" else "#CA8A04"
    st.markdown(
        '<div style="display:flex;gap:12px;padding:4px 0 8px;font-size:0.76rem;">'
        '<span style="display:flex;align-items:center;gap:5px;">'
        '<span style="width:7px;height:7px;border-radius:50%;background:{mc};display:inline-block;"></span>'
        '<span style="color:{mtx};">Mapa</span></span>'
        '<span style="display:flex;align-items:center;gap:5px;">'
        '<span style="width:7px;height:7px;border-radius:50%;background:{pc};display:inline-block;"></span>'
        '<span style="color:{ptx};">Movel</span></span>'
        '</div>'.format(
            mc=dot_on if m_ok else dot_off,
            mtx="#A5A1BC" if theme == "dark" else "#64607D",
            pc=dot_on if p_ok else dot_off,
            ptx="#A5A1BC" if theme == "dark" else "#64607D",
        ), unsafe_allow_html=True)

    # -- Filters --
    if "df_mapa" in st.session_state and st.session_state["df_mapa"] is not None:
        st.markdown('<hr style="margin:8px 0;border-color:{}">'
                    .format("#252533" if theme == "dark" else "#E9E5F0"),
                    unsafe_allow_html=True)

        with st.expander("Filtros", expanded=False):
            df_ref = st.session_state["df_mapa"]
            seg_filter = st.selectbox(
                "Segmento", ["Todos"] + sorted(df_ref["SEGMENTO"].dropna().unique().tolist()),
                key="f_seg")
            catm_col = "CATEGORIA_M_REAL" if "CATEGORIA_M_REAL" in df_ref.columns else "CATEGORIA_M"
            cat_filter = st.selectbox(
                "Categoria M", ["Todos"] + sorted(df_ref[catm_col].dropna().unique().tolist()),
                key="f_cat")
            sem_filter = st.selectbox(
                "Semaforo", ["Todos"] + sorted(df_ref["SEMAFORO"].dropna().unique().tolist()),
                key="f_sem")
            mancha_filter = st.checkbox("Apenas mancha FTTH", key="f_mancha")
    else:
        seg_filter = cat_filter = sem_filter = "Todos"
        mancha_filter = False


# ==========================================================
# DATA PROCESSING
# ==========================================================

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
            st.session_state["df_mapa"] = df_mapa
            st.session_state["cruzamento_done"] = True


# ==========================================================
# WELCOME
# ==========================================================

if df_mapa is None and df_movel is None:
    logo_full_b64 = _logo_b64("logo_full.png")
    if logo_full_b64:
        st.markdown(
            '<div style="text-align:center;padding:40px 24px 0;">'
            '<img src="data:image/png;base64,{}" style="width:220px;margin-bottom:20px;background-color:transparent;" />'
            '</div>'.format(logo_full_b64), unsafe_allow_html=True)

    st.markdown(
        '<div style="text-align:center;padding:12px 24px 48px;">'
        '<h2 style="font-size:2.2rem;font-weight:700;margin-bottom:10px;letter-spacing:-0.03em;">Mirai Insights</h2>'
        '<p style="color:{tx2};font-size:0.95rem;max-width:480px;margin:0 auto;line-height:1.6;">'
        'Carregue o <strong style="color:{tx};">Mapa Parque</strong> e o '
        '<strong style="color:{tx};">Parque Movel</strong> na barra lateral para iniciar.</p>'
        '<div class="cg" style="max-width:460px;margin:28px auto 0;">'
        '{card1}{card2}'
        '</div></div>'.format(
            c1="#E879F9" if theme == "dark" else "#D946EF",
            c2="#A78BFA" if theme == "dark" else "#8B5CF6",
            c3="#22D3EE" if theme == "dark" else "#06B6D4",
            tx2="#A5A1BC" if theme == "dark" else "#64607D",
            tx="#F5F3FF" if theme == "dark" else "#1A1A2E",
            card1=segment_card("Passo 1", "Mapa Parque", "Visao consolidada por CNPJ."),
            card2=segment_card("Passo 2", "Parque Movel", "Cada linha com M real."),
        ), unsafe_allow_html=True)
    st.stop()


# ==========================================================
# APPLY FILTERS
# ==========================================================

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


# ==========================================================
# TABS
# ==========================================================

tab_names = []
if df_mapa is not None:
    tab_names += ["Mapa Parque", "Raio X", "Segmentacao"]
if df_movel is not None:
    tab_names += ["Parque Movel", "Regua M"]
if df_mapa is not None:
    tab_names += ["Explorar Cliente", "Mailings", "Dados Brutos", "Metodologia"]

tabs = st.tabs(tab_names)
ti = 0


# ==========================================================
# TAB: MAPA PARQUE
# ==========================================================

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Carteira", "Mapa Parque"]), unsafe_allow_html=True)
        st.markdown(page_header(
            "Visao Geral da Carteira",
            "Analise consolidada por CNPJ com classificacao comercial e indicadores de saude."
        ), unsafe_allow_html=True)

        cards = [
            kpi_card("Total Clientes", "{:,}".format(len(df_f)), accent=True),
            kpi_card("Linhas Moveis", "{:,}".format(df_f["QTD_MOVEL"].sum())),
            kpi_card("Banda Larga", "{:,}".format(df_f["QTD_BL"].sum())),
            kpi_card("Vivo Tech", "{:,}".format(df_f["QTD_VTECH"].sum())),
            kpi_card("FTTH", "{:.1f}%".format(df_f["NA_MANCHA"].sum() / max(len(df_f), 1) * 100)),
            kpi_card("Big Deals", "{:,}".format(df_f["BIG_DEAL"].sum())),
        ]
        st.markdown(kpi_grid(cards), unsafe_allow_html=True)

        if "PM_QTD_LINHAS" in df_f.columns:
            pm_cards = [
                kpi_card("Linhas PM", "{:,}".format(int(df_f["PM_QTD_LINHAS"].sum())), accent=True),
                kpi_card("Fat. Medio", "R$ {:,.0f}".format(df_f["PM_FAT_TOTAL"].sum())),
                kpi_card("Linhas M17+", "{:,}".format(int(df_f["PM_LINHAS_M17_PLUS"].sum()))),
                kpi_card("% Fidelizado", "{:.1f}%".format(
                    df_f["PM_QTD_FIDELIZADAS"].sum() / max(df_f["PM_QTD_LINHAS"].sum(), 1) * 100)),
            ]
            st.markdown(kpi_grid(pm_cards), unsafe_allow_html=True)

        st.markdown(divider(), unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(chart_categoria_m(df_f, theme), use_container_width=True, config={"displayModeBar": False})
        with c2:
            st.plotly_chart(chart_semaforo(df_f, theme), use_container_width=True, config={"displayModeBar": False})
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(chart_segmentacao(df_f, theme), use_container_width=True, config={"displayModeBar": False})
        with c2:
            st.plotly_chart(chart_posse(df_f, theme), use_container_width=True, config={"displayModeBar": False})

        st.markdown(footer_html(APP_VERSION), unsafe_allow_html=True)
    ti += 1


# ==========================================================
# TAB: RAIO X
# ==========================================================

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Carteira", "Raio X"]), unsafe_allow_html=True)
        st.markdown(page_header(
            "Raio X da Carteira",
            "Indicadores cruzados do PDF Raio X Carteira Mirai Telecom."
        ), unsafe_allow_html=True)

        st.plotly_chart(chart_raio_x(df_f, theme), use_container_width=True, config={"displayModeBar": False})
        st.markdown(divider(), unsafe_allow_html=True)
        st.plotly_chart(chart_heatmap_segmento_catm(df_f, theme), use_container_width=True, config={"displayModeBar": False})

        st.markdown(divider(), unsafe_allow_html=True)
        st.markdown(section_title("Fidelizacao"), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(chart_fidelizacao(df_f, theme), use_container_width=True, config={"displayModeBar": False})
        with c2:
            seg_data = []
            for seg in df_f["SEGMENTO"].value_counts().index:
                desc = SEGMENTOS_DESC.get(seg, "")
                cnt = (df_f["SEGMENTO"] == seg).sum()
                seg_data.append({"Segmento": seg, "Clientes": cnt, "Descricao": desc})
            if seg_data:
                st.dataframe(pd.DataFrame(seg_data), use_container_width=True, hide_index=True, height=300)

        st.markdown(footer_html(APP_VERSION), unsafe_allow_html=True)
    ti += 1


# ==========================================================
# TAB: SEGMENTACAO
# ==========================================================

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Carteira", "Segmentacao"]), unsafe_allow_html=True)
        st.markdown(page_header(
            "Segmentacao Comercial",
            "Classificacao por tipo de posse e estrategia comercial recomendada."
        ), unsafe_allow_html=True)

        cards_html = []
        for seg in df_f["SEGMENTO"].value_counts().index:
            n = (df_f["SEGMENTO"] == seg).sum()
            desc = SEGMENTOS_DESC.get(seg, "")
            cards_html.append(segment_card("Segmento", seg, desc, "{:,} clientes".format(n)))
        st.markdown('<div class="cg">{}</div>'.format("".join(cards_html)), unsafe_allow_html=True)

        st.markdown(divider(), unsafe_allow_html=True)
        st.markdown(section_title("Detalhamento"), unsafe_allow_html=True)
        seg_choice = st.selectbox("Segmento", df_f["SEGMENTO"].unique().tolist(), key="seg_detail")
        df_seg = df_f[df_f["SEGMENTO"] == seg_choice]

        seg_cards = [
            kpi_card("Clientes", "{:,}".format(len(df_seg)), accent=True),
            kpi_card("Linhas Moveis", "{:,}".format(df_seg["QTD_MOVEL"].sum())),
            kpi_card("Banda Larga", "{:,}".format(df_seg["QTD_BL"].sum())),
            kpi_card("Big Deals", "{:,}".format(df_seg["BIG_DEAL"].sum())),
        ]
        st.markdown(kpi_grid(seg_cards), unsafe_allow_html=True)

        cols_show = ["NOME_CLIENTE", "NR_CNPJ", "POSSE_SIMPL", "QTD_MOVEL", "QTD_BL", "SEMAFORO", "BIG_DEAL"]
        avail = [c for c in cols_show if c in df_seg.columns]
        df_show = df_seg[avail].copy()
        if "BIG_DEAL" in df_show.columns:
            df_show["BIG_DEAL"] = df_show["BIG_DEAL"].map({True: "Sim", False: ""})
        st.dataframe(df_show.head(100), use_container_width=True, hide_index=True, height=400)
        st.markdown(footer_html(APP_VERSION), unsafe_allow_html=True)
    ti += 1


# ==========================================================
# TAB: PARQUE MOVEL
# ==========================================================

if df_movel is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Movel", "Parque Movel"]), unsafe_allow_html=True)
        st.markdown(page_header(
            "Parque Movel",
            "Visao por linha telefonica com M real do contrato, fidelizacao e dados de trafego."
        ), unsafe_allow_html=True)

        pm_cards = [
            kpi_card("Total Linhas", "{:,}".format(len(df_movel)), accent=True),
            kpi_card("Fidelizadas", "{:,}".format(df_movel["FIDELIZADO_MOVEL"].sum())),
            kpi_card("Fat. Medio", "R$ {:,.0f}".format(df_movel["FAT_MEDIO"].sum())),
            kpi_card("Elig. Blindagem", "{:,}".format(df_movel["ELEGIVEL_BLINDAR_FLAG"].sum())),
            kpi_card("Excedente", "{:,}".format(df_movel["EXCEDENTE_DADOS"].sum())),
            kpi_card("CNPJs", "{:,}".format(df_movel["CNPJ_NORM"].nunique())),
        ]
        st.markdown(kpi_grid(pm_cards), unsafe_allow_html=True)
        st.markdown(divider(), unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(chart_faixa_m_linhas(df_movel, theme), use_container_width=True, config={"displayModeBar": False})
        with c2:
            st.plotly_chart(chart_fidelizacao_linhas(df_movel, theme), use_container_width=True, config={"displayModeBar": False})
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(chart_serasa_linhas(df_movel, theme), use_container_width=True, config={"displayModeBar": False})
        with c2:
            st.plotly_chart(chart_blindagem(df_movel, theme), use_container_width=True, config={"displayModeBar": False})

        st.markdown(divider(), unsafe_allow_html=True)
        st.plotly_chart(chart_planos_top(df_movel, 10, theme), use_container_width=True, config={"displayModeBar": False})

        st.markdown(divider(), unsafe_allow_html=True)
        st.markdown(section_title("Classificacao M por Cliente"), unsafe_allow_html=True)
        st.markdown(info_box(
            "Cada CNPJ pode ter linhas em <strong>diferentes faixas de M</strong>. "
            "Abaixo: clientes com linhas em multiplos Ms simultaneamente."
        ), unsafe_allow_html=True)

        st.plotly_chart(chart_m_por_cliente(df_movel, theme), use_container_width=True, config={"displayModeBar": False})

        faixas = ["M0-M6", "M7-M12", "M13-M16", "M17-M21", "M22+"]
        cross = df_movel.groupby("CNPJ_NORM")["FAIXA_M"].value_counts().unstack(fill_value=0)
        cross = cross.reindex(columns=[f for f in faixas if f in cross.columns], fill_value=0)
        cross["TOTAL_FAIXAS"] = (cross > 0).sum(axis=1)
        multi = cross[cross["TOTAL_FAIXAS"] > 1].sort_values("TOTAL_FAIXAS", ascending=False)

        if len(multi) > 0:
            if df_mapa is not None and "CNPJ_NORM" in df_mapa.columns:
                names = df_mapa[["CNPJ_NORM", "NOME_CLIENTE"]].drop_duplicates("CNPJ_NORM")
                display = multi.reset_index().merge(names, on="CNPJ_NORM", how="left")
            else:
                display = multi.reset_index()
            cols_show = ["CNPJ_NORM"]
            if "NOME_CLIENTE" in display.columns:
                cols_show = ["NOME_CLIENTE"] + cols_show
            cols_show += [f for f in faixas if f in display.columns] + ["TOTAL_FAIXAS"]
            avail = [c for c in cols_show if c in display.columns]
            st.dataframe(display[avail].head(50), use_container_width=True, hide_index=True, height=400)

        st.markdown(footer_html(APP_VERSION), unsafe_allow_html=True)
    ti += 1


# ==========================================================
# TAB: REGUA M
# ==========================================================

if df_movel is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Comercial", "Regua M"]), unsafe_allow_html=True)
        st.markdown(page_header(
            "Regua de Relacionamento",
            "Distribuicao de linhas M16-M24+ para disparos automatizados."
        ), unsafe_allow_html=True)

        st.markdown(info_box(
            "<strong>Estrategia por M:</strong><br>"
            "M16: Informativo (SMS, email, WhatsApp)<br>"
            "M17: Semanal (+ ligacao IA)<br>"
            "M18-M22: Quinzenal, escalacao progressiva<br>"
            "M23: Semanal emergencial<br>"
            "M24+: Mensal, contato gerencial"
        ), unsafe_allow_html=True)

        st.plotly_chart(chart_regua_m(df_movel, theme), use_container_width=True, config={"displayModeBar": False})

        st.markdown(divider(), unsafe_allow_html=True)
        st.markdown(section_title("Detalhamento por Mes"), unsafe_allow_html=True)

        m = df_movel["M_INT"]
        regua_data = []
        for mes in range(16, 25):
            if mes == 24:
                mask = m >= 24
                label = "M24+"
            else:
                mask = (m >= mes) & (m < mes + 1)
                label = "M{}".format(mes)
            linhas = mask.sum()
            cnpjs = df_movel[mask]["CNPJ_NORM"].nunique()
            fat = df_movel[mask]["FAT_MEDIO"].sum()
            fid = df_movel[mask]["FIDELIZADO_MOVEL"].sum()
            pct_fid = fid / max(linhas, 1) * 100
            freq = "Semanal" if mes in [17, 23] else "Informativo" if mes == 16 else "Quinzenal" if 18 <= mes <= 22 else "Mensal"
            regua_data.append({
                "Mes": label, "Linhas": linhas, "CNPJs": cnpjs,
                "Fat. Medio": "R$ {:,.0f}".format(fat),
                "% Fidelizado": "{:.1f}%".format(pct_fid),
                "Frequencia": freq,
            })
        st.dataframe(pd.DataFrame(regua_data), use_container_width=True, hide_index=True, height=400)

        st.markdown(divider(), unsafe_allow_html=True)
        st.markdown(section_title("Exportar Mailing da Regua"), unsafe_allow_html=True)

        mes_sel = st.selectbox(
            "Selecionar M", list(range(16, 25)),
            format_func=lambda x: "M{}{}".format(x, "+" if x == 24 else ""), key="regua_sel")

        if mes_sel == 24:
            df_regua = df_movel[df_movel["M_INT"] >= 24]
        else:
            df_regua = df_movel[(df_movel["M_INT"] >= mes_sel) & (df_movel["M_INT"] < mes_sel + 1)]

        if len(df_regua) > 0:
            cols_export = ["CNPJ_NORM", "CLIENTE", "NR_TELEFONE", "PLANO", "M_INT", "FAIXA_M",
                          "FIDELIZADO", "FAT_MEDIO", "SEMAFORO_SERASA", "ELEGIVEL_BLINDAR",
                          "TIPO_REDE", "DS_MUNICIPIO"]
            avail = [c for c in cols_export if c in df_regua.columns]
            df_export = df_regua[avail].copy()
            df_export["MES_REGUA"] = "M{}{}".format(mes_sel, "+" if mes_sel == 24 else "")
            df_export["GERADO_EM"] = datetime.now().strftime("%d/%m/%Y %H:%M")

            st.download_button(
                "Baixar M{}{} ({:,} linhas)".format(mes_sel, "+" if mes_sel == 24 else "", len(df_export)),
                data=to_csv(df_export),
                file_name="Regua_M{}_{}.csv".format(mes_sel, datetime.now().strftime("%Y%m%d")),
                mime="text/csv")

        st.markdown(footer_html(APP_VERSION), unsafe_allow_html=True)
    ti += 1


# ==========================================================
# TAB: EXPLORAR CLIENTE (drill-down hierarquico)
# ==========================================================

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Carteira", "Explorar Cliente"]), unsafe_allow_html=True)
        st.markdown(page_header(
            "Explorar Cliente",
            "Visao hierarquica detalhada: selecione um cliente e veja todas as suas linhas, Ms e indicacoes."
        ), unsafe_allow_html=True)

        # Search
        search_val = st.text_input("Buscar por nome ou CNPJ", key="explore_search", placeholder="Digite parte do nome ou CNPJ...")

        if search_val and len(search_val) >= 3:
            mask = (
                df_f["NOME_CLIENTE"].astype(str).str.contains(search_val, case=False, na=False) |
                df_f["NR_CNPJ"].astype(str).str.contains(search_val, case=False, na=False)
            )
            results = df_f[mask].head(20)

            if len(results) == 0:
                st.warning("Nenhum cliente encontrado.")
            else:
                options = results.apply(lambda r: "{} ({})".format(
                    r.get("NOME_CLIENTE", "?"), r.get("NR_CNPJ", "?")), axis=1).tolist()
                selected_idx = st.selectbox("Selecione o cliente", range(len(options)),
                                           format_func=lambda i: options[i], key="explore_sel")
                cliente = results.iloc[selected_idx]
                cnpj = cliente.get("CNPJ_NORM", cliente.get("NR_CNPJ", ""))

                st.markdown(divider_grad(), unsafe_allow_html=True)

                # -- NIVEL 1: Dados do cliente --
                st.markdown(section_title(str(cliente.get("NOME_CLIENTE", ""))), unsafe_allow_html=True)

                cli_cards = [
                    kpi_card("CNPJ", str(cliente.get("NR_CNPJ", "")), accent=True),
                    kpi_card("Segmento", str(cliente.get("SEGMENTO", ""))),
                    kpi_card("Semaforo", str(cliente.get("SEMAFORO", ""))),
                    kpi_card("Linhas Moveis", str(cliente.get("QTD_MOVEL", 0))),
                    kpi_card("Banda Larga", str(cliente.get("QTD_BL", 0))),
                    kpi_card("Posse", str(cliente.get("POSSE_SIMPL", ""))),
                ]
                st.markdown(kpi_grid(cli_cards), unsafe_allow_html=True)

                # Extra info
                extra_items = []
                if cliente.get("BIG_DEAL"):
                    extra_items.append("Big Deal")
                if cliente.get("MEI"):
                    extra_items.append("MEI")
                if cliente.get("NA_MANCHA"):
                    extra_items.append("Mancha FTTH")
                if cliente.get("BIOMETRADO"):
                    extra_items.append("Biometrado")
                if cliente.get("TEM_5G"):
                    extra_items.append("Cobertura 5G")
                if cliente.get("FIDELIZADO"):
                    extra_items.append("Fidelizado")

                if extra_items:
                    pills_html = "".join(
                        '<span style="display:inline-block;padding:4px 12px;border-radius:16px;'
                        'font-size:0.74rem;font-weight:500;margin:2px 4px;'
                        'background:var(--acc-bg);color:var(--acc);">{}</span>'.format(p)
                        for p in extra_items)
                    st.markdown('<div style="margin:8px 0 16px;">{}</div>'.format(pills_html), unsafe_allow_html=True)

                # PM data
                if "PM_QTD_LINHAS" in cliente.index and pd.notna(cliente.get("PM_QTD_LINHAS")) and cliente["PM_QTD_LINHAS"] > 0:
                    st.markdown(divider(), unsafe_allow_html=True)
                    st.markdown(section_title("Parque Movel do Cliente"), unsafe_allow_html=True)

                    pm_cards = [
                        kpi_card("Linhas PM", "{:,.0f}".format(cliente["PM_QTD_LINHAS"]), accent=True),
                        kpi_card("M Medio", "{:.1f}".format(cliente.get("PM_M_MEDIO", 0))),
                        kpi_card("M Min / Max", "{:.0f} / {:.0f}".format(
                            cliente.get("PM_M_MIN", 0), cliente.get("PM_M_MAX", 0))),
                        kpi_card("Fat. Total", "R$ {:,.0f}".format(cliente.get("PM_FAT_TOTAL", 0))),
                        kpi_card("% Fidelizado", "{:.0f}%".format(cliente.get("PM_PCT_FIDELIZADO", 0))),
                        kpi_card("Faixa Predom.", str(cliente.get("PM_FAIXA_M_PREDOMINANTE", ""))),
                    ]
                    st.markdown(kpi_grid(pm_cards), unsafe_allow_html=True)

                    # -- NIVEL 2: Arvore hierarquica das linhas --
                    if df_movel is not None:
                        linhas_cli = df_movel[df_movel["CNPJ_NORM"] == cnpj].copy()
                        if len(linhas_cli) > 0:
                            st.markdown(section_title("Arvore de Linhas por Faixa M"), unsafe_allow_html=True)

                            # Hierarchical tree view
                            faixas_order = ["M0-M6", "M7-M12", "M13-M16", "M17-M21", "M22+"]
                            tree_html = '<div style="font-family:var(--font-body);font-size:0.84rem;">'

                            for faixa in faixas_order:
                                faixa_linhas = linhas_cli[linhas_cli["FAIXA_M"] == faixa]
                                if len(faixa_linhas) == 0:
                                    continue

                                # Faixa header
                                is_urgent = faixa in ["M17-M21", "M22+"]
                                faixa_color = "var(--acc2)" if is_urgent else "var(--acc)"
                                tree_html += (
                                    '<div style="margin:12px 0 4px 0;padding:8px 14px;border-radius:8px;'
                                    'background:var(--hover);border-left:3px solid {fc};">'
                                    '<span style="font-weight:600;color:{fc};">{faixa}</span>'
                                    '<span style="color:var(--tx2);margin-left:8px;">'
                                    '{n} linha{s}</span>'
                                    '</div>'
                                ).format(fc=faixa_color, faixa=faixa, n=len(faixa_linhas),
                                        s="s" if len(faixa_linhas) != 1 else "")

                                # Individual lines
                                for _, linha in faixa_linhas.iterrows():
                                    tel = str(linha.get("NR_TELEFONE", ""))
                                    plano = str(linha.get("PLANO", ""))[:40]
                                    m_val = linha.get("M_INT", 0)
                                    fid = "Fidelizada" if linha.get("FIDELIZADO_MOVEL") else "Nao fidelizada"
                                    fat = linha.get("FAT_MEDIO", 0)
                                    serasa = str(linha.get("SEMAFORO_SERASA", ""))
                                    blind = "Elegivel" if linha.get("ELEGIVEL_BLINDAR_FLAG") else ""

                                    fid_color = "var(--success)" if "Fidelizada" == fid else "var(--error)"
                                    tree_html += (
                                        '<div style="margin-left:20px;padding:6px 14px;border-left:1px solid var(--border);'
                                        'font-size:0.8rem;">'
                                        '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">'
                                        '<span style="font-weight:600;color:var(--tx);font-family:var(--font-mono,monospace);">{tel}</span>'
                                        '<span style="color:var(--tx2);">M{m:.0f}</span>'
                                        '<span style="color:{fc};font-size:0.72rem;">{fid}</span>'
                                        '{blind}'
                                        '</div>'
                                        '<div style="color:var(--tx3);font-size:0.76rem;margin-top:2px;">'
                                        '{plano} | R$ {fat:,.0f}/mes | Serasa: {serasa}</div>'
                                        '</div>'
                                    ).format(tel=tel, m=m_val, fid=fid, fc=fid_color,
                                            plano=plano, fat=fat, serasa=serasa,
                                            blind='<span style="font-size:0.68rem;padding:2px 6px;border-radius:10px;background:var(--acc-bg);color:var(--acc);">Blindar</span>' if blind else "")

                                tree_html += '</div>'
                            st.markdown(tree_html, unsafe_allow_html=True)

                # -- NIVEL 3: Indicacoes comerciais automaticas --
                st.markdown(divider(), unsafe_allow_html=True)
                st.markdown(section_title("Indicacoes Comerciais"), unsafe_allow_html=True)

                indicacoes = []
                pm_m17 = cliente.get("PM_LINHAS_M17_PLUS", 0) or 0
                pm_m7_16 = cliente.get("PM_LINHAS_M7_M16", 0) or 0
                pm_m7_12 = cliente.get("PM_LINHAS_M7_M12", 0) or 0

                if pm_m17 > 0 and not cliente.get("TEM_FIXA"):
                    indicacoes.append(("RENOVAR + FTTH", "Tem {:.0f} linhas com M17+, sem fixa. Oportunidade de renovacao + venda de FTTH.".format(pm_m17), "var(--acc)"))
                if pm_m17 > 0 and cliente.get("TEM_FIXA"):
                    indicacoes.append(("RENOVAR", "Tem {:.0f} linhas com M17+ e ja possui fixa. Foco na renovacao.".format(pm_m17), "var(--acc)"))
                if pm_m7_16 > 0:
                    indicacoes.append(("UP", "Tem {:.0f} linhas entre M7-M16. Janela ideal para upgrade de plano.".format(pm_m7_16), "var(--acc3)"))
                if pm_m7_12 > 0 and cliente.get("TEM_APARELHOS"):
                    indicacoes.append(("UP + APARELHO", "Linhas M7-M12 com aparelho financiado. Oferecer upgrade + aparelho novo.".format(pm_m7_12), "var(--acc3)"))
                if not cliente.get("NA_MANCHA") and cliente.get("TEM_MOVEL"):
                    indicacoes.append(("VVN", "Fora da mancha FTTH. Considerar oferta de VVN (Vivo Voz Negocio).", "var(--warning)"))
                if cliente.get("CAR_TOTAL", 0) > 0:
                    indicacoes.append(("CAR", "Conta a Receber pendente: R$ {:.0f}. Priorizar relacionamento.".format(cliente["CAR_TOTAL"]), "var(--error)"))
                if not cliente.get("BIOMETRADO"):
                    indicacoes.append(("BIOMETRIA", "Cliente nao biometrado. Agendar visita.", "var(--warning)"))
                if cliente.get("TEM_5G"):
                    indicacoes.append(("5G", "Em area de cobertura 5G. Oferecer troca de chip + aparelho.", "var(--info)"))
                if not cliente.get("TEM_MOVEL") and cliente.get("TEM_FIXA"):
                    indicacoes.append(("TOTALIZACAO", "Tem fixa sem movel. Grande oportunidade de migracao/totalizacao.", "var(--acc2)"))

                if indicacoes:
                    for titulo, desc, cor in indicacoes:
                        st.markdown(
                            '<div style="padding:10px 16px;border-radius:8px;border-left:3px solid {c};'
                            'background:var(--hover);margin-bottom:8px;">'
                            '<span style="font-weight:600;color:{c};font-size:0.84rem;">{t}</span>'
                            '<div style="color:var(--tx2);font-size:0.8rem;margin-top:2px;">{d}</div>'
                            '</div>'.format(c=cor, t=titulo, d=desc), unsafe_allow_html=True)
                else:
                    st.markdown(info_box("Sem indicacoes automaticas para este perfil de cliente."), unsafe_allow_html=True)

        else:
            st.markdown(info_box(
                "Digite pelo menos <strong>3 caracteres</strong> do nome ou CNPJ para buscar."
            ), unsafe_allow_html=True)

        st.markdown(footer_html(APP_VERSION), unsafe_allow_html=True)
    ti += 1


# ==========================================================
# TAB: MAILINGS
# ==========================================================

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Comercial", "Mailings"]), unsafe_allow_html=True)
        st.markdown(page_header(
            "Mailings - Raio X Carteira",
            "16 mailings automatizados conforme PDF Raio X Carteira."
        ), unsafe_allow_html=True)

        all_mailings = gerar_todos_mailings(df_mapa)

        if all_mailings:
            st.download_button(
                "Baixar TODOS ({} mailings em Excel)".format(len(all_mailings)),
                data=to_excel(all_mailings),
                file_name="Mailings_RaioX_{}.xlsx".format(datetime.now().strftime("%Y%m%d_%H%M")),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        def _render_section(prefix, title):
            st.markdown(section_title(title), unsafe_allow_html=True)
            section = {k: v for k, v in all_mailings.items() if k.startswith(prefix)}
            cols = st.columns(2)
            for i, (cod, ml) in enumerate(section.items()):
                if len(ml) == 0:
                    continue
                objetivo = ml["OBJETIVO"].iloc[0] if "OBJETIVO" in ml.columns else ""
                obs = ml["OBSERVACAO"].iloc[0] if "OBSERVACAO" in ml.columns else ""
                color = "#8B5CF6"
                for key, c in MAILING_CORES.items():
                    if key in objetivo.upper():
                        color = c
                        break
                display_name = cod.split("_", 1)[1].replace("_", " ") if "_" in cod else cod
                with cols[i % 2]:
                    st.markdown(mailing_card_html(
                        cod.split("_")[0], display_name, len(ml), objetivo, obs, color
                    ), unsafe_allow_html=True)
                    st.download_button(
                        "Baixar {}".format(cod.split("_")[0]),
                        data=to_csv(ml),
                        file_name="Mailing_{}_{}.csv".format(cod, datetime.now().strftime("%Y%m%d")),
                        mime="text/csv", key="ml_{}".format(cod))

        _render_section("1.", "1. Movel")
        st.markdown(divider(), unsafe_allow_html=True)
        _render_section("2.", "2. Fixa")
        st.markdown(divider(), unsafe_allow_html=True)
        _render_section("3.", "3. Indicadores")

        st.markdown(divider_grad(), unsafe_allow_html=True)
        st.markdown(section_title("Mailing Customizado"), unsafe_allow_html=True)
        st.markdown(info_box(
            "Base filtrada: <strong>{:,}</strong> clientes. Aplique filtros na sidebar e exporte.".format(
                len(df_f) if df_f is not None else 0)
        ), unsafe_allow_html=True)

        custom_name = st.text_input("Nome do mailing", value="CUSTOM", key="custom_name")
        if st.button("Gerar Mailing Customizado", key="gen_custom"):
            if df_f is not None:
                custom = gerar_mailing_customizado(df_f, custom_name)
                st.success("{:,} clientes no mailing.".format(len(custom)))
                st.download_button(
                    "Baixar {}".format(custom_name),
                    data=to_csv(custom),
                    file_name="Mailing_{}_{}.csv".format(custom_name, datetime.now().strftime("%Y%m%d")),
                    mime="text/csv", key="dl_custom")

        st.markdown(footer_html(APP_VERSION), unsafe_allow_html=True)
    ti += 1


# ==========================================================
# TAB: DADOS BRUTOS
# ==========================================================

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Dados", "Dados Brutos"]), unsafe_allow_html=True)
        st.markdown(page_header(
            "Dados Brutos",
            "Tabela interativa com todas as colunas."
        ), unsafe_allow_html=True)

        default_cols = [
            "NOME_CLIENTE", "NR_CNPJ", "SEGMENTO", "CATEGORIA_M_REAL",
            "QTD_MOVEL", "QTD_BL", "SEMAFORO", "NA_MANCHA",
            "BIG_DEAL", "FIDELIZADO", "CAR_TOTAL",
            "PM_QTD_LINHAS", "PM_M_MEDIO", "PM_FAT_TOTAL",
        ]
        avail_cols = [c for c in default_cols if c in df_f.columns]
        all_cols = df_f.columns.tolist()

        selected = st.multiselect("Colunas", options=all_cols, default=avail_cols[:10], key="raw_cols")

        if selected:
            df_display = df_f[selected].copy()
            for bc in ["NA_MANCHA", "MEI", "BIG_DEAL", "FIDELIZADO", "TEM_5G", "BIOMETRADO"]:
                if bc in df_display.columns:
                    df_display[bc] = df_display[bc].map({True: "Sim", False: "Nao"})
            search = st.text_input("Buscar", key="search_raw", placeholder="Nome, CNPJ...")
            if search:
                mask = df_display.astype(str).apply(
                    lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
                df_display = df_display[mask]
            st.dataframe(df_display, use_container_width=True, height=500, hide_index=True)
            st.caption("{:,} de {:,} clientes".format(len(df_display), len(df_f)))
            st.download_button(
                "Baixar CSV",
                data=to_csv(df_display),
                file_name="Dados_{}.csv".format(datetime.now().strftime("%Y%m%d_%H%M")),
                mime="text/csv", key="dl_raw")

        st.markdown(footer_html(APP_VERSION), unsafe_allow_html=True)
    ti += 1


# ==========================================================
# TAB: METODOLOGIA
# ==========================================================

if df_mapa is not None:
    with tabs[ti]:
        st.markdown(breadcrumb(["Dados", "Metodologia"]), unsafe_allow_html=True)
        st.markdown(page_header(
            "Metodologia e Classificacoes",
            "Como os dados sao processados, cruzados e classificados neste dashboard."
        ), unsafe_allow_html=True)

        st.markdown(section_title("1. Fontes de Dados"), unsafe_allow_html=True)
        st.markdown(info_box(
            "<strong>Mapa Parque (Visao Cliente)</strong><br>"
            "Arquivo: RelatorioInfoB2B_MapaParqueVisaoCliente_*.csv<br>"
            "Origem: InfoB2B Vivo | 1 linha por CNPJ | 92 colunas<br>"
            "Conteudo: posse (movel, fixa, BL, VVN, Vivo Tech), "
            "cobertura FTTH, fidelizacao, biometria, CAR, contatos, endereco, vertical, cluster."
        ), unsafe_allow_html=True)
        st.markdown(info_box(
            "<strong>Parque Movel (Visao Linha)</strong><br>"
            "Arquivo: RelatorioInfoB2B_ParqueMovel_*.csv<br>"
            "Origem: InfoB2B Vivo | 1 linha por telefone | 45 colunas<br>"
            "Conteudo: numero, CNPJ, plano, <strong>M real</strong>, fidelizacao, "
            "faturamento, Serasa, blindagem, excedente, tipo de rede."
        ), unsafe_allow_html=True)

        st.markdown(divider(), unsafe_allow_html=True)
        st.markdown(section_title("2. Cruzamento de Dados"), unsafe_allow_html=True)
        st.markdown(info_box(
            "<strong>Passo a passo:</strong><br>"
            "1. Normalizamos CNPJ do Parque Movel (so numeros, 14 digitos)<br>"
            "2. Agrupamos por CNPJ: total linhas, fidelizadas, M min/max/medio, "
            "faturamento, linhas M17+, M7-M16, M7-M12, faixa predominante, pior Serasa<br>"
            "3. LEFT JOIN do Mapa Parque com Parque Movel agrupado (chave: CNPJ)<br>"
            "4. Resultado: colunas PM_* com dados reais<br><br>"
            "<strong>Por que importa:</strong> O Mapa Parque tem MESES_CARTEIRA (impreciso). "
            "O Parque Movel tem o <strong>M real</strong> de cada linha."
        ), unsafe_allow_html=True)

        st.markdown(divider(), unsafe_allow_html=True)
        st.markdown(section_title("3. Classificacoes"), unsafe_allow_html=True)
        st.markdown(info_box(
            "<strong>Semaforo CAR</strong> = CAR_MOVEL + CAR_FIXA<br>"
            "PRETO/CINZA: 0 | VERDE: 1-49 | AMARELO: 50-149 | VERMELHO: 150+"
        ), unsafe_allow_html=True)
        st.markdown(info_box(
            "<strong>Categoria M</strong> (do Parque Movel)<br>"
            "M0-M6: Novo | M7-M12: Janela UP | M13-M16: Pre-renovacao | "
            "M17-M21: RENOVACAO | M22+: Vencido<br>"
            "Um cliente pode ter linhas em DIFERENTES Ms!"
        ), unsafe_allow_html=True)
        st.markdown(info_box(
            "<strong>Segmentacao</strong> (derivada da posse)<br>"
            "TOTALIZACAO: movel sem fixa | MIGRACAO: fixa sem movel | "
            "BLINDAGEM: totalizado renovando | CROSS-SELL: totalizado + produtos | "
            "AVANCADOS: internet dedicada | DIGITALIZACAO: produtos digitais"
        ), unsafe_allow_html=True)

        st.markdown(info_box(

                    "<strong>Régua M (detalhamento por mês)</strong><br>"

                    "A régua M classifica as linhas em diferentes estágios de relacionamento com base no 'M' (mês) do contrato.<br>"

                    "M16: Informativo (SMS, email, WhatsApp)<br>"

                    "M17: Semanal (+ ligacao IA)<br>"

                    "M18-M22: Quinzenal, escalacao progressiva<br>"

                    "M23: Semanal emergencial<br>"

                    "M24+: Mensal, contato gerencial<br>"

                    "Essa classificação permite ações de comunicação e retenção direcionadas para cada grupo."

                ), unsafe_allow_html=True)

        st.markdown(divider(), unsafe_allow_html=True)
        st.markdown(section_title("4. Logica dos 16 Mailings"), unsafe_allow_html=True)
        mailing_docs = [
            ("1.1", "Movel s/ Fixa M17+", "TEM_MOVEL + !TEM_FIXA + PM_M17+>0"),
            ("1.2", "Movel c/ Fixa M17+", "TEM_MOVEL + TEM_FIXA + PM_M17+>0"),
            ("1.3", "Excedente M7-M16", "TEM_MOVEL + PM_M7_M16>0"),
            ("1.4", "Credito Aparelho", "TEM_MOVEL + PM_M7_M12>0 + TEM_APARELHOS"),
            ("1.5", "s/ Mancha M17-21", "TEM_MOVEL + !MANCHA + PM_M_MEDIO 17-21"),
            ("1.6", "Propensao", "PORT_POTENCIAL Alto/Medio"),
            ("2.1", "Fixa s/ Movel", "TEM_FIXA + !TEM_MOVEL"),
            ("2.2", "PEN", "TEM_PEN"),
            ("2.3", "Fixa UP", "TEM_FIXA + !MOVEL + !FIDELIZADO"),
            ("2.4", "Renovacao Fixa", "TEM_FIXA + FIDELIZADO"),
            ("3.1", "CAR", "CAR_TOTAL>0"),
            ("3.2", "Biometria", "!BIOMETRADO"),
            ("3.3", "5G", "TEM_5G"),
            ("3.4", "VTech Atual", "QTD_VTECH>0"),
            ("3.5", "VTech Potencial", "QTD_VTECH=0 + VIVO_TECH preenchido"),
            ("3.6", "Digital", "DIGITAL_1 preenchido"),
        ]
        for cod, nome, filtro in mailing_docs:
            st.markdown(
                '<div style="padding:8px 14px;border-radius:8px;background:var(--hover);'
                'margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;">'
                '<span style="font-weight:600;color:var(--tx);font-size:0.84rem;">{} - {}</span>'
                '<span style="font-size:0.74rem;color:var(--acc);font-family:monospace;'
                'background:var(--acc-bg);padding:3px 8px;border-radius:4px;">{}</span>'
                '</div>'.format(cod, nome, filtro), unsafe_allow_html=True)

        st.markdown(divider(), unsafe_allow_html=True)
        st.markdown(section_title("5. INFO_FONTE nos Mailings"), unsafe_allow_html=True)
        st.markdown(info_box(
            "Todo mailing tem coluna <strong>INFO_FONTE</strong> com: tabela de origem, "
            "colunas e filtros usados, explicacao legivel. "
            "Garante rastreabilidade total."
        ), unsafe_allow_html=True)

        st.markdown(divider(), unsafe_allow_html=True)
        st.markdown(section_title("6. Glossario"), unsafe_allow_html=True)
        glossario = [
            ("M", "Meses desde ativacao"), ("CAR", "Conta a Receber"),
            ("BL", "Banda Larga"), ("VB", "Voz Basica"), ("FTTH", "Fibra ate o cliente"),
            ("PEN", "Terminal metalico"), ("VVN", "Vivo Voz Negocio"),
            ("Big Deal", "Fat. alto"), ("MEI", "Microempreendedor"),
            ("Mancha", "Area FTTH"), ("Serasa", "Score credito"),
            ("Blindagem", "Renovacao antecipada"), ("PM_*", "Dados do Parque Movel"),
        ]
        html = '<div style="display:grid;grid-template-columns:120px 1fr;gap:3px 12px;font-size:0.82rem;">'
        for t, d in glossario:
            html += '<div style="font-weight:600;color:var(--acc);font-family:monospace;padding:3px 0;">{}</div>'.format(t)
            html += '<div style="color:var(--tx2);padding:3px 0;">{}</div>'.format(d)
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

        st.markdown(footer_html(APP_VERSION), unsafe_allow_html=True)
    ti += 1