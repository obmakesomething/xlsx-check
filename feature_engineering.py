import pandas as pd
import pandas_ta as ta
import ccxt
from data_fetcher import fetch_detailed_klines

def calculate_fast_features(df, ema_short_len=5, ema_long_len=20, atr_len=14, vol_ma_len=20):
    """Calculates the 'Fast Loop' features with customizable parameters."""
    df = df.sort_index()

    # Dynamic column names
    ema_short_name = f'ema_{ema_short_len}'
    ema_long_name = f'ema_{ema_long_len}'
    atr_name = f'mini_ATR_{atr_len}'

    df['ret_1m'] = df['k_close'].pct_change()
    df.ta.ema(close=df['k_close'], length=ema_short_len, append=True, col_names=(ema_short_name,))
    df.ta.ema(close=df['k_close'], length=ema_long_len, append=True, col_names=(ema_long_name,))
    df['price_ema_gap'] = (df['k_close'] - df[ema_short_name]) / df[ema_short_name]
    df.ta.atr(high=df['k_high'], low=df['k_low'], close=df['k_close'], length=atr_len, append=True, col_names=(atr_name,))
    vol_ma = df['k_volume'].rolling(window=vol_ma_len).mean()
    df['vol_rel'] = df['k_volume'] / vol_ma

    return df

def add_regime_features(df_1m, symbol, timeframe='4h', adx_len=14):
    """Calculates and merges 'Regime Loop' features."""
    print(f"Fetching {timeframe} data for regime analysis...")
    exchange = ccxt.kucoinfutures()

    candles_needed = adx_len * 3 # Ensure enough data for ADX calculation
    timeframe_duration_ms = exchange.parse_timeframe(timeframe) * 1000
    since = exchange.milliseconds() - candles_needed * timeframe_duration_ms

    df_4h = fetch_detailed_klines(symbol=symbol, timeframe=timeframe, since=since, limit=candles_needed)

    if df_4h.empty:
        print("Could not fetch 4h data for regime, defaulting to 'Range'.")
        df_1m['trend_regime'] = 'Range'
        return df_1m

    adx = df_4h.ta.adx(high=df_4h['k_high'], low=df_4h['k_low'], close=df_4h['k_close'], length=adx_len)

    if adx is None or adx.empty:
        print("Could not calculate ADX, defaulting to 'Range'.")
        df_1m['trend_regime'] = 'Range'
        return df_1m

    df_4h['ADX'] = adx[f'ADX_{adx_len}']
    df_4h['DMP'] = adx[f'DMP_{adx_len}']
    df_4h['DMN'] = adx[f'DMN_{adx_len}']

    def determine_regime(row):
        if row['ADX'] > 25 and row['DMP'] > row['DMN']:
            return 'Uptrend'
        elif row['ADX'] > 25 and row['DMP'] < row['DMN']:
            return 'Downtrend'
        else:
            return 'Range'

    df_4h['trend_regime'] = df_4h.apply(determine_regime, axis=1)

    df_merged = pd.merge_asof(df_1m.sort_index(), df_4h[['trend_regime']].sort_index(),
                              left_index=True, right_index=True, direction='backward')

    df_merged.dropna(inplace=True)
    return df_merged

if __name__ == '__main__':
    SYMBOL = 'BTC/USDT:USDT'
    ohlcv_data = fetch_detailed_klines(symbol=SYMBOL, limit=1000)
    features_df = calculate_fast_features(ohlcv_data.copy())
    final_df = add_regime_features(features_df, symbol=SYMBOL)

    print("--- Final DataFrame with Regime (Sample) ---")
    print(final_df[['k_close', 'ema_20', 'vol_rel', 'trend_regime']].tail())
