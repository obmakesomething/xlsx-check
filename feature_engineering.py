import pandas as pd
import pandas_ta as ta
import ccxt
import logging
from historical_data_downloader import download_historical_data

def calculate_fast_features(df, ema_short_len=5, ema_long_len=20, atr_len=14, vol_ma_len=20):
    """Calculates the 'Fast Loop' features with customizable parameters."""
    df = df.sort_index()

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

def add_regime_features(df_1m, symbol, timeframe='4h', adx_len=14, exchange_name='okx'):
    """Calculates and merges 'Regime Loop' features into the 1-minute dataframe."""
    logging.info(f"Getting {timeframe} data for regime analysis...")

    candles_needed = adx_len * 3
    ms_per_candle = ccxt.okx().parse_timeframe(timeframe) * 1000
    days_to_fetch = (candles_needed * ms_per_candle) / (1000 * 60 * 60 * 24)
    days_to_fetch = int(days_to_fetch) + 2

    regime_data_file = download_historical_data(
        symbol=symbol,
        days_to_fetch=days_to_fetch,
        timeframe=timeframe,
        exchange_name=exchange_name
    )

    df_4h = pd.read_csv(regime_data_file, parse_dates=['k_open_time'], index_col='k_open_time')

    if df_4h.empty:
        logging.warning("Could not load 4h data for regime, defaulting to 'Range'.")
        df_1m['trend_regime'] = 'Range'
        return df_1m

    adx = df_4h.ta.adx(high=df_4h['k_high'], low=df_4h['k_low'], close=df_4h['k_close'], length=adx_len)

    if adx is None or adx.empty:
        logging.warning("Could not calculate ADX, defaulting to 'Range'.")
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
