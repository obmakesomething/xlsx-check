from data_fetcher import fetch_detailed_klines
from feature_engineering import calculate_fast_features, add_regime_features
from ai_decision_module import AIStrategy
from backtester import run_ai_futures_backtest
from visualizer import plot_results
import pandas as pd

def generate_report(symbol, leverage, best_params, data_limit=2000):
    """
    Generates a final report with the performance of the best parameters.
    """
    print("--- Generating Final Report ---")
    print(f"Symbol: {symbol}, Leverage: {leverage}")
    print("Applying optimized parameters...")
    print(best_params)

    # 1. Create strategy with the best parameters
    strategy = AIStrategy(**best_params)

    # 2. Fetch data and calculate features
    ohlcv_data = fetch_detailed_klines(symbol=symbol, limit=data_limit)
    features_df = calculate_fast_features(
        ohlcv_data.copy(),
        ema_short_len=strategy.ema_short_len,
        ema_long_len=strategy.ema_long_len
    )
    final_df = add_regime_features(features_df, symbol=symbol)

    # 3. Run final backtest
    final_backtest = run_ai_futures_backtest(final_df.copy(), strategy, leverage=leverage)

    # 4. Print final performance summary
    print("\n--- Optimized Performance Summary ---")
    print(f"Total Return: {final_backtest['total_return']:.2f}%")
    print(f"Final Capital: ${final_backtest['final_capital']:,.2f}")
    print(f"Number of Trades: {final_backtest['num_trades']}")
    print(f"Win Rate: {final_backtest['win_rate']:.2%}")

    # 5. Generate and save the final performance chart
    if not final_backtest['results_df'].empty:
        plot_results(final_backtest['results_df'])

if __name__ == '__main__':
    # These are the best parameters we found in the optimization step
    best_doge_params = {
        'ema_short_len': 5,
        'ema_long_len': 20,
        'vol_threshold': 1.2,
        'gap_threshold': 0.0005
    }

    generate_report(
        symbol='DOGE/USDT:USDT',
        leverage=20,
        best_params=best_doge_params
    )
