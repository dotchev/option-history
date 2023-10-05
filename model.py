class WeekData:
    def __init__(self, stock_data, call_options):
        self.stock_data = stock_data
        self.call_options = call_options

    def print(self):
        print(self.stock_data.date, self.stock_data.close)
        for c in self.call_options:
            print(c)


class OptionData:
    def __init__(self, contract, history):
        self.contract = contract
        self.history = history

    @property
    def profit_ratio(self):
        return self.history[1].close / self.history[0].close - 1

    def __str__(self):
        return f'{self.contract.strike_price}\t{self.history[0].close}\t{self.history[1].close}\t({self.profit_ratio:.2f})'
