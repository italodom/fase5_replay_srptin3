"""
Serviço de predição com Machine Learning
"""
import joblib
import numpy as np
from typing import Tuple
from config.settings import Settings


class MLPredictor:
    """Classe para realizar predições usando o modelo treinado"""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self._load_models()

    def _load_models(self):
        """Carrega os modelos salvos"""
        try:
            self.model = joblib.load(Settings.ML_MODEL_PATH)
            self.scaler = joblib.load(Settings.ML_SCALER_PATH)
            self.label_encoder = joblib.load(Settings.ML_LABEL_ENCODER_PATH)
            print("✓ Modelos ML carregados com sucesso")
        except Exception as e:
            print(f"✗ Erro ao carregar modelos ML: {e}")
            raise

    def predict(self, temperatura: float, umidade: float) -> Tuple[str, float]:
        """
        Faz predição baseada em temperatura e umidade

        Args:
            temperatura: Valor da temperatura em °C
            umidade: Valor da umidade em %

        Returns:
            Tupla (classe_predita, confiança)
        """
        # Preparar features (temperatura, umidade, hora, dia_semana, is_dia)
        # Para simulação, usar valores padrão para hora e dia
        from datetime import datetime
        now = datetime.now()
        hora = now.hour
        dia_semana = now.weekday()
        is_dia = 1 if 6 <= hora <= 18 else 0

        # Criar array de features
        features = np.array([[temperatura, umidade, hora, dia_semana, is_dia]])

        # Normalizar
        features_scaled = self.scaler.transform(features)

        # Fazer predição
        prediction = self.model.predict(features_scaled)[0]
        prediction_proba = self.model.predict_proba(features_scaled)[0]

        # Decodificar classe
        classe = self.label_encoder.inverse_transform([prediction])[0]
        confianca = max(prediction_proba)

        return classe, confianca

    def classify_by_rules(self, temperatura: float, umidade: float) -> str:
        """
        Classificação por regras (fallback se ML falhar)

        Args:
            temperatura: Valor da temperatura em °C
            umidade: Valor da umidade em %

        Returns:
            Classe: 'Normal', 'Alerta' ou 'Critico'
        """
        # Condições ideais
        if (Settings.TEMP_IDEAL_MIN <= temperatura <= Settings.TEMP_IDEAL_MAX and
            Settings.HUMIDITY_IDEAL_MIN <= umidade <= Settings.HUMIDITY_IDEAL_MAX):
            return 'Normal'

        # Condições críticas
        if (temperatura < Settings.TEMP_CRITICO_MIN or
            temperatura > Settings.TEMP_CRITICO_MAX or
            umidade < Settings.HUMIDITY_CRITICO_MIN or
            umidade > Settings.HUMIDITY_CRITICO_MAX):
            return 'Critico'

        # Condições de alerta
        return 'Alerta'
