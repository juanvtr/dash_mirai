"""
╔══════════════════════════════════════════════════════════════════════╗
║  MIRAI TELECOM - GRÁFICOS                                          ║
║  Funções de criação de gráficos Plotly padronizados                ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from config import PLOTLY_COLORS, SEMAFORO_CORES, CORES


def _base_layout(fig, title=None):
    """Aplica layout base padronizado a um gráfico."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=CORES["azul_mirai"])) if title else None,
        font=dict(family="Segoe UI, Arial", size=12, color=CORES["texto"]),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════
# GRÁFICOS DO MAPA PARQUE
# ══════════════════════════════════════════════════════════════════════

def chart_semaforo(df):
    """Gráfico de barras do semáforo CAR."""
    counts = df["SEMAFORO"].value_counts().reindex(
        ["VERDE", "AMARELO", "VERMELHO", "PRETO/CINZA"], fill_value=0
    ).reset_index()
    counts.columns = ["Semáforo", "Quantidade"]

    fig = px.bar(
        counts, x="Semáforo", y="Quantidade",
        color="Semáforo", color_discrete_map=SEMAFORO_CORES,
        text="Quantidade",
    )
    fig.update_traces(textposition="outside", texttemplate="%{text:,}")
    fig.update_layout(showlegend=False)
    return _base_layout(fig, "Situação CAR (Semáforo)")


def chart_segmentacao(df):
    """Gráfico de barras dos segmentos comerciais."""
    counts = df["SEGMENTO"].value_counts().reset_index()
    counts.columns = ["Segmento", "Quantidade"]

    fig = px.bar(
        counts, x="Segmento", y="Quantidade",
        color="Quantidade", color_continuous_scale=["#F0E6FA", "#660099"],
        text="Quantidade",
    )
    fig.update_traces(textposition="outside", texttemplate="%{text:,}")
    fig.update_xaxes(tickangle=45)
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    return _base_layout(fig, "Segmentação Comercial")


def chart_categoria_m(df):
    """Donut chart de Categoria M."""
    counts = df["CATEGORIA_M"].value_counts().reindex(
        ["M0-M6", "M7-M16", "M17-M21", "M22+"], fill_value=0
    ).reset_index()
    counts.columns = ["Categoria M", "Quantidade"]

    fig = px.pie(
        counts, values="Quantidade", names="Categoria M",
        color_discrete_sequence=PLOTLY_COLORS, hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _base_layout(fig, "Distribuição por Categoria M")


def chart_posse(df):
    """Donut chart de tipo de posse."""
    counts = df["POSSE_SIMPL"].value_counts().reset_index()
    counts.columns = ["Posse", "Quantidade"]

    fig = px.pie(
        counts, values="Quantidade", names="Posse",
        color_discrete_sequence=PLOTLY_COLORS, hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _base_layout(fig, "Distribuição por Tipo de Posse")


def chart_raio_x(df):
    """Gráfico de barras horizontais do Raio X da carteira."""
    raio_x_data = [
        ("Móvel s/ Fixa M17+", len(df[(df["TEM_MOVEL"]) & (~df["TEM_FIXA"]) & (df["MESES_CARTEIRA"] >= 17)])),
        ("Móvel c/ Fixa M17+", len(df[(df["TEM_MOVEL"]) & (df["TEM_FIXA"]) & (df["MESES_CARTEIRA"] >= 17)])),
        ("Excedente Dados M7-M16", len(df[(df["TEM_MOVEL"]) & (df["MESES_CARTEIRA"].between(7, 16))])),
        ("Fixa s/ Móvel", len(df[(df["TEM_FIXA"]) & (~df["TEM_MOVEL"])])),
        ("Clientes PEN", len(df[df["TEM_PEN"]])),
        ("CAR > 0", len(df[df["CAR_TOTAL"] > 0])),
        ("Não Biometrados", len(df[~df["BIOMETRADO"]])),
        ("Cobertura 5G", len(df[df["TEM_5G"]])),
        ("Vivo Tech Atual", len(df[df["QTD_VTECH"] > 0])),
        ("Alto Port. Potencial", len(df[df["PORT_POTENCIAL"] == "Alto"])),
    ]

    rx_df = pd.DataFrame(raio_x_data, columns=["Categoria", "Clientes"])
    rx_df = rx_df.sort_values("Clientes", ascending=True)

    fig = px.bar(
        rx_df, x="Clientes", y="Categoria", orientation="h",
        color="Clientes", color_continuous_scale=["#E8EEF7", "#2F5496"],
        text="Clientes",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(showlegend=False, coloraxis_showscale=False, height=450)
    return _base_layout(fig, "Raio X da Carteira")


def chart_heatmap_segmento_catm(df):
    """Heatmap Segmento × Categoria M."""
    cross = pd.crosstab(df["SEGMENTO"], df["CATEGORIA_M"])
    # Reorder columns
    for col in ["M0-M6", "M7-M16", "M17-M21", "M22+"]:
        if col not in cross.columns:
            cross[col] = 0
    cross = cross[["M0-M6", "M7-M16", "M17-M21", "M22+"]]

    fig = px.imshow(
        cross, labels=dict(x="Categoria M", y="Segmento", color="Clientes"),
        color_continuous_scale=["#F8F5FC", "#660099"],
        aspect="auto", text_auto=True,
    )
    return _base_layout(fig, "Segmento × Categoria M")


def chart_fidelizacao(df):
    """Gráfico de barras de fidelização."""
    data = pd.DataFrame({
        "Status": ["Fidelizados", "Não Fidelizados"],
        "Quantidade": [df["FIDELIZADO"].sum(), len(df) - df["FIDELIZADO"].sum()],
    })
    fig = px.bar(
        data, x="Status", y="Quantidade", color="Status",
        color_discrete_map={"Fidelizados": "#92D050", "Não Fidelizados": "#FF6600"},
        text="Quantidade",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(showlegend=False)
    return _base_layout(fig, "Situação de Fidelização")


# ══════════════════════════════════════════════════════════════════════
# GRÁFICOS DE DEALS
# ══════════════════════════════════════════════════════════════════════

def chart_deals_por_fase(df):
    """Distribuição de deals por fase do funil."""
    if "Fase" not in df.columns:
        return None
    counts = df["Fase"].value_counts().reset_index()
    counts.columns = ["Fase", "Quantidade"]
    fig = px.bar(
        counts, x="Fase", y="Quantidade", color="Fase",
        color_discrete_sequence=PLOTLY_COLORS, text="Quantidade",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_xaxes(tickangle=45)
    fig.update_layout(showlegend=False)
    return _base_layout(fig, "Deals por Fase do Funil")


def chart_deals_por_tipo(df_concluidos):
    """Donut chart de deals concluídos por tipo agrupado."""
    if "TIPO_AGRUPADO" not in df_concluidos.columns:
        return None
    counts = df_concluidos["TIPO_AGRUPADO"].value_counts().reset_index()
    counts.columns = ["Tipo", "Quantidade"]
    fig = px.pie(
        counts, values="Quantidade", names="Tipo",
        color_discrete_sequence=PLOTLY_COLORS, hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _base_layout(fig, "Pedidos Concluídos por Tipo")


def chart_deals_por_gerencia(df_concluidos):
    """Top gerências por deals concluídos."""
    if "Gerência" not in df_concluidos.columns:
        return None
    ger = df_concluidos.groupby("Gerência").agg(
        pedidos=("Gerência", "count"),
        linhas=("QTD_LINHAS", "sum") if "QTD_LINHAS" in df_concluidos.columns else ("Gerência", "count"),
    ).sort_values("pedidos", ascending=True).tail(10).reset_index()

    fig = px.bar(
        ger, x="pedidos", y="Gerência", orientation="h",
        color="pedidos", color_continuous_scale=["#E8EEF7", "#2F5496"],
        text="pedidos",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    return _base_layout(fig, "Top Gerências (Concluídos)")


def chart_deals_por_consultor(df_concluidos, top_n=10):
    """Top consultores por deals concluídos."""
    if "Nome do Consultor" not in df_concluidos.columns:
        return None
    cons = df_concluidos["Nome do Consultor"].value_counts().head(top_n).reset_index()
    cons.columns = ["Consultor", "Pedidos"]
    cons = cons.sort_values("Pedidos", ascending=True)

    fig = px.bar(
        cons, x="Pedidos", y="Consultor", orientation="h",
        color="Pedidos", color_continuous_scale=["#F0E6FA", "#660099"],
        text="Pedidos",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    return _base_layout(fig, f"Top {top_n} Consultores (Concluídos)")


# ══════════════════════════════════════════════════════════════════════
# GRÁFICOS DE CRUZAMENTO
# ══════════════════════════════════════════════════════════════════════

def chart_penetracao_deals(df_mapa):
    """Pizza de penetração: clientes com/sem deal."""
    com_deal = df_mapa["TEM_DEAL"].sum()
    sem_deal = len(df_mapa) - com_deal

    fig = go.Figure(data=[go.Pie(
        labels=["Com Deal", "Sem Deal"],
        values=[com_deal, sem_deal],
        marker_colors=[CORES["roxo_vivo"], CORES["amarelo"]],
        hole=0.45,
        textinfo="percent+value",
    )])
    return _base_layout(fig, "Penetração de Deals na Base")


def chart_penetracao_por_segmento(df_mapa):
    """Barras empilhadas: com/sem deal por segmento."""
    seg_stats = df_mapa.groupby("SEGMENTO").agg(
        com_deal=("TEM_DEAL", "sum"),
        total=("TEM_DEAL", "count"),
    ).reset_index()
    seg_stats["sem_deal"] = seg_stats["total"] - seg_stats["com_deal"]
    seg_stats["penetracao"] = (seg_stats["com_deal"] / seg_stats["total"] * 100).round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Com Deal", x=seg_stats["SEGMENTO"], y=seg_stats["com_deal"],
        marker_color=CORES["roxo_vivo"], text=seg_stats["com_deal"],
        texttemplate="%{text:,}", textposition="inside",
    ))
    fig.add_trace(go.Bar(
        name="Sem Deal", x=seg_stats["SEGMENTO"], y=seg_stats["sem_deal"],
        marker_color=CORES["borda"], text=seg_stats["sem_deal"],
        texttemplate="%{text:,}", textposition="inside",
    ))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(tickangle=45)
    return _base_layout(fig, "Penetração por Segmento")


def chart_portabilidade_potencial_vs_real(df_mapa):
    """Barras agrupadas: potencial de portabilidade vs deals realizados."""
    mig = df_mapa[df_mapa["SEGMENTO"] == "MIGRAÇÃO MÓVEL"]
    if len(mig) == 0:
        return None

    stats = []
    for pot in ["Alto", "Médio", "Baixo", "Renovação", "Sem info"]:
        pot_df = mig[mig["PORT_POTENCIAL"] == pot]
        stats.append({
            "Potencial": pot,
            "Total": len(pot_df),
            "Com Deal": pot_df["TEM_DEAL"].sum(),
        })
    df_stats = pd.DataFrame(stats)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Total no Mapa", x=df_stats["Potencial"], y=df_stats["Total"],
        marker_color=CORES["azul_mirai"], text=df_stats["Total"],
        texttemplate="%{text:,}", textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Com Deal", x=df_stats["Potencial"], y=df_stats["Com Deal"],
        marker_color=CORES["roxo_vivo"], text=df_stats["Com Deal"],
        texttemplate="%{text:,}", textposition="outside",
    ))
    fig.update_layout(barmode="group")
    return _base_layout(fig, "Potencial Portabilidade × Deals Realizados")
