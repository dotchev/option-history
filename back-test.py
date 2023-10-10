import sys
import math
import pickle

from model import OptionData, WeekData, History, load_history


def main():
    if len(sys.argv) < 2:
        print('Stock symbol expected as argument', file=sys.stderr)
        exit(1)

    symbol = sys.argv[1]

    history = load_history(symbol)
    print(history)
    weeks = len(history.week_data)
    strike_step = history.min_strike_gap
    strike_mul = 1
    print(
        f'Testing from 1 to {history.strike_range:.2f} at step {strike_step:.4f}')
    while strike_mul <= history.strike_range:
        profit = 0
        positive = 0
        for w in history.week_data:
            call = w.find_strike(w.stock.prev.close * strike_mul)
            profit += call.profit_ratio
            if call.profit_ratio > 0:
                positive += 1
        print(
            f'{strike_mul-1:+.2%}\taverage profit {profit/weeks:.1%}\tpositive {positive/weeks:.1%}')
        strike_mul += strike_step


if __name__ == "__main__":
    main()
