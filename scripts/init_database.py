#!/usr/bin/env python3
"""
Script para inicializar o banco de dados SQLite
"""
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import Database
from config.settings import Settings


def main():
    """Inicializa o banco de dados"""
    print("=" * 60)
    print("FARMTECH SOLUTIONS - INICIALIZAÇÃO DO BANCO DE DADOS")
    print("=" * 60)

    # Verificar se arquivo SQL existe
    if not Settings.DB_SCHEMA.exists():
        print(f"✗ Erro: Arquivo SQL não encontrado em {Settings.DB_SCHEMA}")
        return 1

    # Verificar argumento --force
    force = '--force' in sys.argv or '-f' in sys.argv

    # Criar conexão
    db = Database()

    # Verificar se banco já existe
    if Settings.DB_PATH.exists():
        if not force:
            print(f"\n⚠️  Banco de dados já existe em {Settings.DB_PATH}")
            print("Use --force ou -f para recriar automaticamente")
            return 0

        # Remover banco existente
        Settings.DB_PATH.unlink()
        print("🗑️  Banco de dados anterior removido")

    # Executar script SQL
    print(f"\n📝 Executando script SQL de {Settings.DB_SCHEMA}...")

    try:
        db.execute_script(Settings.get_schema_path())
        print("✅ Banco de dados criado com sucesso!")

        # Verificar dados inseridos
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM Equipamento")
            num_equipamentos = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM Sensor")
            num_sensores = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM Atuador")
            num_atuadores = cursor.fetchone()['count']

        print(f"\n📊 Dados iniciais inseridos:")
        print(f"   - Equipamentos (Estufas): {num_equipamentos}")
        print(f"   - Sensores: {num_sensores}")
        print(f"   - Atuadores: {num_atuadores}")

        print(f"\n✨ Banco de dados pronto em: {Settings.DB_PATH}")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"✗ Erro ao criar banco de dados: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
