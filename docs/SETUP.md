# 🌱 FarmTech Solutions - Guia de Instalação e Uso

## 📋 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## 🚀 Instalação

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

## 🗄️ Configuração do Banco de Dados

### 1. Inicializar o banco SQLite

```bash
python scripts/init_database.py
```

Este script irá:
- Criar o banco de dados SQLite em `db/farmtech.db`
- Criar todas as tabelas necessárias
- Inserir dados iniciais (4 estufas, 8 sensores, 8 atuadores)

## 🔄 Executar o Simulador IoT

O simulador gera leituras de temperatura e umidade a cada 2 segundos, passa pelo modelo ML para classificação e salva no banco de dados.

```bash
python scripts/run_simulator.py
```

**Características do simulador:**
- Gera valores de temperatura entre 18°C e 32°C
- Umidade inversamente proporcional à temperatura (40% a 90%)
- Usa modelo ML treinado para classificar em Normal/Alerta/Crítico
- Salva leituras na tabela `Leitura`
- Cria alertas automáticos quando necessário

Para parar o simulador, pressione `Ctrl+C`.

## 📊 Dashboard Streamlit

Execute o dashboard em um terminal separado (enquanto o simulador está rodando):

```bash
streamlit run dashboard/app.py
```

O dashboard será aberto automaticamente no navegador (geralmente em http://localhost:8501).

**Funcionalidades:**
- Visualização em tempo real das 4 estufas
- Mostra temperatura, umidade e status atual
- Auto-refresh configurável (padrão: 3 segundos)
- Estatísticas gerais no sidebar
- Código de cores: Verde (Normal), Amarelo (Alerta), Vermelho (Crítico)

## 📁 Estrutura do Projeto

```
projeto_reply_sprint3/
├── config/              # Configurações e conexão com banco
│   ├── settings.py     # Configurações centralizadas
│   └── database.py     # Gerenciador de conexão SQLite
├── models/              # Modelos de domínio
│   ├── equipamento.py
│   ├── sensor.py
│   ├── leitura.py
│   ├── atuador.py
│   └── alerta.py
├── repositories/        # Camada de acesso a dados
│   ├── base_repository.py
│   ├── equipamento_repository.py
│   ├── sensor_repository.py
│   ├── leitura_repository.py
│   └── alerta_repository.py
├── services/            # Lógica de negócio
│   ├── ml_predictor.py          # Predição com ML
│   ├── simulator.py             # Simulador IoT
│   └── monitoring_service.py    # Orquestração
├── dashboard/           # Interface Streamlit
│   ├── app.py          # Aplicação principal
│   └── components/     # Componentes visuais
├── scripts/            # Scripts de inicialização
│   ├── init_database.py
│   └── run_simulator.py
├── db/                 # Banco de dados
│   ├── create_tables.sql
│   └── farmtech.db    # (criado automaticamente)
└── notebooks/          # Modelos ML treinados
    ├── best_model.pkl
    ├── scaler.pkl
    └── label_encoder.pkl
```

## 🔍 Fluxo de Funcionamento

1. **Simulador** gera temperatura e umidade para cada estufa
2. **MLPredictor** classifica os valores (Normal/Alerta/Crítico)
3. **LeituraRepository** salva no banco de dados
4. **AlertaRepository** cria alertas se necessário
5. **Dashboard** consulta e exibe dados em tempo real

## 🛠️ Comandos Úteis

### Parar todos os processos em background
```bash
# Listar processos Python
ps aux | grep python

# Matar processo específico
kill <PID>
```

### Limpar banco de dados
```bash
rm db/farmtech.db
python scripts/init_database.py
```

## 📝 Notas Importantes

- O simulador deve estar rodando para que o dashboard mostre dados em tempo real
- Os modelos ML já estão treinados e salvos em `notebooks/`
- O banco SQLite é criado automaticamente no primeiro uso
- Cada estufa tem 2 sensores (temperatura e umidade) e 2 atuadores (irrigação e ventilação)

## 🐛 Troubleshooting

### Erro: "Modelos ML não encontrados"
Verifique se os arquivos estão em `notebooks/`:
- best_model.pkl
- scaler.pkl
- label_encoder.pkl

### Erro: "Banco de dados não encontrado"
Execute: `python scripts/init_database.py`

### Dashboard não mostra dados
Verifique se o simulador está rodando: `python scripts/run_simulator.py`
