import pickle

from model import OptionData, WeekData


def load_data(symbol):
    with open(f'data/{symbol}.pickle', 'rb') as f:
        return pickle.load(f)
