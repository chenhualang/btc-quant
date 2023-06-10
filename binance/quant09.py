import requests
import json
import time
import hmac
import hashlib

# 用币安API写一个基于币安模拟账户的量化交易程序python demo, 交易btc的. API Key: kFnTdNxT4ZjKTyjYtZ4grjpWYlfvOb6l6GteFf4sARBdFe3sUApQA9mrF2sgB0N7
# Secret Key: praXZVYgy5erAXxgN2scw1PkyfExxt2UDlpfP2pKMSibcTKzMKIaO4uDmlzdJqWS.要求能直接运行，有main 方法

# 币安模拟账户API
api_key = 'kFnTdNxT4ZjKTyjYtZ4grjpWYlfvOb6l6GteFf4sARBdFe3sUApQA9mrF2sgB0N7'
secret_key = 'praXZVYgy5erAXxgN2scw1PkyfExxt2UDlpfP2pKMSibcTKzMKIaO4uDmlzdJqWS'
base_url = 'https://testnet.binance.vision'
headers = {'Content-Type': 'application/json;charset=utf-8'}
params = {'timestamp': int(time.time() * 1000)}


# 下单
def place_order(symbol, side, quantity, price):
    # 请求参数
    params['symbol'] = symbol
    params['side'] = side
    params['type'] = 'LIMIT'
    params['timeInForce'] = 'GTC'
    params['quantity'] = quantity
    params['price'] = price

    # 生成签名
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(secret_key, query_string.encode(), hashlib.sha256).hexdigest()

    # 发送请求
    endpoint = f"/api/v3/order?{query_string}&signature={signature}"
    url = base_url + endpoint
    response = requests.post(url, headers=headers, json=params, auth=(api_key, secret_key))

    # 处理响应
    if response.status_code != 200:
        print('下单失败')
        print(response.text)
        return

    print('下单成功')
    print(response.json())


if __name__ == '__main__':
    symbol = 'BTCUSDT'
    side = 'BUY'
    quantity = 0.01
    price = 50000
    place_order(symbol, side, quantity, price)
