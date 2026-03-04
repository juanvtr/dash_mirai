# -*- coding: utf-8 -*-
"""
Mirai Telecom - Processamento de Dados v3.
ETL: Mapa Parque + Parque Movel + Users (Bitrix).

Referencia: PDF "Raio X Carteira Mirai Telecom - Fev/2026"

Estrutura do Raio X:
  1. MOVEL
     1.1 Movel SEM Fixa M17+        -> RENOVAR + VENDA FTTH
     1.2 Movel COM Fixa M17+        -> RENOVAR
     1.3 Excedente Dados M7-M16     -> UP
     1.4 Credito Aparelho M7-M12    -> UP + APARELHO
     1.5 Movel SEM Mancha M17-M21   -> RENOVAR + VVN + LINHA NOVA
     1.6 Propensao Aquisicao Movel  -> VENDA LINHA NOVA
  2. FIXA
     2.1 Fixa SEM Movel             -> RENOVAR + VENDA FTTH
     2.2 Cliente PEN                -> VENDA FTTH
     2.3 Fixa c/ UP e Propensao Mov -> UP FIXA + LINHA NOVA
     2.4 Renovacao Fixa Basica      -> VENDA FTTH + LINHA NOVA
  3. INDICADORES
     3.1 CAR                        -> RELACIONAMENTO + REG. CAR
     3.2 Nao Biometrado             -> RELACIONAMENTO
     3.3 Cobertura 5G               -> TROCA APARELHO + CHIP 5G
     3.4 Vivo Tech Atual            -> VENDA + RENOVACAO MAQUINAS
     3.5 Vivo Tech Potencial        -> VENDA DE MAQUINAS
     3.6 Digital                    -> DIGITALIZAR + RECEITA
"""

import pandas as pd
import numpy as np
from datetime import datetime
from collections import OrderedDict


# ===================================================================
# UTILIDADES
# ===================================================================

def safe_int(val):
    try:
        return int(float(str(val)))
    except (ValueError, TypeError):
        return 0

def safe_float(val):
    try:
        return float(str(val).replace(",", "."))
    except (ValueError, TypeError):
        return 0.0

def normalize_cnpj(val):
    s = str(val).split(".")[0]
    s = "".join(c for c in s if c.isdigit())
    return s.zfill(14) if len(s) > 0 else None

def _read_csv_auto(file_or_path, sep=";"):
    """Le CSV tentando multiplos encodings. Retorna DataFrame."""
    encodings = ["cp1252", "latin1", "iso-8859-1", "utf-8-sig", "utf-8"]
    for enc in encodings:
        try:
            if hasattr(file_or_path, "seek"):
                file_or_path.seek(0)
            df = pd.read_csv(
                file_or_path, encoding=enc, sep=sep,
                on_bad_lines="skip", low_memory=False
            )
            if len(df.columns) > 3:
                return df
        except (UnicodeDecodeError, Exception):
            continue
    raise ValueError("Nao foi possivel ler o arquivo com nenhum encoding.")


# ===================================================================
# CLASSIFICACOES
# ===================================================================

def calcular_meses_carteira(dt_inclusao):
    """Calcula meses desde DT_INCLUSAO_CARTEIRA ate hoje."""
    if pd.isna(dt_inclusao):
        return 0
    try:
        dt = pd.to_datetime(dt_inclusao, format="%d/%m/%Y", errors="coerce")
        if pd.isna(dt):
            dt = pd.to_datetime(dt_inclusao, errors="coerce")
        if pd.isna(dt):
            return 0
        hoje = datetime.now()
        return max(0, (hoje.year - dt.year) * 12 + (hoje.month - dt.month))
    except Exception:
        return 0

def classificar_semaforo_car(car_movel, car_fixa):
    """PRETO/CINZA: 0 | VERDE: <50 | AMARELO: 50-149 | VERMELHO: >=150."""
    car = safe_float(car_movel) + safe_float(car_fixa)
    if car == 0:     return "PRETO/CINZA"
    elif car < 50:   return "VERDE"
    elif car < 150:  return "AMARELO"
    else:            return "VERMELHO"

def simplificar_posse(txt):
    txt = str(txt)
    mov = "Movel" in txt or "movel" in txt or "Móvel" in txt or "móvel" in txt
    bl = "Banda Larga" in txt
    vb = "Voz" in txt and "Bas" in txt
    if vb and bl and mov: return "VB + BL + Movel"
    if vb and bl:         return "VB + BL"
    if bl and mov:        return "BL + Movel"
    if mov:               return "So Movel"
    if bl:                return "So BL"
    if vb:                return "So Voz"
    return "Outros"

def port_potencial(txt):
    txt = str(txt).lower()
    if "alto potencial" in txt:  return "Alto"
    if "medio potencial" in txt or "médio potencial" in txt: return "Medio"
    if "baixo potencial" in txt: return "Baixo"
    if "renovacao" in txt or "renovação" in txt: return "Renovacao"
    return "Sem info"

def classificar_segmento(row):
    posse = row.get("POSSE_SIMPL", "")
    of1 = str(row.get("OFERTA_1_REC", ""))
    prim = str(row.get("PRIMEIRA_OFERTA", ""))
    if posse == "So Movel":
        return "TOTALIZACAO"
    if posse in ("VB + BL", "So Voz", "So BL"):
        return "MIGRACAO MOVEL"
    if posse in ("VB + BL + Movel", "BL + Movel"):
        if "Blindagem" in prim or "Renovac" in of1: return "BLINDAGEM / RENOVACAO"
        if "Digital" in prim or "Digitalizar" in of1: return "DIGITALIZACAO"
        if "Avancad" in prim or "Avançad" in prim or "Internet Dedicada" in of1 or "VVN" in prim: return "AVANCADOS / VVN"
        return "CROSS-SELL"
    return "OUTROS"

def faixa_m(m):
    """Classifica M (meses) na faixa do Raio X."""
    m = safe_int(m)
    if m <= 6:   return "M0-M6"
    if m <= 12:  return "M7-M12"
    if m <= 16:  return "M13-M16"
    if m <= 21:  return "M17-M21"
    return "M22+"


# ===================================================================
# PROCESSAR MAPA PARQUE (visao cliente / CNPJ)
# ===================================================================

def processar_mapa_parque(file_or_path):
    """
    Le e processa RelatorioInfoB2B_MapaParqueVisaoCliente_*.csv.
    Retorna DataFrame no nivel de CNPJ (1 linha por cliente).
    """
    df = _read_csv_auto(file_or_path, sep=";")

    if "SITUACAO_RECEITA" in df.columns:
        df = df[df["SITUACAO_RECEITA"].str.contains("ATIVA", case=False, na=False)].copy()

    df["MESES_CARTEIRA"] = df["DT_INCLUSAO_CARTEIRA"].apply(calcular_meses_carteira)

    df["QTD_MOVEL"] = df["QT_MOVEL_TERM"].apply(safe_int)
    df["QTD_BL"] = (df["QT_BASICA_BL"].apply(safe_int) +
                    df.get("QT_BL_FTTH", pd.Series(0)).apply(safe_int) +
                    df.get("QT_BL_FTTC", pd.Series(0)).apply(safe_int))
    df["QTD_VTECH"] = df["QT_VIVO_TECH"].apply(safe_int) if "QT_VIVO_TECH" in df.columns else 0
    df["QTD_PEN"] = df["QT_BASICA_TERM_METALICO"].apply(safe_int) if "QT_BASICA_TERM_METALICO" in df.columns else 0
    df["QTD_VVN"] = df["QT_VVN"].apply(safe_int) if "QT_VVN" in df.columns else 0

    df["BIG_DEAL"] = df["FL_BIG_DEAL"].fillna(0).astype(float).astype(int) == 1
    df["MEI"] = df["FLG_MEI"].fillna(0).astype(float).astype(int) == 1
    df["FIDELIZADO"] = df["FLG_FIDELIZADO"].fillna(0).astype(float).astype(int) == 1
    df["BIOMETRADO"] = df["FLG_CLI_BIOMETRADO"].fillna(0).astype(float).astype(int) == 1
    df["TEM_5G"] = df["COBERTURA_5G"].notna() & (df["COBERTURA_5G"].astype(str).str.strip() != "")
    df["TEM_DIGITAL"] = df["DIGITAL_1"].notna() if "DIGITAL_1" in df.columns else False

    df["CAR_MOVEL"] = df["VL_CAR_MOVEL"].apply(safe_float)
    df["CAR_FIXA"] = df["VL_CAR_FIXA"].apply(safe_float)
    df["CAR_TOTAL"] = df["CAR_MOVEL"] + df["CAR_FIXA"]
    df["SEMAFORO"] = df.apply(lambda r: classificar_semaforo_car(r["CAR_MOVEL"], r["CAR_FIXA"]), axis=1)

    df["TEM_MOVEL"] = df["QTD_MOVEL"] > 0
    df["TEM_FIXA"] = df["QTD_BL"] > 0
    df["TEM_PEN"] = df["QTD_PEN"] > 0
    df["NA_MANCHA"] = df["DS_DISPONIBILIDADE"].str.contains("FTTH", na=False, case=False)
    df["TEM_APARELHOS"] = df["APARELHOS"].notna() & (df["APARELHOS"].astype(str).str.strip() != "")

    df["CNPJ_NORM"] = df["NR_CNPJ"].apply(normalize_cnpj)
    df["POSSE_SIMPL"] = df["POSSE"].apply(simplificar_posse)
    df["OFERTA_1_REC"] = df["RECOMENDACAO"].str.extract(r'1. Oferta -> (.+?)(?:\s*///|$)')[0].str.strip()
    df["PORT_POTENCIAL"] = df["REC_MOVEL"].apply(port_potencial)
    df["SEGMENTO"] = df.apply(classificar_segmento, axis=1)
    df["CATEGORIA_M"] = df["MESES_CARTEIRA"].apply(
        lambda m: "M0-M6" if m <= 6 else "M7-M16" if m <= 16 else "M17-M21" if m <= 21 else "M22+"
    )
    df["NOME_CLIENTE"] = df.get("NM_CLIENTE", df.get("NR_CNPJ", "")).astype(str)

    return df


# ===================================================================
# PROCESSAR PARQUE MOVEL (visao linha telefonica)
# ===================================================================

def processar_parque_movel(file_or_path):
    """
    Le e processa RelatorioInfoB2B_ParqueMovel_*.csv.
    Retorna DataFrame no nivel de LINHA (1 linha por numero de telefone).

    Colunas-chave geradas:
      - CNPJ_NORM: CNPJ normalizado (14 digitos)
      - M_INT: coluna M convertida para inteiro
      - FAIXA_M: classificacao M0-M6, M7-M12, M13-M16, M17-M21, M22+
      - FIDELIZADO_MOVEL: True/False a partir do campo FIDELIZADO
      - FAT_MEDIO: faturamento medio 3 meses (float)
      - GB_CONTRATADO / GB_CONSUMIDO: dados de trafego
    """
    df = _read_csv_auto(file_or_path, sep=";")

    df["CNPJ_NORM"] = df["CNPJ_CLIENTE"].astype(str).str.zfill(14)
    df["M_INT"] = pd.to_numeric(df["M"], errors="coerce").fillna(0).astype(int)
    df["FAIXA_M"] = df["M_INT"].apply(faixa_m)
    df["FIDELIZADO_MOVEL"] = df["FIDELIZADO"].str.contains("Fidelizado", case=False, na=False) & ~df["FIDELIZADO"].str.contains("Nao|Não", case=False, na=False)
    df["ELEGIVEL_BLINDAR_FLAG"] = df["ELEGIVEL_BLINDAR"].str.upper().str.strip() == "SIM"
    df["APTO_CONVERGENCIA"] = df["CLIENTE_APTO_CONVERGENCIA"].str.upper().str.strip() == "SIM"

    df["FAT_MEDIO"] = df["FAT_MEDIO_03_MESES"].apply(safe_float)
    df["GB_CONTRATADO"] = df["QTD_GB_CONTRATADO_DADOS"].apply(safe_float)
    df["GB_CONSUMIDO"] = df["QTD_GB_TRAF_DADOS"].apply(safe_float)

    # Excedente de dados: consumiu mais de 80% do contratado
    df["EXCEDENTE_DADOS"] = (df["GB_CONTRATADO"] > 0) & (df["GB_CONSUMIDO"] >= df["GB_CONTRATADO"] * 0.8)

    # M_RECOMENDACAO
    df["M_REC"] = pd.to_numeric(df["M_RECOMENDACAO"], errors="coerce").fillna(0).astype(int)

    return df


def agregar_parque_movel_por_cnpj(df_movel):
    """
    Agrega Parque Movel no nivel de CNPJ para cruzar com Mapa Parque.

    Retorna DataFrame com 1 linha por CNPJ e colunas:
      - PM_QTD_LINHAS: total de linhas moveis
      - PM_QTD_FIDELIZADAS: linhas fidelizadas
      - PM_QTD_NAO_FIDELIZADAS: linhas nao fidelizadas
      - PM_QTD_ELEGIVEL_BLINDAR: linhas elegiveis para blindagem
      - PM_M_MIN / PM_M_MAX / PM_M_MEDIO: menor, maior e media do M
      - PM_FAT_TOTAL: soma do faturamento medio
      - PM_LINHAS_M17_PLUS: linhas com M >= 17
      - PM_LINHAS_M7_M16: linhas com M entre 7 e 16
      - PM_LINHAS_EXCEDENTE: linhas com excedente de dados
      - PM_FAIXA_M_PREDOMINANTE: faixa de M mais frequente
      - PM_SEMAFORO_SERASA_PIOR: pior semaforo Serasa do cliente
    """
    agg = df_movel.groupby("CNPJ_NORM").agg(
        PM_QTD_LINHAS=("NR_TELEFONE", "count"),
        PM_QTD_FIDELIZADAS=("FIDELIZADO_MOVEL", "sum"),
        PM_QTD_ELEGIVEL_BLINDAR=("ELEGIVEL_BLINDAR_FLAG", "sum"),
        PM_QTD_APTO_CONV=("APTO_CONVERGENCIA", "sum"),
        PM_M_MIN=("M_INT", "min"),
        PM_M_MAX=("M_INT", "max"),
        PM_M_MEDIO=("M_INT", "mean"),
        PM_FAT_TOTAL=("FAT_MEDIO", "sum"),
        PM_LINHAS_M17_PLUS=("M_INT", lambda x: (x >= 17).sum()),
        PM_LINHAS_M7_M16=("M_INT", lambda x: ((x >= 7) & (x <= 16)).sum()),
        PM_LINHAS_M7_M12=("M_INT", lambda x: ((x >= 7) & (x <= 12)).sum()),
        PM_LINHAS_EXCEDENTE=("EXCEDENTE_DADOS", "sum"),
    ).reset_index()

    agg["PM_QTD_NAO_FIDELIZADAS"] = agg["PM_QTD_LINHAS"] - agg["PM_QTD_FIDELIZADAS"]
    agg["PM_M_MEDIO"] = agg["PM_M_MEDIO"].round(1)
    agg["PM_PCT_FIDELIZADO"] = (agg["PM_QTD_FIDELIZADAS"] / agg["PM_QTD_LINHAS"] * 100).round(1)

    # Faixa predominante
    faixa_mode = df_movel.groupby("CNPJ_NORM")["FAIXA_M"].agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "M0-M6")
    agg = agg.merge(faixa_mode.rename("PM_FAIXA_M_PREDOMINANTE"), on="CNPJ_NORM", how="left")

    # Pior semaforo Serasa
    serasa_order = {"PRETO": 0, "VERMELHO": 1, "CINZA": 2, "AMARELO": 3, "VERDE": 4}
    def pior_serasa(group):
        vals = group.dropna().unique()
        if len(vals) == 0:
            return "VERDE"
        return min(vals, key=lambda x: serasa_order.get(str(x).upper(), 5))
    serasa_worst = df_movel.groupby("CNPJ_NORM")["SEMAFORO_SERASA"].agg(pior_serasa)
    agg = agg.merge(serasa_worst.rename("PM_SEMAFORO_SERASA_PIOR"), on="CNPJ_NORM", how="left")

    return agg


# ===================================================================
# PROCESSAR USERS (Bitrix)
# ===================================================================

def processar_users(file_or_path):
    """
    Le users.xls (na verdade HTML) do Bitrix.
    Retorna DataFrame com Colaborador, Departamento (time), Email.
    """
    dfs = pd.read_html(file_or_path)
    if not dfs:
        raise ValueError("Nenhuma tabela encontrada no arquivo de usuarios.")
    df = dfs[0].copy()

    # Corrigir encoding mojibake (latin1 -> utf8)
    for c in df.columns.tolist():
        new_c = c
        if isinstance(c, str) and "\xc3" in c.encode("latin1", errors="ignore").decode("utf-8", errors="ignore"):
            try:
                new_c = c.encode("latin1").decode("utf-8")
            except:
                pass
        df = df.rename(columns={c: new_c})

    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].apply(lambda x: _fix_mojibake(x) if isinstance(x, str) else x)

    # Padronizar colunas
    if "Colaborador" in df.columns:
        df = df.rename(columns={"Colaborador": "NOME_VENDEDOR"})
    if "Departamento" in df.columns:
        df = df.rename(columns={"Departamento": "TIME"})
    if "E-mail" in df.columns:
        df = df.rename(columns={"E-mail": "EMAIL"})

    # Extrair gerencia do TIME
    df["GERENCIA"] = df["TIME"].apply(_extrair_gerencia)

    return df

def _fix_mojibake(text):
    """Tenta corrigir texto com encoding mojibake."""
    try:
        return text.encode("latin1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text

def _extrair_gerencia(time_str):
    """Extrai gerencia a partir do nome do time."""
    s = str(time_str)
    if "Adriana" in s: return "Gestao Adriana"
    if "Giovany" in s: return "Gestao Giovany"
    if "Beto" in s:    return "Gerencia Beto"
    if "Jessica" in s or "Jéssica" in s: return "Time Jessica"
    if "Xiscatti" in s: return "Time Xiscatti"
    if "Pedro Tech" in s: return "Time Pedro Tech"
    if "Pedro de Paula" in s: return "Time Pedro de Paula"
    if "Inside" in s:  return "Inside Sales"
    if "Intelig" in s: return "Inteligencia"
    if "Tramit" in s:  return "Tramitacao"
    if "Calister" in s: return "Calister"
    if "RH" in s:      return "RH"
    if "Bitrix" in s:  return "Bitrix/Admin"
    return "Outros"


# ===================================================================
# CRUZAMENTO MAPA PARQUE x PARQUE MOVEL
# ===================================================================

def cruzar_mapa_com_movel(df_mapa, df_movel_agg):
    """
    Cruza Mapa Parque com Parque Movel agregado por CNPJ.
    Adiciona colunas PM_* ao Mapa Parque.
    Atualiza CATEGORIA_M para usar o M real do Parque Movel.
    """
    df = df_mapa.merge(df_movel_agg, on="CNPJ_NORM", how="left")

    # Preencher NaN com zeros para clientes sem movel no Parque Movel
    pm_cols = [c for c in df.columns if c.startswith("PM_")]
    for c in pm_cols:
        if df[c].dtype in ("float64", "int64"):
            df[c] = df[c].fillna(0)

    # Atualizar CATEGORIA_M com M real do Parque Movel (quando disponivel)
    df["CATEGORIA_M_REAL"] = df["PM_FAIXA_M_PREDOMINANTE"].fillna(df["CATEGORIA_M"])
    df["M_REAL_MEDIO"] = df["PM_M_MEDIO"].fillna(0)

    return df


# ===================================================================
# GERACAO DE MAILINGS - CONFORME PDF RAIO X
# ===================================================================

_COLS_CONTATO = [
    "NR_CNPJ", "NOME_CLIENTE", "NM_CONTATO_SFA",
    "EMAIL_CONTATO_PRINCIPAL_SFA", "CELULAR_CONTATO_PRINCIPAL_SFA",
    "TLFN_1", "TLFN_2", "DS_CIDADE", "DS_ENDERECO",
]

_COLS_ANALISE = [
    "POSSE", "SEGMENTO", "CATEGORIA_M", "CATEGORIA_M_REAL", "SEMAFORO",
    "QTD_MOVEL", "QTD_BL", "QTD_VTECH", "QTD_PEN",
    "CAR_TOTAL", "VERTICAL", "CLUSTER",
    "PM_QTD_LINHAS", "PM_M_MEDIO", "PM_FAT_TOTAL", "PM_PCT_FIDELIZADO",
]


def _montar_mailing(df_filtrado, codigo, objetivo, obs_extra=None, info_fonte=None):
    if len(df_filtrado) == 0:
        return pd.DataFrame()
    cols_c = [c for c in _COLS_CONTATO if c in df_filtrado.columns]
    cols_a = [c for c in _COLS_ANALISE if c in df_filtrado.columns]
    mailing = df_filtrado[cols_c + cols_a].copy()
    for flag in ["BIG_DEAL", "MEI", "FIDELIZADO", "NA_MANCHA", "BIOMETRADO"]:
        if flag in df_filtrado.columns:
            col_name = flag if flag != "NA_MANCHA" else "NA_MANCHA_FTTH"
            mailing[col_name] = df_filtrado[flag].map({True: "SIM", False: ""}).values
    mailing.insert(0, "CODIGO_MAILING", codigo)
    mailing["OBJETIVO"] = objetivo
    if obs_extra:
        mailing["OBSERVACAO"] = obs_extra
    # INFO_FONTE: rastreabilidade das fontes e filtros usados
    if info_fonte:
        mailing["INFO_FONTE"] = info_fonte
    else:
        mailing["INFO_FONTE"] = "Mapa Parque + Parque Movel | Codigo: {} | Objetivo: {}".format(codigo, objetivo)
    mailing["GERADO_EM"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    return mailing.reset_index(drop=True)


def gerar_todos_mailings(df):
    """Gera todos os 16 mailings do Raio X. Retorna OrderedDict."""
    m = OrderedDict()

    # -- 1. MOVEL --
    # Usa PM_LINHAS_M17_PLUS quando disponivel para filtro de M17+
    has_pm = "PM_LINHAS_M17_PLUS" in df.columns

    # 1.1 MOVEL SEM FIXA M17+
    if has_pm:
        s = df[(df["TEM_MOVEL"]) & (~df["TEM_FIXA"]) & (df["PM_LINHAS_M17_PLUS"] > 0)]
    else:
        s = df[(df["TEM_MOVEL"]) & (~df["TEM_FIXA"]) & (df["MESES_CARTEIRA"] >= 17)]
    m["1.1_MOVEL_SEM_FIXA_M17"] = _montar_mailing(s, "1.1", "RENOVAR + VENDA FTTH",
        "Clientes: {} | Linhas: {} | Mancha: {} | Big: {}".format(
            len(s), s["QTD_MOVEL"].sum(), s["NA_MANCHA"].sum(), s["BIG_DEAL"].sum()),
        info_fonte="FONTE: Mapa Parque (TEM_MOVEL=True, TEM_FIXA=False) + Parque Movel (PM_LINHAS_M17_PLUS>0) | "
                   "Filtro: cliente tem movel, NAO tem fixa, possui linhas com M>=17 no Parque Movel")

    # 1.2 MOVEL COM FIXA M17+
    if has_pm:
        s = df[(df["TEM_MOVEL"]) & (df["TEM_FIXA"]) & (df["PM_LINHAS_M17_PLUS"] > 0)]
    else:
        s = df[(df["TEM_MOVEL"]) & (df["TEM_FIXA"]) & (df["MESES_CARTEIRA"] >= 17)]
    m["1.2_MOVEL_COM_FIXA_M17"] = _montar_mailing(s, "1.2", "RENOVAR",
        "Clientes: {} | Linhas: {} | Big: {}".format(len(s), s["QTD_MOVEL"].sum(), s["BIG_DEAL"].sum()),
        info_fonte="FONTE: Mapa Parque (TEM_MOVEL=True, TEM_FIXA=True) + Parque Movel (PM_LINHAS_M17_PLUS>0) | "
                   "Filtro: cliente tem movel E fixa, possui linhas com M>=17")

    # 1.3 EXCEDENTE DADOS M7-M16
    if has_pm:
        s = df[(df["TEM_MOVEL"]) & (df["PM_LINHAS_M7_M16"] > 0)]
    else:
        s = df[(df["TEM_MOVEL"]) & (df["MESES_CARTEIRA"] >= 7) & (df["MESES_CARTEIRA"] <= 16)]
    m["1.3_EXCEDENTE_DADOS_M7_M16"] = _montar_mailing(s, "1.3", "UP",
        "Clientes: {} | Linhas: {}".format(len(s), s["QTD_MOVEL"].sum()),
        info_fonte="FONTE: Mapa Parque (TEM_MOVEL=True) + Parque Movel (PM_LINHAS_M7_M16>0) | "
                   "Filtro: cliente com movel e linhas entre M7-M16 (janela de UP)")

    # 1.4 CREDITO APARELHO M7-M12
    if has_pm:
        s = df[(df["TEM_MOVEL"]) & (df["PM_LINHAS_M7_M12"] > 0) & (df["TEM_APARELHOS"])]
    else:
        s = df[(df["TEM_MOVEL"]) & (df["MESES_CARTEIRA"] >= 7) & (df["MESES_CARTEIRA"] <= 12) & (df["TEM_APARELHOS"])]
    m["1.4_CREDITO_APARELHO_M7_M12"] = _montar_mailing(s, "1.4", "UP + APARELHO",
        "Clientes: {} | Linhas: {}".format(len(s), s["QTD_MOVEL"].sum()),
        info_fonte="FONTE: Mapa Parque (TEM_MOVEL=True, TEM_APARELHOS=True) + Parque Movel (PM_LINHAS_M7_M12>0) | "
                   "Filtro: tem movel + aparelhos financiados + linhas M7-M12")

    # 1.5 MOVEL SEM MANCHA M17-M21
    if has_pm:
        s = df[(df["TEM_MOVEL"]) & (~df["NA_MANCHA"]) & (df["PM_M_MEDIO"] >= 17) & (df["PM_M_MEDIO"] <= 21)]
    else:
        s = df[(df["TEM_MOVEL"]) & (~df["NA_MANCHA"]) & (df["MESES_CARTEIRA"] >= 17) & (df["MESES_CARTEIRA"] <= 21)]
    m["1.5_MOVEL_SEM_MANCHA_M17_M21"] = _montar_mailing(s, "1.5", "RENOVAR + VVN + LINHA NOVA",
        "Clientes: {} | Linhas: {}".format(len(s), s["QTD_MOVEL"].sum()),
        info_fonte="FONTE: Mapa Parque (TEM_MOVEL=True, NA_MANCHA=False) + Parque Movel (PM_M_MEDIO entre 17-21) | "
                   "Filtro: movel fora da mancha FTTH, M medio 17-21 (janela renovacao sem fixa disponivel)")

    # 1.6 PROPENSAO AQUISICAO MOVEL
    s = df[df["PORT_POTENCIAL"].isin(["Alto", "Medio"])]
    m["1.6_PROPENSAO_AQUISICAO"] = _montar_mailing(s, "1.6", "VENDA LINHA NOVA",
        "Alto: {} | Medio: {} | Big: {}".format(
            (s["PORT_POTENCIAL"]=="Alto").sum(), (s["PORT_POTENCIAL"]=="Medio").sum(), s["BIG_DEAL"].sum()),
        info_fonte="FONTE: Mapa Parque (PORT_POTENCIAL in Alto,Medio) | "
                   "Filtro: clientes com propensao alta ou media a adquirir novas linhas")

    # -- 2. FIXA --
    s = df[(df["TEM_FIXA"]) & (~df["TEM_MOVEL"])]
    m["2.1_FIXA_SEM_MOVEL"] = _montar_mailing(s, "2.1", "RENOVAR + VENDA FTTH",
        "BLs: {} | Terminal met: {} | MEI: {} | Big: {}".format(
            s["QTD_BL"].sum(), s["QTD_PEN"].sum(), s["MEI"].sum(), s["BIG_DEAL"].sum()),
        info_fonte="FONTE: Mapa Parque (TEM_FIXA=True, TEM_MOVEL=False) | "
                   "Filtro: tem fixa mas NAO tem movel - oportunidade de totalizacao")

    s = df[df["TEM_PEN"]]
    m["2.2_CLIENTE_PEN"] = _montar_mailing(s, "2.2", "VENDA FTTH",
        "PENs: {} | Mancha: {} | Nao fid: {}".format(s["QTD_PEN"].sum(), s["NA_MANCHA"].sum(), (~s["FIDELIZADO"]).sum()),
        info_fonte="FONTE: Mapa Parque (TEM_PEN=True) | "
                   "Filtro: clientes com terminal metalico (linha analogica) - candidatos a migracao FTTH")

    s = df[(df["TEM_FIXA"]) & (~df["TEM_MOVEL"]) & (~df["FIDELIZADO"])]
    m["2.3_FIXA_UP_PROPENSAO"] = _montar_mailing(s, "2.3", "UP FIXA BASICA + LINHA NOVA",
        "BLs: {} | Nao fid: {}".format(s["QTD_BL"].sum(), len(s)),
        info_fonte="FONTE: Mapa Parque (TEM_FIXA=True, TEM_MOVEL=False, FIDELIZADO=False) | "
                   "Filtro: tem fixa, sem movel, NAO fidelizado - janela de UP e venda de linha nova")

    s = df[(df["TEM_FIXA"]) & (df["FIDELIZADO"])]
    m["2.4_RENOVACAO_FIXA"] = _montar_mailing(s, "2.4", "VENDA FTTH + LINHA NOVA",
        "Clientes fidelizados c/ fixa: {}".format(len(s)),
        info_fonte="FONTE: Mapa Parque (TEM_FIXA=True, FIDELIZADO=True) | "
                   "Filtro: tem fixa e fidelizado - renovacao + FTTH + linha nova")

    # -- 3. INDICADORES --
    s = df[df["CAR_TOTAL"] > 0]
    m["3.1_CAR"] = _montar_mailing(s, "3.1", "RELACIONAMENTO + REGULARIZAR CAR",
        "CAR Movel>0: {} | CAR Fixa>0: {} | Big: {}".format(
            (df["CAR_MOVEL"]>0).sum(), (df["CAR_FIXA"]>0).sum(), s["BIG_DEAL"].sum()),
        info_fonte="FONTE: Mapa Parque (CAR_TOTAL>0, somando CAR_MOVEL + CAR_FIXA) | "
                   "Filtro: clientes com Conta a Receber pendente")

    s = df[~df["BIOMETRADO"]]
    m["3.2_NAO_BIOMETRADO"] = _montar_mailing(s, "3.2", "RELACIONAMENTO",
        "MEI: {} | Nao fid: {} | Big: {}".format(s["MEI"].sum(), (~s["FIDELIZADO"]).sum(), s["BIG_DEAL"].sum()),
        info_fonte="FONTE: Mapa Parque (BIOMETRADO=False) | "
                   "Filtro: clientes que NAO fizeram biometria - oportunidade de relacionamento")

    s = df[df["TEM_5G"]]
    m["3.3_COBERTURA_5G"] = _montar_mailing(s, "3.3", "TROCA APARELHO + CHIP 5G",
        "Nao fid: {} | Big: {}".format((~s["FIDELIZADO"]).sum(), s["BIG_DEAL"].sum()),
        info_fonte="FONTE: Mapa Parque (TEM_5G=True, coluna de cobertura 5G) | "
                   "Filtro: clientes em area 5G - oportunidade de troca de aparelho + chip")

    s = df[df["QTD_VTECH"] > 0]
    m["3.4_VIVO_TECH_ATUAL"] = _montar_mailing(s, "3.4", "VENDA + RENOVACAO DE MAQUINAS",
        "Maquinas: {} | Nao fid: {}".format(s["QTD_VTECH"].sum(), (~s["FIDELIZADO"]).sum()),
        info_fonte="FONTE: Mapa Parque (QTD_VTECH>0) | "
                   "Filtro: clientes que JA possuem maquininhas Vivo Tech - renovacao ou venda adicional")

    if "VIVO_TECH" in df.columns:
        s = df[(df["QTD_VTECH"] == 0) & (df["VIVO_TECH"].notna()) & (df["VIVO_TECH"].astype(str).str.strip() != "")]
        m["3.5_VIVO_TECH_POTENCIAL"] = _montar_mailing(s, "3.5", "VENDA DE MAQUINAS",
            "Nao fid: {}".format((~s["FIDELIZADO"]).sum()),
            info_fonte="FONTE: Mapa Parque (QTD_VTECH=0 mas coluna VIVO_TECH preenchida) | "
                       "Filtro: clientes SEM maquininha mas com indicacao de potencial no Mapa")

    if "DIGITAL_1" in df.columns:
        s = df[df["DIGITAL_1"].notna() & (df["DIGITAL_1"].astype(str).str.strip() != "")]
        m["3.6_DIGITAL"] = _montar_mailing(s, "3.6", "DIGITALIZAR PARQUE COM AUMENTO DE RECEITA",
            "MEI: {} | Nao fid: {} | Big: {}".format(s["MEI"].sum(), (~s["FIDELIZADO"]).sum(), s["BIG_DEAL"].sum()),
            info_fonte="FONTE: Mapa Parque (DIGITAL_1 preenchido) | "
                       "Filtro: clientes com produtos digitais registrados - oportunidade de ampliacao")

    return m


def gerar_mailing_customizado(df_filtrado, nome="CUSTOM"):
    return _montar_mailing(df_filtrado, "CUSTOM_{}".format(nome), "DEFINIDO PELO USUARIO")