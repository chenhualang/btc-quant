import time
import hashlib
import hmac
import requests

# 币安API信息
api_key = 'YOUR_API_KEY'
api_secret = 'YOUR_API_SECRET'
base_url = 'https://api.binance.com'

# 获取服务器时间
def get_server_time():
    url = f'{base_url}/api/v3/time'
    response = requests.get(url)
    response_json = response.json()
    return response_json['serverTime']

# 生成签名
def generate_signature(data):
    ordered_data = '&'.join([f'{key}={data[key]}' for key in data])
    signature = hmac.new(api_secret.encode(), ordered_data.encode(), hashlib.sha256).hexdigest()
    return signature

# 下单方法
def place_order(symbol, side, quantity):
    endpoint = '/api/v3/order'
    timestamp = get_server_time()

    request_data = {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': quantity,
        'timestamp': timestamp,
        'recvWindow': 5000,
        'timestamp': timestamp
    }

    request_data['signature'] = generate_signature(request_data)

    headers = {
        'X-MBX-APIKEY': api_key
    }

    response = requests.post(base_url + endpoint, params=request_data, headers=headers)
    response_json = response.json()
    return response_json

# 获取账户余额
def get_account_balance():
    endpoint = '/api/v3/account'
    timestamp = get_server_time()

    request_data = {
        'timestamp': timestamp,
        'recvWindow': 5000
    }

    request_data['signature'] = generate_signature(request_data)

    headers = {
        'X-MBX-APIKEY': api_key
    }

    response = requests.get(base_url + endpoint, params=request_data, headers=headers)
    response_json = response.json()
    return response_json

# 查询K线数据
def get_kline_data(symbol, interval='1h', limit=1):
    endpoint = '/api/v3/klines'

    request_data = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }

    response = requests.get(base_url + endpoint, params=request_data)
    response_json = response.json()
    return response_json

# 主函数
if __name__ == '__main__':
    symbol = 'BTCUSDT'  # 根据实际需要修改
    trade_quantity = 0.7  # 七成仓位
    profit_threshold = 0.1  # 盈利10%

    # 获取最新K线数据
    kline_data = get_kline_data(symbol)
    latest_kline = kline_data[-1]
    high = float(latest_kline[2])
    low = float(latest_kline[3])
    volume = float(latest_kline[5])
    close = float(latest_kline[4])

    # 判断条件并执行交易
    if volume > 1000000 and (high - close) >= (3 * (close - low)):
        # 符合条件，执行买入操作
        response = place_order(symbol, 'BUY', trade_quantity)
        if 'orderId' in response:
            print('买入订单已执行')

            # 查询账
