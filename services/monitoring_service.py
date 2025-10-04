"""
Serviço de monitoramento que orquestra simulação, ML e persistência
"""
from datetime import datetime
from config.database import Database
from repositories.sensor_repository import SensorRepository
from repositories.leitura_repository import LeituraRepository
from repositories.alerta_repository import AlertaRepository
from models.leitura import Leitura
from models.alerta import Alerta
from services.ml_predictor import MLPredictor
from services.simulator import IoTSimulator


class MonitoringService:
    """Serviço que coordena todo o processo de monitoramento"""

    def __init__(self):
        self.db = Database()
        self.sensor_repo = SensorRepository(self.db)
        self.leitura_repo = LeituraRepository(self.db)
        self.alerta_repo = AlertaRepository(self.db)
        self.ml_predictor = MLPredictor()
        self.simulator = IoTSimulator()

    def processar_ciclo_leitura(self):
        """Executa um ciclo completo de leitura para todas as estufas"""
        # Gerar leituras para todas as estufas
        leituras = self.simulator.gerar_leituras_todas_estufas()

        for id_equipamento, (temperatura, umidade) in leituras.items():
            self._processar_leitura_estufa(id_equipamento, temperatura, umidade)

    def _processar_leitura_estufa(self, id_equipamento: int, temperatura: float, umidade: float):
        """Processa leitura de uma estufa específica"""
        # Buscar sensores da estufa
        sensor_temp = self.sensor_repo.find_by_tipo(id_equipamento, 'Temperatura')
        sensor_umid = self.sensor_repo.find_by_tipo(id_equipamento, 'Umidade')

        if not sensor_temp or not sensor_umid:
            print(f"⚠ Sensores não encontrados para estufa {id_equipamento}")
            return

        # Fazer predição ML
        try:
            qualidade, confianca = self.ml_predictor.predict(temperatura, umidade)
        except Exception as e:
            print(f"⚠ Erro na predição ML: {e}. Usando regras...")
            qualidade = self.ml_predictor.classify_by_rules(temperatura, umidade)
            confianca = 1.0

        # Criar e salvar leitura de temperatura
        leitura_temp = Leitura(
            id_sensor=sensor_temp.id_sensor,
            valor=temperatura,
            data_hora=datetime.now(),
            qualidade=qualidade
        )
        id_leitura_temp = self.leitura_repo.save(leitura_temp)

        # Criar e salvar leitura de umidade
        leitura_umid = Leitura(
            id_sensor=sensor_umid.id_sensor,
            valor=umidade,
            data_hora=datetime.now(),
            qualidade=qualidade
        )
        id_leitura_umid = self.leitura_repo.save(leitura_umid)

        # Criar alerta se necessário
        if qualidade in ['Alerta', 'Critico']:
            mensagem = self._gerar_mensagem_alerta(
                id_equipamento, temperatura, umidade, qualidade
            )

            alerta = Alerta(
                id_leitura=id_leitura_temp,
                tipo_alerta=qualidade,
                mensagem=mensagem,
                data_alerta=datetime.now(),
                resolvido='N'
            )
            self.alerta_repo.save(alerta)

        # Log
        status_emoji = self._get_status_emoji(qualidade)
        print(f"{status_emoji} Estufa {id_equipamento}: {temperatura}°C, {umidade}% - {qualidade} ({confianca:.1%})")

    def _gerar_mensagem_alerta(self, id_equipamento: int, temp: float, umid: float, tipo: str) -> str:
        """Gera mensagem descritiva para o alerta"""
        if tipo == 'Critico':
            return f"CRÍTICO: Estufa {id_equipamento} - Temp: {temp}°C, Umid: {umid}%. Ação imediata necessária!"
        else:
            return f"ALERTA: Estufa {id_equipamento} - Temp: {temp}°C, Umid: {umid}%. Monitorar com atenção."

    def _get_status_emoji(self, qualidade: str) -> str:
        """Retorna emoji baseado no status"""
        emojis = {
            'Normal': '✓',
            'Alerta': '⚠',
            'Critico': '✗'
        }
        return emojis.get(qualidade, '?')
