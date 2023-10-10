import sys
import math
import pickle

from model import OptionData, WeekData, History, load_history


def main():
    if len(sys.argv) < 3:
        print('arguments: <symbol> <strike-gap%>', file=sys.stderr)
        exit(1)

    symbol = sys.argv[1]
    strike_gap = float(sys.argv[2])/100

    history = load_history(symbol)
    print(history)
    weeks = len(history.week_data)
    stock_start_price = history.week_data[0].stock.prev.close
    option_profit = stock_profit = 0
    option_positive = 0
    for w in history.week_data:
        call = w.find_strike(w.stock.prev.close * (1+strike_gap))
        actual_strike_gap = call.strike_price / w.stock.prev.close - 1
        option_profit += call.profit_ratio
        if call.profit_ratio > 0:
            option_positive += 1
        stock_profit = w.stock.close / stock_start_price - 1
        print(f'{w.date}\t'
              f'{w.stock.close} ({w.stock.close/w.stock.prev.close-1:+.2%} {stock_profit:+.0%})\t'
              f'{call.strike_price} ({actual_strike_gap:+.2%} x{call.strike_price/call.history[0].close:.0f})\t'
              f'{call.profit_ratio:+.2%} ({option_profit:+.0%})')
    print(f'average profit {option_profit/weeks:.1%}\t'
          f'positive {option_positive/weeks:.1%}')


if __name__ == "__main__":
    main()
