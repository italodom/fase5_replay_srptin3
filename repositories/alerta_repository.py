"""
Repositório de Alertas
"""
from typing import List
from config.database import Database
from models.alerta import Alerta
from repositories.base_repository import BaseRepository


class AlertaRepository(BaseRepository):
    """Repositório para gerenciar alertas"""

    def __init__(self, db: Database):
        super().__init__(db, Alerta, "Alerta")

    def save(self, alerta: Alerta) -> int:
        """Salva um novo alerta"""
        query = """
            INSERT INTO Alerta (id_leitura, tipo_alerta, mensagem, data_alerta, resolvido)
            VALUES (?, ?, ?, ?, ?)
        """
        return self._execute_insert(
            query,
            (alerta.id_leitura, alerta.tipo_alerta, alerta.mensagem,
             alerta.data_alerta, alerta.resolvido)
        )

    def find_unresolved(self) -> List[Alerta]:
        """Busca alertas não resolvidos"""
        query = """
            SELECT * FROM Alerta
            WHERE resolvido = 'N'
            ORDER BY data_alerta DESC
        """
        rows = self._execute_query(query)
        return [Alerta.from_db_row(row) for row in rows]

    def find_by_equipamento(self, id_equipamento: int, limit: int = 50) -> List[Alerta]:
        """Busca alertas de um equipamento"""
        query = """
            SELECT a.* FROM Alerta a
            JOIN Leitura l ON a.id_leitura = l.id_leitura
            JOIN Sensor s ON l.id_sensor = s.id_sensor
            WHERE s.id_equipamento = ?
            ORDER BY a.data_alerta DESC
            LIMIT ?
        """
        rows = self._execute_query(query, (id_equipamento, limit))
        return [Alerta.from_db_row(row) for row in rows]

    def resolve(self, id_alerta: int) -> bool:
        """Marca um alerta como resolvido"""
        query = """
            UPDATE Alerta
            SET resolvido = 'S', data_resolucao = CURRENT_TIMESTAMP
            WHERE id_alerta = ?
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (id_alerta,))
            return cursor.rowcount > 0
