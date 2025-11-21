from ai_decision_module import AIStrategy
from feature_engineering import calculate_fast_features, add_regime_features
from historical_data_downloader import download_historical_data
import pandas as pd

def run_ai_futures_backtest(df, strategy, initial_capital=10000, leverage=10, trailing_stop_percent=None):
    """Runs a futures backtest with an optional trailing stop loss."""
    capital = initial_capital
    position = None
    trades = 0
    winning_trades = 0
    pnl_history = []

    df['portfolio_value'] = float(initial_capital)
    df['signal'] = 0
    df['decision'] = df.apply(strategy.get_decision, axis=1)

    for i in range(1, len(df)):
        current_price = df['k_close'].iloc[i]
        decision = df['decision'].iloc[i]

        # --- Trailing Stop Logic ---
        if position and trailing_stop_percent:
            stop_triggered = False
            if position['type'] == 'long':
                new_ts_price = current_price * (1 - trailing_stop_percent)
                position['trailing_stop_price'] = max(position['trailing_stop_price'], new_ts_price)
                if current_price < position['trailing_stop_price']:
                    stop_triggered = True
            elif position['type'] == 'short':
                new_ts_price = current_price * (1 + trailing_stop_percent)
                position['trailing_stop_price'] = min(position['trailing_stop_price'], new_ts_price)
                if current_price > position['trailing_stop_price']:
                    stop_triggered = True

            if stop_triggered:
                pnl = (current_price - position['entry_price']) * position['size'] if position['type'] == 'long' else (position['entry_price'] - current_price) * position['size']
                if pnl > 0:
                    winning_trades += 1
                capital += pnl
                pnl_history.append(pnl)
                position = None
                trades += 1

        # --- Entry/Exit Logic based on AI Signal ---
        if position and (
            (position['type'] == 'long' and decision == 'SHORT') or
            (position['type'] == 'short' and decision == 'LONG')
        ):
            pnl = (current_price - position['entry_price']) * position['size'] if position['type'] == 'long' else (position['entry_price'] - current_price) * position['size']
            if pnl > 0:
                winning_trades += 1
            capital += pnl
            pnl_history.append(pnl)
            position = None
            trades += 1

        if not position:
            if decision == 'LONG':
                position_size = (capital * leverage) / current_price
                ts_price = current_price * (1 - trailing_stop_percent) if trailing_stop_percent else 0
                position = {'type': 'long', 'entry_price': current_price, 'size': position_size, 'trailing_stop_price': ts_price}
                df.loc[df.index[i], 'signal'] = 1
            elif decision == 'SHORT':
                position_size = (capital * leverage) / current_price
                ts_price = current_price * (1 + trailing_stop_percent) if trailing_stop_percent else float('inf')
                position = {'type': 'short', 'entry_price': current_price, 'size': position_size, 'trailing_stop_price': ts_price}
                df.loc[df.index[i], 'signal'] = -1

        portfolio_pnl = 0
        if position:
            portfolio_pnl = (current_price - position['entry_price']) * position['size'] if position['type'] == 'long' else (position['entry_price'] - current_price) * position['size']
        df.loc[df.index[i], 'portfolio_value'] = capital + portfolio_pnl

    if position:
        current_price = df['k_close'].iloc[-1]
        pnl = (current_price - position['entry_price']) * position['size'] if position['type'] == 'long' else (position['entry_price'] - current_price) * position['size']
        if pnl > 0:
            winning_trades += 1
        capital += pnl
        pnl_history.append(pnl)
        trades += 1

    final_capital = capital
    total_return = (final_capital - initial_capital) / initial_capital * 100
    win_rate = winning_trades / trades if trades > 0 else 0

    return {
        'total_return': total_return,
        'final_capital': final_capital,
        'num_trades': trades,
        'win_rate': win_rate,
        'results_df': df
    }

if __name__ == '__main__':
    SYMBOL = 'DOGE-USDT-SWAP'
    EXCHANGE = 'okx'
    DAYS = 30

    best_params = {'ema_short_len': 13, 'ema_long_len': 100}
    strategy = AIStrategy(ema_short_len=13, ema_long_len=100, vol_threshold=2.0, gap_threshold=0.002)

    data_file = download_historical_data(SYMBOL, days_to_fetch=DAYS, exchange_name=EXCHANGE)
    ohlcv_data = pd.read_csv(data_file, parse_dates=['k_open_time'], index_col='k_open_time')

    features_df = calculate_fast_features(ohlcv_data.copy(), **best_params)

    # Correctly construct the spot market symbol for regime features
    base_currency = SYMBOL.split('-')[0]
    quote_currency = SYMBOL.split('-')[1]
    regime_symbol = f"{base_currency}/{quote_currency}:{quote_currency}"
    final_df = add_regime_features(features_df, symbol=regime_symbol, exchange_name=EXCHANGE)

    backtest_results = run_ai_futures_backtest(final_df.copy(), strategy=strategy, leverage=20, trailing_stop_percent=0.02)

    print("\n--- Backtest Results with 2% Trailing Stop ---")
    print(f"Total Return: {backtest_results['total_return']:.2f}%")
    print(f"Win Rate: {backtest_results['win_rate']:.2%}")
    print(f"Number of Trades: {backtest_results['num_trades']}")
