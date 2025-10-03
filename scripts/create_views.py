#!/usr/bin/env python3
"""
Script para criar VIEWs no SQLite para simplificar queries do dashboard
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'farmtech.db'

def create_views():
    """Cria VIEWs para o dashboard"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # DROP views se existirem
    cursor.execute("DROP VIEW IF EXISTS Leitura")
    cursor.execute("DROP VIEW IF EXISTS Alerta")

    # Renomear tabelas originais
    cursor.execute("ALTER TABLE Leitura RENAME TO Leitura_Base")
    cursor.execute("ALTER TABLE Alerta RENAME TO Alerta_Base")

    # Criar VIEW Leitura com colunas adicionais
    cursor.execute("""
        CREATE VIEW Leitura AS
        SELECT
            l.id_leitura,
            l.id_sensor,
            ts.nome as tipo_sensor,
            l.valor,
            l.data_hora,
            l.qualidade,
            e.nome as equipamento
        FROM Leitura_Base l
        JOIN Sensor s ON l.id_sensor = s.id_sensor
        JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
        LEFT JOIN Equipamento e ON s.id_equipamento = e.id_equipamento
    """)

    # Criar VIEW Alerta com colunas renomeadas
    cursor.execute("""
        CREATE VIEW Alerta AS
        SELECT
            a.id_alerta,
            a.id_leitura,
            a.mensagem as descricao,
            CASE
                WHEN a.tipo_alerta LIKE '%Crítico%' OR a.tipo_alerta LIKE '%Critico%' THEN 'Critico'
                WHEN a.tipo_alerta LIKE '%Alerta%' THEN 'Alerta'
                ELSE 'Normal'
            END as nivel_severidade,
            a.data_alerta as data_hora_alerta,
            a.resolvido
        FROM Alerta_Base a
    """)

    conn.commit()
    conn.close()

    print("✅ VIEWs criadas com sucesso!")

if __name__ == '__main__':
    create_views()
