import matplotlib.pyplot as plt
from data_fetcher import fetch_detailed_klines
from feature_engineering import calculate_fast_features, add_regime_features
from backtester import run_ai_futures_backtest
from ai_decision_module import AIStrategy # Import AIStrategy

def plot_results(df):
    """Plots the backtest results."""
    # ... (rest of the function is unchanged)
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax1 = plt.subplots(figsize=(16, 8))

    # Plot portfolio value
    ax1.plot(df.index, df['portfolio_value'], label='Portfolio Value', color='blue', linewidth=2)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Portfolio Value ($)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True)

    # Plot buy signals on the portfolio value line
    buy_signals = df[df['signal'] == 1]
    ax1.plot(buy_signals.index, buy_signals['portfolio_value'], '^', markersize=12, color='green', label='Long Entry', markeredgecolor='black')

    # Plot sell signals on the portfolio value line
    sell_signals = df[df['signal'] == -1]
    ax1.plot(sell_signals.index, sell_signals['portfolio_value'], 'v', markersize=12, color='red', label='Short Entry', markeredgecolor='black')

    # Create a second y-axis for the price
    ax2 = ax1.twinx()
    ax2.plot(df.index, df['k_close'], label='BTC Price', color='gray', alpha=0.6)
    ax2.set_ylabel('BTC Price ($)', color='gray')
    ax2.tick_params(axis='y', labelcolor='gray')

    fig.suptitle('AI Futures Backtest with Trend Regime Filter', fontsize=16)
    # Combine legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')

    plt.savefig('ai_backtest_regime_results.png')
    print(f"\nChart saved to ai_backtest_regime_results.png")

if __name__ == '__main__':
    # --- This block is for standalone testing of the visualizer ---
    SYMBOL = 'BTC/USDT:USDT'
    LEVERAGE = 20

    # Create a default strategy to run the backtest
    strategy = AIStrategy()

    # 1. Fetch Data
    ohlcv_data = fetch_detailed_klines(symbol=SYMBOL, limit=2000)

    # 2. Calculate Features
    features_df = calculate_fast_features(
        ohlcv_data.copy(),
        ema_short_len=strategy.ema_short_len,
        ema_long_len=strategy.ema_long_len
    )

    # 3. Add Regime Features
    final_df = add_regime_features(features_df, symbol=SYMBOL)

    # 4. Run Backtest
    backtest_results_dict = run_ai_futures_backtest(final_df.copy(), strategy, leverage=LEVERAGE)

    # 5. Plot Results
    if not backtest_results_dict['results_df'].empty:
        plot_results(backtest_results_dict['results_df'])
    else:
        print("Backtest did not produce results to plot.")
