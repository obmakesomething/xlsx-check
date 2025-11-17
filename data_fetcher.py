import ccxt
import pandas as pd
import time

def fetch_detailed_klines(symbol='BTC/USDT:USDT', timeframe='1m', limit=100, since=None):
    """Fetches detailed historical kline data from KuCoin Futures."""
    exchange = ccxt.kucoinfutures({
        'options': {
            'adjustForTimeDifference': True,
        }
    })

    # If since is not provided, fetch `limit` candles from the past
    if since is None:
        since = exchange.milliseconds() - limit * exchange.parse_timeframe(timeframe) * 1000

    response = exchange.fetch_ohlcv(symbol, timeframe, since, limit)

    columns = ['k_open_time', 'k_open', 'k_high', 'k_low', 'k_close', 'k_volume']

    df = pd.DataFrame(response, columns=columns)

    if df.empty:
        return df

    df['k_open_time'] = pd.to_datetime(df['k_open_time'], unit='ms')

    numeric_cols = ['k_open', 'k_high', 'k_low', 'k_close', 'k_volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col])

    df.set_index('k_open_time', inplace=True)

    return df

if __name__ == '__main__':
    try:
        detailed_data = fetch_detailed_klines(limit=5)
        print("--- Detailed Kline Data (from KuCoin Futures) ---")
        print(detailed_data)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
