# -*- coding: utf-8 -*-
"""
Mirai Insights - Integracao Supabase.

Persiste dados no Supabase (Postgres) para nao depender de uploads manuais.
Requer: SUPABASE_URL e SUPABASE_KEY.

Tabelas:
  - deals: deals do Bitrix (atualizado via webhook)
  - mailing_log: historico de mailings gerados
  - config: configuracoes (webhook URL, etc)
  
Alternativa gratuita: usa SQLite local se Supabase nao configurado.
"""

import os
import json
import sqlite3
import pandas as pd
from datetime import datetime

# Tenta importar supabase, fallback pra SQLite
try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False


class MiraiDB:
    """
    Camada de persistencia unificada.
    Usa Supabase se configurado, senao SQLite local.
    """
    
    def __init__(self, supabase_url=None, supabase_key=None, local_path="mirai_data.db"):
        self.use_supabase = False
        self.supabase = None
        self.local_path = local_path
        
        if supabase_url and supabase_key and HAS_SUPABASE:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                self.use_supabase = True
            except Exception as e:
                print("Supabase indisponivel, usando SQLite: {}".format(e))
        
        if not self.use_supabase:
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Cria tabelas SQLite se nao existirem."""
        conn = sqlite3.connect(self.local_path)
        c = conn.cursor()
        
        c.execute("""CREATE TABLE IF NOT EXISTS deals (
            id TEXT PRIMARY KEY,
            cnpj TEXT,
            nome TEXT,
            responsavel TEXT,
            pipeline TEXT,
            fase TEXT,
            renda REAL,
            aberto INTEGER,
            criado TEXT,
            modificado TEXT,
            dados_json TEXT,
            atualizado_em TEXT
        )""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS mailing_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            objetivo TEXT,
            qtd_registros INTEGER,
            gerado_em TEXT,
            gerado_por TEXT,
            filtro_deals INTEGER DEFAULT 0,
            removidos_deals INTEGER DEFAULT 0
        )""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT,
            atualizado_em TEXT
        )""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS vendedor_stats (
            vendedor TEXT,
            mes TEXT,
            deals_abertos INTEGER DEFAULT 0,
            deals_ganhos INTEGER DEFAULT 0,
            deals_perdidos INTEGER DEFAULT 0,
            faturamento REAL DEFAULT 0,
            atualizado_em TEXT,
            PRIMARY KEY (vendedor, mes)
        )""")
        
        conn.commit()
        conn.close()
    
    # ===== CONFIG =====
    
    def get_config(self, chave, default=None):
        if self.use_supabase:
            try:
                r = self.supabase.table("config").select("valor").eq("chave", chave).execute()
                return r.data[0]["valor"] if r.data else default
            except:
                return default
        else:
            conn = sqlite3.connect(self.local_path)
            c = conn.cursor()
            c.execute("SELECT valor FROM config WHERE chave = ?", (chave,))
            row = c.fetchone()
            conn.close()
            return row[0] if row else default
    
    def set_config(self, chave, valor):
        now = datetime.now().isoformat()
        if self.use_supabase:
            self.supabase.table("config").upsert({
                "chave": chave, "valor": valor, "atualizado_em": now
            }).execute()
        else:
            conn = sqlite3.connect(self.local_path)
            conn.execute(
                "INSERT OR REPLACE INTO config (chave, valor, atualizado_em) VALUES (?, ?, ?)",
                (chave, valor, now))
            conn.commit()
            conn.close()
    
    # ===== DEALS =====
    
    def upsert_deals(self, df_deals):
        """Salva/atualiza deals no banco."""
        if df_deals.empty:
            return 0
        
        now = datetime.now().isoformat()
        count = 0
        
        if self.use_supabase:
            # Batch upsert no Supabase
            records = []
            for _, row in df_deals.iterrows():
                records.append({
                    "id": str(row.get("ID", "")),
                    "cnpj": str(row.get("CNPJ_NORM", "")),
                    "nome": str(row.get("NOME_NORM", "")),
                    "responsavel": str(row.get("RESPONSAVEL", "")),
                    "pipeline": str(row.get("CATEGORY_ID", "")),
                    "fase": str(row.get("STAGE_ID", "")),
                    "renda": float(row.get("RENDA", 0)),
                    "aberto": bool(row.get("DEAL_ABERTO", True)),
                    "criado": str(row.get("DATE_CREATE", "")),
                    "modificado": str(row.get("DATE_MODIFY", "")),
                    "atualizado_em": now,
                })
            
            # Batch de 500
            for i in range(0, len(records), 500):
                batch = records[i:i+500]
                try:
                    self.supabase.table("deals").upsert(batch).execute()
                    count += len(batch)
                except Exception as e:
                    print("Erro upsert Supabase: {}".format(e))
        else:
            conn = sqlite3.connect(self.local_path)
            for _, row in df_deals.iterrows():
                conn.execute(
                    """INSERT OR REPLACE INTO deals 
                    (id, cnpj, nome, responsavel, pipeline, fase, renda, aberto, criado, modificado, atualizado_em)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (str(row.get("ID", "")),
                     str(row.get("CNPJ_NORM", "")),
                     str(row.get("NOME_NORM", "")),
                     str(row.get("RESPONSAVEL", "")),
                     str(row.get("CATEGORY_ID", "")),
                     str(row.get("STAGE_ID", "")),
                     float(row.get("RENDA", 0)),
                     1 if row.get("DEAL_ABERTO", True) else 0,
                     str(row.get("DATE_CREATE", "")),
                     str(row.get("DATE_MODIFY", "")),
                     now))
                count += 1
            conn.commit()
            conn.close()
        
        return count
    
    def get_deals_abertos(self):
        """Retorna DataFrame com deals abertos."""
        if self.use_supabase:
            try:
                r = self.supabase.table("deals").select("*").eq("aberto", True).execute()
                return pd.DataFrame(r.data) if r.data else pd.DataFrame()
            except:
                return pd.DataFrame()
        else:
            conn = sqlite3.connect(self.local_path)
            df = pd.read_sql("SELECT * FROM deals WHERE aberto = 1", conn)
            conn.close()
            return df
    
    def get_cnpjs_em_tratativa(self):
        """Retorna (set_cnpjs, set_nomes) de deals abertos."""
        df = self.get_deals_abertos()
        if df.empty:
            return set(), set()
        cnpjs = set(df["cnpj"].unique()) - {"", "nan", "None"}
        nomes = set(df["nome"].unique()) - {"", "nan", "None", "NAN"}
        return cnpjs, nomes
    
    # ===== VENDEDOR STATS =====
    
    def calcular_stats_vendedores(self):
        """Calcula estatisticas por vendedor a partir dos deals salvos."""
        if self.use_supabase:
            try:
                r = self.supabase.table("deals").select("*").execute()
                df = pd.DataFrame(r.data) if r.data else pd.DataFrame()
            except:
                return pd.DataFrame()
        else:
            conn = sqlite3.connect(self.local_path)
            df = pd.read_sql("SELECT * FROM deals", conn)
            conn.close()
        
        if df.empty:
            return pd.DataFrame()
        
        # Agrupar por vendedor
        stats = df.groupby("responsavel").agg(
            total_deals=("id", "count"),
            deals_abertos=("aberto", "sum"),
            faturamento_total=("renda", "sum"),
            faturamento_medio=("renda", "mean"),
        ).reset_index()
        
        stats["deals_fechados"] = stats["total_deals"] - stats["deals_abertos"]
        stats["taxa_conversao"] = (stats["deals_fechados"] / stats["total_deals"] * 100).round(1)
        stats = stats.sort_values("faturamento_total", ascending=False)
        
        return stats
    
    # ===== MAILING LOG =====
    
    def log_mailing(self, codigo, objetivo, qtd, filtro_deals=False, removidos=0):
        """Registra geracao de mailing no historico."""
        now = datetime.now().isoformat()
        if self.use_supabase:
            try:
                self.supabase.table("mailing_log").insert({
                    "codigo": codigo, "objetivo": objetivo, "qtd_registros": qtd,
                    "gerado_em": now, "filtro_deals": filtro_deals, "removidos_deals": removidos,
                }).execute()
            except:
                pass
        else:
            conn = sqlite3.connect(self.local_path)
            conn.execute(
                "INSERT INTO mailing_log (codigo, objetivo, qtd_registros, gerado_em, filtro_deals, removidos_deals) VALUES (?, ?, ?, ?, ?, ?)",
                (codigo, objetivo, qtd, now, 1 if filtro_deals else 0, removidos))
            conn.commit()
            conn.close()
    
    def get_mailing_log(self, limit=50):
        """Retorna historico de mailings gerados."""
        if self.use_supabase:
            try:
                r = self.supabase.table("mailing_log").select("*").order("gerado_em", desc=True).limit(limit).execute()
                return pd.DataFrame(r.data) if r.data else pd.DataFrame()
            except:
                return pd.DataFrame()
        else:
            conn = sqlite3.connect(self.local_path)
            df = pd.read_sql("SELECT * FROM mailing_log ORDER BY gerado_em DESC LIMIT ?", conn, params=(limit,))
            conn.close()
            return df
    
    # ===== STATUS =====
    
    def status(self):
        """Retorna dict com status do banco."""
        info = {
            "backend": "Supabase" if self.use_supabase else "SQLite Local",
            "path": "cloud" if self.use_supabase else self.local_path,
        }
        
        if self.use_supabase:
            try:
                r = self.supabase.table("deals").select("id", count="exact").execute()
                info["total_deals"] = r.count or 0
            except:
                info["total_deals"] = "erro"
        else:
            try:
                conn = sqlite3.connect(self.local_path)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM deals")
                info["total_deals"] = c.fetchone()[0]
                c.execute("SELECT MAX(atualizado_em) FROM deals")
                info["ultima_atualizacao"] = c.fetchone()[0] or "nunca"
                conn.close()
            except:
                info["total_deals"] = 0
                info["ultima_atualizacao"] = "nunca"
        
        return info