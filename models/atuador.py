"""
Modelo de Atuador
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Atuador:
    """Representa um atuador"""

    id_atuador: Optional[int] = None
    tipo: str = ""
    id_equipamento: int = 0
    status: str = "Ativo"
    intensidade: float = 0.0
    data_instalacao: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'id_atuador': self.id_atuador,
            'tipo': self.tipo,
            'id_equipamento': self.id_equipamento,
            'status': self.status,
            'intensidade': self.intensidade,
            'data_instalacao': self.data_instalacao
        }

    @classmethod
    def from_db_row(cls, row) -> 'Atuador':
        """Cria instância a partir de uma linha do banco"""
        return cls(
            id_atuador=row['id_atuador'],
            tipo=row['tipo'],
            id_equipamento=row['id_equipamento'],
            status=row['status'],
            intensidade=row['intensidade'],
            data_instalacao=row['data_instalacao']
        )
