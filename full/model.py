
from datetime import date


def find_buy_price(start_date, option):
    option_history = option['history']
    contract = option['contract']
    if not option_history:
        return None
    if option_history[0].date < start_date:
        print(f'WARN: option history for {contract.ticker} starts on {option_history[0].date} - before {start_date}')
        return None
    if option_history[0].date == start_date:
        return option_history[0].close
    if (option_history[0].date - start_date).days <= 3:  # Sat & Sun
        return option_history[0].open
    return None


def create_transactions(data):
    stock_days = {w['day'].date: w['day'] for w in data['options_weekly']}
    tx = []
    missing_price = 0
    count = 0
    for w in data['options_weekly']:
        for p in w['options']:
            count += 1
            buy_date = w['day'].date
            sell_date = date.fromisoformat(p['contract'].expiration_date)
            if sell_date == buy_date or sell_date > data['to_date']:
                continue
            strike = p['contract'].strike_price
            buy_price = find_buy_price(buy_date, p)
            if not buy_price:
                missing_price += 1
                continue
            expiration_day = stock_days.get(sell_date)
            if not expiration_day:
                print(f'WARN: no stock data for {sell_date}')
                continue
            sell_price = max(0, expiration_day.close - strike - buy_price)
            profit_ratio = sell_price / buy_price - 1
            tx.append({
                'contract': p['contract'].ticker,
                'strike': strike,
                'buy_price': buy_price,
                'buy_date': buy_date,
                'sell_price': sell_price,
                'sell_date': sell_date,
                'weeks': round((sell_date - buy_date).days/7),
                'profit_ratio': profit_ratio,
                'stock_start_price': w['day'].close,
                'stock_end_price': expiration_day.close,
                'stock_change_ratio': expiration_day.close / w['day'].close - 1,
            })
    print(f'WARN: {missing_price}/{count} option contracts with missing price data')
    return tx