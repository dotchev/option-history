import os
import pickle


def save(data):
    os.makedirs('data', exist_ok=True)
    file_path = f'data/{data["symbol"]}.pickle'
    with open(file_path, 'wb') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f'Data saved in {file_path}')
    
def load(symbol):
    with open(f'data/{symbol}.pickle', 'rb') as f:
        return pickle.load(f)

def load_all():
  map = {}
  for file in os.listdir('data'):
      if not file.endswith('.pickle'):
          continue
      with open(os.path.join('data', file), 'rb') as f:
          data = pickle.load(f)
          map[data['symbol']] = data
  return map