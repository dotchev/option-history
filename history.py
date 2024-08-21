import os
import pickle
import sys
import pandas as pd
from datetime import date
from itertools import pairwise
from statistics import quantiles, mean, median
from time import sleep

from polygon import RESTClient
from polygon.rest.models import Agg

from model import OptionData, WeekData, History, save_history


client = RESTClient()  # POLYGON_API_KEY environment variable is used


def list_stock_history(symbol, from_date, to_date):
    '''Returns a list with the last trading day of each week (usually Friday)'''
    aggs = list(client.list_aggs(
        symbol,
        1, 'day',
        from_date, to_date,
        adjusted=False))
    for a in aggs:
        a.date = date.fromtimestamp(a.timestamp/1000)
    h = list[Agg]()
    for a, next_a in pairwise(aggs):
        if a.date >= next_a.date:
            raise Exception(
                f'bad stock history order: {a.date} >= {next_a.date}')
        if a.date.isoweekday() > next_a.date.isoweekday():
            h.append(a)
    Friday = 5
    last_a = aggs[-1]
    if last_a.date.isoweekday() == Friday:
        h.append(last_a)
    print(f'Fetched {len(aggs)} days - {len(h)} weeks')
    return h


def check_option_consistency(contract, option_history, start_day, end_day):
    for p, n in pairwise(option_history):
        if p.date >= n.date:
            raise Exception(
                f'bad history order for contract {contract.ticker}: {p.date} >= {n.date}')
    if len(option_history) < 1:
        print(
            f'{contract.ticker}: history too short: {len(option_history)} - no trades?')
        return False
    option_start = option_history[0]
    option_end = option_history[-1]
    if option_start.date < start_day.date:
        raise Exception(
            f'{contract.ticker}: history starts on {option_end.date} before {end_day.date}')
    if option_start.date != start_day.date:
        print(
            f'{contract.ticker}: history starts on {option_start.date} after {start_day.date}')
        if (option_start.date - start_day.date).days > 3:
            print('too late - ignoring')
            return False
    if option_end.date > end_day.date:
        raise Exception(
            f'{contract.ticker}: history ends on {option_end.date} after {end_day.date}')
    # if option_end.date != end_day.date:
    #     print(
    #         f'{contract.ticker}: history ends on {option_end.date} '
    #         f'expected {end_day.date}')
    #     return False
    # stock_delta = max(0, end_day.close - contract.strike_price)
    # if abs(stock_delta - option_end.close) > 0.20 and (stock_delta == 0 or abs(option_end.close / stock_delta - 1) > 0.20):
    #     print(
    #         f'{contract.ticker}: stock close price {end_day.close}, '
    #         f'strike price {contract.strike_price} ({end_day.close - contract.strike_price:+.2f}), '
    #         f'but option close at {option_end.close}!')
    return True


def fetch_call_option(symbol: str, start_day: Agg, end_day: Agg):
    call_contracts = list(client.list_options_contracts(
        symbol,
        contract_type='call',
        expiration_date=end_day.date,
        as_of=start_day.date,
        strike_price_gte=start_day.close,
        sort='strike_price',
        order='asc',
        limit=1000))
    if len(call_contracts) == 0:
        # print(f'No call contracts for {symbol} that expire on {end_day.date} as of {start_day.date}')
        return None

    for p, n in pairwise(call_contracts):
        if p.strike_price >= n.strike_price:
            raise Exception(
                f'bad contract order: strike price {p.strike_price} >= {n.strike_price}')

    # pick the first strike price above the current price
    contract = call_contracts[0]

    option_history = list(client.list_aggs(
        contract.ticker,
        1, 'day',
        start_day.date, end_day.date,
        adjusted=False))
    for a in option_history:
        a.date = date.fromtimestamp(a.timestamp/1000)
    if not check_option_consistency(contract, option_history, start_day, end_day):
        return None
    return OptionData(contract, option_history, start_day, end_day)


def list_stock_splits(symbol, from_date, to_date):
    splits = list(client.list_splits(symbol,
                                     execution_date_gte=from_date,
                                     execution_date_lte=to_date))
    if len(splits) == 0:
        print('No stock splits in this period')
    else:
        print(f'WARNING: {len(splits)} stock splits in this period:')
        print(splits, sep='\n')
    return splits


def fix_splits(stock_splits, start_day: Agg, end_day: Agg):
    for split in stock_splits:
        split_date = date.fromisoformat(split.execution_date)
        if start_day.date < split_date <= end_day.date:
            q = split.split_to / split.split_from
            d = Agg(
                open=end_day.open * q,
                high=end_day.high * q,
                low=end_day.low * q,
                close=end_day.close * q,
            )
            d.date = end_day.date
            end_day = d
    return end_day


def main():
    if len(sys.argv) < 2:
        print('Stock symbol expected as argument', file=sys.stderr)
        exit(1)

    symbol = sys.argv[1]
    ticker_details = client.get_ticker_details(symbol)
    print(f'{symbol} - {ticker_details.name} ({ticker_details.locale}, {ticker_details.type})')

    to_date = date.today()
    # free plan provides only 2y of history
    from_date = to_date.replace(year=to_date.year - 2)
    # from_date = date.fromisoformat('2021-01-01')

    print(
        f'Fetching price history for {symbol} from {from_date} to {to_date}...')
    stock_splits = list_stock_splits(symbol, from_date, to_date)
    stock_history = list_stock_history(symbol, from_date, to_date)

    for span_weeks in range(1, 27):  # 1 - 26
        # span_weeks = 3  # option expiration period in weeks
        print(
            f'\nFetching {symbol} call options with {span_weeks}w expiration')
        results = []
        for i in range(0, len(stock_history) - span_weeks):
            start_day = stock_history[i]
            end_day = stock_history[i + span_weeks]
            end_day = fix_splits(stock_splits, start_day, end_day)
            call_option = fetch_call_option(symbol, start_day, end_day)
            if call_option is None:
                continue
            # print(f'from: {start_day.date} {symbol}@${start_day.close} strike@${call_option.strike_price} call@${call_option.buy_price} leverage:x{call_option.leverage:.1f}')
            # print(f'  to: {end_day.date} {symbol}@${end_day.close} {end_day.close-start_day.close:+.2f} ({end_day.close/start_day.close-1:+.2%}) call@${call_option.sell_price} ({call_option.profit_ratio:+.1%})')
            results.append({
                'start_date': start_day.date,
                'end_date': end_day.date,
                'stock_start_price': start_day.close,
                'stock_end_price': end_day.close,
                'call_expiration_date': call_option.expiration_date,
                'call_strike_price': call_option.strike_price,
                'call_start_price': call_option.buy_price,
                'call_end_price': call_option.sell_price,
                'call_max_price': call_option.max_price,
                'call_daily_tx': call_option.daily_tx,
                'call_history_length': len(call_option.history),
            })
            # sleep(24)  # do not breach free rate limit of 5r/m

        if len(results) == 0:
            print('No transactions!')
            os.remove(f'data/{symbol}/{span_weeks}w.csv')
            continue

        df = pd.DataFrame(results)
        os.makedirs(f'data/{symbol}', exist_ok=True)
        df.to_csv(f'data/{symbol}/{span_weeks}w.csv', index=False)

        stock_median_change = (df.stock_end_price /
                               df.stock_start_price - 1).median()
        call_profits = df.call_end_price / df.call_start_price - 1
        mean_call_profit = call_profits.mean()
        positive_ratio = (call_profits > 0).mean()
        call_daily_tx = df.call_daily_tx.median()
        print(f'{len(df)} transactions')
        print(f'stock median change: {stock_median_change:+.1%}')
        print(f'Call profit - average: {mean_call_profit:+.1%} '
              f'positive: {positive_ratio:.1%} '
              f'daily tx: {call_daily_tx:.0f}')


if __name__ == "__main__":
    main()
