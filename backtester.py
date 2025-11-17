from ai_decision_module import AIStrategy
from feature_engineering import calculate_fast_features, add_regime_features
from data_fetcher import fetch_detailed_klines
import pandas as pd

def run_ai_futures_backtest(df, strategy, initial_capital=10000, leverage=10):
    """Runs a futures backtest using a provided AIStrategy object."""
    capital = initial_capital
    position = None
    trades = 0
    pnl_history = []

    df['portfolio_value'] = float(initial_capital)
    df['signal'] = 0

    # Apply the strategy's decision logic to the entire dataframe at once (vectorized)
    df['decision'] = df.apply(strategy.get_decision, axis=1)

    for i in range(1, len(df)):
        current_price = df['k_close'].iloc[i]
        decision = df['decision'].iloc[i]

        # Close position logic
        if position and (
            (position['type'] == 'long' and decision == 'SHORT') or
            (position['type'] == 'short' and decision == 'LONG')
        ):
            pnl = (current_price - position['entry_price']) * position['size'] if position['type'] == 'long' else (position['entry_price'] - current_price) * position['size']
            capital += pnl
            pnl_history.append(pnl)
            position = None
            trades += 1

        # Open position logic
        if not position:
            if decision == 'LONG':
                position_size = (capital * leverage) / current_price
                position = {'type': 'long', 'entry_price': current_price, 'size': position_size}
                df.loc[df.index[i], 'signal'] = 1
            elif decision == 'SHORT':
                position_size = (capital * leverage) / current_price
                position = {'type': 'short', 'entry_price': current_price, 'size': position_size}
                df.loc[df.index[i], 'signal'] = -1

        # Update portfolio value
        if position:
            pnl = (current_price - position['entry_price']) * position['size'] if position['type'] == 'long' else (position['entry_price'] - current_price) * position['size']
            df.loc[df.index[i], 'portfolio_value'] = capital + pnl
        else:
            df.loc[df.index[i], 'portfolio_value'] = capital

    if position:
        current_price = df['k_close'].iloc[-1]
        pnl = (current_price - position['entry_price']) * position['size'] if position['type'] == 'long' else (position['entry_price'] - current_price) * position['size']
        capital += pnl
        pnl_history.append(pnl)
        trades += 1

    final_capital = capital
    total_return = (final_capital - initial_capital) / initial_capital * 100

    # Return results as a dictionary for the optimizer
    return {
        'total_return': total_return,
        'final_capital': final_capital,
        'num_trades': trades,
        'win_rate': (sum(1 for p in pnl_history if p > 0) / len(pnl_history)) if pnl_history else 0,
        'results_df': df
    }

if __name__ == '__main__':
    SYMBOL = 'BTC/USDT:USDT'
    default_strategy = AIStrategy()

    ohlcv_data = fetch_detailed_klines(symbol=SYMBOL, limit=1000)
    features_df = calculate_fast_features(
        ohlcv_data.copy(),
        ema_short_len=default_strategy.ema_short_len,
        ema_long_len=default_strategy.ema_long_len
    )
    final_df = add_regime_features(features_df, symbol=SYMBOL)

    backtest_results = run_ai_futures_backtest(final_df.copy(), strategy=default_strategy, leverage=20)

    print("--- Backtest Results ---")
    print(f"Total Return: {backtest_results['total_return']:.2f}%")
    print(f"Number of Trades: {backtest_results['num_trades']}")
    print(f"Win Rate: {backtest_results['win_rate']:.2%}")
