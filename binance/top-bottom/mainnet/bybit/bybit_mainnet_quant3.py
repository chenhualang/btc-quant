import requests
import time
import hashlib
import hmac
import uuid
from pybit.unified_trading import HTTP

api_key='GeS2xzvYScxnIjWEOU'
secret_key='2JDubktuzxTvzkqE0AozIRcL5SByUrotzcCx'
httpClient=requests.Session()
recv_window=str(5000)
url="https://api.bybit.com" # Testnet endpoint

def HTTP_Request(endPoint,method,payload,Info):
    global time_stamp
    time_stamp=str(int(time.time() * 10 ** 3))
    signature=genSignature(payload)
    headers = {
        'X-BAPI-API-KEY': api_key,
        'X-BAPI-SIGN': signature,
        'X-BAPI-SIGN-TYPE': '2',
        'X-BAPI-TIMESTAMP': time_stamp,
        'X-BAPI-RECV-WINDOW': recv_window,
        'Content-Type': 'application/json'
    }
    if(method=="POST"):
        response = httpClient.request(method, url+endPoint, headers=headers, data=payload)
    else:
        response = httpClient.request(method, url+endPoint+"?"+payload, headers=headers)
    print(response.text)
    print(Info + " Elapsed Time : " + str(response.elapsed))

def genSignature(payload):
    param_str= str(time_stamp) + api_key + recv_window + payload
    hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"),hashlib.sha256)
    signature = hash.hexdigest()
    return signature


def get_kline():
    return session.get_kline(
        category="inverse",
        symbol="BTCUSD",
        interval=60,
        start=1670601600000,
        end=1670608800000,
    )

def get_top_20_volume_symbols():
    endpoint = '/v5/market/tickers'
    method = "GET"
    params = 'category=linear'
    response = HTTP_Request(endpoint, method, params)

    tickers = response.json()['result']

    print(response.json())

    # 根据交易量进行排序
    tickers.sort(key=lambda x: float(x['turnover_24h']), reverse=True)

    # 提取前20个币的交易对
    top_symbols = [ticker['symbol'] for ticker in tickers[:20]]
    return top_symbols

def create_order():
    endpoint = "/v5/order/create"
    method = "POST"
    orderLinkId = uuid.uuid4().hex
    params = '{"category":"linear","symbol": "BTCUSDT","side": "Buy","positionIdx": 0,"orderType": "Limit","qty": "0.001","price": "10000","timeInForce": "GTC","orderLinkId": "' + orderLinkId + '"}'
    HTTP_Request(endpoint, method, params, "Create")

def get_unfilled_orders():
    endpoint = "/v5/order/realtime"
    method = "GET"
    params = 'category=linear&settleCoin=USDT'
    HTTP_Request(endpoint, method, params, "UnFilled")

def cancel_order(orderLinkId):
    endpoint = "/v5/order/cancel"
    method = "POST"
    params = '{"category":"linear","symbol": "BTCUSDT","orderLinkId": "' + orderLinkId + '"}'
    HTTP_Request(endpoint, method, params, "Cancel")

if __name__ == "__main__":
    session = HTTP(testnet=False)

    # Call your methods here
    kline_result = get_top_20_volume_symbols()
    print(kline_result)

    # create_order()
    #
    # get_unfilled_orders()
    #
    # # Replace 'your_orderLinkId' with the actual orderLinkId you want to cancel
    # cancel_order('your_orderLinkId')