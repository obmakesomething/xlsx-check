import ccxt
import pandas as pd
import time
import datetime as dt
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("downloader.log"), logging.StreamHandler()])

def download_historical_data(symbol, days_to_fetch, timeframe='1m', data_dir='data', exchange_name='okx'):
    """
    Downloads historical kline data from a specified exchange and saves it to a CSV file.
    """
    exchange_class = getattr(ccxt, exchange_name)
    exchange = exchange_class()

    filename = f"{data_dir}/{symbol.replace('/', '_').replace(':', '_')}_{timeframe}_{days_to_fetch}d_{exchange_name}.csv"

    os.makedirs(data_dir, exist_ok=True)

    if os.path.exists(filename):
        logging.info(f"Data already exists: {filename}. Skipping download.")
        return filename

    logging.info(f"--- Starting Download for {symbol} from {exchange_name} ({days_to_fetch} days) ---")

    all_ohlcv = []
    since = exchange.milliseconds() - days_to_fetch * 24 * 60 * 60 * 1000

    limit = 100

    while since < exchange.milliseconds():
        try:
            logging.info(f"Fetching data from {exchange.iso8601(since)}")
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            if len(ohlcv):
                since = ohlcv[-1][0] + (exchange.parse_timeframe(timeframe) * 1000)
                all_ohlcv.extend(ohlcv)
                time.sleep(exchange.rateLimit / 1000)
            else:
                since += limit * exchange.parse_timeframe(timeframe) * 1000

        except Exception as e:
            logging.error(f"An error occurred: {e}. Retrying...")
            time.sleep(5)

    logging.info(f"Download complete. Total candles: {len(all_ohlcv)}")

    df = pd.DataFrame(all_ohlcv, columns=['k_open_time', 'k_open', 'k_high', 'k_low', 'k_close', 'k_volume'])
    df['k_open_time'] = pd.to_datetime(df['k_open_time'], unit='ms')
    df.drop_duplicates(subset='k_open_time', keep='first', inplace=True)

    df.to_csv(filename, index=False)
    logging.info(f"Data saved to {filename}")

    return filename

if __name__ == '__main__':
    SYMBOL_TO_DOWNLOAD = 'DOGE-USDT-SWAP' # Final correct symbol for OKX perpetual swap
    DAYS = 365

    download_historical_data(SYMBOL_TO_DOWNLOAD, days_to_fetch=DAYS, exchange_name='okx')
