"""
Script para visualizar leituras dos sensores
FarmTech Solutions - Sprint 3
Adaptado do Sprint 2
"""

import pandas as pd
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# Configurações
CSV_PATH = "../data/sensor_data.csv"
OUTPUT_PATH = "prints/readings_chart.png"
NUM_READINGS = 100  # Últimas N leituras a serem visualizadas

def load_data(csv_path):
    """Carrega dados do CSV"""
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Dados carregados: {len(df)} registros")
        return df
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo {csv_path} não encontrado!")
        sys.exit(1)

def filter_data(df, num_readings=100):
    """Filtra últimas N leituras de temperatura e umidade"""
    # Filtrar apenas sensores de temperatura e umidade
    df_temp = df[df['tipo_sensor'] == 'Temperatura'].tail(num_readings).copy()
    df_umid = df[df['tipo_sensor'] == 'Umidade'].tail(num_readings).copy()

    print(f"📊 Temperatura: {len(df_temp)} leituras")
    print(f"📊 Umidade: {len(df_umid)} leituras")

    return df_temp, df_umid

def create_visualization(df_temp, df_umid, output_path):
    """Cria gráfico de visualização"""

    # Criar numeração de leituras
    df_temp['Leitura'] = range(1, len(df_temp) + 1)
    df_umid['Leitura'] = range(1, len(df_umid) + 1)

    # Criar figura com dois subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    # Plot da Temperatura
    ax1.plot(df_temp["Leitura"], df_temp["valor"],
             color="#FF5733", marker='o', linewidth=2, markersize=4, alpha=0.7)
    ax1.set_title("Temperatura ao Longo das Leituras", fontsize=16, fontweight='bold')
    ax1.set_ylabel("Temperatura (°C)", fontsize=13)
    ax1.grid(True, linestyle='--', alpha=0.4)
    ax1.axhline(y=18, color='green', linestyle='--', alpha=0.3, label='Min Ideal (18°C)')
    ax1.axhline(y=28, color='green', linestyle='--', alpha=0.3, label='Max Ideal (28°C)')
    ax1.axhline(y=32, color='red', linestyle='--', alpha=0.3, label='Crítico (>32°C)')
    ax1.legend(loc='upper right', fontsize=9)

    # Plot da Umidade
    ax2.plot(df_umid["Leitura"], df_umid["valor"],
             color="#3399FF", marker='x', linestyle='--', linewidth=2, markersize=4, alpha=0.7)
    ax2.set_title("Umidade ao Longo das Leituras", fontsize=16, fontweight='bold')
    ax2.set_xlabel("Número da Leitura", fontsize=13)
    ax2.set_ylabel("Umidade Relativa (%)", fontsize=13)
    ax2.grid(True, linestyle='--', alpha=0.4)
    ax2.axhline(y=50, color='green', linestyle='--', alpha=0.3, label='Min Ideal (50%)')
    ax2.axhline(y=80, color='green', linestyle='--', alpha=0.3, label='Max Ideal (80%)')
    ax2.axhline(y=40, color='red', linestyle='--', alpha=0.3, label='Crítico (<40%)')
    ax2.legend(loc='upper right', fontsize=9)

    # Ajustar layout
    plt.subplots_adjust(hspace=0.3)
    plt.tight_layout()

    # Salvar
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Gráfico salvo em: {output_path}")

    # Mostrar (opcional)
    # plt.show()

def print_statistics(df_temp, df_umid):
    """Imprime estatísticas básicas"""
    print("\n" + "="*60)
    print("📈 ESTATÍSTICAS DAS LEITURAS")
    print("="*60)

    print("\n🌡️  TEMPERATURA:")
    print(f"   Média: {df_temp['valor'].mean():.2f}°C")
    print(f"   Mínima: {df_temp['valor'].min():.2f}°C")
    print(f"   Máxima: {df_temp['valor'].max():.2f}°C")
    print(f"   Desvio Padrão: {df_temp['valor'].std():.2f}°C")

    print("\n💧 UMIDADE:")
    print(f"   Média: {df_umid['valor'].mean():.2f}%")
    print(f"   Mínima: {df_umid['valor'].min():.2f}%")
    print(f"   Máxima: {df_umid['valor'].max():.2f}%")
    print(f"   Desvio Padrão: {df_umid['valor'].std():.2f}%")

    print("\n" + "="*60)

def main():
    """Função principal"""
    print("🌱 FarmTech Solutions - Visualização de Leituras")
    print("="*60)

    # Carregar dados
    df = load_data(CSV_PATH)

    # Filtrar dados
    df_temp, df_umid = filter_data(df, NUM_READINGS)

    if len(df_temp) == 0 or len(df_umid) == 0:
        print("❌ Erro: Não há dados suficientes para visualizar!")
        sys.exit(1)

    # Criar visualização
    create_visualization(df_temp, df_umid, OUTPUT_PATH)

    # Mostrar estatísticas
    print_statistics(df_temp, df_umid)

    print("\n✨ Processo concluído com sucesso!")

if __name__ == "__main__":
    main()
