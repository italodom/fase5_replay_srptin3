"""
Repositório de Equipamentos
"""
from typing import List, Optional
from config.database import Database
from models.equipamento import Equipamento
from repositories.base_repository import BaseRepository


class EquipamentoRepository(BaseRepository):
    """Repositório para gerenciar equipamentos"""

    def __init__(self, db: Database):
        super().__init__(db, Equipamento, "Equipamento")

    def find_all_with_cultura(self) -> List[Equipamento]:
        """Busca todos os equipamentos com informações da cultura"""
        query = """
            SELECT
                e.id_equipamento,
                e.nome,
                e.localizacao,
                e.id_cultura,
                c.nome as cultura_nome,
                e.data_instalacao,
                e.status
            FROM Equipamento e
            LEFT JOIN Cultura c ON e.id_cultura = c.id_cultura
            ORDER BY e.id_equipamento
        """
        rows = self._execute_query(query)
        return [Equipamento.from_db_row(row) for row in rows]

    def find_by_id_with_cultura(self, id_equipamento: int) -> Optional[Equipamento]:
        """Busca equipamento por ID com informações da cultura"""
        query = """
            SELECT
                e.id_equipamento,
                e.nome,
                e.localizacao,
                e.id_cultura,
                c.nome as cultura_nome,
                e.data_instalacao,
                e.status
            FROM Equipamento e
            LEFT JOIN Cultura c ON e.id_cultura = c.id_cultura
            WHERE e.id_equipamento = ?
        """
        rows = self._execute_query(query, (id_equipamento,))
        if rows:
            return Equipamento.from_db_row(rows[0])
        return None

    def find_active(self) -> List[Equipamento]:
        """Busca equipamentos ativos"""
        query = """
            SELECT
                e.id_equipamento,
                e.nome,
                e.localizacao,
                e.id_cultura,
                c.nome as cultura_nome,
                e.data_instalacao,
                e.status
            FROM Equipamento e
            LEFT JOIN Cultura c ON e.id_cultura = c.id_cultura
            WHERE e.status = 'Ativo'
            ORDER BY e.id_equipamento
        """
        rows = self._execute_query(query)
        return [Equipamento.from_db_row(row) for row in rows]
