-- =============================================================
-- CAMADA SILVER — Dado limpo, tipado e confiável
-- Remove duplicatas, corrige tipos, padroniza valores
-- =============================================================

-- Clientes limpos
CREATE TABLE IF NOT EXISTS silver_clientes AS
SELECT
    cliente_id,
    TRIM(nome)                              AS nome,
    REPLACE(cpf, '.', '')                  AS cpf,         -- padroniza CPF
    DATE(data_nascimento)                   AS data_nascimento,
    CAST(score_credito AS INTEGER)          AS score_credito,
    CAST(renda_mensal   AS REAL)            AS renda_mensal,
    UPPER(TRIM(estado))                     AS estado,
    DATE(data_cadastro)                     AS data_cadastro,

    -- Segmentação de risco pelo score
    CASE
        WHEN CAST(score_credito AS INTEGER) >= 750 THEN 'BAIXO'
        WHEN CAST(score_credito AS INTEGER) >= 600 THEN 'MEDIO'
        WHEN CAST(score_credito AS INTEGER) >= 500 THEN 'ALTO'
        ELSE 'MUITO_ALTO'
    END AS faixa_risco,

    -- Faixa de renda
    CASE
        WHEN CAST(renda_mensal AS REAL) >= 10000 THEN 'ALTA'
        WHEN CAST(renda_mensal AS REAL) >=  5000 THEN 'MEDIA'
        WHEN CAST(renda_mensal AS REAL) >=  2000 THEN 'BAIXA'
        ELSE 'MUITO_BAIXA'
    END AS faixa_renda

FROM bronze_clientes
WHERE cliente_id IS NOT NULL
  AND score_credito IS NOT NULL
  AND cpf IS NOT NULL;


-- Empréstimos limpos
CREATE TABLE IF NOT EXISTS silver_emprestimos AS
SELECT
    emprestimo_id,
    cliente_id,
    CAST(valor_emprestado AS REAL)  AS valor_emprestado,
    CAST(valor_parcela    AS REAL)  AS valor_parcela,
    CAST(num_parcelas     AS INTEGER) AS num_parcelas,
    CAST(taxa_juros       AS REAL)  AS taxa_juros,
    DATE(data_concessao)            AS data_concessao,
    UPPER(TRIM(status))             AS status,

    -- Valor total a pagar
    CAST(valor_parcela AS REAL) * CAST(num_parcelas AS INTEGER) AS valor_total,

    -- Custo do crédito (juros pagos)
    (CAST(valor_parcela AS REAL) * CAST(num_parcelas AS INTEGER))
    - CAST(valor_emprestado AS REAL) AS custo_credito

FROM bronze_emprestimos
WHERE emprestimo_id IS NOT NULL
  AND cliente_id    IS NOT NULL
  AND status IN ('ATIVO', 'QUITADO', 'INADIMPLENTE');


-- Pagamentos limpos
CREATE TABLE IF NOT EXISTS silver_pagamentos AS
SELECT
    pagamento_id,
    emprestimo_id,
    parcela_num,
    DATE(data_vencimento) AS data_vencimento,
    DATE(data_pagamento)  AS data_pagamento,
    CAST(valor_devido AS REAL) AS valor_devido,
    CAST(valor_pago   AS REAL) AS valor_pago,
    UPPER(TRIM(status))        AS status,

    -- Dias de atraso
    CASE
        WHEN data_pagamento IS NOT NULL
        THEN JULIANDAY(data_pagamento) - JULIANDAY(data_vencimento)
        ELSE NULL
    END AS dias_atraso,

    -- Diferença paga vs devida
    CAST(valor_pago AS REAL) - CAST(valor_devido AS REAL) AS diferenca_valor

FROM bronze_pagamentos
WHERE pagamento_id IS NOT NULL;


-- Eventos de risco limpos
CREATE TABLE IF NOT EXISTS silver_eventos_risco AS
SELECT
    evento_id,
    cliente_id,
    emprestimo_id,
    UPPER(TRIM(tipo_evento))       AS tipo_evento,
    DATE(data_evento)              AS data_evento,
    CAST(valor_em_risco AS REAL)   AS valor_em_risco,

    -- Severidade do evento
    CASE tipo_evento
        WHEN 'ATRASO_30' THEN 1
        WHEN 'ATRASO_60' THEN 2
        WHEN 'ATRASO_90' THEN 3
        WHEN 'CALOTE'    THEN 4
        ELSE 0
    END AS severidade

FROM bronze_eventos_risco
WHERE evento_id IS NOT NULL;
