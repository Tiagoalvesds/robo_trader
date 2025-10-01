
import pandas as pd
import numpy as np
from binance.client import Client
from datetime import datetime, timedelta
from ta.volatility import BollingerBands
from ta.trend import SMAIndicator
from tqdm import tqdm
import time

# 🔐 Substitua pelas suas credenciais da Binance
API_KEY = 'SUA_API_KEY'
API_SECRET = 'SEU_API_SECRET'

# ⚙️ Configurações
SYMBOL = 'SOLBRL'
INTERVAL = Client.KLINE_INTERVAL_1HOUR
PERIODOS = 72  # Para SMA
DESVIO = 2     # Para Bollinger Bands
ANOS = 2       # Período de análise

# 📅 Datas de início e fim
fim = datetime.now()
inicio = fim - timedelta(days=ANOS * 365)

# 🧠 Inicializa o cliente da Binance
client = Client(API_KEY, API_SECRET)

def obter_dados(symbol, interval, start, end):
    dados = []
    limite = 1000  # Máximo permitido por chamada
    inicio_ts = int(start.timestamp() * 1000)
    fim_ts = int(end.timestamp() * 1000)

    with tqdm(total=fim_ts - inicio_ts, desc="Baixando dados") as pbar:
        while inicio_ts < fim_ts:
            klines = client.get_klines(
                symbol=symbol,
                interval=interval,
                startTime=inicio_ts,
                endTime=fim_ts,
                limit=limite
            )
            if not klines:
                break
            dados.extend(klines)
            ultimo_tempo = klines[-1][0]
            inicio_ts = ultimo_tempo + 1
            pbar.update(ultimo_tempo - inicio_ts)
            time.sleep(0.5)  # Para evitar rate limits
    return dados

def preparar_dataframe(klines):
    colunas = [
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ]
    df = pd.DataFrame(klines, columns=colunas)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df

def calcular_indicadores(df):
    bb = BollingerBands(close=df['close'], window=20, window_dev=DESVIO)
    sma = SMAIndicator(close=df['close'], window=PERIODOS)

    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['sma72'] = sma.sma_indicator()
    return df

def identificar_sinais(df):
    df['sinal_compra'] = (df['close'] <= df['bb_lower']) & (df['close'] < df['sma72'])
    df['sinal_venda'] = (df['close'] >= df['bb_upper']) & (df['close'] > df['sma72'])
    return df

def analisar_estatisticas(df):
    total_candles = len(df)
    total_compras = df['sinal_compra'].sum()
    total_vendas = df['sinal_venda'].sum()

    print(f"Total de candles analisados: {total_candles}")
    print(f"Total de sinais de COMPRA: {total_compras}")
    print(f"Total de sinais de VENDA: {total_vendas}")

    # Distribuição mensal
    df['mes'] = df.index.to_period('M')
    compras_mensais = df.groupby('mes')['sinal_compra'].sum()
    vendas_mensais = df.groupby('mes')['sinal_venda'].sum()

    print("\nSinais de COMPRA por mês:")
    print(compras_mensais)

    print("\nSinais de VENDA por mês:")
    print(vendas_mensais)

    # Salvar em CSV
    df.to_csv('analise_SOLBRL.csv')
    print("\nDados salvos em 'analise_SOLBRL.csv'.")

# 🔄 Execução
klines = obter_dados(SYMBOL, INTERVAL, inicio, fim)
df = preparar_dataframe(klines)
df = calcular_indicadores(df)
df = identificar_sinais(df)
analisar_estatisticas(df)
