# 🏦 FinBank - Data Pipeline & Credit Risk Analytics (Medallion Architecture)

## 📌 Cenário de Negócio
O **FinBank** é uma fintech de crédito que precisava monitorar a saúde financeira de sua carteira de empréstimos, antecipar o impacto da inadimplência no fluxo de caixa e criar um mecanismo preditivo para futuras concessões. 

O grande desafio da instituição era ir além das análises estáticas de Bureaus de Crédito (como score bruto), identificando padrões comportamentais complexos como superendividamento induzido e fraudes de primeiro pagamento (*First Payment Default*).

---

## 🛠️ Tecnologias e Arquitetura de Dados
O ecossistema foi desenhado seguindo as melhores práticas de mercado utilizando o conceito de **Data Lakehouse moderno**:

* **Python (Faker, NumPy & Pandas):** Geração distribuída e simulação estatística de massas de dados realistas (perfis de clientes, contratos e histórico de eventos).
* **SQL (SQLite & DBeaver):** Estruturação do pipeline de transformação de dados e queries analíticas avançadas.
* **Machine Learning (Scikit-Learn):** Modelagem preditiva baseada nos frameworks internacionais de gestão de risco bancário.

### 📐 Arquitetura Medallion
1. **`Bronze`:** Ingestão dos dados brutos simulados, preservando o histórico original sem alterações.
2. **`Silver` (`silver_clientes`, `silver_emprestimos`, `silver_eventos_risco`):** Camada de higienização, tratamento de nulos, tipagem correta, correção de anomalias e aplicação de regras de negócio preliminares (como a criação da coluna `faixa_renda`).
3. **`Gold` (`gold_faixa_emprestimos`, `gold_risco_por_score`):** Agregações analíticas e *views* de negócio prontas para consumo da diretoria e alimentação dos modelos.

---

## 📊 Principais Insights da Análise Descritiva (Visão do Head Financeiro)

Abaixo estão as respostas analíticas obtidas diretamente na camada **Gold** do banco de dados, que baseiam as decisões estratégicas da instituição:

### 1. Relação Renda vs. Inadimplência (Volume Absoluto vs. Proporção)
A análise cruzada revelou um comportamento crucial para a precificação de juros:
* **Classe Baixa:** Concentra o **maior volume absoluto de calotes** do banco, impulsionado pela facilidade de acesso ao crédito (total de empréstimos elevado). É onde o maior montante de capital da instituição encontra-se retido.
* **Classe Muito Baixa:** Representa o **maior risco relativo e proporcional** (com taxa de inadimplência superior a 20%). Estatisticamente, a cada 5 empréstimos concedidos para esta faixa, 1 vira calote.

### 2. O Efeito "FPD" (First Payment Default) e Comportamento de Risco
Através da view `gold_risco_por_score`, foi identificado um padrão crítico: clientes com scores médios/bons obtendo aprovação para valores volumosos divididos em múltiplos contratos simultâneos, resultando em **inadimplência imediata** (sem amortização de nenhuma parcela). 

> **Decisão Estratégica:** O score estático não é suficiente para barrar fraudes ou superendividamento. Tornou-se obrigatória a criação de travas operacionais na camada Silver baseadas na velocidade de tomada de crédito e comportamento de atrasos.

---

## 🔮 Engenharia de Risco & Modelagem Preditiva (Framework Basileia)

O modelo preditivo implementado no script `predict_risk.py` foi estruturado sob os pilares regulatórios de risco bancário internacional para guiar o provisionamento de caixa:

1. **Probability of Default (PD - Probabilidade de Calote):** Um classificador *Random Forest* analisa as variáveis de score, renda, volume de contratos acumulados e histórico comportamental de atrasos (`silver_eventos_risco`) para calcular a probabilidade exata (0% a 100%) de o cliente deixar de pagar.
2. **Exposure at Default (EAD - Exposição ao Risco):** O modelo calcula o montante financeiro exato que estará em risco no momento da falha.
3. **Perda Esperada (Expected Loss):** O script cruza os pesos preditivos para fornecer ao Head Financeiro o valor exato em moeda corrente que deve ser provisionado em caixa para garantir a solvência do banco.

---

## 🚀 Como Executar o Projeto

1. **Clonar o Repositório:**
   ```bash
   git clone https://github.com
   cd finbank-risk-analytics
   ```
2. **Instalar Dependências:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Executar o Pipeline de Engenharia (Bronze ➡️ Silver):**
   ```bash
   python generate_data.py
   ```
4. **Executar o Modelo de Machine Learning (Previsão de Risco):**
   ```bash
   python predict_risk.py
