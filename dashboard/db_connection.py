"""
Módulo de conexão com Banco de Dados
FarmTech Solutions - Dashboard

Suporta 3 modos:
1. Oracle (produção)
2. SQLite (teste local)
3. Mock (simulação sem banco)
"""

import os
import sqlite3
import pandas as pd

# Tentar importar oracledb
try:
    import oracledb
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False

from config import DB_CONFIG, QUERIES


class DatabaseConnection:
    """Gerencia conexão com banco de dados (Oracle ou SQLite)"""

    def __init__(self, db_type='auto'):
        """
        Inicializa conexão

        Args:
            db_type: 'oracle', 'sqlite', 'mock' ou 'auto' (detecta automaticamente)
        """
        self.connection = None
        self.db_type = db_type
        self.use_mock = False

        # SQLite database path
        self.sqlite_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'data',
            'farmtech.db'
        )

        # Carregar credenciais Oracle de variáveis de ambiente
        self.user = os.getenv('ORACLE_USER', DB_CONFIG.get('user'))
        self.password = os.getenv('ORACLE_PASSWORD', DB_CONFIG.get('password'))
        self.dsn = os.getenv('ORACLE_DSN', DB_CONFIG.get('dsn'))

        # Auto-detectar tipo de banco
        if self.db_type == 'auto':
            self._auto_detect_db_type()

    def _auto_detect_db_type(self):
        """Detecta automaticamente qual tipo de banco usar"""
        # Prioridade 1: Oracle se credenciais disponíveis
        if ORACLE_AVAILABLE and all([self.user, self.password, self.dsn]):
            self.db_type = 'oracle'
        # Prioridade 2: SQLite se arquivo existe
        elif os.path.exists(self.sqlite_path):
            self.db_type = 'sqlite'
        # Prioridade 3: Mock
        else:
            self.db_type = 'mock'
            self.use_mock = True

    def connect(self):
        """Estabelece conexão com o banco"""
        if self.db_type == 'mock' or self.use_mock:
            print("📊 Modo SIMULAÇÃO ativado (dados mockados)")
            return True

        elif self.db_type == 'sqlite':
            return self._connect_sqlite()

        elif self.db_type == 'oracle':
            return self._connect_oracle()

        else:
            print(f"❌ Tipo de banco inválido: {self.db_type}")
            self.use_mock = True
            return False

    def _connect_sqlite(self):
        """Conecta ao SQLite"""
        try:
            self.connection = sqlite3.connect(
                self.sqlite_path,
                check_same_thread=False  # Permite uso em múltiplas threads (necessário para Streamlit)
            )
            print(f"✅ Conectado ao SQLite: {self.sqlite_path}")
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar ao SQLite: {e}")
            print("📊 Usando modo SIMULAÇÃO")
            self.use_mock = True
            return False

    def _connect_oracle(self):
        """Conecta ao Oracle"""
        if not ORACLE_AVAILABLE:
            print("❌ oracledb não disponível")
            print("📊 Usando modo SIMULAÇÃO")
            self.use_mock = True
            return False

        try:
            if not all([self.user, self.password, self.dsn]):
                raise ValueError(
                    "Credenciais do banco não configuradas. "
                    "Configure ORACLE_USER, ORACLE_PASSWORD e ORACLE_DSN"
                )

            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            print("✅ Conectado ao Oracle Database")
            return True

        except Exception as e:
            print(f"❌ Erro ao conectar ao Oracle: {e}")
            print("📊 Usando modo SIMULAÇÃO")
            self.use_mock = True
            return False

    def disconnect(self):
        """Fecha conexão"""
        if self.connection:
            self.connection.close()
            print("🔌 Desconectado do banco")

    def execute_query(self, query, params=None):
        """Executa query e retorna DataFrame"""
        if self.use_mock:
            return self._get_mock_data(query)

        try:
            # Adaptar query para SQLite se necessário
            if self.db_type == 'sqlite':
                query = self._adapt_query_for_sqlite(query)

            df = pd.read_sql(query, self.connection, params=params)

            # SQLite retorna colunas em minúsculas, converter para maiúsculas
            if self.db_type == 'sqlite' and not df.empty:
                df.columns = df.columns.str.upper()

            return df
        except Exception as e:
            print(f"❌ Erro ao executar query: {e}")
            return pd.DataFrame()

    def _adapt_query_for_sqlite(self, query):
        """Adapta queries Oracle para SQLite"""
        # Substituir TO_TIMESTAMP por datetime
        query = query.replace('TO_TIMESTAMP', 'datetime')

        # Substituir FETCH FIRST N ROWS ONLY por LIMIT
        if 'FETCH FIRST' in query:
            import re
            query = re.sub(
                r'FETCH FIRST\s+:num_rows\s+ROWS ONLY',
                'LIMIT :num_rows',
                query,
                flags=re.IGNORECASE
            )

        # Substituir NVL por COALESCE (caso exista)
        query = query.replace('NVL(', 'COALESCE(')

        # Ajustar alias para maiúsculas (SQLite é case-sensitive)
        query = query.replace(' as total', ' as TOTAL')
        query = query.replace(' as qualidade', ' as QUALIDADE')
        query = query.replace(' as tipo_sensor', ' as TIPO_SENSOR')
        query = query.replace(' as equipamento', ' as EQUIPAMENTO')
        query = query.replace(' as media_valor', ' as MEDIA_VALOR')

        return query

    def _get_mock_data(self, query):
        """Retorna dados mockados para testes sem banco"""
        import random
        from datetime import datetime, timedelta

        # Identifica qual query está sendo executada
        if 'COUNT(*)' in query and 'Leitura' in query and 'GROUP BY' not in query:
            # total_leituras
            return pd.DataFrame({'TOTAL': [14400]})

        elif 'GROUP BY qualidade' in query:
            # leituras_por_qualidade
            return pd.DataFrame({
                'QUALIDADE': ['Normal', 'Alerta', 'Critico'],
                'TOTAL': [6750, 5050, 2600]
            })

        elif 'Alerta' in query and 'resolvido' in query:
            # alertas_ativos
            return pd.DataFrame({
                'ID_ALERTA': [1, 2, 3],
                'ID_LEITURA': [1001, 1502, 2003],
                'DESCRICAO': [
                    'Temperatura acima do limite',
                    'Umidade abaixo do ideal',
                    'Temperatura crítica'
                ],
                'NIVEL_SEVERIDADE': ['Alerta', 'Alerta', 'Critico'],
                'DATA_HORA_ALERTA': [
                    datetime.now() - timedelta(hours=2),
                    datetime.now() - timedelta(hours=1),
                    datetime.now() - timedelta(minutes=30)
                ],
                'TIPO_SENSOR': ['Temperatura', 'Umidade', 'Temperatura'],
                'EQUIPAMENTO': ['Estufa 1', 'Estufa 2', 'Estufa 3']
            })

        elif 'ORDER BY l.data_hora DESC' in query:
            # leituras_recentes
            num_rows = 100
            data = []
            base_time = datetime.now()

            for i in range(num_rows):
                sensor_type = random.choice(['Temperatura', 'Umidade'])
                equipamento = f"Estufa {random.randint(1, 4)}"

                if sensor_type == 'Temperatura':
                    valor = round(random.uniform(15, 35), 2)
                    if 18 <= valor <= 28:
                        qualidade = 'Normal'
                    elif 15 <= valor <= 32:
                        qualidade = 'Alerta'
                    else:
                        qualidade = 'Critico'
                else:  # Umidade
                    valor = round(random.uniform(30, 95), 2)
                    if 50 <= valor <= 80:
                        qualidade = 'Normal'
                    elif 40 <= valor <= 90:
                        qualidade = 'Alerta'
                    else:
                        qualidade = 'Critico'

                data.append({
                    'ID_LEITURA': 14400 - i,
                    'ID_SENSOR': random.randint(1, 10),
                    'TIPO_SENSOR': sensor_type,
                    'VALOR': valor,
                    'DATA_HORA': base_time - timedelta(minutes=i*30),
                    'QUALIDADE': qualidade,
                    'EQUIPAMENTO': equipamento
                })

            return pd.DataFrame(data)

        elif 'metricas_ml' in query.lower() or 'AVG(valor)' in query:
            # metricas_ml
            return pd.DataFrame({
                'QUALIDADE': ['Normal', 'Alerta', 'Critico'],
                'TOTAL': [6750, 5050, 2600],
                'MEDIA_VALOR': [23.5, 29.8, 35.2]
            })

        else:
            # Query não reconhecida - retorna vazio
            return pd.DataFrame()

    # ========================================
    # MÉTODOS ESPECÍFICOS PARA DASHBOARD
    # ========================================

    def get_total_leituras(self):
        """Retorna total de leituras"""
        df = self.execute_query(QUERIES['total_leituras'])
        return df['TOTAL'].iloc[0] if not df.empty else 0

    def get_leituras_por_qualidade(self):
        """Retorna contagem por qualidade"""
        return self.execute_query(QUERIES['leituras_por_qualidade'])

    def get_leituras_recentes(self, num_rows=100):
        """Retorna últimas N leituras"""
        return self.execute_query(
            QUERIES['leituras_recentes'],
            params={'num_rows': num_rows}
        )

    def get_alertas_ativos(self):
        """Retorna alertas não resolvidos"""
        return self.execute_query(QUERIES['alertas_ativos'])

    def get_metricas_ml(self):
        """Retorna métricas do modelo ML"""
        return self.execute_query(QUERIES['metricas_ml'])

    def get_kpis(self):
        """Retorna todos os KPIs do dashboard"""
        total = self.get_total_leituras()
        por_qualidade = self.get_leituras_por_qualidade()
        alertas = self.get_alertas_ativos()

        # Calcular percentuais
        if not por_qualidade.empty:
            total_calc = por_qualidade['TOTAL'].sum()
            percentuais = {}
            for _, row in por_qualidade.iterrows():
                qual = row['QUALIDADE']
                pct = (row['TOTAL'] / total_calc * 100) if total_calc > 0 else 0
                percentuais[qual.lower()] = {
                    'count': int(row['TOTAL']),
                    'percentage': round(pct, 1)
                }
        else:
            percentuais = {
                'normal': {'count': 0, 'percentage': 0},
                'alerta': {'count': 0, 'percentage': 0},
                'critico': {'count': 0, 'percentage': 0}
            }

        return {
            'total_leituras': int(total),
            'percentuais': percentuais,
            'alertas_ativos': len(alertas) if not alertas.empty else 0
        }


# ========================================
# FUNÇÕES AUXILIARES
# ========================================

def test_connection():
    """Testa conexão com o banco"""
    db = DatabaseConnection()
    success = db.connect()

    if success:
        print("\n✅ Teste de conexão bem-sucedido!")
        if not db.use_mock:
            total = db.get_total_leituras()
            print(f"📊 Total de leituras no banco: {total}")
        else:
            print("📊 Usando dados simulados (mock)")
        db.disconnect()
    else:
        print("\n❌ Falha no teste de conexão")

    return success


if __name__ == "__main__":
    # Teste de conexão ao executar diretamente
    test_connection()
