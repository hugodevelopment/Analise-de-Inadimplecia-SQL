"""
pipeline.py
-----------
Executa o pipeline Medallion completo do FinBank.

Bronze → Silver → Gold
"""

import sqlite3
import pandas as pd
import logging
import sys

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt = "%H:%M:%S",
)
logger = logging.getLogger(__name__)

"Aqui é onde será criado nosso banco de dados com os bancos"
DB_PATH = "data/finbank.db"


"Aqui ele faz a conexão do banco de dados com SQLITE3"
def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

"Aqui ele conecta os arquivos csvs criados no generate data.py, no entano no aquivo bronze sql ele verifica se essas arquivos existem e criam a tabela caso não"
def carregar_bronze(conn):
    """Ingere os CSVs na camada Bronze."""
    logger.info("Iniciando camada Bronze...")
    tabelas = {
        "bronze_clientes":      "data/clientes.csv",
        "bronze_emprestimos":   "data/emprestimos.csv",
        "bronze_pagamentos":    "data/pagamentos.csv",
        "bronze_eventos_risco": "data/eventos_risco.csv",
    }
    for tabela, arquivo in tabelas.items():
        df = pd.read_csv(arquivo, sep=";", dtype=str)
        df.to_sql(tabela, conn, if_exists="replace", index=False)
        logger.info(f"Bronze: {tabela} → {len(df):,} registros")


def executar_sql(conn, caminho):
    """Executa um arquivo SQL no banco."""
    with open(caminho, 'r', encoding='utf-8') as f:
        sql = f.read()
    for statement in sql.split(';'):
        stmt = statement.strip()
        if stmt:
            try:
                conn.execute(stmt)
            except Exception as e:
                if 'already exists' not in str(e):
                    logger.warning(f"SQL ignorado: {e}")
    conn.commit()


def executar_pipeline():
    logger.info("─" * 50)
    logger.info("FinBank Risk Analysis — Pipeline Medallion")
    logger.info("─" * 50)

    conn = conectar()

    # Bronze
    carregar_bronze(conn)

    # Silver
    logger.info("Iniciando camada Silver...")
    #Aaui ele verifica a a camada Silver, no entanto, ele valida antes se as tabelas ja existem
    conn.execute("DROP TABLE IF EXISTS silver_clientes")
    conn.execute("DROP TABLE IF EXISTS silver_emprestimos")
    conn.execute("DROP TABLE IF EXISTS silver_pagamentos")
    conn.execute("DROP TABLE IF EXISTS silver_eventos_risco")
    executar_sql(conn, "sql/silver/transform.sql")
    for tabela in ["silver_clientes","silver_emprestimos",
                   "silver_pagamentos","silver_eventos_risco"]:
        n = conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        logger.info(f"Silver: {tabela} → {n:,} registros")

    # Gold
    logger.info("Iniciando camada Gold...")
     #Aaui ele verifica a camada Gold, no entanto, ele valida antes se as tabelas ja existem usando o for
    for view in ["gold_inadimplencia_por_estado","gold_evolucao_inadimplencia",
                 "gold_ranking_risco_clientes","gold_risco_por_score",
                 "gold_alerta_risco_iminente"]:
        conn.execute(f"DROP VIEW IF EXISTS {view}")
    executar_sql(conn, "sql/gold/metrics.sql")
    logger.info("Gold: 5 views analíticas criadas")

    # Preview
    logger.info("─" * 50)
    # Aqui ele cria a view com as metricas do gold
    logger.info("Preview — Inadimplência por Estado (Top 5):")
    # Aqui ele transformas as colunas da tabela em sql em tabelas em csv
    df = pd.read_sql("""
        SELECT estado, total_emprestimos, inadimplentes,
               taxa_inadimplencia_pct, valor_em_risco
        FROM gold_inadimplencia_por_estado LIMIT 5
    """, conn)
    print(df.to_string(index=False))

    logger.info("─" * 50)
    logger.info("Preview — Risco por Faixa de Score:")
    df2 = pd.read_sql("""
        SELECT faixa_risco, score_medio, total_emprestimos,
               inadimplentes, taxa_inadimplencia_pct
        FROM gold_risco_por_score
    """, conn)
    print(df2.to_string(index=False))
    logger.info("─" * 50)
    logger.info("Pipeline concluído! Banco: data/finbank.db")

    conn.close()


if __name__ == "__main__":
    executar_pipeline()
