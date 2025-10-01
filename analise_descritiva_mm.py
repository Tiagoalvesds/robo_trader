# cruzamentos_mm.py

import pandas as pd
from utils import obter_dados, preparar_dataframe
from ta.trend import SMAIndicator
from config import SYMBOL, INTERVAL

def calcular_cruzamentos(df):
    sma40 = SMAIndicator(close=df['close'], window=40).sma_indicator()
    sma72 = SMAIndicator(close=df['close'], window=72).sma_indicator()

    df['sma40'] = sma40
    df['sma72'] = sma72

    df = df.dropna().copy()
    df['cruzamento'] = 0  # 1: alta, -1: baixa

    df['cruzamento'] = ((df['sma40'] > df['sma72']) & (df['sma40'].shift(1) <= df['sma72'].shift(1))).astype(int)
    df['cruzamento'] -= ((df['sma40'] < df['sma72']) & (df['sma40'].shift(1) >= df['sma72'].shift(1))).astype(int)

    return df

def analisar_cruzamentos(df):
    cruzamentos = df[df['cruzamento'] != 0]
    total = len(cruzamentos)
    alta = (cruzamentos['cruzamento'] == 1).sum()
    baixa = (cruzamentos['cruzamento'] == -1).sum()

    pct_alta = round((alta / total) * 100, 2) if total else 0
    pct_baixa = round((baixa / total) * 100, 2) if total else 0

    print(f"\n📈 Total de cruzamentos: {total}")
    print(f"🔼 Cruzamentos de alta (compra): {alta} ({pct_alta}%)")
    print(f"🔽 Cruzamentos de baixa (venda): {baixa} ({pct_baixa}%)")

    # Exporta CSV
    cruzamentos.to_csv(f'cruzamentos_{SYMBOL}.csv')
    print(f"\n💾 Arquivo salvo: cruzamentos de médias móveis_{SYMBOL}.csv")

# 🚀 Execução
if __name__ == "__main__":
    klines = obter_dados()
    df = preparar_dataframe(klines)
    df = calcular_cruzamentos(df)
    analisar_cruzamentos(df)
