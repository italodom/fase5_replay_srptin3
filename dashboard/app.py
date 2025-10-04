"""
Dashboard Streamlit - FarmTech Solutions
Sistema de Monitoramento de Estufas em Tempo Real
"""
import streamlit as st
import sys
from pathlib import Path
import time
import pandas as pd
from datetime import datetime

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import Database
from repositories.equipamento_repository import EquipamentoRepository
from repositories.leitura_repository import LeituraRepository
from dashboard.components.estufa_card import EstufaCard

# Configuração da página
st.set_page_config(
    page_title="FarmTech - Monitoramento de Estufas",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# CSS customizado - Dark Mode
st.markdown("""
    <style>
    /* Dark Mode - Fundo da página */
    .stApp {
        background: linear-gradient(to bottom, #1a1a1a 0%, #0d1117 100%);
    }

    /* Dark Mode - Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
    }

    .main-header {
        font-size: 2.8em;
        font-weight: 700;
        background: linear-gradient(135deg, #3fb950 0%, #2ea043 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }
    .subtitle {
        font-size: 1.1em;
        color: #8b949e;
        text-align: center;
        margin-bottom: 40px;
        font-weight: 400;
    }

    /* Dark Mode - Containers com borda */
    [data-testid="stVerticalBlock"] > div:has(> div.element-container) {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
    }

    /* Dark Mode - Métricas */
    [data-testid="stMetric"] {
        background-color: #0d1117;
        padding: 10px;
        border-radius: 6px;
    }

    /* Dark Mode - Texto */
    .stMarkdown, p, span, div {
        color: #c9d1d9 !important;
    }

    /* Dark Mode - Separadores */
    hr {
        border-color: #30363d !important;
    }

    /* Esconder elementos desnecessários */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Espaçamento entre colunas */
    [data-testid="column"] {
        padding: 0 8px;
    }
    </style>
""", unsafe_allow_html=True)


class DashboardApp:
    """Aplicação principal do dashboard"""

    def __init__(self):
        self.db = Database()
        self.equipamento_repo = EquipamentoRepository(self.db)
        self.leitura_repo = LeituraRepository(self.db)

    def run(self):
        """Executa o dashboard"""
        # Header
        st.markdown('<h1 class="main-header">🌱 FarmTech Solutions</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Sistema de Monitoramento de Estufas em Tempo Real</p>',
                   unsafe_allow_html=True)

        # Buscar dados das estufas para KPIs
        estufas_data = self._get_all_estufas_data()

        # KPIs principais
        if estufas_data:
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)

            # Total de leituras no sistema
            total_leituras = self.leitura_repo.count_all_readings()

            # Temperatura média geral
            temp_media = sum([e['temperatura'] for e in estufas_data]) / len(estufas_data)

            # Umidade média geral
            umid_media = sum([e['umidade'] for e in estufas_data]) / len(estufas_data)

            # Total de alertas ativos (Alerta + Crítico)
            alertas_ativos = sum([1 for e in estufas_data if e['status'] in ['Alerta', 'Critico']])

            with kpi1:
                st.metric(
                    label="📊 Total de Leituras",
                    value=total_leituras
                )

            with kpi2:
                st.metric(
                    label="🌡️ Temperatura Média",
                    value=f"{temp_media:.1f}°C"
                )

            with kpi3:
                st.metric(
                    label="💧 Umidade Média",
                    value=f"{umid_media:.1f}%"
                )

            with kpi4:
                st.metric(
                    label="Alertas Ativos",
                    value=alertas_ativos
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # Sidebar
        with st.sidebar:
            st.markdown("# Menu")
            st.markdown("---")
            st.markdown("### ⚙️ Configurações")

            auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
            refresh_interval = st.slider("Intervalo (segundos)", 1, 10, 3)

        # Container principal
        if not estufas_data:
            st.warning("⚠️ Nenhuma estufa encontrada. Execute o script de inicialização do banco de dados.")
            return

        # Exibir estufas em uma única linha (4 colunas com espaçamento)
        cols = st.columns(4, gap="medium")

        for idx, estufa_data in enumerate(estufas_data):
            with cols[idx]:
                EstufaCard.render(estufa_data)

        # Gráfico de histórico de temperatura
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📈 Histórico de Temperatura das Estufas")

        # Buscar dados de histórico
        temp_history = self.leitura_repo.get_temperature_history(limit=100)

        if temp_history:
            # Converter para DataFrame
            df = pd.DataFrame(temp_history)

            # Ordenar por data (do mais antigo para o mais recente)
            df = df.sort_values('data_hora')

            # Converter data_hora para datetime
            df['data_hora'] = pd.to_datetime(df['data_hora'])

            # Criar pivot table para ter cada estufa como coluna
            df_pivot = df.pivot_table(
                index='data_hora',
                columns='estufa',
                values='temperatura',
                aggfunc='mean'
            )

            # Exibir gráfico de linha
            st.line_chart(df_pivot, height=400)
        else:
            st.info("Sem dados históricos disponíveis")

        # Footer moderno - Dark Mode
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style="
                display: flex;
                justify-content: space-around;
                padding: 20px;
                background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
                border: 1px solid #30363d;
                border-radius: 10px;
                margin-top: 20px;
            ">
                <div style="text-align: center;">
                    <p style="margin: 0; font-size: 0.9em; color: #8b949e;">📅 Última atualização</p>
                    <p style="margin: 4px 0 0 0; font-weight: 600; color: #c9d1d9;">{time.strftime("%d/%m/%Y %H:%M:%S")}</p>
                </div>
                <div style="text-align: center;">
                    <p style="margin: 0; font-size: 0.9em; color: #8b949e;">🔗 Status do sistema</p>
                    <p style="margin: 4px 0 0 0; font-weight: 600; color: #3fb950;">Online ✅</p>
                </div>
                <div style="text-align: center;">
                    <p style="margin: 0; font-size: 0.9em; color: #8b949e;">📈 Estufas ativas</p>
                    <p style="margin: 4px 0 0 0; font-weight: 600; color: #c9d1d9;">{len(estufas_data)}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Auto-refresh
        if auto_refresh:
            time.sleep(refresh_interval)
            st.rerun()

    def _get_all_estufas_data(self):
        """Busca dados de todas as estufas"""
        estufas = self.equipamento_repo.find_all_with_cultura()
        estufas_data = []

        for estufa in estufas:
            # Buscar últimas leituras
            leituras = self.leitura_repo.get_latest_readings_by_equipamento(estufa.id_equipamento)

            # Extrair temperatura e umidade
            temp_data = leituras.get('Temperatura', {})
            umid_data = leituras.get('Umidade', {})

            temperatura = temp_data.get('valor', 0.0)
            umidade = umid_data.get('valor', 0.0)

            # Status é o pior entre temperatura e umidade
            status_temp = temp_data.get('qualidade', 'Normal')
            status_umid = umid_data.get('qualidade', 'Normal')
            status = self._get_worst_status(status_temp, status_umid)

            estufas_data.append({
                'id': estufa.id_equipamento,
                'nome': estufa.nome,
                'cultura': estufa.cultura_nome or 'N/A',
                'temperatura': temperatura,
                'umidade': umidade,
                'status': status
            })

        return estufas_data

    def _get_worst_status(self, status1: str, status2: str) -> str:
        """Retorna o pior status entre dois"""
        hierarchy = {'Critico': 3, 'Alerta': 2, 'Normal': 1}
        if hierarchy.get(status1, 0) >= hierarchy.get(status2, 0):
            return status1
        return status2


if __name__ == "__main__":
    app = DashboardApp()
    app.run()
