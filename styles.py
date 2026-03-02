"""
╔══════════════════════════════════════════════════════════════════════╗
║  MIRAI TELECOM - ESTILOS CSS                                       ║
║  Tema visual baseado nas cores Vivo/Mirai                          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

CUSTOM_CSS = """
<style>
    /* ── Reset & Base ── */
    .main .block-container {
        padding-top: 1rem;
        max-width: 1400px;
    }

    /* ── Header Principal ── */
    .main-header {
        background: linear-gradient(135deg, #660099 0%, #2F5496 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(102, 0, 153, 0.3);
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.85;
        font-size: 1rem;
    }

    /* ── KPI Cards ── */
    .kpi-card {
        background: white;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #660099;
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .kpi-icon { font-size: 1.8rem; }
    .kpi-title {
        font-size: 0.8rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.3rem;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #2F5496;
    }
    .kpi-delta {
        font-size: 0.75rem;
        color: #92D050;
    }

    /* ── Semáforo badges ── */
    .badge-verde {
        background-color: #92D050; color: black;
        padding: 3px 10px; border-radius: 12px;
        font-size: 0.8rem; font-weight: 600;
    }
    .badge-amarelo {
        background-color: #FFD700; color: black;
        padding: 3px 10px; border-radius: 12px;
        font-size: 0.8rem; font-weight: 600;
    }
    .badge-vermelho {
        background-color: #FF0000; color: white;
        padding: 3px 10px; border-radius: 12px;
        font-size: 0.8rem; font-weight: 600;
    }
    .badge-preto {
        background-color: #333; color: white;
        padding: 3px 10px; border-radius: 12px;
        font-size: 0.8rem; font-weight: 600;
    }

    /* ── Section headers ── */
    .section-header {
        color: #2F5496;
        border-bottom: 3px solid #660099;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
        font-weight: 700;
    }

    /* ── Info boxes ── */
    .info-box {
        background-color: #F0E6FA;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid #660099;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
    .info-box-blue {
        background-color: #E8EEF7;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid #2F5496;
        margin-bottom: 1rem;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F8F5FC 0%, #FFFFFF 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown h2 {
        color: #660099;
    }

    /* ── Download buttons ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #660099, #2F5496) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .stDownloadButton > button:hover {
        opacity: 0.9;
    }

    /* ── Tab styling ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #660099 !important;
        color: white !important;
    }

    /* ── Métrica customizada ── */
    [data-testid="stMetricValue"] {
        color: #2F5496;
        font-weight: 700;
    }

    /* ── Divider ── */
    .purple-divider {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, #660099, #2F5496, transparent);
        margin: 1.5rem 0;
    }
</style>
"""


def render_kpi_card(icon, title, value, delta=None):
    """Retorna HTML de um KPI card."""
    delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    return f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """


def render_header(title, subtitle):
    """Retorna HTML do header principal."""
    return f"""
    <div class="main-header">
        <h1> {title}</h1>
        <p>{subtitle}</p>
    </div>
    """
