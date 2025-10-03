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
    ALERT_MESSAGES, CHART_CONFIG
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
                'evento': None,
                'evento_duracao': 0,
                'caracteristica': 'quente',  # Orientação norte, mais sol
                'offset_temp': 2.0,
                'offset_humid': -5.0
            },
            'Estufa 2': {
                'temp': 21.0,
                'humid': 68.0,
                'evento': None,
                'evento_duracao': 0,
                'caracteristica': 'estavel',  # Climatização controlada
                'offset_temp': 0.0,
                'offset_humid': 0.0
            },
            'Estufa 3': {
                'temp': 20.0,
                'humid': 72.0,
                'evento': None,
                'evento_duracao': 0,
                'caracteristica': 'umida',  # Sistema de irrigação
                'offset_temp': -1.0,
                'offset_humid': 8.0
            },
            'Estufa 4': {
                'temp': 23.0,
                'humid': 62.0,
                'evento': None,
                'evento_duracao': 0,
                'caracteristica': 'variavel',  # Ventilação natural
                'offset_temp': 1.0,
                'offset_humid': -3.0
            }
        }

def generate_simulated_reading(estufa_nome):
    """Gera leitura simulada realista com continuidade temporal"""
    init_estufa_state()

    state = st.session_state.estufa_state[estufa_nome]
    now = datetime.now()
    hour = now.hour
    minute = now.minute

    # Temperatura alvo baseada na hora (ciclo diário suave)
    # Usa seno para transição suave
    hour_decimal = hour + minute / 60.0
    # Pico às 14h (hour 14), mínimo às 5h (hour 5)
    temp_cycle = 23 + 5 * math.sin((hour_decimal - 5) / 24 * 2 * math.pi - math.pi/2)

    # Aplicar características da estufa
    temp_target = temp_cycle + state['offset_temp']
    humid_target = 70 - (temp_target - 23) * 1.5 + state['offset_humid']

    # Processar eventos em andamento
    if state['evento']:
        state['evento_duracao'] -= 1

        if state['evento'] == 'porta_aberta':
            # Porta aberta: temperatura cai, umidade varia
            temp_target -= 3
            humid_target += 10
        elif state['evento'] == 'falha_climatizacao':
            # Falha AC: temperatura sobe
            temp_target += 8
            humid_target -= 5
        elif state['evento'] == 'irrigacao':
            # Irrigação: umidade sobe
            humid_target += 15
            temp_target -= 1
        elif state['evento'] == 'ventilacao':
            # Ventilação: umidade cai
            humid_target -= 12
            temp_target -= 2

        # Finalizar evento
        if state['evento_duracao'] <= 0:
            state['evento'] = None

    # Chance de novo evento (2% por leitura)
    if not state['evento'] and random.random() < 0.02:
        eventos = ['porta_aberta', 'falha_climatizacao', 'irrigacao', 'ventilacao']
        state['evento'] = random.choice(eventos)
        state['evento_duracao'] = random.randint(3, 8)  # Dura 3-8 leituras (15-40s)

    # Variação gradual com inércia térmica
    # Mudança máxima de ±0.8°C e ±3% por leitura
    max_temp_change = 0.8 if not state['evento'] else 1.5
    max_humid_change = 3.0 if not state['evento'] else 5.0

    # Tendência em direção ao alvo + pequeno ruído
    temp_diff = temp_target - state['temp']
    humid_diff = humid_target - state['humid']

    # Aplicar inércia (só move 20% em direção ao alvo + ruído)
    temp_change = temp_diff * 0.2 + random.uniform(-0.3, 0.3)
    humid_change = humid_diff * 0.2 + random.uniform(-1.5, 1.5)

    # Limitar mudança máxima
    temp_change = max(-max_temp_change, min(max_temp_change, temp_change))
    humid_change = max(-max_humid_change, min(max_humid_change, humid_change))

    # Aplicar mudança
    new_temp = state['temp'] + temp_change
    new_humid = state['humid'] + humid_change

    # Garantir limites físicos
    new_temp = max(10, min(40, new_temp))
    new_humid = max(25, min(100, new_humid))

    # Atualizar estado
    state['temp'] = new_temp
    state['humid'] = new_humid

    temp_quality = get_quality(new_temp, 'temperatura')
    humid_quality = get_quality(new_humid, 'umidade')

    return {
        'temperatura': {'valor': round(new_temp, 1), 'qualidade': temp_quality, 'timestamp': now},
        'umidade': {'valor': round(new_humid, 1), 'qualidade': humid_quality, 'timestamp': now},
        'estufa': estufa_nome,
        'evento': state['evento']
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
            'Estufa 1': (1, 2),
            'Estufa 2': (4, 5),
            'Estufa 3': (6, 7),
            'Estufa 4': (9, 10),
        }

        # Randomizar estufa para esta leitura
        estufa_nome = random.choice(list(sensor_map.keys()))
        temp_sensor, humid_sensor = sensor_map[estufa_nome]

        # Gerar leitura realista com continuidade
        reading = generate_simulated_reading(estufa_nome)

        # Inserir temperatura
        cursor.execute("""
            INSERT INTO Leitura_Base (id_sensor, valor, data_hora, qualidade)
            VALUES (?, ?, ?, ?)
        """, (temp_sensor, reading['temperatura']['valor'],
              reading['temperatura']['timestamp'].isoformat(), reading['temperatura']['qualidade']))

        temp_id = cursor.lastrowid

        # Inserir umidade
        cursor.execute("""
            INSERT INTO Leitura_Base (id_sensor, valor, data_hora, qualidade)
            VALUES (?, ?, ?, ?)
        """, (humid_sensor, reading['umidade']['valor'],
              reading['umidade']['timestamp'].isoformat(), reading['umidade']['qualidade']))

        humid_id = cursor.lastrowid

        # Criar alertas com informação do evento se houver
        evento_info = f" ({reading['evento'].replace('_', ' ').title()})" if reading['evento'] else ""

        if reading['temperatura']['qualidade'] in ['Alerta', 'Critico']:
            tipo_alerta = f"{'Crítico' if reading['temperatura']['qualidade'] == 'Critico' else 'Alerta'} Temperatura"
            mensagem = f"{estufa_nome}: Temperatura em nível de {reading['temperatura']['qualidade'].lower()}{evento_info}"
            cursor.execute("""
                INSERT INTO Alerta_Base (id_leitura, tipo_alerta, mensagem, data_alerta, resolvido)
                VALUES (?, ?, ?, ?, 'N')
            """, (temp_id, tipo_alerta, mensagem, reading['temperatura']['timestamp'].isoformat()))

        if reading['umidade']['qualidade'] in ['Alerta', 'Critico']:
            tipo_alerta = f"{'Crítico' if reading['umidade']['qualidade'] == 'Critico' else 'Alerta'} Umidade"
            mensagem = f"{estufa_nome}: Umidade em nível de {reading['umidade']['qualidade'].lower()}{evento_info}"
            cursor.execute("""
                INSERT INTO Alerta_Base (id_leitura, tipo_alerta, mensagem, data_alerta, resolvido)
                VALUES (?, ?, ?, ?, 'N')
            """, (humid_id, tipo_alerta, mensagem, reading['umidade']['timestamp'].isoformat()))

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
                    pd.to_datetime(df_eq['DATA_HORA'])
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

    # Linhas de threshold temperatura
    if not df_temp.empty:
        fig.add_hline(
            y=THRESHOLDS['temperatura']['max_ideal'],
            line_dash="dash",
            line_color="rgba(40, 167, 69, 0.5)",
            annotation_text="Temp Ideal Max",
            annotation_position="right"
        )
        fig.add_hline(
            y=THRESHOLDS['temperatura']['min_ideal'],
            line_dash="dash",
            line_color="rgba(40, 167, 69, 0.5)",
            annotation_text="Temp Ideal Min",
            annotation_position="right"
        )
        fig.add_hline(
            y=THRESHOLDS['temperatura']['critico_alto'],
            line_dash="dot",
            line_color="rgba(220, 53, 69, 0.5)",
            annotation_text="Temp Crítico Alto",
            annotation_position="right"
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
                    pd.to_datetime(df_eq['DATA_HORA'])
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

    # Linhas de threshold umidade
    if not df_umid.empty:
        fig.add_hline(
            y=THRESHOLDS['umidade']['max_ideal'],
            line_dash="dash",
            line_color="rgba(40, 167, 69, 0.3)",
            annotation_text="Umid Ideal Max",
            annotation_position="left",
            yref='y2'
        )
        fig.add_hline(
            y=THRESHOLDS['umidade']['min_ideal'],
            line_dash="dash",
            line_color="rgba(40, 167, 69, 0.3)",
            annotation_text="Umid Ideal Min",
            annotation_position="left",
            yref='y2'
        )

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
    """Exibe banner de alerta crítico"""
    if alertas_df.empty:
        return

    criticos = alertas_df[alertas_df['NIVEL_SEVERIDADE'] == 'Critico']

    if not criticos.empty:
        st.markdown("""
        <div class="alert-critico">
            <h2 style="color: #721c24; margin: 0;">🚨 ALERTAS CRÍTICOS ATIVOS!</h2>
            <p style="margin: 10px 0 0 0;">Ação imediata necessária em {} equipamento(s)</p>
        </div>
        """.format(len(criticos)), unsafe_allow_html=True)

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
            # Mostrar toast com nova leitura
            if reading['temperatura']['qualidade'] == 'Critico' or reading['umidade']['qualidade'] == 'Critico':
                st.toast(f"🚨 ALERTA CRÍTICO! Temp: {reading['temperatura']['valor']}°C, Umid: {reading['umidade']['valor']}%", icon="🔴")
            elif reading['temperatura']['qualidade'] == 'Alerta' or reading['umidade']['qualidade'] == 'Alerta':
                st.toast(f"⚠️ Alerta! Temp: {reading['temperatura']['valor']}°C, Umid: {reading['umidade']['valor']}%", icon="⚠️")

    # Sidebar
    with st.sidebar:
        st.image("assets/farmtech_logo.svg", width=200)
        st.markdown("---")
        st.markdown("### ⚙️ Configurações")

        # Simulação ativa
        st.success("🔄 Simulação Ativa  \n(Atualiza a cada 5s)")

        st.markdown("---")
        st.markdown("### 📊 Informações")
        st.markdown(f"**Última atualização:**  \n{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

        # Modo de operação
        if db.use_mock:
            st.warning("⚠️ Modo Simulação  \n(Sem conexão Oracle)")
        elif db.db_type == 'sqlite':
            st.info("💾 SQLite Local")
        else:
            st.success("✅ Conectado ao Oracle")

        # Status das estufas
        st.markdown("---")
        st.markdown("### 🏭 Status das Estufas")

        init_estufa_state()
        for estufa_nome, state in st.session_state.estufa_state.items():
            with st.expander(f"{estufa_nome}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🌡️ Temp", f"{state['temp']:.1f}°C")
                with col2:
                    st.metric("💧 Umid", f"{state['humid']:.1f}%")

                if state['evento']:
                    evento_icons = {
                        'porta_aberta': '🚪',
                        'falha_climatizacao': '🔥',
                        'irrigacao': '💦',
                        'ventilacao': '💨'
                    }
                    icon = evento_icons.get(state['evento'], '⚠️')
                    evento_nome = state['evento'].replace('_', ' ').title()
                    st.warning(f"{icon} **{evento_nome}**  \n(~{state['evento_duracao'] * 5}s restantes)")
                else:
                    st.success("✅ Normal")

    # ========================================
    # SEÇÃO 1: KPIs
    # ========================================

    st.markdown("## 📈 Indicadores Principais")

    kpis = db.get_kpis()

    col1, col2, col3, col4, col5 = st.columns(5)

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

    with col5:
        display_kpi_card(
            "Alertas Ativos",
            kpis['alertas_ativos'],
            delta="🚨" if kpis['alertas_ativos'] > 0 else "✅"
        )

    # ========================================
    # SEÇÃO 2: ALERTAS CRÍTICOS
    # ========================================

    alertas_df = db.get_alertas_ativos()
    display_alert_banner(alertas_df)

    # ========================================
    # SEÇÃO 3: GRÁFICOS
    # ========================================

    st.markdown("## 📊 Análise de Dados")

    leituras_df = db.get_leituras_recentes(NUM_RECENT_READINGS)

    # Tabs para diferentes visualizações
    tab1, tab2, tab3 = st.tabs(["📈 Série Temporal", "📊 Distribuição", "🔥 Heatmap"])

    with tab1:
        # Filtro de equipamentos
        if not leituras_df.empty:
            equipamentos_disponiveis = sorted(leituras_df['EQUIPAMENTO'].dropna().unique())
            if equipamentos_disponiveis:
                col_filter1, col_filter2 = st.columns([3, 1])
                with col_filter1:
                    equipamentos_selecionados = st.multiselect(
                        "🔍 Filtrar por equipamento:",
                        options=equipamentos_disponiveis,
                        default=equipamentos_disponiveis,
                        help="Selecione quais estufas você deseja visualizar no gráfico"
                    )
                with col_filter2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("↻ Resetar", key="reset_filter"):
                        st.rerun()

                create_time_series_chart(leituras_df, equipamentos_selecionados)
            else:
                create_time_series_chart(leituras_df)
        else:
            create_time_series_chart(leituras_df)

    with tab2:
        create_distribution_chart(leituras_df)

    with tab3:
        create_heatmap_chart(leituras_df)

    # ========================================
    # SEÇÃO 4: TABELA DE ALERTAS
    # ========================================

    if not alertas_df.empty:
        st.markdown("## 🚨 Alertas Ativos")

        # Filtro por severidade
        filtro_severidade = st.multiselect(
            "Filtrar por Severidade",
            options=['Alerta', 'Critico'],
            default=['Alerta', 'Critico']
        )

        alertas_filtrados = alertas_df[alertas_df['NIVEL_SEVERIDADE'].isin(filtro_severidade)]

        if not alertas_filtrados.empty:
            # Mapear IDs para nomes de equipamento
            equipamento_map = {
                '1': 'Estufa 1',
                '2': 'Estufa 2',
                '3': 'Estufa 3',
                '4': 'Estufa 4',
                '5': 'Estufa 5'
            }

            # Formatar tabela com HTML customizado para animações
            html_table = '<table style="width:100%; border-collapse: collapse; margin-top: 10px;">'
            html_table += '<thead><tr style="background-color: #2c3e50; color: white;">'
            html_table += '<th style="padding: 12px; text-align: left;">EQUIPAMENTO</th>'
            html_table += '<th style="padding: 12px; text-align: left;">TIPO_SENSOR</th>'
            html_table += '<th style="padding: 12px; text-align: left;">DESCRIÇÃO</th>'
            html_table += '<th style="padding: 12px; text-align: left;">SEVERIDADE</th>'
            html_table += '<th style="padding: 12px; text-align: left;">DATA/HORA</th>'
            html_table += '</tr></thead><tbody>'

            for _, row in alertas_filtrados.iterrows():
                # Classe CSS baseada na severidade
                row_class = 'critico-row' if row['NIVEL_SEVERIDADE'] == 'Critico' else 'alerta-row'

                data_formatada = pd.to_datetime(row['DATA_HORA_ALERTA'], format='mixed').strftime('%d/%m/%Y %H:%M')

                # Mapear equipamento ID para nome
                equipamento_nome = equipamento_map.get(str(row["EQUIPAMENTO"]), row["EQUIPAMENTO"])

                html_table += f'<tr class="{row_class}" style="border-bottom: 1px solid #444;">'
                html_table += f'<td style="padding: 10px;">{equipamento_nome}</td>'
                html_table += f'<td style="padding: 10px;">{row["TIPO_SENSOR"]}</td>'
                html_table += f'<td style="padding: 10px;">{row["DESCRICAO"]}</td>'
                html_table += f'<td style="padding: 10px;"><strong>{row["NIVEL_SEVERIDADE"]}</strong></td>'
                html_table += f'<td style="padding: 10px;">{data_formatada}</td>'
                html_table += '</tr>'

            html_table += '</tbody></table>'

            st.markdown(html_table, unsafe_allow_html=True)
        else:
            st.info("Nenhum alerta com os filtros selecionados")

    # ========================================
    # SEÇÃO 5: PERFORMANCE DO MODELO ML
    # ========================================

    st.markdown("## 🤖 Performance do Modelo ML")

    metricas_df = db.get_metricas_ml()

    if not metricas_df.empty:
        col1, col2 = st.columns(2)

        with col1:
            fig_pie = px.pie(
                metricas_df,
                names='QUALIDADE',
                values='TOTAL',
                title='Distribuição de Classificações',
                color='QUALIDADE',
                color_discrete_map={
                    'Normal': COLORS['normal'],
                    'Alerta': COLORS['alerta'],
                    'Critico': COLORS['critico']
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.markdown("### Métricas do Modelo")
            st.markdown("""
            - **Modelo:** Gradient Boosting
            - **Acurácia:** 100%
            - **F1-Score:** 1.0000
            - **Validação Cruzada:** 99.83%
            """)

            st.markdown("### 📁 Artefatos")
            st.markdown("""
            - `best_model.pkl` - Modelo treinado
            - `scaler.pkl` - Normalizador
            - `label_encoder.pkl` - Encoder de labels
            """)

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
