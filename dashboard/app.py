"""
Dashboard Streamlit - FarmTech Solutions
Sistema de Monitoramento e Alertas
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import os
import random
import time
import math

# Importar módulos locais
from config import (
    DASHBOARD_CONFIG, THRESHOLDS, COLORS,
    AUTO_REFRESH_INTERVAL, NUM_RECENT_READINGS,
    ALERT_MESSAGES, CHART_CONFIG, SIMULATION_CYCLES, CYCLE_PROBABILITIES,
    ANOMALY_CONFIG, CRITICAL_ALERT_TYPES, ANOMALY_ICONS
)
from db_connection import DatabaseConnection

# ========================================
# CONFIGURAÇÃO DA PÁGINA
# ========================================

st.set_page_config(**DASHBOARD_CONFIG)

# ========================================
# ESTILO CSS CUSTOMIZADO
# ========================================

st.markdown("""
<style>
    /* Cards KPI com fundo sutil */
    .stMetric {
        background: rgba(40, 167, 69, 0.08);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(40, 167, 69, 0.2);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    /* Labels dos KPIs */
    [data-testid="stMetricLabel"] {
        color: #28a745 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }

    /* Valores dos KPIs */
    [data-testid="stMetricValue"] {
        color: #e8e8e8 !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
    }

    /* Delta dos KPIs */
    [data-testid="stMetricDelta"] {
        font-size: 1.2rem !important;
    }

    /* Alertas críticos dark mode */
    .alert-critico {
        background: rgba(220, 53, 69, 0.2);
        border: 2px solid #dc3545;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
    }

    /* Alertas de atenção dark mode */
    .alert-warning {
        background: rgba(255, 193, 7, 0.15);
        border: 2px solid #ffc107;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(255, 193, 7, 0.2);
    }

    /* Título principal */
    h1 {
        color: #28a745 !important;
        font-weight: 700 !important;
        text-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
    }

    /* Subtítulos sem borda */
    h2 {
        color: #ffffff !important;
        font-weight: 600 !important;
        margin-top: 30px !important;
        margin-bottom: 15px !important;
    }

    h3 {
        color: #adb5bd !important;
    }

    /* Tabs personalizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: none !important;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: rgba(40, 167, 69, 0.1);
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        border: 1px solid rgba(40, 167, 69, 0.3);
        border-bottom: none !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(40, 167, 69, 0.3) !important;
        border: 1px solid #28a745 !important;
        border-bottom: none !important;
    }

    /* Remover linha vermelha do tabpanel */
    .stTabs [data-baseweb="tab-panel"] {
        border-top: none !important;
    }

    /* Animação piscante para alertas */
    @keyframes blink-alerta {
        0%, 100% { background-color: rgba(255, 193, 7, 0.2); }
        50% { background-color: rgba(255, 193, 7, 0.5); }
    }

    @keyframes blink-critico {
        0%, 100% { background-color: rgba(220, 53, 69, 0.3); }
        50% { background-color: rgba(220, 53, 69, 0.6); }
    }

    /* Classes para linhas piscantes */
    .alerta-row {
        animation: blink-alerta 2s infinite;
    }

    .critico-row {
        animation: blink-critico 1s infinite;
    }
</style>
""", unsafe_allow_html=True)

# ========================================
# FUNÇÕES AUXILIARES
# ========================================

@st.cache_resource
def get_db_connection():
    """Obtém conexão com banco (com cache)"""
    db = DatabaseConnection()
    db.connect()
    return db

def get_quality(value, sensor_type):
    """Determina qualidade da leitura"""
    thresholds = THRESHOLDS[sensor_type]
    if value < thresholds['critico_baixo'] or value > thresholds['critico_alto']:
        return 'Critico'
    elif value < thresholds['min_ideal'] or value > thresholds['max_ideal']:
        return 'Alerta'
    else:
        return 'Normal'

def init_estufa_state():
    """Inicializa estado de cada estufa se não existir"""
    if 'estufa_state' not in st.session_state:
        st.session_state.estufa_state = {
            'Estufa 1': {
                'temp': 22.0,
                'humid': 65.0,
                'ciclo_ativo': 'estavel',
                'ciclo_contador': 0,
                'caracteristica': 'quente',  # Orientação norte, mais sol
                'offset_temp': 2.0,
                'offset_humid': -5.0,
                'cultura': 'Tomate',
                # Campos para detecção de anomalias
                'anomalia_sensor': None,
                'anomalia_contador': 0,
                'valores_historico': [],  # Últimas 5 leituras
                'valor_travado': None,
                'criticos_prolongados': 0,  # Contador de leituras críticas consecutivas
            },
            'Estufa 2': {
                'temp': 21.0,
                'humid': 68.0,
                'ciclo_ativo': 'estavel',
                'ciclo_contador': 0,
                'caracteristica': 'estavel',  # Climatização controlada
                'offset_temp': 0.0,
                'offset_humid': 0.0,
                'cultura': 'Alface',
                'anomalia_sensor': None,
                'anomalia_contador': 0,
                'valores_historico': [],
                'valor_travado': None,
                'criticos_prolongados': 0,
            },
            'Estufa 3': {
                'temp': 20.0,
                'humid': 72.0,
                'ciclo_ativo': 'estavel',
                'ciclo_contador': 0,
                'caracteristica': 'umida',  # Sistema de irrigação
                'offset_temp': -1.0,
                'offset_humid': 8.0,
                'cultura': 'Pepino',
                'anomalia_sensor': None,
                'anomalia_contador': 0,
                'valores_historico': [],
                'valor_travado': None,
                'criticos_prolongados': 0,
            },
            'Estufa 4': {
                'temp': 23.0,
                'humid': 62.0,
                'ciclo_ativo': 'estavel',
                'ciclo_contador': 0,
                'caracteristica': 'variavel',  # Ventilação natural
                'offset_temp': 1.0,
                'offset_humid': -3.0,
                'cultura': 'Morango',
                'anomalia_sensor': None,
                'anomalia_contador': 0,
                'valores_historico': [],
                'valor_travado': None,
                'criticos_prolongados': 0,
            }
        }

def generate_simulated_reading(estufa_nome):
    """Gera leitura simulada com ciclos progressivos de ~30 segundos"""
    init_estufa_state()

    state = st.session_state.estufa_state[estufa_nome]
    now = datetime.now()

    # Incrementar contador de ciclo
    state['ciclo_contador'] += 1

    # Se completou 6 leituras (30 segundos), escolher novo ciclo
    if state['ciclo_contador'] >= 6:
        state['ciclo_contador'] = 0
        # Escolher novo ciclo baseado nas probabilidades da característica da estufa
        caracteristica = state['caracteristica']
        probabilidades = CYCLE_PROBABILITIES[caracteristica]

        # Escolha ponderada do próximo ciclo
        ciclos = list(probabilidades.keys())
        pesos = list(probabilidades.values())
        state['ciclo_ativo'] = random.choices(ciclos, weights=pesos)[0]

    # Obter configuração do ciclo ativo
    ciclo_config = SIMULATION_CYCLES[state['ciclo_ativo']]

    # Calcular mudança gradual baseada no ciclo (por leitura de 5s)
    temp_delta_min, temp_delta_max = ciclo_config['temp_delta_per_5s']
    humid_delta_min, humid_delta_max = ciclo_config['humid_delta_per_5s']

    # Mudança base do ciclo
    temp_change = random.uniform(temp_delta_min, temp_delta_max)
    humid_change = random.uniform(humid_delta_min, humid_delta_max)

    # ========================================
    # EFEITOS DOS ATUADORES (sobrepõem ciclo natural)
    # ========================================

    # Extrair ID da estufa (ex: "Estufa 1" -> 1)
    estufa_id = int(estufa_nome.split()[1])

    # Importar simulador para verificar atuadores ativos
    from realtime_simulator import RealtimeSimulator
    db = get_db_connection()

    if db.db_type == 'sqlite':
        simulator = RealtimeSimulator(db.connection)
        active_actuators = simulator.controller.get_active_actuators()

        for actuator in active_actuators:
            if actuator['equipamento'] == estufa_nome:
                tipo = actuator['tipo']

                # Efeitos dos atuadores
                if tipo == 'Ventilador':
                    # Ventilador: resfria e seca
                    temp_change -= random.uniform(0.4, 0.6)
                    humid_change -= random.uniform(0.8, 1.2)
                elif tipo == 'Bomba':
                    # Bomba: umidifica e resfria levemente
                    humid_change += random.uniform(3.0, 5.0)
                    temp_change -= random.uniform(0.1, 0.2)

    # Aplicar mudanças
    new_temp = state['temp'] + temp_change
    new_humid = state['humid'] + humid_change

    # ========================================
    # SISTEMA DE ANOMALIAS DE SENSOR
    # ========================================

    anomalias_detectadas = []

    # Verificar se anomalias estão ativadas no toggle
    anomalias_ativas = st.session_state.get('anomalias_ativas', False)

    if anomalias_ativas:
        # Decrementar contador de anomalia ativa
        if state['anomalia_contador'] > 0:
            state['anomalia_contador'] -= 1
            if state['anomalia_contador'] == 0:
                state['anomalia_sensor'] = None
                state['valor_travado'] = None

        # Verificar se deve iniciar nova anomalia (apenas se não há uma ativa)
        if state['anomalia_sensor'] is None:
            # Chance de sensor com oscilação
            if random.random() < ANOMALY_CONFIG['sensor_oscilacao']['probabilidade']:
                state['anomalia_sensor'] = 'oscilacao'
                state['anomalia_contador'] = ANOMALY_CONFIG['sensor_oscilacao']['duracao_ciclos']
                anomalias_detectadas.append('SENSOR_OSCILANDO')

            # Chance de sensor travado
            elif random.random() < ANOMALY_CONFIG['sensor_travado']['probabilidade']:
                state['anomalia_sensor'] = 'travado'
                state['anomalia_contador'] = ANOMALY_CONFIG['sensor_travado']['duracao_ciclos']
                state['valor_travado'] = {'temp': new_temp, 'humid': new_humid}
                anomalias_detectadas.append('SENSOR_TRAVADO')

        # Aplicar efeitos da anomalia ativa
        if state['anomalia_sensor'] == 'oscilacao':
            # Oscilação: alterna entre valores erráticos
            oscilacao_tipo = random.choice(ANOMALY_CONFIG['sensor_oscilacao']['tipos'])
            if oscilacao_tipo == 'zerando':
                new_temp = 0.0
                new_humid = 0.0
            elif oscilacao_tipo == 'muito_alto':
                new_temp = new_temp * random.uniform(2.0, 2.5)
                new_humid = new_humid * random.uniform(1.5, 2.0)
            elif oscilacao_tipo == 'muito_baixo':
                new_temp = new_temp * random.uniform(0.3, 0.5)
                new_humid = new_humid * random.uniform(0.4, 0.6)

        elif state['anomalia_sensor'] == 'travado':
            # Sensor travado: mantém mesmo valor
            if state['valor_travado']:
                new_temp = state['valor_travado']['temp']
                new_humid = state['valor_travado']['humid']

        # Garantir limites físicos (permite valores impossíveis para detecção)
        new_temp = max(-5, min(50, new_temp))
        new_humid = max(0, min(110, new_humid))

        # Detectar leituras impossíveis
        if new_temp < 0 or new_temp > 45 or new_humid < 5 or new_humid > 100:
            if 'SENSOR_IMPOSSIVEL' not in anomalias_detectadas:
                anomalias_detectadas.append('SENSOR_IMPOSSIVEL')
    else:
        # Se anomalias estão desativadas, limpar estado de anomalia
        state['anomalia_sensor'] = None
        state['anomalia_contador'] = 0
        state['valor_travado'] = None

        # Garantir limites físicos normais
        new_temp = max(10, min(35, new_temp))
        new_humid = max(30, min(95, new_humid))

    # ========================================
    # DETECÇÃO DE EMERGÊNCIAS AMBIENTAIS
    # ========================================

    # Adicionar leitura atual ao histórico
    state['valores_historico'].append({
        'temp': new_temp,
        'humid': new_humid,
        'timestamp': now
    })

    # Manter apenas últimas 5 leituras (25 segundos)
    if len(state['valores_historico']) > 5:
        state['valores_historico'].pop(0)

    # Verificar emergências apenas se anomalias estão ativadas
    if anomalias_ativas and len(state['valores_historico']) >= 3:
        # Temperatura subindo muito rápido (últimos 15s = 3 leituras)
        temp_change_15s = new_temp - state['valores_historico'][-3]['temp']
        if temp_change_15s > ANOMALY_CONFIG['emergencia_ambiental']['temp_rapida_subida']:
            anomalias_detectadas.append('EMERGENCIA_INCENDIO')

        # Umidade subindo muito rápido sem bomba ligada
        humid_change_15s = new_humid - state['valores_historico'][-3]['humid']

        # Verificar se bomba está ligada
        bomba_ligada = False
        if db.db_type == 'sqlite':
            from realtime_simulator import RealtimeSimulator
            simulator = RealtimeSimulator(db.connection)
            active_actuators = simulator.controller.get_active_actuators()
            for actuator in active_actuators:
                if actuator['equipamento'] == estufa_nome and actuator['tipo'] == 'Bomba':
                    bomba_ligada = True
                    break

        if humid_change_15s > ANOMALY_CONFIG['emergencia_ambiental']['umid_rapida_subida'] and not bomba_ligada:
            anomalias_detectadas.append('EMERGENCIA_INFILTRACAO')

        # Ambos caindo juntos (vazamento/porta aberta)
        if temp_change_15s < ANOMALY_CONFIG['emergencia_ambiental']['ambos_caindo_delta'] and \
           humid_change_15s < ANOMALY_CONFIG['emergencia_ambiental']['ambos_caindo_delta']:
            anomalias_detectadas.append('EMERGENCIA_VAZAMENTO')

    # Detectar valores críticos prolongados (apenas se anomalias ativas)
    temp_quality = get_quality(new_temp, 'temperatura')
    humid_quality = get_quality(new_humid, 'umidade')

    if anomalias_ativas:
        if temp_quality == 'Critico' or humid_quality == 'Critico':
            state['criticos_prolongados'] += 1
            # Se mais de 24 leituras críticas (2 minutos)
            if state['criticos_prolongados'] >= 24:
                anomalias_detectadas.append('EMERGENCIA_PROLONGADA')
        else:
            state['criticos_prolongados'] = 0
    else:
        state['criticos_prolongados'] = 0

    # Atualizar estado
    state['temp'] = new_temp
    state['humid'] = new_humid

    return {
        'temperatura': {'valor': round(new_temp, 1), 'qualidade': temp_quality, 'timestamp': now},
        'umidade': {'valor': round(new_humid, 1), 'qualidade': humid_quality, 'timestamp': now},
        'estufa': estufa_nome,
        'ciclo_ativo': state['ciclo_ativo'],
        'ciclo_contador': state['ciclo_contador'],
        'anomalias': anomalias_detectadas,
        'anomalia_ativa': state['anomalia_sensor']
    }

def insert_simulated_reading(db):
    """Insere leitura simulada realista no banco SQLite"""
    if db.db_type != 'sqlite':
        return None

    try:
        import sqlite3
        conn = db.connection
        cursor = conn.cursor()

        # Pares de sensores (temperatura, umidade) por estufa
        sensor_map = {
            'Estufa 1': {'temp_sensor': 1, 'humid_sensor': 2, 'equipamento': 1},
            'Estufa 2': {'temp_sensor': 4, 'humid_sensor': 5, 'equipamento': 2},
            'Estufa 3': {'temp_sensor': 6, 'humid_sensor': 7, 'equipamento': 3},
            'Estufa 4': {'temp_sensor': 9, 'humid_sensor': 10, 'equipamento': 4},
        }

        # Randomizar estufa para esta leitura
        estufa_nome = random.choice(list(sensor_map.keys()))
        config = sensor_map[estufa_nome]

        # Gerar leitura realista com continuidade
        reading = generate_simulated_reading(estufa_nome)

        # Inserir temperatura
        cursor.execute("""
            INSERT INTO Leitura (id_sensor, valor, data_hora, qualidade)
            VALUES (?, ?, ?, ?)
        """, (config['temp_sensor'],
              reading['temperatura']['valor'],
              reading['temperatura']['timestamp'].isoformat(), reading['temperatura']['qualidade']))

        temp_id = cursor.lastrowid

        # Inserir umidade
        cursor.execute("""
            INSERT INTO Leitura (id_sensor, valor, data_hora, qualidade)
            VALUES (?, ?, ?, ?)
        """, (config['humid_sensor'],
              reading['umidade']['valor'],
              reading['umidade']['timestamp'].isoformat(), reading['umidade']['qualidade']))

        humid_id = cursor.lastrowid

        # Criar alertas com informação do ciclo se houver
        ciclo_info = f" (Ciclo: {reading['ciclo_ativo'].title()})" if 'ciclo_ativo' in reading else ""

        if reading['temperatura']['qualidade'] in ['Alerta', 'Critico']:
            tipo_alerta = f"{'Crítico' if reading['temperatura']['qualidade'] == 'Critico' else 'Alerta'} Temperatura"
            mensagem = f"{estufa_nome}: Temperatura em nível de {reading['temperatura']['qualidade'].lower()}{ciclo_info}"
            cursor.execute("""
                INSERT INTO Alerta (id_leitura, tipo_alerta, mensagem, data_alerta, resolvido)
                VALUES (?, ?, ?, ?, 'N')
            """, (temp_id, tipo_alerta, mensagem, reading['temperatura']['timestamp'].isoformat()))

        if reading['umidade']['qualidade'] in ['Alerta', 'Critico']:
            tipo_alerta = f"{'Crítico' if reading['umidade']['qualidade'] == 'Critico' else 'Alerta'} Umidade"
            mensagem = f"{estufa_nome}: Umidade em nível de {reading['umidade']['qualidade'].lower()}{ciclo_info}"
            cursor.execute("""
                INSERT INTO Alerta (id_leitura, tipo_alerta, mensagem, data_alerta, resolvido)
                VALUES (?, ?, ?, ?, 'N')
            """, (humid_id, tipo_alerta, mensagem, reading['umidade']['timestamp'].isoformat()))

        # ========================================
        # REGISTRAR ANOMALIAS CRÍTICAS
        # ========================================

        if 'anomalias' in reading and reading['anomalias']:
            for anomalia_tipo in reading['anomalias']:
                # Criar alerta crítico
                descricao = CRITICAL_ALERT_TYPES.get(anomalia_tipo, 'Anomalia detectada')
                icon = ANOMALY_ICONS.get(anomalia_tipo, '⚠️')

                # Determinar qual sensor (temperatura ou umidade)
                sensor_afetado = temp_id if 'TEMP' in anomalia_tipo or 'INCENDIO' in anomalia_tipo else humid_id

                mensagem = f"{icon} {estufa_nome}: {descricao}"

                # Adicionar detalhes específicos
                if anomalia_tipo == 'SENSOR_OSCILANDO':
                    mensagem += f" - Temp: {reading['temperatura']['valor']:.1f}°C, Umid: {reading['umidade']['valor']:.1f}%"
                elif anomalia_tipo == 'SENSOR_IMPOSSIVEL':
                    if reading['temperatura']['valor'] < 0 or reading['temperatura']['valor'] > 45:
                        mensagem += f" - Temperatura impossível: {reading['temperatura']['valor']:.1f}°C"
                    if reading['umidade']['valor'] < 5 or reading['umidade']['valor'] > 100:
                        mensagem += f" - Umidade impossível: {reading['umidade']['valor']:.1f}%"
                elif anomalia_tipo == 'EMERGENCIA_INCENDIO':
                    mensagem += f" - Temperatura: {reading['temperatura']['valor']:.1f}°C (subindo >3°C em 15s)"
                elif anomalia_tipo == 'EMERGENCIA_INFILTRACAO':
                    mensagem += f" - Umidade: {reading['umidade']['valor']:.1f}% (subindo >10% em 15s)"
                elif anomalia_tipo == 'EMERGENCIA_VAZAMENTO':
                    mensagem += f" - Temp e Umid caindo rapidamente"

                # Inserir alerta crítico
                cursor.execute("""
                    INSERT INTO Alerta (id_leitura, tipo_alerta, mensagem, data_alerta, resolvido)
                    VALUES (?, ?, ?, ?, 'N')
                """, (sensor_afetado, f"Crítico - {anomalia_tipo}", mensagem,
                      reading['temperatura']['timestamp'].isoformat()))

                # Atualizar saúde do sensor
                cursor.execute("""
                    UPDATE Sensor_Health
                    SET status_saude = 'Falha',
                        num_leituras_anomalas = num_leituras_anomalas + 1,
                        observacoes = ?,
                        ultima_verificacao = ?
                    WHERE id_sensor = ?
                """, (descricao, reading['temperatura']['timestamp'].isoformat(), config['temp_sensor']))

                cursor.execute("""
                    UPDATE Sensor_Health
                    SET status_saude = 'Falha',
                        num_leituras_anomalas = num_leituras_anomalas + 1,
                        observacoes = ?,
                        ultima_verificacao = ?
                    WHERE id_sensor = ?
                """, (descricao, reading['temperatura']['timestamp'].isoformat(), config['humid_sensor']))

                # Registrar evento crítico na tabela de eventos
                from actuator_logic import ActuatorController
                controller = ActuatorController(conn)
                controller.registrar_evento_critico(
                    tipo_evento=anomalia_tipo,
                    equipamento_id=config['equipamento'],
                    sensor_id=config['temp_sensor'] if 'TEMP' in anomalia_tipo or 'INCENDIO' in anomalia_tipo else config['humid_sensor'],
                    descricao=mensagem
                )

        conn.commit()
        return reading

    except Exception as e:
        st.error(f"Erro ao inserir leitura simulada: {e}")
        return None

def display_kpi_card(title, value, delta=None, color="primary"):
    """Exibe card de KPI"""
    st.metric(
        label=title,
        value=value,
        delta=delta
    )

def create_time_series_chart(df, selected_equipamentos=None):
    """Cria gráfico de série temporal separado por equipamento"""
    if df.empty:
        st.warning("Sem dados para exibir")
        return

    # Filtrar por equipamentos selecionados
    if selected_equipamentos:
        df = df[df['EQUIPAMENTO'].isin(selected_equipamentos)].copy()

    if df.empty:
        st.warning("Sem dados para os equipamentos selecionados")
        return

    # Importar cores de equipamentos
    from config import EQUIPMENT_COLORS

    fig = go.Figure()

    # Obter lista de equipamentos únicos
    equipamentos = sorted(df['EQUIPAMENTO'].unique())

    # Adicionar linhas de temperatura por equipamento
    df_temp = df[df['TIPO_SENSOR'] == 'Temperatura'].copy()
    for equipamento in equipamentos:
        df_eq = df_temp[df_temp['EQUIPAMENTO'] == equipamento]
        if not df_eq.empty:
            # Cor do equipamento (com fallback)
            color = EQUIPMENT_COLORS.get(equipamento, '#999999')

            # Criar texto customizado para hover
            hover_text = [
                f"<b>{equipamento}</b><br>" +
                f"Temperatura: {valor:.1f}°C<br>" +
                f"Qualidade: {qual}<br>" +
                f"Data: {data.strftime('%d/%m/%Y %H:%M:%S')}"
                for valor, qual, data in zip(
                    df_eq['VALOR'],
                    df_eq['QUALIDADE'],
                    pd.to_datetime(df_eq['DATA_HORA'], format='mixed')
                )
            ]

            fig.add_trace(go.Scatter(
                x=df_eq['DATA_HORA'],
                y=df_eq['VALOR'],
                name=f'{equipamento} - Temp',
                mode='lines+markers',
                line=dict(color=color, width=2),
                marker=dict(size=5, symbol='circle'),
                hovertext=hover_text,
                hoverinfo='text'
            ))

    # Linhas de threshold temperatura com labels organizados
    if not df_temp.empty:
        # Zona ideal (faixa verde)
        fig.add_hrect(
            y0=THRESHOLDS['temperatura']['min_ideal'],
            y1=THRESHOLDS['temperatura']['max_ideal'],
            fillcolor="rgba(40, 167, 69, 0.1)",
            layer="below",
            line_width=0,
        )
        # Linha ideal máxima
        fig.add_hline(
            y=THRESHOLDS['temperatura']['max_ideal'],
            line_dash="dash",
            line_color="rgba(40, 167, 69, 0.5)",
            line_width=1
        )
        # Linha ideal mínima
        fig.add_hline(
            y=THRESHOLDS['temperatura']['min_ideal'],
            line_dash="dash",
            line_color="rgba(40, 167, 69, 0.5)",
            line_width=1
        )
        # Linha crítica alta
        fig.add_hline(
            y=THRESHOLDS['temperatura']['critico_alto'],
            line_dash="dot",
            line_color="rgba(220, 53, 69, 0.6)",
            line_width=1
        )

    # Adicionar linhas de umidade por equipamento (eixo Y secundário)
    df_umid = df[df['TIPO_SENSOR'] == 'Umidade'].copy()
    for equipamento in equipamentos:
        df_eq = df_umid[df_umid['EQUIPAMENTO'] == equipamento]
        if not df_eq.empty:
            # Cor do equipamento (um pouco mais escura para diferenciar)
            base_color = EQUIPMENT_COLORS.get(equipamento, '#999999')

            # Criar texto customizado para hover
            hover_text = [
                f"<b>{equipamento}</b><br>" +
                f"Umidade: {valor:.1f}%<br>" +
                f"Qualidade: {qual}<br>" +
                f"Data: {data.strftime('%d/%m/%Y %H:%M:%S')}"
                for valor, qual, data in zip(
                    df_eq['VALOR'],
                    df_eq['QUALIDADE'],
                    pd.to_datetime(df_eq['DATA_HORA'], format='mixed')
                )
            ]

            fig.add_trace(go.Scatter(
                x=df_eq['DATA_HORA'],
                y=df_eq['VALOR'],
                name=f'{equipamento} - Umid',
                mode='lines+markers',
                line=dict(color=base_color, width=2, dash='dot'),
                marker=dict(size=5, symbol='square'),
                yaxis='y2',
                hovertext=hover_text,
                hoverinfo='text'
            ))

    # Zona ideal umidade com labels organizados
    if not df_umid.empty:
        # Faixa verde zona ideal
        fig.add_hrect(
            y0=THRESHOLDS['umidade']['min_ideal'],
            y1=THRESHOLDS['umidade']['max_ideal'],
            fillcolor="rgba(40, 167, 69, 0.08)",
            layer="below",
            line_width=0,
            yref='y2'
        )
        # Linha ideal máxima umidade
        fig.add_hline(
            y=THRESHOLDS['umidade']['max_ideal'],
            line_dash="dash",
            line_color="rgba(40, 167, 69, 0.4)",
            line_width=1,
            yref='y2'
        )
        # Linha ideal mínima umidade
        fig.add_hline(
            y=THRESHOLDS['umidade']['min_ideal'],
            line_dash="dash",
            line_color="rgba(40, 167, 69, 0.4)",
            line_width=1,
            yref='y2'
        )

    # ========================================
    # ADICIONAR ESTADOS DOS ATUADORES
    # ========================================

    # Buscar acionamentos no período do gráfico
    if not df.empty:
        min_data = pd.to_datetime(df['DATA_HORA'], format='mixed').min()
        max_data = pd.to_datetime(df['DATA_HORA'], format='mixed').max()

        # Conectar ao banco para buscar acionamentos
        db = get_db_connection()
        if db.db_type == 'sqlite':
            import sqlite3
            cursor = db.connection.cursor()

            # Buscar acionamentos que se sobrepõem ao período
            cursor.execute("""
                SELECT
                    a.data_hora_inicio,
                    a.data_hora_fim,
                    at.tipo,
                    'Estufa ' || at.id_equipamento as equipamento,
                    a.motivo
                FROM Acionamento a
                JOIN Atuador at ON a.id_atuador = at.id_atuador
                WHERE (
                    (a.data_hora_inicio BETWEEN ? AND ?)
                    OR (a.data_hora_fim BETWEEN ? AND ?)
                    OR (a.data_hora_inicio <= ? AND (a.data_hora_fim >= ? OR a.data_hora_fim IS NULL))
                )
                ORDER BY a.data_hora_inicio
            """, (
                min_data.isoformat(), max_data.isoformat(),
                min_data.isoformat(), max_data.isoformat(),
                min_data.isoformat(), max_data.isoformat()
            ))

            acionamentos = cursor.fetchall()

            # Cores para atuadores
            actuator_colors = {
                'Bomba': 'rgba(33, 150, 243, 0.15)',      # Azul translúcido
                'Ventilador': 'rgba(76, 175, 80, 0.15)'   # Verde translúcido
            }

            # Adicionar shapes para cada acionamento
            shapes = []
            annotations = []

            for acionamento in acionamentos:
                inicio_str, fim_str, tipo, equipamento, motivo = acionamento

                # Se ainda está ativo (fim é None), usar data máxima do gráfico
                inicio = pd.to_datetime(inicio_str, format='mixed')
                fim = pd.to_datetime(fim_str, format='mixed') if fim_str else max_data

                # Filtrar por equipamentos selecionados
                if selected_equipamentos and equipamento not in selected_equipamentos:
                    continue

                color = actuator_colors.get(tipo, 'rgba(128, 128, 128, 0.1)')

                # Adicionar shape (retângulo vertical)
                shapes.append(dict(
                    type="rect",
                    xref="x",
                    yref="paper",
                    x0=inicio,
                    y0=0,
                    x1=fim,
                    y1=1,
                    fillcolor=color,
                    layer="below",
                    line_width=0,
                ))

                # Adicionar anotação pequena (apenas ícone)
                icon = '💦' if tipo == 'Bomba' else '💨'
                annotations.append(dict(
                    x=inicio,
                    y=1.02,
                    xref="x",
                    yref="paper",
                    text=f"{icon}",
                    showarrow=False,
                    font=dict(size=10),
                    hovertext=f"{equipamento}: {tipo} ligado<br>{motivo}"
                ))

            # Aplicar shapes e annotations ao layout
            fig.update_layout(shapes=shapes, annotations=annotations)

    # Layout
    fig.update_layout(
        title='Evolução Temporal - Temperatura e Umidade por Equipamento',
        xaxis_title='Data/Hora',
        yaxis_title='Temperatura (°C)',
        yaxis2=dict(
            title='Umidade (%)',
            overlaying='y',
            side='right'
        ),
        height=CHART_CONFIG['height'],
        template=CHART_CONFIG['template'],
        hovermode='closest',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.15
        )
    )

    # Adicionar annotations para thresholds de temperatura (lado direito)
    if not df_temp.empty:
        fig.add_annotation(
            x=1.02, xref="paper", xanchor="left",
            y=THRESHOLDS['temperatura']['max_ideal'], yref="y",
            text="28°C Ideal", showarrow=False,
            font=dict(size=9, color="#28a745")
        )
        fig.add_annotation(
            x=1.02, xref="paper", xanchor="left",
            y=THRESHOLDS['temperatura']['min_ideal'], yref="y",
            text="18°C Ideal", showarrow=False,
            font=dict(size=9, color="#28a745")
        )
        fig.add_annotation(
            x=1.02, xref="paper", xanchor="left",
            y=THRESHOLDS['temperatura']['critico_alto'], yref="y",
            text="32°C Crítico", showarrow=False,
            font=dict(size=9, color="#dc3545")
        )

    # Adicionar annotations para thresholds de umidade (lado esquerdo)
    if not df_umid.empty:
        fig.add_annotation(
            x=-0.02, xref="paper", xanchor="right",
            y=THRESHOLDS['umidade']['max_ideal'], yref="y2",
            text="80% Ideal", showarrow=False,
            font=dict(size=9, color="#28a745")
        )
        fig.add_annotation(
            x=-0.02, xref="paper", xanchor="right",
            y=THRESHOLDS['umidade']['min_ideal'], yref="y2",
            text="50% Ideal", showarrow=False,
            font=dict(size=9, color="#28a745")
        )

    st.plotly_chart(fig, use_container_width=True)

def create_distribution_chart(df):
    """Cria gráfico de distribuição por equipamento"""
    if df.empty:
        st.warning("Sem dados para exibir")
        return

    # Mapear IDs para nomes de equipamento
    equipamento_map = {
        '1': 'Estufa 1',
        '2': 'Estufa 2',
        '3': 'Estufa 3',
        '4': 'Estufa 4',
        '5': 'Estufa 5'
    }

    df_copy = df.copy()
    df_copy['EQUIPAMENTO'] = df_copy['EQUIPAMENTO'].astype(str).map(equipamento_map).fillna(df_copy['EQUIPAMENTO'])

    # Contar leituras por equipamento e qualidade
    dist = df_copy.groupby(['EQUIPAMENTO', 'QUALIDADE']).size().reset_index(name='count')

    fig = px.bar(
        dist,
        x='EQUIPAMENTO',
        y='count',
        color='QUALIDADE',
        title='Distribuição de Leituras por Equipamento',
        labels={'count': 'Quantidade', 'EQUIPAMENTO': 'Equipamento'},
        color_discrete_map={
            'Normal': COLORS['normal'],
            'Alerta': COLORS['alerta'],
            'Critico': COLORS['critico']
        },
        height=CHART_CONFIG['height']
    )

    st.plotly_chart(fig, use_container_width=True)

def create_heatmap_chart(df):
    """Cria heatmap de alertas por hora do dia"""
    if df.empty:
        st.warning("Sem dados para exibir")
        return

    # Extrair hora do dia (formato misto de datetime)
    df['hora'] = pd.to_datetime(df['DATA_HORA'], format='mixed').dt.hour

    # Filtrar apenas alertas e críticos
    df_alertas = df[df['QUALIDADE'].isin(['Alerta', 'Critico'])]

    if df_alertas.empty:
        st.info("Nenhum alerta registrado no período")
        return

    # Criar matriz de contagem
    heatmap_data = df_alertas.groupby(['EQUIPAMENTO', 'hora']).size().reset_index(name='count')
    heatmap_pivot = heatmap_data.pivot(index='EQUIPAMENTO', columns='hora', values='count').fillna(0)

    fig = px.imshow(
        heatmap_pivot,
        title='Heatmap de Alertas por Hora do Dia',
        labels=dict(x='Hora do Dia', y='Equipamento', color='Nº Alertas'),
        color_continuous_scale='Reds',
        height=CHART_CONFIG['height']
    )

    st.plotly_chart(fig, use_container_width=True)

def display_alert_banner(alertas_df):
    """Exibe alertas críticos com detalhes e plano de ação"""
    if alertas_df.empty:
        return

    # Buscar alertas críticos não resolvidos
    db = get_db_connection()
    if db.db_type != 'sqlite':
        return

    cursor = db.connection.cursor()
    cursor.execute("""
        SELECT
            a.mensagem,
            a.tipo_alerta,
            ts.nome as tipo_sensor,
            l.id_sensor,
            e.nome as equipamento,
            l.valor,
            a.data_alerta
        FROM Alerta a
        JOIN Leitura l ON a.id_leitura = l.id_leitura
        JOIN Sensor s ON l.id_sensor = s.id_sensor
        JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
        JOIN Equipamento e ON s.id_equipamento = e.id_equipamento
        WHERE a.resolvido = 'N'
            AND a.tipo_alerta LIKE '%Crítico%'
            AND datetime(a.data_alerta) >= datetime('now', '-30 minutes')
        ORDER BY a.data_alerta DESC
        LIMIT 5
    """)

    alertas_criticos = cursor.fetchall()

    if not alertas_criticos:
        return

    st.markdown("### 🚨 Alertas Críticos Ativos")

    for mensagem, tipo_alerta, tipo_sensor, id_sensor, equipamento, valor, data_alerta in alertas_criticos:
        # Determinar plano de ação baseado no tipo de sensor e valor
        if tipo_sensor == 'Temperatura':
            if valor > 32:
                problema = f"Temperatura crítica alta: {valor:.1f}°C (acima de 32°C)"
                plano_acao = "🔧 **Ação Sugerida:** Verificar ventilador, aumentar ventilação e verificar sistema de resfriamento"
            else:
                problema = f"Temperatura crítica baixa: {valor:.1f}°C (abaixo de 15°C)"
                plano_acao = "🔧 **Ação Sugerida:** Verificar aquecimento, isolar estufa e verificar sensor"
        elif tipo_sensor == 'Umidade':
            if valor > 90:
                problema = f"Umidade crítica alta: {valor:.1f}% (acima de 90%)"
                plano_acao = "🔧 **Ação Sugerida:** Aumentar ventilação, verificar vazamentos e reduzir irrigação"
            else:
                problema = f"Umidade crítica baixa: {valor:.1f}% (abaixo de 40%)"
                plano_acao = "🔧 **Ação Sugerida:** Verificar sistema de irrigação, aumentar pulverização e verificar sensor"
        else:
            problema = f"{tipo_sensor}: Valor crítico {valor:.1f}"
            plano_acao = "🔧 **Ação Sugerida:** Verificar sensor e equipamento"

        # Exibir card do alerta
        st.error(f"""
**{equipamento}** - Sensor #{id_sensor} ({tipo_sensor})

⚠️ **Problema:** {problema}

{plano_acao}

📍 **Localização:** {equipamento}
⏰ **Detectado em:** {pd.to_datetime(data_alerta, format='mixed').strftime('%d/%m/%Y %H:%M:%S')}
        """, icon="🚨")

def display_estufa_status():
    """Exibe status das estufas em formato horizontal"""
    init_estufa_state()

    st.markdown("### 🏭 Status das Estufas")

    # Grid horizontal (4 colunas para 4 estufas)
    cols = st.columns(4)

    estufas = list(st.session_state.estufa_state.items())

    # Obter conexão com banco para consultar alertas e atuadores
    db = get_db_connection()

    for idx, (estufa_nome, state) in enumerate(estufas):
        with cols[idx]:
            _render_estufa_card(estufa_nome, state, db)

def _render_estufa_card(estufa_nome, state, db):
    """Renderiza card individual de uma estufa"""

    # Extrair ID da estufa (ex: "Estufa 1" -> 1)
    estufa_id = int(estufa_nome.split()[1])

    # Cor única para todas as estufas
    estufa_color = '#28a745'  # Verde padrão

    # Buscar última leitura do banco para esta estufa
    temp_atual = state['temp']
    humid_atual = state['humid']

    if db.db_type == 'sqlite':
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT l.valor, ts.nome
            FROM Leitura l
            JOIN Sensor s ON l.id_sensor = s.id_sensor
            JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
            WHERE s.id_equipamento = ?
            ORDER BY l.data_hora DESC
            LIMIT 2
        """, (estufa_id,))
        leituras_recentes = cursor.fetchall()

        # Atualizar valores com dados do banco
        for valor, tipo in leituras_recentes:
            if tipo == 'Temperatura':
                temp_atual = float(valor)
                state['temp'] = temp_atual  # Sincronizar session_state
            elif tipo == 'Umidade':
                humid_atual = float(valor)
                state['humid'] = humid_atual  # Sincronizar session_state

    # Determinar status para o badge
    temp_quality = get_quality(temp_atual, 'temperatura')
    humid_quality = get_quality(humid_atual, 'umidade')

    # Status geral (pior qualidade prevalece)
    if temp_quality == 'Critico' or humid_quality == 'Critico':
        status_icon = '🔴'
        status_text = 'CRÍTICO'
        status_bg = '#dc3545'
    elif temp_quality == 'Alerta' or humid_quality == 'Alerta':
        status_icon = '⚠️'
        status_text = 'ALERTA'
        status_bg = '#ffc107'
    else:
        status_icon = '✅'
        status_text = 'NORMAL'
        status_bg = '#28a745'

    # Buscar atuadores ativos e alertas para esta estufa
    atuadores_ativos = []
    alertas_ativos = []

    if db.db_type == 'sqlite':
        cursor = db.connection.cursor()

        # Buscar atuadores ativos
        cursor.execute("""
            SELECT tipo_atuador, motivo
            FROM Acionamentos_Ativos
            WHERE id_equipamento = ?
        """, (estufa_id,))
        atuadores_ativos = cursor.fetchall()

        # Buscar alertas ativos desta estufa (últimos 15 minutos)
        cursor.execute("""
            SELECT a.tipo_alerta, a.mensagem
            FROM Alerta a
            JOIN Leitura l ON a.id_leitura = l.id_leitura
            JOIN Sensor s ON l.id_sensor = s.id_sensor
            WHERE s.id_equipamento = ?
                AND a.resolvido = 'N'
                AND datetime(a.data_alerta) >= datetime('now', '-15 minutes')
            ORDER BY a.data_alerta DESC
            LIMIT 2
        """, (estufa_id,))
        alertas_ativos = cursor.fetchall()

    # Obter cultura
    cultura = state.get('cultura', 'N/A')

    # Renderizar card
    st.markdown(f"""
    <div style="
        background: rgba(0, 0, 0, 0.2);
        border: 2px solid {estufa_color};
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
    ">
        <h4 style="margin: 0 0 5px 0; color: {estufa_color};">{estufa_nome}</h4>
        <p style="margin: 0 0 10px 0; color: #999; font-size: 0.85em;">🌱 {cultura}</p>
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span>🌡️ Temperatura:</span>
            <strong>{temp_atual:.1f}°C</strong>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span>💧 Umidade:</span>
            <strong>{humid_atual:.1f}%</strong>
        </div>
        <div style="
            background: {status_bg}33;
            padding: 5px;
            border-radius: 5px;
            text-align: center;
            font-weight: 600;
            color: {status_bg};
        ">
            {status_icon} {status_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Exibir alertas ativos
    if alertas_ativos:
        st.markdown("---")
        st.markdown("**🚨 Alertas Ativos:**")
        for tipo_alerta, mensagem in alertas_ativos:
            if 'Crítico' in tipo_alerta:
                st.error(f"🔴 {mensagem}", icon="🚨")
            else:
                st.warning(f"⚠️ {mensagem}", icon="⚠️")

    # Exibir ações tomadas (atuadores ativos)
    if atuadores_ativos:
        st.markdown("---")
        st.markdown("**⚡ Ações Ativas:**")
        for tipo_atuador, motivo in atuadores_ativos:
            if tipo_atuador == 'Bomba':
                st.success(f"💦 **Bomba Ligada**", icon="✅")
                st.caption(f"↳ {motivo}")
            elif tipo_atuador == 'Ventilador':
                st.success(f"💨 **Ventilador Ligado**", icon="✅")
                st.caption(f"↳ {motivo}")

    # Ciclo ativo (se houver)
    if state.get('ciclo_ativo'):
        ciclo_icons = {
            'aquecimento': '🔥',
            'resfriamento': '❄️',
            'secagem': '💨',
            'umidificacao': '💦',
            'estavel': '✅'
        }
        icon = ciclo_icons.get(state['ciclo_ativo'], '⚙️')
        ciclo_nome = state['ciclo_ativo'].replace('_', ' ').title()
        contador = state.get('ciclo_contador', 0)
        tempo_restante = (6 - contador) * 5
        st.caption(f"{icon} {ciclo_nome} ({contador}/6 - ~{tempo_restante}s)")

    # Anomalia ativa (se houver)
    if state.get('anomalia_sensor'):
        st.markdown("---")
        anomalia_tipo = state['anomalia_sensor']
        contador_anomalia = state.get('anomalia_contador', 0)

        if anomalia_tipo == 'oscilacao':
            st.error(f"📡 **Sensor Oscilando!**", icon="🚨")
            st.caption(f"↳ Leituras erráticas (~{contador_anomalia * 5}s restantes)")
        elif anomalia_tipo == 'travado':
            st.error(f"⏸️ **Sensor Travado!**", icon="🚨")
            st.caption(f"↳ Mesmo valor (~{contador_anomalia * 5}s restantes)")

# ========================================
# NOVOS COMPONENTES DO DASHBOARD
# ========================================

def display_timeline_eventos(db):
    """Timeline de eventos em tempo real"""
    from realtime_simulator import RealtimeSimulator
    from actuator_logic import ActuatorController

    simulator = RealtimeSimulator(db.connection)
    controller = ActuatorController(db.connection)

    # Simular manutenção em sensores com falha (5% de chance por refresh)
    if random.random() < 0.05:
        sensores_problemas = controller.get_sensor_health_summary()
        for sensor in sensores_problemas:
            if sensor['status'] == 'Falha' and sensor['leituras_anomalas'] >= 3:
                # Simular manutenção
                controller.simular_manutencao_sensor(sensor['id_sensor'])
                break  # Apenas um sensor por vez

    eventos_atuadores = simulator.get_actuator_timeline(limit=15)
    eventos_criticos = controller.get_eventos_criticos(limit=15, apenas_nao_resolvidos=False)

    st.markdown("### ⏱️ Timeline de Eventos")

    # Debug: mostrar quantidade de eventos
    st.caption(f"📊 {len(eventos_atuadores)} eventos de atuadores | {len(eventos_criticos)} eventos críticos")

    # Combinar e ordenar todos os eventos por timestamp
    todos_eventos = []

    # Adicionar eventos de atuadores
    for evento in eventos_atuadores:
        timestamp = pd.to_datetime(evento['timestamp'], format='mixed')
        todos_eventos.append({
            'timestamp': timestamp,
            'tipo': 'atuador',
            'evento': evento
        })

    # Adicionar eventos críticos
    for evento in eventos_criticos:
        timestamp = pd.to_datetime(evento['data_hora'], format='mixed')
        todos_eventos.append({
            'timestamp': timestamp,
            'tipo': 'critico',
            'evento': evento
        })

    # Ordenar por timestamp (mais recente primeiro)
    todos_eventos.sort(key=lambda x: x['timestamp'], reverse=True)

    if not todos_eventos:
        st.info("Nenhum evento registrado ainda")
        return

    # Exibir eventos (limitar a 10)
    for item in todos_eventos[:10]:
        hora = item['timestamp'].strftime('%H:%M:%S')
        data = item['timestamp'].strftime('%d/%m')

        if item['tipo'] == 'atuador':
            evento = item['evento']
            if evento['tipo_evento'] == 'Ligado':
                icon = '🟢' if evento['tipo'] == 'Bomba' else '🟡'
                st.markdown(f"`{data} {hora}` {icon} **{evento['equipamento']}**: {evento['tipo']} ligado - {evento['motivo']}")
            else:
                icon = '⚫'
                duracao_min = evento['duracao_segundos'] // 60
                st.markdown(f"`{data} {hora}` {icon} **{evento['equipamento']}**: {evento['tipo']} desligado ({duracao_min}min, {evento['economia_kwh']:.2f} kWh economizado)")

        elif item['tipo'] == 'critico':
            evento = item['evento']
            tipo_evento = evento['tipo_evento']

            # Ícones específicos por tipo
            if tipo_evento == 'MANUTENCAO_SENSOR':
                icon = '🔧'
                resolvido = '✅'
                st.success(f"`{data} {hora}` {icon} {resolvido} **{evento['equipamento']}**: {evento['descricao']}", icon="🔧")
            else:
                icon = ANOMALY_ICONS.get(tipo_evento, '🚨')
                resolvido = '✅' if evento['resolvido'] == 'S' else '🔴'
                st.error(f"`{data} {hora}` {icon} {resolvido} **{evento['equipamento']}**: {evento['descricao']}", icon="🚨")

def display_tendencia_previsao(db):
    """Gráfico de tendência e previsão simples"""
    st.markdown("### 📈 Tendência e Previsão")

    # Buscar últimas 50 leituras
    cursor = db.connection.cursor()
    cursor.execute("""
        SELECT
            data_hora,
            AVG(CASE WHEN id_sensor IN (1,4,6,9) THEN valor END) as temp_media,
            AVG(CASE WHEN id_sensor IN (2,5,7,10) THEN valor END) as umid_media
        FROM Leitura
        WHERE data_hora >= datetime('now', '-2 hours')
        GROUP BY data_hora
        ORDER BY data_hora
    """)

    rows = cursor.fetchall()

    if not rows:
        st.info("Dados insuficientes para previsão")
        return

    df = pd.DataFrame(rows, columns=['data_hora', 'temp_media', 'umid_media'])
    df['data_hora'] = pd.to_datetime(df['data_hora'], format='mixed')

    # Média móvel simples (últimos 10 pontos)
    df['temp_ma'] = df['temp_media'].rolling(window=10, min_periods=1).mean()
    df['umid_ma'] = df['umid_media'].rolling(window=10, min_periods=1).mean()

    # Previsão linear simples (próximos 30 min)
    if len(df) >= 10:
        # Usar últimos 10 pontos para tendência
        recent = df.tail(10)
        temp_slope = (recent['temp_media'].iloc[-1] - recent['temp_media'].iloc[0]) / 10
        umid_slope = (recent['umid_media'].iloc[-1] - recent['umid_media'].iloc[0]) / 10

        # Projetar 6 pontos futuros (30 min = 6x5min)
        last_time = df['data_hora'].iloc[-1]
        future_times = [last_time + pd.Timedelta(minutes=5*i) for i in range(1, 7)]
        future_temp = [df['temp_media'].iloc[-1] + temp_slope * i for i in range(1, 7)]
        future_umid = [df['umid_media'].iloc[-1] + umid_slope * i for i in range(1, 7)]

        df_future = pd.DataFrame({
            'data_hora': future_times,
            'temp_previsao': future_temp,
            'umid_previsao': future_umid
        })
    else:
        df_future = pd.DataFrame()

    # Gráfico
    fig = go.Figure()

    # Temperatura real
    fig.add_trace(go.Scatter(
        x=df['data_hora'], y=df['temp_media'],
        name='Temp Média', mode='lines',
        line=dict(color='#FF6B6B', width=2)
    ))

    # Temperatura média móvel
    fig.add_trace(go.Scatter(
        x=df['data_hora'], y=df['temp_ma'],
        name='Temp Tendência', mode='lines',
        line=dict(color='#FF6B6B', width=3, dash='dash')
    ))

    # Previsão temperatura
    if not df_future.empty:
        fig.add_trace(go.Scatter(
            x=df_future['data_hora'], y=df_future['temp_previsao'],
            name='Temp Previsão', mode='lines',
            line=dict(color='#FF6B6B', width=2, dash='dot')
        ))

    fig.update_layout(
        title='Tendência Média (Todas as Estufas)',
        xaxis_title='Tempo',
        yaxis_title='Temperatura (°C)',
        height=350
    )

    st.plotly_chart(fig, use_container_width=True)

def display_comparativo_estufas(db):
    """Comparativo e ranking entre estufas"""
    from realtime_simulator import RealtimeSimulator

    st.markdown("### 🏆 Ranking de Eficiência das Estufas")

    simulator = RealtimeSimulator(db.connection)
    ranking = simulator.get_equipment_efficiency_ranking()

    if not ranking:
        st.info("Dados insuficientes para ranking")
        return

    # Tabela formatada
    for item in ranking:
        rank_icon = {1: '🥇', 2: '🥈', 3: '🥉', 4: '4️⃣'}.get(item['ranking'], '•')

        col1, col2, col3, col4 = st.columns([1, 3, 2, 2])

        with col1:
            st.markdown(f"### {rank_icon}")

        with col2:
            st.markdown(f"**{item['equipamento']}**")
            st.caption(f"{item['pct_normal']:.1f}% Normal")

        with col3:
            st.metric("Acionamentos", item['num_acionamentos'])

        with col4:
            st.metric("Economia", f"R$ {item['economia_reais']:.2f}")

        st.markdown("---")

def display_saude_sensores(db):
    """Monitoramento de saúde dos sensores"""
    from actuator_logic import ActuatorController

    st.markdown("### 🔧 Saúde dos Sensores")

    controller = ActuatorController(db.connection)
    sensores_problemas = controller.get_sensor_health_summary()

    if not sensores_problemas:
        st.success("✅ Todos os sensores operando normalmente!")
        return

    for sensor in sensores_problemas:
        status_colors = {
            'Atenção': '#ffc107',
            'Crítico': '#ff9800',
            'Falha': '#f44336'
        }
        color = status_colors.get(sensor['status'], '#999')

        # Determinar ícone baseado no tipo de problema
        icon = '⚠️'
        if sensor['status'] == 'Falha':
            icon = '🚨'
        elif sensor['status'] == 'Crítico':
            icon = '⚠️'
        else:
            icon = '⚡'

        # Extrair tipo de anomalia das observações se houver
        observacoes = sensor.get('observacoes', '')

        st.markdown(f"""
        <div style="border-left: 4px solid {color}; padding: 15px; margin: 10px 0; background: rgba(0,0,0,0.1); border-radius: 8px;">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 1.5em; margin-right: 10px;">{icon}</span>
                <strong style="font-size: 1.1em;">{sensor['equipamento']} - Sensor #{sensor['id_sensor']} ({sensor['tipo_sensor']})</strong>
            </div>
            <div style="margin-left: 40px;">
                <div style="margin-bottom: 5px;">
                    📊 <strong>Status:</strong> <span style="color: {color}; font-weight: bold;">{sensor['status']}</span>
                </div>
                <div style="margin-bottom: 5px;">
                    🔴 <strong>Alertas críticos:</strong> {sensor['alertas_criticos']}
                </div>
                <div style="margin-bottom: 5px;">
                    📡 <strong>Leituras anômalas:</strong> {sensor['leituras_anomalas']}
                </div>
                <div style="margin-top: 10px; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px;">
                    💬 <strong>Observações:</strong> {observacoes}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_metricas_economia(db):
    """Métricas consolidadas de economia"""
    from actuator_logic import ActuatorController

    st.markdown("### 💰 Economia de Energia")

    controller = ActuatorController(db.connection)

    # Métricas para diferentes períodos
    hoje = controller.get_economy_stats(periodo_dias=1)
    semana = controller.get_economy_stats(periodo_dias=7)
    mes = controller.get_economy_stats(periodo_dias=30)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "💵 Economia Hoje",
            f"R$ {hoje['economia_reais']:.2f}",
            f"{hoje['economia_kwh']:.2f} kWh"
        )
        st.caption(f"{hoje['total_acionamentos']} acionamentos")

    with col2:
        st.metric(
            "📅 Economia Semana",
            f"R$ {semana['economia_reais']:.2f}",
            f"{semana['economia_kwh']:.2f} kWh"
        )
        st.caption(f"{semana['total_acionamentos']} acionamentos")

    with col3:
        st.metric(
            "📊 Economia Mês",
            f"R$ {mes['economia_reais']:.2f}",
            f"{mes['economia_kwh']:.2f} kWh"
        )
        st.caption(f"{mes['total_acionamentos']} acionamentos")

    # Projeção anual
    projecao_anual = mes['economia_reais'] * 12
    st.info(f"📈 **Projeção anual:** R$ {projecao_anual:.2f} de economia")

def display_alertas_priorizados(db):
    """Alertas ativos com priorização"""
    st.markdown("### 🚨 Alertas Ativos Priorizados")

    cursor = db.connection.cursor()
    cursor.execute("""
        SELECT
            a.id_alerta,
            a.tipo_alerta,
            a.mensagem,
            a.data_alerta,
            l.id_sensor,
            e.nome as equipamento,
            ts.nome as tipo_sensor
        FROM Alerta a
        JOIN Leitura l ON a.id_leitura = l.id_leitura
        JOIN Sensor s ON l.id_sensor = s.id_sensor
        JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
        JOIN Equipamento e ON s.id_equipamento = e.id_equipamento
        WHERE a.resolvido = 'N'
        ORDER BY
            CASE
                WHEN a.tipo_alerta LIKE '%Crítico%' THEN 1
                ELSE 2
            END,
            a.data_alerta DESC
        LIMIT 10
    """)

    alertas = cursor.fetchall()

    if not alertas:
        st.success("✅ Nenhum alerta ativo no momento!")
        return

    for alerta in alertas:
        id_alerta, tipo_alerta, mensagem, data, id_sensor, equipamento, tipo_sensor = alerta

        critico = 'Crítico' in tipo_alerta
        color = '#dc3545' if critico else '#ffc107'
        icon = '🔴' if critico else '⚠️'

        timestamp = pd.to_datetime(data, format='mixed').strftime('%d/%m %H:%M')

        col1, col2 = st.columns([5, 1])

        with col1:
            st.markdown(f"{icon} **{equipamento}** ({tipo_sensor}) - {timestamp}")
            st.caption(mensagem)

        with col2:
            if st.button("✓", key=f"resolve_{id_alerta}", help="Resolver alerta"):
                cursor.execute("UPDATE Alerta SET resolvido = 'S' WHERE id_alerta = ?", (id_alerta,))
                db.connection.commit()
                st.rerun()

# ========================================
# APLICAÇÃO PRINCIPAL
# ========================================

def main():
    """Função principal do dashboard"""

    # Header
    st.title("🌱 FarmTech Solutions")
    st.markdown("### Dashboard de Monitoramento IoT e Machine Learning")

    # Conectar ao banco
    db = get_db_connection()

    # Auto-refresh de 5 segundos automático
    st_autorefresh(interval=5000, key="datarefresh")

    # Inserir leitura simulada (apenas para SQLite)
    if db.db_type == 'sqlite':
        reading = insert_simulated_reading(db)
        if reading:
            # Mostrar toasts separados para temperatura e umidade
            estufa = reading['estufa']

            # Toast para temperatura
            if reading['temperatura']['qualidade'] == 'Critico':
                st.toast(f"🚨 {estufa}: Temperatura CRÍTICA! {reading['temperatura']['valor']:.1f}°C", icon="🔴")
            elif reading['temperatura']['qualidade'] == 'Alerta':
                st.toast(f"⚠️ {estufa}: Temperatura em Alerta! {reading['temperatura']['valor']:.1f}°C", icon="⚠️")

            # Toast para umidade
            if reading['umidade']['qualidade'] == 'Critico':
                st.toast(f"🚨 {estufa}: Umidade CRÍTICA! {reading['umidade']['valor']:.1f}%", icon="🔴")
            elif reading['umidade']['qualidade'] == 'Alerta':
                st.toast(f"⚠️ {estufa}: Umidade em Alerta! {reading['umidade']['valor']:.1f}%", icon="⚠️")

    # Sidebar - Simples com menus apenas
    with st.sidebar:
        st.image("assets/farmtech_logo.svg", width=200)
        st.markdown("---")

        # Menu de navegação
        st.markdown("### 📊 Menu")
        menu_option = st.radio(
            "Navegação",
            ["Dashboard", "Alertas", "Relatórios", "Configurações"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Configurações de Simulação
        st.markdown("### ⚙️ Simulação")

        # Toggle para ativar/desativar anomalias e alertas críticos
        if 'anomalias_ativas' not in st.session_state:
            st.session_state.anomalias_ativas = False

        anomalias_toggle = st.toggle(
            "🚨 Anomalias e Alertas Críticos",
            value=st.session_state.anomalias_ativas,
            help="Ativa/desativa a simulação de anomalias críticas nos sensores e atuadores"
        )
        st.session_state.anomalias_ativas = anomalias_toggle

        if anomalias_toggle:
            st.caption("🔴 Anomalias ATIVADAS")
        else:
            st.caption("🟢 Apenas ciclos normais")

        st.markdown("---")

        # Informações básicas
        st.markdown("### ℹ️ Info")
        st.caption(f"**Atualização:**  \n{datetime.now().strftime('%H:%M:%S')}")

        # Modo de operação (compacto)
        if db.use_mock:
            st.caption("⚠️ Modo Simulação")
        elif db.db_type == 'sqlite':
            st.caption("💾 SQLite Local")
        else:
            st.caption("✅ Oracle DB")

        st.caption("🔄 Auto-refresh: 5s")

    # ========================================
    # SEÇÃO 1: KPIs
    # ========================================

    st.markdown("## 📈 Indicadores Principais")

    kpis = db.get_kpis()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        display_kpi_card(
            "Total de Leituras",
            f"{kpis['total_leituras']:,}",
            delta="📊"
        )

    with col2:
        normal_pct = kpis['percentuais'].get('normal', {}).get('percentage', 0)
        display_kpi_card(
            "% Normal",
            f"{normal_pct}%",
            delta="✅"
        )

    with col3:
        alerta_pct = kpis['percentuais'].get('alerta', {}).get('percentage', 0)
        display_kpi_card(
            "% Alerta",
            f"{alerta_pct}%",
            delta="⚠️"
        )

    with col4:
        critico_pct = kpis['percentuais'].get('critico', {}).get('percentage', 0)
        display_kpi_card(
            "% Crítico",
            f"{critico_pct}%",
            delta="🔴"
        )

    st.markdown("---")

    # ========================================
    # SEÇÃO 2: STATUS DAS ESTUFAS (Horizontal)
    # ========================================

    display_estufa_status()

    st.markdown("---")

    # ========================================
    # SEÇÃO 3: ALERTAS CRÍTICOS
    # ========================================

    alertas_df = db.get_alertas_ativos()
    display_alert_banner(alertas_df)

    # ========================================
    # SEÇÃO 4: GRÁFICOS PRINCIPAIS
    # ========================================

    st.markdown("## 📊 Análise de Dados")

    leituras_df = db.get_leituras_recentes(NUM_RECENT_READINGS)

    # Tabs principais para gráficos
    tab1, tab2, tab3 = st.tabs([
        "📈 Série Temporal",
        "📊 Distribuição",
        "🔥 Heatmap"
    ])

    with tab1:
        # Seletor de UMA estufa por vez
        if not leituras_df.empty:
            equipamentos_disponiveis = sorted(leituras_df['EQUIPAMENTO'].dropna().unique())
            if equipamentos_disponiveis:
                estufa_selecionada = st.selectbox(
                    "🏭 Selecione a estufa:",
                    options=equipamentos_disponiveis,
                    help="Visualize os dados de uma estufa por vez"
                )

                # Passar apenas a estufa selecionada como lista
                create_time_series_chart(leituras_df, [estufa_selecionada])
            else:
                create_time_series_chart(leituras_df)
        else:
            create_time_series_chart(leituras_df)

    with tab2:
        create_distribution_chart(leituras_df)

    with tab3:
        create_heatmap_chart(leituras_df)

    # ========================================
    # SEÇÃO 5: MONITORAMENTO E ECONOMIA
    # ========================================

    st.markdown("---")
    st.markdown("## 🔍 Monitoramento em Tempo Real")

    col1, col2 = st.columns(2)

    with col1:
        # Timeline de Eventos
        display_timeline_eventos(db)

    with col2:
        # Saúde dos Sensores
        display_saude_sensores(db)

    # ========================================
    # SEÇÃO 6: ECONOMIA
    # ========================================

    st.markdown("---")
    st.markdown("## 💰 Economia de Energia")

    # Métricas de Economia
    display_metricas_economia(db)

    st.markdown("---")

    # Comparativo de Estufas
    display_comparativo_estufas(db)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        FarmTech Solutions - Sprint 3 | Fase 5 - FIAP<br>
        🤖 Powered by Machine Learning & Oracle Database
    </div>
    """, unsafe_allow_html=True)


# ========================================
# EXECUÇÃO
# ========================================

if __name__ == "__main__":
    main()
