"""
╔══════════════════════════════════════════════════════════════════════╗
║  MIRAI TELECOM - DASHBOARD CONFIGURAÇÃO                            ║
║  Cores da marca, constantes e configurações globais                ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ══════════════════════════════════════════════════════════════════════
# PALETA DE CORES - Baseada no PDF "Regras de Venda" Vivo/Mirai
# ══════════════════════════════════════════════════════════════════════

CORES = {
    "roxo_vivo":      "#660099",
    "azul_mirai":     "#2F5496",
    "roxo_escuro":    "#4A0072",
    "roxo_claro":     "#9B59B6",
    "amarelo":        "#FFCC00",
    "laranja":        "#FF6600",
    "verde":          "#92D050",
    "amarelo_sem":    "#FFD700",
    "vermelho":       "#FF0000",
    "preto":          "#333333",
    "fundo":          "#F5F5FA",
    "fundo_card":     "#FFFFFF",
    "texto":          "#333333",
    "texto_claro":    "#666666",
    "borda":          "#E0E0E0",
}

PLOTLY_COLORS = [
    "#660099", "#2F5496", "#9B59B6", "#3498DB",
    "#1ABC9C", "#F39C12", "#E74C3C", "#95A5A6",
]

SEMAFORO_CORES = {
    "VERDE": "#92D050", "AMARELO": "#FFD700",
    "VERMELHO": "#FF0000", "PRETO/CINZA": "#333333",
}

SEGMENTOS_ORDEM = [
    "MIGRAÇÃO MÓVEL", "TOTALIZAÇÃO", "BLINDAGEM / RENOVAÇÃO",
    "CROSS-SELL", "AVANÇADOS / VVN", "DIGITALIZAÇÃO", "OUTROS",
]

SEGMENTOS_ICONS = {
    "MIGRAÇÃO MÓVEL": "📱", "TOTALIZAÇÃO": "🔗",
    "BLINDAGEM / RENOVAÇÃO": "🛡️", "CROSS-SELL": "🔄",
    "AVANÇADOS / VVN": "🚀", "DIGITALIZAÇÃO": "💻", "OUTROS": "📋",
}

SEGMENTOS_DESC = {
    "MIGRAÇÃO MÓVEL": "Tem fixa, não tem móvel",
    "TOTALIZAÇÃO": "Tem móvel, não tem fixa",
    "BLINDAGEM / RENOVAÇÃO": "Totalizado, móvel vencido",
    "CROSS-SELL": "Totalizado, oportunidades adicionais",
    "AVANÇADOS / VVN": "Internet Dedicada, Voz Avançada",
    "DIGITALIZAÇÃO": "Foco primário em digital",
    "OUTROS": "Sem informação suficiente",
}

MAILING_COLUMNS = [
    "CNPJ", "RAZÃO", "POSSE", "PLANTA_MOVEL", "PLANTA_BL",
    "DISPONIBILIDADE", "NM_CONTATO", "EMAIL", "CELULAR", "TELEFONE",
    "VERTICAL", "SEGMENTO", "CATEGORIA_M", "SEMAFORO",
    "TRILHA", "COMENTARIO", "INFO_FONTE",
]

APP_TITLE = "Mirai Insights"
APP_SUBTITLE = "Raio X Carteira + Análise de Deals"
APP_ICON = ""
APP_VERSION = "2.0"
