from historical_data_downloader import download_historical_data
from feature_engineering import calculate_fast_features, add_regime_features
from ai_decision_module import AIStrategy
from backtester import run_ai_futures_backtest
import itertools
import pandas as pd
import logging

def run_optimization(param_grid, symbol, leverage, days_to_backtest, exchange_name='okx'):
    """
    Runs a grid search optimization for the AI strategy including trailing stop.
    """
    logging.info("--- Starting Full Optimization ---")

    data_file = download_historical_data(symbol, days_to_fetch=days_to_backtest, exchange_name=exchange_name)

    logging.info("\nStep 1: Loading historical data...")
    ohlcv_data = pd.read_csv(data_file, parse_dates=['k_open_time'], index_col='k_open_time')

    logging.info("Step 2: Pre-calculating regime features...")
    max_ema_long = max(param_grid.get('ema_long_len', [200]))
    regime_base_df = calculate_fast_features(ohlcv_data.copy(), ema_long_len=max_ema_long)
    # The regime feature fetcher needs the ccxt-compatible symbol format
    regime_symbol = 'DOGE/USDT:USDT'
    final_base_df = add_regime_features(regime_base_df, symbol=regime_symbol, exchange_name=exchange_name)

    logging.info(f"\nStep 3: Testing combinations...")

    results = []
    keys, values = zip(*param_grid.items())
    param_combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

    for i, params in enumerate(param_combinations):
        if params.get('ema_short_len', 0) >= params.get('ema_long_len', float('inf')):
            continue

        logging.info(f"  Testing combo {i+1}/{len(param_combinations)}: {params}")

        # Separate strategy params from backtester params
        strategy_params = {k: v for k, v in params.items() if k not in ['trailing_stop_percent']}
        ts_param = params.get('trailing_stop_percent')

        strategy = AIStrategy(**strategy_params)

        temp_df = calculate_fast_features(
            ohlcv_data.copy(),
            ema_short_len=strategy.ema_short_len,
            ema_long_len=strategy.ema_long_len
        )
        temp_df_with_regime = pd.merge_asof(temp_df.sort_index(), final_base_df[['trend_regime']].sort_index(),
                                            left_index=True, right_index=True, direction='backward').dropna()

        backtest_result = run_ai_futures_backtest(
            temp_df_with_regime.copy(),
            strategy,
            leverage=leverage,
            trailing_stop_percent=ts_param
        )

        result_summary = { 'params': params, 'total_return': backtest_result['total_return'], 'num_trades': backtest_result['num_trades'] }
        results.append(result_summary)

    if not results:
        logging.error("\nNo valid combinations tested.")
        return None

    best_result = max(results, key=lambda x: x['total_return'])

    logging.info("\n--- Optimization Finished ---")
    logging.info("Best Parameters Found (including Trailing Stop):")
    logging.info(best_result['params'])
    logging.info(f"\nBest Performance over {days_to_backtest} days:")
    logging.info(f"  Total Return: {best_result['total_return']:.2f}%")
    logging.info(f"  Number of Trades: {best_result['num_trades']}")

    return best_result

if __name__ == '__main__':
    param_grid = {
        'ema_short_len': [13],
        'ema_long_len': [100],
        'vol_threshold': [2.0],
        'gap_threshold': [0.002],
        'trailing_stop_percent': [0.01, 0.02, 0.03, 0.05] # 1%, 2%, 3%, 5%
    }

    run_optimization(
        param_grid,
        symbol='DOGE-USDT-SWAP',
        leverage=20,
        days_to_backtest=365,
        exchange_name='okx'
    )
