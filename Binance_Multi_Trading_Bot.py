from binance.client import Client
from datetime import datetime, timedelta
import pandas as pd
import time

API_KEY = "GJmyg3ignVucrmtLGjUMRXi08XNt4piE46PU55gLlBeBhzl6qBjOhR5Io2nxJQs4"
API_SECRET = "Pn5JqSGx0E7hsWtTLivQ62DPpcEDpdzSZUXCXFXbmcn8YuL3ApClUaQ1mlcUl4bl"

client = Client(API_KEY, API_SECRET, testnet=True)

def get_bars(asset='BTC'):
    bars = client.get_historical_klines(f"{asset}USDT", Client.KLINE_INTERVAL_1MINUTE, start_str="1 hour ago UTC")
    df = pd.DataFrame(bars, columns=["Open time", "Open", "High", "Low", "Close", "Volume", "Close time", "Quote asset volume", "Number of trades", "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"])
    df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')
    df.set_index('Open time', inplace=True)
    df = df.iloc[:, :4]
    for col in df.columns:
        df[col] = pd.to_numeric(df[col])
    return df

def get_macd(data, slow=12, fast=26, signal=9):
    macd = data["Close"].ewm(span=fast).mean() - data["Close"].ewm(span=slow).mean()
    signal_line = macd.ewm(span=signal).mean()
    return macd, signal_line

assets = [
    {'asset': 'BTC', 'is_long': False, 'order_size': 0.0025},
    {'asset': 'LTC', 'is_long': False, 'order_size': 100},
    {'asset': 'ETH', 'is_long': False, 'order_size': 0.03}
]

while True:
    for index, asset in enumerate(assets):
        asset, is_long, order_size = asset['asset'], asset['is_long'], asset['order_size']
        bars = get_bars(asset=asset)
        macd, signal_line = get_macd(bars)
        should_buy = macd[-1] > signal_line[-1] and bars['Close'].pct_change(30)[-1] > 0
        should_sell = macd[-1] < signal_line[-1] and bars['Close'].pct_change(30)[-1] < 0
        
        print(f"Asset: {asset} / Is Long: {is_long} / Should Buy: {should_buy}, / Should Sell: {should_sell}")

        if is_long == False and should_buy == True:
            print(f'We are buying {order_size} {asset}')
            order = client.order_market_buy(symbol=f'{asset}USDT', quantity=order_size)
            assets[index]['is_long'] = True

        elif is_long == True and should_sell == True:
            print(f'We are selling {order_size} {asset}')
            order = client.order_market_sell(symbol=f'{asset}USDT', quantity=order_size)
            assets[index]['is_long'] = False
            
    print('Iteration ended')
    print(assets)
    print("*" * 20)
    time.sleep(10)
