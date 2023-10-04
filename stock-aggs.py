import os
import pickle
import sys
from datetime import date
from itertools import pairwise
from statistics import quantiles

from polygon import RESTClient

client = RESTClient()  # POLYGON_API_KEY environment variable is used


class WeekData:
    def __init__(self, stock_data, call_options):
        self.stock_data = stock_data
        self.call_options = call_options


class OptionData:
    def __init__(self, contract, history):
        self.contract = contract
        self.history = history
        self.profit_ratio = history[1].close / history[0].close - 1


def fetch_stock_history(symbol, from_date, to_date):
    aggs = list(client.list_aggs(
        symbol,
        1, 'day',
        from_date, to_date,
        adjusted=False))
    for a in aggs:
        a.date = date.fromtimestamp(a.timestamp/1000)
    h = []
    for a, next_a in pairwise(aggs):
        if a.date.isoweekday() > next_a.date.isoweekday():
            h.append(a)
    Friday = 5
    last_a = aggs[-1]
    if last_a.date.isoweekday() == Friday:
        h.append(a)
    return h


def fetch_call_options(symbol, buy_date, stock_price, expiration_date, max_strike):
    call_contracts = client.list_options_contracts(
        symbol,
        contract_type='call',
        expiration_date=expiration_date,
        as_of=buy_date,
        strike_price_gte=stock_price,
        strike_price_lte=max_strike)
    call_options = []
    for contract in call_contracts:
        option_history = list(client.list_aggs(
            contract.ticker,
            1, 'week',
            buy_date, expiration_date,
            adjusted=False))
        if len(option_history) != 2:
            raise Exception(
                f'Unexpected option history for {contract.ticker}: {option_history}')
        call_options.append(
            OptionData(contract=contract, history=option_history))
    if len(call_options) == 0:
        raise Exception(
            f'No call contracts for {symbol} with expiration on {expiration_date}')
    return call_options


def save_data(symbol, data):
    os.makedirs('data', exist_ok=True)
    with open(f'data/{symbol}.pickle', 'wb') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


def main():
    if len(sys.argv) < 2:
        print('Stock symbol expected as argument', file=sys.stderr)
        exit(1)

    symbol = sys.argv[1]

    to_date = date.today()
    from_date = to_date.replace(year=to_date.year - 2)

    print(
        f'Fetching price history for {symbol} from {from_date} to {to_date}...')

    history = []
    stock_history = fetch_stock_history(symbol, from_date, to_date)
    stock_change_quantiles = quantiles(
        [n.close / p.close for p, n in pairwise(stock_history)],
        n=10)
    print('Stock weekly change quantiles:', stock_change_quantiles)
    strike_range = stock_change_quantiles[-1]
    for prev, next in pairwise(stock_history):
        call_options = fetch_call_options(
            symbol,
            buy_date=prev.date,
            stock_price=prev.close,
            expiration_date=next.date,
            max_strike=prev.close * strike_range)
        history.append(WeekData(next, call_options))
        print(f'{next.date} {next.close} {len(call_options)} strikes')
    print(f'{len(history)} weeks')
    save_data(symbol, history)


main()
