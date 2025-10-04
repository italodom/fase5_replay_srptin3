"""
Repositório de Leituras
"""
from typing import List, Optional
from datetime import datetime
from config.database import Database
from models.leitura import Leitura
from repositories.base_repository import BaseRepository


class LeituraRepository(BaseRepository):
    """Repositório para gerenciar leituras de sensores"""

    def __init__(self, db: Database):
        super().__init__(db, Leitura, "Leitura")

    def save(self, leitura: Leitura) -> int:
        """Salva uma nova leitura"""
        query = """
            INSERT INTO Leitura (id_sensor, valor, data_hora, qualidade)
            VALUES (?, ?, ?, ?)
        """
        return self._execute_insert(
            query,
            (leitura.id_sensor, leitura.valor, leitura.data_hora, leitura.qualidade)
        )

    def find_latest_by_sensor(self, id_sensor: int) -> Optional[Leitura]:
        """Busca a última leitura de um sensor"""
        query = """
            SELECT * FROM Leitura
            WHERE id_sensor = ?
            ORDER BY data_hora DESC
            LIMIT 1
        """
        rows = self._execute_query(query, (id_sensor,))
        if rows:
            return Leitura.from_db_row(rows[0])
        return None

    def find_by_equipamento(self, id_equipamento: int, limit: int = 100) -> List[Leitura]:
        """Busca leituras de um equipamento"""
        query = """
            SELECT l.* FROM Leitura l
            JOIN Sensor s ON l.id_sensor = s.id_sensor
            WHERE s.id_equipamento = ?
            ORDER BY l.data_hora DESC
            LIMIT ?
        """
        rows = self._execute_query(query, (id_equipamento, limit))
        return [Leitura.from_db_row(row) for row in rows]

    def get_latest_readings_by_equipamento(self, id_equipamento: int) -> dict:
        """Retorna as últimas leituras de temperatura e umidade de um equipamento"""
        query = """
            SELECT
                ts.nome as tipo_sensor,
                l.valor,
                l.qualidade,
                l.data_hora
            FROM Leitura l
            JOIN Sensor s ON l.id_sensor = s.id_sensor
            JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
            WHERE s.id_equipamento = ?
            AND ts.nome IN ('Temperatura', 'Umidade')
            AND l.id_leitura IN (
                SELECT MAX(id_leitura)
                FROM Leitura l2
                JOIN Sensor s2 ON l2.id_sensor = s2.id_sensor
                WHERE s2.id_equipamento = ?
                GROUP BY s2.id_tipo_sensor
            )
        """
        rows = self._execute_query(query, (id_equipamento, id_equipamento))

        result = {}
        for row in rows:
            result[row['tipo_sensor']] = {
                'valor': row['valor'],
                'qualidade': row['qualidade'],
                'data_hora': row['data_hora']
            }
        return result
