"""
Repositório base com operações comuns
"""
from typing import List, Optional, Type, TypeVar
from config.database import Database

T = TypeVar('T')


class BaseRepository:
    """Classe base para repositórios"""

    def __init__(self, db: Database, model_class: Type[T], table_name: str):
        self.db = db
        self.model_class = model_class
        self.table_name = table_name

    def _execute_query(self, query: str, params: tuple = ()):
        """Executa uma query e retorna resultados"""
        with self.db.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def _execute_insert(self, query: str, params: tuple = ()) -> int:
        """Executa um insert e retorna o ID inserido"""
        with self.db.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid

    def find_all(self) -> List[T]:
        """Busca todos os registros"""
        query = f"SELECT * FROM {self.table_name}"
        rows = self._execute_query(query)
        return [self.model_class.from_db_row(row) for row in rows]

    def find_by_id(self, id_value: int, id_column: str = None) -> Optional[T]:
        """Busca por ID"""
        if id_column is None:
            id_column = f"id_{self.table_name.lower()}"

        query = f"SELECT * FROM {self.table_name} WHERE {id_column} = ?"
        rows = self._execute_query(query, (id_value,))

        if rows:
            return self.model_class.from_db_row(rows[0])
        return None

    def delete_by_id(self, id_value: int, id_column: str = None) -> bool:
        """Deleta por ID"""
        if id_column is None:
            id_column = f"id_{self.table_name.lower()}"

        query = f"DELETE FROM {self.table_name} WHERE {id_column} = ?"
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (id_value,))
            return cursor.rowcount > 0
