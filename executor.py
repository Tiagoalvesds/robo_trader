import os
import time
import logging
import math
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException
from ta.volatility import BollingerBands
from ta.trend import SMAIndicator
import pandas as pd
from telegram import Bot
import asyncio

# ============================
# Configurações iniciais
# ============================
load_dotenv()

SYMBOL = os.getenv('SYMBOL', 'SOLBRL')
INTERVAL = os.getenv('INTERVAL', '1h')
MARGIN_FACTOR = float(os.getenv('MARGIN_FACTOR', '0.99'))  # Fator de margem padrão: 0.99
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ============================
# Setup de serviços
# ============================
client = Client(API_KEY, API_SECRET)
bot_telegram = Bot(token=TELEGRAM_TOKEN)

# ============================
# Setup de logs
# ============================
log_dir = "/root/robo_trade/logs"
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "bot.log")

logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def send_telegram_message(message: str):
    try:
        await bot_telegram.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem no Telegram: {e}")

def log_info(message: str):
    logging.info(message)

def log_and_notify(message: str):
    logging.info(message)
    asyncio.run(send_telegram_message(message))

# ============================
# Função de saldo real
# ============================
def consultar_saldos():
    base_asset = SYMBOL[:3]
    quote_asset = SYMBOL[3:]
    try:
        saldo_base = float(client.get_asset_balance(asset=base_asset)['free'])
        saldo_quote = float(client.get_asset_balance(asset=quote_asset)['free'])
        return saldo_base, saldo_quote, base_asset, quote_asset
    except Exception as e:
        log_and_notify(f"❌ Erro ao obter saldos: {e}")
        return 0.0, 0.0, base_asset, quote_asset

# ============================
# Função de posição real
# ============================
def consultar_posicao(saldo_base):
    return "COMPRADO" if saldo_base > 0.001 else "SEM_POSICAO"

# ============================
# Função principal
# ============================
def main():
    while True:
        try:
            klines = client.get_klines(symbol=SYMBOL, interval=INTERVAL, limit=100)
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'num_trades',
                'taker_buy_base_vol', 'taker_buy_quote_vol', 'ignore'
            ])
            df['close'] = df['close'].astype(float)

            df['sma72'] = SMAIndicator(close=df['close'], window=72).sma_indicator()
            bb = BollingerBands(close=df['close'], window=20, window_dev=2)
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()

            preco_atual = df['close'].iloc[-1]
            banda_superior = df['bb_upper'].iloc[-1]
            banda_inferior = df['bb_lower'].iloc[-1]

            saldo_base, saldo_quote, base_asset, quote_asset = consultar_saldos()
            posicao = consultar_posicao(saldo_base)

            symbol_info = client.get_symbol_info(SYMBOL)
            step_size = 0.0001
            min_qty = 0.0
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    min_qty = float(f['minQty'])
                    break
            precision = int(round(-math.log10(step_size)))

            if posicao == "SEM_POSICAO":
                if preco_atual < banda_inferior and saldo_quote > 10:
                    try:
                        qtde_compra = (saldo_quote / preco_atual) * MARGIN_FACTOR
                        qtde_compra = qtde_compra - (qtde_compra % step_size)
                        qtde_compra = round(qtde_compra, precision)

                        if qtde_compra >= min_qty:
                            client.order_market_buy(symbol=SYMBOL, quantity=qtde_compra)
                            msg = f"🐃 🟢COMPRA EXECUTADA🟢: {qtde_compra} {base_asset} a {preco_atual:.2f} {quote_asset}"
                            log_and_notify(msg)
                        else:
                            log_info(f"❌ Quantidade insuficiente para compra: {qtde_compra} < minQty {min_qty}")
                    except Exception as e:
                        log_and_notify(f"❌ Erro na compra: {e}")
                else:
                    log_info("🔍 Aguardando oportunidade de compra...")

            elif posicao == "COMPRADO":
                if preco_atual > banda_superior and saldo_base > 0.001:
                    try:
                        qtde_venda = saldo_base * MARGIN_FACTOR
                        qtde_venda = qtde_venda - (qtde_venda % step_size)
                        qtde_venda = round(qtde_venda, precision)

                        if qtde_venda >= min_qty:
                            client.order_market_sell(symbol=SYMBOL, quantity=qtde_venda)
                            msg = f"🐻 🔴VENDA EXECUTADA🔴: {qtde_venda} {base_asset} a {preco_atual:.2f} {quote_asset}"
                            log_and_notify(msg)
                        else:
                            log_info(f"❌ Quantidade insuficiente para venda: {qtde_venda} < minQty {min_qty}")
                    except Exception as e:
                        log_and_notify(f"❌ Erro na venda: {e}")
                else:
                    log_info("🔍 Aguardando oportunidade de venda...")

        except BinanceAPIException as e:
            log_and_notify(f"❌ Erro Binance API: {str(e)}")
        except Exception as e:
            log_and_notify(f"❌ Erro inesperado: {str(e)}")

        time.sleep(60)

# ============================
# Execução contínua
# ============================
if __name__ == "__main__":
    main()
