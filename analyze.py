import sys
import math
import pickle

from model import OptionData, WeekData, History, load_history


def find_closest_call(call_options, strike_target):
    best = call_options[0]
    for c in call_options[1:]:
        if abs(c.strike_price-strike_target) < abs(best.strike_price-strike_target):
            best = c
    return best


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
            call = find_closest_call(w.call_options,
                                     strike_target=w.stock.prev.close * strike_mul)
            profit += call.profit_ratio
            if call.profit_ratio > 0:
                positive += 1
        print(
            f'{strike_mul-1:+.2%}\taverage profit {profit/weeks:.1%}\tpositive {positive/weeks:.1%}')
        strike_mul += strike_step


if __name__ == "__main__":
    main()
