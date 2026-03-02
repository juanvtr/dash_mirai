"""
MIRAI TELECOM - PROCESSAMENTO DE DADOS
ETL: leitura, limpeza, classificação, cruzamento e mailings
"""
import pandas as pd
import numpy as np
from datetime import datetime
from collections import OrderedDict
import glob
import os

# ══════════════════════════════════════════════════════════════════════
# FUNCOES DE CARREGAMENTO DE DADOS
# ══════════════════════════════════════════════════════════════════════

def carregar_dados_locais(diretorio="."):
    """
    Localiza e carrega os arquivos de dados (Mapa Parque, Deals, Users)
    a partir de um diretorio local, aplicando o processamento inicial.

    Args:
        diretorio (str): O caminho para o diretorio onde os arquivos estao.

    Returns:
        tuple: Uma tupla contendo os DataFrames (df_mapa, df_deals, df_users).
               Retorna None para um DataFrame se o arquivo correspondente nao
               for encontrado.
    """
    # --- Carregar Mapa Parque ---
    df_mapa = None
    arquivos_mapa = glob.glob(os.path.join(diretorio, "RelatorioInfoB2B_MapaParqueVisaoCliente_*.csv"))
    if arquivos_mapa:
        caminho_mapa = max(arquivos_mapa, key=os.path.getctime) # Pega o mais recente
        encodings = ["cp1252", "latin1", "iso-8859-1", "utf-8-sig", "utf-8"]
        raw_df_mapa = None
        for enc in encodings:
            try:
                raw_df_mapa = pd.read_csv(caminho_mapa, encoding=enc, sep=";", on_bad_lines="skip", low_memory=False)
                if len(raw_df_mapa.columns) > 3:
                    break
            except (UnicodeDecodeError, Exception):
                continue
        if raw_df_mapa is not None:
            df_mapa = processar_mapa_parque(raw_df_mapa)

    # --- Carregar Deals ---
    df_deals = None
    arquivos_deals = glob.glob(os.path.join(diretorio, "DEAL_*.csv"))
    if arquivos_deals:
        caminho_deals = max(arquivos_deals, key=os.path.getctime)
        raw_df_deals = None
        for enc in ["utf-8-sig", "utf-8", "cp1252", "latin1"]:
            for sep in [";", ","]:
                try:
                    raw_df_deals = pd.read_csv(caminho_deals, encoding=enc, sep=sep, on_bad_lines="skip", low_memory=False)
                    if len(raw_df_deals.columns) > 3:
                        break
                except Exception:
                    continue
            if raw_df_deals is not None and len(raw_df_deals.columns) > 3:
                break
        if raw_df_deals is not None:
             df_deals = processar_deals(raw_df_deals)

    # --- Carregar Users ---
    df_users = None
    # Assumindo que o nome da coluna de vendedor em users.xls é 'Vendedor'
    # e que as colunas de hierarquia sao 'Time' e 'Gerente'
    arquivos_users = glob.glob(os.path.join(diretorio, "users.xls*"))
    if arquivos_users:
        caminho_users = arquivos_users[0]
        try:
            df_users = pd.read_excel(caminho_users)
            if 'Vendedor' in df_users.columns:
                df_users['Vendedor_Norm'] = df_users['Vendedor'].apply(normalizar_vendedores)
        except Exception as e:
            print(f"Erro ao carregar o arquivo de usuarios: {e}")

    return df_mapa, df_deals, df_users


# ══════════════════════════════════════════════════════════════════════
# FUNÇÕES UTILITÁRIAS
# ══════════════════════════════════════════════════════════════════════

def safe_int(val):
    """Converte valor para inteiro de forma segura. Retorna 0 se falhar."""
    try:
        return int(float(str(val)))
    except (ValueError, TypeError):
        return 0

def safe_float(val):
    """Converte valor para float de forma segura. Retorna 0.0 se falhar."""
    try:
        return float(str(val))
    except (ValueError, TypeError):
        return 0.0

def normalize_cnpj(val):
    """Normaliza CNPJ para 14 dígitos com zeros à esquerda."""
    s = str(val).split(".")[0]
    s = "".join(c for c in s if c.isdigit())
    return s.zfill(14) if len(s) > 0 else None

def normalizar_vendedores(nome):
    """
    Funcao para tratar as duplicidades e variacoes de nomes no Bitrix.
    Remove sufixos de numeracao e padroniza abreviacoes conhecidas.
    """
    if pd.isna(nome):
        return "Nao Identificado"
    
    n = str(nome).upper().strip()
    
    import re
    n = re.sub(r'\s*\(\d+\)$', '', n)
    n = re.sub(r'\s*-\s*\d+$', '', n)
    
    mapeamento_manual = {
        "KATIA H. SANTANA": "KATIA HELENA SANTANA",
        "KATIA SANTANA": "KATIA HELENA SANTANA",
    }
    
    return mapeamento_manual.get(n, n)

# ══════════════════════════════════════════════════════════════════════
# CLASSIFICAÇÕES
# ══════════════════════════════════════════════════════════════════════

def calcular_meses_carteira(dt_inclusao):
    """Calcula meses desde DT_INCLUSAO_CARTEIRA até hoje."""
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

def classificar_semaforo(car_movel, car_fixa):
    """PRETO/CINZA: 0 | VERDE: <50 | AMARELO: 50-149 | VERMELHO: >=150."""
    car = safe_float(car_movel) + safe_float(car_fixa)
    if car == 0:     return "PRETO/CINZA"
    elif car < 50:   return "VERDE"
    elif car < 150:  return "AMARELO"
    else:            return "VERMELHO"

def classificar_segmento(row):
    """Classifica segmento comercial baseado em POSSE + PRIMEIRA_OFERTA + RECOMENDACAO."""
    posse = row.get("POSSE_SIMPL", "")
    of1 = str(row.get("OFERTA_1_REC", ""))
    prim = str(row.get("PRIMEIRA_OFERTA", ""))
    if posse == "Móvel":
        return "TOTALIZAÇÃO"
    if posse in ("VB + BL", "Fixa Basica (VB)", "BL"):
        return "MIGRAÇÃO MÓVEL"
    if posse in ("VB + BL + Móvel", "BL + Móvel"):
        if "Blindagem" in prim or "Renovação" in of1: return "BLINDAGEM / RENOVAÇÃO"
        if "Digital" in prim or "Digitalizar" in of1: return "DIGITALIZAÇÃO"
        if "Avançad" in prim or "Internet Dedicada" in of1 or "VVN" in prim: return "AVANÇADOS / VVN"
        return "CROSS-SELL"
    return "OUTROS"

def classificar_tipo_solicitacao(tipo):
    """Agrupa tipos de solicitação de deals: Portabilidade, Migração, Alta, TT, Outros."""
    tipo = str(tipo).strip()
    if tipo in ("Portabilidade", "Portabilidade Novo", "Portabilidade PF",
                "Portabilidade PJ PJ", "Portabilidade Base"): return "Portabilidade"
    elif tipo in ("Migração", "Migração Pré Pós", "Migração + Troca"): return "Migração"
    elif tipo in ("Alta", "Alta Base", "Alta Novo"): return "Alta"
    elif tipo in ("TT PJ PJ", "TT PF PJ"): return "Troca de Titularidade"
    return "Outros"

# ══════════════════════════════════════════════════════════════════════
# PROCESSAMENTO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════

def processar_mapa_parque(df_bruto):
    """Aplica todas as transformações e classificações ao DataFrame do Mapa Parque."""
    df = df_bruto.copy()
    if "SITUACAO_RECEITA" in df.columns:
        df = df[df["SITUACAO_RECEITA"].str.contains("ATIVA", case=False, na=False)].copy()

    df["MESES_CARTEIRA"] = df["DT_INCLUSAO_CARTEIRA"].apply(calcular_meses_carteira)
    df["QTD_MOVEL"] = df["QT_MOVEL_TERM"].apply(safe_int)
    df["QTD_BL"] = (df["QT_BASICA_BL"].apply(safe_int) + df["QT_BL_FTTH"].apply(safe_int) + df["QT_BL_FTTC"].apply(safe_int))
    df["QTD_VTECH"] = df["QT_VIVO_TECH"].apply(safe_int)
    df["QTD_PEN"] = df["QT_BASICA_TERM_METALICO"].apply(safe_int)
    
    df["BIG_DEAL"] = df["FL_BIG_DEAL"].fillna(0).astype(float).astype(int) == 1
    df["MEI"] = df["FLG_MEI"].fillna(0).astype(float).astype(int) == 1
    df["FIDELIZADO"] = df["FLG_FIDELIZADO"].fillna(0).astype(float).astype(int) == 1
    
    df["CAR_MOVEL"] = df["VL_CAR_MOVEL"].apply(safe_float)
    df["CAR_FIXA"] = df["VL_CAR_FIXA"].apply(safe_float)
    df["CAR_TOTAL"] = df["CAR_MOVEL"] + df["CAR_FIXA"]
    df["SEMAFORO"] = df.apply(lambda r: classificar_semaforo(r["CAR_MOVEL"], r["CAR_FIXA"]), axis=1)

    df["TEM_MOVEL"] = df["QTD_MOVEL"] > 0
    df["TEM_FIXA"] = df["QTD_BL"] > 0
    df["TEM_PEN"] = df["QTD_PEN"] > 0
    df["NA_MANCHA"] = df["DS_DISPONIBILIDADE"].str.contains("FTTH", na=False, case=False)

    df["CNPJ_NORM"] = df["NR_CNPJ"].apply(normalize_cnpj)
    df["SEGMENTO"] = df.apply(classificar_segmento, axis=1)
    df["CATEGORIA_M"] = df["MESES_CARTEIRA"].apply(
        lambda m: "M0-M6" if m <= 6 else "M7-M16" if m <= 16 else "M17-M21" if m <= 21 else "M22+"
    )
    df["NOME_CLIENTE"] = df.get("NM_CLIENTE", df.get("NR_CNPJ", "")).astype(str)
    return df

def processar_deals(df_bruto):
    """Aplica todas as transformações e classificações ao DataFrame de Deals."""
    df = df_bruto.copy()
    if "CNPJ" in df.columns:
        df["CNPJ_NORM"] = df["CNPJ"].apply(normalize_cnpj)
    if "Tipo de Solicitação" in df.columns:
        df["TIPO_AGRUPADO"] = df["Tipo de Solicitação"].apply(classificar_tipo_solicitacao)
    if "Quantidade de linhas" in df.columns:
        df["QTD_LINHAS"] = pd.to_numeric(df["Quantidade de linhas"], errors="coerce").fillna(0).astype(int)
    
    for col in ["Criado", "Modificado", "Data de fechamento"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    
    df = calcular_sla_deals(df)
    
    if "Responsável" in df.columns:
        df['Vendedor_Norm'] = df['Responsável'].apply(normalizar_vendedores)
        
    return df

def cruzar_dados(df_mapa, df_deals):
    """Cruza Mapa Parque e Deals por CNPJ, adicionando flags de existência mútua."""
    if df_mapa is None or df_deals is None:
        return df_mapa, df_deals, set(), set(), set()
        
    cnpjs_mapa = set(df_mapa["CNPJ_NORM"].dropna())
    cnpjs_deal = set(df_deals["CNPJ_NORM"].dropna())
    cnpjs_comum = cnpjs_mapa & cnpjs_deal
    
    df_mapa["TEM_DEAL"] = df_mapa["CNPJ_NORM"].isin(cnpjs_comum)
    df_deals["TEM_CNPJ_MAPA"] = df_deals["CNPJ_NORM"].isin(cnpjs_comum)
    
    return df_mapa, df_deals, cnpjs_mapa, cnpjs_deal, cnpjs_comum


# ══════════════════════════════════════════════════════════════════════
# ANALISE DE PERFORMANCE E SLA
# ══════════════════════════════════════════════════════════════════════

def calcular_sla_deals(df):
    """
    Calcula o tempo de ciclo (Lead Time) de cada deal e define o status de SLA.
    """
    if 'Criado' not in df.columns or 'Data de fechamento' not in df.columns:
        return df

    df['Criado'] = pd.to_datetime(df['Criado'], errors='coerce')
    df['Data de fechamento'] = pd.to_datetime(df['Data de fechamento'], errors='coerce')
    
    hoje = pd.Timestamp.now()
    df['LEAD_TIME_DIAS'] = (df['Data de fechamento'].fillna(hoje) - df['Criado']).dt.days
    
    # SLA de 3 dias para fechamento
    df['STATUS_SLA'] = df['LEAD_TIME_DIAS'].apply(lambda x: "FORA DO PRAZO" if x > 3 else "NO PRAZO")
    
    return df

def calcular_ranking_comercial(df_deals, df_users):
    """
    Cria rankings de performance por gerente, time e vendedor.
    """
    if df_deals is None or df_users is None or 'Vendedor_Norm' not in df_deals.columns or 'Vendedor_Norm' not in df_users.columns:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_merged = pd.merge(df_deals, df_users, on="Vendedor_Norm", how="left")

    if "QTD_LINHAS" in df_merged.columns:
        df_merged["FATURAMENTO_EST"] = df_merged["QTD_LINHAS"] * 50 
    else:
        df_merged["FATURAMENTO_EST"] = 0

    # Agrupamentos
    agg_dict = {
        "Total_Deals": ("CNPJ_NORM", "nunique"),
        "Linhas_Totais": ("QTD_LINHAS", "sum"),
        "Faturamento_Total": ("FATURAMENTO_EST", "sum"),
        "Lead_Time_Medio": ("LEAD_TIME_DIAS", "mean")
    }
    
    ranking_vendedor = df_merged.groupby(["Gerente", "Time", "Vendedor_Norm"]).agg(**agg_dict).reset_index()
    ranking_time = df_merged.groupby(["Gerente", "Time"]).agg(**agg_dict).reset_index()
    ranking_gerente = df_merged.groupby("Gerente").agg(**agg_dict).reset_index()

    for df_ranking in [ranking_vendedor, ranking_time, ranking_gerente]:
        df_ranking["Ticket_Medio"] = df_ranking.apply(
            lambda row: row["Faturamento_Total"] / row["Linhas_Totais"] if row["Linhas_Totais"] > 0 else 0, axis=1
        )

    return ranking_gerente, ranking_time, ranking_vendedor

def calcular_eficiencia_conversao(df_mapa, df_deals, df_users):
    """
    Calcula a penetracao de deals na carteira de clientes de cada vendedor.
    """
    if df_mapa is None or df_deals is None or df_users is None or "Consultor" not in df_mapa.columns:
        return pd.DataFrame()

    df_mapa['Vendedor_Norm'] = df_mapa['Consultor'].apply(normalizar_vendedores)

    clientes_por_vendedor = df_mapa.groupby("Vendedor_Norm")["CNPJ_NORM"].nunique().reset_index()
    clientes_por_vendedor.columns = ["Vendedor_Norm", "Total_Clientes_Carteira"]

    deals_por_vendedor = df_deals.groupby("Vendedor_Norm")["CNPJ_NORM"].nunique().reset_index()
    deals_por_vendedor.columns = ["Vendedor_Norm", "Clientes_Com_Deal"]

    eficiencia = pd.merge(clientes_por_vendedor, deals_por_vendedor, on="Vendedor_Norm", how="left")
    eficiencia["Clientes_Com_Deal"] = eficiencia["Clientes_Com_Deal"].fillna(0)
    
    eficiencia["Penetracao"] = eficiencia.apply(
        lambda row: (row["Clientes_Com_Deal"] / row["Total_Clientes_Carteira"]) * 100 if row["Total_Clientes_Carteira"] > 0 else 0, axis=1
    )
    
    eficiencia = pd.merge(eficiencia, df_users, on="Vendedor_Norm", how="left")

    return eficiencia.sort_values(by="Penetracao", ascending=False)