import sys
from itertools import pairwise

from model import History, OptionData, WeekData, load_history


def main():
    if len(sys.argv) < 2:
        print('arguments: <symbol>', file=sys.stderr)
        exit(1)

    symbol = sys.argv[1]

    history = load_history(symbol)
    print(history)
    for w in history.week_data:
        print(
            f'{w.date}\t',
            # * (f'{n.leverage:.0f}' for n in w.call_options)
            * (f'{n.leverage / p.leverage:.2f}' for
               p, n in pairwise(w.call_options))
        )


if __name__ == "__main__":
    main()
