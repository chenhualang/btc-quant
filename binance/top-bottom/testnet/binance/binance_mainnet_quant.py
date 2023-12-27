import time
import random
import requests
import logging
import datetime
from notice.email1 import EmailSender
import concurrent.futures

# -*- coding: utf-8 -*-

# API信息
api_key = 'bGsgWApeV2jF6Pqf0ywA75q9UZcnfEnx5dJraYZESHr8AqvpplbkTdgsiJ6cwWuo'
secret_key = '34f417ee5c6d2d2c094689004b9768daaee476a7786138407a4cc8bb7e1cefd4'
base_url = "https://fapi.binance.com"
headers = {"Content-Type": "application/json",
           "X-MBX-APIKEY": api_key}

# 配置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建一个文件处理器，将日志写入文件
file_handler = logging.FileHandler('binance_quant_mainnet.log')
file_handler.setLevel(logging.INFO)

# 创建一个日志格式器，设置日志的输出格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 将文件处理器添加到日志记录器中
logger.addHandler(file_handler)

# logging.basicConfig(level=logging.INFO)  # 设置日志级别为INFO，可以根据需要调整级别    本地运行用这个
# logging.basicConfig(filename='binance_quant_mainnet.log', level=logging.INFO)  # 设置日志级别为INFO，可以根据需要调整级别   服务器运行用这个

# 查询K线数据
def get_kline_data(symbol, interval='15m', limit=1):
    endpoint = '/fapi/v1/klines'

    request_data = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }

    response = requests.get(base_url + endpoint, params=request_data)
    response_json = response.json()
    return response_json


def is_volume_spike(symbol):
    # 获取最近6小时的K线数据
    kline_data = get_kline_data(symbol, '5m', 72)
    if len(kline_data) > 0:
        # 计算最近6小时内平均成交量
        average_volume = sum(float(kline[5]) for kline in kline_data) / len(kline_data)

        # 获取最新一次15分钟的K线数据
        current_kline = get_kline_data(symbol, '5m')[-1]
        current_volume = float(current_kline[5])

        # 判断是否放量
        if current_volume >= 2 * average_volume:
            return True

    return False

# 获取成交量最高的20个币
def get_top_20_volume_symbols():
    base_url = 'https://fapi.binance.com'
    endpoint = '/fapi/v1/ticker/24hr'
    response = requests.get(base_url + endpoint)
    response.raise_for_status()
    tickers = response.json()

    # 根据交易量进行排序
    tickers.sort(key=lambda x: float(x['quoteVolume']), reverse=True)

    # 提取前10个币的交易对
    top_symbols = [ticker['symbol'] for ticker in tickers[:20]]
    return top_symbols

def send_email_notification(action, symbol):
    # 你的邮箱地址和授权密码
    sender_email = "chenhualang_1988@sina.com"
    sender_password = "b1f3558e5244792f"
    # 邮件服务器的地址和端口（使用 sina 邮箱作为示例）
    smtp_server = "smtp.sina.com"
    smtp_port = 465  # 使用 SMTP_SSL，端口改为465
    # 接收邮件的邮箱地址
    receiver_email = "charliechen1207@gmail.com"
    # 邮件主题和内容
    subject = f"{action} for symbol: {symbol}"
    body = f"{action} for symbol: {symbol}"
    # 创建 EmailSender 实例
    email_sender = EmailSender(sender_email, sender_password, smtp_server, smtp_port)
    # 发送邮件
    email_sender.send_email(receiver_email, subject, body)

# 主函数
if __name__ == '__main__':
    # 获取24h成交量最高的20个币
    symbols = get_top_20_volume_symbols()
    logger.info(f"24h成交量最高的20个币: {symbols}")


    def process_symbol(symbol):
        try:
            logger.info(f"Executing strategy for symbol: {symbol}")
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

                # 判断条件并执行交易
                if spike_flag and (high - close) >= (3 * (close - low)):
                    logger.info(f"放量长下影线买入 for symbol: {symbol}")
                    send_email_notification("放量长下影线买入", symbol)
                elif spike_flag and close > open_price and (high - close) >= (3 * (close - low)):
                    logger.info(f"放量长上影线卖出 for symbol: {symbol}")
                    send_email_notification("放量长上影线卖出", symbol)
                else:
                    logger.info('不满足做多做空条件，继续等待')
        except Exception as e:
            logger.info(f"Error occurred for symbol: {symbol}")
            logger.info(f"Error message: {str(e)}")


    # 使用多线程处理每个币种
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(process_symbol, symbols)

def process_symbols(symbols):
    for symbol in symbols:
        try:
            logger.info(f"Executing strategy for symbol: {symbol}")
            # 获取最新K线数据
            kline_data = get_kline_data(symbol)
            if len(kline_data) > 0:
                latest_kline = kline_data[0]
                open_price = float(latest_kline[1])
                high = float(latest_kline[2])
                low = float(latest_kline[3])
                volume = float(latest_kline[5])
                close = float(latest_kline[4])

                spike_flag = is_volume_spike(symbol)

                # 判断条件并执行交易
                if spike_flag and (high - close) >= (1.5 * abs(close - open_price)):
                    logger.info(f"放量长上影线买入 for symbol: {symbol}")
                    # 执行买入逻辑，可以调用相关函数
                elif spike_flag and (close - low) >= (1.5 * abs(close - open_price)):
                    logger.info(f"放量长下影线卖出 for symbol: {symbol}")
                    # 执行卖出逻辑，可以调用相关函数
                else:
                    logger.info(f"不满足做多做空条件，继续等待 for symbol: {symbol}")
        except Exception as e:
            logger.info(f"Error occurred for symbol: {symbol}")
            logger.info(f"Error message: {str(e)}")

def main():
    # 获取24h成交量最高的20个币
    symbols = get_top_20_volume_symbols()
    # symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'LTCUSDT']  # 你需要监控的币种列表
    logger.info(f"24h成交量最高的20个币: {symbols}")

    while True:
        # 执行监控任务
        process_symbols(symbols)
        logger.info('扫描完一次20个币对，随机休眠一段时间后继续扫描')
        # 休眠一段时间，避免频繁请求
        time.sleep(random.uniform(60, 120))  # 随机休眠60-120秒


if __name__ == '__main__':
    main()


# 下单结果： {'symbol': 'BTCUSDT', 'orderId': 841438, 'orderListId': -1, 'clientOrderId': 'hxNg58dRDHPeNsSW3mQD7U', 'transactTime': 1686315508366, 'price': '60000.00000000', 'origQty': '0.01000000', 'executedQty': '0.01000000', 'cummulativeQuoteQty': '266.59520000', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY', 'workingTime': 1686315508366, 'fills': [{'price': '26659.52000000', 'qty': '0.01000000', 'commission': '0.00000000', 'commissionAsset': 'BTC', 'tradeId': 244649}], 'selfTradePreventionMode': 'NONE'}
# BTC余额：1.01
#
# 该策略实现在某货币在放量长下影线的时候三成仓位买入，在盈利2%的时候全部卖出，亏损2%的时候全部平仓。
#  trade_quantity = 0.3  # 三成仓位
#     profit_threshold = 0.02  # 盈利2%
#     stop_loss_threshold = 0.02  # 止损2%
#     # 获取24h成交量最高的10个币
#     symbols = get_top_10_volume_symbols()

#     暂时采用邮件通知后手动下单，后续采用自动交易