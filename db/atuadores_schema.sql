-- ============================================
-- Schema de Atuadores e Monitoramento
-- FarmTech Solutions - Sprint 4
-- ============================================

-- Tabela de Atuadores (Bombas, Ventiladores, Aquecedores)
CREATE TABLE Atuador (
    id_atuador INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('Bomba', 'Ventilador', 'Aquecedor')),
    id_equipamento INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Ativo' CHECK(status IN ('Ativo', 'Inativo', 'Manutenção')),
    potencia_watts INTEGER NOT NULL,  -- Potência em Watts para cálculo de energia
    data_instalacao TEXT DEFAULT (date('now')),
    FOREIGN KEY (id_equipamento) REFERENCES Equipamento(id_equipamento)
);

-- Tabela de Acionamentos (Histórico de Ligado/Desligado)
CREATE TABLE Acionamento (
    id_acionamento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_atuador INTEGER NOT NULL,
    data_hora_inicio TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    data_hora_fim TEXT,  -- NULL enquanto estiver ligado
    motivo TEXT NOT NULL,  -- Ex: "Umidade Baixa", "Temperatura Alta"
    id_leitura_trigger INTEGER,  -- Leitura que disparou o acionamento
    economia_kwh REAL,  -- Calculado ao desligar (vs. sistema 24/7)
    duracao_segundos INTEGER,  -- Calculado ao desligar
    FOREIGN KEY (id_atuador) REFERENCES Atuador(id_atuador),
    FOREIGN KEY (id_leitura_trigger) REFERENCES Leitura_Base(id_leitura)
);

-- Tabela de Saúde dos Sensores (Monitoramento Preditivo)
CREATE TABLE Sensor_Health (
    id_sensor_health INTEGER PRIMARY KEY AUTOINCREMENT,
    id_sensor INTEGER NOT NULL UNIQUE,
    status_saude TEXT NOT NULL DEFAULT 'Normal' CHECK(status_saude IN ('Normal', 'Atenção', 'Crítico', 'Falha')),
    num_alertas_criticos INTEGER DEFAULT 0,  -- Contador de alertas críticos
    num_leituras_anomalas INTEGER DEFAULT 0,  -- Leituras fora do padrão
    ultima_verificacao TEXT DEFAULT (datetime('now', 'localtime')),
    ultima_manutencao TEXT,
    observacoes TEXT,
    FOREIGN KEY (id_sensor) REFERENCES Sensor(id_sensor)
);

-- Tabela de Eventos Críticos (Anomalias e Falhas)
CREATE TABLE IF NOT EXISTS Evento_Critico (
    id_evento INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_evento TEXT NOT NULL,  -- Ex: SENSOR_OSCILANDO, ATUADOR_VENTILADOR_FALHA
    equipamento_id INTEGER,
    sensor_id INTEGER,
    atuador_id INTEGER,
    descricao TEXT,  -- Descrição detalhada do evento
    data_hora TEXT NOT NULL,
    resolvido TEXT DEFAULT 'N' CHECK(resolvido IN ('S', 'N')),
    FOREIGN KEY (sensor_id) REFERENCES Sensor(id_sensor),
    FOREIGN KEY (atuador_id) REFERENCES Atuador(id_atuador)
);

-- Índices para performance
CREATE INDEX idx_acionamento_atuador ON Acionamento(id_atuador);
CREATE INDEX idx_acionamento_periodo ON Acionamento(data_hora_inicio, data_hora_fim);
CREATE INDEX idx_sensor_health_status ON Sensor_Health(status_saude);
CREATE INDEX idx_atuador_equipamento ON Atuador(id_equipamento);
CREATE INDEX idx_evento_critico_tipo ON Evento_Critico(tipo_evento);
CREATE INDEX idx_evento_critico_data ON Evento_Critico(data_hora);
CREATE INDEX idx_evento_critico_resolvido ON Evento_Critico(resolvido);

-- VIEW para acionamentos ativos (atuadores ligados agora)
CREATE VIEW Acionamentos_Ativos AS
SELECT
    ac.id_acionamento,
    ac.id_atuador,
    at.nome as nome_atuador,
    at.tipo as tipo_atuador,
    at.id_equipamento,
    e.nome as nome_equipamento,
    ac.data_hora_inicio,
    ac.motivo,
    CAST((julianday('now', 'localtime') - julianday(ac.data_hora_inicio)) * 24 * 60 * 60 AS INTEGER) as duracao_segundos,
    at.potencia_watts
FROM Acionamento ac
JOIN Atuador at ON ac.id_atuador = at.id_atuador
JOIN Equipamento e ON at.id_equipamento = e.id_equipamento
WHERE ac.data_hora_fim IS NULL;

-- VIEW para estatísticas de economia de energia
CREATE VIEW Estatisticas_Economia AS
SELECT
    at.id_equipamento,
    e.nome as equipamento,
    at.tipo as tipo_atuador,
    COUNT(ac.id_acionamento) as total_acionamentos,
    ROUND(SUM(ac.duracao_segundos) / 3600.0, 2) as horas_ligado,
    ROUND(SUM(ac.economia_kwh), 2) as economia_total_kwh,
    ROUND(AVG(ac.duracao_segundos), 0) as duracao_media_segundos
FROM Atuador at
JOIN Equipamento e ON at.id_equipamento = e.id_equipamento
LEFT JOIN Acionamento ac ON at.id_atuador = ac.id_atuador
    AND ac.data_hora_fim IS NOT NULL
GROUP BY at.id_equipamento, e.nome, at.tipo;

-- VIEW para sensores com problemas
CREATE VIEW Sensores_Problematicos AS
SELECT
    sh.id_sensor,
    s.id_equipamento,
    e.nome as equipamento,
    ts.nome as tipo_sensor,
    sh.status_saude,
    sh.num_alertas_criticos,
    sh.num_leituras_anomalas,
    sh.ultima_verificacao,
    sh.observacoes
FROM Sensor_Health sh
JOIN Sensor s ON sh.id_sensor = s.id_sensor
JOIN Tipo_Sensor ts ON s.id_tipo_sensor = ts.id_tipo_sensor
JOIN Equipamento e ON s.id_equipamento = e.id_equipamento
WHERE sh.status_saude IN ('Atenção', 'Crítico', 'Falha')
ORDER BY
    CASE sh.status_saude
        WHEN 'Falha' THEN 1
        WHEN 'Crítico' THEN 2
        WHEN 'Atenção' THEN 3
    END,
    sh.num_alertas_criticos DESC;
