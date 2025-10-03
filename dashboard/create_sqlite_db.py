"""
Script para criar banco SQLite local para testes
FarmTech Solutions - Dashboard

Cria tabelas e popula com dados do CSV
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path

# Caminhos
DB_PATH = Path(__file__).parent.parent / 'data' / 'farmtech.db'
CSV_PATH = Path(__file__).parent.parent / 'data' / 'sensor_data.csv'

def create_tables(conn):
    """Cria tabelas no SQLite"""
    cursor = conn.cursor()

    # Tabela LEITURA (simplificada)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Leitura (
            id_leitura INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sensor INTEGER,
            tipo_sensor TEXT,
            equipamento TEXT,
            valor REAL,
            data_hora TIMESTAMP,
            qualidade TEXT
        )
    ''')

    # Tabela ALERTA (simplificada)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Alerta (
            id_alerta INTEGER PRIMARY KEY AUTOINCREMENT,
            id_leitura INTEGER,
            descricao TEXT,
            nivel_severidade TEXT,
            data_hora_alerta TIMESTAMP,
            resolvido TEXT DEFAULT 'N',
            FOREIGN KEY (id_leitura) REFERENCES Leitura(id_leitura)
        )
    ''')

    conn.commit()
    print("✅ Tabelas criadas")

def populate_from_csv(conn):
    """Popula tabelas com dados do CSV"""
    if not CSV_PATH.exists():
        print(f"❌ Arquivo CSV não encontrado: {CSV_PATH}")
        return

    # Ler CSV
    df = pd.read_csv(CSV_PATH)
    print(f"📊 Lendo {len(df)} registros do CSV...")

    # Inserir na tabela Leitura
    df_insert = df[['id_sensor', 'tipo_sensor', 'equipamento', 'estufa', 'valor', 'data_hora', 'qualidade']].copy()
    df_insert.rename(columns={'estufa': 'equipamento'}, inplace=True)

    df_insert.to_sql('Leitura', conn, if_exists='replace', index_label='id_leitura')
    print(f"✅ {len(df_insert)} leituras inseridas")

    # Criar alguns alertas de exemplo
    cursor = conn.cursor()

    # Alertas para leituras críticas
    cursor.execute('''
        INSERT INTO Alerta (id_leitura, descricao, nivel_severidade, data_hora_alerta, resolvido)
        SELECT
            id_leitura,
            'Temperatura ' || CASE
                WHEN valor > 32 THEN 'acima do limite crítico (' || valor || '°C)'
                WHEN valor < 15 THEN 'abaixo do limite crítico (' || valor || '°C)'
                ELSE 'em nível de alerta'
            END,
            CASE
                WHEN qualidade = 'Critico' THEN 'Critico'
                ELSE 'Alerta'
            END,
            data_hora,
            'N'
        FROM Leitura
        WHERE qualidade IN ('Critico', 'Alerta')
        AND tipo_sensor = 'Temperatura'
        LIMIT 10
    ''')

    conn.commit()
    print(f"✅ {cursor.rowcount} alertas criados")

def create_indexes(conn):
    """Cria índices para performance"""
    cursor = conn.cursor()

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_leitura_data
        ON Leitura(data_hora DESC)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_leitura_qualidade
        ON Leitura(qualidade)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_alerta_resolvido
        ON Alerta(resolvido)
    ''')

    conn.commit()
    print("✅ Índices criados")

def print_statistics(conn):
    """Imprime estatísticas do banco"""
    cursor = conn.cursor()

    # Total de leituras
    cursor.execute("SELECT COUNT(*) FROM Leitura")
    total = cursor.fetchone()[0]

    # Por qualidade
    cursor.execute("""
        SELECT qualidade, COUNT(*) as total
        FROM Leitura
        GROUP BY qualidade
    """)
    por_qualidade = cursor.fetchall()

    # Alertas ativos
    cursor.execute("SELECT COUNT(*) FROM Alerta WHERE resolvido = 'N'")
    alertas = cursor.fetchone()[0]

    print("\n" + "="*60)
    print("📈 ESTATÍSTICAS DO BANCO SQLite")
    print("="*60)
    print(f"\n📊 Total de leituras: {total:,}")
    print("\n📊 Leituras por qualidade:")
    for qual, count in por_qualidade:
        print(f"   - {qual}: {count:,}")
    print(f"\n🚨 Alertas ativos: {alertas}")
    print("\n" + "="*60)

def main():
    """Função principal"""
    print("🌱 FarmTech Solutions - Criação de Banco SQLite")
    print("="*60)

    # Verificar se CSV existe
    if not CSV_PATH.exists():
        print(f"❌ Erro: CSV não encontrado em {CSV_PATH}")
        print("💡 Execute primeiro: python scripts/generate_data.py")
        return

    # Remover banco existente (opcional)
    if DB_PATH.exists():
        resposta = input(f"\n⚠️  Banco {DB_PATH.name} já existe. Recriar? (s/n): ")
        if resposta.lower() != 's':
            print("❌ Operação cancelada")
            return
        DB_PATH.unlink()
        print("🗑️  Banco antigo removido")

    # Criar conexão
    print(f"\n📁 Criando banco em: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    try:
        # Criar estrutura
        create_tables(conn)

        # Popular com dados
        populate_from_csv(conn)

        # Criar índices
        create_indexes(conn)

        # Mostrar estatísticas
        print_statistics(conn)

        print("\n✨ Banco SQLite criado com sucesso!")
        print(f"📍 Localização: {DB_PATH}")
        print("\n💡 Para usar no dashboard:")
        print("   1. cd dashboard/")
        print("   2. streamlit run app.py")
        print("   3. O dashboard detectará automaticamente o SQLite")

    except Exception as e:
        print(f"\n❌ Erro ao criar banco: {e}")
        import traceback
        traceback.print_exc()

    finally:
        conn.close()

if __name__ == "__main__":
    main()
