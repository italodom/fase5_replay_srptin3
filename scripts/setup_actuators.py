#!/usr/bin/env python3
"""
Script para adicionar tabelas de atuadores ao banco SQLite existente
e popular com dados iniciais.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random

# Caminhos
DB_PATH = Path(__file__).parent.parent / 'data' / 'farmtech.db'
SCHEMA_PATH = Path(__file__).parent.parent / 'db' / 'atuadores_schema.sql'


def add_actuator_tables():
    """Adiciona as tabelas de atuadores ao banco existente"""

    print("🔧 Configurando sistema de atuadores...")

    if not DB_PATH.exists():
        print(f"❌ Erro: Banco de dados não encontrado em {DB_PATH}")
        print("   Execute 'python scripts/setup_sqlite.py' primeiro!")
        return False

    # Conectar ao banco
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ler schema SQL
    print("📋 Lendo schema de atuadores...")
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Executar statements SQL
    print("🔨 Criando tabelas de atuadores...")

    # Limpar comentários do schema
    import re
    lines = []
    for line in schema_sql.split('\n'):
        # Remover comentários de linha
        if line.strip().startswith('--'):
            continue
        # Remover comentários inline
        line = re.sub(r'--.*$', '', line)
        if line.strip():
            lines.append(line)

    cleaned_sql = '\n'.join(lines)

    # Separar por CREATE statements para melhor feedback
    create_table_pattern = r'CREATE TABLE (\w+)'
    create_view_pattern = r'CREATE VIEW (\w+)'
    create_index_pattern = r'CREATE INDEX (\w+)'

    tables = re.findall(create_table_pattern, cleaned_sql)
    views = re.findall(create_view_pattern, cleaned_sql)
    indexes = re.findall(create_index_pattern, cleaned_sql)

    try:
        # Usar executescript para executar múltiplos statements
        cursor.executescript(cleaned_sql)

        # Feedback
        for table in tables:
            print(f"   ✓ Tabela {table} criada")
        for view in views:
            print(f"   ✓ VIEW {view} criada")
        if indexes:
            print(f"   ✓ {len(indexes)} índices criados")

        print("✅ Estrutura criada com sucesso!\n")
    except sqlite3.Error as e:
        if 'already exists' in str(e):
            print(f"   ⚠️  Algumas estruturas já existem (continuando...)\n")
        else:
            print(f"   ❌ Erro ao criar estrutura: {e}\n")
            conn.close()
            return False

    conn.commit()

    # Popular dados iniciais
    print("🌱 Populando dados iniciais...")

    # 1. Atuadores (Bombas e Ventiladores para cada estufa)
    atuadores = [
        # Estufa 1
        ('Bomba Estufa 1', 'Bomba', 1, 'Ativo', 500),  # 500W
        ('Ventilador Estufa 1', 'Ventilador', 1, 'Ativo', 150),  # 150W
        # Estufa 2
        ('Bomba Estufa 2', 'Bomba', 2, 'Ativo', 500),
        ('Ventilador Estufa 2', 'Ventilador', 2, 'Ativo', 150),
        # Estufa 3
        ('Bomba Estufa 3', 'Bomba', 3, 'Ativo', 500),
        ('Ventilador Estufa 3', 'Ventilador', 3, 'Ativo', 150),
        # Estufa 4
        ('Bomba Estufa 4', 'Bomba', 4, 'Ativo', 500),
        ('Ventilador Estufa 4', 'Ventilador', 4, 'Ativo', 150),
    ]

    cursor.executemany("""
        INSERT INTO Atuador (nome, tipo, id_equipamento, status, potencia_watts)
        VALUES (?, ?, ?, ?, ?)
    """, atuadores)

    print(f"   ✓ {len(atuadores)} atuadores criados (4 bombas + 4 ventiladores)")

    # 2. Saúde dos Sensores (inicializar todos como Normal)
    cursor.execute("SELECT DISTINCT id_sensor FROM Leitura")
    sensores = cursor.fetchall()

    for (id_sensor,) in sensores:
        cursor.execute("""
            INSERT INTO Sensor_Health (id_sensor, status_saude, num_alertas_criticos, num_leituras_anomalas)
            VALUES (?, 'Normal', 0, 0)
        """, (id_sensor,))

    print(f"   ✓ {len(sensores)} sensores inicializados com status 'Normal'")

    # 3. Criar alguns acionamentos históricos (últimos 7 dias)
    print("📊 Gerando histórico de acionamentos (últimos 7 dias)...")

    cursor.execute("SELECT id_atuador, tipo, potencia_watts FROM Atuador")
    atuadores_db = cursor.fetchall()

    acionamentos_count = 0
    now = datetime.now()

    for id_atuador, tipo, potencia_watts in atuadores_db:
        # Gerar 20-40 acionamentos aleatórios nos últimos 7 dias
        num_acionamentos = random.randint(20, 40)

        for _ in range(num_acionamentos):
            # Data aleatória nos últimos 7 dias
            dias_atras = random.randint(0, 7)
            hora_inicio = now - timedelta(
                days=dias_atras,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            # Duração: 5-60 minutos
            duracao_minutos = random.randint(5, 60)
            hora_fim = hora_inicio + timedelta(minutes=duracao_minutos)
            duracao_segundos = duracao_minutos * 60

            # Motivo baseado no tipo
            if tipo == 'Bomba':
                motivos = ['Umidade Baixa', 'Irrigação Programada', 'Temperatura Alta']
            else:  # Ventilador
                motivos = ['Temperatura Alta', 'Umidade Alta', 'Ventilação Programada']

            motivo = random.choice(motivos)

            # Calcular economia (vs. sistema 24/7)
            # Sistema inteligente liga apenas quando necessário
            # Economia = (24h - horas_ligadas) * potencia_watts / 1000
            horas_ligadas_dia = duracao_minutos / 60
            economia_kwh = ((24 - horas_ligadas_dia) * potencia_watts / 1000) / num_acionamentos

            cursor.execute("""
                INSERT INTO Acionamento
                (id_atuador, data_hora_inicio, data_hora_fim, motivo, duracao_segundos, economia_kwh)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                id_atuador,
                hora_inicio.strftime('%Y-%m-%d %H:%M:%S'),
                hora_fim.strftime('%Y-%m-%d %H:%M:%S'),
                motivo,
                duracao_segundos,
                round(economia_kwh, 3)
            ))

            acionamentos_count += 1

    print(f"   ✓ {acionamentos_count} acionamentos históricos criados")

    conn.commit()

    # Estatísticas finais
    print("\n📈 Estatísticas do sistema de atuadores:")

    cursor.execute("SELECT COUNT(*) FROM Atuador")
    print(f"   Atuadores: {cursor.fetchone()[0]}")

    cursor.execute("SELECT tipo, COUNT(*) FROM Atuador GROUP BY tipo")
    for tipo, count in cursor.fetchall():
        print(f"     - {tipo}: {count}")

    cursor.execute("SELECT COUNT(*) FROM Acionamento")
    print(f"   Acionamentos históricos: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM Sensor_Health")
    print(f"   Sensores monitorados: {cursor.fetchone()[0]}")

    cursor.execute("""
        SELECT status_saude, COUNT(*)
        FROM Sensor_Health
        GROUP BY status_saude
    """)
    print("   Status de saúde dos sensores:")
    for status, count in cursor.fetchall():
        print(f"     - {status}: {count}")

    # Economia total
    cursor.execute("SELECT SUM(economia_kwh) FROM Acionamento")
    economia_total = cursor.fetchone()[0]
    if economia_total:
        print(f"\n💰 Economia total estimada: {economia_total:.2f} kWh")
        # Assumindo R$ 0,80 por kWh
        economia_reais = economia_total * 0.80
        print(f"   Equivalente a: R$ {economia_reais:.2f}")

    conn.close()
    print(f"\n✅ Sistema de atuadores configurado com sucesso!")
    return True


if __name__ == '__main__':
    success = add_actuator_tables()
    if not success:
        exit(1)
