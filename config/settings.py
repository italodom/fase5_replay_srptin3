"""
Configurações centralizadas do sistema FarmTech
"""
import os
from pathlib import Path


class Settings:
    """Classe de configurações do sistema"""

    # Diretórios base
    BASE_DIR = Path(__file__).resolve().parent.parent
    DB_DIR = BASE_DIR / "db"
    MODELS_DIR = BASE_DIR / "notebooks"

    # Banco de dados
    DB_PATH = DB_DIR / "farmtech.db"
    DB_SCHEMA = DB_DIR / "create_tables.sql"

    # Modelos de Machine Learning
    ML_MODEL_PATH = MODELS_DIR / "best_model.pkl"
    ML_SCALER_PATH = MODELS_DIR / "scaler.pkl"
    ML_LABEL_ENCODER_PATH = MODELS_DIR / "label_encoder.pkl"

    # Configurações do simulador
    SIMULATION_INTERVAL = 2  # segundos
    TEMP_MIN = 18.0
    TEMP_MAX = 32.0
    HUMIDITY_MIN = 40.0
    HUMIDITY_MAX = 90.0

    # Configurações do dashboard
    DASHBOARD_REFRESH_INTERVAL = 3  # segundos

    # Limites para classificação
    TEMP_IDEAL_MIN = 18
    TEMP_IDEAL_MAX = 28
    TEMP_CRITICO_MIN = 15
    TEMP_CRITICO_MAX = 32

    HUMIDITY_IDEAL_MIN = 50
    HUMIDITY_IDEAL_MAX = 80
    HUMIDITY_CRITICO_MIN = 40
    HUMIDITY_CRITICO_MAX = 90

    @classmethod
    def get_db_path(cls) -> str:
        """Retorna o caminho do banco de dados"""
        return str(cls.DB_PATH)

    @classmethod
    def get_schema_path(cls) -> str:
        """Retorna o caminho do schema SQL"""
        return str(cls.DB_SCHEMA)

    @classmethod
    def ensure_db_dir(cls):
        """Garante que o diretório do banco existe"""
        cls.DB_DIR.mkdir(parents=True, exist_ok=True)
