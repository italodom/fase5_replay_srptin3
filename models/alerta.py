"""
Modelo de Alerta
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Alerta:
    """Representa um alerta do sistema"""

    id_alerta: Optional[int] = None
    id_leitura: int = 0
    tipo_alerta: str = ""
    mensagem: str = ""
    data_alerta: Optional[datetime] = None
    resolvido: str = "N"
    data_resolucao: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'id_alerta': self.id_alerta,
            'id_leitura': self.id_leitura,
            'tipo_alerta': self.tipo_alerta,
            'mensagem': self.mensagem,
            'data_alerta': self.data_alerta,
            'resolvido': self.resolvido,
            'data_resolucao': self.data_resolucao
        }

    @classmethod
    def from_db_row(cls, row) -> 'Alerta':
        """Cria instância a partir de uma linha do banco"""
        row_dict = dict(row)
        return cls(
            id_alerta=row_dict['id_alerta'],
            id_leitura=row_dict['id_leitura'],
            tipo_alerta=row_dict['tipo_alerta'],
            mensagem=row_dict['mensagem'],
            data_alerta=row_dict['data_alerta'],
            resolvido=row_dict['resolvido'],
            data_resolucao=row_dict.get('data_resolucao')
        )
