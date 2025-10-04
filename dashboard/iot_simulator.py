"""
Simulador IoT - FarmTech Solutions
Simula sensores reais inserindo leituras no banco de dados
"""

import sqlite3
import time
import random
from datetime import datetime
from pathlib import Path
import os

# Importar configurações e lógica de atuadores
from config import THRESHOLDS, ANOMALY_CONFIG
from actuator_logic import ActuatorController
from ml_inference import get_predictor


class IoTSimulator:
    """Simulador de sensores IoT que insere leituras reais no banco"""

    def __init__(self, db_path: str, interval_seconds: int = 5):
        """
        Inicializa o simulador IoT

        Args:
            db_path: Caminho para o banco SQLite
            interval_seconds: Intervalo entre leituras (padrão: 5s)
        """
        self.db_path = db_path
        self.interval = interval_seconds
        self.conn = None
        self.cursor = None
        self.controller = None

        # Estado para anomalias (se ativadas)
        self.anomalias_ativas = False
        self.sensor_anomalies = {}  # {sensor_id: {'tipo': 'oscilacao', 'contador': 5}}

        # Preditor ML para classificação
        self.ml_predictor = get_predictor()
        print(f"🤖 ML Predictor: {self.ml_predictor.get_model_info()['loaded']}")

    def connect(self):
        """Conecta ao banco de dados"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.controller = ActuatorController(self.conn)
        print(f"✅ Simulador IoT conectado ao banco: {self.db_path}")

    def get_last_reading(self, sensor_id: int) -> tuple:
        """
        Busca última leitura de um sensor

        Returns:
            (valor, timestamp) ou (None, None) se não houver leituras
        """
        self.cursor.execute("""
            SELECT valor, data_hora
            FROM Leitura
            WHERE id_sensor = ?
            ORDER BY data_hora DESC
            LIMIT 1
        """, (sensor_id,))

        result = self.cursor.fetchone()
        if result:
            return float(result[0]), result[1]
        return None, None

    def get_sensor_type(self, sensor_id: int) -> str:
        """Retorna o tipo do sensor (Temperatura ou Umidade)"""
        self.cursor.execute("""
            SELECT ts.nome
            FROM Sensor s
            JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
            WHERE s.id_sensor = ?
        """, (sensor_id,))

        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_sensor_equipment(self, sensor_id: int) -> int:
        """Retorna o ID do equipamento do sensor"""
        self.cursor.execute("""
            SELECT id_equipamento
            FROM Sensor
            WHERE id_sensor = ?
        """, (sensor_id,))

        result = self.cursor.fetchone()
        return result[0] if result else None

    def calculate_natural_variation(self, sensor_type: str) -> float:
        """
        Calcula variação natural do sensor

        Args:
            sensor_type: 'Temperatura' ou 'Umidade'

        Returns:
            Delta de variação
        """
        if sensor_type == 'Temperatura':
            # Variação natural pequena: -0.2 a +0.2°C por leitura
            return random.uniform(-0.2, 0.2)
        else:  # Umidade
            # Variação natural pequena: -0.5 a +0.5% por leitura
            return random.uniform(-0.5, 0.5)

    def apply_actuator_effects(self, sensor_id: int, current_value: float,
                                sensor_type: str) -> float:
        """
        Aplica efeitos dos atuadores ativos no valor do sensor

        Args:
            sensor_id: ID do sensor
            current_value: Valor atual
            sensor_type: Tipo do sensor

        Returns:
            Valor com efeitos dos atuadores aplicados
        """
        equipment_id = self.get_sensor_equipment(sensor_id)
        if not equipment_id:
            return current_value

        # Buscar atuadores ativos deste equipamento
        active_actuators = self.controller.get_active_actuators()

        delta = 0.0
        for actuator in active_actuators:
            if actuator['id_equipamento'] != equipment_id:
                continue

            tipo_atuador = actuator['tipo']

            if tipo_atuador == 'Ventilador':
                if sensor_type == 'Temperatura':
                    # Ventilador resfria: -0.4 a -0.6°C por leitura
                    delta -= random.uniform(0.4, 0.6)
                elif sensor_type == 'Umidade':
                    # Ventilador seca: -0.8 a -1.2% por leitura
                    delta -= random.uniform(0.8, 1.2)

            elif tipo_atuador == 'Bomba':
                if sensor_type == 'Umidade':
                    # Bomba umidifica: +3.0 a +5.0% por leitura
                    delta += random.uniform(3.0, 5.0)
                elif sensor_type == 'Temperatura':
                    # Bomba resfria levemente: -0.1 a -0.2°C
                    delta -= random.uniform(0.1, 0.2)

        return current_value + delta

    def apply_anomaly_effects(self, sensor_id: int, value: float,
                              sensor_type: str) -> tuple:
        """
        Aplica efeitos de anomalias se estiverem ativas

        Returns:
            (valor_modificado, lista_anomalias_detectadas)
        """
        if not self.anomalias_ativas:
            return value, []

        anomalias = []

        # Verificar se sensor já tem anomalia ativa
        if sensor_id in self.sensor_anomalies:
            anomaly = self.sensor_anomalies[sensor_id]
            anomaly['contador'] -= 1

            # Se contador chegou a 0, remover anomalia
            if anomaly['contador'] <= 0:
                del self.sensor_anomalies[sensor_id]
            else:
                # Aplicar efeito da anomalia
                if anomaly['tipo'] == 'oscilacao':
                    tipo_oscilacao = random.choice(['zerando', 'muito_alto', 'muito_baixo'])
                    if tipo_oscilacao == 'zerando':
                        value = 0.0
                    elif tipo_oscilacao == 'muito_alto':
                        value = value * random.uniform(2.0, 2.5)
                    elif tipo_oscilacao == 'muito_baixo':
                        value = value * random.uniform(0.3, 0.5)
                    anomalias.append('SENSOR_OSCILANDO')

                elif anomaly['tipo'] == 'travado':
                    value = anomaly['valor_travado']
                    anomalias.append('SENSOR_TRAVADO')

        else:
            # Chance de iniciar nova anomalia
            if random.random() < ANOMALY_CONFIG['sensor_oscilacao']['probabilidade']:
                self.sensor_anomalies[sensor_id] = {
                    'tipo': 'oscilacao',
                    'contador': ANOMALY_CONFIG['sensor_oscilacao']['duracao_ciclos']
                }
                anomalias.append('SENSOR_OSCILANDO')

            elif random.random() < ANOMALY_CONFIG['sensor_travado']['probabilidade']:
                self.sensor_anomalies[sensor_id] = {
                    'tipo': 'travado',
                    'contador': ANOMALY_CONFIG['sensor_travado']['duracao_ciclos'],
                    'valor_travado': value
                }
                anomalias.append('SENSOR_TRAVADO')

        return value, anomalias

    def get_quality_ml(self, sensor_id: int, value: float, sensor_type: str,
                       timestamp: datetime) -> str:
        """
        Determina qualidade da leitura usando ML

        Para fazer predição, busca a última leitura do sensor complementar
        (se é temp, busca umid; se é umid, busca temp) do mesmo equipamento.

        Args:
            sensor_id: ID do sensor
            value: Valor lido
            sensor_type: 'Temperatura' ou 'Umidade'
            timestamp: Timestamp da leitura

        Returns:
            Qualidade: 'Normal', 'Alerta' ou 'Critico'
        """
        try:
            # Buscar equipamento do sensor
            equipment_id = self.get_sensor_equipment(sensor_id)
            if not equipment_id:
                return self._fallback_quality(value, sensor_type)

            # Buscar última leitura do sensor complementar do mesmo equipamento
            if sensor_type == 'Temperatura':
                # Buscar umidade
                self.cursor.execute("""
                    SELECT l.valor
                    FROM Leitura l
                    JOIN Sensor s ON l.id_sensor = s.id_sensor
                    JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
                    WHERE s.id_equipamento = ?
                        AND ts.nome = 'Umidade'
                    ORDER BY l.data_hora DESC
                    LIMIT 1
                """, (equipment_id,))
                result = self.cursor.fetchone()
                umidade = float(result[0]) if result else 65.0  # Valor padrão
                temperatura = value
            else:  # Umidade
                # Buscar temperatura
                self.cursor.execute("""
                    SELECT l.valor
                    FROM Leitura l
                    JOIN Sensor s ON l.id_sensor = s.id_sensor
                    JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
                    WHERE s.id_equipamento = ?
                        AND ts.nome = 'Temperatura'
                    ORDER BY l.data_hora DESC
                    LIMIT 1
                """, (equipment_id,))
                result = self.cursor.fetchone()
                temperatura = float(result[0]) if result else 22.0  # Valor padrão
                umidade = value

            # Fazer predição com ML
            condicao, confianca = self.ml_predictor.predict(temperatura, umidade, timestamp)
            return condicao

        except Exception as e:
            # Em caso de erro, usar fallback
            return self._fallback_quality(value, sensor_type)

    def _fallback_quality(self, value: float, sensor_type: str) -> str:
        """Fallback: determina qualidade usando regras simples"""
        sensor_key = 'temperatura' if sensor_type == 'Temperatura' else 'umidade'
        thresholds = THRESHOLDS[sensor_key]

        if value < thresholds['critico_baixo'] or value > thresholds['critico_alto']:
            return 'Critico'
        elif value < thresholds['min_ideal'] or value > thresholds['max_ideal']:
            return 'Alerta'
        else:
            return 'Normal'

    def simulate_reading(self, sensor_id: int):
        """
        Simula uma leitura de sensor e insere no banco

        Args:
            sensor_id: ID do sensor a simular
        """
        # Buscar informações do sensor
        sensor_type = self.get_sensor_type(sensor_id)
        if not sensor_type:
            return

        # Buscar última leitura
        last_value, _ = self.get_last_reading(sensor_id)

        # Se não há leitura anterior, usar valor inicial
        if last_value is None:
            if sensor_type == 'Temperatura':
                last_value = random.uniform(20.0, 25.0)
            else:  # Umidade
                last_value = random.uniform(60.0, 70.0)

        # Calcular variação natural
        natural_delta = self.calculate_natural_variation(sensor_type)
        new_value = last_value + natural_delta

        # Aplicar efeitos dos atuadores
        new_value = self.apply_actuator_effects(sensor_id, new_value, sensor_type)

        # Aplicar efeitos de anomalias (se ativadas)
        new_value, anomalias = self.apply_anomaly_effects(sensor_id, new_value, sensor_type)

        # Garantir limites físicos
        if self.anomalias_ativas:
            # Permite valores impossíveis para detecção
            new_value = max(-5, min(50, new_value)) if sensor_type == 'Temperatura' else max(0, min(110, new_value))
        else:
            # Limites normais
            new_value = max(10, min(35, new_value)) if sensor_type == 'Temperatura' else max(30, min(95, new_value))

        # Timestamp
        timestamp = datetime.now()

        # Determinar qualidade usando ML
        quality = self.get_quality_ml(sensor_id, new_value, sensor_type, timestamp)

        # Inserir leitura no banco
        timestamp_iso = timestamp.isoformat()
        self.cursor.execute("""
            INSERT INTO Leitura (id_sensor, valor, data_hora, qualidade)
            VALUES (?, ?, ?, ?)
        """, (sensor_id, round(new_value, 1), timestamp_iso, quality))

        # Processar leitura através do controlador (para decidir ações)
        equipment_id = self.get_sensor_equipment(sensor_id)
        if equipment_id:
            self.controller.process_reading(
                sensor_id=sensor_id,
                equipment_id=equipment_id,
                sensor_type=sensor_type,
                value=new_value,
                quality=quality,
                anomalias=anomalias
            )

        self.conn.commit()

    def get_all_sensors(self) -> list:
        """Retorna lista de todos os sensores"""
        self.cursor.execute("SELECT id_sensor FROM Sensor ORDER BY id_sensor")
        return [row[0] for row in self.cursor.fetchall()]

    def run(self):
        """Loop principal do simulador"""
        print(f"🚀 Iniciando simulador IoT (intervalo: {self.interval}s)")
        print(f"{'='*60}")

        sensors = self.get_all_sensors()
        print(f"📡 Sensores encontrados: {len(sensors)}")

        # Caminho do arquivo flag para anomalias
        flag_file = Path(__file__).parent / '.anomalias_flag'

        iteration = 0
        try:
            while True:
                iteration += 1

                # Verificar arquivo flag de anomalias
                anomalias_ativas_anterior = self.anomalias_ativas
                self.anomalias_ativas = flag_file.exists()

                # Notificar mudança de estado
                if self.anomalias_ativas != anomalias_ativas_anterior:
                    if self.anomalias_ativas:
                        print(f"\n🚨 MODO ANOMALIA ATIVADO (via flag)")
                    else:
                        print(f"\n🟢 MODO NORMAL ATIVADO (via flag)")

                print(f"\n⏱️  Iteração {iteration} - {datetime.now().strftime('%H:%M:%S')}")
                print(f"   Anomalias: {'ATIVAS' if self.anomalias_ativas else 'DESATIVADAS'}")

                # Simular leitura de cada sensor
                for sensor_id in sensors:
                    self.simulate_reading(sensor_id)

                print(f"✅ {len(sensors)} leituras inseridas no banco")

                # Aguardar próximo ciclo
                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\n🛑 Simulador IoT encerrado pelo usuário")
        finally:
            if self.conn:
                self.conn.close()
                print("✅ Conexão com banco fechada")


def main():
    """Função principal"""
    # Determinar caminho do banco
    db_path = Path(__file__).parent.parent / 'data' / 'farmtech.db'

    # Criar simulador
    simulator = IoTSimulator(str(db_path), interval_seconds=5)
    simulator.connect()

    # Verificar se deve ativar anomalias (via variável de ambiente)
    if os.getenv('ANOMALIAS_ATIVAS', 'false').lower() == 'true':
        simulator.anomalias_ativas = True
        print("🚨 Modo de anomalias ATIVADO")
    else:
        print("🟢 Modo normal (sem anomalias)")

    # Iniciar simulação
    simulator.run()


if __name__ == "__main__":
    main()
