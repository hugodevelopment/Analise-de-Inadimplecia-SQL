import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

def executar_predicao_risco(caminho_banco="finbank.db"):
    print("🔮 Iniciando o Pipeline de Machine Learning do FinBank...\n")
    
    # 1. Conexão direta com o banco de dados (Nível Pleno)
    conn = sqlite3.connect("data/finbank.db")
    
    # Buscando os dados da sua view consolidada de risco
    query = """
    SELECT 
        score_credito,
        total_emprestimos,
        valor_total_emprestado,
        valor_inadimplente
    FROM gold_ranking_risco_clientes
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("❌ Erro: A view selecionada não retornou dados.")
        return

    print(f"📊 Dados carregados com sucesso! Total de registros: {len(df)}")
    
    # 2. FEATURE ENGINEERING & DEFINIÇÃO DOS TARGETS (Basileia)
    # Target 1 (PD): Se o valor inadimplente for maior que zero, é considerado calote (1), se não (0)
    df['target_pd'] = np.where(df['valor_inadimplente'] > 0, 1, 0)
    
    # Target 2 (EAD): A exposição real é o valor total que estava na mão do cliente quando ele falhou
    df['ead_real'] = df['valor_total_emprestado']
    
    # Variáveis explicativas (Features) que o modelo vai usar para aprender
    X = df[['score_credito', 'total_emprestimos', 'valor_total_emprestado']]
    y_pd = df['target_pd']
    
    # 3. DIVISÃO EM TREINO E TESTE (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X, y_pd, test_size=0.2, random_state=42, stratify=y_pd)
    
    # 4. TREINAMENTO MODELO DE PD (Probability of Default)
    # Usamos Random Forest para capturar casos complexos (como o do Vinícius que tinha score médio mas muitos empréstimos)
    modelo_pd = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=6)
    modelo_pd.fit(X_train, y_train)
    
    # 5. AVALIAÇÃO DO MODELO DE CALOTE
    predicoes = modelo_pd.predict(X_test)
    probabilidades = modelo_pd.predict_proba(X_test)[:, 1]# Pega a probabilidade do calote acontecer
    
    print("\n--- 📈 RELATÓRIO DE PERFORMANCE (PD) ---")
    print(classification_report(y_test, predicoes))
    print(f"ROC AUC Score (Poder de Discriminação): {roc_auc_score(y_test, probabilidades):.4f}")
    
    # 6. ENGENHARIA DE RISCO FINAL: CALCULANDO O PARÂMETRO EAD
    # Para os clientes que o modelo calculou alto risco, aplicamos a exposição
    df['probabilidade_default_pct'] = modelo_pd.predict_proba(X)[:, 1]* 100

    print((df['probabilidade_default_pct']))

    df['perda_esperada_ead'] = df['valor_total_emprestado'] * (df['probabilidade_default_pct'] / 100)

    print("oi")
    print(df['perda_esperada_ead'])
    
    print("\n--- 💰 SUMÁRIO DE EXPOSIÇÃO FINANCEIRA (EAD) ---")
    Exposicao_total_risco = df['perda_esperada_ead'].sum()
    print(f"O Head Financeiro deve provisionar R$ {exposicao_total_risco:,.2f} para cobrir perdas estimadas.")
    
    return df

if __name__ == "__main__":
    # Certifique-se de passar o nome correto do seu arquivo de banco SQLite aqui
    df_resultado = executar_predicao_risco("finbank.db")
