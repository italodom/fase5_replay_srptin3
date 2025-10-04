"""
Lógica de Controle de Atuadores
FarmTech Solutions - Sistema Inteligente de Irrigação e Climatização
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd


class ActuatorController:
    """Controlador inteligente de atuadores (bombas, ventiladores)"""

    # Thresholds de acionamento (ajustados para zona de alerta)
    THRESHOLDS = {
        'umidade_baixa': 52,       # Abaixo disso, liga bomba (antes era 50)
        'umidade_alta': 82,        # Acima disso, liga ventilador (antes era 80)
        'temperatura_alta': 27.5,  # Acima disso, liga ventilador (antes era 28)
        'temperatura_baixa': 18,   # Abaixo disso, desliga ventilador
    }

    # Potências médias (Watts) para cálculo de economia
    POTENCIAS = {
        'Bomba': 500,
        'Ventilador': 150,
    }

    # Custo médio de energia (R$/kWh)
    CUSTO_KWH = 0.80

    def __init__(self, db_connection):
        """
        Inicializa o controlador com conexão ao banco

        Args:
            db_connection: Conexão SQLite ativa
        """
        self.conn = db_connection
        self.cursor = self.conn.cursor()

    def should_activate_pump(self, umidade: float, equipamento_id: int) -> bool:
        """
        Decide se deve ativar a bomba de irrigação

        Args:
            umidade: Nível atual de umidade (%)
            equipamento_id: ID do equipamento (estufa)

        Returns:
            True se deve ligar a bomba
        """
        # Verifica se bomba já está ligada
        if self._is_actuator_active('Bomba', equipamento_id):
            # Mantém ligada se umidade ainda está baixa (hysteresis)
            return umidade < 55  # Desliga quando chega a 55%
        else:
            # Liga se umidade está abaixo de 52% (antes era 50%)
            return umidade < self.THRESHOLDS['umidade_baixa']

    def should_activate_fan(self, temperatura: float, umidade: float, equipamento_id: int) -> bool:
        """
        Decide se deve ativar o ventilador

        Args:
            temperatura: Temperatura atual (°C)
            umidade: Umidade atual (%)
            equipamento_id: ID do equipamento (estufa)

        Returns:
            True se deve ligar o ventilador
        """
        # Verifica se ventilador já está ligado
        is_active = self._is_actuator_active('Ventilador', equipamento_id)

        if is_active:
            # Mantém ligado se ainda precisa (hysteresis)
            return (temperatura > 26 or umidade > 75)
        else:
            # Liga se temperatura > 27.5°C ou umidade > 82% (acionamento mais cedo)
            return (temperatura > self.THRESHOLDS['temperatura_alta'] or
                    umidade > self.THRESHOLDS['umidade_alta'])

    def _is_actuator_active(self, tipo: str, equipamento_id: int) -> bool:
        """
        Verifica se um atuador está atualmente ativo

        Args:
            tipo: Tipo do atuador ('Bomba' ou 'Ventilador')
            equipamento_id: ID do equipamento

        Returns:
            True se o atuador está ligado
        """
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM Acionamentos_Ativos
            WHERE tipo_atuador = ? AND id_equipamento = ?
        """, (tipo, equipamento_id))

        return self.cursor.fetchone()[0] > 0

    def trigger_actuator(self, tipo: str, equipamento_id: int, motivo: str,
                        id_leitura: Optional[int] = None) -> Optional[int]:
        """
        Aciona um atuador (liga)

        Args:
            tipo: Tipo do atuador ('Bomba' ou 'Ventilador')
            equipamento_id: ID do equipamento
            motivo: Motivo do acionamento (ex: "Umidade Baixa")
            id_leitura: ID da leitura que disparou o acionamento (opcional)

        Returns:
            ID do acionamento criado, ou None se já estava ligado
        """
        # Verifica se já está ligado
        if self._is_actuator_active(tipo, equipamento_id):
            return None

        # Busca ID do atuador
        self.cursor.execute("""
            SELECT id_atuador
            FROM Atuador
            WHERE tipo = ? AND id_equipamento = ? AND status = 'Ativo'
            LIMIT 1
        """, (tipo, equipamento_id))

        result = self.cursor.fetchone()
        if not result:
            return None

        id_atuador = result[0]

        # Cria registro de acionamento
        self.cursor.execute("""
            INSERT INTO Acionamento (id_atuador, motivo, id_leitura_trigger)
            VALUES (?, ?, ?)
        """, (id_atuador, motivo, id_leitura))

        self.conn.commit()
        return self.cursor.lastrowid

    def stop_actuator(self, tipo: str, equipamento_id: int) -> Optional[Dict]:
        """
        Desliga um atuador e calcula economia

        Args:
            tipo: Tipo do atuador
            equipamento_id: ID do equipamento

        Returns:
            Dict com informações do acionamento finalizado, ou None se não estava ligado
        """
        # Busca acionamento ativo
        self.cursor.execute("""
            SELECT id_acionamento, data_hora_inicio, potencia_watts
            FROM Acionamentos_Ativos
            WHERE tipo_atuador = ? AND id_equipamento = ?
            LIMIT 1
        """, (tipo, equipamento_id))

        result = self.cursor.fetchone()
        if not result:
            return None

        id_acionamento, data_hora_inicio, potencia_watts = result

        # Calcular duração
        inicio = datetime.fromisoformat(data_hora_inicio)
        fim = datetime.now()
        duracao = (fim - inicio).total_seconds()

        # Calcular economia (vs. sistema 24/7)
        economia_kwh = self._calculate_energy_savings(potencia_watts, duracao)

        # Atualizar acionamento
        self.cursor.execute("""
            UPDATE Acionamento
            SET data_hora_fim = ?,
                duracao_segundos = ?,
                economia_kwh = ?
            WHERE id_acionamento = ?
        """, (fim.isoformat(), int(duracao), economia_kwh, id_acionamento))

        self.conn.commit()

        return {
            'id_acionamento': id_acionamento,
            'duracao_segundos': int(duracao),
            'economia_kwh': economia_kwh,
            'economia_reais': economia_kwh * self.CUSTO_KWH
        }

    def _calculate_energy_savings(self, potencia_watts: int, duracao_segundos: float) -> float:
        """
        Calcula economia de energia em relação a sistema 24/7

        Args:
            potencia_watts: Potência do atuador em Watts
            duracao_segundos: Duração que ficou ligado

        Returns:
            Economia em kWh
        """
        # Energia consumida neste acionamento
        energia_consumida_kwh = (potencia_watts * duracao_segundos / 3600) / 1000

        # Sistema 24/7 consumiria
        horas_no_periodo = duracao_segundos / 3600
        energia_24_7 = (potencia_watts * 24) / 1000  # kWh por dia

        # Proporção do dia que o sistema ficou ligado
        proporcao = horas_no_periodo / 24

        # Economia = quanto deixou de consumir
        economia = (energia_24_7 * proporcao) - energia_consumida_kwh

        return max(0, economia)  # Nunca negativo

    def check_sensor_health(self, id_sensor: int, num_alertas_criticos: int,
                           num_leituras_anomalas: int, anomalia_tipo: Optional[str] = None) -> str:
        """
        Verifica saúde do sensor e atualiza status

        Args:
            id_sensor: ID do sensor
            num_alertas_criticos: Número de alertas críticos recentes
            num_leituras_anomalas: Número de leituras fora do padrão
            anomalia_tipo: Tipo de anomalia detectada (opcional)

        Returns:
            Status de saúde: 'Normal', 'Atenção', 'Crítico', 'Falha'
        """
        # Determinar status com prioridade para anomalias de hardware
        if anomalia_tipo in ['SENSOR_OSCILANDO', 'SENSOR_TRAVADO', 'SENSOR_IMPOSSIVEL']:
            status = 'Falha'
            observacoes = f"Anomalia detectada: {anomalia_tipo}"
        elif num_alertas_criticos >= 5 or num_leituras_anomalas >= 10:
            status = 'Falha'
            observacoes = f"Alertas: {num_alertas_criticos}, Leituras anômalas: {num_leituras_anomalas}"
        elif num_alertas_criticos >= 3 or num_leituras_anomalas >= 6:
            status = 'Crítico'
            observacoes = f"Alertas: {num_alertas_criticos}, Leituras anômalas: {num_leituras_anomalas}"
        elif num_alertas_criticos >= 1 or num_leituras_anomalas >= 3:
            status = 'Atenção'
            observacoes = f"Alertas: {num_alertas_criticos}, Leituras anômalas: {num_leituras_anomalas}"
        else:
            status = 'Normal'
            observacoes = "Sensor funcionando normalmente"

        # Atualizar banco
        self.cursor.execute("""
            UPDATE Sensor_Health
            SET status_saude = ?,
                num_alertas_criticos = ?,
                num_leituras_anomalas = ?,
                ultima_verificacao = ?,
                observacoes = ?
            WHERE id_sensor = ?
        """, (status, num_alertas_criticos, num_leituras_anomalas,
              datetime.now().isoformat(), observacoes, id_sensor))

        self.conn.commit()
        return status

    def simular_manutencao_sensor(self, sensor_id: int) -> bool:
        """
        Simula manutenção/troca de sensor com problema

        Args:
            sensor_id: ID do sensor a ser mantido

        Returns:
            True se manutenção foi realizada
        """
        try:
            # Verificar se sensor está em falha
            self.cursor.execute("""
                SELECT status_saude, num_leituras_anomalas
                FROM Sensor_Health
                WHERE id_sensor = ?
            """, (sensor_id,))

            result = self.cursor.fetchone()
            if not result or result[0] != 'Falha':
                return False

            # Resetar saúde do sensor
            self.cursor.execute("""
                UPDATE Sensor_Health
                SET status_saude = 'Normal',
                    num_alertas_criticos = 0,
                    num_leituras_anomalas = 0,
                    observacoes = 'Sensor substituído em manutenção preventiva',
                    ultima_manutencao = ?,
                    ultima_verificacao = ?
                WHERE id_sensor = ?
            """, (datetime.now().isoformat(), datetime.now().isoformat(), sensor_id))

            # Marcar eventos críticos deste sensor como resolvidos
            self.cursor.execute("""
                UPDATE Evento_Critico
                SET resolvido = 'S'
                WHERE sensor_id = ? AND resolvido = 'N'
            """, (sensor_id,))

            # Marcar alertas deste sensor como resolvidos
            self.cursor.execute("""
                UPDATE Alerta
                SET resolvido = 'S'
                WHERE id_leitura IN (
                    SELECT id_leitura
                    FROM Leitura
                    WHERE id_sensor = ?
                ) AND resolvido = 'N'
            """, (sensor_id,))

            # Buscar informações do sensor
            self.cursor.execute("""
                SELECT s.id_equipamento, ts.nome
                FROM Sensor s
                JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
                WHERE s.id_sensor = ?
            """, (sensor_id,))

            sensor_info = self.cursor.fetchone()
            if sensor_info:
                equipamento_id, tipo_sensor = sensor_info

                # Registrar evento de manutenção
                self.registrar_evento_critico(
                    tipo_evento='MANUTENCAO_SENSOR',
                    equipamento_id=equipamento_id,
                    sensor_id=sensor_id,
                    descricao=f'Sensor #{sensor_id} ({tipo_sensor}) substituído - manutenção corretiva'
                )

            self.conn.commit()
            return True

        except Exception as e:
            print(f"Erro ao simular manutenção: {e}")
            return False

    def registrar_evento_critico(self, tipo_evento: str, equipamento_id: int,
                                 sensor_id: Optional[int] = None,
                                 atuador_id: Optional[int] = None,
                                 descricao: str = "") -> int:
        """
        Registra evento crítico na timeline

        Args:
            tipo_evento: Tipo do evento crítico
            equipamento_id: ID do equipamento
            sensor_id: ID do sensor afetado (opcional)
            atuador_id: ID do atuador afetado (opcional)
            descricao: Descrição detalhada do evento

        Returns:
            ID do evento criado
        """
        try:
            # Verificar se a tabela existe, senão criar
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Evento_Critico (
                    id_evento INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_evento TEXT NOT NULL,
                    equipamento_id INTEGER,
                    sensor_id INTEGER,
                    atuador_id INTEGER,
                    descricao TEXT,
                    data_hora TEXT NOT NULL,
                    resolvido TEXT DEFAULT 'N',
                    FOREIGN KEY (sensor_id) REFERENCES Sensor(id_sensor),
                    FOREIGN KEY (atuador_id) REFERENCES Atuador(id_atuador)
                )
            """)

            # Inserir evento
            self.cursor.execute("""
                INSERT INTO Evento_Critico (
                    tipo_evento, equipamento_id, sensor_id, atuador_id,
                    descricao, data_hora, resolvido
                ) VALUES (?, ?, ?, ?, ?, ?, 'N')
            """, (tipo_evento, equipamento_id, sensor_id, atuador_id,
                  descricao, datetime.now().isoformat()))

            self.conn.commit()
            return self.cursor.lastrowid

        except Exception as e:
            print(f"Erro ao registrar evento crítico: {e}")
            return -1

    def get_eventos_criticos(self, limit: int = 20, apenas_nao_resolvidos: bool = True) -> List[Dict]:
        """
        Retorna eventos críticos registrados

        Args:
            limit: Número máximo de eventos
            apenas_nao_resolvidos: Se True, retorna apenas eventos não resolvidos

        Returns:
            Lista de eventos críticos
        """
        try:
            # Verificar se tabela existe
            self.cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='Evento_Critico'
            """)

            if not self.cursor.fetchone():
                return []

            where_clause = "WHERE resolvido = 'N'" if apenas_nao_resolvidos else ""

            self.cursor.execute(f"""
                SELECT
                    ec.id_evento,
                    ec.tipo_evento,
                    ec.equipamento_id,
                    'Estufa ' || ec.equipamento_id as equipamento,
                    ec.sensor_id,
                    ec.atuador_id,
                    ec.descricao,
                    ec.data_hora,
                    ec.resolvido
                FROM Evento_Critico ec
                {where_clause}
                ORDER BY ec.data_hora DESC
                LIMIT ?
            """, (limit,))

            eventos = []
            for row in self.cursor.fetchall():
                eventos.append({
                    'id_evento': row[0],
                    'tipo_evento': row[1],
                    'equipamento_id': row[2],
                    'equipamento': row[3],
                    'sensor_id': row[4],
                    'atuador_id': row[5],
                    'descricao': row[6],
                    'data_hora': row[7],
                    'resolvido': row[8]
                })

            return eventos

        except Exception as e:
            print(f"Erro ao buscar eventos críticos: {e}")
            return []

    def get_active_actuators(self) -> List[Dict]:
        """
        Retorna lista de atuadores atualmente ativos

        Returns:
            Lista de dicionários com informações dos acionamentos ativos
        """
        self.cursor.execute("""
            SELECT
                id_acionamento,
                nome_atuador,
                tipo_atuador,
                nome_equipamento,
                data_hora_inicio,
                motivo,
                duracao_segundos,
                potencia_watts
            FROM Acionamentos_Ativos
            ORDER BY data_hora_inicio DESC
        """)

        rows = self.cursor.fetchall()
        return [
            {
                'id_acionamento': row[0],
                'nome_atuador': row[1],
                'tipo': row[2],
                'equipamento': row[3],
                'inicio': row[4],
                'motivo': row[5],
                'duracao_segundos': row[6],
                'potencia_watts': row[7]
            }
            for row in rows
        ]

    def get_economy_stats(self, periodo_dias: int = 7) -> Dict:
        """
        Calcula estatísticas de economia de energia

        Args:
            periodo_dias: Período em dias para calcular

        Returns:
            Dict com estatísticas de economia
        """
        from datetime import timedelta
        data_limite = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        data_limite = data_limite - timedelta(days=periodo_dias)

        self.cursor.execute("""
            SELECT
                SUM(economia_kwh) as economia_total_kwh,
                COUNT(*) as total_acionamentos,
                AVG(duracao_segundos) as duracao_media,
                SUM(duracao_segundos) / 3600.0 as horas_totais
            FROM Acionamento
            WHERE data_hora_inicio >= ?
                AND data_hora_fim IS NOT NULL
        """, (data_limite.isoformat(),))

        row = self.cursor.fetchone()

        economia_kwh = row[0] or 0
        total_acionamentos = row[1] or 0
        duracao_media = row[2] or 0
        horas_totais = row[3] or 0

        return {
            'economia_kwh': round(economia_kwh, 2),
            'economia_reais': round(economia_kwh * self.CUSTO_KWH, 2),
            'total_acionamentos': total_acionamentos,
            'duracao_media_minutos': round(duracao_media / 60, 1),
            'horas_totais': round(horas_totais, 1),
            'periodo_dias': periodo_dias
        }

    def get_sensor_health_summary(self) -> List[Dict]:
        """
        Retorna resumo da saúde de todos os sensores

        Returns:
            Lista de sensores com problemas
        """
        self.cursor.execute("""
            SELECT
                id_sensor,
                equipamento,
                tipo_sensor,
                status_saude,
                num_alertas_criticos,
                num_leituras_anomalas,
                ultima_verificacao,
                observacoes
            FROM Sensores_Problematicos
        """)

        rows = self.cursor.fetchall()
        return [
            {
                'id_sensor': row[0],
                'equipamento': row[1],
                'tipo_sensor': row[2],
                'status': row[3],
                'alertas_criticos': row[4],
                'leituras_anomalas': row[5],
                'ultima_verificacao': row[6],
                'observacoes': row[7]
            }
            for row in rows
        ]
