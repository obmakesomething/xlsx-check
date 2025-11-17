from data_fetcher import fetch_detailed_klines
from feature_engineering import calculate_fast_features, add_regime_features
from ai_decision_module import AIStrategy
from backtester import run_ai_futures_backtest
import itertools
import pandas as pd

def run_optimization(param_grid, symbol, leverage, data_limit=2000):
    """
    Runs a grid search optimization for the AI strategy.
    """
    print("--- Starting Optimization ---")
    print(f"Symbol: {symbol}, Leverage: {leverage}")

    # 1. Fetch and process data once to save time
    print("\nStep 1: Fetching and processing base data...")
    ohlcv_data = fetch_detailed_klines(symbol=symbol, limit=data_limit)
    # We need to calculate features for the superset of all required lengths
    max_ema_long = max(param_grid['ema_long_len'])
    # Ensure other params are maxed out for the initial feature calculation if they affect length
    base_features_df = calculate_fast_features(ohlcv_data.copy(), ema_long_len=max_ema_long)
    final_base_df = add_regime_features(base_features_df, symbol=symbol)

    print(f"\nStep 2: Testing {len(list(itertools.product(*param_grid.values())))} parameter combinations...")

    results = []

    # Create all combinations of parameters
    keys, values = zip(*param_grid.items())
    param_combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

    for i, params in enumerate(param_combinations):
        if params['ema_short_len'] >= params['ema_long_len']:
            continue # Skip invalid combinations

        print(f"  Testing combo {i+1}/{len(param_combinations)}: {params}")

        # Create a strategy with the current parameter combination
        strategy = AIStrategy(**params)

        # We need to recalculate features that depend on the specific params
        # This is a trade-off: recalculating is slower but more accurate
        temp_df = calculate_fast_features(
            ohlcv_data.copy(),
            ema_short_len=params['ema_short_len'],
            ema_long_len=params['ema_long_len']
        )
        # We can reuse the regime features as they don't depend on these params
        temp_df_with_regime = pd.merge_asof(temp_df.sort_index(), final_base_df[['trend_regime']].sort_index(),
                                            left_index=True, right_index=True, direction='backward').dropna()

        # Run the backtest
        backtest_result = run_ai_futures_backtest(temp_df_with_regime.copy(), strategy, leverage=leverage)

        result_summary = {
            'params': params,
            'total_return': backtest_result['total_return'],
            'num_trades': backtest_result['num_trades'],
            'win_rate': backtest_result['win_rate'],
        }
        results.append(result_summary)

    if not results:
        print("\nNo valid parameter combinations were tested.")
        return None

    # Find the best result based on total return
    best_result = max(results, key=lambda x: x['total_return'])

    print("\n--- Optimization Finished ---")
    print("Best Parameters Found:")
    print(best_result['params'])
    print(f"\nBest Performance:")
    print(f"  Total Return: {best_result['total_return']:.2f}%")
    print(f"  Number of Trades: {best_result['num_trades']}")
    print(f"  Win Rate: {best_result['win_rate']:.2%}")

    return best_result

if __name__ == '__main__':
    # Define the parameter grid to search
    param_grid = {
        'ema_short_len': [5, 7, 9],
        'ema_long_len': [20, 30, 40],
        'vol_threshold': [1.2, 1.5],
        'gap_threshold': [0.0005, 0.001]
    }

    # Run optimization for DOGE coin
    run_optimization(param_grid, symbol='DOGE/USDT:USDT', leverage=20)
