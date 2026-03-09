# -*- coding: utf-8 -*-
"""
Mirai Insights - Integracao Bitrix24 via Webhook.

Usa a REST API do Bitrix24 para buscar deals sem precisar de upload manual.
Requer: BITRIX_WEBHOOK_URL no formato https://seudominio.bitrix24.com.br/rest/USER_ID/WEBHOOK_KEY/

Endpoints usados:
  - crm.deal.list: listar deals com filtros
  - crm.deal.fields: campos disponiveis
"""

import requests
import pandas as pd
import re
from datetime import datetime


def fetch_deals(webhook_url, status_callback=None):
    """
    Busca TODOS os deals do Bitrix24 via webhook (paginado, 50 por vez).
    
    Args:
        webhook_url: URL do webhook (ex: https://xxx.bitrix24.com.br/rest/1/abc123/)
        status_callback: funcao opcional para reportar progresso (recebe string)
    
    Returns:
        DataFrame com deals processados
    """
    url = webhook_url.rstrip("/") + "/crm.deal.list"
    
    all_deals = []
    start = 0
    
    while True:
        if status_callback:
            status_callback("Buscando deals... ({:,} carregados)".format(len(all_deals)))
        
        params = {
            "order[ID]": "DESC",
            "select[]": [
                "ID", "TITLE", "STAGE_ID", "CATEGORY_ID", "ASSIGNED_BY_ID",
                "COMPANY_ID", "CONTACT_ID", "OPPORTUNITY", "CURRENCY_ID",
                "CLOSED", "DATE_CREATE", "DATE_MODIFY", "CLOSEDATE",
                "UF_CRM_1*",  # campos customizados
            ],
            "start": start,
        }
        
        try:
            resp = requests.post(url, json=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            if status_callback:
                status_callback("Erro na requisicao: {}".format(str(e)))
            break
        except ValueError:
            if status_callback:
                status_callback("Erro ao parsear resposta JSON")
            break
        
        if "result" not in data:
            if status_callback:
                status_callback("Resposta sem 'result'. Erro: {}".format(data.get("error_description", "desconhecido")))
            break
        
        deals = data["result"]
        if not deals:
            break
        
        all_deals.extend(deals)
        
        # Paginacao do Bitrix: campo 'next' indica proximo offset
        if "next" in data:
            start = data["next"]
        else:
            break
    
    if not all_deals:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_deals)
    
    if status_callback:
        status_callback("Processando {:,} deals...".format(len(df)))
    
    return df


def fetch_deal_details(webhook_url, deal_ids, status_callback=None):
    """Busca detalhes de deals especificos (incluindo campos custom)."""
    url = webhook_url.rstrip("/") + "/crm.deal.get"
    results = []
    
    for i, did in enumerate(deal_ids):
        if status_callback and i % 50 == 0:
            status_callback("Detalhes: {}/{}".format(i, len(deal_ids)))
        try:
            resp = requests.post(url, json={"id": did}, timeout=15)
            data = resp.json()
            if "result" in data:
                results.append(data["result"])
        except:
            continue
    
    return pd.DataFrame(results) if results else pd.DataFrame()


def fetch_companies_by_ids(webhook_url, company_ids, status_callback=None):
    """Busca dados de empresas (CNPJ, nome) por IDs."""
    url = webhook_url.rstrip("/") + "/crm.company.list"
    
    # Batch de 50
    all_companies = []
    ids = [i for i in company_ids if i and str(i) != "0"]
    
    for batch_start in range(0, len(ids), 50):
        batch = ids[batch_start:batch_start+50]
        if status_callback:
            status_callback("Empresas: {:,}/{:,}".format(batch_start, len(ids)))
        
        # Filtro por IDs
        filter_params = {}
        for idx, cid in enumerate(batch):
            filter_params["filter[ID][{}]".format(idx)] = cid
        
        try:
            params = {
                "select[]": ["ID", "TITLE", "UF_CRM_*", "ASSIGNED_BY_ID"],
                "filter[ID]": batch,
            }
            resp = requests.post(url, json=params, timeout=30)
            data = resp.json()
            if "result" in data:
                all_companies.extend(data["result"])
        except:
            continue
    
    return pd.DataFrame(all_companies) if all_companies else pd.DataFrame()


def fetch_users(webhook_url, status_callback=None):
    """Busca lista de usuarios (vendedores) do Bitrix."""
    url = webhook_url.rstrip("/") + "/user.get"
    
    all_users = []
    start = 0
    
    while True:
        try:
            resp = requests.post(url, json={"start": start, "ACTIVE": True}, timeout=30)
            data = resp.json()
        except:
            break
        
        if "result" not in data:
            break
        
        users = data["result"]
        if not users:
            break
        
        all_users.extend(users)
        
        if "next" in data:
            start = data["next"]
        else:
            break
    
    if not all_users:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_users)
    
    # Simplificar
    cols = {
        "ID": "USER_ID",
        "NAME": "NOME",
        "LAST_NAME": "SOBRENOME",
        "EMAIL": "EMAIL",
        "PERSONAL_PHONE": "TELEFONE",
        "UF_DEPARTMENT": "DEPARTAMENTO_IDS",
    }
    avail = {k: v for k, v in cols.items() if k in df.columns}
    result = df[list(avail.keys())].rename(columns=avail)
    result["NOME_COMPLETO"] = (result.get("NOME", "") + " " + result.get("SOBRENOME", "")).str.strip()
    
    return result


def process_webhook_deals(df_raw, df_users=None):
    """
    Processa deals crus do webhook para o formato padrao do dashboard.
    
    Returns:
        DataFrame com CNPJ_NORM, DEAL_ABERTO, NOME_NORM, etc.
    """
    if df_raw.empty:
        return pd.DataFrame()
    
    df = df_raw.copy()
    
    # Deal aberto
    df["DEAL_ABERTO"] = df["CLOSED"].astype(str).str.upper() != "Y"
    
    # Renda/valor
    df["RENDA"] = pd.to_numeric(df.get("OPPORTUNITY", 0), errors="coerce").fillna(0)
    
    # Datas
    for col in ["DATE_CREATE", "DATE_MODIFY"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    
    # Vendedor
    if df_users is not None and not df_users.empty and "ASSIGNED_BY_ID" in df.columns:
        user_map = df_users.set_index("USER_ID")["NOME_COMPLETO"].to_dict()
        df["RESPONSAVEL"] = df["ASSIGNED_BY_ID"].astype(str).map(user_map).fillna("Desconhecido")
    else:
        df["RESPONSAVEL"] = "N/A"
    
    # CNPJ e Nome serao preenchidos depois do fetch de companies
    df["CNPJ_NORM"] = ""
    df["NOME_NORM"] = df.get("TITLE", "").astype(str).str.upper().str.strip()
    # Limpar prefixos numericos do titulo
    df["NOME_NORM"] = df["NOME_NORM"].str.replace(r"^\d+\s+", "", regex=True)
    
    return df


def test_webhook(webhook_url):
    """Testa se o webhook esta funcionando. Retorna (ok, mensagem)."""
    url = webhook_url.rstrip("/") + "/crm.deal.list"
    try:
        resp = requests.post(url, json={"start": 0, "limit": 1}, timeout=10)
        data = resp.json()
        if "result" in data:
            return True, "Webhook OK. {} deals acessiveis.".format(data.get("total", "?"))
        else:
            return False, "Erro: {}".format(data.get("error_description", "resposta invalida"))
    except requests.exceptions.RequestException as e:
        return False, "Erro de conexao: {}".format(str(e))
    except:
        return False, "Erro desconhecido ao testar webhook."