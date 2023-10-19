import sys
import math
import pickle
from statistics import quantiles
from itertools import pairwise
from model import OptionData, WeekData, History, load_history


def main():
    if len(sys.argv) < 2:
        print('Stock symbol expected as argument', file=sys.stderr)
        exit(1)

    symbol = sys.argv[1]

    history = load_history(symbol)
    print(history)

    stock_change_quantiles = quantiles(
        [w.stock.close / w.stock.prev.close - 1 for w in history.week_data],
        n=10)
    print('Stock weekly change quantiles:', ', '.join([
          f'{q:+.02%}' for q in stock_change_quantiles]))
    strike_range = stock_change_quantiles[-1]

    weeks = len(history.week_data)
    strike_step = history.min_strike_gap
    strike_gap = 0
    print(
        f'Testing strike gap from 0 to {strike_range:+.2%} at step {strike_step:.2%}')
    while strike_gap <= strike_range:
        profit = 0
        positive = 0
        for w in history.week_data:
            call = w.find_strike(w.stock.prev.close * (1+strike_gap))
            profit += call.profit_ratio
            if call.profit_ratio > 0:
                positive += 1
        print(
            f'{strike_gap:+.2%}\t'
            f'average profit {profit/weeks:.1%}\t'
            f'positive {positive/weeks:.1%}\t'
            f'{(profit/weeks)*(positive/weeks)*10000:.0f}')
        strike_gap += strike_step


if __name__ == "__main__":
    main()
