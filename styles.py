# -*- coding: utf-8 -*-
"""Mirai Insights v4 - Sidebar fixa, linhas finas com cores da logo, ultra clean."""

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

    html, body, .stApp {{
        background: var(--bg) !important;
        color: var(--tx) !important;
        font-family: 'DM Sans', -apple-system, sans-serif !important;
    }}

    /* Header limpo */
    #MainMenu {{ visibility: hidden !important; }}
    footer {{ visibility: hidden !important; }}
    header[data-testid="stHeader"] {{
        background: transparent !important;
        border: none !important;
    }}
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    /* Esconde Deploy mas nao o toolbar inteiro (senao mata o sidebar toggle) */
    [data-testid="stToolbar"] > div > div:last-child {{ display: none !important; }}
    .block-container {{ padding-top: 1rem !important; max-width: 1180px !important; }}

    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {{
        background: var(--sidebar) !important;
        border-right: 1px solid var(--border) !important;
    }}
    section[data-testid="stSidebar"] > div {{ padding-top: 0.5rem !important; }}
    section[data-testid="stSidebar"] * {{ color: var(--tx) !important; }}

    /* Botao de reabrir sidebar */
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

    /* Labels da sidebar */
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stCheckbox label,
    section[data-testid="stSidebar"] .stFileUploader label {{
        font-size: 0.76rem !important;
        font-weight: 500 !important;
        color: var(--tx2) !important;
        letter-spacing: 0.01em;
    }}

    /* File uploader clean */
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] {{
        border: none !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
        background: transparent !important;
        border: 1px dashed var(--border) !important;
        border-radius: 8px !important;
        padding: 8px !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {{
        border-color: var(--acc) !important;
    }}

    /* Sidebar divider - linha fina com gradiente da logo */
    .sb-line {{
        height: 1px;
        background: var(--grad);
        margin: 10px 0;
        border: none;
        opacity: 0.4;
    }}

    /* ===== BREADCRUMB ===== */
    .bc {{ display:flex; align-items:center; gap:6px; padding:6px 0 2px; font-size:0.8rem; }}
    .bc a {{ color: var(--tx3); text-decoration:none; transition: color 0.15s; }}
    .bc a:hover {{ color: var(--acc); }}
    .bc .sep {{ color: var(--tx3); font-size:0.65rem; }}
    .bc .cur {{ color: var(--tx2); font-weight:500; }}

    /* ===== PAGE HEADER ===== */
    .ph {{ padding:0 0 20px; border-bottom:1px solid var(--border); margin-bottom:20px; }}
    .ph h1 {{
        font-size:1.8rem; font-weight:700; margin:0; line-height:1.2; letter-spacing:-0.03em;
        background: var(--grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .ph p {{ color:var(--tx2); font-size:0.84rem; margin:4px 0 0; line-height:1.5; }}

    /* ===== KPI CARD ===== */
    .kg {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(145px, 1fr)); gap:10px; margin:14px 0; }}
    .k {{
        background:var(--card); border:1px solid var(--border); border-radius:8px;
        padding:14px 16px; transition: all 0.15s ease;
    }}
    .k:hover {{ border-color:var(--border-h); box-shadow:var(--sh2); }}
    .kv {{ font-size:1.4rem; font-weight:700; color:var(--tx); line-height:1.2; letter-spacing:-0.01em; }}
    .kl {{ font-size:0.72rem; color:var(--tx2); margin-top:3px; font-weight:500; }}
    .ka .kv {{
        background: var(--grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    /* ===== SECTIONS ===== */
    .st {{ font-size:1.1rem; font-weight:600; color:var(--tx); margin:20px 0 10px; letter-spacing:-0.01em; }}
    .dv {{ height:1px; background:var(--border); margin:20px 0; border:none; }}
    .dv-grad {{ height:1px; border:none; margin:20px 0; background:var(--grad); opacity:0.5; }}

    /* ===== INFO BOX ===== */
    .ib {{
        background:var(--acc-bg); border:1px solid var(--border); border-radius:8px;
        padding:12px 16px; font-size:0.82rem; color:var(--tx2); line-height:1.6; margin:10px 0 16px;
    }}
    .ib strong {{ color:var(--tx); }}

    /* ===== CARDS ===== */
    .cg {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:12px; margin:14px 0; }}
    .cd {{
        background:var(--card); border:1px solid var(--border); border-radius:8px;
        padding:16px 18px; transition: all 0.15s ease;
    }}
    .cd:hover {{ border-color:var(--border-h); box-shadow:var(--sh2); }}
    .cd-tag {{ font-size:0.68rem; font-weight:600; color:var(--acc); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:5px; }}
    .cd-t {{ font-size:0.95rem; font-weight:600; color:var(--tx); margin-bottom:3px; }}
    .cd-d {{ font-size:0.8rem; color:var(--tx2); line-height:1.4; }}
    .cd-b {{
        display:inline-block; background:var(--acc-bg); color:var(--acc);
        padding:2px 8px; border-radius:12px; font-size:0.7rem; font-weight:600; margin-top:8px;
    }}

    /* ===== MAILING CARD ===== */
    .mc {{
        background:var(--card); border:1px solid var(--border); border-radius:8px;
        padding:14px 16px; transition:all 0.15s ease; margin-bottom:10px;
    }}
    .mc:hover {{ border-color:var(--border-h); box-shadow:var(--sh2); }}
    .mc-h {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px; }}
    .mc-c {{ font-size:0.84rem; font-weight:600; color:var(--tx); }}
    .mc-n {{ font-size:0.68rem; font-weight:600; padding:2px 8px; border-radius:12px; font-family:'JetBrains Mono',monospace; }}
    .mc-o {{ font-size:0.74rem; font-weight:500; padding:3px 8px; border-radius:4px; margin-bottom:4px; display:inline-block; }}
    .mc-ob {{ font-size:0.74rem; color:var(--tx2); line-height:1.4; }}

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {{ gap:0; border-bottom:1px solid var(--border); background:transparent; }}
    .stTabs [data-baseweb="tab"] {{
        border-radius:0; padding:8px 16px; font-weight:500; font-size:0.82rem;
        color: var(--tx2) !important; border-bottom:2px solid transparent;
        background:transparent !important; transition:all 0.15s ease;
    }}
    .stTabs [data-baseweb="tab"]:hover {{ color:var(--tx) !important; background:var(--hover) !important; }}
    .stTabs [aria-selected="true"] {{ color:var(--acc) !important; border-bottom-color:var(--acc) !important; font-weight:600; }}

    /* ===== INPUTS ===== */
    .stSelectbox > div > div, .stMultiSelect > div > div, .stTextInput > div > div {{
        border-color: var(--border) !important; border-radius:6px !important; background:var(--card) !important;
        font-size: 0.84rem !important;
    }}
    .stSelectbox > div > div:focus-within, .stTextInput > div > div:focus-within {{
        border-color:var(--acc) !important; box-shadow:0 0 0 1px var(--acc) !important;
    }}

    /* ===== BUTTONS ===== */
    .stDownloadButton > button {{
        background:var(--card) !important; color:var(--acc) !important;
        border:1px solid var(--border) !important; border-radius:6px !important;
        font-weight:500 !important; font-size:0.8rem !important; padding:5px 14px !important;
        transition:all 0.15s ease !important;
    }}
    .stDownloadButton > button:hover {{ border-color:var(--acc) !important; background:var(--acc-bg) !important; }}
    .stButton > button {{
        background:var(--acc) !important; color:#fff !important;
        border:none !important; border-radius:6px !important;
        font-weight:600 !important; font-size:0.8rem !important; padding:7px 18px !important;
    }}
    .stButton > button:hover {{ background:var(--acc-h) !important; }}

    /* ===== DATAFRAMES ===== */
    .stDataFrame {{ border-radius:8px; overflow:hidden; }}
    .stDataFrame [data-testid="stDataFrameResizable"] {{ border:1px solid var(--border) !important; border-radius:8px; }}

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {{
        font-size:0.82rem !important; font-weight:500 !important; color:var(--tx) !important;
        background:transparent !important; border:none !important; padding:6px 0 !important;
    }}

    /* ===== FOOTER ===== */
    .ft {{
        display:flex; justify-content:space-between; padding:16px 0 10px;
        border-top:1px solid var(--border); margin-top:28px; font-size:0.72rem; color:var(--tx3);
    }}

    ::-webkit-scrollbar {{ width:4px; }}
    ::-webkit-scrollbar-track {{ background:var(--bg2); }}
    ::-webkit-scrollbar-thumb {{ background:var(--border); border-radius:2px; }}
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
        '<div class="mc"><div class="mc-h">'
        '<div class="mc-c">{code} {name}</div>'
        '<span class="mc-n" style="background:{c}18;color:{c};">{count:,}</span>'
        '</div>'
        '<span class="mc-o" style="background:{c}12;color:{c};">{obj}</span>'
        '<div class="mc-ob">{obs}</div></div>'
    ).format(code=code, name=name, count=count, obj=objetivo, obs=obs, c=color)

def segment_card(tag, title, desc, badge=""):
    b = '<div class="cd-b">{}</div>'.format(badge) if badge else ""
    return '<div class="cd"><div class="cd-tag">{}</div><div class="cd-t">{}</div><div class="cd-d">{}</div>{}</div>'.format(tag, title, desc, b)

def sidebar_line():
    return '<hr class="sb-line">'

def footer_html():
    from datetime import datetime
    return '<div class="ft"><span>Mirai Telecom</span><span>{}</span></div>'.format(
        datetime.now().strftime("%d/%m/%Y %H:%M"))