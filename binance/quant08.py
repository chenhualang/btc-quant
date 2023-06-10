import ccxt

# 币安模拟账户交易，基于ccxt API，实现买入BTC
# 本程序用于演示如何使用ccxt API连接币安模拟盘进行交易

# Binance模拟账户API Key和Secret Key
api_key = 'kFnTdNxT4ZjKTyjYtZ4grjpWYlfvOb6l6GteFf4sARBdFe3sUApQA9mrF2sgB0N7'
secret_key = 'praXZVYgy5erAXxgN2scw1PkyfExxt2UDlpfP2pKMSibcTKzMKIaO4uDmlzdJqWS'

# 创建交易所对象
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': secret_key,
    'enableRateLimit': True, # 启用请求频率限制
    'rateLimit': 1000, # 限制每秒最多发起的请求次数为1次
    'options': {
        'defaultType': 'future', # 设置默认交易类型为合约
        'test': True # 用于连接币安模拟盘的API
    }
})

# 交易对和数量
symbol = 'BTC/USDT'
amount = 0.01

# 买入BTC
try:
    # 创建市价买入订单
    order = exchange.create_market_buy_order(symbol, amount)
    print(f'买入BTC成功：订单号{order["id"]}')
except ccxt.InsufficientFunds as e:
    print('账户余额不足，无法买入BTC')
except ccxt.NetworkError as e:
    print('网络连接出错，无法完成交易')
except ccxt.ExchangeError as e:
    print('交易所错误，无法完成交易')

# 查询账户余额
balance = exchange.fetch_balance()['total']
print(f'账户余额：{balance["USDT"]:.2f} USDT')
