from datetime import date
import sys
from itertools import pairwise

from model import History, OptionData, WeekData, load_history


def main():
    if len(sys.argv) < 3:
        print('arguments: <symbol> <date>', file=sys.stderr)
        exit(1)

    symbol = sys.argv[1]
    d = date.fromisoformat(sys.argv[2])

    history = load_history(symbol)
    print(history)
    w = next((w for w in history.week_data if w.date == d), None)
    if not w:
        print(d, 'not found')
        exit(1)
    print(w.stock.prev.date, w.stock.prev.close)
    print(w.date, w.stock.close)
    for c in w.call_options:
        print(
            f'strike={c.strike_price}\t'
            f'call-buy={c.buy_price} (x{c.leverage:.0f})\t'
            f'cal-sell={c.sell_price} ({c.profit_ratio:+.0%})'
        )


if __name__ == "__main__":
    main()
