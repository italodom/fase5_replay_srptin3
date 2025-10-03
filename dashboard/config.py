"""
Configurações do Dashboard - FarmTech Solutions
Thresholds e parâmetros de alertas
"""

# ========================================
# THRESHOLDS DE ALERTAS
# ========================================

THRESHOLDS = {
    'temperatura': {
        'min_ideal': 18,      # °C - Mínimo ideal
        'max_ideal': 28,      # °C - Máximo ideal
        'min_alerta': 15,     # °C - Mínimo para alerta
        'max_alerta': 32,     # °C - Máximo para alerta
        'critico_baixo': 15,  # °C - Abaixo disso é crítico
        'critico_alto': 32,   # °C - Acima disso é crítico
    },
    'umidade': {
        'min_ideal': 50,      # % - Mínimo ideal
        'max_ideal': 80,      # % - Máximo ideal
        'min_alerta': 40,     # % - Mínimo para alerta
        'max_alerta': 90,     # % - Máximo para alerta
        'critico_baixo': 40,  # % - Abaixo disso é crítico
        'critico_alto': 90,   # % - Acima disso é crítico
    }
}

# ========================================
# CONFIGURAÇÕES DO DASHBOARD
# ========================================

DASHBOARD_CONFIG = {
    'page_title': 'FarmTech Solutions - Dashboard',
    'page_icon': '🌱',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded',
}

# Intervalo de refresh automático (segundos)
AUTO_REFRESH_INTERVAL = 30

# Número de leituras recentes a mostrar
NUM_RECENT_READINGS = 100

# Cores do dashboard
COLORS = {
    'normal': '#28a745',    # Verde
    'alerta': '#ffc107',    # Amarelo
    'critico': '#dc3545',   # Vermelho
    'primary': '#007bff',   # Azul
    'secondary': '#6c757d', # Cinza
}

# ========================================
# CONFIGURAÇÕES DE BANCO DE DADOS
# ========================================

# IMPORTANTE: Configure as variáveis de ambiente:
# export ORACLE_USER="seu_usuario"
# export ORACLE_PASSWORD="sua_senha"
# export ORACLE_DSN="localhost:1521/XE"

DB_CONFIG = {
    'user': None,      # Será lido de variável de ambiente
    'password': None,  # Será lido de variável de ambiente
    'dsn': None,       # Será lido de variável de ambiente
}

# Queries SQL pré-definidas
QUERIES = {
    'total_leituras': """
        SELECT COUNT(*) as total FROM Leitura
    """,

    'leituras_por_qualidade': """
        SELECT qualidade, COUNT(*) as total
        FROM Leitura
        GROUP BY qualidade
    """,

    'leituras_recentes': """
        SELECT
            id_leitura,
            id_sensor,
            tipo_sensor,
            valor,
            data_hora,
            qualidade,
            equipamento
        FROM Leitura
        ORDER BY data_hora DESC
        FETCH FIRST :num_rows ROWS ONLY
    """,

    'alertas_ativos': """
        SELECT
            a.id_alerta,
            a.id_leitura,
            a.descricao,
            a.nivel_severidade,
            a.data_hora_alerta,
            l.tipo_sensor,
            l.equipamento
        FROM Alerta a
        JOIN Leitura l ON a.id_leitura = l.id_leitura
        WHERE a.resolvido = 'N'
        ORDER BY a.data_hora_alerta DESC
        LIMIT 10
    """,

    'metricas_ml': """
        SELECT
            qualidade,
            COUNT(*) as total,
            ROUND(AVG(valor), 2) as media_valor
        FROM Leitura
        WHERE tipo_sensor IN ('Temperatura', 'Umidade')
        GROUP BY qualidade
    """,
}

# ========================================
# MENSAGENS DE ALERTA
# ========================================

ALERT_MESSAGES = {
    'critico_temperatura_alta': '🔥 Temperatura CRÍTICA! Acima de {valor}°C',
    'critico_temperatura_baixa': '❄️ Temperatura CRÍTICA! Abaixo de {valor}°C',
    'critico_umidade_alta': '💧 Umidade CRÍTICA! Acima de {valor}%',
    'critico_umidade_baixa': '🏜️ Umidade CRÍTICA! Abaixo de {valor}%',
    'alerta_temperatura': '⚠️ Temperatura em ALERTA: {valor}°C',
    'alerta_umidade': '⚠️ Umidade em ALERTA: {valor}%',
}

# ========================================
# CONFIGURAÇÕES DE GRÁFICOS
# ========================================

CHART_CONFIG = {
    'height': 400,
    'template': 'plotly_white',
    'font_size': 12,
}

# Cores para gráficos por equipamento
EQUIPMENT_COLORS = {
    'Estufa 1': '#FF6B6B',
    'Estufa 2': '#4ECDC4',
    'Estufa 3': '#45B7D1',
    'Estufa 4': '#96CEB4',
}
