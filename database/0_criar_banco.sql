-- ==========================================
-- CAMADA RAW (Dados Brutos do CSV)
-- ==========================================

-- As colunas seguem a MESMA ORDEM do CSV, renomeadas para snake_case.
-- Tudo VARCHAR e sem constraints (a Raw guarda o conteudo bruto, sem tratar).

-- Tabela Raw Viagem  (22 colunas = 2025_Viagem.csv)
CREATE TABLE IF NOT EXISTS raw_viagem (
    id_viagem VARCHAR(255),
    num_proposta VARCHAR(255),
    situacao VARCHAR(255),
    viagem_urgente VARCHAR(255),
    justificativa_urgencia VARCHAR(4000),
    cod_orgao_superior VARCHAR(255),
    nome_orgao_superior VARCHAR(255),
    cod_orgao_solicitante VARCHAR(255),
    nome_orgao_solicitante VARCHAR(255),
    cpf_viajante VARCHAR(255),
    nome_viajante VARCHAR(255),
    cargo VARCHAR(255),
    funcao VARCHAR(255),
    descricao_funcao VARCHAR(255),
    data_inicio VARCHAR(255),
    data_fim VARCHAR(255),
    destinos VARCHAR(4000),
    motivo VARCHAR(4000),
    valor_diarias VARCHAR(255),
    valor_passagens VARCHAR(255),
    valor_devolucao VARCHAR(255),
    valor_outros_gastos VARCHAR(255)
);

-- Tabela Raw Passagem  (19 colunas = 2025_Passagem.csv)
CREATE TABLE IF NOT EXISTS raw_passagem (
    id_viagem VARCHAR(255),
    num_proposta VARCHAR(255),
    meio_transporte VARCHAR(255),
    pais_origem_ida VARCHAR(255),
    uf_origem_ida VARCHAR(255),
    cidade_origem_ida VARCHAR(255),
    pais_destino_ida VARCHAR(255),
    uf_destino_ida VARCHAR(255),
    cidade_destino_ida VARCHAR(255),
    pais_origem_volta VARCHAR(255),
    uf_origem_volta VARCHAR(255),
    cidade_origem_volta VARCHAR(255),
    pais_destino_volta VARCHAR(255),
    uf_destino_volta VARCHAR(255),
    cidade_destino_volta VARCHAR(255),
    valor_passagem VARCHAR(255),
    taxa_servico VARCHAR(255),
    data_emissao VARCHAR(255),
    hora_emissao VARCHAR(255)
);

-- Tabela Raw Pagamento  (10 colunas = 2025_Pagamento.csv)
CREATE TABLE IF NOT EXISTS raw_pagamento (
    id_viagem VARCHAR(255),
    num_proposta VARCHAR(255),
    cod_orgao_superior VARCHAR(255),
    nome_orgao_superior VARCHAR(255),
    cod_orgao_pagador VARCHAR(255),
    nome_orgao_pagador VARCHAR(255),
    cod_ug_pagadora VARCHAR(255),
    nome_ug_pagadora VARCHAR(255),
    tipo_pagamento VARCHAR(255),
    valor VARCHAR(255)
);

-- Tabela Raw Trecho  (14 colunas = 2025_Trecho.csv)
CREATE TABLE IF NOT EXISTS raw_trecho (
    id_viagem VARCHAR(255),
    num_proposta VARCHAR(255),
    sequencia_trecho VARCHAR(255),
    origem_data VARCHAR(255),
    origem_pais VARCHAR(255),
    origem_uf VARCHAR(255),
    origem_cidade VARCHAR(255),
    destino_data VARCHAR(255),
    destino_pais VARCHAR(255),
    destino_uf VARCHAR(255),
    destino_cidade VARCHAR(255),
    meio_transporte VARCHAR(255),
    numero_diarias VARCHAR(255),
    missao VARCHAR(255)
);


-- ==========================================
-- CAMADA SILVER (Dados Tratados e Relacionais)
-- ==========================================

-- 1. Tabela Silver Viagem
CREATE TABLE IF NOT EXISTS silver_viagem (
    id_viagem VARCHAR(20) PRIMARY KEY NOT NULL,
    num_proposta VARCHAR(20),
    situacao VARCHAR(50),
    viagem_urgente VARCHAR(5),
    cod_orgao_superior VARCHAR(20),
    nome_orgao_superior VARCHAR(255) NOT NULL, -- Constraint 1 (NOT NULL)
    nome_viajante VARCHAR(255),
    cargo VARCHAR(255),
    data_inicio DATE, 
    data_fim DATE,
    destinos VARCHAR(4000),
    motivo VARCHAR(4000),
    valor_diarias DECIMAL(10,2) DEFAULT 0.00,
    valor_passagens DECIMAL(10,2) DEFAULT 0.00,
    valor_devolucao DECIMAL(10,2) DEFAULT 0.00,
    valor_outros_gastos DECIMAL(10,2) DEFAULT 0.00,
    valor_total DECIMAL(12,2) DEFAULT 0.00, -- Calculado
    duracao_dias INT, -- Calculado
    
    -- Constraint 2 (CHECK)
    CONSTRAINT chk_valor_diarias CHECK (valor_diarias >= 0)
);

-- 2. Tabela Silver Passagem
CREATE TABLE IF NOT EXISTS silver_passagem (
    id_passagem SERIAL PRIMARY KEY,
    id_viagem VARCHAR(20) NOT NULL,
    meio_transporte VARCHAR(50),
    pais_origem_ida VARCHAR(60),
    uf_origem_ida VARCHAR(40),
    cidade_origem_ida VARCHAR(80),
    pais_destino_ida VARCHAR(60),
    uf_destino_ida VARCHAR(40),
    cidade_destino_ida VARCHAR(80),
    valor_passagem DECIMAL(10,2) DEFAULT 0.00,
    taxa_servico DECIMAL(10,2) DEFAULT 0.00,
    data_emissao DATE,
    
    -- Relacionamento (Foreign Key)
    FOREIGN KEY (id_viagem) REFERENCES silver_viagem(id_viagem) ON DELETE CASCADE,
    
    -- Constraints 1 e 2 (CHECKs)
    CONSTRAINT chk_valor_passagem CHECK (valor_passagem >= 0),
    CONSTRAINT chk_taxa_servico CHECK (taxa_servico >= 0)
);

-- 3. Tabela Silver Pagamento
CREATE TABLE IF NOT EXISTS silver_pagamento (
    id_pagamento SERIAL PRIMARY KEY,
    id_viagem VARCHAR(20) NOT NULL,
    num_proposta VARCHAR(20),
    nome_orgao_pagador VARCHAR(255),
    nome_ug_pagadora VARCHAR(255),
    tipo_pagamento VARCHAR(50) NOT NULL, -- Constraint 2 (NOT NULL)
    valor DECIMAL(10,2) DEFAULT 0.00,
    
    -- Relacionamento (Foreign Key)
    FOREIGN KEY (id_viagem) REFERENCES silver_viagem(id_viagem) ON DELETE CASCADE,
    
    -- Constraint 1 (CHECK)
    CONSTRAINT chk_valor_pagamento CHECK (valor >= 0)
);

-- 4. Tabela Silver Trecho
CREATE TABLE IF NOT EXISTS silver_trecho (
    id_trecho SERIAL PRIMARY KEY,
    id_viagem VARCHAR(20) NOT NULL,
    sequencia_trecho INT,
    origem_data DATE,
    origem_uf VARCHAR(40),
    origem_cidade VARCHAR(80),
    destino_data DATE,
    destino_uf VARCHAR(40),
    destino_cidade VARCHAR(80),
    meio_transporte VARCHAR(50),
    numero_diarias DECIMAL(10,2) DEFAULT 0.00,
    
    -- Relacionamento (Foreign Key)
    FOREIGN KEY (id_viagem) REFERENCES silver_viagem(id_viagem) ON DELETE CASCADE,
    
    -- Constraint 1 (CHECK) e Constraint 2 (UNIQUE)
    CONSTRAINT chk_numero_diarias CHECK (numero_diarias >= 0),
    CONSTRAINT uq_viagem_trecho UNIQUE (id_viagem, sequencia_trecho)
);
