import ccxt

# 用CCXT写一个基于Bybit API的量化交易程序demo, 交易btc的

# Replace YOUR_API_KEY and YOUR_SECRET with your actual API key and secret
api_key = 'FtyBklKL3is4XWlZWS'
secret = '0QVMOut3yXx2R3MwdRLRzHAtQeKXwdFg2LJV'

# 建立Bybit交易所连接
exchange = ccxt.bybit({
    'test': True,  # 连接模拟账户
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
})

# 获取账户余额
def get_balance():
    balance = exchange.fetch_balance()
    return balance['BTC']['free']

# 在Bybit交易所下单买入BTC
def buy_btc(symbol, amount, price):
    # 限价单下单
    order = exchange.create_order(symbol=symbol, type='limit', side='buy', amount=amount, price=price)
    print(order)

if __name__ == '__main__':
    # 设置下单参数
    symbol = 'BTC/USDT'
    amount = 0.01  # 买入数量
    price = 55000  # 买入价格

    # 下单买入BTC
    buy_btc(symbol, amount, price)

    # 获取账户余额并打印
    balance = get_balance()
    print("账户余额：", balance)
