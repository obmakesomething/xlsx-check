from historical_data_downloader import download_historical_data
from feature_engineering import calculate_fast_features, add_regime_features
from ai_decision_module import AIStrategy
from backtester import run_ai_futures_backtest
from visualizer import plot_results
import pandas as pd
import logging

def generate_report(symbol, leverage, best_params, days_to_backtest, exchange_name='okx'):
    """
    Generates a final report using pre-downloaded historical data.
    """
    logging.info("--- Generating Final Report ---")

    # 1. Ensure data is available and load it
    data_file = download_historical_data(symbol, days_to_fetch=days_to_backtest, exchange_name=exchange_name)
    ohlcv_data = pd.read_csv(data_file, parse_dates=['k_open_time'], index_col='k_open_time')

    # 2. Create strategy with the best parameters
    strategy_params = {k: v for k, v in best_params.items() if k not in ['trailing_stop_percent']}
    ts_param = best_params.get('trailing_stop_percent')
    strategy = AIStrategy(**strategy_params)

    # 3. Calculate features
    logging.info("Calculating features for the final report...")
    features_df = calculate_fast_features(
        ohlcv_data.copy(),
        ema_short_len=strategy.ema_short_len,
        ema_long_len=strategy.ema_long_len
    )

    base_currency = symbol.split('-')[0]
    quote_currency = symbol.split('-')[1]
    regime_symbol = f"{base_currency}/{quote_currency}:{quote_currency}"
    final_df = add_regime_features(features_df, symbol=regime_symbol, exchange_name=exchange_name)

    # 4. Run final backtest
    logging.info("Running final backtest with optimized parameters...")
    final_backtest = run_ai_futures_backtest(final_df.copy(), strategy, leverage=leverage, trailing_stop_percent=ts_param)

    # 5. Print final performance summary
    print("\n--- Final Optimized Performance Summary ---")
    print(f"Period: {days_to_backtest} days")
    print(f"Leverage: {leverage}x")
    print("Best Parameters:", best_params)
    print(f"\nTotal Return: {final_backtest['total_return']:.2f}%")
    print(f"Final Capital: ${final_backtest['final_capital']:,.2f}")
    print(f"Number of Trades: {final_backtest['num_trades']}")
    print(f"Win Rate: {final_backtest.get('win_rate', 0):.2%}")

    # 6. Generate and save the final performance chart
    if not final_backtest['results_df'].empty:
        plot_results(final_backtest['results_df'])

if __name__ == '__main__':
    # Best parameters found from the 365-day optimization including trailing stop
    final_best_params = {
        'ema_short_len': 13,
        'ema_long_len': 100,
        'vol_threshold': 2.0,
        'gap_threshold': 0.002,
        'trailing_stop_percent': 0.05
    }

    generate_report(
        symbol='DOGE-USDT-SWAP',
        leverage=20,
        best_params=final_best_params,
        days_to_backtest=365,
        exchange_name='okx'
    )
