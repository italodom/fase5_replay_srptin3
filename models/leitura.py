"""
Modelo de Leitura de Sensor
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Leitura:
    """Representa uma leitura de sensor"""

    id_leitura: Optional[int] = None
    id_sensor: int = 0
    valor: float = 0.0
    data_hora: Optional[datetime] = None
    qualidade: str = "Normal"

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'id_leitura': self.id_leitura,
            'id_sensor': self.id_sensor,
            'valor': self.valor,
            'data_hora': self.data_hora,
            'qualidade': self.qualidade
        }

    @classmethod
    def from_db_row(cls, row) -> 'Leitura':
        """Cria instância a partir de uma linha do banco"""
        return cls(
            id_leitura=row['id_leitura'],
            id_sensor=row['id_sensor'],
            valor=row['valor'],
            data_hora=row['data_hora'],
            qualidade=row['qualidade']
        )
