import pandas as pd

class AIStrategy:
    """
    Encapsulates the AI decision logic and its parameters.
    This makes it easier to pass around and modify for optimization.
    """
    def __init__(self, ema_short_len=5, ema_long_len=20, vol_threshold=1.2, gap_threshold=0.0005):
        self.ema_short_len = ema_short_len
        self.ema_long_len = ema_long_len
        self.vol_threshold = vol_threshold
        self.gap_threshold = gap_threshold

        # Construct dynamic column names based on params
        self.ema_short_name = f'ema_{self.ema_short_len}'
        self.ema_long_name = f'ema_{self.ema_long_len}'

    def get_decision(self, row):
        """
        Generates a trading decision for a given data row based on the strategy's parameters.
        """
        # --- Feature Extraction ---
        is_uptrend_fast = row[self.ema_short_name] > row[self.ema_long_name]
        is_downtrend_fast = row[self.ema_short_name] < row[self.ema_long_name]
        is_volatile_move = row['vol_rel'] > self.vol_threshold
        price_below_ema = row['price_ema_gap'] < -self.gap_threshold
        price_above_ema = row['price_ema_gap'] > self.gap_threshold
        regime = row['trend_regime']

        # --- AI Logic with Regime Filter ---
        fast_signal = 'HOLD'
        if is_uptrend_fast and price_below_ema and is_volatile_move:
            fast_signal = 'LONG'
        elif is_downtrend_fast and price_above_ema and is_volatile_move:
            fast_signal = 'SHORT'

        if fast_signal == 'LONG' and regime == 'Uptrend':
            return 'LONG'
        elif fast_signal == 'SHORT' and regime == 'Downtrend':
            return 'SHORT'
        else:
            return 'HOLD'

if __name__ == '__main__':
    from data_fetcher import fetch_detailed_klines
    from feature_engineering import calculate_fast_features, add_regime_features

    # Using the specific symbol for OKX perpetual swap
    SYMBOL = 'DOGE-USDT-SWAP'
    EXCHANGE = 'okx'

    # --- Create a default strategy instance ---
    default_strategy = AIStrategy()

    # --- Fetch data and calculate features based on strategy params ---
    ohlcv_data = fetch_detailed_klines(symbol=SYMBOL, limit=2000, exchange_name=EXCHANGE)
    features_df = calculate_fast_features(
        ohlcv_data.copy(),
        ema_short_len=default_strategy.ema_short_len,
        ema_long_len=default_strategy.ema_long_len
    )
    final_df = add_regime_features(features_df, symbol=SYMBOL)

    print("--- AI Decision Simulation with Strategy Object ---")
    final_df['decision'] = final_df.apply(default_strategy.get_decision, axis=1)

    active_decisions = final_df[final_df['decision'] != 'HOLD']

    if active_decisions.empty:
        print("No LONG/SHORT signals generated.")
    else:
        print(active_decisions[['k_close', 'trend_regime', 'decision']])
