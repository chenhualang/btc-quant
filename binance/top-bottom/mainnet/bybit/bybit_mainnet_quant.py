import math

import requests
import json
import time
import hmac
import hashlib
import logging

# Bybit API相关信息
base_url = 'https://api.bybit.com'
api_key = 'GeS2xzvYScxnIjWEOU'
secret_key = '2JDubktuzxTvzkqE0AozIRcL5SByUrotzcCx'
headers = {
    'Content-Type': 'application/json',
}

# 获取服务器时间
def get_server_time():
    url = f"{base_url}/v2/public/time"
    response = requests.get(url)
    response_json = response.json()
    return response_json["time_now"]

# 签名方法
def generate_signature(data):
    data_string = json.dumps(data)
    signature = hmac.new(secret_key.encode('utf-8'), data_string.encode('utf-8'), hashlib.sha256).hexdigest()
    return signature

# 下单方法
def place_order(symbol, side, quantity, price):
    endpoint = '/v2/private/order/create'
    timestamp = int(time.time() * 1000)

    data = {
        'symbol': symbol,
        'side': side,
        'qty': quantity,
        'price': price,
        'time_in_force': 'GoodTillCancel',
        'order_type': 'Limit',
        'timestamp': timestamp,
        'api_key': api_key,
    }

    # 创建签名
    data['sign'] = generate_signature(data)

    response = requests.post(base_url + endpoint, data=json.dumps(data), headers=headers)
    response.raise_for_status()
    logging.info(f"place_order result response={response.json()}")
    return response.json()

# 查询订单状态
def get_order_status(symbol, order_id):
    endpoint = '/v2/private/order'
    timestamp = int(time.time() * 1000)

    data = {
        'symbol': symbol,
        'order_id': order_id,
        'timestamp': timestamp,
        'api_key': api_key,
    }

    # 创建签名
    data['sign'] = generate_signature(data)

    response = requests.get(base_url + endpoint, params=data, headers=headers)
    response.raise_for_status()
    return response.json()

# 撤销订单
def cancel_order(symbol, order_id):
    endpoint = '/v2/private/order/cancel'
    timestamp = int(time.time() * 1000)

    data = {
        'symbol': symbol,
        'order_id': order_id,
        'timestamp': timestamp,
        'api_key': api_key,
    }

    # 创建签名
    data['sign'] = generate_signature(data)

    response = requests.post(base_url + endpoint, data=json.dumps(data), headers=headers)
    response.raise_for_status()
    return response.json()

# 获取账户余额
def get_account_balance():
    endpoint = '/v2/private/wallet/balance'
    timestamp = get_server_time()

    data = {
        'timestamp': timestamp,
        'api_key': api_key,
    }

    # 创建签名
    data['sign'] = generate_signature(data)

    response = requests.get(base_url + endpoint, params=data, headers=headers)
    response_json = response.json()
    return response_json

# 查询K线数据
def get_kline_data(symbol, interval='15m', limit=1):
    endpoint = '/v2/public/kline/list'

    data = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit,
    }

    response = requests.get(base_url + endpoint, params=data)
    response_json = response.json()
    return response_json

def is_volume_spike(symbol):
    # 获取最近6小时的K线数据
    kline_data = get_kline_data(symbol, '6h')
    if len(kline_data) > 0:
        # 计算最近6小时内平均成交量
        average_volume = sum(float(kline[5]) for kline in kline_data) / len(kline_data)

        # 获取最新一次15分钟的K线数据
        current_kline = get_kline_data(symbol, '15m')[-1]
        current_volume = float(current_kline[5])

        # 判断是否放量
        if current_volume >= 3 * average_volume:
            return True

    return False

# 获取成交量最高的10个币
def get_top_10_volume_symbols():
    endpoint = '/v2/public/tickers'
    response = requests.get(base_url + endpoint)
    response.raise_for_status()
    tickers = response.json()['result']

    # 根据交易量进行排序
    tickers.sort(key=lambda x: float(x['volume_24h']), reverse=True)

    # 提取前10个币的交易对
    top_symbols = [ticker['symbol'] for ticker in tickers[:10]]
    return top_symbols

# 获取交易对的最新价格
def get_ticker(symbol):
    endpoint = '/v2/public/ticker'
    params = {'symbol': symbol}
    response = requests.get(base_url + endpoint, params=params)
    response.raise_for_status()
    return response.json()

def get_market_price(symbol):
    endpoint = '/v2/public/ticker'
    params = {'symbol': symbol}

    response = requests.get(base_url + endpoint, params=params)
    response.raise_for_status()
    ticker_data = response.json()

    market_price = float(ticker_data['result'][0]['last_price'])
    return market_price


# 主函数
if __name__ == '__main__':
    trade_quantity = 0.3  # 三成仓位
    profit_threshold = 0.02  # 盈利2%
    stop_loss_threshold = 0.02  # 止损2%
    # 获取24h成交量最高的10个币
    symbols = get_top_10_volume_symbols()

    # 遍历每个币并执行策略
    for symbol in symbols:
        try:
            # symbol = 'BTCUSDT'  # 根据实际需要修改
            logging.info(f"Executing strategy for symbol: {symbol}")
            while True:
                # 获取最新K线数据
                kline_data = get_kline_data(symbol)
                if len(kline_data) > 0:
                    latest_kline = kline_data[-1]
                    open_price = float(latest_kline[1])
                    high = float(latest_kline[2])
                    low = float(latest_kline[3])
                    volume = float(latest_kline[5])
                    close = float(latest_kline[4])


                    spike_flag = is_volume_spike(symbol)

                    market_price = get_market_price(symbol)
                    # 查询账户余额
                    account_balance = get_account_balance()
                    usdt_balance = next(item['availableBalance'] for item in account_balance if item['asset'] == 'USDT')
                    logging.info(f"binance 合约账户余额为:{usdt_balance}" )
                    # 计算买入数量
                    buy_quantity = float(usdt_balance) * trade_quantity / market_price
                    buy_quantity = math.ceil(buy_quantity)


                    # 判断条件并执行交易
                    if spike_flag and (high - close) >= (3 * (close - low)):
                    # if symbol == 'BTCUSDT':
                        logging.info(f"放量长下影线买入 for symbol: {symbol}")
                        # 符合条件，执行买入做多操作

                        if buy_quantity > 0:

                            # 计算卖出目标价格
                            target_price = market_price * (1 + profit_threshold)
                            stop_loss_price = market_price * (1 - stop_loss_threshold)

                            response = place_order(symbol, 'BUY', buy_quantity, market_price)
                            if 'orderId' in response:
                                logging.info('买入订单已执行')
                                order_info = get_order_status(symbol, response['orderId'])

                                while True:
                                    if order_info['status'] == 'FILLED':
                                        logging.info('委托订单已完全成交')
                                        break
                                    elif order_info['status'] == 'PARTIALLY_FILLED':
                                        executed_qty = float(order_info['executedQty'])
                                        if executed_qty >= buy_quantity / 2:
                                            logging.info('委托订单部分成交，等待执行止盈止损逻辑')
                                            break
                                        else:
                                            logging.info('委托订单部分成交，撤销未成交部分')
                                            cancel_order(symbol, response['orderId'])
                                            response = place_order(symbol, 'BUY', buy_quantity - executed_qty,
                                                                   market_price)
                                            if 'orderId' in response:
                                                logging.info('重新下单买入未成交部分')
                                            else:
                                                logging.info('重新下单买入未成交部分失败')
                                            break
                                    else:
                                        logging.info('委托订单未成交')
                                        time.sleep(1)
                                        order_info = get_order_status(symbol, response['orderId'])


                                # 监控价格并执行卖出操作
                                while True:
                                    time.sleep(1)
                                    # 获取最新价格
                                    ticker_data = get_ticker(symbol)
                                    last_price = float(ticker_data['price'])

                                    if last_price >= target_price:
                                        # 达到目标价格，执行卖出操作
                                        response = place_order(symbol, 'SELL', buy_quantity, last_price)
                                        if 'orderId' in response:
                                            logging.info(f"止盈订单已执行，Closed {symbol} at {last_price} with profit {profit_threshold * 100}%")
                                        else:
                                            logging.info('止盈订单执行失败')

                                        break
                                    elif last_price <= stop_loss_price:
                                        # 达到止损价格，执行止损操作
                                        response = place_order(symbol, 'SELL', buy_quantity, last_price)
                                        if 'orderId' in response:
                                            logging.info(f"止损订单已执行，Closed {symbol} at {last_price} with profit {profit_threshold * 100}%")
                                        else:
                                            logging.info('止损订单执行失败')
                            else:
                                logging.info('买入订单执行失败')
                        else:
                            logging.info('账户余额不足，无法进行买入操作')
                    elif spike_flag and close > open_price and (high - close) >= (3 * (close - low)):
                            logging.info(f"放量长上影线卖出 for symbol: {symbol}")
                            # if symbol == 'BTCUSDT':
                            if buy_quantity > 0:
                                # 符合条件，执行卖空操作
                                response = place_order(symbol, 'SELL', buy_quantity, market_price)
                                if 'orderId' in response:
                                    logging.info('卖空订单已执行')
                                    order_info = get_order_status(symbol, response['orderId'])

                                    while True:
                                        if order_info['status'] == 'FILLED':
                                            logging.info('委托订单已完全成交')
                                            break
                                        elif order_info['status'] == 'PARTIALLY_FILLED':
                                            executed_qty = float(order_info['executedQty'])
                                            if executed_qty >= buy_quantity / 2:
                                                logging.info('委托订单部分成交，等待执行止盈止损逻辑')
                                                break
                                            else:
                                                logging.info('委托订单部分成交，撤销未成交部分')
                                                cancel_order(symbol, response['orderId'])
                                                response = place_order(symbol, 'SELL', buy_quantity - executed_qty,
                                                                       market_price)
                                                if 'orderId' in response:
                                                    logging.info('重新下单卖空未成交部分')
                                                else:
                                                    logging.info('重新下单卖空未成交部分失败')
                                                break
                                        else:
                                            logging.info('委托订单未成交')
                                            time.sleep(1)
                                            order_info = get_order_status(symbol, response['orderId'])

                                    # 监控价格并执行平仓操作
                                    while True:
                                        time.sleep(1)
                                        # 获取最新价格
                                        ticker_data = get_ticker(symbol)
                                        last_price = float(ticker_data['price'])
                                        if last_price <= target_price:
                                            # 达到盈利目标价格，执行平仓操作
                                            response = place_order(symbol, 'BUY', buy_quantity, last_price)
                                            if 'orderId' in response:
                                                logging.info(
                                                    f"止盈订单已执行，Closed {symbol} at {last_price} with profit {profit_threshold * 100}%")
                                            else:
                                                logging.info('止盈订单执行失败')

                                            break
                                        elif last_price >= stop_loss_price:
                                            # 达到止损价格，执行止损操作
                                            response = place_order(symbol, 'BUY', buy_quantity, last_price)
                                            if 'orderId' in response:
                                                logging.info(
                                                    f"止损订单已执行，Closed {symbol} at {last_price} with profit {profit_threshold * 100}%")
                                            else:
                                                logging.info('止损订单执行失败')
                                else:
                                    logging.info('卖空订单执行失败')
                            else:
                                logging.info('账户余额不足，无法进行卖空操作')
                    else:
                        logging.info('不满足做多做空条件，继续等待')
        except Exception as e:
            logging.info(f"Error occurred for symbol: {symbol}")
            logging.info(f"Error message: {str(e)}")
            continue

# 下单结果： {'symbol': 'BTCUSDT', 'orderId': 841438, 'orderListId': -1, 'clientOrderId': 'hxNg58dRDHPeNsSW3mQD7U', 'transactTime': 1686315508366, 'price': '60000.00000000', 'origQty': '0.01000000', 'executedQty': '0.01000000', 'cummulativeQuoteQty': '266.59520000', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY', 'workingTime': 1686315508366, 'fills': [{'price': '26659.52000000', 'qty': '0.01000000', 'commission': '0.00000000', 'commissionAsset': 'BTC', 'tradeId': 244649}], 'selfTradePreventionMode': 'NONE'}
# BTC余额：1.01
#
# 该策略实现在某货币在放量长下影线的时候三成仓位买入，在盈利2%的时候全部卖出，亏损2%的时候全部平仓。
#  trade_quantity = 0.3  # 三成仓位
#     profit_threshold = 0.02  # 盈利2%
#     stop_loss_threshold = 0.02  # 止损2%
#     # 获取24h成交量最高的10个币
#     symbols = get_top_10_volume_symbols()