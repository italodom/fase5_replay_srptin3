"""
Simulador IoT de Sensores
"""
import random
import time
from datetime import datetime
from typing import Dict, Tuple
from config.settings import Settings


class IoTSimulator:
    """Simula leituras de sensores de temperatura e umidade"""

    def __init__(self):
        # Estado inicial aleatório para cada estufa
        self.estados = {}
        self._initialize_states()

    def _initialize_states(self):
        """Inicializa estados para cada estufa (1 a 4)"""
        for estufa_id in range(1, 5):
            # Temperatura inicial aleatória entre limites
            temp_inicial = random.uniform(
                (Settings.TEMP_MIN + Settings.TEMP_MAX) / 2 - 3,
                (Settings.TEMP_MIN + Settings.TEMP_MAX) / 2 + 3
            )

            # Umidade inicial inversamente proporcional
            umidade_inicial = self._calcular_umidade_inversa(temp_inicial)

            self.estados[estufa_id] = {
                'temperatura': temp_inicial,
                'umidade': umidade_inicial,
                'tendencia_temp': random.choice([-1, 1])  # -1 para baixo, 1 para cima
            }

    def _calcular_umidade_inversa(self, temperatura: float) -> float:
        """
        Calcula umidade inversamente proporcional à temperatura

        Lógica: quanto maior a temperatura, menor a umidade
        """
        # Normalizar temperatura para range 0-1
        temp_norm = (temperatura - Settings.TEMP_MIN) / (Settings.TEMP_MAX - Settings.TEMP_MIN)

        # Inverter (1 - temp_norm) para relação inversa
        umidade_norm = 1 - temp_norm

        # Mapear para range de umidade com alguma variação
        umidade = Settings.HUMIDITY_MIN + (umidade_norm * (Settings.HUMIDITY_MAX - Settings.HUMIDITY_MIN))

        # Adicionar pequena variação aleatória (-5 a +5%)
        variacao = random.uniform(-5, 5)
        umidade += variacao

        # Garantir que fica dentro dos limites
        return max(Settings.HUMIDITY_MIN, min(Settings.HUMIDITY_MAX, umidade))

    def gerar_leitura(self, id_equipamento: int) -> Tuple[float, float]:
        """
        Gera uma nova leitura de temperatura e umidade para um equipamento

        Args:
            id_equipamento: ID do equipamento (estufa)

        Returns:
            Tupla (temperatura, umidade)
        """
        if id_equipamento not in self.estados:
            self._initialize_states()

        estado = self.estados[id_equipamento]

        # Variação na temperatura (-0.5 a +0.5°C)
        variacao_temp = random.uniform(-0.5, 0.5) * estado['tendencia_temp']
        nova_temp = estado['temperatura'] + variacao_temp

        # Inverter tendência se atingir limites (agora permite valores críticos)
        if nova_temp >= Settings.TEMP_MAX + 2:
            estado['tendencia_temp'] = -1
            nova_temp = Settings.TEMP_MAX + 2
        elif nova_temp <= Settings.TEMP_MIN - 2:
            estado['tendencia_temp'] = 1
            nova_temp = Settings.TEMP_MIN - 2

        # Chance aleatória de inverter tendência (15% - aumentado para mais variação)
        if random.random() < 0.15:
            estado['tendencia_temp'] *= -1

        # Calcular umidade inversamente proporcional
        nova_umidade = self._calcular_umidade_inversa(nova_temp)

        # Atualizar estado
        estado['temperatura'] = nova_temp
        estado['umidade'] = nova_umidade

        return round(nova_temp, 2), round(nova_umidade, 2)

    def gerar_leituras_todas_estufas(self) -> Dict[int, Tuple[float, float]]:
        """
        Gera leituras para todas as 4 estufas

        Returns:
            Dicionário {id_equipamento: (temperatura, umidade)}
        """
        leituras = {}
        for estufa_id in range(1, 5):
            leituras[estufa_id] = self.gerar_leitura(estufa_id)
        return leituras
