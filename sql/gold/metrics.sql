-- =============================================================
-- CAMADA GOLD — Métricas de negócio prontas para decisão
-- Views analíticas para o time de risco do FinBank
-- =============================================================


-- ── 1. Taxa de inadimplência por estado ──────────────────────────────────────
-- Pergunta: Onde o banco tem mais risco concentrado?
CREATE VIEW IF NOT EXISTS gold_inadimplencia_por_estado AS
SELECT
    c.estado,
    COUNT(DISTINCT e.emprestimo_id)                          AS total_emprestimos,
    COUNT(DISTINCT CASE WHEN e.status = 'INADIMPLENTE'
          THEN e.emprestimo_id END)                          AS inadimplentes,
    ROUND(
        COUNT(DISTINCT CASE WHEN e.status = 'INADIMPLENTE'
              THEN e.emprestimo_id END) * 100.0
        / COUNT(DISTINCT e.emprestimo_id), 2
    )                                                        AS taxa_inadimplencia_pct,
    ROUND(SUM(CASE WHEN e.status = 'INADIMPLENTE'
              THEN e.valor_emprestado ELSE 0 END), 2)        AS valor_em_risco
FROM silver_emprestimos e
JOIN silver_clientes c ON e.cliente_id = c.cliente_id
GROUP BY c.estado
ORDER BY taxa_inadimplencia_pct DESC;


-- ── 2. Evolução mensal da inadimplência ──────────────────────────────────────
-- Pergunta: A inadimplência está crescendo ou caindo?
CREATE VIEW IF NOT EXISTS gold_evolucao_inadimplencia AS
WITH mensal AS (
    SELECT
        STRFTIME('%Y-%m', data_concessao)    AS mes,
        COUNT(*)                             AS total,
        SUM(CASE WHEN status = 'INADIMPLENTE' THEN 1 ELSE 0 END) AS inadimplentes,
        SUM(CASE WHEN status = 'INADIMPLENTE'
            THEN valor_emprestado ELSE 0 END) AS valor_inadimplente
    FROM silver_emprestimos
    GROUP BY mes
)
SELECT
    mes,
    total,
    inadimplentes,
    ROUND(inadimplentes * 100.0 / total, 2)  AS taxa_pct,
    valor_inadimplente,
    LAG(inadimplentes) OVER (ORDER BY mes)   AS inadimplentes_mes_anterior,
    inadimplentes - LAG(inadimplentes)
        OVER (ORDER BY mes)                  AS variacao_absoluta,
    ROUND(
        (inadimplentes - LAG(inadimplentes) OVER (ORDER BY mes))
        * 100.0 / NULLIF(LAG(inadimplentes) OVER (ORDER BY mes), 0)
    , 2)                                     AS variacao_pct
FROM mensal
ORDER BY mes;


-- ── 3. Ranking de clientes por exposição ao risco ────────────────────────────
-- Pergunta: Quem são os clientes mais arriscados da carteira?
CREATE VIEW IF NOT EXISTS gold_ranking_risco_clientes AS
WITH exposicao AS (
    SELECT
        c.cliente_id,
        c.nome,
        c.score_credito,
        c.faixa_risco,
        c.estado,
        COUNT(e.emprestimo_id)              AS total_emprestimos,
        SUM(e.valor_emprestado)             AS valor_total_emprestado,
        SUM(CASE WHEN e.status = 'INADIMPLENTE'
            THEN e.valor_emprestado ELSE 0 END) AS valor_inadimplente,
        COUNT(er.evento_id)                 AS total_eventos_risco,
        MAX(er.severidade)                  AS maior_severidade
    FROM silver_clientes c
    LEFT JOIN silver_emprestimos e  ON c.cliente_id = e.cliente_id
    LEFT JOIN silver_eventos_risco er ON c.cliente_id = er.cliente_id
    GROUP BY c.cliente_id, c.nome, c.score_credito, c.faixa_risco, c.estado
)
SELECT
    *,
    RANK() OVER (ORDER BY valor_inadimplente DESC) AS ranking_exposicao,
    ROUND(valor_inadimplente * 100.0
          / NULLIF(valor_total_emprestado, 0), 2)  AS pct_inadimplente
FROM exposicao
WHERE valor_inadimplente > 0
ORDER BY ranking_exposicao;


-- ── 4. Perfil de risco por faixa de score ────────────────────────────────────
-- Pergunta: Score de crédito realmente prevê inadimplência?
CREATE VIEW IF NOT EXISTS gold_risco_por_score AS
SELECT
    c.faixa_risco,
    ROUND(AVG(c.score_credito), 0)          AS score_medio,
    COUNT(DISTINCT c.cliente_id)            AS total_clientes,
    COUNT(DISTINCT e.emprestimo_id)         AS total_emprestimos,
    COUNT(DISTINCT CASE WHEN e.status = 'INADIMPLENTE'
          THEN e.emprestimo_id END)         AS inadimplentes,
    ROUND(AVG(e.taxa_juros), 2)             AS taxa_juros_media,
    ROUND(AVG(e.valor_emprestado), 2)       AS ticket_medio,
    ROUND(
        COUNT(DISTINCT CASE WHEN e.status = 'INADIMPLENTE'
              THEN e.emprestimo_id END) * 100.0
        / NULLIF(COUNT(DISTINCT e.emprestimo_id), 0), 2
    )                                       AS taxa_inadimplencia_pct
FROM silver_clientes c
JOIN silver_emprestimos e ON c.cliente_id = e.cliente_id
GROUP BY c.faixa_risco
ORDER BY score_medio DESC;


-- ── 5. Clientes em risco iminente ────────────────────────────────────────────
-- Pergunta: Quem pode calotear nos próximos 30 dias?
CREATE VIEW IF NOT EXISTS gold_alerta_risco_iminente AS
WITH historico_atrasos AS (
    SELECT
        e.cliente_id,
        COUNT(*) FILTER (WHERE p.dias_atraso > 0)  AS qtd_atrasos,
        MAX(p.dias_atraso)                          AS maior_atraso,
        AVG(p.dias_atraso) FILTER
            (WHERE p.dias_atraso > 0)               AS media_atraso
    FROM silver_emprestimos e
    JOIN silver_pagamentos p ON e.emprestimo_id = p.emprestimo_id
    GROUP BY e.cliente_id
)
SELECT
    c.cliente_id,
    c.nome,
    c.score_credito,
    c.faixa_risco,
    c.estado,
    h.qtd_atrasos,
    h.maior_atraso,
    ROUND(h.media_atraso, 1)                AS media_atraso,
    SUM(e.valor_emprestado)                 AS exposicao_total,

    -- Score de risco composto (0 a 100)
    ROUND(
        (h.qtd_atrasos * 10)
        + (CASE WHEN h.maior_atraso > 60 THEN 30
                WHEN h.maior_atraso > 30 THEN 15
                ELSE 5 END)
        + ((850 - c.score_credito) / 20.0)
    , 1) AS score_risco_composto

FROM silver_clientes c
JOIN silver_emprestimos e  ON c.cliente_id = e.cliente_id
JOIN historico_atrasos h   ON c.cliente_id = h.cliente_id
WHERE e.status = 'ATIVO'
  AND h.qtd_atrasos > 0
GROUP BY c.cliente_id, c.nome, c.score_credito,
         c.faixa_risco, c.estado,
         h.qtd_atrasos, h.maior_atraso, h.media_atraso
ORDER BY score_risco_composto DESC;



-- ── 6. Qual faixa de renda realiza mais empresitmos ?  ────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS gold_faixa_emprestimos AS
WITH resumo_clientes_emprestimos AS (
    SELECT
        c.cliente_id,
        c.faixa_renda,
        -- Contamos quantos empréstimos cada cliente específico tem
        COUNT(e.emprestimo_id) AS qtd_contratos
    FROM silver_clientes c
    -- IMPORTANTE: Usei 'silver_empresitmos' com o erro de digitação que vimos na sua barra lateral
    LEFT JOIN silver_emprestimos e ON c.cliente_id = e.cliente_id
    GROUP BY c.cliente_id, c.faixa_renda
)
SELECT
    faixa_renda,
    -- Total de pessoas físicas únicas na faixa
    COUNT(DISTINCT cliente_id) AS total_clientes,
    -- Soma de todos os contratos gerados por essas pessoas
    SUM(qtd_contratos) AS total_emprestimos,
    -- Média real de contratos por cliente nesta faixa de renda
    ROUND(CAST(SUM(qtd_contratos) AS REAL) / COUNT(DISTINCT cliente_id), 2) AS media_emprestimos_por_cliente
FROM resumo_clientes_emprestimos
GROUP BY faixa_renda
ORDER BY faixa_renda;


CREATE VIEW IF NOT EXISTS gold_emprestimos_por_idade AS
WITH idades_clientes AS (
    SELECT 
        cliente_id,
        -- Calcula a idade baseada na data de nascimento cadastrada na Silver
        (CAST(strftime('%Y', 'now') AS INTEGER) - CAST(strftime('%Y', data_nascimento) AS INTEGER)) AS idade
    FROM silver_clientes
)
SELECT 
    i.idade,
    COUNT(DISTINCT i.cliente_id) AS total_clientes,
    COUNT(e.emprestimo_id) AS total_emprestimos,
    -- Média de contratos por faixa etária
    ROUND(CAST(COUNT(e.emprestimo_id) AS REAL) / COUNT(DISTINCT i.cliente_id), 2) AS media_emprestimos
FROM idades_clientes i
LEFT JOIN silver_emprestimos e ON i.cliente_id = e.cliente_id
WHERE i.idade IS NOT NULL
GROUP BY i.idade
ORDER BY i.idade;


CREATE VIEW gold_faixa_emprestimos AS
WITH dados_base AS (
    SELECT
        c.faixa_renda,
        COUNT(e.emprestimo_id) AS total_emprestimos,
        SUM(CASE WHEN e.status = 'INADIMPLENTE' THEN 1 ELSE 0 END) AS total_inadimplentes
    FROM silver_clientes c
    LEFT JOIN silver_emprestimos e ON c.cliente_id = e.cliente_id
    WHERE e.emprestimo_id IS NOT NULL
    GROUP BY c.faixa_renda
)
SELECT 
    faixa_renda,
    total_emprestimos,
    total_inadimplentes,
    -- Agora sim podemos usar as colunas calculadas diretamente!
    ROUND((total_inadimplentes * 100.0) / total_emprestimos, 2) AS taxa_inadimplencia_da_faixa_pct
FROM dados_base
ORDER BY faixa_renda;



