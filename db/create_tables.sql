-- ========================================
-- FARMTECH SOLUTIONS - BANCO DE DADOS SQLITE
-- Sistema de Monitoramento de Sensores IoT
-- ========================================

-- Limpar tabelas existentes
DROP TABLE IF EXISTS Alerta;
DROP TABLE IF EXISTS Leitura;
DROP TABLE IF EXISTS Atuador;
DROP TABLE IF EXISTS Sensor;
DROP TABLE IF EXISTS Equipamento;
DROP TABLE IF EXISTS Cultura;
DROP TABLE IF EXISTS Tipo_Sensor;

-- Criar tabela de tipos de sensores
CREATE TABLE Tipo_Sensor (
    id_tipo_sensor INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(50) NOT NULL UNIQUE,
    unidade_medida VARCHAR(20) NOT NULL,
    valor_minimo REAL,
    valor_maximo REAL,
    descricao VARCHAR(200)
);

-- Criar tabela de culturas
CREATE TABLE Cultura (
    id_cultura INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    temp_min_ideal REAL,
    temp_max_ideal REAL,
    umidade_min_ideal REAL,
    umidade_max_ideal REAL,
    descricao VARCHAR(500)
);

-- Criar tabela de equipamentos
CREATE TABLE Equipamento (
    id_equipamento INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    localizacao VARCHAR(100),
    id_cultura INTEGER,
    data_instalacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'Ativo' CHECK (status IN ('Ativo', 'Inativo', 'Manutenção')),
    FOREIGN KEY (id_cultura) REFERENCES Cultura(id_cultura)
);

-- Criar tabela de sensores
CREATE TABLE Sensor (
    id_sensor INTEGER PRIMARY KEY AUTOINCREMENT,
    id_tipo_sensor INTEGER NOT NULL,
    id_equipamento INTEGER,
    modelo VARCHAR(50),
    fabricante VARCHAR(50),
    data_instalacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'Ativo' CHECK (status IN ('Ativo', 'Inativo', 'Manutenção')),
    intervalo_leitura INTEGER DEFAULT 60,
    FOREIGN KEY (id_tipo_sensor) REFERENCES Tipo_Sensor(id_tipo_sensor),
    FOREIGN KEY (id_equipamento) REFERENCES Equipamento(id_equipamento)
);

-- Criar tabela de atuadores
CREATE TABLE Atuador (
    id_atuador INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo VARCHAR(50) NOT NULL,
    id_equipamento INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'Ativo' CHECK (status IN ('Ativo', 'Inativo', 'Manutenção')),
    intensidade REAL DEFAULT 0 CHECK (intensidade >= 0 AND intensidade <= 100),
    data_instalacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_equipamento) REFERENCES Equipamento(id_equipamento)
);

-- Criar tabela de leituras
CREATE TABLE Leitura (
    id_leitura INTEGER PRIMARY KEY AUTOINCREMENT,
    id_sensor INTEGER NOT NULL,
    valor REAL NOT NULL,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    qualidade VARCHAR(20) DEFAULT 'Normal' CHECK (qualidade IN ('Normal', 'Alerta', 'Critico')),
    FOREIGN KEY (id_sensor) REFERENCES Sensor(id_sensor)
);

-- Criar tabela de alertas
CREATE TABLE Alerta (
    id_alerta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_leitura INTEGER NOT NULL,
    tipo_alerta VARCHAR(50) NOT NULL,
    mensagem VARCHAR(500),
    data_alerta DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolvido CHAR(1) DEFAULT 'N' CHECK (resolvido IN ('S', 'N')),
    data_resolucao DATETIME,
    FOREIGN KEY (id_leitura) REFERENCES Leitura(id_leitura)
);

-- Criar índices para melhor performance
CREATE INDEX idx_leitura_sensor ON Leitura(id_sensor);
CREATE INDEX idx_leitura_data ON Leitura(data_hora);
CREATE INDEX idx_sensor_tipo ON Sensor(id_tipo_sensor);
CREATE INDEX idx_sensor_equip ON Sensor(id_equipamento);
CREATE INDEX idx_alerta_leitura ON Alerta(id_leitura);
CREATE INDEX idx_atuador_equip ON Atuador(id_equipamento);

-- ========================================
-- INSERÇÃO DE DADOS INICIAIS
-- ========================================

-- Inserir tipos de sensores (apenas Temperatura e Umidade)
INSERT INTO Tipo_Sensor (nome, unidade_medida, valor_minimo, valor_maximo, descricao)
VALUES ('Temperatura', '°C', -10, 50, 'Sensor de temperatura ambiente');

INSERT INTO Tipo_Sensor (nome, unidade_medida, valor_minimo, valor_maximo, descricao)
VALUES ('Umidade', '%', 0, 100, 'Sensor de umidade relativa do ar');

-- Inserir culturas
INSERT INTO Cultura (nome, temp_min_ideal, temp_max_ideal, umidade_min_ideal, umidade_max_ideal, descricao)
VALUES ('Tomate', 18, 25, 60, 70, 'Cultura de tomates em estufa');

INSERT INTO Cultura (nome, temp_min_ideal, temp_max_ideal, umidade_min_ideal, umidade_max_ideal, descricao)
VALUES ('Alface', 15, 22, 65, 75, 'Cultura de alface hidropônica');

INSERT INTO Cultura (nome, temp_min_ideal, temp_max_ideal, umidade_min_ideal, umidade_max_ideal, descricao)
VALUES ('Morango', 15, 23, 60, 70, 'Cultura de morangos em estufa');

INSERT INTO Cultura (nome, temp_min_ideal, temp_max_ideal, umidade_min_ideal, umidade_max_ideal, descricao)
VALUES ('Pimentão', 20, 28, 55, 65, 'Cultura de pimentões em estufa');

-- Inserir equipamentos (4 estufas)
INSERT INTO Equipamento (nome, localizacao, id_cultura, status)
VALUES ('Estufa 1', 'Setor A - Norte', 1, 'Ativo');

INSERT INTO Equipamento (nome, localizacao, id_cultura, status)
VALUES ('Estufa 2', 'Setor A - Sul', 2, 'Ativo');

INSERT INTO Equipamento (nome, localizacao, id_cultura, status)
VALUES ('Estufa 3', 'Setor B - Leste', 3, 'Ativo');

INSERT INTO Equipamento (nome, localizacao, id_cultura, status)
VALUES ('Estufa 4', 'Setor B - Oeste', 4, 'Ativo');

-- Inserir sensores (2 por estufa: Temperatura e Umidade)
-- Estufa 1
INSERT INTO Sensor (id_tipo_sensor, id_equipamento, modelo, fabricante, intervalo_leitura)
VALUES (1, 1, 'DHT22', 'Aosong', 2);

INSERT INTO Sensor (id_tipo_sensor, id_equipamento, modelo, fabricante, intervalo_leitura)
VALUES (2, 1, 'DHT22', 'Aosong', 2);

-- Estufa 2
INSERT INTO Sensor (id_tipo_sensor, id_equipamento, modelo, fabricante, intervalo_leitura)
VALUES (1, 2, 'DS18B20', 'Dallas', 2);

INSERT INTO Sensor (id_tipo_sensor, id_equipamento, modelo, fabricante, intervalo_leitura)
VALUES (2, 2, 'HIH-4030', 'Honeywell', 2);

-- Estufa 3
INSERT INTO Sensor (id_tipo_sensor, id_equipamento, modelo, fabricante, intervalo_leitura)
VALUES (1, 3, 'DHT22', 'Aosong', 2);

INSERT INTO Sensor (id_tipo_sensor, id_equipamento, modelo, fabricante, intervalo_leitura)
VALUES (2, 3, 'DHT22', 'Aosong', 2);

-- Estufa 4
INSERT INTO Sensor (id_tipo_sensor, id_equipamento, modelo, fabricante, intervalo_leitura)
VALUES (1, 4, 'BME280', 'Bosch', 2);

INSERT INTO Sensor (id_tipo_sensor, id_equipamento, modelo, fabricante, intervalo_leitura)
VALUES (2, 4, 'BME280', 'Bosch', 2);

-- Inserir atuadores (2 por estufa: Irrigação e Ventilação)
-- Estufa 1
INSERT INTO Atuador (tipo, id_equipamento, status, intensidade)
VALUES ('Irrigação', 1, 'Ativo', 0);

INSERT INTO Atuador (tipo, id_equipamento, status, intensidade)
VALUES ('Ventilação', 1, 'Ativo', 0);

-- Estufa 2
INSERT INTO Atuador (tipo, id_equipamento, status, intensidade)
VALUES ('Irrigação', 2, 'Ativo', 0);

INSERT INTO Atuador (tipo, id_equipamento, status, intensidade)
VALUES ('Ventilação', 2, 'Ativo', 0);

-- Estufa 3
INSERT INTO Atuador (tipo, id_equipamento, status, intensidade)
VALUES ('Irrigação', 3, 'Ativo', 0);

INSERT INTO Atuador (tipo, id_equipamento, status, intensidade)
VALUES ('Ventilação', 3, 'Ativo', 0);

-- Estufa 4
INSERT INTO Atuador (tipo, id_equipamento, status, intensidade)
VALUES ('Irrigação', 4, 'Ativo', 0);

INSERT INTO Atuador (tipo, id_equipamento, status, intensidade)
VALUES ('Ventilação', 4, 'Ativo', 0);
