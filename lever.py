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
    for w in history.week_data:
        l = ' '.join(f'{c.sell_price}' for c in w.call_options)
        # l = ' '.join(f'{c.leverage:.0f}' for c in w.call_options)
        print(f'{w.date} ({w.stock.close}) {l}')


if __name__ == "__main__":
    main()
