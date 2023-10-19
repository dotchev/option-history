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
    weeks = len(history.week_data)

    lever = min(c.leverage for c in history.all_calls)

    lever_quantiles = quantiles(
        (c.leverage for c in history.all_calls),
        n=10)
    max_lever = lever_quantiles[-1]

    lever_step_quantiles = quantiles(
        (n.leverage/p.leverage
         for w in history.week_data if len(w.call_options) > 1
         for p, n in pairwise(w.call_options)),
        n=10)
    lever_step = lever_step_quantiles[0]

    print(
        f'Testing call leverage from {lever:.0f} to {max_lever:.0f} '
        f'at step x{lever_step:.2f}')
    while lever <= max_lever:
        profit = 0
        positive = 0
        for w in history.week_data:
            call = w.find_lever(lever)
            profit += call.profit_ratio
            if call.profit_ratio > 0:
                positive += 1
        # if profit > 0 and positive/weeks > 0.1:
        print(
            f'{lever:.2f}\t'
            f'average profit {profit/weeks:.1%}\t'
            f'positive {positive/weeks:.1%}\t'
            f'{(profit/weeks)*(positive/weeks)*10000:.0f}')
        lever *= lever_step


if __name__ == "__main__":
    main()
