"""
Simulador em Tempo Real com Atuadores Inteligentes
FarmTech Solutions - Simula efeitos dos atuadores e acionamentos automáticos
"""

import sqlite3
from datetime import datetime
from typing import Dict, Optional
import random

from actuator_logic import ActuatorController


class RealtimeSimulator:
    """Simula comportamento em tempo real com atuadores inteligentes"""

    # Efeitos dos atuadores nas leituras (por ciclo de 5s) - AJUSTADO
    ACTUATOR_EFFECTS = {
        'Bomba': {
            'umidade_delta': +4.0,      # Aumenta umidade em 4% por ciclo de 5s (antes era +2.0)
            'temperatura_delta': -0.15,  # Diminui temp em 0.15°C por ciclo (antes era -0.2)
        },
        'Ventilador': {
            'umidade_delta': -1.0,      # Diminui umidade em 1% por ciclo de 5s (antes era -3.0)
            'temperatura_delta': -0.5,  # Diminui temp em 0.5°C por ciclo (mantém)
        }
    }

    def __init__(self, db_connection):
        """
        Inicializa simulador

        Args:
            db_connection: Conexão SQLite ativa
        """
        self.conn = db_connection
        self.cursor = self.conn.cursor()
        self.controller = ActuatorController(db_connection)

    def apply_actuator_effects(self, equipamento_id: int, temperatura: float,
                               umidade: float) -> Dict[str, float]:
        """
        Aplica efeitos dos atuadores ativos nas leituras simuladas

        Args:
            equipamento_id: ID do equipamento (estufa)
            temperatura: Temperatura atual (°C)
            umidade: Umidade atual (%)

        Returns:
            Dict com temperatura e umidade ajustadas
        """
        temp_ajustada = temperatura
        umid_ajustada = umidade

        # Buscar atuadores ativos para este equipamento
        active = self.controller.get_active_actuators()

        for actuator in active:
            if actuator['equipamento'] == f'Estufa {equipamento_id}':
                tipo = actuator['tipo']

                if tipo in self.ACTUATOR_EFFECTS:
                    effects = self.ACTUATOR_EFFECTS[tipo]
                    temp_ajustada += effects['temperatura_delta']
                    umid_ajustada += effects['umidade_delta']

        # Garantir limites físicos
        temp_ajustada = max(10, min(40, temp_ajustada))
        umid_ajustada = max(20, min(100, umid_ajustada))

        return {
            'temperatura': round(temp_ajustada, 1),
            'umidade': round(umid_ajustada, 1)
        }

    def detect_actuator_failure(self, equipamento_id: int, equipamento_nome: str,
                               temperatura_anterior: float, temperatura_atual: float,
                               umidade_anterior: float, umidade_atual: float,
                               temp_sensor_id: int, umid_sensor_id: int) -> list:
        """
        Detecta falhas nos atuadores (não estão produzindo efeito esperado)

        Args:
            equipamento_id: ID do equipamento (estufa)
            equipamento_nome: Nome do equipamento
            temperatura_anterior: Temperatura da leitura anterior
            temperatura_atual: Temperatura atual
            umidade_anterior: Umidade da leitura anterior
            umidade_atual: Umidade atual
            temp_sensor_id: ID do sensor de temperatura
            umid_sensor_id: ID do sensor de umidade

        Returns:
            Lista de anomalias detectadas
        """
        anomalias = []

        # Calcular deltas (mudanças)
        temp_delta = temperatura_atual - temperatura_anterior
        umid_delta = umidade_atual - umidade_anterior

        # Verificar se ventilador está ativo
        ventilador_ativo = False
        bomba_ativa = False

        for actuator in self.controller.get_active_actuators():
            if actuator['equipamento'] == equipamento_nome:
                if actuator['tipo'] == 'Ventilador':
                    ventilador_ativo = True
                    # Ventilador ligado: temperatura deveria estar CAINDO
                    # Se está subindo ou não está caindo o suficiente = FALHA

                    if temp_delta > 0:
                        # CRÍTICO: Temperatura SUBINDO com ventilador ligado!
                        anomalias.append({
                            'tipo': 'ATUADOR_VENTILADOR_FALHA',
                            'mensagem': f'{equipamento_nome}: Ventilador ligado mas temperatura SUBINDO ({temp_delta:+.1f}°C)',
                            'sensor_id': temp_sensor_id,
                            'atuador_id': actuator['id_acionamento'],
                            'severidade': 'CRÍTICO'
                        })
                    elif temp_delta > -0.2:
                        # ALERTA: Ventilador não está resfriando adequadamente
                        anomalias.append({
                            'tipo': 'ATUADOR_VENTILADOR_FALHA',
                            'mensagem': f'{equipamento_nome}: Ventilador não está resfriando adequadamente (delta: {temp_delta:+.1f}°C)',
                            'sensor_id': temp_sensor_id,
                            'atuador_id': actuator['id_acionamento'],
                            'severidade': 'ALERTA'
                        })

                elif actuator['tipo'] == 'Bomba':
                    bomba_ativa = True
                    # Bomba ligada: umidade deveria estar SUBINDO
                    # Se está caindo ou não está subindo o suficiente = FALHA

                    if umid_delta < 0:
                        # CRÍTICO: Umidade CAINDO com bomba ligada!
                        anomalias.append({
                            'tipo': 'ATUADOR_BOMBA_FALHA',
                            'mensagem': f'{equipamento_nome}: Bomba ligada mas umidade CAINDO ({umid_delta:+.1f}%)',
                            'sensor_id': umid_sensor_id,
                            'atuador_id': actuator['id_acionamento'],
                            'severidade': 'CRÍTICO'
                        })
                    elif umid_delta < 1.0:
                        # ALERTA: Bomba não está irrigando adequadamente
                        anomalias.append({
                            'tipo': 'ATUADOR_BOMBA_FALHA',
                            'mensagem': f'{equipamento_nome}: Bomba não está irrigando adequadamente (delta: {umid_delta:+.1f}%)',
                            'sensor_id': umid_sensor_id,
                            'atuador_id': actuator['id_acionamento'],
                            'severidade': 'ALERTA'
                        })

        return anomalias

    def registrar_anomalia_atuador(self, anomalia: dict):
        """
        Registra anomalia de atuador no banco de dados

        Args:
            anomalia: Dicionário com informações da anomalia
        """
        try:
            # Inserir alerta crítico
            self.cursor.execute("""
                INSERT INTO Alerta (
                    id_leitura,
                    tipo_alerta,
                    mensagem,
                    data_alerta,
                    resolvido
                ) VALUES (?, ?, ?, ?, 'N')
            """, (
                anomalia.get('sensor_id'),
                f"Crítico - {anomalia['tipo']}",
                anomalia['mensagem'],
                datetime.now().isoformat()
            ))

            # Atualizar saúde do sensor afetado
            self.cursor.execute("""
                UPDATE Sensor_Health
                SET status_saude = 'Falha',
                    num_leituras_anomalas = num_leituras_anomalas + 1,
                    ultima_verificacao = ?
                WHERE id_sensor = ?
            """, (datetime.now().isoformat(), anomalia['sensor_id']))

            self.conn.commit()

        except Exception as e:
            print(f"Erro ao registrar anomalia de atuador: {e}")

    def process_reading_and_actuate(self, equipamento_id: int, equipamento_nome: str,
                                    temperatura: float, umidade: float,
                                    temp_sensor_id: int, umid_sensor_id: int,
                                    temp_leitura_id: Optional[int] = None,
                                    umid_leitura_id: Optional[int] = None,
                                    temperatura_anterior: Optional[float] = None,
                                    umidade_anterior: Optional[float] = None) -> Dict:
        """
        Processa leitura e aciona/desliga atuadores automaticamente

        Args:
            equipamento_id: ID do equipamento
            equipamento_nome: Nome do equipamento (ex: "Estufa 1")
            temperatura: Temperatura lida
            umidade: Umidade lida
            temp_sensor_id: ID do sensor de temperatura
            umid_sensor_id: ID do sensor de umidade
            temp_leitura_id: ID da leitura de temperatura (opcional)
            umid_leitura_id: ID da leitura de umidade (opcional)

        Returns:
            Dict com informações sobre acionamentos realizados
        """
        actions = {
            'bomba_ligada': False,
            'bomba_desligada': False,
            'ventilador_ligado': False,
            'ventilador_desligado': False,
            'motivos': []
        }

        # ========================================
        # LÓGICA DA BOMBA
        # ========================================
        should_pump = self.controller.should_activate_pump(umidade, equipamento_id)

        if should_pump:
            # Ligar bomba se não está ligada
            result = self.controller.trigger_actuator(
                'Bomba',
                equipamento_id,
                f'Umidade Baixa ({umidade:.1f}%)',
                umid_leitura_id
            )
            if result:
                actions['bomba_ligada'] = True
                actions['motivos'].append(f'💦 Bomba ligada: umidade baixa')
        else:
            # Desligar bomba se está ligada
            result = self.controller.stop_actuator('Bomba', equipamento_id)
            if result:
                actions['bomba_desligada'] = True
                economia = result['economia_reais']
                actions['motivos'].append(f'💦 Bomba desligada (economia: R$ {economia:.2f})')

        # ========================================
        # LÓGICA DO VENTILADOR
        # ========================================
        should_fan = self.controller.should_activate_fan(
            temperatura, umidade, equipamento_id
        )

        if should_fan:
            # Determinar motivo principal
            if temperatura > self.controller.THRESHOLDS['temperatura_alta']:
                motivo = f'Temperatura Alta ({temperatura:.1f}°C)'
                leitura_id = temp_leitura_id
            else:
                motivo = f'Umidade Alta ({umidade:.1f}%)'
                leitura_id = umid_leitura_id

            # Ligar ventilador se não está ligado
            result = self.controller.trigger_actuator(
                'Ventilador',
                equipamento_id,
                motivo,
                leitura_id
            )
            if result:
                actions['ventilador_ligado'] = True
                actions['motivos'].append(f'💨 Ventilador ligado: {motivo.lower()}')
        else:
            # Desligar ventilador se está ligado
            result = self.controller.stop_actuator('Ventilador', equipamento_id)
            if result:
                actions['ventilador_desligado'] = True
                economia = result['economia_reais']
                actions['motivos'].append(f'💨 Ventilador desligado (economia: R$ {economia:.2f})')

        # ========================================
        # DETECÇÃO DE FALHAS DE ATUADORES
        # ========================================

        if temperatura_anterior is not None and umidade_anterior is not None:
            anomalias_atuador = self.detect_actuator_failure(
                equipamento_id,
                equipamento_nome,
                temperatura_anterior,
                temperatura,
                umidade_anterior,
                umidade,
                temp_sensor_id,
                umid_sensor_id
            )

            # Registrar anomalias detectadas
            for anomalia in anomalias_atuador:
                self.registrar_anomalia_atuador(anomalia)
                # Adicionar aos motivos de ação
                icon = '⚠️' if anomalia['severidade'] == 'ALERTA' else '🔴'
                actions['motivos'].append(f"{icon} {anomalia['mensagem']}")

        # ========================================
        # MONITORAMENTO DE SAÚDE DOS SENSORES
        # ========================================
        self._update_sensor_health_counters(
            temp_sensor_id,
            umid_sensor_id,
            temperatura,
            umidade
        )

        return actions

    def _update_sensor_health_counters(self, temp_sensor_id: int, umid_sensor_id: int,
                                       temperatura: float, umidade: float):
        """
        Atualiza contadores de saúde dos sensores

        Args:
            temp_sensor_id: ID do sensor de temperatura
            umid_sensor_id: ID do sensor de umidade
            temperatura: Leitura de temperatura
            umidade: Leitura de umidade
        """
        # Contar alertas críticos recentes (últimas 24h)
        data_limite = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Sensor de temperatura
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM Alerta a
            JOIN Leitura l ON a.id_leitura = l.id_leitura
            WHERE l.id_sensor = ?
                AND a.tipo_alerta LIKE '%Crítico%'
                AND a.data_alerta >= ?
        """, (temp_sensor_id, data_limite.isoformat()))

        temp_alertas = self.cursor.fetchone()[0]

        # Sensor de umidade
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM Alerta a
            JOIN Leitura l ON a.id_leitura = l.id_leitura
            WHERE l.id_sensor = ?
                AND a.tipo_alerta LIKE '%Crítico%'
                AND a.data_alerta >= ?
        """, (umid_sensor_id, data_limite.isoformat()))

        umid_alertas = self.cursor.fetchone()[0]

        # Detectar leituras anômalas (muito fora do esperado)
        # Considera anômalo se:
        # - Temperatura < 5°C ou > 45°C
        # - Umidade < 10% ou > 98%
        temp_anomala = 1 if (temperatura < 5 or temperatura > 45) else 0
        umid_anomala = 1 if (umidade < 10 or umidade > 98) else 0

        # Atualizar saúde do sensor de temperatura
        if temp_alertas > 0 or temp_anomala:
            self.controller.check_sensor_health(
                temp_sensor_id,
                temp_alertas,
                temp_anomala
            )

        # Atualizar saúde do sensor de umidade
        if umid_alertas > 0 or umid_anomala:
            self.controller.check_sensor_health(
                umid_sensor_id,
                umid_alertas,
                umid_anomala
            )

    def get_actuator_timeline(self, limit: int = 20) -> list:
        """
        Retorna timeline de eventos dos atuadores

        Args:
            limit: Número máximo de eventos

        Returns:
            Lista de eventos ordenados por data (mais recente primeiro)
        """
        # Eventos de início
        self.cursor.execute("""
            SELECT
                'inicio' as tipo_evento,
                a.data_hora_inicio as timestamp,
                at.nome as atuador,
                at.tipo as tipo_atuador,
                'Estufa ' || at.id_equipamento as equipamento,
                a.motivo
            FROM Acionamento a
            JOIN Atuador at ON a.id_atuador = at.id_atuador
            ORDER BY a.data_hora_inicio DESC
            LIMIT ?
        """, (limit,))

        eventos = []
        for row in self.cursor.fetchall():
            eventos.append({
                'tipo_evento': 'Ligado',
                'timestamp': row[1],
                'atuador': row[2],
                'tipo': row[3],
                'equipamento': row[4],
                'motivo': row[5]
            })

        # Eventos de fim
        self.cursor.execute("""
            SELECT
                'fim' as tipo_evento,
                a.data_hora_fim as timestamp,
                at.nome as atuador,
                at.tipo as tipo_atuador,
                'Estufa ' || at.id_equipamento as equipamento,
                a.duracao_segundos,
                a.economia_kwh
            FROM Acionamento a
            JOIN Atuador at ON a.id_atuador = at.id_atuador
            WHERE a.data_hora_fim IS NOT NULL
            ORDER BY a.data_hora_fim DESC
            LIMIT ?
        """, (limit,))

        for row in self.cursor.fetchall():
            eventos.append({
                'tipo_evento': 'Desligado',
                'timestamp': row[1],
                'atuador': row[2],
                'tipo': row[3],
                'equipamento': row[4],
                'duracao_segundos': row[5],
                'economia_kwh': row[6]
            })

        # Ordenar por timestamp (mais recente primeiro)
        eventos.sort(key=lambda x: x['timestamp'], reverse=True)

        return eventos[:limit]

    def get_equipment_efficiency_ranking(self) -> list:
        """
        Retorna ranking de eficiência dos equipamentos

        Returns:
            Lista ordenada por eficiência (melhor primeiro)
        """
        self.cursor.execute("""
            SELECT
                e.id_equipamento,
                e.nome,
                COUNT(CASE WHEN l.qualidade = 'Normal' THEN 1 END) * 100.0 / NULLIF(COUNT(l.id_leitura), 0) as pct_normal,
                COUNT(DISTINCT ac.id_acionamento) as num_acionamentos,
                COALESCE(SUM(ac.economia_kwh), 0) as economia_total
            FROM Leitura l
            JOIN Sensor s ON l.id_sensor = s.id_sensor
            JOIN Equipamento e ON s.id_equipamento = e.id_equipamento
            LEFT JOIN Atuador a ON e.id_equipamento = a.id_equipamento
            LEFT JOIN Acionamento ac ON a.id_atuador = ac.id_atuador
                AND ac.data_hora_fim IS NOT NULL
            WHERE l.data_hora >= datetime('now', '-7 days')
            GROUP BY e.id_equipamento, e.nome
            ORDER BY pct_normal DESC, economia_total DESC
        """)

        ranking = []
        for idx, row in enumerate(self.cursor.fetchall(), 1):
            ranking.append({
                'ranking': idx,
                'equipamento_id': row[0],
                'equipamento': row[1],
                'pct_normal': round(row[2], 1),
                'num_acionamentos': row[3],
                'economia_kwh': round(row[4], 2),
                'economia_reais': round(row[4] * ActuatorController.CUSTO_KWH, 2)
            })

        return ranking
