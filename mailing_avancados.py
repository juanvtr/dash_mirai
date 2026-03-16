# -*- coding: utf-8 -*-
"""
Mirai Insights - Gerador Avancado de Mailings.

Mailings por produto + propensao, cruzando PRIMEIRA_OFERTA, SEGUNDA_OFERTA,
TERCEIRA_OFERTA com colunas especificas (VVN, VIVO_TECH, DIGITAL_1/2/3, AVANCADOS)
e niveis de propensao.

Uso no app.py:
    from mailing_avancado import gerar_mailings_produto, get_filtros_disponiveis, gerar_mailing_custom_avancado
"""

import pandas as pd
import re
from datetime import datetime


# =============================================================
# PARSING DE PROPENSAO E PRODUTO
# =============================================================

def _extrair_propensao_digital(texto):
    """Extrai propensao de campos DIGITAL_1/2/3."""
    if pd.isna(texto) or not str(texto).strip():
        return ""
    m = re.search(r"(Muito Alta|Alta|Média|Media|Baixa|Muito Baixa)", str(texto), re.IGNORECASE)
    return m.group(1).title().replace("Media", "Média") if m else ""


def _extrair_produto_digital(texto):
    """Extrai nome do produto de campos DIGITAL_1/2/3."""
    if pd.isna(texto) or not str(texto).strip():
        return ""
    m = re.search(r"Aquisição de (.+?)(?:\s*-\s*|\s*com\s)", str(texto))
    if m:
        return m.group(1).strip()
    # fallback: pegar tudo depois de "Aquisição de"
    m2 = re.search(r"Aquisição de (.+?)$", str(texto))
    return m2.group(1).strip()[:50] if m2 else str(texto)[:50]


def _extrair_propensao_movel(texto):
    """Extrai propensao de PROPENSAO_MOVEL_AVANCADA (formato: 'Alto|Movel /')."""
    if pd.isna(texto) or not str(texto).strip():
        return ""
    t = str(texto).lower()
    if "muito alto" in t: return "Muito Alta"
    if "alto" in t: return "Alta"
    if "medio" in t or "médio" in t: return "Média"
    if "muito baixo" in t: return "Muito Baixa"
    if "baixo" in t: return "Baixa"
    return ""


def _extrair_potencial_vtech(texto):
    """Extrai potencial de VIVO_TECH."""
    if pd.isna(texto) or not str(texto).strip():
        return ""
    t = str(texto).lower()
    if "alto" in t: return "Alta"
    if "médio" in t or "medio" in t: return "Média"
    if "baixo" in t: return "Baixa"
    return "Sim"  # tem texto mas sem nivel explicito


def enriquecer_df_com_propensoes(df):
    """
    Adiciona colunas derivadas de propensao e produto ao DataFrame.
    Chamar DEPOIS do processar_mapa_parque e cruzar_mapa_com_movel.
    """
    df = df.copy()

    # -- VVN --
    df["TEM_PROP_VVN"] = df["VVN"].notna() & (df["VVN"].astype(str).str.strip() != "")
    df["TIPO_VVN"] = df["VVN"].apply(lambda x: "MIGRACAO" if "Migração" in str(x) else "AQUISICAO" if pd.notna(x) and str(x).strip() else "")

    # -- AVANCADOS --
    df["TEM_PROP_AVANCADOS"] = df["AVANCADOS"].notna() & (df["AVANCADOS"].astype(str).str.strip() != "")
    df["TIPO_AVANCADOS"] = df["AVANCADOS"].apply(
        lambda x: "RENOVACAO" if "Renovação" in str(x) else "AQUISICAO" if pd.notna(x) and str(x).strip() else "")

    # -- VIVO TECH --
    df["TEM_PROP_VTECH"] = df["VIVO_TECH"].notna() & (df["VIVO_TECH"].astype(str).str.strip() != "") if "VIVO_TECH" in df.columns else False
    df["PROP_VTECH"] = df["VIVO_TECH"].apply(_extrair_potencial_vtech) if "VIVO_TECH" in df.columns else ""

    # -- PROPENSAO MOVEL --
    df["PROP_MOVEL"] = df["PROPENSAO_MOVEL_AVANCADA"].apply(_extrair_propensao_movel) if "PROPENSAO_MOVEL_AVANCADA" in df.columns else ""

    # -- DIGITAL 1 (Microsoft 365, Google Workspace, Presenca Digital) --
    if "DIGITAL_1" in df.columns:
        df["DIGITAL_1_PRODUTO"] = df["DIGITAL_1"].apply(_extrair_produto_digital)
        df["DIGITAL_1_PROP"] = df["DIGITAL_1"].apply(_extrair_propensao_digital)
        df["TEM_PROP_M365"] = df["DIGITAL_1_PRODUTO"].str.contains("Microsoft 365", case=False, na=False)
        df["TEM_PROP_GOOGLE"] = df["DIGITAL_1_PRODUTO"].str.contains("Google Workspace", case=False, na=False)
        df["TEM_PROP_PRESENCA"] = df["DIGITAL_1_PRODUTO"].str.contains("Presença Digital", case=False, na=False)
    else:
        df["DIGITAL_1_PRODUTO"] = ""
        df["DIGITAL_1_PROP"] = ""
        df["TEM_PROP_M365"] = False
        df["TEM_PROP_GOOGLE"] = False
        df["TEM_PROP_PRESENCA"] = False

    # -- DIGITAL 2 (Gestao Equipes, Frota, Wifi Pro) --
    if "DIGITAL_2" in df.columns:
        df["DIGITAL_2_PRODUTO"] = df["DIGITAL_2"].apply(_extrair_produto_digital)
        df["DIGITAL_2_PROP"] = df["DIGITAL_2"].apply(_extrair_propensao_digital)
        df["TEM_PROP_GESTAO_EQUIPES"] = df["DIGITAL_2_PRODUTO"].str.contains("Gestão de Equipes", case=False, na=False)
        df["TEM_PROP_FROTA"] = df["DIGITAL_2_PRODUTO"].str.contains("Frota", case=False, na=False)
        df["TEM_PROP_WIFI"] = df["DIGITAL_2_PRODUTO"].str.contains("Wifi Pro", case=False, na=False)
    else:
        df["DIGITAL_2_PRODUTO"] = ""
        df["DIGITAL_2_PROP"] = ""
        df["TEM_PROP_GESTAO_EQUIPES"] = False
        df["TEM_PROP_FROTA"] = False
        df["TEM_PROP_WIFI"] = False

    # -- DIGITAL 3 (Antivirus, Gestao Dispositivo) --
    if "DIGITAL_3" in df.columns:
        df["DIGITAL_3_PRODUTO"] = df["DIGITAL_3"].apply(_extrair_produto_digital)
        df["DIGITAL_3_PROP"] = df["DIGITAL_3"].apply(_extrair_propensao_digital)
        df["TEM_PROP_ANTIVIRUS"] = df["DIGITAL_3_PRODUTO"].str.contains("Antivírus", case=False, na=False)
        df["TEM_PROP_MDM"] = df["DIGITAL_3_PRODUTO"].str.contains("Gestão de Dispositivo", case=False, na=False)
    else:
        df["DIGITAL_3_PRODUTO"] = ""
        df["DIGITAL_3_PROP"] = ""
        df["TEM_PROP_ANTIVIRUS"] = False
        df["TEM_PROP_MDM"] = False

    # -- OFERTAS (1a, 2a, 3a) --
    for col in ["PRIMEIRA_OFERTA", "SEGUNDA_OFERTA", "TERCEIRA_OFERTA"]:
        if col not in df.columns:
            df[col] = ""

    # Flag: tem alguma oferta de determinado tipo
    all_ofertas = (df["PRIMEIRA_OFERTA"].fillna("") + " | " +
                   df["SEGUNDA_OFERTA"].fillna("") + " | " +
                   df["TERCEIRA_OFERTA"].fillna("")).str.upper()
    df["OFERTA_TEM_VVN"] = all_ofertas.str.contains("VVN", na=False)
    df["OFERTA_TEM_AVANCADOS"] = all_ofertas.str.contains("AVANÇADOS", na=False)
    df["OFERTA_TEM_DIGITAL"] = all_ofertas.str.contains("DIGITAL", na=False)
    df["OFERTA_TEM_MOVEL"] = all_ofertas.str.contains("MÓVEL", na=False)
    df["OFERTA_TEM_BL"] = all_ofertas.str.contains("BANDA LARGA", na=False)
    df["OFERTA_TEM_BLINDAGEM"] = all_ofertas.str.contains("BLINDAGEM", na=False)

    return df


# =============================================================
# CATALOGO DE MAILINGS POR PRODUTO
# =============================================================

def gerar_mailings_produto(df):
    """
    Gera mailings especificos por produto e propensao.
    Retorna OrderedDict com mailings prontos.
    """
    from collections import OrderedDict
    m = OrderedDict()

    # -- VVN --
    s = df[df["TEM_PROP_VVN"]]
    if len(s) > 0:
        m["P1_VVN_AQUISICAO"] = (s[s["TIPO_VVN"] == "AQUISICAO"], "VVN - AQUISIÇÃO",
            "Clientes com propensao a adquirir Vivo Voz Negocio")
        m["P2_VVN_MIGRACAO"] = (s[s["TIPO_VVN"] == "MIGRACAO"], "VVN - MIGRAÇÃO METÁLICA",
            "Clientes com voz metalica aptos a migrar pra VVN")

    # -- AVANCADOS + VVN (combo) --
    s = df[(df["TEM_PROP_AVANCADOS"]) & (df["TEM_PROP_VVN"])]
    if len(s) > 0:
        m["P3_AVANCADOS_VVN"] = (s, "AVANÇADOS + VVN",
            "Clientes com propensao a internet dedicada E VVN")

    # -- AVANCADOS SOLO --
    s = df[(df["TEM_PROP_AVANCADOS"]) & (~df["TEM_PROP_VVN"])]
    if len(s) > 0:
        m["P4_AVANCADOS"] = (s, "AVANÇADOS (Internet Dedicada)",
            "Clientes com propensao a dados avancados sem VVN")

    # -- MICROSOFT 365 --
    for prop, label in [("Alta", "ALTA"), ("Média", "MEDIA"), ("Baixa", "BAIXA")]:
        s = df[(df["TEM_PROP_M365"]) & (df["DIGITAL_1_PROP"] == prop)]
        if len(s) > 0:
            m["P5_M365_{}".format(label)] = (s, "MICROSOFT 365 - Propensão {}".format(prop),
                "Clientes com propensao {} a aquisicao de Microsoft 365".format(prop.lower()))

    # -- GOOGLE WORKSPACE --
    for prop, label in [("Alta", "ALTA"), ("Média", "MEDIA"), ("Baixa", "BAIXA")]:
        s = df[(df["TEM_PROP_GOOGLE"]) & (df["DIGITAL_1_PROP"] == prop)]
        if len(s) > 0:
            m["P6_GOOGLE_{}".format(label)] = (s, "GOOGLE WORKSPACE - Propensão {}".format(prop),
                "Clientes com propensao {} a Google Workspace".format(prop.lower()))

    # -- M365 OU GOOGLE (ambos) --
    s = df[(df["TEM_PROP_M365"]) | (df["TEM_PROP_GOOGLE"])]
    if len(s) > 0:
        m["P7_DIGITAL_M365_GOOGLE"] = (s, "DIGITAL - M365 ou Google",
            "Todos os clientes com propensao a M365 ou Google Workspace")

    # -- PRESENCA DIGITAL --
    s = df[df["TEM_PROP_PRESENCA"]]
    if len(s) > 0:
        m["P8_PRESENCA_DIGITAL"] = (s, "PRESENÇA DIGITAL",
            "Clientes com propensao a Vivo Presenca Digital")

    # -- VIVO TECH --
    s = df[df["TEM_PROP_VTECH"]]
    if len(s) > 0:
        m["P9_VIVO_TECH"] = (s, "VIVO TECH (Maquininhas)",
            "Clientes com potencial pra maquininhas Vivo Tech")

    # -- GESTAO EQUIPES --
    for prop, label in [("Alta", "ALTA"), ("Média", "MEDIA"), ("Baixa", "BAIXA")]:
        s = df[(df["TEM_PROP_GESTAO_EQUIPES"]) & (df["DIGITAL_2_PROP"] == prop)]
        if len(s) > 0:
            m["P10_GESTAO_EQ_{}".format(label)] = (s, "GESTÃO EQUIPES - {}".format(prop),
                "Propensao {} a Gestao de Equipes".format(prop.lower()))

    # -- FROTA INTELIGENTE --
    s = df[df["TEM_PROP_FROTA"]]
    if len(s) > 0:
        m["P11_FROTA"] = (s, "VIVO FROTA INTELIGENTE",
            "Clientes com propensao a Frota Inteligente")

    # -- WIFI PRO --
    s = df[df["TEM_PROP_WIFI"]]
    if len(s) > 0:
        m["P12_WIFI_PRO"] = (s, "WIFI PRO",
            "Clientes com propensao a Wifi Pro")

    # -- ANTIVIRUS --
    for prop, label in [("Alta", "ALTA"), ("Média", "MEDIA")]:
        s = df[(df["TEM_PROP_ANTIVIRUS"]) & (df["DIGITAL_3_PROP"] == prop)]
        if len(s) > 0:
            m["P13_ANTIVIRUS_{}".format(label)] = (s, "ANTIVÍRUS - {}".format(prop),
                "Propensao {} a antivirus".format(prop.lower()))

    # -- GESTAO DISPOSITIVO (MDM) --
    for prop, label in [("Alta", "ALTA"), ("Média", "MEDIA"), ("Baixa", "BAIXA")]:
        s = df[(df["TEM_PROP_MDM"]) & (df["DIGITAL_3_PROP"] == prop)]
        if len(s) > 0:
            m["P14_MDM_{}".format(label)] = (s, "GESTÃO DISPOSITIVO (MDM) - {}".format(prop),
                "Propensao {} a gestao de dispositivo".format(prop.lower()))

    # -- MOVEL POR PROPENSAO --
    for prop, label in [("Muito Alta", "MUITO_ALTA"), ("Alta", "ALTA"), ("Média", "MEDIA")]:
        s = df[df["PROP_MOVEL"] == prop]
        if len(s) > 0:
            m["P15_MOVEL_{}".format(label)] = (s, "MÓVEL - Propensão {}".format(prop),
                "Propensao {} a aquisicao movel avancada".format(prop.lower()))

    return m


# =============================================================
# FILTROS DISPONIVEIS (pra UI)
# =============================================================

def get_filtros_disponiveis(df):
    """Retorna dict com opcoes de filtro pra UI do mailing customizado."""
    filtros = {}

    # Produtos
    produtos = []
    if df["TEM_PROP_VVN"].any(): produtos.append("VVN")
    if df["TEM_PROP_AVANCADOS"].any(): produtos.append("Avançados / Internet Dedicada")
    if df["TEM_PROP_M365"].any(): produtos.append("Microsoft 365")
    if df["TEM_PROP_GOOGLE"].any(): produtos.append("Google Workspace")
    if df["TEM_PROP_PRESENCA"].any(): produtos.append("Presença Digital")
    if df["TEM_PROP_VTECH"].any(): produtos.append("Vivo Tech")
    if df["TEM_PROP_GESTAO_EQUIPES"].any(): produtos.append("Gestão de Equipes")
    if df["TEM_PROP_FROTA"].any(): produtos.append("Frota Inteligente")
    if df["TEM_PROP_WIFI"].any(): produtos.append("Wifi Pro")
    if df["TEM_PROP_ANTIVIRUS"].any(): produtos.append("Antivírus")
    if df["TEM_PROP_MDM"].any(): produtos.append("Gestão de Dispositivo (MDM)")
    filtros["produtos"] = produtos

    # Propensoes
    filtros["propensoes"] = ["Muito Alta", "Alta", "Média", "Baixa", "Muito Baixa"]

    # Ofertas
    filtros["ofertas"] = [
        "AQUISIÇÃO MÓVEL", "BLINDAGEM MÓVEL", "AQUISIÇÃO DIGITAL",
        "AQUISIÇÃO AVANÇADOS E VVN", "AQUISIÇÃO BANDA LARGA",
        "AQUISIÇÃO VOZ BÁSICA OU VVN", "BLINDAGEM FIXA BÁSICA", "RENOVAÇÃO DIGITAL",
    ]

    # Trilhas
    filtros["trilhas"] = ["TRILHA MÓVEL", "TRILHA DIGITAL", "TRILHA AVANÇADOS", "TRILHA FIXA BÁSICA"]

    # Segmentos
    if "SEGMENTO" in df.columns:
        filtros["segmentos"] = sorted(df["SEGMENTO"].dropna().unique().tolist())

    # Semaforo
    if "SEMAFORO" in df.columns:
        filtros["semaforos"] = sorted(df["SEMAFORO"].dropna().unique().tolist())

    return filtros


# =============================================================
# GERADOR CUSTOMIZADO AVANCADO
# =============================================================

def gerar_mailing_custom_avancado(df, filtros_aplicados):
    """
    Gera mailing customizado com base nos filtros selecionados pelo usuario.
    
    filtros_aplicados: dict com chaves opcionais:
        - produtos: list de produtos selecionados
        - propensao_min: str (Alta, Media, Baixa)
        - oferta_contem: list de ofertas
        - trilha: str
        - segmento: str
        - semaforo: str
        - apenas_mancha: bool
        - apenas_big_deal: bool
        - apenas_nao_fidelizado: bool
        - m_min: int
        - m_max: int
    """
    result = df.copy()

    # -- Filtro por PRODUTO --
    produtos = filtros_aplicados.get("produtos", [])
    if produtos:
        mask = pd.Series(False, index=result.index)
        produto_map = {
            "VVN": "TEM_PROP_VVN",
            "Avançados / Internet Dedicada": "TEM_PROP_AVANCADOS",
            "Microsoft 365": "TEM_PROP_M365",
            "Google Workspace": "TEM_PROP_GOOGLE",
            "Presença Digital": "TEM_PROP_PRESENCA",
            "Vivo Tech": "TEM_PROP_VTECH",
            "Gestão de Equipes": "TEM_PROP_GESTAO_EQUIPES",
            "Frota Inteligente": "TEM_PROP_FROTA",
            "Wifi Pro": "TEM_PROP_WIFI",
            "Antivírus": "TEM_PROP_ANTIVIRUS",
            "Gestão de Dispositivo (MDM)": "TEM_PROP_MDM",
        }
        for p in produtos:
            col = produto_map.get(p)
            if col and col in result.columns:
                mask = mask | result[col]
        result = result[mask]

    # -- Filtro por PROPENSAO MINIMA --
    prop_min = filtros_aplicados.get("propensao_min", "")
    if prop_min:
        prop_order = {"Muito Alta": 5, "Alta": 4, "Média": 3, "Baixa": 2, "Muito Baixa": 1}
        min_score = prop_order.get(prop_min, 0)
        if min_score > 0:
            # Checa propensao em todas as colunas
            def _max_prop(row):
                props = []
                for col in ["DIGITAL_1_PROP", "DIGITAL_2_PROP", "DIGITAL_3_PROP", "PROP_MOVEL"]:
                    if col in row.index and row[col]:
                        props.append(prop_order.get(row[col], 0))
                # VIVO_TECH
                if row.get("PROP_VTECH"):
                    props.append(prop_order.get(row["PROP_VTECH"], 0))
                return max(props) if props else 0
            result = result[result.apply(_max_prop, axis=1) >= min_score]

    # -- Filtro por OFERTA --
    ofertas = filtros_aplicados.get("oferta_contem", [])
    if ofertas:
        mask = pd.Series(False, index=result.index)
        for of in ofertas:
            for col in ["PRIMEIRA_OFERTA", "SEGUNDA_OFERTA", "TERCEIRA_OFERTA"]:
                if col in result.columns:
                    mask = mask | result[col].astype(str).str.upper().str.contains(of.upper(), na=False)
        result = result[mask]

    # -- Filtro por TRILHA --
    trilha = filtros_aplicados.get("trilha", "")
    if trilha and "TRILHA" in result.columns:
        result = result[result["TRILHA"].astype(str).str.upper().str.contains(trilha.upper(), na=False)]

    # -- Filtro por SEGMENTO --
    seg = filtros_aplicados.get("segmento", "")
    if seg and seg != "Todos" and "SEGMENTO" in result.columns:
        result = result[result["SEGMENTO"] == seg]

    # -- Filtro por SEMAFORO --
    sem = filtros_aplicados.get("semaforo", "")
    if sem and sem != "Todos" and "SEMAFORO" in result.columns:
        result = result[result["SEMAFORO"] == sem]

    # -- Apenas mancha FTTH --
    if filtros_aplicados.get("apenas_mancha") and "NA_MANCHA" in result.columns:
        result = result[result["NA_MANCHA"]]

    # -- Apenas Big Deal --
    if filtros_aplicados.get("apenas_big_deal") and "BIG_DEAL" in result.columns:
        result = result[result["BIG_DEAL"]]

    # -- Apenas nao fidelizado --
    if filtros_aplicados.get("apenas_nao_fidelizado") and "FIDELIZADO" in result.columns:
        result = result[~result["FIDELIZADO"]]

    # -- Filtro por M --
    m_min = filtros_aplicados.get("m_min")
    m_max = filtros_aplicados.get("m_max")
    if m_min is not None and "PM_M_MEDIO" in result.columns:
        result = result[result["PM_M_MEDIO"] >= m_min]
    if m_max is not None and "PM_M_MEDIO" in result.columns:
        result = result[result["PM_M_MEDIO"] <= m_max]

    return result