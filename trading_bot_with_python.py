from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from datetime import datetime
from alpaca_trade_api import REST
from datetime import timedelta

API_KEY = "PKMFICR0G6D1UZVYJL8A"
API_SECRET = "l9ffcyvegEeyBRJHiZLoZFDdfPBUaEdxcwA2xlqk"
BASE_URL = "https://paper-api.alpaca.markets"

ALPACA_CREDS ={
    "API_KEY": API_KEY,
    "API_SECRET": API_SECRET,
    "PAPER": True
}

class Orbit90Trader(Strategy):
    def initialize(self, symbol: str = "SPY", cash_at_risk: float = 0.5):
        self.symbol = symbol
        self.sleeptime = "24H"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)

    def position_sizing(self):
        try:
            cash = self.get_cash()
            last_price = self.get_last_price(self.symbol)
            quantity = round(cash * self.cash_at_risk / last_price)
            return cash, last_price, quantity
        except Exception as e:
            print(f"Error in position sizing: {e}")
            return None, None, None
    
    def get_dates(self):
        try:
            today = self.get_datetime()
            three_days_prior = today - timedelta(days=3)
            return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Error in getting dates: {e}")
            return None, None
    
    def get_news(self):
        try:
            today, three_days_prior = self.get_dates()
            if today is None or three_days_prior is None:
                return []
            news = self.api.get_news(symbol=self.symbol, start=three_days_prior, end=today)
            news = [ev.__dict__["_raw"]["headline"] for ev in news]
            return news
        except Exception as e:
            print(f"Error in getting news: {e}")
            return []

    def on_trading_iteration(self):
        try:
            cash, last_price, quantity = self.position_sizing()
            if cash is None or last_price is None or quantity is None:
                return

            if cash > last_price:
                if self.last_trade == None:
                    news = self.get_news()
                    print(news)
                    order = self.create_order(
                        self.symbol,
                        quantity,
                        "buy",
                        type="bracket",
                        take_profit_price=last_price * 1.20,
                        stop_loss_price=last_price * 0.95
                    )
                    self.submit_order(order)
                    self.last_trade = "buy"
        except Exception as e:
            print(f"Error in trading iteration: {e}")

start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 12, 31)
broker = Alpaca(ALPACA_CREDS)
strategy = Orbit90Trader(name='mlstrat', broker=broker, parameters={"symbol": "SPY", "cash_at_risk": 0.5})
strategy.backtest(YahooDataBacktesting, start_date, end_date, parameters={"symbol": "SPY", "cash_at_risk": 0.5})
