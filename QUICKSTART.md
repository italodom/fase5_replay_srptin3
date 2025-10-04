# 🚀 FarmTech Solutions - Início Rápido

## ✅ Sistema Implementado

Sistema IoT completo para monitoramento de estufas com:
- **4 Estufas** com culturas diferentes
- **8 Sensores** (2 por estufa: temperatura e umidade)
- **8 Atuadores** (2 por estufa: irrigação e ventilação)
- **Simulador IoT** com leituras a cada 2 segundos
- **Machine Learning** para classificação (Normal/Alerta/Crítico)
- **Dashboard Streamlit** em tempo real
- **Banco SQLite** para persistência

## 🎯 Como Executar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Criar banco de dados
```bash
python scripts/init_database.py --force
```

### 3. Iniciar o simulador (Terminal 1)
```bash
python scripts/run_simulator.py
```

### 4. Iniciar o dashboard (Terminal 2)
```bash
streamlit run dashboard/app.py
```

### 5. Acessar o dashboard
Abrir navegador em: http://localhost:8501

## 📊 Como Funciona

1. **Simulador** gera temperatura (18-32°C) e umidade (40-90%) inversamente proporcionais
2. **ML Predictor** classifica as leituras usando modelo Gradient Boosting treinado
3. **Banco de dados** armazena todas as leituras
4. **Dashboard** exibe dados em tempo real com auto-refresh

## 🏗️ Arquitetura Orientada a Objetos

```
config/              → Configurações e Database (Singleton)
models/              → Entidades de domínio (Equipamento, Sensor, Leitura, etc)
repositories/        → Camada de acesso a dados (BaseRepository + especializados)
services/            → Lógica de negócio (MLPredictor, IoTSimulator, MonitoringService)
dashboard/           → Interface Streamlit com componentes reutilizáveis
scripts/             → Scripts de inicialização
```

## ✨ Funcionalidades

### Simulador IoT
- Gera valores realistas com relação inversa temp/umidade
- Variação gradual com tendências
- Executa a cada 2 segundos
- Salva automaticamente no banco
- Cria alertas quando necessário

### Machine Learning
- Modelo: Gradient Boosting (F1-Score: 1.0)
- Features: temperatura, umidade, hora, dia_semana, is_dia
- Classificação: Normal / Alerta / Crítico
- Fallback com regras de negócio

### Dashboard
- Grid 2x2 com cards das estufas
- Cores: Verde (Normal), Amarelo (Alerta), Vermelho (Crítico)
- Auto-refresh configurável (1-10s)
- Estatísticas gerais no sidebar

## 📁 Arquivos Principais

- `db/create_tables.sql` - Schema SQLite
- `config/database.py` - Singleton de conexão
- `services/monitoring_service.py` - Orquestrador principal
- `dashboard/app.py` - Interface Streamlit
- `scripts/run_simulator.py` - Executor do simulador

## 🔍 Verificar Dados

```bash
# Ver total de leituras
sqlite3 db/farmtech.db "SELECT COUNT(*) FROM Leitura"

# Ver últimas leituras
sqlite3 db/farmtech.db "SELECT * FROM Leitura ORDER BY id_leitura DESC LIMIT 10"

# Ver alertas
sqlite3 db/farmtech.db "SELECT * FROM Alerta WHERE resolvido = 'N'"
```

## 📝 Notas

- Modelos ML já estão treinados em `notebooks/`
- Simulador deve estar rodando para dashboard mostrar dados atualizados
- Banco SQLite é thread-safe (Singleton pattern)
- Relação temperatura/umidade é inversamente proporcional
