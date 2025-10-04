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
            l.id_leitura,
            l.id_sensor,
            ts.nome as tipo_sensor,
            l.valor,
            l.data_hora,
            l.qualidade,
            e.nome as equipamento
        FROM Leitura l
        JOIN Sensor s ON l.id_sensor = s.id_sensor
        JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
        JOIN Equipamento e ON s.id_equipamento = e.id_equipamento
        ORDER BY l.data_hora DESC
        FETCH FIRST :num_rows ROWS ONLY
    """,

    'alertas_ativos': """
        SELECT
            a.id_alerta,
            a.id_leitura,
            a.mensagem,
            a.tipo_alerta,
            a.data_alerta,
            ts.nome as tipo_sensor,
            e.nome as equipamento
        FROM Alerta a
        JOIN Leitura l ON a.id_leitura = l.id_leitura
        JOIN Sensor s ON l.id_sensor = s.id_sensor
        JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
        JOIN Equipamento e ON s.id_equipamento = e.id_equipamento
        WHERE a.resolvido = 'N'
        ORDER BY a.data_alerta DESC
        LIMIT 10
    """,

    'metricas_ml': """
        SELECT
            l.qualidade,
            COUNT(*) as total,
            ROUND(AVG(l.valor), 2) as media_valor
        FROM Leitura l
        JOIN Sensor s ON l.id_sensor = s.id_sensor
        JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
        WHERE ts.nome IN ('Temperatura', 'Umidade')
        GROUP BY l.qualidade
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

# ========================================
# CONFIGURAÇÕES DE CICLOS DE SIMULAÇÃO
# ========================================

SIMULATION_CYCLES = {
    'aquecimento': {
        'temp_delta_per_5s': (0.4, 0.7),      # Temperatura sobe gradualmente
        'humid_delta_per_5s': (-2.5, -1.5),   # Umidade cai gradualmente
        'duracao_ciclos': 6,                   # 6 leituras = 30s
    },
    'resfriamento': {
        'temp_delta_per_5s': (-0.5, -0.3),    # Temperatura cai gradualmente
        'humid_delta_per_5s': (1.0, 1.5),     # Umidade sobe gradualmente
        'duracao_ciclos': 6,
    },
    'secagem': {
        'temp_delta_per_5s': (0.2, 0.4),      # Temperatura sobe levemente
        'humid_delta_per_5s': (-3.0, -2.0),   # Umidade cai rapidamente
        'duracao_ciclos': 6,
    },
    'umidificacao': {
        'temp_delta_per_5s': (-0.3, -0.2),    # Temperatura cai levemente
        'humid_delta_per_5s': (2.5, 4.0),     # Umidade sobe rapidamente
        'duracao_ciclos': 6,
    },
    'estavel': {
        'temp_delta_per_5s': (-0.1, 0.1),     # Variação mínima
        'humid_delta_per_5s': (-0.5, 0.5),    # Variação mínima
        'duracao_ciclos': 6,
    }
}

# Probabilidades de cada ciclo por característica de estufa
CYCLE_PROBABILITIES = {
    'quente': {      # Estufa 1 - orientação norte, mais sol
        'aquecimento': 0.35,
        'resfriamento': 0.15,
        'secagem': 0.25,
        'umidificacao': 0.10,
        'estavel': 0.15,
    },
    'estavel': {     # Estufa 2 - climatização controlada
        'aquecimento': 0.15,
        'resfriamento': 0.15,
        'secagem': 0.15,
        'umidificacao': 0.15,
        'estavel': 0.40,
    },
    'umida': {       # Estufa 3 - sistema de irrigação
        'aquecimento': 0.10,
        'resfriamento': 0.20,
        'secagem': 0.15,
        'umidificacao': 0.35,
        'estavel': 0.20,
    },
    'variavel': {    # Estufa 4 - ventilação natural
        'aquecimento': 0.25,
        'resfriamento': 0.25,
        'secagem': 0.20,
        'umidificacao': 0.15,
        'estavel': 0.15,
    }
}

# ========================================
# CONFIGURAÇÕES DE DETECÇÃO DE ANOMALIAS
# ========================================

ANOMALY_CONFIG = {
    'sensor_oscilacao': {
        'probabilidade': 0.03,  # 3% chance por leitura de iniciar anomalia
        'duracao_ciclos': 8,    # Dura 8 leituras (40 segundos)
        'tipos': ['zerando', 'muito_alto', 'muito_baixo']
    },
    'sensor_travado': {
        'probabilidade': 0.02,  # 2% chance por leitura
        'duracao_ciclos': 10,   # Dura 10 leituras (50 segundos)
    },
    'atuador_falha': {
        'probabilidade': 0.05,  # 5% chance quando atuador está ligado
        'duracao_ciclos': 6,    # Dura 6 leituras (30 segundos)
    },
    'emergencia_ambiental': {
        'temp_rapida_subida': 3.0,   # >3°C em 15s (3 leituras) é crítico
        'umid_rapida_subida': 10.0,  # >10% em 15s é crítico
        'ambos_caindo_delta': -2.0,  # Ambos caindo >2 unidades é anômalo
    }
}

# Tipos de alertas críticos
CRITICAL_ALERT_TYPES = {
    'SENSOR_OSCILANDO': 'Sensor com leituras erráticas',
    'SENSOR_TRAVADO': 'Sensor travado no mesmo valor',
    'SENSOR_IMPOSSIVEL': 'Leitura impossível detectada',
    'ATUADOR_VENTILADOR_FALHA': 'Ventilador não está resfriando',
    'ATUADOR_BOMBA_FALHA': 'Bomba não está irrigando',
    'EMERGENCIA_INCENDIO': 'Temperatura subindo muito rápido',
    'EMERGENCIA_INFILTRACAO': 'Umidade subindo sem irrigação',
    'EMERGENCIA_VAZAMENTO': 'Temperatura e umidade caindo',
    'EMERGENCIA_PROLONGADA': 'Valores críticos por tempo prolongado',
}

# Ícones para tipos de anomalias
ANOMALY_ICONS = {
    'SENSOR_OSCILANDO': '📡',
    'SENSOR_TRAVADO': '⏸️',
    'SENSOR_IMPOSSIVEL': '❌',
    'ATUADOR_VENTILADOR_FALHA': '💨',
    'ATUADOR_BOMBA_FALHA': '💦',
    'EMERGENCIA_INCENDIO': '🔥',
    'EMERGENCIA_INFILTRACAO': '🌊',
    'EMERGENCIA_VAZAMENTO': '💨',
    'EMERGENCIA_PROLONGADA': '⏰',
    'MANUTENCAO_SENSOR': '🔧',
}
