"""
Modelo de Equipamento (Estufa)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Equipamento:
    """Representa um equipamento (estufa)"""

    id_equipamento: Optional[int] = None
    nome: str = ""
    localizacao: str = ""
    id_cultura: Optional[int] = None
    cultura_nome: Optional[str] = None
    data_instalacao: Optional[datetime] = None
    status: str = "Ativo"

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'id_equipamento': self.id_equipamento,
            'nome': self.nome,
            'localizacao': self.localizacao,
            'id_cultura': self.id_cultura,
            'cultura_nome': self.cultura_nome,
            'data_instalacao': self.data_instalacao,
            'status': self.status
        }

    @classmethod
    def from_db_row(cls, row) -> 'Equipamento':
        """Cria instância a partir de uma linha do banco"""
        row_dict = dict(row)
        return cls(
            id_equipamento=row_dict['id_equipamento'],
            nome=row_dict['nome'],
            localizacao=row_dict['localizacao'],
            id_cultura=row_dict['id_cultura'],
            cultura_nome=row_dict.get('cultura_nome'),
            data_instalacao=row_dict['data_instalacao'],
            status=row_dict['status']
        )
