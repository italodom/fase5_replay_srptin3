#!/usr/bin/env python3
"""
Script de inicialização - FarmTech Solutions
Inicia o simulador IoT e o dashboard Streamlit em paralelo
"""

import subprocess
import sys
import os
import time
from pathlib import Path


def main():
    """Função principal"""
    print("=" * 70)
    print("🌱 FarmTech Solutions - Sistema IoT")
    print("=" * 70)
    print()

    # Determinar diretório raiz do projeto
    project_root = Path(__file__).parent.parent
    dashboard_dir = project_root / "dashboard"

    # Verificar se deve ativar anomalias
    print("Configuração de Anomalias:")
    print("  Para ativar anomalias críticas, execute:")
    print("  export ANOMALIAS_ATIVAS=true")
    print()

    # Iniciar simulador IoT em background
    print("🚀 Iniciando Simulador IoT em background...")
    iot_simulator_path = dashboard_dir / "iot_simulator.py"

    iot_process = subprocess.Popen(
        [sys.executable, str(iot_simulator_path)],
        cwd=str(dashboard_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Aguardar 2 segundos para o simulador iniciar
    time.sleep(2)

    # Verificar se o simulador está rodando
    if iot_process.poll() is not None:
        print("❌ Erro ao iniciar simulador IoT")
        print("Verifique os logs acima para mais detalhes")
        return 1

    print("✅ Simulador IoT iniciado (PID: {})".format(iot_process.pid))
    print()

    # Iniciar dashboard Streamlit
    print("🚀 Iniciando Dashboard Streamlit...")
    app_path = dashboard_dir / "app.py"

    streamlit_process = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run",
            str(app_path),
            "--server.port=8501"
        ],
        cwd=str(dashboard_dir)
    )

    print("✅ Dashboard Streamlit iniciado (PID: {})".format(streamlit_process.pid))
    print()
    print("=" * 70)
    print("Sistema iniciado com sucesso!")
    print("=" * 70)
    print()
    print("📊 Dashboard: http://localhost:8501")
    print("📡 Simulador IoT: Rodando em background")
    print()
    print("Para encerrar: Pressione Ctrl+C")
    print("=" * 70)
    print()

    try:
        # Aguardar até que o usuário encerre
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Encerrando sistema...")

        # Encerrar processos
        print("   Encerrando Dashboard...")
        streamlit_process.terminate()
        streamlit_process.wait(timeout=5)

        print("   Encerrando Simulador IoT...")
        iot_process.terminate()
        iot_process.wait(timeout=5)

        print("✅ Sistema encerrado")
        return 0


if __name__ == "__main__":
    sys.exit(main())
