-- =============================================================
-- CAMADA BRONZE — Dado bruto, exatamente como veio da fonte
-- Sem transformação, sem limpeza. Apenas ingestão.
-- =============================================================

-- Tabela: clientes brutos
CREATE TABLE IF NOT EXISTS bronze_clientes (
    cliente_id       INTEGER,
    nome             TEXT,
    cpf              TEXT,
    data_nascimento  TEXT,
    score_credito    TEXT,     -- texto intencional: pode vir com erro
    renda_mensal     TEXT,     -- texto intencional: pode vir com vírgula
    estado           TEXT,
    data_cadastro    TEXT,
    _ingestao        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela: empréstimos brutos
CREATE TABLE IF NOT EXISTS bronze_emprestimos (
    emprestimo_id    INTEGER,
    cliente_id       INTEGER,
    valor_emprestado TEXT,
    valor_parcela    TEXT,
    num_parcelas     TEXT,
    taxa_juros       TEXT,
    data_concessao   TEXT,
    status           TEXT,
    _ingestao        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela: pagamentos brutos
CREATE TABLE IF NOT EXISTS bronze_pagamentos (
    pagamento_id     INTEGER,
    emprestimo_id    INTEGER,
    parcela_num      INTEGER,
    data_vencimento  TEXT,
    data_pagamento   TEXT,
    valor_devido     TEXT,
    valor_pago       TEXT,
    status           TEXT,
    _ingestao        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela: eventos de risco brutos
CREATE TABLE IF NOT EXISTS bronze_eventos_risco (
    evento_id        INTEGER,
    cliente_id       INTEGER,
    emprestimo_id    INTEGER,
    tipo_evento      TEXT,
    data_evento      TEXT,
    valor_em_risco   TEXT,
    _ingestao        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
