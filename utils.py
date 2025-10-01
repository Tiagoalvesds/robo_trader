# utils.py

import pandas as pd
import time
from datetime import datetime, timedelta
from binance.client import Client
from ta.volatility import BollingerBands
from ta.trend import SMAIndicator
from tqdm import tqdm
from config import SYMBOL, INTERVAL, ANOS, API_KEY, API_SECRET

client = Client(API_KEY, API_SECRET)

def obter_dados(symbol=SYMBOL, interval=INTERVAL, anos=ANOS):
    fim = datetime.now()
    inicio = fim - timedelta(days=anos * 365)
    inicio_ts = int(inicio.timestamp() * 1000)
    fim_ts = int(fim.timestamp() * 1000)

    dados = []
    limite = 1000

    with tqdm(total=(fim_ts - inicio_ts), desc=f"Baixando {symbol}") as pbar:
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
            ultimo = klines[-1][0]
            inicio_ts = ultimo + 1
            pbar.update(ultimo - inicio_ts)
            time.sleep(0.5)
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
    bb = BollingerBands(close=df['close'], window=20, window_dev=2)
    sma = SMAIndicator(close=df['close'], window=72)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['sma72'] = sma.sma_indicator()
    return df

def identificar_sinais(df):
    df['sinal_compra'] = (df['close'] <= df['bb_lower']) & (df['close'] < df['sma72'])
    df['sinal_venda'] = (df['close'] >= df['bb_upper']) & (df['close'] > df['sma72'])
    return df
