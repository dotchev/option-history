import os
import pickle
import sys
from datetime import date
from itertools import pairwise
from statistics import quantiles

from polygon import RESTClient
from polygon.rest.models import Agg

from model import OptionData, WeekData, History, save_history


client = RESTClient()  # POLYGON_API_KEY environment variable is used


def list_stock_history(symbol, from_date, to_date):
    aggs = list(client.list_aggs(
        symbol,
        1, 'day',
        from_date, to_date,
        adjusted=False))
    for a in aggs:
        a.date = date.fromtimestamp(a.timestamp/1000)
    h = list[Agg]
    for a, next_a in pairwise(aggs):
        if a.date.isoweekday() > next_a.date.isoweekday():
            h.append(a)
    Friday = 5
    last_a = aggs[-1]
    if last_a.date.isoweekday() == Friday:
        h.append(last_a)
    return h


def check_option_consistency(contract, option_history, prev_week, next_week):
    if len(option_history) < 2:
        print(
            f'{contract.ticker}: history too short: {len(option_history)} - skip contract')
        return False
    option_start = option_history[0]
    option_end = option_history[-1]
    if option_start.date != prev_week.date:
        print(
            f'{contract.ticker}: history starts on {option_start.date} expected {prev_week.date} - skip contract')
        return False
    if option_end.date != next_week.date:
        print(
            f'{contract.ticker}: history ends on {option_end.date} expected {next_week.date} - skip contract')
        return False
    stock_delta = max(0, next_week.close - contract.strike_price)
    if abs(stock_delta - option_end.close) > 2 and \
            (stock_delta == 0 or abs(option_end.close / stock_delta - 1) > 0.20):
        print(
            f'{contract.ticker}: stock close price {next_week.close}, '
            f'strike price {contract.strike_price} ({next_week.close - contract.strike_price:+.2f}), '
            f'but option close at {option_end.close}!')
    return True


def list_call_options(symbol, prev_week, next_week, max_strike):
    call_contracts = client.list_options_contracts(
        symbol,
        contract_type='call',
        expiration_date=next_week.date,
        as_of=prev_week.date,
        strike_price_gte=prev_week.close,
        strike_price_lte=max_strike)
    call_options = []
    for contract in call_contracts:
        option_history = list(client.list_aggs(
            contract.ticker,
            1, 'day',
            prev_week.date, next_week.date,
            adjusted=False))
        for a in option_history:
            a.date = date.fromtimestamp(a.timestamp/1000)
        if check_option_consistency(contract, option_history, prev_week, next_week):
            call_options.append(OptionData(contract, option_history))
    return call_options


def list_stock_splits(symbol, from_date, to_date):
    splits = list(client.list_splits(symbol,
                                     execution_date_gte=from_date,
                                     execution_date_lte=to_date))
    if len(splits) == 0:
        print('No stock splits in this period')
    else:
        print(f'{len(splits)} stock splits in this period:')
        print(splits, sep='\n')
    return splits


def stock_split(stock_splits, prev_week, next_week):
    for split in stock_splits:
        split_date = date.fromisoformat(split.execution_date)
        if prev_week.date <= split_date <= next_week.date:
            return split
    return None


def main():
    if len(sys.argv) < 2:
        print('Stock symbol expected as argument', file=sys.stderr)
        exit(1)

    symbol = sys.argv[1]
    ticker_details = client.get_ticker_details(symbol)
    print(f'{symbol} - {ticker_details.name} ({ticker_details.locale}, {ticker_details.type})')

    to_date = date.today()
    from_date = to_date.replace(year=to_date.year - 2)

    print(
        f'Fetching price history for {symbol} from {from_date} to {to_date}...')
    splits = list_stock_splits(symbol, from_date, to_date)

    history = []
    stock_history = list_stock_history(symbol, from_date, to_date)
    stock_change_quantiles = quantiles(
        [n.close / p.close for p, n in pairwise(stock_history)],
        n=10)
    print('Stock weekly gain quantiles:', ', '.join([
          f'{q:.02f}' for q in stock_change_quantiles]))
    strike_range = stock_change_quantiles[-1]
    for prev, next in pairwise(stock_history):
        split = stock_split(splits, prev, next)
        if split:
            print(
                f'Stock split on {split.execution_date}, skipping {next.date}')
            continue
        call_options = list_call_options(
            symbol,
            prev_week=prev,
            next_week=next,
            max_strike=prev.close * strike_range)
        if len(call_options) == 0:
            print(
                f'No call contracts for {symbol} that expire on {next.date}')
            continue
        next.prev = prev
        w = WeekData(next, call_options)
        print(w)
        history.append(w)
    h = History(symbol, strike_range, history, ticker_details)
    save_history(h)
    print(h)


if __name__ == "__main__":
    main()
