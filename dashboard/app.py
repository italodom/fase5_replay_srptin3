"""
Dashboard Streamlit - FarmTech Solutions
Sistema de Monitoramento de Estufas em Tempo Real
"""
import streamlit as st
import sys
from pathlib import Path
import time

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
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5em;
        color: #28a745;
        text-align: center;
        margin-bottom: 20px;
    }
    .subtitle {
        font-size: 1.2em;
        color: #6c757d;
        text-align: center;
        margin-bottom: 30px;
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

        # Sidebar
        with st.sidebar:
            st.image("https://via.placeholder.com/200x80/28a745/ffffff?text=FarmTech",
                    use_container_width=True)
            st.markdown("---")
            st.markdown("### ⚙️ Configurações")

            auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
            refresh_interval = st.slider("Intervalo (segundos)", 1, 10, 3)

            st.markdown("---")
            st.markdown("### 📊 Estatísticas Gerais")

            # Contador de estufas por status
            estufas_data = self._get_all_estufas_data()
            status_count = {'Normal': 0, 'Alerta': 0, 'Critico': 0}
            for estufa in estufas_data:
                status_count[estufa['status']] += 1

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Normal", status_count['Normal'])
            with col2:
                st.metric("⚠️ Alerta", status_count['Alerta'])
            with col3:
                st.metric("🚨 Crítico", status_count['Critico'])

        # Container principal
        if not estufas_data:
            st.warning("⚠️ Nenhuma estufa encontrada. Execute o script de inicialização do banco de dados.")
            return

        # Exibir estufas em grid 2x2
        col1, col2 = st.columns(2)

        for idx, estufa_data in enumerate(estufas_data):
            with col1 if idx % 2 == 0 else col2:
                EstufaCard.render(estufa_data)

        # Footer
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("📅 **Última atualização:** " + time.strftime("%d/%m/%Y %H:%M:%S"))
        with col2:
            st.markdown("🔗 **Status do sistema:** Online ✅")
        with col3:
            st.markdown("📈 **Estufas ativas:** " + str(len(estufas_data)))

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
