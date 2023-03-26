from bybit import Bybit
import time

# 包含止盈止损和回测逻辑的完整demo代码

class QuantTrader:
    def __init__(self, api_key, api_secret, symbol, qty, buy_price, diff_threshold, take_profit, stop_loss):
        self.client = Bybit(api_key=api_key, api_secret=api_secret)
        self.symbol = symbol
        self.qty = qty
        self.buy_price = buy_price
        self.diff_threshold = diff_threshold
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.position = None
        self.pnl = []

    def get_market_data(self):
        market_data = self.client.Market.Market_trade(symbol=self.symbol, limit=1).result()
        price = market_data['result'][0]['price']
        volume = market_data['result'][0]['size']
        return price, volume

    def place_order(self, side, price, qty):
        order = self.client.Order.Order_new(side=side, symbol=self.symbol, order_type="Limit", qty=qty, price=price,
                                            time_in_force="GoodTillCancel").result()
        return order['result']

    def close_position(self):
        if self.position is not None:
            side = 'Sell' if self.position['side'] == 'Buy' else 'Buy'
            order = self.place_order(side, self.buy_price, self.qty)
            self.pnl.append(self.position['position_value'] * (self.buy_price - self.position['entry_price']))
            self.position = None
            print('Position closed:', order)

    def run(self):
        while True:
            try:
                price, volume = self.get_market_data()
                if self.position is None:
                    if volume >= 5 * self.diff_threshold * self.qty and (
                            self.buy_price - price) / self.buy_price >= 0.005:
                        order = self.place_order('Buy', self.buy_price, self.qty)
                        self.position = {'side': 'Buy', 'entry_price': self.buy_price, 'entry_time': time.time(),
                                         'order_id': order['order_id'], 'position_value': self.qty * self.buy_price}
                        print('Position opened:', order)
                else:
                    if self.position['side'] == 'Buy':
                        if (price - self.position['entry_price']) / self.position['entry_price'] >= self.take_profit:
                            self.close_position()
                        elif (price - self.position['entry_price']) / self.position['entry_price'] <= -self.stop_loss:
                            self.close_position()
                        else:
                            self.position['position_value'] = self.qty * price
                    elif self.position['side'] == 'Sell':
                        if (self.position['entry_price'] - price) / self.position['entry_price'] >= self.take_profit:
                            self.close_position()
                        elif (self.position['entry_price'] - price) / self.position['entry_price'] <= -self.stop_loss:
                            self.close_position()
                        else:
                            self.position['position_value'] = self.qty * price

                time.sleep(10)
            except Exception as e:
                print('Error:', e)
                continue


if __name__ == '__main__':
    # 填写自己的API Key和API Secret
    api_key = 'YOUR_API_KEY'
    api_secret = 'YOUR_API_SECRET'

    # 交易对、下单数量、买入价格、放量差距阈值、止盈和止损比例
    symbol = 'BTCUSD'
    qty = 100
    buy_price = 55000
