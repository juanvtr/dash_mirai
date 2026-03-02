#  Mirai Insights - Dashboard Analítico

**Raio X Carteira + Análise de Deals + Geração de Mailings**

Dashboard Streamlit completo para análise da carteira Vivo Empresas B2B, cruzamento com deals do Bitrix e geração automática de mailings comerciais.

---

## Instalação e Execução

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar o dashboard
streamlit run app.py
```

O dashboard abrirá no navegador em `http://localhost:8501`.

---

## 📁 Estrutura do Projeto

```
mirai_dashboard/
├── app.py                 # App principal Streamlit (entry point)
├── config.py              # Cores, constantes, configurações
├── data_processing.py     # ETL: leitura, limpeza, classificação, mailings
├── charts.py              # Funções de gráficos Plotly padronizados
├── styles.py              # CSS customizado e componentes HTML
├── requirements.txt       # Dependências Python
└── README.md              # Este arquivo
```

---

## 📂 Arquivos de Input

### Mapa Parque (CSV)
- **Formato:** CSV com separador `;` e encoding `cp1252`
- **Fonte:** Relatório B2B `RelatorioInfoB2B_MapaParqueVisaoCliente_*.csv`
- **Upload:** Sidebar do dashboard

### Deals Bitrix (CSV)
- **Formato:** CSV com separador `;` e encoding `utf-8-sig`
- **Fonte:** Exportação do Bitrix CRM
- **Upload:** Sidebar do dashboard

---

##  Abas do Dashboard

| Aba | Descrição |
|-----|-----------|
| 🗺️ **Mapa Parque** | KPIs principais, Categoria M, Semáforo CAR, Segmentação, Posse |
| 🎯 **Raio X** | Raio X completo da carteira (Móvel s/ Fixa, Fixa s/ Móvel, PEN, 5G, etc.) com heatmap Segmento × Categoria M |
| 📈 **Segmentação** | Fidelização, MEI por segmento, tabela resumo por segmento |
|  **Deals** | KPIs de deals, por fase, tipo, gerência e consultor |
| 🔄 **Cruzamento** | Penetração de deals na base, por segmento, potencial portabilidade vs real |
|  **Mailings** | Download de mailings por segmento + mailing customizado com filtros |
| 📋 **Dados Brutos** | Tabela interativa com busca e download |

---

##  Mailings Gerados Automaticamente

- **TOTALIZAÇÃO** — Clientes só móvel (candidatos a fixa)
- **MIGRAÇÃO MÓVEL** — Clientes com fixa, sem móvel
- **BLINDAGEM / RENOVAÇÃO** — Clientes totalizados com móvel vencido
- **CROSS-SELL** — Oportunidades adicionais
- **AVANÇADOS / VVN** — Internet Dedicada e Voz Avançada
- **DIGITALIZAÇÃO** — Foco em digital
- **MOVEL_SEM_FIXA_M17** — Móvel sem fixa com 17+ meses
- **COBERTURA_5G** — Clientes com cobertura 5G
- **VIVO_TECH** — Clientes com Vivo Tech ativo
- **CAR_VERMELHO** — Clientes com CAR alto (risco)
- **ALTO_POTENCIAL_PORT** — Alto potencial de portabilidade

---

## 🔍 Filtros Disponíveis

- **Segmento** — Filtra por segmento comercial
- **Categoria M** — Filtra por tempo na carteira (M0-M6, M7-M16, etc.)
- **Semáforo** — Filtra por situação de CAR
- **Mancha FTTH** — Apenas clientes na mancha de fibra

---

## 🎨 Identidade Visual

Cores baseadas na identidade Vivo/Mirai:
- **Roxo Vivo:** `#660099`
- **Azul Mirai:** `#2F5496`
- **Amarelo Vivo:** `#FFCC00`
- **Semáforo:** Verde `#92D050` / Amarelo `#FFD700` / Vermelho `#FF0000`

---

## 🛠️ Manutenção

- Para adicionar novos mailings: editar `gerar_todos_mailings()` em `data_processing.py`
- Para adicionar novos gráficos: criar função em `charts.py` e chamar em `app.py`
- Para ajustar classificações: editar funções `classificar_*` em `data_processing.py`

---

**Desenvolvido por Data Analytics Mirai © 2026**
