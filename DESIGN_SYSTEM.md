# Mirai Insights - Design System & Product Blueprint

**Versao:** 4.0
**Data:** Março 2026
**Autor:** Data Analytics Mirai Telecom

---

## 1. IDENTIDADE VISUAL

### 1.1 Direcao Estetica

**Tom:** Refined Minimal — inspirado em Notion, Linear e Vercel.
Precisao cirurgica nos espacamentos. Tipografia como protagonista.
Cor como pontuacao, nunca como ruido.

O diferencial memoravel: **a ausencia deliberada de elementos decorativos**.
Cada pixel tem uma razao funcional. O dashboard nao "parece bonito" — ele
**desaparece** para que os dados falem.

### 1.2 Paleta de Cores

**Primaria:**
- Roxo Vivo `#660099` — Identidade Mirai. Usado com parcimonia: apenas
  em acentos, KPIs de destaque e elementos interativos ativos.
- Azul Parque `#2F5496` — Secundario. Graficos, links hover, elementos
  informativos.

**Neutros (Light):**
- Background: `#FFFFFF` (puro, sem cinza)
- Surface: `#F7F7F8` (cards, sidebar)
- Border: `#E8E8EC` (divisores, contornos de input)
- Text Primary: `#1A1A1A`
- Text Secondary: `#6B6B76`
- Text Muted: `#A0A0AB`

**Neutros (Dark):**
- Background: `#09090B`
- Surface: `#18181B`
- Border: `#27272A`
- Text Primary: `#FAFAFA`
- Text Secondary: `#A1A1AA`
- Text Muted: `#52525B`

**Semanticos:**
- Success: `#22C55E` (verde sem saturacao excessiva)
- Warning: `#EAB308`
- Error: `#EF4444`
- Info: `#3B82F6`

**Regra de ouro:** O roxo `#660099` nunca aparece em mais de 15% da
area visivel de qualquer tela. Ele eh o tempero, nao o prato.

### 1.3 Tipografia

**Display:** Instrument Sans (Google Fonts) — geometrica, afiada, moderna.
Usada em titulos de pagina e KPIs numericos.

**Body:** DM Sans — humanista, legivel em todos os tamanhos.
Usada em texto corrido, labels, descricoes.

**Mono:** JetBrains Mono — para CNPJs, codigos de mailing,
valores monetarios em tabelas.

Escala tipografica (rem):
- Page title: 2.0rem / 700
- Section title: 1.25rem / 600
- Card title: 1.0rem / 600
- Body: 0.875rem / 400
- Caption: 0.78rem / 500
- Badge: 0.72rem / 600

### 1.4 Espacamento

Sistema baseado em multiplos de 4px:
- xs: 4px (gap entre badge e texto)
- sm: 8px (padding interno de pill)
- md: 16px (padding de card)
- lg: 24px (gap entre secoes)
- xl: 32px (margem entre blocos)
- 2xl: 48px (separacao de contextos)

### 1.5 Icones

Sem emojis no codigo. Sem Font Awesome.
Os unicos "icones" sao indicadores semanticos:
- Status dots (8px circles com cor semantica)
- Chevrons em breadcrumbs (caractere unicode ›)
- Setas em botoes de download (caractere unicode ↓)

A ausencia de icones decorativos EH o design.

### 1.6 Sombras e Elevacao

Light mode:
- Level 0: sem sombra (estado default de cards)
- Level 1: `0 1px 2px rgba(0,0,0,0.04)` (hover sutil)
- Level 2: `0 4px 12px rgba(0,0,0,0.06)` (card ativo/focus)
- Level 3: `0 8px 24px rgba(0,0,0,0.08)` (modal/dropdown)

Dark mode:
- Level 1: `0 1px 2px rgba(0,0,0,0.2)`
- Level 2: `0 4px 12px rgba(0,0,0,0.3)`
- Level 3: `0 8px 24px rgba(0,0,0,0.4)`

Regra: bordas substituem sombras em 90% dos casos.
Sombra so aparece em hover ou elementos flutuantes.

---

## 2. ARQUITETURA DE INFORMACAO

### 2.1 Hierarquia de Navegacao

```
Mirai Insights
├── Carteira (dados do cliente)
│   ├── Visao Geral ← KPIs, graficos consolidados
│   ├── Raio X ← indicadores cruzados do PDF
│   └── Segmentacao ← classificacao comercial
├── Movel (dados da linha)
│   ├── Parque Movel ← distribuicao M, fidelizacao, Serasa
│   └── Classificacao M ← clientes com linhas em multiplos Ms
├── Comercial (acoes)
│   ├── Mailings ← 16 mailings do Raio X + customizado
│   └── Regua M ← regua de relacionamento M16-M24
└── Dados
    └── Tabela Bruta ← explorador interativo
```

### 2.2 Fluxo do Usuario

1. **Entrada**: Upload de 2 CSVs na sidebar (Mapa Parque + Parque Movel)
2. **Processamento**: Spinner com mensagem contextual ("Cruzando dados...")
3. **Navegacao**: Tabs horizontais — usuario ve todas as opcoes de uma vez
4. **Acao**: Download de mailings (CSV individual ou Excel consolidado)
5. **Iteracao**: Filtros na sidebar refinam TODAS as telas simultaneamente

### 2.3 Modelo Mental do Usuario

O usuario pensa em 3 perguntas:
1. "Como esta minha carteira?" → Carteira / Visao Geral
2. "Quem eu devo ligar?" → Comercial / Regua M + Mailings
3. "Quais sao os numeros exatos?" → Dados / Tabela Bruta

O design prioriza essas 3 perguntas nessa ordem.

---

## 3. WIREFRAMES

### 3.1 Sidebar

```
┌──────────────────────────┐
│  MIRAI INSIGHTS    [D/L] │ ← logo + toggle tema
│  v4.0                    │
│──────────────────────────│
│  ▼ Fontes de Dados       │ ← expander (default aberto)
│    [Mapa Parque ▲]       │ ← file uploader
│    [Parque Movel ▲]      │ ← file uploader
│    ● Mapa  ● Movel       │ ← status dots
│──────────────────────────│
│  ▶ Filtros               │ ← expander (default fechado)
│    Segmento  [Todos ▼]   │
│    Categoria M [Todos ▼] │
│    Semaforo  [Todos ▼]   │
│    □ Apenas mancha FTTH  │
│──────────────────────────│
│                          │
│  Mirai Data Analytics    │
│  2026                    │
└──────────────────────────┘
```

A sidebar tem no maximo 2 expanders. Nada mais.
Filtros ficam collapsed por default porque o usuario
tipicamente analisa tudo primeiro, depois filtra.

### 3.2 Tela: Visao Geral (Mapa Parque)

```
Carteira › Visao Geral                    ← breadcrumb

Visao Geral da Carteira                   ← h1 page header
Analise consolidada por CNPJ              ← subtitle

┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐     ← KPI grid (6 cols)
│12.8k││37.1k││9.7k││ 186││32.3%││ 847│
│Cli. ││Linhas││ BL ││VTech││FTTH ││Big D│
└────┘└────┘└────┘└────┘└────┘└────┘

┌────┐┌────┐┌────┐┌────┐                  ← KPI grid (4 cols, PM data)
│37.1k││R$1.9M││4.9k ││70.1% │
│Lin PM││Fat Tot││M17+ ││% Fid │
└────┘└────┘└────┘└────┘

─────────────────────────────────────     ← divider

┌──────────────┐ ┌──────────────┐         ← charts 2x2
│  Categoria M │ │  Semaforo CAR │
│   (donut)    │ │    (bar)      │
└──────────────┘ └──────────────┘
┌──────────────┐ ┌──────────────┐
│ Segmentacao  │ │ Tipo Posse   │
│  (bar horiz) │ │   (donut)    │
└──────────────┘ └──────────────┘
```

KPIs usam o pattern: numero grande em cima, label pequeno embaixo.
O primeiro KPI de cada grid eh "accent" (roxo). Os demais sao neutros.

### 3.3 Tela: Regua M (NOVA)

```
Comercial › Regua M                       ← breadcrumb

Regua de Relacionamento                   ← h1
Linhas nos meses M16-M24+                 ← subtitle

┌─────────────────────────────────────┐   ← info box
│ M16: Informativo | M17: Semanal     │
│ M18-M22: Quinzenal | M23+: Urgente  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐   ← bar chart (M16 a M24+)
│  ████  M16: 1.489                   │
│  ███   M17: 1.315                   │
│  ██    M18: 1.025                   │
│  ...                                │
└─────────────────────────────────────┘

─────────────────────────────────────

Detalhamento por Mes                      ← section title

┌────────────────────────────────────┐    ← dataframe
│ Mes │ Linhas │ CNPJs │ Fat │ Freq │
│ M16 │ 1.489  │ 1.102 │ 85k │ Info │
│ M17 │ 1.315  │  998  │ 73k │ Sem  │
│ ...                                │
└────────────────────────────────────┘

Exportar Mailing                          ← section title
[M16 ▼]  [Baixar Mailing M16 (1.489)]   ← select + download
```

### 3.4 Tela: Mailings

```
Comercial › Mailings                      ← breadcrumb

Mailings - Raio X Carteira               ← h1
16 mailings automatizados                 ← subtitle

[Baixar TODOS (16 em Excel)]             ← primary download

─────────────────────────────────────

1. Movel                                  ← section

┌────────────────────┐┌──────────────────┐
│ 1.1 MOVEL SEM FIXA │ 1.2 MOVEL COM    │ ← card grid 2 cols
│                     │ FIXA M17          │
│ RENOVAR + FTTH      │ RENOVAR           │
│ 1.651 clientes      │ 1.619 clientes   │
│                     │                   │
│ Linhas: 7.2k       │ Linhas: 8.1k     │
│ Mancha: 842        │ Big: 124          │
│                     │                   │
│ [↓ Baixar 1.1]     │ [↓ Baixar 1.2]   │
└────────────────────┘└──────────────────┘
```

### 3.5 Tela: Parque Movel

```
Movel › Parque Movel                      ← breadcrumb

Parque Movel                              ← h1
37.103 linhas telefonicas                 ← subtitle

┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐     ← KPIs
│37.1k││25.9k││R$1.9M││17.9k││5.4k││9.0k│
│Total││Fidel││Fat   ││Blind││Exced││CNPJs│
└────┘└────┘└────┘└────┘└────┘└────┘

─────────────────────────────────────

┌──────────────┐ ┌──────────────┐         ← charts
│ Faixa M      │ │ Fidelizacao  │
└──────────────┘ └──────────────┘
┌──────────────┐ ┌──────────────┐
│ Serasa       │ │ Blindagem    │
└──────────────┘ └──────────────┘

─────────────────────────────────────

Top 10 Planos                             ← bar horiz

─────────────────────────────────────

Classificacao M por Cliente               ← section

info: Cada CNPJ pode ter linhas em
diferentes faixas de M...

[chart: clientes por faixa M]

[tabela: clientes com multiplos Ms]
```

---

## 4. MICROINTERACOES

### 4.1 Cards

- **Hover**: borda transita de `#E8E8EC` para `#D4D4D8` em 150ms.
  Sombra level 0 → level 1. Transform translateY(-1px).
- **Nenhum efeito de escala** — scale eh brega em dashboards profissionais.

### 4.2 KPIs

- **Ao carregar**: numeros aparecem sem animacao de contagem.
  Animacoes de contagem sao para landing pages, nao para dashboards
  onde o usuario quer a informacao imediatamente.
- **Hover**: apenas sombra sutil aparece.

### 4.3 Tabs

- **Ativa**: borda inferior 2px na cor accent. Texto vira accent + bold.
- **Hover**: background sutil (#F7F7F8 light / #18181B dark).
- **Transicao**: 150ms ease. Sem slide. Sem fade. Instantaneo
  para que o usuario sinta responsividade.

### 4.4 Botoes de Download

- **Default**: borda neutra, texto accent, fundo transparente.
- **Hover**: fundo muda para accent_bg, borda muda para accent.
- **Active/click**: nenhum efeito extra — o browser faz o download
  e isso ja eh feedback suficiente.

### 4.5 Filtros

- Selects com borda neutra. Focus ring na cor accent (0 0 0 1px accent).
- Checkbox com accent color quando marcado.
- Toda mudanca de filtro causa rerun instantaneo do Streamlit.

### 4.6 Toggle de Tema

- Botao "D" (dark) / "L" (light) no canto superior da sidebar.
- Nenhuma animacao de transicao — troca instantanea.
  Transicoes de tema sao desconcertantes em ferramentas de trabalho.

---

## 5. ACESSIBILIDADE

### 5.1 Contraste

Todos os pares de cor atendem WCAG AA (minimo 4.5:1 para texto normal):
- Light: #1A1A1A sobre #FFFFFF = 17.4:1
- Light: #6B6B76 sobre #FFFFFF = 5.2:1
- Dark: #FAFAFA sobre #09090B = 19.3:1
- Dark: #A1A1AA sobre #09090B = 7.1:1
- Accent light: #660099 sobre #FFFFFF = 7.9:1
- Accent dark: #A855F7 sobre #09090B = 6.2:1

### 5.2 Navegacao por Teclado

- Tabs sao navegaveis com Tab/Shift+Tab.
- Selects e checkboxes sao nativos do Streamlit (acessiveis por padrao).
- Botoes de download tem focus ring visivel.

### 5.3 Screen Readers

- Breadcrumbs usam tags semanticas.
- KPIs tem label descritivo + valor numerico.
- Graficos Plotly tem texto alternativo via title.
- Tabelas usam headers de coluna explicitos.

### 5.4 Responsividade

- KPI grid usa auto-fit com minmax(160px, 1fr) — adapta de 6 colunas
  em desktop para 2 em mobile.
- Card grid usa minmax(320px, 1fr) — 2 colunas em desktop, 1 em mobile.
- Sidebar collapse nativo do Streamlit.

---

## 6. COMPONENTES REUTILIZAVEIS

### 6.1 Catalogo

| Componente | Uso | Arquivo |
|------------|-----|---------|
| `kpi_card(label, value, accent)` | KPI numerico | styles.py |
| `kpi_grid(cards)` | Grid de KPIs responsivo | styles.py |
| `breadcrumb(items)` | Navegacao contextual | styles.py |
| `page_header(title, desc)` | Header de pagina | styles.py |
| `section_title(text)` | Titulo de secao | styles.py |
| `divider()` | Linha divisoria | styles.py |
| `info_box(html)` | Caixa informativa | styles.py |
| `mailing_card_html(...)` | Card de mailing | styles.py |
| `welcome_html()` | Tela de boas vindas | styles.py |
| `footer_html(version)` | Rodape com versao/data | styles.py |
| `get_css(theme)` | CSS completo por tema | styles.py |

### 6.2 Graficos (charts.py)

Todos aceitam parametro `theme` para cores.
Todos usam `config={"displayModeBar": False}` para esconder toolbar.

---

## 7. ROADMAP DE MELHORIAS

### v4.1 (Abril 2026)
- Integracao Supabase: dados persistem no banco, sem upload manual
- Webhook Bitrix: deals e users via API, sem upload de arquivos
- Cache de sessao: processamento so roda quando o CSV muda

### v4.2 (Maio 2026)
- Regua M automatizada: script que roda diariamente e classifica
  linhas novas no M correto
- API Claude Haiku: sugestao de abordagem por cliente baseada no perfil
- Export para Brevo/Z-API: mailing ja sai no formato da API de disparo

### v4.3 (Junho 2026)
- Landing pages dinamicas: link no mailing aponta para pagina
  personalizada no HostGator
- Tracking de conversao: formulario da landing cria deal no Bitrix
- Dashboard de campanhas: taxa de abertura, cliques, conversoes

### v5.0 (Futuro)
- Multi-tenant: cada GN/gerente ve apenas sua carteira
- IA preditiva: propensao de churn com base no historico de M
- Integracao Retell: agendamento de ligacoes direto do dashboard

---

## 8. CONCLUSAO ESTRATEGICA

Este design segue 3 principios:

**Simplicidade radical.** O dashboard so tem 2 inputs manuais
(CSVs). Todo o resto eh derivado automaticamente. O usuario nao
precisa de treinamento — a interface eh autoexplicativa.

**Dados como protagonista.** O design visual eh deliberadamente
discreto para que numeros, graficos e tabelas dominem. Nenhum
elemento decorativo compete com a informacao.

**Acao sobre analise.** Cada tela termina com um download.
O dashboard nao existe para ser admirado — existe para gerar
mailings que viram vendas. A Regua M conecta diretamente o dado
(M da linha) com a acao comercial (tipo de disparo).

A proposta de valor se resume em: pegar 2 CSVs crus da Vivo,
e em 10 segundos ter 16 mailings prontos, a regua de
relacionamento completa, e a classificacao de toda a carteira.
Sem configuracao. Sem treinamento. Sem complicacao.

---

*Mirai Telecom - Data Analytics - Marco 2026*
