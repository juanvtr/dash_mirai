# -*- coding: utf-8 -*-
"""
Mirai Insights v4 - Design System com paleta da logo.
Gradiente: magenta #D946EF -> roxo #8B5CF6 -> ciano #06B6D4
"""

from config import LIGHT, DARK


def get_css(theme="light"):
    t = LIGHT if theme == "light" else DARK
    return """<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {{
        --bg: {bg}; --bg2: {bg2}; --sidebar: {sidebar}; --card: {card};
        --hover: {hover}; --border: {border}; --border-h: {border_h};
        --tx: {tx}; --tx2: {tx2}; --tx3: {tx3};
        --acc: {acc}; --acc-h: {acc_h}; --acc-bg: {acc_bg};
        --acc2: {acc2}; --acc3: {acc3};
        --sh1: {sh1}; --sh2: {sh2};
        --grad: linear-gradient(135deg, {acc2}, {acc}, {acc3});
    }}

    /* ===== RESET ===== */
    html, body, .stApp {{
        background: var(--bg) !important;
        color: var(--tx) !important;
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}
    h1, h2, h3 {{ font-family: 'DM Sans', -apple-system, sans-serif !important; }}

    /* Esconde lixo do Streamlit mas mantem sidebar toggle funcional */
    #MainMenu {{ visibility: hidden !important; }}
    footer {{ visibility: hidden !important; }}
    .stDeployButton {{ display: none !important; }}
    header[data-testid="stHeader"] {{
        background: transparent !important;
        border: none !important;
    }}
    /* Esconde toolbar (Stop/Deploy/menu) mas nao o sidebar toggle */
    [data-testid="stStatusWidget"] {{ display: none !important; }}

    .block-container {{ padding-top: 1.2rem !important; max-width: 1180px !important; }}

    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {{
        background: var(--sidebar) !important;
        border-right: 1px solid var(--border) !important;
    }}
    section[data-testid="stSidebar"] * {{ color: var(--tx) !important; }}
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stCheckbox label {{
        font-size: 0.78rem !important; font-weight: 500 !important; color: var(--tx2) !important;
    }}
    /* Botao de collapse da sidebar - manter visivel e estilizado */
    section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] {{
        color: var(--tx2) !important;
    }}

    /* ===== SIDEBAR COLLAPSE: botao de reabrir ===== */
    [data-testid="collapsedControl"] {{
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        box-shadow: var(--sh2) !important;
        margin: 8px !important;
    }}
    [data-testid="collapsedControl"]:hover {{
        border-color: var(--acc) !important;
        background: var(--hover) !important;
    }}
    [data-testid="collapsedControl"] svg {{
        fill: var(--tx2) !important;
    }}

    /* ===== UPLOADER ===== */
    [data-testid="stFileUploaderDropzone"] {{
        background: transparent !important;
        border: 1px dashed var(--border) !important;
    }}
    [data-testid="stFileUploaderDropzone"] p, [data-testid="stFileUploaderDropzone"] span {{
        color: var(--tx2) !important;
    }}
    [data-testid="stFileUploaderDropzone"] svg {{
        fill: var(--tx3) !important;
    }}

    /* ===== BREADCRUMB ===== */
    .bc {{ display:flex; align-items:center; gap:6px; padding:8px 0 4px; font-size:0.82rem; }}
    .bc a {{ color: var(--tx3); text-decoration:none; transition: color 0.15s; }}
    .bc a:hover {{ color: var(--acc); }}
    .bc .sep {{ color: var(--tx3); font-size:0.7rem; }}
    .bc .cur {{ color: var(--tx2); font-weight:600; }}

    /* ===== PAGE HEADER ===== */
    .ph {{ padding:0 0 24px; border-bottom:1px solid var(--border); margin-bottom:24px; }}
    .ph h1 {{
        font-size:2rem; font-weight:700; margin:0; line-height:1.2; letter-spacing:-0.03em;
        background: var(--grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .ph p {{ color:var(--tx2); font-size:0.88rem; margin:6px 0 0; line-height:1.5; }}

    /* ===== KPI CARD ===== */
    .kg {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(155px, 1fr)); gap:12px; margin:16px 0; }}
    .k {{
        background:var(--card); border:1px solid var(--border); border-radius:10px;
        padding:16px 18px; transition: all 0.15s ease; cursor:default;
    }}
    .k:hover {{ border-color:var(--border-h); box-shadow:var(--sh2); transform:translateY(-1px); }}
    .kv {{ font-size:1.55rem; font-weight:700; color:var(--tx); line-height:1.2; letter-spacing:-0.01em; }}
    .kl {{ font-size:0.76rem; color:var(--tx2); margin-top:4px; font-weight:500; }}
    .ka .kv {{
        background: var(--grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    /* ===== SECTION / DIVIDER ===== */
    .st {{ font-size:1.2rem; font-weight:600; color:var(--tx); margin:24px 0 12px; letter-spacing:-0.01em; }}
    .dv {{ height:1px; background:var(--border); margin:24px 0; border:none; }}
    .dv-grad {{
        height:2px; border:none; margin:24px 0;
        background: var(--grad);
        border-radius: 1px;
    }}

    /* ===== INFO BOX ===== */
    .ib {{
        background:var(--acc-bg); border:1px solid var(--border); border-radius:10px;
        padding:14px 18px; font-size:0.84rem; color:var(--tx2); line-height:1.6; margin:12px 0 20px;
    }}
    .ib strong {{ color:var(--tx); }}

    /* ===== CARDS ===== */
    .cg {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:14px; margin:16px 0; }}
    .cd {{
        background:var(--card); border:1px solid var(--border); border-radius:10px;
        padding:18px 20px; transition: all 0.15s ease;
    }}
    .cd:hover {{ border-color:var(--border-h); box-shadow:var(--sh2); transform:translateY(-1px); }}
    .cd-tag {{ font-size:0.7rem; font-weight:600; color:var(--acc); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px; }}
    .cd-t {{ font-size:1rem; font-weight:600; color:var(--tx); margin-bottom:4px; line-height:1.3; }}
    .cd-d {{ font-size:0.82rem; color:var(--tx2); line-height:1.5; }}
    .cd-b {{
        display:inline-block; background:var(--acc-bg); color:var(--acc);
        padding:3px 10px; border-radius:16px; font-size:0.72rem; font-weight:600; margin-top:10px;
    }}

    /* ===== MAILING CARD ===== */
    .mc {{
        background:var(--card); border:1px solid var(--border); border-radius:10px;
        padding:16px 18px; transition:all 0.15s ease; margin-bottom:12px;
    }}
    .mc:hover {{ border-color:var(--border-h); box-shadow:var(--sh2); }}
    .mc-h {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px; }}
    .mc-c {{ font-size:0.88rem; font-weight:600; color:var(--tx); }}
    .mc-n {{ font-size:0.7rem; font-weight:600; padding:3px 10px; border-radius:14px; font-family:'JetBrains Mono',monospace; }}
    .mc-o {{ font-size:0.76rem; font-weight:500; padding:4px 10px; border-radius:6px; margin-bottom:6px; display:inline-block; }}
    .mc-ob {{ font-size:0.76rem; color:var(--tx2); line-height:1.5; }}

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {{ gap:0; border-bottom:1px solid var(--border); background:transparent; }}
    .stTabs [data-baseweb="tab"] {{
        border-radius:0; padding:10px 20px; font-weight:500; font-size:0.84rem;
        color: var(--tx2) !important; border-bottom:2px solid transparent;
        background:transparent !important; transition:all 0.15s ease;
    }}
    .stTabs [data-baseweb="tab"]:hover {{ color:var(--tx) !important; background:var(--hover) !important; }}
    .stTabs [aria-selected="true"] {{ color:var(--acc) !important; border-bottom-color:var(--acc) !important; font-weight:600; }}

    /* ===== INPUTS ===== */
    .stSelectbox > div > div, .stMultiSelect > div > div, .stTextInput > div > div {{
        border-color: var(--border) !important; border-radius:8px !important; background:var(--card) !important;
    }}
    .stSelectbox > div > div:focus-within, .stTextInput > div > div:focus-within {{
        border-color:var(--acc) !important; box-shadow:0 0 0 1px var(--acc) !important;
    }}

    /* ===== BUTTONS ===== */
    .stDownloadButton > button, .stButton > button {{
        background:var(--card) !important; color:var(--acc) !important;
        border:1px solid var(--border) !important; border-radius:8px !important;
        font-weight:500 !important; font-size:0.82rem !important; padding:6px 16px !important;
        transition:all 0.15s ease !important;
    }}
    .stDownloadButton > button:hover, .stButton > button:hover {{
        border-color:var(--acc) !important; background:var(--acc-bg) !important;
    }}

    /* ===== DATAFRAMES ===== */
    .stDataFrame {{ border-radius:10px; overflow:hidden; }}
    .stDataFrame [data-testid="stDataFrameResizable"] {{ border:1px solid var(--border) !important; border-radius:10px; }}

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {{
        font-size:0.86rem !important; font-weight:500 !important; color:var(--tx) !important;
        background:transparent !important; border:none !important; padding:8px 0 !important;
    }}

    /* ===== WELCOME ===== */
    .wc {{ text-align:center; padding:60px 24px; }}
    .wc h2 {{
        font-size:2.4rem; font-weight:700; margin-bottom:12px; letter-spacing:-0.03em;
        background: var(--grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .wc p {{ color:var(--tx2); font-size:1rem; max-width:520px; margin:0 auto; line-height:1.6; }}

    /* ===== FOOTER ===== */
    .ft {{
        display:flex; justify-content:space-between; padding:20px 0 12px;
        border-top:1px solid var(--border); margin-top:32px; font-size:0.74rem; color:var(--tx3);
    }}

    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {{ width:5px; }}
    ::-webkit-scrollbar-track {{ background:var(--bg2); }}
    ::-webkit-scrollbar-thumb {{ background:var(--border); border-radius:3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background:var(--tx3); }}

    /* ===== PLOTLY ===== */
    .js-plotly-plot .plotly .modebar {{ display:none !important; }}
</style>""".format(**t)


# ===== COMPONENTS =====

def breadcrumb(items):
    parts = []
    for i, item in enumerate(items):
        if i == len(items) - 1:
            parts.append('<span class="cur">{}</span>'.format(item))
        else:
            parts.append('<a href="#">{}</a>'.format(item))
            parts.append('<span class="sep">&#x203A;</span>')
    return '<div class="bc">{}</div>'.format("".join(parts))


def page_header(title, desc=""):
    d = "<p>{}</p>".format(desc) if desc else ""
    return '<div class="ph"><h1>{}</h1>{}</div>'.format(title, d)


def kpi_card(label, value, accent=False):
    cls = "k ka" if accent else "k"
    return '<div class="{}"><div class="kv">{}</div><div class="kl">{}</div></div>'.format(cls, value, label)


def kpi_grid(cards):
    return '<div class="kg">{}</div>'.format("".join(cards))


def section_title(text):
    return '<div class="st">{}</div>'.format(text)


def divider():
    return '<hr class="dv">'


def divider_grad():
    return '<hr class="dv-grad">'


def info_box(html):
    return '<div class="ib">{}</div>'.format(html)


def mailing_card_html(code, name, count, objetivo, obs, color="#8B5CF6"):
    return (
        '<div class="mc">'
        '<div class="mc-h">'
        '<div class="mc-c">{code} {name}</div>'
        '<span class="mc-n" style="background:{c}18;color:{c};">{count:,}</span>'
        '</div>'
        '<span class="mc-o" style="background:{c}12;color:{c};">{obj}</span>'
        '<div class="mc-ob">{obs}</div>'
        '</div>'
    ).format(code=code, name=name, count=count, obj=objetivo, obs=obs, c=color)


def segment_card(tag, title, desc, badge=""):
    b = '<div class="cd-b">{}</div>'.format(badge) if badge else ""
    return (
        '<div class="cd">'
        '<div class="cd-tag">{}</div>'
        '<div class="cd-t">{}</div>'
        '<div class="cd-d">{}</div>'
        '{}'
        '</div>'
    ).format(tag, title, desc, b)


def welcome_html():
    return (
        '<div class="wc">'
        '<h2>Mirai Insights</h2>'
        '<p>Carregue o <strong>Mapa Parque</strong> e o <strong>Parque Movel</strong> '
        'na barra lateral para iniciar a analise da carteira B2B.</p>'
        '<div class="cg" style="max-width:500px;margin:32px auto 0;">'
        + segment_card("Passo 1", "Mapa Parque", "Visao consolidada por CNPJ.")
        + segment_card("Passo 2", "Parque Movel", "Cada linha com M real do contrato.")
        + '</div></div>'
    )


def footer_html(version):
    from datetime import datetime
    return (
        '<div class="ft">'
        '<span>Mirai Insights v{v}</span>'
        '<span>{d}</span>'
        '<span>Mirai Telecom</span>'
        '</div>'
    ).format(v=version, d=datetime.now().strftime("%d/%m/%Y %H:%M"))