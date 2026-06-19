"""
data/generate_data.py
---------------------
Gera dados simulados realistas para o projeto FinBank Risk Analysis.

Volumes:
    - 10.000 clientes
    - 15.000 empréstimos
    - ~60.000 pagamentos
    -  3.000 eventos de risco
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('pt_BR')
np.random.seed(42)
random.seed(42)

# ── Configurações ─────────────────────────────────────────────────────────────
N_CLIENTES    = 10_000
N_EMPRESTIMOS = 15_000
ESTADOS = ['SP', 'RJ', 'MG', 'RS', 'PR', 'BA', 'SC', 'GO', 'PE', 'CE']
DATA_INICIO = datetime(2021, 1, 1)
DATA_FIM    = datetime(2024, 12, 31)


def data_aleatoria(inicio, fim):
    delta = fim - inicio
    return inicio + timedelta(days=random.randint(0, delta.days))


# ── 1. Clientes ───────────────────────────────────────────────────────────────
def gerar_clientes():
    print("Gerando clientes...")
    clientes = []
    for i in range(1, N_CLIENTES + 1):
        # Score influencia renda e perfil de risco
        score = int(np.random.normal(620, 120))
        score = max(300, min(850, score))

        # Renda correlacionada com score
        renda_base = score * 8 + np.random.normal(0, 1000)
        renda = max(800, round(renda_base, 2))

        clientes.append({
            "cliente_id":      i,
            "nome":            fake.name(),
            "cpf":             fake.cpf(),
            "data_nascimento": fake.date_of_birth(minimum_age=18, maximum_age=70).strftime("%Y-%m-%d"),
            "score_credito":   score,
            "renda_mensal":    round(renda, 2),
            "estado":          random.choice(ESTADOS),
            "data_cadastro":   data_aleatoria(DATA_INICIO, DATA_FIM).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(clientes)


# ── 2. Empréstimos ────────────────────────────────────────────────────────────
def gerar_emprestimos(clientes_df):
    print("Gerando empréstimos...")
    emprestimos = []

    for i in range(1, N_EMPRESTIMOS + 1):
        cliente = clientes_df.sample(1).iloc[0]
        score   = cliente['score_credito']
        renda   = cliente['renda_mensal']

        # Score define taxa de juros e valor máximo
        if score >= 750:
            taxa    = round(random.uniform(0.8, 1.5), 2)
            valor   = round(random.uniform(5000, 50000), 2)
        elif score >= 600:
            taxa    = round(random.uniform(1.5, 3.5), 2)
            valor   = round(random.uniform(1000, 20000), 2)
        else:
            taxa    = round(random.uniform(3.5, 8.0), 2)
            valor   = round(random.uniform(500, 8000), 2)

        num_parcelas = random.choice([6, 12, 18, 24, 36, 48])
        parcela      = round(valor / num_parcelas * (1 + taxa / 100), 2)
        data_conc    = data_aleatoria(DATA_INICIO, DATA_FIM)

        # Status influenciado pelo score
        prob_inadimplente = max(0.02, (700 - score) / 1000)
        status = np.random.choice(
            ['ATIVO', 'QUITADO', 'INADIMPLENTE'],
            p=[0.5, 0.5 - prob_inadimplente, prob_inadimplente]
        )

        emprestimos.append({
            "emprestimo_id":  i,
            "cliente_id":     int(cliente['cliente_id']),
            "valor_emprestado": valor,
            "valor_parcela":  parcela,
            "num_parcelas":   num_parcelas,
            "taxa_juros":     taxa,
            "data_concessao": data_conc.strftime("%Y-%m-%d"),
            "status":         status,
        })
    return pd.DataFrame(emprestimos)


# ── 3. Pagamentos ─────────────────────────────────────────────────────────────
def gerar_pagamentos(emprestimos_df, clientes_df):
    print("Gerando pagamentos...")
    pagamentos = []
    pagamento_id = 1

    clientes_idx = clientes_df.set_index('cliente_id')

    for _, emp in emprestimos_df.iterrows():
        data_conc = datetime.strptime(emp['data_concessao'], "%Y-%m-%d")
        score     = clientes_idx.loc[emp['cliente_id'], 'score_credito']
        prob_atraso = max(0.05, (700 - score) / 800)

        for parcela_num in range(1, emp['num_parcelas'] + 1):
            vencimento = data_conc + timedelta(days=30 * parcela_num)

            if vencimento > datetime.now():
                break

            atrasou = random.random() < prob_atraso

            if not atrasou:
                dias_antes = random.randint(0, 3)
                data_pag   = vencimento - timedelta(days=dias_antes)
                status     = 'PAGO'
                valor_pago = emp['valor_parcela']
            else:
                dias_atraso = random.randint(1, 90)
                data_pag    = vencimento + timedelta(days=dias_atraso)
                status      = 'ATRASADO'
                multa       = emp['valor_parcela'] * 0.02
                valor_pago  = round(emp['valor_parcela'] + multa, 2)

            pagamentos.append({
                "pagamento_id":   pagamento_id,
                "emprestimo_id":  int(emp['emprestimo_id']),
                "parcela_num":    parcela_num,
                "data_vencimento": vencimento.strftime("%Y-%m-%d"),
                "data_pagamento":  data_pag.strftime("%Y-%m-%d"),
                "valor_devido":   emp['valor_parcela'],
                "valor_pago":     valor_pago,
                "status":         status,
            })
            pagamento_id += 1

    return pd.DataFrame(pagamentos)


# ── 4. Eventos de Risco ───────────────────────────────────────────────────────
def gerar_eventos_risco(emprestimos_df):
    print("Gerando eventos de risco...")
    eventos     = []
    evento_id   = 1
    inadimplentes = emprestimos_df[emprestimos_df['status'] == 'INADIMPLENTE']

    for _, emp in inadimplentes.iterrows():
        data_base = datetime.strptime(emp['data_concessao'], "%Y-%m-%d")
        tipos = ['ATRASO_30', 'ATRASO_60', 'ATRASO_90', 'CALOTE']

        for i, tipo in enumerate(tipos):
            if random.random() > 0.3:
                eventos.append({
                    "evento_id":     evento_id,
                    "cliente_id":    int(emp['cliente_id']),
                    "emprestimo_id": int(emp['emprestimo_id']),
                    "tipo_evento":   tipo,
                    "data_evento":   (data_base + timedelta(days=30*(i+1))).strftime("%Y-%m-%d"),
                    "valor_em_risco": round(emp['valor_emprestado'] * (1 - i * 0.2), 2),
                })
                evento_id += 1

    return pd.DataFrame(eventos)


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    clientes    = gerar_clientes()
    emprestimos = gerar_emprestimos(clientes)
    pagamentos  = gerar_pagamentos(emprestimos, clientes)
    eventos     = gerar_eventos_risco(emprestimos)

    clientes.to_csv("data/clientes.csv",       index=False, sep=";")
    emprestimos.to_csv("data/emprestimos.csv", index=False, sep=";")
    pagamentos.to_csv("data/pagamentos.csv",   index=False, sep=";")
    eventos.to_csv("data/eventos_risco.csv",   index=False, sep=";")

    print("\n" + "─" * 50)
    print("  FinBank — Dados Gerados com Sucesso!")
    print("─" * 50)
    print(f"  Clientes    : {len(clientes):,}")
    print(f"  Empréstimos : {len(emprestimos):,}")
    print(f"  Pagamentos  : {len(pagamentos):,}")
    print(f"  Eventos     : {len(eventos):,}")
    print("─" * 50)
