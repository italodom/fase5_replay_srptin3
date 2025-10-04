"""
Modelo de Sensor
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Sensor:
    """Representa um sensor"""

    id_sensor: Optional[int] = None
    id_tipo_sensor: int = 0
    tipo_sensor_nome: Optional[str] = None
    id_equipamento: Optional[int] = None
    modelo: str = ""
    fabricante: str = ""
    data_instalacao: Optional[datetime] = None
    status: str = "Ativo"
    intervalo_leitura: int = 60

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'id_sensor': self.id_sensor,
            'id_tipo_sensor': self.id_tipo_sensor,
            'tipo_sensor_nome': self.tipo_sensor_nome,
            'id_equipamento': self.id_equipamento,
            'modelo': self.modelo,
            'fabricante': self.fabricante,
            'data_instalacao': self.data_instalacao,
            'status': self.status,
            'intervalo_leitura': self.intervalo_leitura
        }

    @classmethod
    def from_db_row(cls, row) -> 'Sensor':
        """Cria instância a partir de uma linha do banco"""
        row_dict = dict(row)
        return cls(
            id_sensor=row_dict['id_sensor'],
            id_tipo_sensor=row_dict['id_tipo_sensor'],
            tipo_sensor_nome=row_dict.get('tipo_sensor_nome'),
            id_equipamento=row_dict['id_equipamento'],
            modelo=row_dict['modelo'],
            fabricante=row_dict['fabricante'],
            data_instalacao=row_dict['data_instalacao'],
            status=row_dict['status'],
            intervalo_leitura=row_dict['intervalo_leitura']
        )
