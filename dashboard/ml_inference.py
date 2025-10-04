"""
Módulo de Inferência de Machine Learning
FarmTech Solutions - Classificação de Condições Ambientais

Este módulo carrega o modelo treinado e faz predições em tempo real
sobre as condições das estufas (Normal, Alerta, Crítico).
"""

import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLPredictor:
    """Classe para fazer predições usando o modelo ML treinado"""

    def __init__(self, models_dir: Optional[str] = None):
        """
        Inicializa o preditor carregando os modelos

        Args:
            models_dir: Diretório onde estão os arquivos .pkl (padrão: ../notebooks)
        """
        if models_dir is None:
            # Diretório padrão: ../notebooks (relativo a este arquivo)
            models_dir = Path(__file__).parent.parent / 'notebooks'
        else:
            models_dir = Path(models_dir)

        self.models_dir = models_dir
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.loaded = False

        # Features esperadas pelo modelo
        self.feature_columns = ['Temperatura', 'Umidade', 'hora', 'dia_semana', 'is_dia']

        # Carregar modelos
        self._load_models()

    def _load_models(self):
        """Carrega os modelos salvos"""
        try:
            model_path = self.models_dir / 'best_model.pkl'
            scaler_path = self.models_dir / 'scaler.pkl'
            encoder_path = self.models_dir / 'label_encoder.pkl'

            # Verificar se arquivos existem
            if not model_path.exists():
                logger.warning(f"Modelo não encontrado em {model_path}")
                return

            # Carregar modelo
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            self.label_encoder = joblib.load(encoder_path)

            self.loaded = True
            logger.info(f"✅ Modelo ML carregado com sucesso de {self.models_dir}")
            logger.info(f"   Classes: {self.label_encoder.classes_}")

        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelos ML: {e}")
            self.loaded = False

    def predict(self, temperatura: float, umidade: float,
                timestamp: Optional[datetime] = None) -> Tuple[str, float]:
        """
        Faz predição da condição ambiental

        Args:
            temperatura: Temperatura em °C
            umidade: Umidade em %
            timestamp: Timestamp da leitura (usa now() se None)

        Returns:
            Tupla (condicao, confianca)
            - condicao: 'Normal', 'Alerta' ou 'Critico'
            - confianca: Probabilidade da predição (0-1)
        """
        # Se modelo não carregou, usar fallback (regras simples)
        if not self.loaded:
            return self._fallback_predict(temperatura, umidade)

        try:
            # Preparar timestamp
            if timestamp is None:
                timestamp = datetime.now()

            # Extrair features temporais
            hora = timestamp.hour
            dia_semana = timestamp.weekday()
            is_dia = 1 if 6 <= hora <= 18 else 0

            # Criar DataFrame com as features
            features_dict = {
                'Temperatura': temperatura,
                'Umidade': umidade,
                'hora': hora,
                'dia_semana': dia_semana,
                'is_dia': is_dia
            }

            X = pd.DataFrame([features_dict])[self.feature_columns]

            # Normalizar
            X_scaled = self.scaler.transform(X)

            # Fazer predição
            prediction = self.model.predict(X_scaled)[0]
            prediction_proba = self.model.predict_proba(X_scaled)[0]

            # Decodificar label
            condicao = self.label_encoder.inverse_transform([prediction])[0]
            confianca = float(max(prediction_proba))

            return condicao, confianca

        except Exception as e:
            logger.error(f"Erro na predição ML: {e}")
            # Usar fallback em caso de erro
            return self._fallback_predict(temperatura, umidade)

    def _fallback_predict(self, temperatura: float, umidade: float) -> Tuple[str, float]:
        """
        Predição de fallback usando regras simples (quando ML não disponível)

        Args:
            temperatura: Temperatura em °C
            umidade: Umidade em %

        Returns:
            Tupla (condicao, confianca)
        """
        # Regras de negócio simples (mesmas do treinamento)
        if 18 <= temperatura <= 28 and 50 <= umidade <= 80:
            return 'Normal', 1.0
        elif temperatura < 15 or temperatura > 32 or umidade < 40 or umidade > 90:
            return 'Critico', 1.0
        else:
            return 'Alerta', 1.0

    def get_model_info(self) -> dict:
        """
        Retorna informações sobre o modelo carregado

        Returns:
            Dicionário com informações do modelo
        """
        if not self.loaded:
            return {
                'loaded': False,
                'message': 'Modelo não carregado - usando regras simples'
            }

        return {
            'loaded': True,
            'model_type': type(self.model).__name__,
            'features': self.feature_columns,
            'classes': self.label_encoder.classes_.tolist(),
            'models_dir': str(self.models_dir)
        }


# Instância global (singleton) para reutilizar o modelo carregado
_global_predictor = None

def get_predictor() -> MLPredictor:
    """
    Retorna instância global do preditor (singleton)

    Returns:
        Instância de MLPredictor
    """
    global _global_predictor
    if _global_predictor is None:
        _global_predictor = MLPredictor()
    return _global_predictor


def predict_quality(temperatura: float, umidade: float,
                    timestamp: Optional[datetime] = None) -> str:
    """
    Função de conveniência para fazer predição direta

    Args:
        temperatura: Temperatura em °C
        umidade: Umidade em %
        timestamp: Timestamp da leitura (opcional)

    Returns:
        Condição predita: 'Normal', 'Alerta' ou 'Critico'
    """
    predictor = get_predictor()
    condicao, _ = predictor.predict(temperatura, umidade, timestamp)
    return condicao


# Teste do módulo quando executado diretamente
if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DO MÓDULO ML INFERENCE")
    print("=" * 60)

    # Criar preditor
    predictor = MLPredictor()

    # Mostrar info do modelo
    info = predictor.get_model_info()
    print(f"\nInformações do Modelo:")
    print(f"  Carregado: {info['loaded']}")
    if info['loaded']:
        print(f"  Tipo: {info['model_type']}")
        print(f"  Classes: {info['classes']}")
        print(f"  Features: {info['features']}")

    # Fazer predições de teste
    print(f"\nPredições de Teste:")
    print("-" * 60)

    test_cases = [
        (22.0, 65.0, "Normal"),
        (35.0, 45.0, "Crítico - Temp alta"),
        (16.0, 92.0, "Crítico - Umid alta"),
        (30.0, 75.0, "Alerta - Temp no limite"),
    ]

    for temp, umid, descricao in test_cases:
        condicao, confianca = predictor.predict(temp, umid)
        print(f"\nCaso: {descricao}")
        print(f"  Entrada: Temp={temp}°C, Umid={umid}%")
        print(f"  Predição: {condicao}")
        print(f"  Confiança: {confianca*100:.1f}%")

    print("\n" + "=" * 60)
