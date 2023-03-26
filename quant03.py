import time
import logging
import ccxt
import numpy as np

logging.basicConfig(level=logging.INFO)


class QuantStrategy:
    def __init__(self, symbol, qty, buy_price, volume_threshold, take_profit_ratio, stop_loss_ratio):
        self.exchange = ccxt.bybit({
            'apiKey': 'YOUR_API_KEY',
            'secret': 'YOUR_SECRET_KEY',
            'enableRateLimit': True,
        })
        self.symbol = symbol
        self.qty = qty
        self.buy_price = buy_price
        self.volume_threshold = volume_threshold
        self.take_profit_ratio = take_profit_ratio
        self.stop_loss_ratio = stop_loss_ratio
        self.position = None
        self.pnl = []

    def close_position(self):
        if self.position:
            close_price = self.exchange.fetch_ticker(self.symbol)['last']
            order = self.exchange.create_order(
                symbol=self.symbol,
                type='market',
                side='sell' if self.position['side'] == 'Buy' else 'buy',
                amount=self.qty,
            )
            self.pnl.append(self.position['position_value'] * (close_price - self.position['entry_price']))
            self.position = None
            logging.info(f'Close position: {order}, PnL: {self.pnl[-1]:.2f}')

    def check_signal(self):
        kline = self.exchange.fetch_ohlcv(self.symbol, timeframe='1h', limit=1)
        current_vol = kline[0][5]
        current_price = kline[0][4]
        current_change = (current_price - self.buy_price) / self.buy_price
        if current_vol > self.volume_threshold:
            if self.position is None:
                self.position = {
                    'side': 'Buy',
                    'entry_price': current_price,
                    'entry_time': time.time(),
                    'order_id': None,
                    'position_value': self.qty * current_price,
                }
                order = self.exchange.create_order(
                    symbol=self.symbol,
                    type='limit',
                    side='buy',
                    amount=self.qty,
                    price=current_price,
                )
                self.position['order_id'] = order['id']
                logging.info(f'Open position: {order}')
        else:
            if self.position and current_change >= self.take_profit_ratio:
                self.close_position()
            elif self.position and current_change <= -self.stop_loss_ratio:
                self.close_position()

    def run_strategy(self):
        while True:
            try:
                self.check_signal()
            except Exception as e:
                logging.error(e)
            time.sleep(60)


if __name__ == '__main__':
    symbol = 'BTC/USDT'
    qty = 0.01
    buy_price = 55000
    volume_threshold = 300
    take_profit_ratio = 0.1
    stop_loss_ratio = 0.05
    strategy = QuantStrategy(symbol, qty, buy_price, volume_threshold, take_profit_ratio, stop_loss_ratio)
    strategy.run_strategy()
