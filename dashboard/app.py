"""
Dashboard Streamlit - FarmTech Solutions
Sistema de Monitoramento e Alertas
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

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
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    .alert-critico {
        background-color: #f8d7da;
        border: 2px solid #f5c6cb;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .alert-warning {
        background-color: #fff3cd;
        border: 2px solid #ffeaa7;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
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

    # Contar leituras por equipamento e qualidade
    dist = df.groupby(['EQUIPAMENTO', 'QUALIDADE']).size().reset_index(name='count')

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

    # Extrair hora do dia
    df['hora'] = pd.to_datetime(df['DATA_HORA']).dt.hour

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

    # Sidebar
    with st.sidebar:
        st.image("assets/logo-fiap.png", width=200)
        st.markdown("---")
        st.markdown("### ⚙️ Configurações")

        # Seletor de refresh
        auto_refresh = st.checkbox(
            "Auto-refresh",
            value=False,
            help=f"Atualiza a cada {AUTO_REFRESH_INTERVAL}s"
        )

        if auto_refresh:
            st_autorefresh = st.empty()
            with st_autorefresh:
                st.info(f"🔄 Atualizando a cada {AUTO_REFRESH_INTERVAL}s")

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
            f"{kpis['total_leituras']:,}"
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
            # Formatar tabela
            alertas_display = alertas_filtrados[[
                'EQUIPAMENTO', 'TIPO_SENSOR', 'DESCRICAO',
                'NIVEL_SEVERIDADE', 'DATA_HORA_ALERTA'
            ]].copy()

            alertas_display['DATA_HORA_ALERTA'] = pd.to_datetime(
                alertas_display['DATA_HORA_ALERTA']
            ).dt.strftime('%d/%m/%Y %H:%M')

            st.dataframe(
                alertas_display,
                use_container_width=True,
                hide_index=True
            )
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
