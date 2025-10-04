"""
Repositório de Sensores
"""
from typing import List, Optional
from config.database import Database
from models.sensor import Sensor
from repositories.base_repository import BaseRepository


class SensorRepository(BaseRepository):
    """Repositório para gerenciar sensores"""

    def __init__(self, db: Database):
        super().__init__(db, Sensor, "Sensor")

    def find_by_equipamento(self, id_equipamento: int) -> List[Sensor]:
        """Busca sensores de um equipamento específico"""
        query = """
            SELECT
                s.id_sensor,
                s.id_tipo_sensor,
                ts.nome as tipo_sensor_nome,
                s.id_equipamento,
                s.modelo,
                s.fabricante,
                s.data_instalacao,
                s.status,
                s.intervalo_leitura
            FROM Sensor s
            JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
            WHERE s.id_equipamento = ?
            ORDER BY ts.nome
        """
        rows = self._execute_query(query, (id_equipamento,))
        return [Sensor.from_db_row(row) for row in rows]

    def find_by_tipo(self, id_equipamento: int, tipo_nome: str) -> Optional[Sensor]:
        """Busca sensor por tipo em um equipamento"""
        query = """
            SELECT
                s.id_sensor,
                s.id_tipo_sensor,
                ts.nome as tipo_sensor_nome,
                s.id_equipamento,
                s.modelo,
                s.fabricante,
                s.data_instalacao,
                s.status,
                s.intervalo_leitura
            FROM Sensor s
            JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
            WHERE s.id_equipamento = ? AND ts.nome = ?
        """
        rows = self._execute_query(query, (id_equipamento, tipo_nome))
        if rows:
            return Sensor.from_db_row(rows[0])
        return None
