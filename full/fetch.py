# Fetch all data for a given symbol from Polygon API and save it to a file

from datetime import date
from itertools import pairwise
import os
import pickle
from statistics import median
import sys
from polygon import RESTClient
from file import save

client = RESTClient()  # POLYGON_API_KEY environment variable is used

base_dir = os.path.dirname(os.path.realpath(__file__))


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


def list_stock_history(symbol, from_date, to_date):
    aggs = list(client.list_aggs(
        symbol,
        1, 'day',
        from_date, to_date,
        adjusted=False))
    for a in aggs:
        a.date = date.fromtimestamp(a.timestamp/1000)
    print(f'Fetched stock history for {len(aggs)} days')
    return aggs

def list_option_history(contract, start_day):
    aggs = list(client.list_aggs(
        contract.ticker,
        1, 'day',
        start_day.date, 
        contract.expiration_date,
        adjusted=False))
    for a in aggs:
        a.date = date.fromtimestamp(a.timestamp/1000)
    # if not aggs:
    #     print(
    #         f'{contract.ticker}: no history - no trades?')
    # elif aggs[0].date != start_day.date:
    #     print(
    #         f'{contract.ticker}: history starts on {aggs[0].date} after {start_day.date}')
    return aggs

def select_fridays(aggs):
    h = []
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
    print(f'Found {len(h)} weeks')
    return h


def list_call_contracts(symbol, start_day):
    contracts = client.list_options_contracts(
        symbol,
        contract_type='call',
        as_of=start_day.date,
        strike_price_gte=start_day.close,
        strike_price_lte=start_day.close * 1.1,
        sort='expiration_date',
        order='asc',
        limit=1000)
    result = []
    last = None
    for c in contracts:
        if not last or last.expiration_date != c.expiration_date:
            # c.expiration_date = date.fromisoformat(c.expiration_date)
            result.append(c)
            last = c
    return result        

def fetch_options(symbol, start_day):
    result = []
    contracts = list_call_contracts(symbol, start_day)
    if not contracts:
        print(f'{start_day.date}: no call contracts')
        return result
    for c in contracts:
        oh = list_option_history(c, start_day)
        result.append({
            'contract': c,
            'history': oh
        })
    hl = [len(c['history']) for c in result]
    minh = min(hl)
    maxh = max(hl)
    midh = round(median(hl))
    print(f'{start_day.date}: {len(result)} contracts, history length: min {minh}, median {midh}, max {maxh}')
    return result
        
def fetch_options_weekly(symbol, stock_history):
    fridays = select_fridays(stock_history)
    weeklies = []
    for i, d in enumerate(fridays):
      print(f'{i+1}/{len(fridays)}...')
      options = fetch_options(symbol, d)
      weeklies.append({
        'day': d,
        'options': options,
      })
    return weeklies

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

    stock_splits = list_stock_splits(symbol, from_date, to_date)
    stock_history = list_stock_history(symbol, from_date, to_date)
    weeklies = fetch_options_weekly(symbol, stock_history)

    stock_data = {
        'symbol': symbol,
        'from_date': from_date,
        'to_date': to_date,
        'ticker_details': ticker_details,
        'stock_splits': stock_splits,
        'stock_history': stock_history,
        'options_weekly': weeklies,
    }
    save(stock_data)


if __name__ == "__main__":
    main()
