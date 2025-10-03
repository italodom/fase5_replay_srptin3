# 📊 Dashboard - FarmTech Solutions

Dashboard interativo de monitoramento IoT com Machine Learning para sistema de estufas agrícolas.

## 🎯 Funcionalidades

### **KPIs Principais**
- Total de leituras realizadas
- Percentual de leituras: Normal / Alerta / Crítico
- Número de alertas ativos

### **Gráficos Interativos**
- **Série Temporal:** Evolução de temperatura e umidade ao longo do tempo
- **Distribuição:** Leituras por equipamento e qualidade
- **Heatmap:** Concentração de alertas por hora do dia

### **Sistema de Alertas**
- Banner vermelho para alertas críticos
- Tabela de alertas ativos com filtros
- Níveis de severidade: Alerta / Crítico

### **Performance ML**
- Visualização da distribuição de classificações
- Métricas do modelo Gradient Boosting
- Informações sobre artefatos (`.pkl`)

---

## 📁 Estrutura de Arquivos

```
dashboard/
├── app.py              # Aplicação principal Streamlit
├── config.py           # Configurações e thresholds
├── db_connection.py    # Conexão com Oracle Database
├── requirements.txt    # Dependências Python
├── assets/             # Recursos visuais
│   └── logo-fiap.png
├── screenshots/        # Prints do dashboard
└── README.md           # Este arquivo
```

---

## 🚀 Como Executar

### **1. Instalar Dependências**

```bash
cd dashboard/
pip install -r requirements.txt
```

### **2. Configurar Banco de Dados (Opcional)**

#### **Opção A: Usar Modo Simulação** (Padrão)
Não precisa configurar nada. O dashboard roda com dados mockados.

#### **Opção B: Conectar ao Oracle Real**
Configure as variáveis de ambiente:

```bash
export ORACLE_USER="seu_usuario"
export ORACLE_PASSWORD="sua_senha"
export ORACLE_DSN="localhost:1521/XE"
```

Ou crie um arquivo `.env`:
```
ORACLE_USER=seu_usuario
ORACLE_PASSWORD=sua_senha
ORACLE_DSN=localhost:1521/XE
```

### **3. Executar Dashboard**

```bash
streamlit run app.py
```

O dashboard abrirá automaticamente em: **http://localhost:8501**

---

## ⚙️ Configurações

### **Thresholds de Alerta** (`config.py`)

#### **Temperatura**
```python
'min_ideal': 18°C      # Mínimo ideal
'max_ideal': 28°C      # Máximo ideal
'critico_baixo': 15°C  # Abaixo disso → Crítico
'critico_alto': 32°C   # Acima disso → Crítico
```

#### **Umidade**
```python
'min_ideal': 50%       # Mínimo ideal
'max_ideal': 80%       # Máximo ideal
'critico_baixo': 40%   # Abaixo disso → Crítico
'critico_alto': 90%    # Acima disso → Crítico
```

### **Auto-Refresh**
- Intervalo padrão: 30 segundos
- Pode ser ativado/desativado na sidebar

### **Número de Leituras Exibidas**
- Padrão: 100 leituras mais recentes
- Configurável em `config.py`

---

## 🗄️ Conexão com Banco de Dados

### **Modo Simulação** (Padrão)
- Ativado automaticamente se:
  - Biblioteca `oracledb` não instalada
  - Credenciais não configuradas
  - Erro ao conectar
- Usa dados mockados realistas
- Ideal para testes e demonstrações

### **Modo Produção** (Oracle)
- Requer Oracle Database instalado
- Credenciais via variáveis de ambiente
- Executa queries reais nas tabelas:
  - `LEITURA`
  - `SENSOR`
  - `ALERTA`
  - `EQUIPAMENTO`
  - `TIPO_SENSOR`

### **Testar Conexão**
```bash
python db_connection.py
```

Saída esperada:
```
✅ Conectado ao Oracle Database
📊 Total de leituras no banco: 14400
```

---

## 📊 Componentes do Dashboard

### **1. Header**
- Logo FarmTech Solutions
- Título e subtítulo

### **2. Sidebar**
- Logo FIAP
- Controle de auto-refresh
- Status da conexão (Simulação/Oracle)
- Timestamp da última atualização

### **3. KPIs (Cards)**
- 5 métricas principais
- Cores e ícones indicativos
- Atualização em tempo real

### **4. Banner de Alerta**
- Aparece apenas se houver alertas críticos
- Destaque visual vermelho
- Contagem de equipamentos afetados

### **5. Gráficos (Tabs)**

#### **Tab 1: Série Temporal**
- Linha dupla (temperatura + umidade)
- Linhas de threshold (ideal/crítico)
- Eixo Y duplo (°C e %)
- Hover interativo

#### **Tab 2: Distribuição**
- Gráfico de barras por equipamento
- Cores por qualidade (verde/amarelo/vermelho)
- Comparação entre estufas

#### **Tab 3: Heatmap**
- Mapa de calor 24h
- Identificação de padrões temporais
- Alertas por hora do dia

### **6. Tabela de Alertas**
- Lista de alertas não resolvidos
- Filtros por severidade
- Ordenação por data/hora
- Informações detalhadas

### **7. Performance ML**
- Gráfico de pizza (distribuição)
- Métricas do modelo
- Links para artefatos

### **8. Footer**
- Créditos e informações do projeto

---

## 🎨 Cores e Temas

```python
COLORS = {
    'normal': '#28a745',    # Verde
    'alerta': '#ffc107',    # Amarelo
    'critico': '#dc3545',   # Vermelho
    'primary': '#007bff',   # Azul
}
```

### **Paleta por Equipamento**
- Estufa 1: `#FF6B6B` (Vermelho claro)
- Estufa 2: `#4ECDC4` (Turquesa)
- Estufa 3: `#45B7D1` (Azul)
- Estufa 4: `#96CEB4` (Verde menta)

---

## 🐛 Troubleshooting

### **Erro: "ModuleNotFoundError: No module named 'oracledb'"**
**Solução:**
```bash
pip install oracledb
```
Ou rode em modo simulação (não precisa instalar).

### **Erro: "Credenciais do banco não configuradas"**
**Solução:**
Configure as variáveis de ambiente ou rode em modo simulação.

### **Dashboard não atualiza automaticamente**
**Solução:**
Marque o checkbox "Auto-refresh" na sidebar.

### **Gráficos aparecem vazios**
**Solução:**
- Verifique se há dados no banco
- Em modo simulação, os dados são gerados automaticamente
- Verifique logs no terminal

---

## 📸 Screenshots

_(Adicione screenshots em `/dashboard/screenshots/` após executar)_

- `dashboard_full.png` - Visão geral completa
- `kpis.png` - Cards de KPIs
- `graficos.png` - Tabs de gráficos
- `alertas.png` - Tabela de alertas
- `alerta_critico.png` - Banner de alerta crítico

---

## 📦 Dependências

```txt
streamlit>=1.28.0      # Framework do dashboard
plotly>=5.14.0         # Gráficos interativos
oracledb>=1.4.0        # Conexão Oracle (opcional)
pandas>=1.5.0          # Manipulação de dados
```

---

## 🔗 Links Úteis

- **Documentação Streamlit:** https://docs.streamlit.io
- **Plotly Docs:** https://plotly.com/python/
- **Oracle Python Driver:** https://python-oracledb.readthedocs.io

---

## 📝 Notas

- Dashboard roda em **modo simulação** por padrão (não precisa de banco)
- Ideal para demonstrações e testes
- Produção: Configure Oracle Database
- Personalização: Edite `config.py`

---

**FarmTech Solutions - Sprint 3**
**Última atualização:** 02/10/2025
