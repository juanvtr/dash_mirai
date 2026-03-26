# Mirai Insights v3.0 - Dashboard B2B Vivo

## O que e este app

Dashboard Streamlit para analise completa da carteira B2B da Mirai Telecom (parceira Vivo).
Integra 3 fontes de dados e gera mailings automatizados conforme o PDF "Raio X Carteira".

---

## Fontes de Dados

| Arquivo | Descricao | Nivel | Encoding |
|---------|-----------|-------|----------|
| `RelatorioInfoB2B_MapaParqueVisaoCliente_*.csv` | Mapa Parque - visao cliente | 1 linha por CNPJ | cp1252/latin1, sep `;` |
| `RelatorioInfoB2B_ParqueMovel_*.csv` | Parque Movel - visao linha | 1 linha por numero | latin1, sep `;` |
| `users.xls` | Equipe comercial do Bitrix | 1 linha por colaborador | HTML (exportado Bitrix) |

### Mapa Parque (~92 colunas)
Contem a visao consolidada do cliente: CNPJ, produtos (movel, fixa, BL, VVN, Vivo Tech),
CAR (conta a receber movel/fixa), cobertura FTTH, fidelizacao, biometria, recomendacoes
de oferta, trilha comercial, propensao, digital, aparelhos, contatos.

### Parque Movel (~45 colunas)
Contem cada linha movel individualmente: numero, plano, M (meses de contrato),
faturamento medio 3 meses, trafego de dados, fidelizacao por linha, semaforo Serasa,
elegibilidade para blindagem, convergencia, aparelho em uso.

**IMPORTANTE**: A coluna `M` do Parque Movel e o dado REAL de meses do contrato movel.
O Mapa Parque so tem `DT_INCLUSAO_CARTEIRA` (data de inclusao na carteira do consultor),
que e diferente. O dashboard cruza os dois por CNPJ para usar o M real.

### Users (Bitrix)
Lista de colaboradores exportada do Bitrix CRM. Contem nome, departamento (time/gerencia),
email, celular, ultima atividade.

---

## Arquitetura do Codigo

```
📂 mirai_dashboard/
├── 📄 app.py              # App Streamlit principal (sidebar, tabs, layout)
├── 📄 config.py            # Cores, constantes, versao
├── 📄 data_processing.py   # ETL: leitura, limpeza, classificacao, mailings
├── 📄 charts.py            # Graficos Plotly padronizados
├── 📄 styles.py            # CSS customizado e funcoes de renderizacao
├── 📄 requirements.txt     # Dependencias Python
└── 📄 README.md            # Este arquivo
```

### Fluxo de Dados

```
Mapa Parque (CSV) ──→ processar_mapa_parque() ──→ df_mapa (12.835 clientes)
                                                        │
Parque Movel (CSV) ──→ processar_parque_movel() ──→ df_movel (37.103 linhas)
                              │
                              └──→ agregar_parque_movel_por_cnpj() ──→ df_movel_agg (9.006 CNPJs)
                                                                           │
                                    cruzar_mapa_com_movel() ←─────────────┘
                                              │
                                              └──→ df_mapa + colunas PM_* (M real, fidelizacao, faturamento)
                                                        │
                                                        └──→ gerar_todos_mailings() ──→ 16 mailings Raio X

Users (XLS) ──→ processar_users() ──→ df_users (105 colaboradores)
```

---

## Abas do Dashboard

### 1. Mapa Parque (Visao Geral)
- 6 KPIs principais: Total Clientes, Linhas Moveis, Banda Larga, Vivo Tech, FTTH%, Big Deals
- 4 KPIs do Parque Movel (quando carregado): Linhas PM, Faturamento, Linhas M17+, % Fidelizado
- Graficos: Categoria M, Semaforo CAR, Segmentacao Comercial, Tipo de Posse

### 2. Raio X
- Grafico de barras horizontais com todos os indicadores do Raio X
- Tabela detalhada por indicador com contagens e metricas
- Heatmap Segmento x Categoria M

### 3. Segmentacao
- Detalhamento dos segmentos comerciais
- Grafico de fidelizacao
- Tabela resumo com descricoes

### 4. Parque Movel (quando carregado)
- KPIs: Total Linhas, Fidelizadas, Fat. Medio Total, Excedente Dados
- Graficos: Faixa M das linhas, Fidelizacao por linha, Semaforo Serasa, Blindagem
- Top 10 Planos
- **Classificacao M por Cliente**: mostra clientes com linhas em multiplos Ms
  - Exemplo: cliente com 8 linhas, sendo 3 em M7-M12 e 5 em M17-M21

### 5. Equipe (quando Users carregado)
- KPIs: Total Colaboradores, Times, Gerencias
- Tabela de colaboradores por time e gerencia
- Busca por nome

### 6. Mailings
- 16 mailings automatizados conforme PDF Raio X:
  - Secao 1 - MOVEL (6 mailings)
  - Secao 2 - FIXA (4 mailings)
  - Secao 3 - INDICADORES (6 mailings)
- Download individual (CSV) ou consolidado (Excel com 16 abas)
- Mailing customizado com filtros aplicados

### 7. Dados Brutos
- Tabela interativa com seletor de colunas
- Busca por nome/CNPJ
- Download CSV

---

## Mailings - Referencia Raio X

Cada mailing segue EXATAMENTE as definicoes do PDF "Raio X Carteira Mirai Telecom".

| Codigo | Nome | Filtro | Objetivo |
|--------|------|--------|----------|
| 1.1 | Movel SEM Fixa M17+ | TEM_MOVEL, nao TEM_FIXA, PM_LINHAS_M17_PLUS > 0 | RENOVAR + VENDA FTTH |
| 1.2 | Movel COM Fixa M17+ | TEM_MOVEL, TEM_FIXA, PM_LINHAS_M17_PLUS > 0 | RENOVAR |
| 1.3 | Excedente Dados M7-M16 | TEM_MOVEL, PM_LINHAS_M7_M16 > 0 | UP |
| 1.4 | Credito Aparelho M7-M12 | TEM_MOVEL, PM_LINHAS_M7_M12 > 0, TEM_APARELHOS | UP + APARELHO |
| 1.5 | Movel SEM Mancha M17-M21 | TEM_MOVEL, nao NA_MANCHA, PM_M_MEDIO 17-21 | RENOVAR + VVN + LINHA NOVA |
| 1.6 | Propensao Aquisicao | PORT_POTENCIAL Alto ou Medio | VENDA LINHA NOVA |
| 2.1 | Fixa SEM Movel | TEM_FIXA, nao TEM_MOVEL | RENOVAR + VENDA FTTH |
| 2.2 | Cliente PEN | TEM_PEN (terminal metalico) | VENDA FTTH |
| 2.3 | Fixa c/ UP e Propensao | TEM_FIXA, nao TEM_MOVEL, nao FIDELIZADO | UP FIXA + LINHA NOVA |
| 2.4 | Renovacao Fixa Basica | TEM_FIXA, FIDELIZADO | VENDA FTTH + LINHA NOVA |
| 3.1 | CAR | CAR_TOTAL > 0 | RELACIONAMENTO + REGULARIZAR CAR |
| 3.2 | Nao Biometrado | BIOMETRADO = False | RELACIONAMENTO |
| 3.3 | Cobertura 5G | TEM_5G = True | TROCA APARELHO + CHIP 5G |
| 3.4 | Vivo Tech Atual | QTD_VTECH > 0 | VENDA + RENOVACAO MAQUINAS |
| 3.5 | Vivo Tech Potencial | QTD_VTECH = 0, VIVO_TECH preenchido | VENDA DE MAQUINAS |
| 3.6 | Digital | DIGITAL_1 preenchido | DIGITALIZAR + RECEITA |

**Quando o Parque Movel esta carregado**, os mailings 1.1 a 1.5 usam o M REAL
(coluna M do Parque Movel) em vez do MESES_CARTEIRA do Mapa Parque.

---

## Classificacoes Automaticas

### Semaforo CAR (Conta a Receber)
| Cor | Regra | Significado |
|-----|-------|-------------|
| PRETO/CINZA | CAR = 0 | Sem pendencia |
| VERDE | CAR < 50 | Pendencia leve |
| AMARELO | 50 <= CAR < 150 | Atencao |
| VERMELHO | CAR >= 150 | Critico |

### Categoria M (meses do contrato movel)
| Faixa | Meses | Acao tipica |
|-------|-------|-------------|
| M0-M6 | 0 a 6 | Cliente novo, acompanhar |
| M7-M12 | 7 a 12 | UP, credito aparelho |
| M13-M16 | 13 a 16 | Excedente dados, preparar renovacao |
| M17-M21 | 17 a 21 | RENOVAR, VVN, blindagem |
| M22+ | 22+ | Vencido, risco de churn |

### Segmento Comercial
| Segmento | Posse do cliente | Foco |
|----------|------------------|------|
| TOTALIZACAO | So Movel | Vender fixa |
| MIGRACAO MOVEL | So Fixa (VB, BL, VB+BL) | Vender movel |
| BLINDAGEM/RENOVACAO | Totalizado (movel+fixa) | Renovar contratos |
| CROSS-SELL | Totalizado | Produtos adicionais |
| AVANCADOS/VVN | Totalizado | Internet dedicada, VVN |
| DIGITALIZACAO | Totalizado | Produtos digitais |

### Posse Simplificada
Derivada do campo POSSE do Mapa Parque:
- **VB + BL + Movel**: Voz Basica (fixa) + Banda Larga + Movel = cliente totalizado
- **BL + Movel**: Banda Larga + Movel, sem voz fixa
- **VB + BL**: Voz Basica + Banda Larga, sem movel
- **So Movel**: Apenas linhas moveis
- **So BL**: Apenas banda larga
- **So Voz**: Apenas voz fixa basica

---

## Instalacao e Uso

### Requisitos
```
Python 3.10+
streamlit >= 1.30.0
pandas >= 2.0.0
plotly >= 5.18.0
openpyxl >= 3.1.0
```

### Instalacao Local
```bash
cd mirai_dashboard
pip install -r requirements.txt
streamlit run app.py
```

### Deploy no Streamlit Cloud
1. Suba a pasta `mirai_dashboard/` para um repositorio GitHub
2. Acesse https://share.streamlit.io
3. Conecte o repositorio e selecione `app.py`
4. Deploy automatico

### Tutorial de Uso
1. Abra o app no navegador
2. Na barra lateral, carregue o **Mapa Parque** (obrigatorio)
3. Carregue o **Parque Movel** (recomendado - ativa M real e KPIs extras)
4. Carregue o **Users** (opcional - ativa aba de equipe)
5. Aguarde o processamento (aparece spinner)
6. Use os **filtros** na sidebar: Segmento, Categoria M, Semaforo, Mancha FTTH
7. Navegue pelas abas para explorar os dados
8. Na aba **Mailings**, baixe os CSVs para importar no CRM/discador

---

## Recomendacao de Infraestrutura (ate R$ 500/mes)

### Opcao 1: Streamlit Cloud (GRATIS)
- Ja esta hospedado la
- Limite: 1GB RAM, dados nao persistem entre sessoes
- Bom para uso individual e equipe pequena
- Upload manual dos CSVs a cada sessao

### Opcao 2: Supabase + Streamlit Cloud (R$ 0-130/mes)
- **Supabase Free Tier**: banco Postgres gratuito ate 500MB
- Armazena os dados processados (Mapa + Movel + Users) no banco
- Elimina necessidade de upload manual
- ETL roda uma vez e salva no banco
- R$ 130/mes no plano Pro para 8GB e backups diarios

### Opcao 3: Railway ou Render (R$ 25-100/mes)
- **Railway**: deploy de Streamlit com banco Postgres integrado
- 512MB-2GB RAM por R$ 25-60/mes
- Persistencia de dados com volume
- Deploy automatico via GitHub

### Opcao 4: VPS (Hetzner/DigitalOcean) (R$ 30-80/mes)
- **Hetzner CX22**: 4GB RAM, 40GB SSD por ~R$ 30/mes
- Instala Streamlit + DuckDB (banco leve em arquivo)
- Total controle, dados persistem no disco
- Precisa de manutencao manual

### Opcao Recomendada para Voce
**Supabase (Free/Pro) + Streamlit Cloud** e a melhor relacao custo-beneficio:
1. Os CSVs sao convertidos para tabelas no Supabase (1x)
2. O Streamlit puxa os dados do banco (sem upload manual)
3. Novos CSVs podem ser carregados pelo app ou via script agendado
4. Custo: R$ 0 (free tier) ou R$ 130/mes (pro com mais espaco)

Para implementar isso, basta adicionar `supabase-py` ao requirements e criar
um modulo `db.py` que substitui o upload por queries ao banco.

---

## Glossario

| Termo | Significado |
|-------|-------------|
| **M** | Meses desde a ativacao/renovacao do contrato movel |
| **CAR** | Conta a Receber - valor em aberto do cliente |
| **BL** | Banda Larga (internet fixa) |
| **VB** | Voz Basica (telefone fixo) |
| **FTTH** | Fiber To The Home - fibra otica |
| **PEN** | Terminal metalico (linha fixa analogica) |
| **VVN** | Vivo Voz Negocio (PABX virtual) |
| **Big Deal** | Cliente com faturamento significativo |
| **MEI** | Microempreendedor Individual |
| **Mancha** | Area com cobertura FTTH disponivel |
| **Serasa** | Score de credito (Verde/Amarelo/Vermelho/Cinza/Preto) |
| **Blindagem** | Renovacao antecipada para reter cliente |
| **Convergencia** | Cliente apto a ter movel + fixa juntos |

---

## Versoes

| Versao | Data | Mudancas |
|--------|------|----------|
| 1.0 | Fev/2026 | Dashboard basico com upload de Mapa Parque |
| 2.0 | Fev/2026 | Mailings automatizados, semaforo CAR, raio X |
| 3.0 | Mar/2026 | Parque Movel (M real), Users, ranking equipe, 16 mailings |

---

*Juan Vieira - Data Engineer - 2026*

