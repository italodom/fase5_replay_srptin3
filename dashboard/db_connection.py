"""
Módulo de conexão com Oracle Database
FarmTech Solutions - Dashboard
"""

import os
import pandas as pd
try:
    import oracledb
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False
    print("⚠️ Aviso: Biblioteca oracledb não instalada. Usando modo simulação.")

from config import DB_CONFIG, QUERIES


class DatabaseConnection:
    """Gerencia conexão com Oracle Database"""

    def __init__(self):
        """Inicializa conexão"""
        self.connection = None
        self.use_mock = not ORACLE_AVAILABLE

        # Carregar credenciais de variáveis de ambiente
        self.user = os.getenv('ORACLE_USER', DB_CONFIG.get('user'))
        self.password = os.getenv('ORACLE_PASSWORD', DB_CONFIG.get('password'))
        self.dsn = os.getenv('ORACLE_DSN', DB_CONFIG.get('dsn'))

    def connect(self):
        """Estabelece conexão com o banco"""
        if self.use_mock:
            print("📊 Modo SIMULAÇÃO ativado (sem banco Oracle)")
            return True

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
            print(f"❌ Erro ao conectar ao banco: {e}")
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
            df = pd.read_sql(query, self.connection, params=params)
            return df
        except Exception as e:
            print(f"❌ Erro ao executar query: {e}")
            return pd.DataFrame()

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
