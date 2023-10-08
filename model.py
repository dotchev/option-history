import pickle
import os


class WeekData:
    def __init__(self, stock, call_options):
        self.stock = stock
        self.call_options = call_options

    def print(self):
        print(self.stock.date, self.stock.close)
        for c in self.call_options:
            print(c)

    def __str__(self):
        return str(self.stock.date)


class OptionData:
    def __init__(self, contract, history):
        self.contract = contract
        self.history = history

    @property
    def profit_ratio(self):
        return self.history[1].close / self.history[0].close - 1

    def __str__(self):
        return f'{self.contract.strike_price}\t{self.history[0].close}\t{self.history[1].close}\t({self.profit_ratio:.2f})'


def load_data(symbol):
    with open(f'data/{symbol}.pickle', 'rb') as f:
        return pickle.load(f)


def save_data(symbol, data):
    os.makedirs('data', exist_ok=True)
    with open(f'data/{symbol}.pickle', 'wb') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
