"""
╔══════════════════════════════════════════════════════════════════════╗
║  MIRAI TELECOM - PROCESSAMENTO DE DADOS                            ║
║  ETL: leitura, limpeza, classificação, cruzamento e mailings       ║
║                                                                      ║
║  Referência: PDF "Raio X Carteira Mirai Telecom - Fev/2026"        ║
║                                                                      ║
║  Estrutura do Raio X (seções do PDF):                               ║
║    1. MÓVEL                                                          ║
║       1.1 Móvel SEM Fixa M17+        → RENOVAR + VENDA FTTH        ║
║       1.2 Móvel COM Fixa M17+        → RENOVAR                     ║
║       1.3 Excedente Dados M7-M16     → UP                          ║
║       1.4 Crédito Aparelho M7-M12    → UP + APARELHO               ║
║       1.5 Móvel SEM Mancha M17-M21   → RENOVAR + VVN + LINHA NOVA  ║
║       1.6 Propensão Aquisição Móvel  → VENDA LINHA NOVA            ║
║    2. FIXA                                                           ║
║       2.1 Fixa SEM Móvel             → RENOVAR + VENDA FTTH        ║
║       2.2 Cliente PEN                → VENDA FTTH                   ║
║       2.3 Fixa c/ UP e Propensão Móv → UP FIXA + LINHA NOVA        ║
║       2.4 Renovação Fixa Básica      → VENDA FTTH + LINHA NOVA     ║
║    3. INDICADORES DA CARTEIRA                                        ║
║       3.1 CAR (Móvel+Fixa / Fixa)    → RELACIONAMENTO + REG. CAR   ║
║       3.2 Parque Não Biometrado      → RELACIONAMENTO              ║
║       3.3 Cobertura 5G               → TROCA APARELHO + CHIP 5G    ║
║       3.4 Vivo Tech (Atual)          → VENDA + RENOVAÇÃO MÁQUINAS  ║
║       3.5 Vivo Tech (Potencial)      → VENDA DE MÁQUINAS           ║
║       3.6 Digital                     → DIGITALIZAR + RECEITA       ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np
from datetime import datetime
from collections import OrderedDict


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


# ══════════════════════════════════════════════════════════════════════
# CLASSIFICAÇÕES DO MAPA PARQUE
# ══════════════════════════════════════════════════════════════════════

def calcular_meses_carteira(dt_inclusao):
    """Calcula meses desde DT_INCLUSAO_CARTEIRA até hoje. Formato: dd/mm/yyyy."""
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

def simplificar_posse(txt):
    """Simplifica POSSE em: VB+BL+Móvel, VB+BL, BL+Móvel, Móvel, BL, Fixa Basica, Outros."""
    txt = str(txt)
    mov = "Móvel" in txt or "móvel" in txt
    bl = "Banda Larga" in txt
    vb = "Voz Básica" in txt or "Voz básica" in txt
    if vb and bl and mov: return "VB + BL + Móvel"
    if vb and bl:         return "VB + BL"
    if bl and mov:        return "BL + Móvel"
    if mov:               return "Móvel"
    if bl:                return "BL"
    if vb:                return "Fixa Basica (VB)"
    return "Outros"

def port_potencial(txt):
    """Extrai potencial de portabilidade: Alto, Médio, Baixo, Renovação, Sem info."""
    txt = str(txt).lower()
    if "alto potencial" in txt:  return "Alto"
    if "médio potencial" in txt or "medio potencial" in txt: return "Médio"
    if "baixo potencial" in txt: return "Baixo"
    if "renovação" in txt:       return "Renovação"
    return "Sem info"

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
# PROCESSAMENTO DO MAPA PARQUE
# ══════════════════════════════════════════════════════════════════════

def processar_mapa_parque(file_or_path):
    """
    Carrega e processa RelatorioInfoB2B_MapaParqueVisaoCliente_*.csv.
    Encoding: cp1252 (fallback latin1/utf-8). Separador: ;
    """
    encodings = ["cp1252", "latin1", "iso-8859-1", "utf-8-sig", "utf-8"]
    df = None
    for enc in encodings:
        try:
            if hasattr(file_or_path, "seek"):
                file_or_path.seek(0)
            df = pd.read_csv(file_or_path, encoding=enc, sep=";",
                             on_bad_lines="skip", low_memory=False)
            if len(df.columns) > 3:
                break
        except (UnicodeDecodeError, Exception):
            continue
    if df is None or len(df.columns) <= 3:
        raise ValueError("Não foi possível ler o Mapa Parque com nenhum encoding.")

    # Filtro ATIVA
    if "SITUACAO_RECEITA" in df.columns:
        df = df[df["SITUACAO_RECEITA"].str.contains("ATIVA", case=False, na=False)].copy()

    # Meses na carteira
    df["MESES_CARTEIRA"] = df["DT_INCLUSAO_CARTEIRA"].apply(calcular_meses_carteira)

    # Quantidades
    df["QTD_MOVEL"] = df["QT_MOVEL_TERM"].apply(safe_int)
    df["QTD_BL"] = (df["QT_BASICA_BL"].apply(safe_int) +
                    df["QT_BL_FTTH"].apply(safe_int) +
                    df["QT_BL_FTTC"].apply(safe_int))
    df["QTD_VTECH"] = df["QT_VIVO_TECH"].apply(safe_int)
    df["QTD_PEN"] = df["QT_BASICA_TERM_METALICO"].apply(safe_int)
    df["QTD_LINHAS_FIXA"] = df["QT_BASICA_LINAS"].apply(safe_int) if "QT_BASICA_LINAS" in df.columns else 0
    df["QTD_VVN"] = df["QT_VVN"].apply(safe_int) if "QT_VVN" in df.columns else 0

    # Flags
    df["BIG_DEAL"] = df["FL_BIG_DEAL"].fillna(0).astype(float).astype(int) == 1
    df["MEI"] = df["FLG_MEI"].fillna(0).astype(float).astype(int) == 1
    df["FIDELIZADO"] = df["FLG_FIDELIZADO"].fillna(0).astype(float).astype(int) == 1
    df["BIOMETRADO"] = df["FLG_CLI_BIOMETRADO"].fillna(0).astype(float).astype(int) == 1
    df["TEM_5G"] = df["COBERTURA_5G"].notna() & (df["COBERTURA_5G"].astype(str).str.strip() != "")
    df["TEM_DIGITAL"] = df["DIGITAL_1"].notna() if "DIGITAL_1" in df.columns else False

    # CAR e Semáforo
    df["CAR_MOVEL"] = df["VL_CAR_MOVEL"].apply(safe_float)
    df["CAR_FIXA"] = df["VL_CAR_FIXA"].apply(safe_float)
    df["CAR_TOTAL"] = df["CAR_MOVEL"] + df["CAR_FIXA"]
    df["SEMAFORO"] = df.apply(lambda r: classificar_semaforo(r["CAR_MOVEL"], r["CAR_FIXA"]), axis=1)

    # Flags de produto
    df["TEM_MOVEL"] = df["QTD_MOVEL"] > 0
    df["TEM_FIXA"] = df["QTD_BL"] > 0
    df["TEM_PEN"] = df["QTD_PEN"] > 0
    df["NA_MANCHA"] = df["DS_DISPONIBILIDADE"].str.contains("FTTH", na=False, case=False)
    df["TEM_APARELHOS"] = df["APARELHOS"].notna() & (df["APARELHOS"].astype(str).str.strip() != "")

    # Classificações
    df["CNPJ_NORM"] = df["NR_CNPJ"].apply(normalize_cnpj)
    df["POSSE_SIMPL"] = df["POSSE"].apply(simplificar_posse)
    df["OFERTA_1_REC"] = df["RECOMENDACAO"].str.extract(r'1° Oferta -> (.+?)(?:\s*///|$)')[0].str.strip()
    df["PORT_POTENCIAL"] = df["REC_MOVEL"].apply(port_potencial)
    df["SEGMENTO"] = df.apply(classificar_segmento, axis=1)
    df["CATEGORIA_M"] = df["MESES_CARTEIRA"].apply(
        lambda m: "M0-M6" if m <= 6 else "M7-M16" if m <= 16 else "M17-M21" if m <= 21 else "M22+"
    )
    df["NOME_CLIENTE"] = df.get("NM_CLIENTE", df.get("NR_CNPJ", "")).astype(str)

    return df


# ══════════════════════════════════════════════════════════════════════
# PROCESSAMENTO DE DEALS (BITRIX)
# ══════════════════════════════════════════════════════════════════════

def normalizar_vendedores(nome):
    """
    Funcao para tratar as duplicidades e variacoes de nomes no Bitrix.
    Remove sufixos de numeracao e padroniza abreviacoes conhecidas.
    """
    if pd.isna(nome):
        return "Nao Identificado"
    
    # Converte para maiusculo e remove espacos extras
    n = str(nome).upper().strip()
    
    # Remove sufixos do tipo (2), (3) ou - 2 que aparecem no sistema
    import re
    n = re.sub(r'\s*\(\d+\)$', '', n)
    n = re.sub(r'\s*-\s*\d+$', '', n)
    
    # Dicionario de de-para para casos especificos mapeados no documento
    # Adicione novos mapeamentos aqui conforme identificar no banco
    mapeamento_manual = {
        "KATIA H. SANTANA": "KATIA HELENA SANTANA",
        "KATIA SANTANA": "KATIA HELENA SANTANA",
        "THAMER": "THAMER NOME_COMPLETO", # Ajuste conforme o sobrenome real
    }
    
    return mapeamento_manual.get(n, n)

def calcular_sla_deals(df):
    """
    Calcula o tempo de ciclo (Lead Time) de cada deal e define o status de SLA.
    Considera o tempo entre a criacao e o fechamento.
    """
    # Garante que as colunas de data estao no formato correto
    df['Criado'] = pd.to_datetime(df['Criado'], errors='coerce')
    df['Data de fechamento'] = pd.to_datetime(df['Data de fechamento'], errors='coerce')
    
    # Para calculo de SLA de itens abertos, usamos a data atual
    hoje = pd.Timestamp.now()
    
    # Calcula a duracao em dias (Lead Time)
    # Se fechado, usa data de fechamento. Se aberto, usa hoje.
    df['LEAD_TIME_DIAS'] = (df['Data de fechamento'].fillna(hoje) - df['Criado']).dt.days
    
    # Regra de negocio: Consideramos fora de SLA pedidos que demoram mais de 3 dias 
    # na esteira de insercao/ativacao (ajustar conforme necessidade da operacao)
    df['STATUS_SLA'] = df['LEAD_TIME_DIAS'].apply(
        lambda x: "FORA DO PRAZO" if x > 3 else "NO PRAZO"
    )
    
    return df

def processar_deals(file_or_path):
    """Carrega e processa DEAL_*.csv do Bitrix. Tenta múltiplos encodings/separadores."""
    df = pd.DataFrame()
    for enc in ["utf-8-sig", "utf-8", "cp1252", "latin1"]:
        for sep in [";", ","]:
            try:
                if hasattr(file_or_path, "seek"):
                    file_or_path.seek(0)
                df = pd.read_csv(file_or_path, encoding=enc, sep=sep,
                                 on_bad_lines="skip", low_memory=False)
                if len(df.columns) > 3:
                    break
            except Exception:
                continue
        if len(df.columns) > 3:
            break
    if "CNPJ" in df.columns:
        df["CNPJ_NORM"] = df["CNPJ"].apply(normalize_cnpj)
    if "Tipo de Solicitação" in df.columns:
        df["TIPO_AGRUPADO"] = df["Tipo de Solicitação"].apply(classificar_tipo_solicitacao)
    if "Quantidade de linhas" in df.columns:
        df["QTD_LINHAS"] = pd.to_numeric(df["Quantidade de linhas"], errors="coerce").fillna(0).astype(int)
    for col in ["Criado", "Modificado", "Data de fechamento"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    return df


# ══════════════════════════════════════════════════════════════════════
# CRUZAMENTO MAPA PARQUE × DEALS
# ══════════════════════════════════════════════════════════════════════

def cruzar_dados(df_mapa, df_deals):
    """Cruza por CNPJ normalizado. Adiciona TEM_DEAL ao mapa e TEM_CNPJ_MAPA aos deals."""
    cnpjs_mapa = set(df_mapa["CNPJ_NORM"].dropna())
    cnpjs_deal = set(df_deals["CNPJ_NORM"].dropna()) if "CNPJ_NORM" in df_deals.columns else set()
    cnpjs_comum = cnpjs_mapa & cnpjs_deal
    df_mapa = df_mapa.copy()
    df_mapa["TEM_DEAL"] = df_mapa["CNPJ_NORM"].isin(cnpjs_comum)
    if "CNPJ_NORM" in df_deals.columns:
        df_deals = df_deals.copy()
        df_deals["TEM_CNPJ_MAPA"] = df_deals["CNPJ_NORM"].isin(cnpjs_comum)
    return df_mapa, df_deals, cnpjs_mapa, cnpjs_deal, cnpjs_comum


# ══════════════════════════════════════════════════════════════════════
# GERAÇÃO DE MAILINGS - CONFORME PDF RAIO X CARTEIRA
# ══════════════════════════════════════════════════════════════════════

# Colunas padrão de contato para todo mailing
_COLS_CONTATO = [
    "NR_CNPJ", "NOME_CLIENTE", "NM_CONTATO_SFA",
    "EMAIL_CONTATO_PRINCIPAL_SFA", "CELULAR_CONTATO_PRINCIPAL_SFA",
    "TLFN_1", "TLFN_2", "DS_CIDADE", "DS_ENDERECO",
]

# Colunas analíticas para todo mailing
_COLS_ANALISE = [
    "POSSE", "SEGMENTO", "CATEGORIA_M", "SEMAFORO",
    "QTD_MOVEL", "QTD_BL", "QTD_VTECH", "QTD_PEN",
    "CAR_TOTAL", "VERTICAL", "CLUSTER",
]


def _montar_mailing(df_filtrado, codigo, objetivo, obs_extra=None):
    """
    Monta DataFrame de mailing padronizado.
    Inclui colunas de contato + análise + flags + metadados.
    """
    if len(df_filtrado) == 0:
        return pd.DataFrame()

    cols_c = [c for c in _COLS_CONTATO if c in df_filtrado.columns]
    cols_a = [c for c in _COLS_ANALISE if c in df_filtrado.columns]
    mailing = df_filtrado[cols_c + cols_a].copy()

    # Flags como texto SIM/vazio (facilita leitura no Excel)
    for flag in ["BIG_DEAL", "MEI", "FIDELIZADO", "NA_MANCHA", "BIOMETRADO"]:
        if flag in df_filtrado.columns:
            col_name = flag if flag != "NA_MANCHA" else "NA_MANCHA_FTTH"
            mailing[col_name] = df_filtrado[flag].map({True: "SIM", False: ""}).values

    # Metadados
    mailing.insert(0, "CODIGO_MAILING", codigo)
    mailing["OBJETIVO"] = objetivo
    if obs_extra:
        mailing["OBSERVACAO"] = obs_extra
    mailing["GERADO_EM"] = datetime.now().strftime("%d/%m/%Y %H:%M")

    return mailing.reset_index(drop=True)


def gerar_todos_mailings(df):
    """
    Gera TODOS os mailings conforme PDF "Raio X Carteira Mirai Telecom".
    Retorna OrderedDict {código: DataFrame} na ordem exata do PDF.
    """
    m = OrderedDict()

    # ═══ 1. MÓVEL ═══

    # 1.1 MÓVEL SEM FIXA M17+ → RENOVAR + VENDA FTTH
    s = df[(df["TEM_MOVEL"]) & (~df["TEM_FIXA"]) & (df["MESES_CARTEIRA"] >= 17)]
    m["1.1_MOVEL_SEM_FIXA_M17"] = _montar_mailing(s, "1.1", "RENOVAR + VENDA FTTH",
        f"Linhas: {s['QTD_MOVEL'].sum():,} | Mancha: {s['NA_MANCHA'].sum():,} | Verde: {(s['SEMAFORO']=='VERDE').sum():,} | Am/Vm: {s['SEMAFORO'].isin(['AMARELO','VERMELHO']).sum():,} | Big: {s['BIG_DEAL'].sum():,}")

    # 1.2 MÓVEL COM FIXA M17+ → RENOVAR
    s = df[(df["TEM_MOVEL"]) & (df["TEM_FIXA"]) & (df["MESES_CARTEIRA"] >= 17)]
    m["1.2_MOVEL_COM_FIXA_M17"] = _montar_mailing(s, "1.2", "RENOVAR",
        f"Linhas: {s['QTD_MOVEL'].sum():,} | Verde: {(s['SEMAFORO']=='VERDE').sum():,} | Am/Vm: {s['SEMAFORO'].isin(['AMARELO','VERMELHO']).sum():,} | Big: {s['BIG_DEAL'].sum():,}")

    # 1.3 EXCEDENTE DADOS M7-M16 → UP
    s = df[(df["TEM_MOVEL"]) & (df["MESES_CARTEIRA"] >= 7) & (df["MESES_CARTEIRA"] <= 16)]
    m["1.3_EXCEDENTE_DADOS_M7_M16"] = _montar_mailing(s, "1.3", "UP",
        f"Linhas: {s['QTD_MOVEL'].sum():,} | Verde: {(s['SEMAFORO']=='VERDE').sum():,} | Am/Vm: {s['SEMAFORO'].isin(['AMARELO','VERMELHO']).sum():,}")

    # 1.4 CRÉDITO APARELHO M7-M12 → UP + APARELHO
    s = df[(df["TEM_MOVEL"]) & (df["MESES_CARTEIRA"] >= 7) & (df["MESES_CARTEIRA"] <= 12) & (df["TEM_APARELHOS"])]
    m["1.4_CREDITO_APARELHO_M7_M12"] = _montar_mailing(s, "1.4", "UP + APARELHO",
        f"Linhas: {s['QTD_MOVEL'].sum():,}")

    # 1.5 MÓVEL SEM MANCHA FIXA M17-M21 → RENOVAR + VVN + LINHA NOVA
    s = df[(df["TEM_MOVEL"]) & (~df["NA_MANCHA"]) & (df["MESES_CARTEIRA"] >= 17) & (df["MESES_CARTEIRA"] <= 21)]
    m["1.5_MOVEL_SEM_MANCHA_M17_M21"] = _montar_mailing(s, "1.5", "RENOVAR + VVN + LINHA NOVA",
        f"Linhas: {s['QTD_MOVEL'].sum():,} | Verde: {(s['SEMAFORO']=='VERDE').sum():,}")

    # 1.6 PROPENSÃO AQUISIÇÃO MÓVEL → VENDA LINHA NOVA
    s = df[df["PORT_POTENCIAL"].isin(["Alto", "Médio"])]
    m["1.6_PROPENSAO_AQUISICAO"] = _montar_mailing(s, "1.6", "VENDA LINHA NOVA",
        f"Alto: {(s['PORT_POTENCIAL']=='Alto').sum():,} | Médio: {(s['PORT_POTENCIAL']=='Médio').sum():,} | Big: {s['BIG_DEAL'].sum():,}")

    # ═══ 2. FIXA ═══

    # 2.1 FIXA SEM MÓVEL → RENOVAR + VENDA FTTH
    s = df[(df["TEM_FIXA"]) & (~df["TEM_MOVEL"])]
    m["2.1_FIXA_SEM_MOVEL"] = _montar_mailing(s, "2.1", "RENOVAR + VENDA FTTH",
        f"BLs: {s['QTD_BL'].sum():,} | Terminal met: {s['QTD_PEN'].sum():,} | MEI: {s['MEI'].sum():,} | Big: {s['BIG_DEAL'].sum():,}")

    # 2.2 CLIENTE PEN → VENDA FTTH
    s = df[df["TEM_PEN"]]
    m["2.2_CLIENTE_PEN"] = _montar_mailing(s, "2.2", "VENDA FTTH",
        f"PENs: {s['QTD_PEN'].sum():,} | Mancha: {s['NA_MANCHA'].sum():,} | Não fid: {(~s['FIDELIZADO']).sum():,}")

    # 2.3 FIXA COM UP E PROPENSÃO MÓVEL → UP FIXA + LINHA NOVA
    s = df[(df["TEM_FIXA"]) & (~df["TEM_MOVEL"]) & (~df["FIDELIZADO"])]
    m["2.3_FIXA_UP_PROPENSAO"] = _montar_mailing(s, "2.3", "UP FIXA BÁSICA + LINHA NOVA",
        f"BLs: {s['QTD_BL'].sum():,} | Não fid: {len(s):,}")

    # 2.4 RENOVAÇÃO FIXA BÁSICA → VENDA FTTH + LINHA NOVA
    s = df[(df["TEM_FIXA"]) & (df["FIDELIZADO"])]
    m["2.4_RENOVACAO_FIXA"] = _montar_mailing(s, "2.4", "VENDA FTTH + LINHA NOVA",
        f"Clientes fidelizados c/ fixa: {len(s):,}")

    # ═══ 3. INDICADORES ═══

    # 3.1 CAR → RELACIONAMENTO + REGULARIZAR CAR
    s = df[df["CAR_TOTAL"] > 0]
    m["3.1_CAR"] = _montar_mailing(s, "3.1", "RELACIONAMENTO + REGULARIZAR CAR",
        f"CAR Móvel>0: {(df['CAR_MOVEL']>0).sum():,} | CAR Fixa>0: {(df['CAR_FIXA']>0).sum():,} | MEI: {s['MEI'].sum():,} | Big: {s['BIG_DEAL'].sum():,}")

    # 3.2 NÃO BIOMETRADO → RELACIONAMENTO
    s = df[~df["BIOMETRADO"]]
    m["3.2_NAO_BIOMETRADO"] = _montar_mailing(s, "3.2", "RELACIONAMENTO",
        f"Mancha: {s['NA_MANCHA'].sum():,} | MEI: {s['MEI'].sum():,} | Não fid: {(~s['FIDELIZADO']).sum():,} | Big: {s['BIG_DEAL'].sum():,}")

    # 3.3 COBERTURA 5G → TROCA APARELHO + CHIP 5G
    s = df[df["TEM_5G"]]
    m["3.3_COBERTURA_5G"] = _montar_mailing(s, "3.3", "TROCA APARELHO + CHIP 5G",
        f"Não fid: {(~s['FIDELIZADO']).sum():,} | Big: {s['BIG_DEAL'].sum():,}")

    # 3.4 VIVO TECH ATUAL → VENDA + RENOVAÇÃO MÁQUINAS
    s = df[df["QTD_VTECH"] > 0]
    m["3.4_VIVO_TECH_ATUAL"] = _montar_mailing(s, "3.4", "VENDA + RENOVAÇÃO DE MÁQUINAS",
        f"Máquinas: {s['QTD_VTECH'].sum():,} | Mancha: {s['NA_MANCHA'].sum():,} | Não fid: {(~s['FIDELIZADO']).sum():,}")

    # 3.5 VIVO TECH POTENCIAL → VENDA DE MÁQUINAS
    s = df[(df["QTD_VTECH"] == 0) & (df["VIVO_TECH"].notna()) & (df["VIVO_TECH"].astype(str).str.strip() != "")]
    m["3.5_VIVO_TECH_POTENCIAL"] = _montar_mailing(s, "3.5", "VENDA DE MÁQUINAS",
        f"Mancha: {s['NA_MANCHA'].sum():,} | Não fid: {(~s['FIDELIZADO']).sum():,}")

    # 3.6 DIGITAL → DIGITALIZAR PARQUE COM AUMENTO DE RECEITA
    if "DIGITAL_1" in df.columns:
        s = df[df["DIGITAL_1"].notna() & (df["DIGITAL_1"].astype(str).str.strip() != "")]
        m["3.6_DIGITAL"] = _montar_mailing(s, "3.6", "DIGITALIZAR PARQUE COM AUMENTO DE RECEITA",
            f"Mancha: {s['NA_MANCHA'].sum():,} | MEI: {s['MEI'].sum():,} | Não fid: {(~s['FIDELIZADO']).sum():,} | Big: {s['BIG_DEAL'].sum():,}")

    return m

# ══════════════════════════════════════════════════════════════════════
# Vendedores x Esteiras x Faturamento
# ══════════════════════════════════════════════════════════════════════

def gerar_mailing_customizado(df_filtrado, nome="CUSTOM"):
    """Gera mailing customizado a partir de qualquer filtro do usuário."""
    return _montar_mailing(df_filtrado, f"CUSTOM_{nome}", "DEFINIDO PELO USUÁRIO")


def analisar_performance_vendedores(df_deals):
    """
    Agrupa performance por consultor, time (gerência) e esteira (pipeline).
    Calcula faturamento estimado e volume de linhas.
    """
    if df_deals is None or df_deals.empty:
        return pd.DataFrame()

    # Identificamos os campos chave baseados no Mapeamento Bitrix
    # Consultor: "Nome do Consultor" [cite: 246]
    # Time: "Gerência" [cite: 241]
    # Esteira: "Etapa" ou "Pipeline" (dependendo do CSV de exportação)
    
    # Criamos uma métrica de 'Faturamento Estimado'
    # Nota: No B2B, o faturamento costuma ser atrelado ao volume de linhas 
    # Aqui você pode ajustar o multiplicador conforme o ticket médio da Mirai
    if "QTD_LINHAS" in df_deals.columns:
        df_deals["FATURAMENTO_EST"] = df_deals["QTD_LINHAS"] * 50 # Exemplo de Ticket Médio
    else:
        df_deals["FATURAMENTO_EST"] = 0

    # Agrupamento Multidimensional
    performance = df_deals.groupby(["Gerência", "Nome do Consultor"]).agg(
        Total_Deals=("CNPJ_NORM", "count"),
        Linhas_Totais=("QTD_LINHAS", "sum") if "QTD_LINHAS" in df_deals.columns else ("CNPJ_NORM", "count"),
        Faturamento=("FATURAMENTO_EST", "sum"),
        Portabilidades=("TIPO_AGRUPADO", lambda x: (x == "Portabilidade").sum())
    ).reset_index()

    return performance.sort_values(by="Faturamento", ascending=False)

def mapear_eficiencia_esteira(df_deals):
    """
    Analisa o volume de cards em cada fase para identificar gargalos (Gaps [cite: 251, 252]).
    """
    if "Fase" not in df_deals.columns:
        return pd.DataFrame()
        
    esteira_stats = df_deals.groupby("Fase").agg(
        Cards=("CNPJ_NORM", "count"),
        Linhas=("QTD_LINHAS", "sum") if "QTD_LINHAS" in df_deals.columns else ("CNPJ_NORM", "count")
    ).reset_index()
    
    return esteira_stats