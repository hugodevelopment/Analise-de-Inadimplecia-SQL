--DROP VIEW IF EXISTS gold_feature_store_ml;

CREATE VIEW gold_feature_store_ml AS
SELECT
    c.cliente_id,
    c.nome,
    c.score_credito,
    c.renda_mensal,
    c.faixa_renda,
    c.estado,
    ROUND(julianday('now') - julianday(c.data_cadastro)) AS dias_cliente,
    emp.total_emprestimos,
    emp.valor_total_emprestado,
    emp.valor_medio_emprestimo,
    emp.parcela_media,
    emp.prazo_medio,
    rc.valor_total_pago,
    rc.saldo_devedor,
    ROUND(rc.saldo_devedor / c.renda_mensal, 2) AS comprometimento_renda,
    rc.total_eventos_risco,
    rc.nivel_risco,
    emp.target_pd
FROM silver_clientes c
LEFT JOIN (
    SELECT
        cliente_id,
        COUNT(*) AS total_emprestimos,
        SUM(valor_emprestado) AS valor_total_emprestado,
        AVG(valor_emprestado) AS valor_medio_emprestimo,
        AVG(valor_parcela) AS parcela_media,
        AVG(num_parcelas) AS prazo_medio,
        MAX(CASE WHEN status='INADIMPLENTE' THEN 1 ELSE 0 END) AS target_pd
    FROM silver_emprestimos
    GROUP BY cliente_id
) emp ON c.cliente_id = emp.cliente_id
LEFT JOIN (
    SELECT
        e.cliente_id,
        SUM(COALESCE(p.valor_total_pago, 0)) AS valor_total_pago,
        SUM(e.valor_emprestado) - SUM(COALESCE(p.valor_total_pago, 0)) AS saldo_devedor,
        SUM(COALESCE(ev.total_eventos, 0)) AS total_eventos_risco,
        MAX(COALESCE(ev.nivel_risco, 0)) AS nivel_risco
    FROM silver_emprestimos e
    LEFT JOIN (
        SELECT
            emprestimo_id,
            SUM(valor_pago) AS valor_total_pago
        FROM silver_pagamentos
        GROUP BY emprestimo_id
    ) p ON e.emprestimo_id = p.emprestimo_id
    LEFT JOIN (
        SELECT
            emprestimo_id,
            COUNT(*) AS total_eventos,
            MAX(
                CASE
                    WHEN tipo_evento='CALOTE' THEN 4
                    WHEN tipo_evento='ATRASO_90' THEN 3
                    WHEN tipo_evento='ATRASO_60' THEN 2
                    WHEN tipo_evento='ATRASO_30' THEN 1
                    ELSE 0
                END
            ) AS nivel_risco
        FROM silver_eventos_risco
        GROUP BY emprestimo_id
    ) ev ON e.emprestimo_id = ev.emprestimo_id
    GROUP BY e.cliente_id
) rc ON c.cliente_id = rc.cliente_id;