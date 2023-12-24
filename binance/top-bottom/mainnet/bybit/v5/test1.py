from pybit.unified_trading import HTTP

session = HTTP(
    testnet=False,
    api_key="GeS2xzvYScxnIjWEOU",
    api_secret="2JDubktuzxTvzkqE0AozIRcL5SByUrotzcCx",
)

def is_volume_spike(symbol):
    # 获取最近6小时的K线数据
    kline_data = session.get_kline(symbol=symbol,interval=60)
    if len(kline_data) > 0:
        # 计算最近6小时内平均成交量
        average_volume = sum(float(kline['volume']) for kline in kline_data) / len(kline_data)

        # 获取最新一次15分钟的K线数据
        current_kline = session.get_kline(symbol, '6h', limit=1)[-1]
        current_volume = float(current_kline['volume'])

        # 判断是否放量
        if current_volume >= 2 * average_volume:
            return True

    return False

if __name__ == "__main__":
    # print(session.get_orderbook(category="linear", symbol="BTCUSDT"))
    print(is_volume_spike("BTCUSDT"))
    # print(session.get_kline(
    #     symbol="BTCUSD",
    #     interval=60,
    # ))
