# -*- coding: utf-8 -*-
"""Mirai Insights v4 - Paleta derivada da logo Mirai Telecom."""

APP_TITLE = "Mirai Insights"
APP_SUBTITLE = "Raio X Carteira B2B"
APP_VERSION = "4.0"

# Cores extraidas da logo: magenta -> roxo -> ciano
BRAND = {
    "magenta": "#D946EF",   # rosa-magenta da base da logo
    "purple":  "#8B5CF6",   # roxo medio do gradiente
    "cyan":    "#06B6D4",   # ciano dos tracos superiores
    "pink":    "#EC4899",   # rosa quente
    "violet":  "#7C3AED",   # roxo escuro
}

LIGHT = {
    "bg": "#FFFFFF", "bg2": "#F8F7FA", "sidebar": "#FAFAFB", "card": "#FFFFFF",
    "hover": "#F3F2F6", "border": "#E9E5F0", "border_h": "#D4CDE3",
    "tx": "#1A1A2E", "tx2": "#64607D", "tx3": "#A09CB5",
    "acc": "#8B5CF6", "acc_h": "#7C3AED", "acc_bg": "#F5F3FF",
    "acc2": "#D946EF", "acc3": "#06B6D4",
    "sh1": "0 1px 2px rgba(139,92,246,0.04)",
    "sh2": "0 4px 14px rgba(139,92,246,0.08)",
    "success": "#22C55E", "warning": "#EAB308", "error": "#EF4444", "info": "#06B6D4",
}

DARK = {
    "bg": "#0A0A0F", "bg2": "#12121A", "sidebar": "#0E0E15", "card": "#16161F",
    "hover": "#1E1E2A", "border": "#252533", "border_h": "#3A3A4D",
    "tx": "#F5F3FF", "tx2": "#A5A1BC", "tx3": "#5C586E",
    "acc": "#A78BFA", "acc_h": "#C4B5FD", "acc_bg": "#1A1528",
    "acc2": "#E879F9", "acc3": "#22D3EE",
    "sh1": "0 1px 2px rgba(0,0,0,0.3)",
    "sh2": "0 4px 14px rgba(0,0,0,0.4)",
    "success": "#4ADE80", "warning": "#FBBF24", "error": "#F87171", "info": "#22D3EE",
}

CHART_COLORS = ["#8B5CF6", "#D946EF", "#06B6D4", "#EC4899", "#3B82F6", "#22C55E", "#F59E0B", "#6B7280"]
CHART_COLORS_DARK = ["#A78BFA", "#E879F9", "#22D3EE", "#F472B6", "#60A5FA", "#4ADE80", "#FBBF24", "#9CA3AF"]

SEMAFORO_CORES = {"VERDE": "#22C55E", "AMARELO": "#EAB308", "VERMELHO": "#EF4444", "PRETO/CINZA": "#6B7280"}
SEMAFORO_SERASA_CORES = {"VERDE": "#22C55E", "AMARELO": "#EAB308", "VERMELHO": "#EF4444", "CINZA": "#9CA3AF", "PRETO": "#52525B"}

SEGMENTOS_DESC = {
    "MIGRACAO MOVEL": "Tem fixa, nao tem movel",
    "TOTALIZACAO": "Tem movel, nao tem fixa",
    "BLINDAGEM / RENOVACAO": "Totalizado, contrato vencendo",
    "CROSS-SELL": "Totalizado, oportunidades adicionais",
    "AVANCADOS / VVN": "Internet Dedicada, Voz Avancada",
    "DIGITALIZACAO": "Foco em produtos digitais",
    "OUTROS": "Sem informacao suficiente",
}

FAIXAS_M = {"M0-M6": (0, 6), "M7-M12": (7, 12), "M13-M16": (13, 16), "M17-M21": (17, 21), "M22+": (22, 9999)}

MAILING_CORES = {
    "RENOVAR": "#8B5CF6", "UP": "#06B6D4", "VENDA": "#3B82F6",
    "RELACIONAMENTO": "#EAB308", "TROCA": "#22C55E", "DIGITALIZAR": "#D946EF",
}
