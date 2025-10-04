#!/usr/bin/env python3
"""
Script para executar o simulador IoT
Gera leituras de sensores a cada 2 segundos
"""
import sys
from pathlib import Path
import time

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.monitoring_service import MonitoringService
from config.settings import Settings


def main():
    """Executa o simulador em loop"""
    print("=" * 60)
    print("FARMTECH SOLUTIONS - SIMULADOR IoT")
    print("=" * 60)
    print(f"Intervalo de leitura: {Settings.SIMULATION_INTERVAL} segundos")
    print("Pressione Ctrl+C para parar\n")

    # Criar serviço de monitoramento
    try:
        monitoring = MonitoringService()
        print("✅ Serviço de monitoramento inicializado")
        print("✅ Modelos ML carregados")
        print("\n🚀 Iniciando simulação...\n")

    except Exception as e:
        print(f"✗ Erro ao inicializar serviço: {e}")
        print("\n💡 Dica: Execute primeiro o script init_database.py")
        return 1

    # Loop principal
    ciclo = 0
    try:
        while True:
            ciclo += 1
            print(f"\n📡 Ciclo #{ciclo} - {time.strftime('%H:%M:%S')}")
            print("-" * 60)

            # Processar leituras
            monitoring.processar_ciclo_leitura()

            # Aguardar intervalo
            time.sleep(Settings.SIMULATION_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n⏹️  Simulador interrompido pelo usuário")
        print(f"Total de ciclos executados: {ciclo}")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n✗ Erro durante simulação: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
