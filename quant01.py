from bybit import Bybit
import time

# 完整demo代码

class QuantTrader:
    def __init__(self, api_key, api_secret, symbol, qty, buy_price, diff_threshold):
        self.client = Bybit(api_key=api_key, api_secret=api_secret)
        self.symbol = symbol
        self.qty = qty
        self.buy_price = buy_price
        self.diff_threshold = diff_threshold

    def get_market_data(self):
        market_data = self.client.Market.Market_trade(symbol=self.symbol, limit=1).result()
        price = market_data['result'][0]['price']
        volume = market_data['result'][0]['size']
        return price, volume

    def place_order(self, side, price, qty):
        order = self.client.Order.Order_new(side=side, symbol=self.symbol, order_type="Limit", qty=qty, price=price,
                                            time_in_force="GoodTillCancel").result()
        return order['result']

    def run(self):
        while True:
            try:
                price, volume = self.get_market_data()
                if volume >= 5 * self.diff_threshold * self.qty and (self.buy_price - price) / self.buy_price >= 0.005:
                    order = self.place_order('Buy', self.buy_price, self.qty)
                    print('Order placed:', order)

                time.sleep(10)
            except Exception as e:
                print('Error:', e)
                continue


if __name__ == '__main__':
    # 填写自己的API Key和API Secret
    api_key = 'FtyBklKL3is4XWlZWS'
    api_secret = '0QVMOut3yXx2R3MwdRLRzHAtQeKXwdFg2LJV'

    # 交易对、下单数量、买入价格和放量差距阈值
    symbol = 'BTCUSD'
    qty = 100
    buy_price = 55000
    diff_threshold = 0.01

    trader = QuantTrader(api_key, api_secret, symbol, qty, buy_price, diff_threshold)
    trader.run()
