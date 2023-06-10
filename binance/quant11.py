import hmac
import json
import time
import hashlib
import requests

# API信息
api_key = "kFnTdNxT4ZjKTyjYtZ4grjpWYlfvOb6l6GteFf4sARBdFe3sUApQA9mrF2sgB0N7"
secret_key = "praXZVYgy5erAXxgN2scw1PkyfExxt2UDlpfP2pKMSibcTKzMKIaO4uDmlzdJqWS"
base_url = "https://testnet.binancefuture.com"
headers = {"Content-Type": "application/json",
           "X-MBX-APIKEY": api_key}

# 获取服务器时间
def get_server_time():
    url = f"{base_url}/fapi/v1/time"
    response = requests.get(url)
    response_json = json.loads(response.text)
    return response_json["serverTime"]

# 签名方法
def signature(query_string):
    return hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

# 下单方法
def place_order(symbol, side, type, quantity, price):
    query_string = f"symbol={symbol}&side={side}&type={type}&timeInForce=GTC&quantity={quantity}&price={price}&timestamp={get_server_time()}"
    signature_str = signature(query_string)
    url = f"{base_url}/fapi/v1/order?{query_string}&signature={signature_str}"
    response = requests.post(url, headers=headers)
    response_json = json.loads(response.text)
    return response_json

def place_order(symbol, side, quantity, price):
    endpoint = '/fapi/v1/order'
    timestamp = int(time.time() * 1000)

    params = {
        'symbol': symbol,
        'side': side,
        'quantity': quantity,
        'price': price,
        'timeInForce': 'GTC',
        'type': 'LIMIT',
        'timestamp': timestamp,
        'recvWindow': 5000
    }

    # 创建签名
    query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
    signature_str = signature(query_string)

    # 添加签名到参数中
    params['signature'] = signature_str

    response = requests.post(base_url + endpoint, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

# 获取账户余额
def get_account_balance():
    endpoint = '/fapi/v2/balance'
    timestamp = get_server_time()

    request_data = {
        'timestamp': timestamp,
        'recvWindow': 5000
    }

    request_data['signature'] = signature(request_data)

    headers = {
        'X-MBX-APIKEY': api_key
    }

    response = requests.get(base_url + endpoint, params=request_data, headers=headers)
    response_json = response.json()
    return response_json

# 查询K线数据
def get_kline_data(symbol, interval='1h', limit=1):
    endpoint = '/fapi/v1/klines'

    request_data = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }

    response = requests.get(base_url + endpoint, params=request_data)
    response_json = response.json()
    return response_json

# 获取成交量最高的10个币
def get_top_10_volume_symbols():
    base_url = 'https://testnet.binancefuture.com'
    endpoint = '/fapi/v1/ticker/24hr'
    response = requests.get(base_url + endpoint)
    response.raise_for_status()
    tickers = response.json()

    # 根据交易量进行排序
    tickers.sort(key=lambda x: float(x['volume']), reverse=True)

    # 提取前10个币的交易对
    top_symbols = [ticker['symbol'] for ticker in tickers[:10]]
    return top_symbols

# 获取交易对的最新价格
def get_ticker(symbol):
    endpoint = '/fapi/v1/ticker/price'
    params = {'symbol': symbol}
    response = requests.get(base_url + endpoint, params=params)
    response.raise_for_status()
    return response.json()


# 主函数
if __name__ == '__main__':
    # symbol = 'BTCUSDT'  # 根据实际需要修改
    trade_quantity = 0.7  # 七成仓位
    profit_threshold = 0.1  # 盈利10%

    # 获取成交量最高的10个币
    symbols = get_top_10_volume_symbols()

    # 遍历每个币并执行策略
    for symbol in symbols:
        try:
            print(f"Executing strategy for symbol: {symbol}")
            # 获取最新K线数据
            kline_data = get_kline_data(symbol)
            if len(kline_data) > 0:
                latest_kline = kline_data[-1]
                open_price = float(latest_kline[1])
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

                        # 查询账户余额
                        account_balance = get_account_balance()
                        if 'balances' in account_balance:
                            for balance in account_balance['balances']:
                                if balance['asset'] == symbol[:-4]:
                                    asset_balance = float(balance['free'])
                                    break

                            # 计算卖出目标价格
                            target_price = close * (1 + profit_threshold)

                            # 监控价格并执行卖出操作
                            while True:
                                time.sleep(1)

                                # 获取最新价格
                                ticker_data = get_ticker(symbol)
                                last_price = float(ticker_data['lastPrice'])

                                if last_price >= target_price:
                                    # 达到目标价格，执行卖出操作
                                    response = place_order(symbol, 'SELL', asset_balance)
                                    if 'orderId' in response:
                                        print('卖出订单已执行')
                                    else:
                                        print('卖出订单执行失败')

                                    break
                    else:
                        if volume > 1000000 and close > open_price and (high - close) >= (3 * (close - low)):
                            # 符合放量长上影线条件，执行做空卖出操作
                            response = place_order(symbol, 'SELL', trade_quantity)
                            if 'orderId' in response:
                                print('Short sell order executed')
                                print(f"Short sold {trade_quantity * 100}% of {symbol} at {close}")

                                # 计算盈利目标价格
                                target_price = close * (1 - profit_threshold)

                                # 监控价格并执行平仓操作
                                while True:
                                    time.sleep(1)

                                    # 获取最新价格
                                    ticker_data = get_ticker(symbol)
                                    last_price = float(ticker_data['lastPrice'])

                                    if last_price <= target_price:
                                        # 达到盈利目标价格，执行平仓操作
                                        response = place_order(symbol, 'BUY', trade_quantity)
                                        if 'orderId' in response:
                                            print('Close position order executed')
                                            print(
                                                f"Closed {symbol} at {last_price} with profit {profit_threshold * 100}%")
                                        else:
                                            print('Failed to execute close position order')

                                        break
            else:
                print(f"No K-line data available for symbol: {symbol}")
        except Exception as e:
            print(f"Error occurred for symbol: {symbol}")
            print(f"Error message: {str(e)}")
            continue

# 下单结果： {'symbol': 'BTCUSDT', 'orderId': 841438, 'orderListId': -1, 'clientOrderId': 'hxNg58dRDHPeNsSW3mQD7U', 'transactTime': 1686315508366, 'price': '60000.00000000', 'origQty': '0.01000000', 'executedQty': '0.01000000', 'cummulativeQuoteQty': '266.59520000', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY', 'workingTime': 1686315508366, 'fills': [{'price': '26659.52000000', 'qty': '0.01000000', 'commission': '0.00000000', 'commissionAsset': 'BTC', 'tradeId': 244649}], 'selfTradePreventionMode': 'NONE'}
# BTC余额：1.01
#
# 该策略实现在某货币在放量长下影线的时候七成仓位买入，在盈利10%的时候全部卖出