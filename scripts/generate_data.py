"""
Script para gerar dados simulados de sensores
FarmTech Solutions - Fase 5
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)

def gerar_dados_sensores(n_dias=30, leituras_por_dia=48):
    """
    Gera dados simulados de sensores de temperatura e umidade
    
    Parâmetros:
    - n_dias: número de dias de simulação
    - leituras_por_dia: número de leituras por dia (48 = uma a cada 30 minutos)
    
    Retorna:
    - DataFrame com os dados simulados
    """
    
    data_inicio = datetime.now() - timedelta(days=n_dias)
    dados = []
    
    # Configuração dos sensores (10 sensores conforme banco.sql)
    sensores = [
        {'id': 1, 'tipo': 'Temperatura', 'equipamento': 1, 'estufa': 'Estufa 1'},
        {'id': 2, 'tipo': 'Umidade', 'equipamento': 1, 'estufa': 'Estufa 1'},
        {'id': 3, 'tipo': 'Umidade Solo', 'equipamento': 1, 'estufa': 'Estufa 1'},
        {'id': 4, 'tipo': 'Temperatura', 'equipamento': 2, 'estufa': 'Estufa 2'},
        {'id': 5, 'tipo': 'Umidade', 'equipamento': 2, 'estufa': 'Estufa 2'},
        {'id': 6, 'tipo': 'Temperatura', 'equipamento': 3, 'estufa': 'Estufa 3'},
        {'id': 7, 'tipo': 'Umidade', 'equipamento': 3, 'estufa': 'Estufa 3'},
        {'id': 8, 'tipo': 'Luminosidade', 'equipamento': 3, 'estufa': 'Estufa 3'},
        {'id': 9, 'tipo': 'Temperatura', 'equipamento': 4, 'estufa': 'Estufa 4'},
        {'id': 10, 'tipo': 'Umidade', 'equipamento': 4, 'estufa': 'Estufa 4'}
    ]
    
    # Parâmetros por tipo de sensor (aumentado para gerar mais alertas)
    parametros = {
        'Temperatura': {
            'media_dia': 26, 'desvio_dia': 6,
            'media_noite': 19, 'desvio_noite': 5,
            'min': 10, 'max': 40
        },
        'Umidade': {
            'media_dia': 65, 'desvio_dia': 15,
            'media_noite': 70, 'desvio_noite': 12,
            'min': 30, 'max': 95
        },
        'Umidade Solo': {
            'media_dia': 45, 'desvio_dia': 10,
            'media_noite': 50, 'desvio_noite': 8,
            'min': 20, 'max': 80
        },
        'Luminosidade': {
            'media_dia': 50000, 'desvio_dia': 20000,
            'media_noite': 0, 'desvio_noite': 100,
            'min': 0, 'max': 100000
        }
    }
    
    total_leituras = n_dias * leituras_por_dia
    
    for sensor in sensores:
        tipo = sensor['tipo']
        param = parametros.get(tipo, parametros['Temperatura'])
        
        for dia in range(n_dias):
            for hora in range(leituras_por_dia):
                timestamp = data_inicio + timedelta(days=dia, hours=hora*0.5)
                hora_do_dia = timestamp.hour
                
                # Determinar se é dia ou noite
                is_dia = 6 <= hora_do_dia <= 18
                
                if is_dia:
                    media = param['media_dia']
                    desvio = param['desvio_dia']
                else:
                    media = param['media_noite']
                    desvio = param['desvio_noite']
                
                # Adicionar variação sazonal (aumentada para gerar mais variabilidade)
                variacao_sazonal = 8 * np.sin(2 * np.pi * dia / 30)
                
                # Gerar valor com ruído
                valor = np.random.normal(media + variacao_sazonal, desvio)
                
                # Aplicar limites
                valor = np.clip(valor, param['min'], param['max'])

                # Simular anomalias ocasionais (15% de chance - aumentado para fins acadêmicos)
                if random.random() < 0.15:
                    anomalia_tipo = random.random()
                    if anomalia_tipo < 0.4:
                        # Pico alto extremo (40-60% acima)
                        valor = valor * random.uniform(1.4, 1.6)
                    elif anomalia_tipo < 0.8:
                        # Pico baixo extremo (40-60% abaixo)
                        valor = valor * random.uniform(0.4, 0.6)
                    else:
                        # Anomalia moderada
                        valor = valor * random.uniform(1.2, 1.35) if random.random() < 0.5 else valor * random.uniform(0.65, 0.8)
                    valor = np.clip(valor, param['min'], param['max'])
                
                # Classificar qualidade da leitura
                if tipo == 'Temperatura':
                    if 18 <= valor <= 28:
                        qualidade = 'Normal'
                    elif 15 <= valor <= 32:
                        qualidade = 'Alerta'
                    else:
                        qualidade = 'Critico'
                elif tipo == 'Umidade':
                    if 50 <= valor <= 80:
                        qualidade = 'Normal'
                    elif 40 <= valor <= 90:
                        qualidade = 'Alerta'
                    else:
                        qualidade = 'Critico'
                elif tipo == 'Umidade Solo':
                    if 35 <= valor <= 65:
                        qualidade = 'Normal'
                    elif 25 <= valor <= 75:
                        qualidade = 'Alerta'
                    else:
                        qualidade = 'Critico'
                else:  # Luminosidade
                    if is_dia and valor > 10000:
                        qualidade = 'Normal'
                    elif not is_dia and valor < 1000:
                        qualidade = 'Normal'
                    else:
                        qualidade = 'Alerta'
                
                dados.append({
                    'id_sensor': sensor['id'],
                    'tipo_sensor': tipo,
                    'equipamento': sensor['equipamento'],
                    'estufa': sensor['estufa'],
                    'valor': round(valor, 2),
                    'data_hora': timestamp,
                    'qualidade': qualidade,
                    'hora_do_dia': hora_do_dia,
                    'dia_semana': timestamp.strftime('%A'),
                    'is_dia': is_dia
                })
    
    df = pd.DataFrame(dados)
    return df

def gerar_estatisticas(df):
    """
    Gera estatísticas dos dados simulados
    """
    print("=" * 60)
    print("ESTATÍSTICAS DOS DADOS GERADOS")
    print("=" * 60)
    
    print(f"\nTotal de leituras: {len(df):,}")
    print(f"Período: {df['data_hora'].min()} até {df['data_hora'].max()}")
    print(f"Número de sensores: {df['id_sensor'].nunique()}")
    
    print("\n--- Leituras por Sensor ---")
    print(df.groupby(['id_sensor', 'tipo_sensor'])['valor'].count().to_string())
    
    print("\n--- Estatísticas por Tipo de Sensor ---")
    stats = df.groupby('tipo_sensor')['valor'].agg(['mean', 'std', 'min', 'max'])
    print(stats)
    
    print("\n--- Distribuição de Qualidade ---")
    print(df['qualidade'].value_counts())
    print(f"\nPercentual de leituras críticas: {(df['qualidade'] == 'Critico').mean()*100:.2f}%")
    
    print("\n--- Leituras por Equipamento ---")
    print(df.groupby('estufa')['valor'].count())
    
    return stats

def exportar_dados(df, formato='csv'):
    """
    Exporta os dados para arquivo
    """
    if formato == 'csv':
        arquivo = '../data/sensor_data.csv'
        df.to_csv(arquivo, index=False)
        print(f"\n✅ Dados exportados para {arquivo}")
    elif formato == 'json':
        arquivo = '../data/sensor_data.json'
        df.to_json(arquivo, orient='records', date_format='iso')
        print(f"\n✅ Dados exportados para {arquivo}")
    
    return arquivo

def gerar_sql_inserts(df, arquivo='../sql/insert_leituras.sql'):
    """
    Gera arquivo SQL com comandos INSERT para as leituras
    """
    with open(arquivo, 'w') as f:
        f.write("-- Inserção de leituras simuladas\n")
        f.write("-- Gerado automaticamente por generate_data.py\n\n")
        
        for _, row in df.iterrows():
            sql = f"INSERT INTO Leitura (id_sensor, valor, data_hora, qualidade) VALUES ("
            sql += f"{row['id_sensor']}, "
            sql += f"{row['valor']}, "
            sql += f"TO_TIMESTAMP('{row['data_hora'].strftime('%Y-%m-%d %H:%M:%S')}', 'YYYY-MM-DD HH24:MI:SS'), "
            sql += f"'{row['qualidade']}');\n"
            f.write(sql)
        
        f.write("\nCOMMIT;\n")
    
    print(f"✅ Arquivo SQL gerado: {arquivo}")

def main():
    """
    Função principal
    """
    print("🌱 FarmTech Solutions - Gerador de Dados de Sensores")
    print("=" * 60)
    
    # Gerar dados para 30 dias, 48 leituras por dia (uma a cada 30 minutos)
    # Total: 30 * 48 * 10 sensores = 14.400 leituras
    df = gerar_dados_sensores(n_dias=30, leituras_por_dia=48)
    
    # Mostrar estatísticas
    stats = gerar_estatisticas(df)
    
    # Exportar dados
    exportar_dados(df, 'csv')
    exportar_dados(df, 'json')
    
    # Gerar arquivo SQL (primeiras 1000 leituras como exemplo)
    gerar_sql_inserts(df.head(1000))
    
    print("\n✨ Processo concluído com sucesso!")
    print(f"📊 Total de {len(df):,} leituras geradas")
    
    return df

if __name__ == "__main__":
    df = main()