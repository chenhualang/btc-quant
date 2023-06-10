import time
import requests
import hashlib
import hmac
import json

# Bybit V5实盘API地址
BYBIT_ENDPOINT = 'https://api.bybit.com'

# API密钥和密钥
API_KEY = 'GeS2xzvYScxnIjWEOU'
API_SECRET = '2JDubktuzxTvzkqE0AozIRcL5SByUrotzcCx'

# 生成签名的函数
def generate_signature(secret, data):
    # 将请求参数按照键名进行升序排列，并拼接成字符串
    sorted_params = sorted(data.items(), key=lambda x: x[0])
    param_str = '&'.join([f'{k}={v}' for k, v in sorted_params])
    # 使用API密钥作为密钥对拼接字符串进行HMAC-SHA256签名
    signature = hmac.new(bytes(secret, 'utf-8'), bytes(param_str, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return signature

# 调用API的函数
def call_api(method, endpoint, params=None, data=None):
    # 如果提供了请求参数，则对其进行签名并添加到请求头中
    headers = {}
    if params is not None:
        # 添加时间戳
        params.update({'timestamp': int(time.time() * 1000)})
        # 生成签名并添加到请求头中
        signature = generate_signature(API_SECRET, params)
        headers['api-key'] = API_KEY
        headers['sign'] = signature
    # 发送HTTP请求
    response = requests.request(method, BYBIT_ENDPOINT + endpoint, headers=headers, params=params if method == 'GET' else None, json=data if method != 'GET' else None)
    # 如果返回状态码不是200，则抛出异常
    response.raise_for_status()
    # 解析JSON响应并返回
    return response.json()

# 生成时间戳和签名的函数
def generate_signature(api_secret, method, path, expires, data=''):
    signature_str = method + path + str(expires) + data
    signature = hmac.new(bytes(api_secret, encoding='utf-8'), bytes(signature_str, encoding='utf-8'), digestmod=hashlib.sha256).hexdigest()
    return signature

def generate_expires():
    return int(time.time()) + 60 * 60  # 过期时间为当前时间加上1小时

# 生成认证头的函数
def generate_auth_headers(api_key, api_secret, method, path, expires, data=''):
    signature = generate_signature(api_secret, method, path, expires, data)
    return {
        'api-expires': str(expires),
        'api-key': api_key,
        'api-signature': signature,
        'Content-Type': 'application/json'
    }

# 查询账户余额
def get_account_balance():
    expires = generate_expires()
    headers = generate_auth_headers(API_KEY, API_SECRET, 'GET', '/unified/v3/private/account/wallet/balance', expires)
    url = BYBIT_ENDPOINT + '/unified/v3/private/account/wallet/balance'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# 创建市价订单
def create_market_order(symbol, side, quantity):
    body = {
        'symbol': symbol,
        'side': side,
        'order_type': 'Market',
        'qty': quantity,
        'time_in_force': 'ImmediateOrCancel'
    }
    return call_api('POST', '/v2/private/order/create', body=body)




if __name__ == '__main__':
    # 示例调用
    print(get_account_balance())
    # print(create_market_order('BTCUSD', 'Buy', 0.01))