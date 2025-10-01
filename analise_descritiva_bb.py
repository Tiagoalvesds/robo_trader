# analise.py

import pandas as pd
from utils import obter_dados, preparar_dataframe, calcular_indicadores, identificar_sinais
from config import SYMBOL, INTERVAL

def simular_operacoes(df):
    operacoes = []
    em_posicao = False
    preco_compra = None
    data_compra = None

    for i in range(len(df)):
        linha = df.iloc[i]
        data = df.index[i]

        if not em_posicao and linha['sinal_compra']:
            preco_compra = linha['close']
            data_compra = data
            em_posicao = True

        elif em_posicao and linha['sinal_venda']:
            preco_venda = linha['close']
            lucro_pct = ((preco_venda - preco_compra) / preco_compra) * 100
            operacoes.append({
                'data_compra': data_compra,
                'preco_compra': preco_compra,
                'data_venda': data,
                'preco_venda': preco_venda,
                'lucro_percentual': lucro_pct
            })
            em_posicao = False

    return pd.DataFrame(operacoes)

def analisar(df, ops_df):
    df['mes'] = df.index.to_period('M')
    print(f"\n📊 Total de candles: {len(df)}")
    print(f"✅ Sinais de COMPRA: {df['sinal_compra'].sum()}")
    print(f"✅ Sinais de VENDA: {df['sinal_venda'].sum()}")
    print("\n📅 Sinais de COMPRA por mês:")
    print(df.groupby('mes')['sinal_compra'].sum())
    print("\n📅 Sinais de VENDA por mês:")
    print(df.groupby('mes')['sinal_venda'].sum())

    df.to_csv(f'analise de bolinger_{SYMBOL}.csv')
    print(f"\n💾 Arquivo salvo: analise de bolinger_{SYMBOL}.csv")

    if not ops_df.empty:
        ops_df['mes'] = ops_df['data_venda'].dt.to_period('M')
        print("\n📈 Lucro médio por operação (%), por mês:")
        print(ops_df.groupby('mes')['lucro_percentual'].mean().round(2))
        ops_df.to_csv(f'operacoes_simuladas_bolinger{SYMBOL}.csv', index=False)
        print(f"💾 Arquivo salvo: operacoes_simuladas_{SYMBOL}.csv")
    else:
        print("⚠️ Nenhuma operação concluída.")

# 🚀 Execução
if __name__ == "__main__":
    klines = obter_dados()
    df = preparar_dataframe(klines)
    df = calcular_indicadores(df)
    df = identificar_sinais(df)
    operacoes = simular_operacoes(df)
    analisar(df, operacoes)
