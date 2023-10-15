import pickle
import os
from itertools import pairwise
from datetime import date
from polygon.rest.models import TickerDetails, OptionsContract, Agg, Split


class OptionData:
    def __init__(self, contract: OptionsContract, history: list[Agg]):
        self.contract = contract
        self.history = history

    @property
    def strike_price(self):
        return self.contract.strike_price

    @property
    def buy_price(self):
        return self.history[0].close

    @property
    def sell_price(self):
        return self.history[-1].close

    @property
    def profit_ratio(self) -> float:
        return self.sell_price / self.buy_price - 1

    @property
    def leverage(self) -> float:
        return self.strike_price / self.buy_price

    def __str__(self):
        return f'{self.strike_price}\t{self.buy_price}\t{self.sell_price}\t({self.profit_ratio:+.0%})'


class WeekData:
    def __init__(self, stock: Agg, call_options: list[OptionData]):
        self.stock = stock
        self.call_options = call_options

    def print(self):
        print(self.stock.date, self.stock.close)
        for c in self.call_options:
            print(c)

    def __str__(self):
        return f'{self.stock.date} {self.stock.close} {len(self.call_options)} strikes'

    @property
    def date(self) -> date:
        return self.stock.date

    @property
    def min_strike_gap(self) -> float:
        return min(abs(a-b)/self.stock.prev.close
                   for a, b in pairwise(c.strike_price for c in self.call_options))

    @property
    def max_strike_gap(self) -> float:
        return max(abs(a-b)/self.stock.prev.close
                   for a, b in pairwise(self.stock.prev.close,
                                        *(c.strike_price for c in self.call_options)))

    def find_strike(self, strike: float):
        best = self.call_options[0]
        for c in self.call_options[1:]:
            if abs(c.strike_price-strike) < abs(best.strike_price-strike):
                best = c
        return best


class History:
    def __init__(self,
                 symbol: str,
                 strike_range: float,
                 week_data: list[WeekData],
                 ticker_details: TickerDetails,
                 splits: list[Split]):
        self.symbol = symbol
        self.strike_range = strike_range
        self.week_data = week_data
        self.ticker_details = ticker_details
        self.splits = splits

    def __str__(self):
        total_contracts = sum(len(w.call_options) for w in self.week_data)
        first_date = self.week_data[0].date
        last_date = self.week_data[-1].date
        return (f'{self.symbol} '
                f'({first_date}:{last_date}) '
                f'{len(self.week_data)} weeks '
                f'{total_contracts} contracts')
        # f'{len(self.splits)} splits')

    @property
    def min_strike_gap(self) -> float:
        return min(w.min_strike_gap for w in self.week_data)

    @property
    def max_strike_gap(self) -> float:
        return max(w.min_strike_gap for w in self.week_data)

    @property
    def all_calls(self):
        return (c for w in self.week_data for c in w.call_options)


def load_history(symbol) -> History:
    with open(f'data/{symbol}.pickle', 'rb') as f:
        return pickle.load(f)


def save_history(h: History):
    os.makedirs('data', exist_ok=True)
    with open(f'data/{h.symbol}.pickle', 'wb') as f:
        pickle.dump(h, f, protocol=pickle.HIGHEST_PROTOCOL)
