# -*- coding: utf-8 -*-
"""Mirai Insights v4 - Graficos Plotly com suporte a temas."""

import plotly.express as px
import plotly.graph_objects as go
from config import CHART_COLORS, CHART_COLORS_DARK, SEMAFORO_CORES, SEMAFORO_SERASA_CORES


def _colors(theme="light"):
    return CHART_COLORS if theme == "light" else CHART_COLORS_DARK


def _layout(title="", theme="light"):
    is_dark = theme == "dark"
    return dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="DM Sans, -apple-system, sans-serif",
            color="#F5F5F7" if is_dark else "#1D1D1F",
            size=12,
        ),
        margin=dict(l=40, r=20, t=50, b=40),
        title=dict(text=title, font=dict(size=15, color="#F5F5F7" if is_dark else "#1D1D1F")) if title else None,
        xaxis=dict(gridcolor="#2E2E2E" if is_dark else "#F0F0F0", zerolinecolor="#2E2E2E" if is_dark else "#E5E5E5"),
        yaxis=dict(gridcolor="#2E2E2E" if is_dark else "#F0F0F0", zerolinecolor="#2E2E2E" if is_dark else "#E5E5E5"),
    )


# -- Mapa Parque --

def chart_semaforo(df, theme="light"):
    order = ["VERDE", "AMARELO", "VERMELHO", "PRETO/CINZA"]
    counts = df["SEMAFORO"].value_counts().reindex(order, fill_value=0)
    fig = go.Figure(go.Bar(
        x=counts.index, y=counts.values,
        marker_color=[SEMAFORO_CORES.get(s, "#999") for s in counts.index],
        text=counts.values, textposition="outside",
        textfont=dict(size=11),
    ))
    fig.update_layout(**_layout("Semaforo CAR", theme))
    fig.update_layout(height=350)
    return fig


def chart_segmentacao(df, theme="light"):
    counts = df["SEGMENTO"].value_counts()
    colors = _colors(theme)
    fig = go.Figure(go.Bar(
        x=counts.values, y=counts.index, orientation="h",
        marker_color=colors[:len(counts)],
        text=counts.values, textposition="outside",
        textfont=dict(size=11),
    ))
    fig.update_layout(**_layout("Segmentacao Comercial", theme))
    fig.update_layout(yaxis=dict(autorange="reversed"), height=380)
    return fig


def chart_categoria_m(df, theme="light"):
    col = "CATEGORIA_M_REAL" if "CATEGORIA_M_REAL" in df.columns else "CATEGORIA_M"
    counts = df[col].value_counts()
    colors = _colors(theme)
    fig = px.pie(values=counts.values, names=counts.index, hole=0.45,
                 color_discrete_sequence=colors)
    fig.update_layout(**_layout("Categoria M", theme))
    fig.update_layout(height=350, showlegend=True, legend=dict(font=dict(size=11)))
    fig.update_traces(textinfo="percent+value", textfont_size=11)
    return fig


def chart_posse(df, theme="light"):
    counts = df["POSSE_SIMPL"].value_counts()
    colors = _colors(theme)
    fig = px.pie(values=counts.values, names=counts.index, hole=0.45,
                 color_discrete_sequence=colors)
    fig.update_layout(**_layout("Tipo de Posse", theme))
    fig.update_layout(height=350, showlegend=True)
    fig.update_traces(textinfo="percent+value", textfont_size=11)
    return fig


def chart_raio_x(df, theme="light"):
    has_pm = "PM_LINHAS_M17_PLUS" in df.columns
    items = [
        ("Movel s/ Fixa M17+", len(df[(df["TEM_MOVEL"]) & (~df["TEM_FIXA"]) & ((df["PM_LINHAS_M17_PLUS"] > 0) if has_pm else (df["MESES_CARTEIRA"] >= 17))])),
        ("Movel c/ Fixa M17+", len(df[(df["TEM_MOVEL"]) & (df["TEM_FIXA"]) & ((df["PM_LINHAS_M17_PLUS"] > 0) if has_pm else (df["MESES_CARTEIRA"] >= 17))])),
        ("Fixa s/ Movel", len(df[(df["TEM_FIXA"]) & (~df["TEM_MOVEL"])])),
        ("Clientes PEN", len(df[df["TEM_PEN"]])),
        ("Cobertura 5G", len(df[df["TEM_5G"]])),
        ("Nao Biometrado", len(df[~df["BIOMETRADO"]])),
        ("Vivo Tech", len(df[df["QTD_VTECH"] > 0])),
        ("CAR > 0", len(df[df["CAR_TOTAL"] > 0])),
    ]
    labels, vals = zip(*items)
    colors = _colors(theme)
    fig = go.Figure(go.Bar(
        y=list(labels), x=list(vals), orientation="h",
        marker_color=colors[:len(items)],
        text=list(vals), textposition="outside",
        textfont=dict(size=11),
    ))
    fig.update_layout(**_layout("Raio X da Carteira", theme))
    fig.update_layout(yaxis=dict(autorange="reversed"), height=400)
    return fig


def chart_heatmap_segmento_catm(df, theme="light"):
    col = "CATEGORIA_M_REAL" if "CATEGORIA_M_REAL" in df.columns else "CATEGORIA_M"
    cross = df.groupby(["SEGMENTO", col]).size().unstack(fill_value=0)
    cscale = ["#1E0A2E", "#660099"] if theme == "dark" else ["#F3E8FF", "#660099"]
    fig = px.imshow(cross, text_auto=True, color_continuous_scale=cscale)
    fig.update_layout(**_layout("Segmento x Categoria M", theme))
    fig.update_layout(height=420)
    return fig


def chart_fidelizacao(df, theme="light"):
    fid = df["FIDELIZADO"].value_counts().rename({True: "Fidelizado", False: "Nao Fidelizado"})
    fig = go.Figure(go.Bar(
        x=fid.index, y=fid.values,
        marker_color=["#34A853", "#EA4335"],
        text=fid.values, textposition="outside",
    ))
    fig.update_layout(**_layout("Fidelizacao", theme))
    fig.update_layout(height=350)
    return fig


# -- Parque Movel --

def chart_faixa_m_linhas(df_movel, theme="light"):
    order = ["M0-M6", "M7-M12", "M13-M16", "M17-M21", "M22+"]
    counts = df_movel["FAIXA_M"].value_counts().reindex(order, fill_value=0)
    colors = _colors(theme)
    fig = go.Figure(go.Bar(
        x=counts.index, y=counts.values,
        marker_color=colors[:len(counts)],
        text=counts.values, textposition="outside",
    ))
    fig.update_layout(**_layout("Linhas por Faixa de M", theme))
    fig.update_layout(height=350)
    return fig


def chart_fidelizacao_linhas(df_movel, theme="light"):
    fid = df_movel["FIDELIZADO_MOVEL"].value_counts().rename({True: "Fidelizada", False: "Nao Fidelizada"})
    fig = go.Figure(go.Bar(
        x=fid.index, y=fid.values,
        marker_color=["#34A853", "#EA4335"],
        text=fid.values, textposition="outside",
    ))
    fig.update_layout(**_layout("Fidelizacao por Linha", theme))
    fig.update_layout(height=350)
    return fig


def chart_serasa_linhas(df_movel, theme="light"):
    order = ["VERDE", "AMARELO", "VERMELHO", "CINZA", "PRETO"]
    counts = df_movel["SEMAFORO_SERASA"].value_counts().reindex(order, fill_value=0)
    fig = go.Figure(go.Bar(
        x=counts.index, y=counts.values,
        marker_color=[SEMAFORO_SERASA_CORES.get(s, "#999") for s in counts.index],
        text=counts.values, textposition="outside",
    ))
    fig.update_layout(**_layout("Semaforo Serasa", theme))
    fig.update_layout(height=350)
    return fig


def chart_blindagem(df_movel, theme="light"):
    counts = df_movel["ELEGIVEL_BLINDAR_FLAG"].value_counts().rename({True: "Elegivel", False: "Nao Elegivel"})
    colors = _colors(theme)
    fig = px.pie(values=counts.values, names=counts.index, hole=0.45,
                 color_discrete_sequence=[colors[4], colors[7]])
    fig.update_layout(**_layout("Elegibilidade Blindagem", theme))
    fig.update_layout(height=320)
    return fig


def chart_planos_top(df_movel, top_n=10, theme="light"):
    counts = df_movel["PLANO"].value_counts().head(top_n)
    colors = _colors(theme)
    fig = go.Figure(go.Bar(
        y=counts.index, x=counts.values, orientation="h",
        marker_color=colors[:len(counts)],
        text=counts.values, textposition="outside",
    ))
    fig.update_layout(**_layout("Top {} Planos".format(top_n), theme))
    fig.update_layout(yaxis=dict(autorange="reversed"), height=400)
    return fig


def chart_m_por_cliente(df_movel, theme="light"):
    faixas = ["M0-M6", "M7-M12", "M13-M16", "M17-M21", "M22+"]
    cross = df_movel.groupby(["CNPJ_NORM", "FAIXA_M"]).size().unstack(fill_value=0)
    cross = cross.reindex(columns=[f for f in faixas if f in cross.columns], fill_value=0)
    resumo = (cross > 0).sum()
    colors = _colors(theme)
    fig = go.Figure(go.Bar(
        x=resumo.index, y=resumo.values,
        marker_color=colors[:len(resumo)],
        text=resumo.values, textposition="outside",
    ))
    fig.update_layout(**_layout("Clientes com Linhas em Cada Faixa M", theme))
    fig.update_layout(height=350)
    return fig


# -- Regua M --

def chart_regua_m(df_movel, theme="light"):
    """Distribuicao de linhas nas faixas da regua de relacionamento (M16 a M24+)."""
    m = df_movel["M_INT"]
    bins = {
        "M16": ((m >= 16) & (m < 17)).sum(),
        "M17": ((m >= 17) & (m < 18)).sum(),
        "M18": ((m >= 18) & (m < 19)).sum(),
        "M19": ((m >= 19) & (m < 20)).sum(),
        "M20": ((m >= 20) & (m < 21)).sum(),
        "M21": ((m >= 21) & (m < 22)).sum(),
        "M22": ((m >= 22) & (m < 23)).sum(),
        "M23": ((m >= 23) & (m < 24)).sum(),
        "M24+": (m >= 24).sum(),
    }
    colors = _colors(theme)
    fig = go.Figure(go.Bar(
        x=list(bins.keys()), y=list(bins.values()),
        marker_color=colors[:len(bins)],
        text=list(bins.values()), textposition="outside",
    ))
    fig.update_layout(**_layout("Linhas na Regua de Relacionamento (M16-M24+)", theme))
    fig.update_layout(height=380)
    return fig
