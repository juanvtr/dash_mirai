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
import re
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
    # Mancha FTTH: usa coluna 'Mancha' (SIM/NAO) ou fallback pra DS_DISPONIBILIDADE
    if "Mancha" in df.columns:
        df["NA_MANCHA"] = df["Mancha"].astype(str).str.upper().str.strip() == "SIM"
    else:
        df["NA_MANCHA"] = df["DS_DISPONIBILIDADE"].str.contains("FTTH", na=False, case=False)
    
    # Tem metalico (pra migração tec fixa)
    df["TEM_METALICO"] = df["QT_BASICA_TERM_METALICO"].fillna(0) > 0
    # Tem BL FTTH
    df["TEM_BL_FTTH"] = df["QT_BL_FTTH"].fillna(0) > 0
    # Tem dados avancados
    df["TEM_AVANCADOS"] = df["QT_AVANCADA_DADOS"].fillna(0) > 0
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
        PM_LINHAS_M10_PLUS=("M_INT", lambda x: (x >= 10).sum()),
        PM_LINHAS_M10_M16=("M_INT", lambda x: ((x >= 10) & (x <= 16)).sum()),
        PM_LINHAS_M22_PLUS=("M_INT", lambda x: (x >= 22).sum()),
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


# ===================================================================
# 4. DEALS BITRIX
# ===================================================================

def processar_deals(file_or_path):
    """
    Processa export de Deals do Bitrix.
    CNPJ vem corrompido (notacao cientifica), entao usa Razao Social pra match.
    """
    df = pd.read_csv(file_or_path, sep=";", encoding="utf-8", low_memory=False,
                     on_bad_lines="skip", dtype=str)

    # Normalizar CNPJ - tentar recuperar da notacao cientifica
    def _norm_cnpj(x):
        if pd.isna(x) or str(x).strip() == "":
            return ""
        s = str(x).strip()
        if "E+" in s or "e+" in s:
            try:
                s = s.replace(",", ".")
                s = "{:.0f}".format(float(s))
            except:
                pass
        s = re.sub(r"[^0-9]", "", s)
        return s.zfill(14) if 0 < len(s) <= 14 else s

    cnpj_col = "CNPJ" if "CNPJ" in df.columns else None
    if cnpj_col:
        df["CNPJ_NORM"] = df[cnpj_col].apply(_norm_cnpj)
    else:
        df["CNPJ_NORM"] = ""

    # Nome normalizado pra match por nome (fallback quando CNPJ corrompido)
    if "Razão Social" in df.columns:
        df["NOME_NORM"] = df["Razão Social"].astype(str).str.upper().str.strip()
        # Limpar prefixos numericos (tipo "32172442 NOME DA EMPRESA")
        df["NOME_NORM"] = df["NOME_NORM"].str.replace(r"^\d+\s+", "", regex=True)
    elif "Empresa" in df.columns:
        df["NOME_NORM"] = df["Empresa"].astype(str).str.upper().str.strip()
        df["NOME_NORM"] = df["NOME_NORM"].str.replace(r"^\d+\s+", "", regex=True)
    else:
        df["NOME_NORM"] = ""

    # Deal aberto
    if "Fechado" in df.columns:
        df["DEAL_ABERTO"] = df["Fechado"].astype(str).str.strip().str.lower() != "sim"
    else:
        df["DEAL_ABERTO"] = True

    cols_keep = ["CNPJ_NORM", "NOME_NORM", "DEAL_ABERTO", "Pipeline", "Fase",
                 "Responsável", "Nome do negócio", "Razão Social", "ID"]
    avail = [c for c in cols_keep if c in df.columns]
    return df[avail].copy()


def get_cnpjs_em_tratativa(df_deals):
    """Retorna (set_cnpjs, set_nomes) de deals abertos pra match duplo."""
    abertos = df_deals[df_deals["DEAL_ABERTO"]]
    cnpjs = set(abertos["CNPJ_NORM"].unique()) - {"", "00000000000000"}
    nomes = set(abertos["NOME_NORM"].unique()) - {"", "NAN"} if "NOME_NORM" in abertos.columns else set()
    return cnpjs, nomes


def filtrar_mailing_sem_deals(mailing_df, cnpjs_tratativa, nomes_tratativa=None, cnpj_col="CNPJ", nome_col="NOME"):
    """
    Remove do mailing clientes que ja tem deal aberto.
    Match duplo: por CNPJ e por nome (fallback quando CNPJ corrompido).
    """
    if (not cnpjs_tratativa and not nomes_tratativa):
        return mailing_df, 0

    mailing_df = mailing_df.copy()

    # Match por CNPJ
    mask_cnpj = pd.Series(True, index=mailing_df.index)
    if cnpjs_tratativa and cnpj_col in mailing_df.columns:
        def _norm(x):
            s = re.sub(r"[^0-9]", "", str(x))
            return s.zfill(14) if 0 < len(s) <= 14 else s
        mailing_df["_cnpj"] = mailing_df[cnpj_col].apply(_norm)
        mask_cnpj = ~mailing_df["_cnpj"].isin(cnpjs_tratativa)

    # Match por nome
    mask_nome = pd.Series(True, index=mailing_df.index)
    if nomes_tratativa and nome_col in mailing_df.columns:
        mailing_df["_nome"] = mailing_df[nome_col].astype(str).str.upper().str.strip()
        mask_nome = ~mailing_df["_nome"].isin(nomes_tratativa)

    # Combinar: remover se match por CNPJ OU por nome
    mask_final = mask_cnpj & mask_nome
    removidos = (~mask_final).sum()

    cols_drop = [c for c in ["_cnpj", "_nome"] if c in mailing_df.columns]
    result = mailing_df[mask_final].drop(columns=cols_drop)
    return result, removidos

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

    # Calcular CURVA ABC pelo faturamento (PM_FAT_TOTAL)
    fat = df["PM_FAT_TOTAL"].fillna(0)
    df_sorted = fat.sort_values(ascending=False)
    total_fat = df_sorted.sum()
    if total_fat > 0:
        cumsum = df_sorted.cumsum()
        pct = cumsum / total_fat * 100
        curva_map = {}
        for idx, p in pct.items():
            if p <= 20:
                curva_map[idx] = "A"
            elif p <= 50:
                curva_map[idx] = "B"
            elif p <= 80:
                curva_map[idx] = "C"
            else:
                curva_map[idx] = "D"
        df["CURVA_ABC"] = df.index.map(curva_map).fillna("S/F")
    else:
        df["CURVA_ABC"] = "S/F"
    # Clientes sem faturamento
    df.loc[fat == 0, "CURVA_ABC"] = "S/F"

    return df


# ===================================================================
# GERACAO DE MAILINGS - CONFORME PDF RAIO X
# ===================================================================

_COLS_MAILING = [
    # Identificacao
    "NR_CNPJ", "NOME_CLIENTE", "DS_ATIVIDADE_ECONOMICA",
    # Contato SFA
    "NM_CONTATO_SFA", "CELULAR_CONTATO_PRINCIPAL_SFA",
    "EMAIL_CONTATO_PRINCIPAL_SFA",
    # Telefones extras
    "TLFN_1", "TLFN_2",
    # Localizacao
    "DS_CIDADE", "DS_ENDERECO",
    # Analise comercial
    "SEGMENTO", "POSSE", "VERTICAL", "CURVA_ABC",
    "PROPENSAO_MOVEL_AVANCADA",
    "RECOMENDACAO", "PRIMEIRA_OFERTA", "SEGUNDA_OFERTA", "TERCEIRA_OFERTA",
    "CATEGORIA_M", "CATEGORIA_M_REAL", "SEMAFORO",
    # Quantidades de produtos (todas as QT)
    "QTD_MOVEL", "QTD_BL", "QTD_VTECH", "QTD_PEN",
    "QT_MOVEL_TERM", "QT_MOVEL_PEN", "QT_MOVEL_M2M", "QT_MOVEL_FWT",
    "QT_BASICA_TERM_FIBRA", "QT_BASICA_TERM_METALICO", "QT_BASICA_BL",
    "QT_BL_FTTH", "QT_BL_FTTC", "QT_BASICA_TV", "QT_BASICA_OUTROS",
    "QT_BASICA_LINAS", "QT_AVANCADA_DADOS", "QT_VIVO_TECH", "QT_OFFICE_365", "QT_VVN",
    "CAR_TOTAL",
    # Parque Movel agregado
    "PM_QTD_LINHAS", "PM_M_MEDIO", "PM_FAT_TOTAL", "PM_PCT_FIDELIZADO",
    "PM_LINHAS_M17_PLUS", "PM_LINHAS_M7_M16", "PM_LINHAS_M7_M12",
    "PM_LINHAS_M10_PLUS", "PM_LINHAS_M10_M16", "PM_LINHAS_M22_PLUS",
    "PM_QTD_ELEGIVEL_BLINDAR", "PM_QTD_FIDELIZADAS",
]


def _montar_mailing(df_filtrado, codigo, objetivo, obs_extra=None, info_fonte=None):
    if len(df_filtrado) == 0:
        return pd.DataFrame()

    # Pegar colunas disponiveis
    cols = [c for c in _COLS_MAILING if c in df_filtrado.columns]
    mailing = df_filtrado[cols].copy()

    # Renomear para formato do negocio
    rename_map = {
        "NOME_CLIENTE": "NOME",
        "DS_ATIVIDADE_ECONOMICA": "ATIVIDADE",
        "NR_CNPJ": "CNPJ",
        "NM_CONTATO_SFA": "NOME (SFA)",
        "CELULAR_CONTATO_PRINCIPAL_SFA": "CELULAR",
        "EMAIL_CONTATO_PRINCIPAL_SFA": "EMAIL (SFA)",
        "CURVA_ABC": "CURVA",
    }
    mailing = mailing.rename(columns={k: v for k, v in rename_map.items() if k in mailing.columns})

    # Construir FAT_ATUAL a partir do PM
    if "PM_FAT_TOTAL" in mailing.columns:
        mailing["FAT_ATUAL"] = mailing["PM_FAT_TOTAL"].apply(
            lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(x) else "0,00")
    elif "CAR_TOTAL" in mailing.columns:
        mailing["FAT_ATUAL"] = "N/A"
    else:
        mailing["FAT_ATUAL"] = "N/A"

    # Construir INFO_FONTE detalhado no formato do negocio
    def _build_info(row):
        parts = [codigo]
        cnpj = row.get("CNPJ", "")
        nome = row.get("NOME", "")
        if cnpj:
            parts.append(str(cnpj))
        if nome:
            parts.append(str(nome)[:30])

        # Planta e elegiveis
        planta = row.get("PM_QTD_LINHAS", 0)
        if pd.notna(planta) and planta > 0:
            parts.append("PLANTA: {:.0f}".format(planta))
        elegiveis = row.get("PM_QTD_ELEGIVEL_BLINDAR", 0)
        if pd.notna(elegiveis) and elegiveis > 0:
            parts.append("ELEGIVEIS: {:.0f}".format(elegiveis))

        # Curva ABC
        curva = row.get("CURVA", "")
        if pd.notna(curva) and str(curva).strip() and str(curva) != "S/F":
            parts.append("CURVA: {}".format(curva))

        # FAT e M
        fat = row.get("PM_FAT_TOTAL", 0)
        if pd.notna(fat) and fat > 0:
            parts.append("FAT ATUAL: {:.2f}".format(fat))
        m_medio = row.get("PM_M_MEDIO", 0)
        if pd.notna(m_medio) and m_medio > 0:
            parts.append("M MEDIO: {:.0f}".format(m_medio))

        # Quantidades de produtos (resumo)
        qt_parts = []
        for col_qt, label_qt in [
            ("QT_MOVEL_TERM", "Movel"), ("QT_BASICA_BL", "BL"), ("QT_BL_FTTH", "FTTH"),
            ("QT_BASICA_TERM_METALICO", "PEN"), ("QT_BASICA_TERM_FIBRA", "Fibra"),
            ("QT_AVANCADA_DADOS", "Dados Av."), ("QT_VVN", "VVN"),
            ("QT_VIVO_TECH", "VTech"), ("QT_OFFICE_365", "O365"),
            ("QT_BASICA_TV", "TV"), ("QT_MOVEL_M2M", "M2M"),
        ]:
            v = row.get(col_qt, 0)
            if pd.notna(v):
                try:
                    v = float(v)
                except:
                    v = 0
                if v > 0:
                    qt_parts.append("{}: {:.0f}".format(label_qt, v))
        if qt_parts:
            parts.append("QTD [{}]".format(", ".join(qt_parts)))

        # M17+ e M7-16
        m17 = row.get("PM_LINHAS_M17_PLUS", 0)
        if pd.notna(m17) and m17 > 0:
            parts.append("M17+: {:.0f}".format(m17))
        m7 = row.get("PM_LINHAS_M7_M16", 0)
        if pd.notna(m7) and m7 > 0:
            parts.append("M7-16: {:.0f}".format(m7))

        # Posse e Propensao
        posse = row.get("POSSE", "")
        if pd.notna(posse) and str(posse).strip():
            parts.append("POSSE: {}".format(str(posse).strip()))
        propensao = row.get("PROPENSAO_MOVEL_AVANCADA", "")
        if pd.notna(propensao) and str(propensao).strip():
            parts.append("PROPENSAO: {}".format(str(propensao).strip()))

        # Recomendacao (resumida - primeiros 120 chars)
        rec = row.get("RECOMENDACAO", "")
        if pd.notna(rec) and str(rec).strip():
            parts.append("REC: {}".format(str(rec).strip()[:120]))

        return " | ".join(str(p) for p in parts)

        return " | ".join(str(p) for p in parts)

    # INFO_FONTE com detalhes por linha
    mailing["INFO_FONTE"] = mailing.apply(_build_info, axis=1)

    # Se tem info_fonte global (descricao do filtro), adicionar como prefixo
    if info_fonte:
        mailing["FILTRO_MAILING"] = info_fonte

    # Flags como texto
    for flag in ["BIG_DEAL", "MEI", "FIDELIZADO", "NA_MANCHA", "BIOMETRADO"]:
        if flag in df_filtrado.columns:
            col_name = flag if flag != "NA_MANCHA" else "NA_MANCHA_FTTH"
            mailing[col_name] = df_filtrado[flag].map({True: "SIM", False: ""}).values

    # Colunas de controle
    mailing.insert(0, "SEGMENTO_MAILING", codigo + " " + objetivo)
    mailing["OBJETIVO"] = objetivo
    if obs_extra:
        mailing["OBSERVACAO"] = obs_extra
    mailing["GERADO_EM"] = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Reordenar para o formato pedido: SEGMENTO | CNPJ | NOME | ATIVIDADE | CURVA | FAT | INFO_FONTE | CONTATO | CELULAR
    col_order = [
        "SEGMENTO_MAILING", "CNPJ", "NOME", "ATIVIDADE", "CURVA", "FAT_ATUAL",
        "INFO_FONTE", "NOME (SFA)", "CELULAR", "EMAIL (SFA)",
    ]
    # Adicionar restante
    remaining = [c for c in mailing.columns if c not in col_order]
    final_order = [c for c in col_order if c in mailing.columns] + remaining
    mailing = mailing[final_order]

    return mailing.reset_index(drop=True)


def gerar_todos_mailings(df):
    """
    Gera mailings baseados nas regras comerciais da Mirai Telecom.
    
    REGRAS:
    - MIG PRE-POS (aumento dados): a partir de M7 (considerar M10 por delay InfoB2B)
    - MIG DADOS MOVEL: aumentar GB na linha movel
    - MIG DADOS FIXA: aumentar GB na internet fixa
    - MIG TEC FIXA: de metalica pra FTTH (so mancha fibra)
    - MIG POS M17+: migracao/renovacao de pos-pago
    - RENOVACAO: somente movel acima de M17
    - RENOVACAO DADOS AVANCADOS: acima de M22
    - Regra internet fixa: NUNCA descer receita
    
    Obs: Nem toda migracao eh UP, mas todo UP eh migracao.
    """
    m = OrderedDict()
    has_pm = "PM_LINHAS_M17_PLUS" in df.columns

    # =============================================
    # 1. MIGRACOES
    # =============================================

    # 1.1 MIG PRE-POS / AUMENTO DADOS M10+ (M7 real, M10 por delay InfoB2B)
    if has_pm:
        s = df[(df["TEM_MOVEL"]) & (df["PM_LINHAS_M10_PLUS"] > 0) & (df["PM_LINHAS_M17_PLUS"] == 0)]
    else:
        s = df[(df["TEM_MOVEL"]) & (df["MESES_CARTEIRA"] >= 10) & (df["MESES_CARTEIRA"] < 17)]
    m["1.1_MIG_PRE_POS_M10"] = _montar_mailing(s, "1.1", "MIGRACAO PRE-POS / AUMENTO DADOS",
        "Clientes: {} | Linhas M10+: {}".format(len(s), s.get("PM_LINHAS_M10_PLUS", pd.Series([0])).sum()),
        info_fonte="FONTE: PM (PM_LINHAS_M10_PLUS>0, PM_LINHAS_M17_PLUS=0) | "
                   "Filtro: movel com linhas M10+ que NAO sao M17+ (janela de migracao/UP, delay InfoB2B considerado)")

    # 1.2 MIG DADOS MOVEL - AUMENTAR GB (M7-M16 com excedente ou planos baixos)
    if has_pm:
        s = df[(df["TEM_MOVEL"]) & (df["PM_LINHAS_M7_M16"] > 0)]
    else:
        s = df[(df["TEM_MOVEL"]) & (df["MESES_CARTEIRA"] >= 7) & (df["MESES_CARTEIRA"] <= 16)]
    m["1.2_MIG_DADOS_MOVEL_GB"] = _montar_mailing(s, "1.2", "MIGRACAO DADOS MOVEL - AUMENTAR GB",
        "Clientes: {} | Linhas M7-M16: {}".format(len(s), s["PM_LINHAS_M7_M16"].sum() if has_pm else len(s)),
        info_fonte="FONTE: PM (PM_LINHAS_M7_M16>0) | "
                   "Filtro: movel com linhas entre M7-M16 - janela de UP/migracao de dados movel")

    # 1.3 MIG DADOS FIXA - AUMENTAR GB INTERNET (tem BL, nunca descer receita)
    s = df[(df["TEM_FIXA"]) & (df["QTD_BL"] > 0)]
    m["1.3_MIG_DADOS_FIXA_GB"] = _montar_mailing(s, "1.3", "MIGRACAO DADOS FIXA - AUMENTAR GB",
        "Clientes c/ BL: {} | FTTH: {} | FTTC: {}".format(
            len(s), (s["QT_BL_FTTH"].fillna(0)>0).sum(), (s["QT_BL_FTTC"].fillna(0)>0).sum()),
        info_fonte="FONTE: Mapa Parque (TEM_FIXA=True, QTD_BL>0) | "
                   "Filtro: clientes com banda larga - migracao pra plano maior (NUNCA descer receita)")

    # 1.4 MIG TEC FIXA - METALICA PARA FTTH (so mancha fibra)
    s = df[(df["TEM_METALICO"]) & (df["NA_MANCHA"])]
    m["1.4_MIG_TEC_METALICA_FTTH"] = _montar_mailing(s, "1.4", "MIGRACAO TEC FIXA - METALICA P/ FTTH",
        "Clientes metalico+mancha: {} | PENs: {}".format(len(s), s["QTD_PEN"].sum()),
        info_fonte="FONTE: Mapa Parque (TEM_METALICO=True, NA_MANCHA=True) | "
                   "Filtro: cliente com terminal metalico em area com cobertura FTTH - migrar pra fibra")

    # 1.5 MIG POS M17+ (migracao/renovacao pos-pago)
    if has_pm:
        s = df[(df["TEM_MOVEL"]) & (df["PM_LINHAS_M17_PLUS"] > 0)]
    else:
        s = df[(df["TEM_MOVEL"]) & (df["MESES_CARTEIRA"] >= 17)]
    m["1.5_MIG_POS_M17"] = _montar_mailing(s, "1.5", "MIGRACAO POS M17+ / RENOVACAO",
        "Clientes: {} | Linhas M17+: {} | Big: {}".format(
            len(s), s["PM_LINHAS_M17_PLUS"].sum() if has_pm else len(s), s["BIG_DEAL"].sum()),
        info_fonte="FONTE: PM (PM_LINHAS_M17_PLUS>0) | "
                   "Filtro: movel com linhas M17+ - janela de renovacao/migracao pos-pago")

    # =============================================
    # 2. RENOVACOES
    # =============================================

    # 2.1 RENOVACAO MOVEL M17+ (somente movel acima de M17)
    if has_pm:
        s = df[(df["TEM_MOVEL"]) & (~df["TEM_FIXA"]) & (df["PM_LINHAS_M17_PLUS"] > 0)]
    else:
        s = df[(df["TEM_MOVEL"]) & (~df["TEM_FIXA"]) & (df["MESES_CARTEIRA"] >= 17)]
    m["2.1_RENOVACAO_MOVEL_SEM_FIXA"] = _montar_mailing(s, "2.1", "RENOVACAO MOVEL + VENDA FTTH",
        "Clientes: {} | Mancha: {} | Big: {}".format(len(s), s["NA_MANCHA"].sum(), s["BIG_DEAL"].sum()),
        info_fonte="FONTE: PM (M17+, TEM_MOVEL=True, TEM_FIXA=False) | "
                   "Filtro: movel M17+ sem fixa - renovar + oportunidade FTTH")

    # 2.2 RENOVACAO MOVEL COM FIXA M17+
    if has_pm:
        s = df[(df["TEM_MOVEL"]) & (df["TEM_FIXA"]) & (df["PM_LINHAS_M17_PLUS"] > 0)]
    else:
        s = df[(df["TEM_MOVEL"]) & (df["TEM_FIXA"]) & (df["MESES_CARTEIRA"] >= 17)]
    m["2.2_RENOVACAO_MOVEL_COM_FIXA"] = _montar_mailing(s, "2.2", "RENOVACAO MOVEL",
        "Clientes: {} | Big: {}".format(len(s), s["BIG_DEAL"].sum()),
        info_fonte="FONTE: PM (M17+, TEM_MOVEL=True, TEM_FIXA=True) | "
                   "Filtro: movel M17+ com fixa - foco na renovacao")

    # 2.3 RENOVACAO DADOS AVANCADOS M22+
    if has_pm:
        s = df[(df["TEM_AVANCADOS"]) & (df["PM_LINHAS_M22_PLUS"] > 0)]
    else:
        s = df[(df["TEM_AVANCADOS"]) & (df["MESES_CARTEIRA"] >= 22)]
    m["2.3_RENOVACAO_AVANCADOS_M22"] = _montar_mailing(s, "2.3", "RENOVACAO DADOS AVANCADOS",
        "Clientes avancados M22+: {}".format(len(s)),
        info_fonte="FONTE: Mapa Parque (QT_AVANCADA_DADOS>0) + PM (M22+) | "
                   "Filtro: cliente com dados avancados e linhas M22+ - renovacao urgente")

    # 2.4 RENOVACAO FIXA (manter/subir receita)
    s = df[(df["TEM_FIXA"]) & (df["FIDELIZADO"])]
    m["2.4_RENOVACAO_FIXA"] = _montar_mailing(s, "2.4", "RENOVACAO FIXA + VENDA MOVEL",
        "Clientes fid c/ fixa: {} | Sem movel: {}".format(len(s), (~s["TEM_MOVEL"]).sum()),
        info_fonte="FONTE: Mapa Parque (TEM_FIXA=True, FIDELIZADO=True) | "
                   "Filtro: fixa fidelizada - renovacao + oportunidade movel")

    # =============================================
    # 3. CROSS-SELL / TOTALIZACAO
    # =============================================

    # 3.1 MIGRACAO MOVEL (tem fixa, nao tem movel)
    s = df[(df["TEM_FIXA"]) & (~df["TEM_MOVEL"])]
    m["3.1_MIGRACAO_MOVEL"] = _montar_mailing(s, "3.1", "MIGRACAO MOVEL (VENDA DE LINHA)",
        "Clientes fixa s/ movel: {} | Big: {}".format(len(s), s["BIG_DEAL"].sum()),
        info_fonte="FONTE: Mapa Parque (TEM_FIXA=True, TEM_MOVEL=False) | "
                   "Filtro: tem fixa sem movel - oportunidade de venda de linha movel")

    # 3.2 TOTALIZACAO (tem movel, nao tem fixa)
    s = df[(df["TEM_MOVEL"]) & (~df["TEM_FIXA"])]
    m["3.2_TOTALIZACAO"] = _montar_mailing(s, "3.2", "TOTALIZACAO (VENDA FIXA)",
        "Clientes movel s/ fixa: {} | Mancha: {} | Big: {}".format(
            len(s), s["NA_MANCHA"].sum(), s["BIG_DEAL"].sum()),
        info_fonte="FONTE: Mapa Parque (TEM_MOVEL=True, TEM_FIXA=False) | "
                   "Filtro: tem movel sem fixa - oportunidade de totalizacao")

    # 3.3 CLIENTE PEN (terminal metalico - migrar pra FTTH)
    s = df[df["TEM_PEN"]]
    m["3.3_CLIENTE_PEN"] = _montar_mailing(s, "3.3", "MIGRAR PEN PARA FTTH",
        "PENs: {} | Mancha: {}".format(s["QTD_PEN"].sum(), s["NA_MANCHA"].sum()),
        info_fonte="FONTE: Mapa Parque (TEM_PEN=True) | "
                   "Filtro: clientes com terminal metalico - candidatos a FTTH")

    # 3.4 PROPENSAO AQUISICAO
    s = df[df["PORT_POTENCIAL"].isin(["Alto", "Medio"])]
    m["3.4_PROPENSAO_AQUISICAO"] = _montar_mailing(s, "3.4", "VENDA LINHA NOVA",
        "Alto: {} | Medio: {}".format((s["PORT_POTENCIAL"]=="Alto").sum(), (s["PORT_POTENCIAL"]=="Medio").sum()),
        info_fonte="FONTE: Mapa Parque (PORT_POTENCIAL Alto/Medio) | "
                   "Filtro: propensao alta ou media a adquirir novas linhas")

    # =============================================
    # 4. INDICADORES E RELACIONAMENTO
    # =============================================

    # 4.1 CAR
    s = df[df["CAR_TOTAL"] > 0]
    m["4.1_CAR"] = _montar_mailing(s, "4.1", "RELACIONAMENTO + REGULARIZAR CAR",
        "CAR Movel>0: {} | CAR Fixa>0: {}".format((df["CAR_MOVEL"]>0).sum(), (df["CAR_FIXA"]>0).sum()),
        info_fonte="FONTE: Mapa Parque (CAR_TOTAL>0) | Filtro: Conta a Receber pendente")

    # 4.2 NAO BIOMETRADO
    s = df[~df["BIOMETRADO"]]
    m["4.2_NAO_BIOMETRADO"] = _montar_mailing(s, "4.2", "RELACIONAMENTO",
        "Nao biometrados: {}".format(len(s)),
        info_fonte="FONTE: Mapa Parque (BIOMETRADO=False) | Filtro: sem biometria")

    # 4.3 COBERTURA 5G
    s = df[df["TEM_5G"]]
    m["4.3_COBERTURA_5G"] = _montar_mailing(s, "4.3", "TROCA APARELHO + CHIP 5G",
        "Clientes 5G: {}".format(len(s)),
        info_fonte="FONTE: Mapa Parque (TEM_5G=True) | Filtro: area 5G - troca aparelho + chip")

    # 4.4 VIVO TECH
    s = df[df["QTD_VTECH"] > 0]
    m["4.4_VIVO_TECH"] = _montar_mailing(s, "4.4", "RENOVACAO MAQUININHAS",
        "Maquinas: {}".format(s["QTD_VTECH"].sum()),
        info_fonte="FONTE: Mapa Parque (QTD_VTECH>0) | Filtro: clientes com Vivo Tech")

    # 4.5 DIGITAL
    if "DIGITAL_1" in df.columns:
        s = df[df["DIGITAL_1"].notna() & (df["DIGITAL_1"].astype(str).str.strip() != "")]
        m["4.5_DIGITAL"] = _montar_mailing(s, "4.5", "DIGITALIZAR + RECEITA",
            "Clientes digitais: {}".format(len(s)),
            info_fonte="FONTE: Mapa Parque (DIGITAL_1 preenchido) | Filtro: ampliar receita digital")

    return m


def gerar_mailing_customizado(df_filtrado, nome="CUSTOM"):
    return _montar_mailing(df_filtrado, "CUSTOM_{}".format(nome), "DEFINIDO PELO USUARIO")