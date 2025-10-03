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

def generate_simulated_reading():
    """Gera leitura simulada de temperatura e umidade com distribuição realista"""
    # Distribuição: 70% Normal, 20% Alerta, 10% Crítico
    rand = random.random()

    def get_quality(value, sensor_type):
        thresholds = THRESHOLDS[sensor_type]
        if value < thresholds['critico_baixo'] or value > thresholds['critico_alto']:
            return 'Critico'
        elif value < thresholds['min_ideal'] or value > thresholds['max_ideal']:
            return 'Alerta'
        else:
            return 'Normal'

    now = datetime.now()

    if rand < 0.7:  # 70% Normal
        temp = random.uniform(18, 28)  # Faixa ideal
        humid = random.uniform(50, 80)  # Faixa ideal
    elif rand < 0.9:  # 20% Alerta
        if random.random() < 0.5:
            temp = random.choice([random.uniform(15, 18), random.uniform(28, 32)])  # Alerta
            humid = random.uniform(50, 80)  # Normal
        else:
            temp = random.uniform(18, 28)  # Normal
            humid = random.choice([random.uniform(40, 50), random.uniform(80, 90)])  # Alerta
    else:  # 10% Crítico
        if random.random() < 0.5:
            temp = random.choice([random.uniform(13, 15), random.uniform(32, 35)])  # Crítico
            humid = random.uniform(50, 80)  # Normal
        else:
            temp = random.uniform(18, 28)  # Normal
            humid = random.choice([random.uniform(35, 40), random.uniform(90, 95)])  # Crítico

    temp_quality = get_quality(temp, 'temperatura')
    humid_quality = get_quality(humid, 'umidade')

    return {
        'temperatura': {'valor': round(temp, 1), 'qualidade': temp_quality, 'timestamp': now},
        'umidade': {'valor': round(humid, 1), 'qualidade': humid_quality, 'timestamp': now}
    }

def insert_simulated_reading(db):
    """Insere leitura simulada no banco SQLite baseado em sensores reais"""
    if db.db_type != 'sqlite':
        return None

    try:
        import sqlite3
        conn = db.connection
        cursor = conn.cursor()

        # Buscar equipamentos disponíveis
        cursor.execute("SELECT DISTINCT equipamento FROM Leitura LIMIT 1")
        equipamento_row = cursor.fetchone()
        equipamento = equipamento_row[0] if equipamento_row else '1'

        reading = generate_simulated_reading()

        # Inserir temperatura
        cursor.execute("""
            INSERT INTO Leitura (id_sensor, tipo_sensor, equipamento, valor, data_hora, qualidade)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (1, 'Temperatura', equipamento, reading['temperatura']['valor'],
              reading['temperatura']['timestamp'].isoformat(), reading['temperatura']['qualidade']))

        temp_id = cursor.lastrowid

        # Inserir umidade
        cursor.execute("""
            INSERT INTO Leitura (id_sensor, tipo_sensor, equipamento, valor, data_hora, qualidade)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (2, 'Umidade', equipamento, reading['umidade']['valor'],
              reading['umidade']['timestamp'].isoformat(), reading['umidade']['qualidade']))

        humid_id = cursor.lastrowid

        # Criar alertas SEPARADOS para cada sensor (nunca juntos)
        if reading['temperatura']['qualidade'] in ['Alerta', 'Critico']:
            descricao = f"Temperatura em nível de {reading['temperatura']['qualidade'].lower()}: {reading['temperatura']['valor']}°C"
            cursor.execute("""
                INSERT INTO Alerta (id_leitura, descricao, nivel_severidade, data_hora_alerta, resolvido)
                VALUES (?, ?, ?, ?, 'N')
            """, (temp_id, descricao, reading['temperatura']['qualidade'], reading['temperatura']['timestamp'].isoformat()))

        if reading['umidade']['qualidade'] in ['Alerta', 'Critico']:
            descricao = f"Umidade em nível de {reading['umidade']['qualidade'].lower()}: {reading['umidade']['valor']}%"
            cursor.execute("""
                INSERT INTO Alerta (id_leitura, descricao, nivel_severidade, data_hora_alerta, resolvido)
                VALUES (?, ?, ?, ?, 'N')
            """, (humid_id, descricao, reading['umidade']['qualidade'], reading['umidade']['timestamp'].isoformat()))

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

def create_time_series_chart(df):
    """Cria gráfico de série temporal"""
    if df.empty:
        st.warning("Sem dados para exibir")
        return

    # Filtrar temperatura e umidade
    df_temp = df[df['TIPO_SENSOR'] == 'Temperatura'].copy()
    df_umid = df[df['TIPO_SENSOR'] == 'Umidade'].copy()

    fig = go.Figure()

    # Linha de temperatura
    if not df_temp.empty:
        fig.add_trace(go.Scatter(
            x=df_temp['DATA_HORA'],
            y=df_temp['VALOR'],
            name='Temperatura (°C)',
            mode='lines+markers',
            line=dict(color='#FF5733', width=2),
            marker=dict(size=4)
        ))

        # Linhas de threshold temperatura
        fig.add_hline(
            y=THRESHOLDS['temperatura']['max_ideal'],
            line_dash="dash",
            line_color="green",
            annotation_text="Temp Ideal Max"
        )
        fig.add_hline(
            y=THRESHOLDS['temperatura']['critico_alto'],
            line_dash="dash",
            line_color="red",
            annotation_text="Temp Crítico"
        )

    # Linha de umidade (eixo Y secundário)
    if not df_umid.empty:
        fig.add_trace(go.Scatter(
            x=df_umid['DATA_HORA'],
            y=df_umid['VALOR'],
            name='Umidade (%)',
            mode='lines+markers',
            line=dict(color='#3399FF', width=2),
            marker=dict(size=4),
            yaxis='y2'
        ))

    # Layout
    fig.update_layout(
        title='Evolução Temporal - Temperatura e Umidade',
        xaxis_title='Data/Hora',
        yaxis_title='Temperatura (°C)',
        yaxis2=dict(
            title='Umidade (%)',
            overlaying='y',
            side='right'
        ),
        height=CHART_CONFIG['height'],
        template=CHART_CONFIG['template'],
        hovermode='x unified'
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
        else:
            st.success("✅ Conectado ao Oracle")

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
