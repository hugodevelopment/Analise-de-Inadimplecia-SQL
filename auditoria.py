import sqlite3
import pandas as pd


class AuditorFeatureStore:
    """
    Classe responsável por validar a qualidade da Feature Store
    antes do treinamento dos modelos de Machine Learning.
    """

    def __init__(self, caminho_banco="data/finbank.db"):

        self.conn = sqlite3.connect(caminho_banco)

        self.df = pd.read_sql(
            "SELECT * FROM gold_feature_store_ml",
            self.conn
        )

        print("=" * 70)
        print("AUDITORIA DA FEATURE STORE")
        print("=" * 70)

    # ==========================================================
    # Informações gerais
    # ==========================================================

    def informacoes_gerais(self):

        print("\nInformações Gerais\n")

        print(self.df.info())

        print("\nResumo Estatístico\n")

        print(self.df.describe(include="all").T)

    # ==========================================================
    # Valores nulos
    # ==========================================================

    def verificar_nulos(self):

        print("\nValores Nulos\n")

        nulos = (
            self.df
            .isnull()
            .sum()
            .sort_values(ascending=False)
        )

        print(nulos)

        return nulos

    # ==========================================================
    # Duplicidade
    # ==========================================================

    def verificar_duplicados(self):

        print("\nDuplicidade de Clientes\n")

        duplicados = self.df.duplicated(
            subset="cliente_id"
        ).sum()

        print(f"Clientes duplicados: {duplicados}")

        return duplicados

    # ==========================================================
    # Score
    # ==========================================================

    def verificar_score(self):

        print("\nValidação do Score\n")

        print(self.df["score_credito"].describe())

        fora_intervalo = self.df[
            (self.df["score_credito"] < 300) |
            (self.df["score_credito"] > 850)
        ]

        print(
            f"\nClientes com score inválido: {len(fora_intervalo)}"
        )

        return fora_intervalo

    # ==========================================================
    # Renda
    # ==========================================================

    def verificar_renda(self):

        print("\nValidação da Renda\n")

        print(self.df["renda_mensal"].describe())

        renda_negativa = self.df[
            self.df["renda_mensal"] <= 0
        ]

        print(
            f"\nClientes com renda inválida: {len(renda_negativa)}"
        )

        return renda_negativa

    # ==========================================================
    # Saldo Devedor
    # ==========================================================

    def verificar_saldo(self):

        print("\nSaldo Devedor\n")

        negativos = self.df[
            self.df["saldo_devedor"] < 0
        ]

        print(
            f"Saldos negativos: {len(negativos)}"
        )

        return negativos

    # ==========================================================
    # Comprometimento
    # ==========================================================

    def verificar_comprometimento(self):

        print("\nComprometimento de Renda\n")

        negativos = self.df[
            self.df["comprometimento_renda"] < 0
        ]

        print(
            f"Comprometimentos negativos: {len(negativos)}"
        )

        return negativos

    # ==========================================================
    # Target
    # ==========================================================

    def verificar_target(self):

        print("\nDistribuição do Target\n")

        print(
            self.df["target_pd"]
            .value_counts(dropna=False)
        )

        print("\nPercentual")

        print(
            (
                self.df["target_pd"]
                .value_counts(normalize=True, dropna=False)
                * 100
            ).round(2)
        )

    # ==========================================================
    # Empréstimos
    # ==========================================================

    def verificar_emprestimos(self):

        print("\nResumo dos Empréstimos\n")

        print(
            self.df["total_emprestimos"].describe()
        )

        sem_emprestimo = self.df[
            self.df["total_emprestimos"].isna()
        ]

        print(
            f"\nClientes sem empréstimos: {len(sem_emprestimo)}"
        )

        return sem_emprestimo

    # ==========================================================
    # Pagamentos maiores que empréstimos
    # ==========================================================

    def verificar_pagamentos(self):

        print("\nPagamentos x Empréstimos\n")

        inconsistentes = self.df[

            self.df["valor_total_pago"] >
            self.df["valor_total_emprestado"]

        ]

        print(

            f"Clientes com pagamento maior que empréstimo: "

            f"{len(inconsistentes)}"

        )

        return inconsistentes

    # ==========================================================
    # Correlação
    # ==========================================================

    def correlacao(self):

        print("\nCorrelação\n")

        correlacao = self.df.corr(
            numeric_only=True
        )

        print(correlacao)

        return correlacao

    # ==========================================================
    # Auditoria Completa
    # ==========================================================

    def executar(self):

        self.informacoes_gerais()

        self.verificar_nulos()

        self.verificar_duplicados()

        self.verificar_score()

        self.verificar_renda()

        self.verificar_emprestimos()

        self.verificar_saldo()

        self.verificar_comprometimento()

        self.verificar_pagamentos()

        self.verificar_target()

        self.correlacao()

        print("\nAuditoria Finalizada!")

        self.conn.close()


if __name__ == "__main__":

    auditor = AuditorFeatureStore()

    auditor.executar()