"""
Gerenciador de conexão com banco de dados SQLite
"""
import sqlite3
from typing import Optional
from contextlib import contextmanager
from config.settings import Settings


class Database:
    """Singleton para gerenciar conexão com SQLite"""

    _instance: Optional['Database'] = None
    _connection: Optional[sqlite3.Connection] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._connection is None:
            self._connect()

    def _connect(self):
        """Estabelece conexão com o banco de dados"""
        Settings.ensure_db_dir()
        self._connection = sqlite3.connect(
            Settings.get_db_path(),
            check_same_thread=False
        )
        self._connection.row_factory = sqlite3.Row

    def get_connection(self) -> sqlite3.Connection:
        """Retorna a conexão ativa"""
        if self._connection is None:
            self._connect()
        return self._connection

    @contextmanager
    def get_cursor(self):
        """Context manager para cursor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    def execute_script(self, script_path: str):
        """Executa um script SQL"""
        with open(script_path, 'r', encoding='utf-8') as f:
            script = f.read()

        with self.get_cursor() as cursor:
            cursor.executescript(script)

    def close(self):
        """Fecha a conexão"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def __del__(self):
        self.close()
