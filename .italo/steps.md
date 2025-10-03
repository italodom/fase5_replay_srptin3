# 🎯 Plano de Implementação - Entrega 4 (Sprint 3)

## **FASE 1: ARQUITETURA E ESTRUTURA** (30 min)

### 1. Criar Diagrama de Arquitetura
- [x] ~~Acessar [app.diagrams.net](https://app.diagrams.net)~~ Usado Mermaid
- [x] Criar diagrama com fluxo completo:
  - **Origem**: Simulação (generate_data.py + CSV)
  - **Transporte**: Arquivo CSV
  - **Ingestão**: Scripts Python + SQL
  - **Armazenamento**: Banco Oracle (tabelas da Entrega 3)
  - **ML**: Modelo Gradient Boosting (treino/inferência)
  - **Visualização**: Dashboard Streamlit
  - **Alertas**: Sistema de threshold
- [ ] ~~Salvar como `.drawio`~~ e exportar `.png` (via mermaid.live)
- [x] Criar pasta `/docs/arquitetura/`
- [x] Adicionar arquivo: `arquitetura_integrada.md` (Mermaid)

### 2. Reorganizar Estrutura de Pastas
- [x] Criar `/ingest/` (código ESP32 + scripts de coleta)
- [x] Renomear `/sql/` para `/db/`
- [x] Criar `/dashboard/`
- [x] Criar `/db/evidencias/`
- [x] Criar `/dashboard/screenshots/`
- [x] Criar `/ingest/prints/`
- [x] Criar `/dashboard/assets/`
- [ ] Estrutura final:
```
projeto_reply_sprint3/
├── docs/
│   ├── database_doc.md        # JÁ EXISTE ✅
│   └── arquitetura/            # NOVO
├── data/                        # JÁ EXISTE ✅ (manter)
│   ├── sensor_data.csv
│   ├── sensor_data.json
│   └── classification_report.json
├── scripts/                     # JÁ EXISTE ✅ (manter)
│   └── generate_data.py
├── ingest/                      # NOVO
├── db/                          # RENOMEADO (era /sql/)
├── notebooks/                   # JÁ EXISTE ✅ (manter nome)
├── dashboard/                   # NOVO
└── README.md
```

### 3. Atualizar requirements.txt
- [x] Adicionar dependências do dashboard:
```txt
# Dashboard
streamlit>=1.28.0
plotly>=5.14.0

# Banco de Dados Oracle
oracledb>=1.4.0
```

---

## **FASE 2: SIMULAÇÃO ESP32 E COLETA** (45 min)

### 4. Reaproveitar Simulação do Sprint 2
- [ ] Copiar `/esp32/circuito.ino` do Sprint 2 para `/ingest/sketch.ino`
- [ ] Ajustar delay de 2s para 30s no código
- [ ] Criar `/ingest/wokwi_link.txt` com: `https://wokwi.com/projects/433508321885341697`
- [ ] Copiar `/assets/cicuito.jpeg` do Sprint 2 para `/ingest/prints/circuit.png`

**Ajustes necessários no `sketch.ino`:**
```cpp
// Mudar de:
delay(2000);  // 2 segundos

// Para:
delay(30000); // 30 segundos
```

### 5. Criar Estrutura de Ingestão
- [ ] Salvar `/ingest/sketch.ino` (código do ESP32 ajustado)
- [ ] Exportar `diagram.json` do Wokwi (se disponível)
- [ ] Tirar print do Monitor Serial e salvar como `/ingest/prints/monitor_serial.png`

### 6. Criar Script Python de Ingestão
- [ ] Criar `/ingest/ingest_data.py`:
  - Ler dados da porta Serial (ou arquivo simulado)
  - Conectar ao banco Oracle
  - Inserir leituras na tabela `LEITURA`
  - Gerar alertas quando necessário
- [ ] Criar `/ingest/serial_simulator.py` (simular ESP32 sem hardware):
  - Ler do CSV em `/data/sensor_data.csv`
  - Simular envio via Serial
- [ ] Testar inserção no banco

### 7. Criar Gráfico de Leituras Iniciais
- [ ] Adaptar `/scripts/generate_data.py` ou criar `/ingest/visualize_readings.py`:
  - Basear no `main.py` do Sprint 2
  - Ler últimas 100 leituras do banco Oracle
  - Gráfico de linha temporal (temperatura e umidade)
  - Exportar como `/ingest/prints/readings_chart.png`

---

## **FASE 3: DASHBOARD E ALERTAS** (60 min)

### 8. Criar Dashboard Streamlit

#### 8.1 Estrutura do Dashboard
- [ ] Criar `/dashboard/app.py`
- [ ] Criar `/dashboard/requirements.txt`:
```txt
streamlit>=1.28.0
plotly>=5.14.0
oracledb>=1.4.0
pandas>=1.5.0
```
- [ ] Copiar logo: `/assets/logo-fiap.png` do Sprint 2 para `/dashboard/assets/logo-fiap.png`

#### 8.2 Seções do Dashboard
- [ ] **Header**: Título e logo FarmTech Solutions
- [ ] **KPIs** (cards superiores):
  - Total de leituras
  - % Leituras Normais
  - % Leituras em Alerta
  - % Leituras Críticas
  - Número de alertas ativos
- [ ] **Gráficos**:
  - Série temporal (temperatura e umidade últimas 24h)
  - Distribuição por equipamento (barras)
  - Heatmap de alertas por hora do dia
  - Performance do modelo ML (métricas do `/notebooks/`)
- [ ] **Sistema de Alertas**:
  - Tabela de alertas ativos
  - Banner vermelho quando crítico
  - Filtros por equipamento/sensor
  - Histórico de alertas resolvidos

#### 8.3 Configuração de Thresholds
- [ ] Criar `/dashboard/config.py`:
```python
THRESHOLDS = {
    'temperatura': {'min': 18, 'max': 28, 'critico': 32},
    'umidade': {'min': 50, 'max': 80, 'critico': 40}
}
```

#### 8.4 Conexão com Banco
- [ ] Criar `/dashboard/db_connection.py`:
  - Função `get_latest_readings()`
  - Função `get_alerts()`
  - Função `get_kpis()`
  - Função `get_ml_metrics()` (ler de `/notebooks/model_metrics.json`)

### 9. Criar README do Dashboard
- [ ] Criar `/dashboard/README.md`:
  - Como rodar: `streamlit run app.py`
  - Configuração de variáveis de ambiente (Oracle DB)
  - Screenshots

---

## **FASE 4: INTEGRAÇÃO E DOCUMENTAÇÃO** (45 min)

### 10. Criar Script de Pipeline Integrado
- [ ] Criar `/run_pipeline.py` (raiz do projeto):
  - Step 1: Simular coleta ESP32 (usar serial_simulator.py)
  - Step 2: Inserir no banco (via ingest_data.py)
  - Step 3: Carregar modelo ML (de `/notebooks/best_model.pkl`)
  - Step 4: Fazer inferência nas novas leituras
  - Step 5: Gerar alertas
  - Step 6: Instruções para abrir dashboard
- [ ] Adicionar logs coloridos de cada etapa
- [ ] Criar `/run_pipeline.sh` (versão bash) - opcional

### 11. Atualizar README Principal

#### 11.1 Adicionar Seções
- [ ] **Arquitetura Integrada** (com imagem do diagrama)
- [ ] **Fluxo de Dados**:
```
ESP32 → Serial → Python → Oracle DB → ML Model → Dashboard → Alertas
```
- [ ] **Como Executar o Projeto Completo**:
  1. Setup do banco (`/db/banco.sql`)
  2. Instalar dependências (`pip install -r requirements.txt`)
  3. Popular dados (`/db/insert_leituras.sql` ou usar `/data/sensor_data.csv`)
  4. Rodar simulação ESP32 (Wokwi ou `ingest/serial_simulator.py`)
  5. Executar pipeline (`python run_pipeline.py`)
  6. Abrir dashboard (`cd dashboard && streamlit run app.py`)
- [ ] **Vínculo com Entregas Anteriores**:
  - Entrega 1: Arquitetura planejada
  - Entrega 2: Simulação de sensores (ESP32 + DHT22)
  - Entrega 3: Banco de dados + ML
  - Entrega 4: Integração completa ponta-a-ponta
- [ ] **Link do Vídeo** (placeholder inicialmente)

### 12. Gerar Evidências

#### 12.1 Banco de Dados
- [ ] Print: `SELECT COUNT(*) FROM LEITURA;`
- [ ] Print: `SELECT * FROM ALERTA WHERE resolvido = 'N';`
- [ ] Print: `SELECT * FROM SENSOR;`
- [ ] Salvar em `/db/evidencias/`

#### 12.2 Dashboard
- [ ] Screenshot do dashboard completo
- [ ] Screenshot de alerta crítico sendo mostrado
- [ ] Screenshot dos KPIs
- [ ] Screenshot dos gráficos
- [ ] Salvar em `/dashboard/screenshots/`

#### 12.3 ESP32
- [ ] Print do código no Wokwi
- [ ] Print do circuito montado
- [ ] Print do Monitor Serial com dados
- [ ] Salvar em `/ingest/prints/`

---

## **FASE 5: VÍDEO E FINALIZAÇÃO** (30 min)

### 13. Gravar Vídeo Demonstrativo

#### 13.1 Roteiro (até 5 minutos)
- [ ] **00:00 - 00:30**: Introdução
  - Apresentar projeto FarmTech Solutions
  - Objetivos da Entrega 4
  - Integrantes do grupo
- [ ] **00:30 - 01:30**: Arquitetura
  - Mostrar diagrama completo (`/docs/arquitetura/`)
  - Explicar cada componente
  - Decisões técnicas (por que DHT22, por que Oracle, por que Gradient Boosting)
- [ ] **01:30 - 02:30**: Demonstração ESP32
  - Abrir Wokwi (link salvo em `/ingest/wokwi_link.txt`)
  - Rodar simulação
  - Mostrar Monitor Serial
  - Explicar código (`/ingest/sketch.ino`)
- [ ] **02:30 - 03:30**: Pipeline Completo
  - Rodar `run_pipeline.py`
  - Mostrar dados sendo inseridos no banco
  - Mostrar modelo ML fazendo predições
  - Mostrar alertas sendo gerados
- [ ] **03:30 - 04:30**: Dashboard e Alertas
  - Abrir dashboard Streamlit (`streamlit run dashboard/app.py`)
  - Mostrar KPIs
  - Demonstrar alerta sendo disparado
  - Mostrar gráficos em tempo real
  - Filtrar por equipamento
- [ ] **04:30 - 05:00**: Conclusão
  - Resultados alcançados (100% acurácia do modelo)
  - Benefícios para o negócio
  - Próximos passos
  - Vínculo com entregas anteriores

#### 13.2 Gravação
- [ ] Gravar tela com áudio (OBS Studio/QuickTime/Zoom)
- [ ] Editar se necessário (cortes, legendas)
- [ ] Exportar em HD (1080p)
- [ ] Testar o vídeo antes de fazer upload

### 14. Upload e Publicação
- [ ] Fazer upload no YouTube (não listado)
- [ ] Criar thumbnail do vídeo
- [ ] Adicionar descrição:
```
FarmTech Solutions - Entrega 4 (Sprint 3)
Sistema de Monitoramento IoT com Machine Learning para Estufas Agrícolas

🎯 Fluxo completo: ESP32 → Banco Oracle → ML → Dashboard

Repositório: [link do GitHub]

👥 Integrantes:
- Italo Domingues (RM 561787)
- Maison Wendrel Bezerra Ramos (RM 565616)

📚 FIAP - Faculdade de Informática e Administração Paulista
```
- [ ] Copiar link do vídeo

### 15. Validação Final
- [ ] Adicionar link do vídeo no README
- [ ] Verificar todos os requisitos do enunciado:
  - ✅ Arquitetura integrada (4.1)
  - ✅ Coleta e ingestão (4.2)
  - ✅ Banco de dados (4.3)
  - ✅ ML integrado (4.4)
  - ✅ Visualização e alertas (4.5)
  - ✅ Reprodutibilidade (4.6)
  - ✅ Estrutura de pastas (5.1)
  - ✅ Vídeo explicativo (5.2)
- [ ] Testar execução completa do zero (em máquina limpa se possível)
- [ ] Revisar toda a documentação
- [ ] Verificar links (GitHub, Wokwi, YouTube)
- [ ] Commit final: `git commit -m "feat: integração completa - entrega 4"`
- [ ] Push para GitHub
- [ ] **NÃO FAZER MAIS ALTERAÇÕES APÓS PRAZO**

---

## 📊 **CHECKLIST DE ENTREGA**

### Estrutura de Arquivos Obrigatória:
```
✅ /docs/database_doc.md                      # JÁ EXISTE
✅ /docs/arquitetura/arquitetura_integrada.drawio
✅ /docs/arquitetura/arquitetura_integrada.png
✅ /data/sensor_data.csv                       # JÁ EXISTE
✅ /data/sensor_data.json                      # JÁ EXISTE
✅ /scripts/generate_data.py                   # JÁ EXISTE
✅ /ingest/sketch.ino                          # Do Sprint 2 (ajustado)
✅ /ingest/wokwi_link.txt
✅ /ingest/ingest_data.py
✅ /ingest/serial_simulator.py
✅ /ingest/prints/circuit.png
✅ /ingest/prints/monitor_serial.png
✅ /ingest/prints/readings_chart.png
✅ /db/banco.sql                               # Renomeado de /sql/
✅ /db/insert_leituras.sql                     # Renomeado de /sql/
✅ /db/evidencias/*.png
✅ /notebooks/modelo_classificacao_equipamento_2.ipynb  # JÁ EXISTE
✅ /notebooks/best_model.pkl                   # JÁ EXISTE
✅ /dashboard/app.py
✅ /dashboard/config.py
✅ /dashboard/db_connection.py
✅ /dashboard/README.md
✅ /dashboard/screenshots/*.png
✅ /README.md (atualizado)
✅ /requirements.txt (atualizado)
✅ /run_pipeline.py
✅ Link do vídeo no README
```

### Conteúdo do README:
- ✅ Visão geral do projeto integrado
- ✅ Arquitetura com diagrama
- ✅ Como executar (passo a passo)
- ✅ Decisões técnicas
- ✅ Vínculo com Entregas 1, 2 e 3
- ✅ Link do vídeo YouTube

### Vídeo (até 5 min):
- ✅ Demonstração completa do fluxo
- ✅ Arquitetura explicada
- ✅ ESP32 funcionando (Wokwi)
- ✅ Dashboard com alertas
- ✅ Upload no YouTube (não listado)

---

## ⏱️ **CRONOGRAMA SUGERIDO**

| Fase | Duração | Quando fazer |
|------|---------|--------------|
| Fase 1 | 30 min | Dia 1 - Manhã |
| Fase 2 | 45 min | Dia 1 - Tarde |
| Fase 3 | 60 min | Dia 2 - Manhã |
| Fase 4 | 45 min | Dia 2 - Tarde |
| Fase 5 | 30 min | Dia 3 - Finalização |

**TEMPO TOTAL ESTIMADO: ~3h30min**

---

## 💡 **DICAS IMPORTANTES**

1. **Priorize o funcionamento** sobre a perfeição estética
2. **Documente conforme faz**, não deixe para depois
3. **Tire prints de tudo** (evidências são cruciais)
4. **Teste o fluxo completo** antes de gravar o vídeo
5. **Grave o vídeo em 2-3 takes** para garantir qualidade
6. **Use dados reais do banco** no dashboard (não mock)
7. **Prepare ambiente antes de gravar** (feche abas desnecessárias)
8. **Fale com clareza** no vídeo (não precisa ser rápido)
9. **Reaproveite ao máximo o Sprint 2** (código ESP32, circuito, prints)
10. **Mantenha as pastas existentes** (`/data/`, `/scripts/`, `/notebooks/`)

---

## 🔄 **REAPROVEITAMENTO DO SPRINT 2**

### Arquivos para copiar do Sprint 2:
```bash
# Código ESP32
Sprint2/esp32/circuito.ino → Sprint3/ingest/sketch.ino (ajustar delay)

# Imagens
Sprint2/assets/cicuito.jpeg → Sprint3/ingest/prints/circuit.png
Sprint2/assets/logo-fiap.png → Sprint3/dashboard/assets/logo-fiap.png

# Referência para visualização
Sprint2/main.py → Sprint3/ingest/visualize_readings.py (adaptar)

# Link Wokwi (salvar em txt)
https://wokwi.com/projects/433508321885341697 → Sprint3/ingest/wokwi_link.txt
```

**Economia de tempo: ~45 minutos (70% da Fase 2)**

---

## 🚨 **ATENÇÃO**

- ⚠️ **NÃO altere o repositório após o prazo de entrega**
- ⚠️ **NÃO renomeie `/notebooks/` para `/ml/`** (manter nome original)
- ⚠️ **NÃO delete `/data/` ou `/scripts/`** (são importantes)
- ⚠️ **Todos os integrantes devem participar**
- ⚠️ **Qualidade técnica > quantidade de features**
- ⚠️ **Clareza da documentação é essencial**
- ⚠️ **Atualize o `requirements.txt`** com streamlit e oracledb

---

## 📦 **DEPENDÊNCIAS ADICIONAIS NECESSÁRIAS**

Adicionar ao `requirements.txt` existente:
```txt
# Dashboard
streamlit>=1.28.0
plotly>=5.14.0

# Banco de Dados Oracle
oracledb>=1.4.0

# Conexão Serial (se usar ESP32 físico)
pyserial>=3.5
```

---

**Boa sorte! 🚀**
