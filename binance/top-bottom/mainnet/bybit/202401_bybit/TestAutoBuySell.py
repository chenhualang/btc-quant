import math
import threading

from pybit.unified_trading import HTTP
from email1 import EmailSender
import logging
import datetime
import time

session = HTTP(
    testnet=False,
    api_key="N93MO3wRs0PCYH65yI",
    api_secret="igRi3Mq3ticqvBr9cdRgjCMNiEmldbiIdhqD",
)

# # 配置日志记录器
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
#
# # 创建一个文件处理器，将日志写入文件
# file_handler = logging.FileHandler('bybit_quant_mainnet.log')
# file_handler.setLevel(logging.INFO)
#
# # 创建一个日志格式器，设置日志的输出格式
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# file_handler.setFormatter(formatter)
#
# # 将文件处理器添加到日志记录器中
# logger.addHandler(file_handler)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # 设置日志级别为INFO，可以根据需要调整级别    本地运行用这个
# logging.basicConfig(filename='bybit_quant_mainnet.log', level=logging.INFO)  # 设置日志级别为INFO，可以根据需要调整级别   服务器运行用这个


trade_quantity = 0.3  # 三成仓位
profit_threshold = 0.02  # 盈利2%
stop_loss_threshold = 0.02  # 止损2%

def is_volume_spike(symbol):
    # 获取最近6小时的K线数据
    kline_data = session.get_kline(symbol=symbol,interval=5,limit=72)["result"]["list"]
    if len(kline_data) > 0:
        # 计算最近6小时内平均成交量
        average_volume = sum(float(kline[5]) for kline in kline_data) / len(kline_data)

        # 获取最新一次15分钟的K线数据
        current_kline = session.get_kline(symbol=symbol, interval=5, limit=1)["result"]["list"][0]
        current_volume = float(current_kline[5])
        logger.info(f"币种: {symbol}, 最新成交量: {current_volume}, 最近6小时平均成交量: {average_volume}, 时间戳: {current_kline[0]}")
        # 判断是否放量
        if current_volume >= 2 * average_volume:
            logger.info(f"满足放量条件，最近一次成交量是平均成交量的2倍以上, 币种: {symbol}, 最新成交量: {current_volume}, 最近6小时平均成交量: {average_volume}, 时间戳: {current_kline[0]}")
            return True

    return False


def get_top_20_volume_symbols():
    tickers = session.get_tickers(category="linear", limit=100)["result"]["list"]
    tickers.sort(key=lambda x: float(x['turnover24h']), reverse=True)
    top_symbols = [ticker['symbol'] for ticker in tickers[:20]]
    return top_symbols


def send_email_notification(action, symbol, klineData):
    # 你的邮箱地址和授权密码
    sender_email = "chenhualang_1988@sina.com"
    sender_password = "b1f3558e5244792f"
    # 邮件服务器的地址和端口（使用 sina 邮箱作为示例）
    smtp_server = "smtp.sina.com"
    smtp_port = 465  # 使用 SMTP_SSL，端口改为465
    # 接收邮件的邮箱地址
    receiver_email = "charliechen1207@gmail.com"
    # 邮件主题和内容
    subject = f"{action}币种 : {symbol}, 时间: {convert_time(int(klineData[0]))}"
    body = f"{action}币种 : {symbol}, K线数据: {klineData}"
    # 创建 EmailSender 实例
    email_sender = EmailSender(sender_email, sender_password, smtp_server, smtp_port)
    # 发送邮件
    email_sender.send_email(receiver_email, subject, body)

def process_symbols(symbols):
    for symbol in symbols:
        try:
            logger.info(f"Executing strategy for symbol: {symbol}")
            # 获取最新K线数据
            kline_data = session.get_kline(category="linear", symbol=symbol, interval=5)["result"]["list"]
            if len(kline_data) > 0:
                latest_kline = kline_data[0]
                open_price = float(latest_kline[1])
                high = float(latest_kline[2])
                low = float(latest_kline[3])
                volume = float(latest_kline[5])
                close = float(latest_kline[4])

                spike_flag = is_volume_spike(symbol)

                 # 查詢最新行情信息, GET / v5 / market / tickers, https: // bybit - exchange.github.io / docs / zh - TW / v5 / market / tickers
                price_data = session.get_tickers(category="linear", symbol=symbol)["result"]["list"][0]
                # 这里取的是lastPrice,最新市场成交价
                last_price = float(price_data[1])

                # 获取账户余额
                # session.get_wallet_balance(accountType="CONTRACT", coin="USDT")["result"]["list"][0]



                # 判断条件并执行交易
                if spike_flag and close > open_price and (open_price - low) >= (2 * abs(close - open_price)):
                    logger.info(f"放量长下影线买入 for symbol: {symbol}, K线数据: {latest_kline}")
                    send_email_notification("放量长下影线买入", symbol, latest_kline)
                    # 执行买入逻辑，可以调用相关函数   放量长下影线且阳线放量，做多买入
                elif spike_flag and close < open_price and (high - open_price) >= (2 * abs(close - open_price)):
                    logger.info(f"放量长上影线卖出 for symbol: {symbol}, K线数据: {latest_kline}")
                    send_email_notification("放量长上影线卖出", symbol, latest_kline)
                    # 执行卖出逻辑，可以调用相关函数     放量长上影线且阴线放量，做空卖出
                else:
                    logger.info(f"不满足做多做空条件，继续等待 for symbol: {symbol}")
        except Exception as e:
            logger.info(f"Error occurred for symbol: {symbol}")
            logger.info(f"Error message: {str(e)}")


# def main():
    # 获取24h成交量最高的20个币
    # symbols = get_top_20_volume_symbols()
    # # symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'LTCUSDT']  # 你需要监控的币种列表
    # logger.info(f"24h成交量最高的20个币: {symbols}")
    #
    # while True:
    #     # 执行监控任务
    #     process_symbols(symbols)
    #     logger.info('扫描完一次20个币对，随机休眠一段时间后继续扫描')
    #     # 休眠一段时间，避免频繁请求
    #     time.sleep(random.uniform(60, 120))  # 随机休眠60-120秒


def get_coin_price():
    symbol = 'BTCUSDT'
    # 查詢最新行情信息, GET / v5 / market / tickers, https: // bybit - exchange.github.io / docs / zh - TW / v5 / market / tickers
    price_data = session.get_tickers(category="linear", symbol=symbol)["result"]["list"][0]
    # 这里取的是lastPrice,最新市场成交价
    last_price = float(price_data['lastPrice'])
    logger.info(f"当前最新成交价为: {last_price}")
    return last_price

def get_wallet_balance():
    # 获取账户余额
    wallet_balance = session.get_wallet_balance(accountType="CONTRACT", coin="USDT")["result"]["list"][0]
    logger.info(f"账户余额为: {wallet_balance}")
    # 目前简单处理，获取第一个币种的余额，这里第一个币种为USDT
    usdt_balance = wallet_balance['coin'][0]['equity']
    logger.info(f"账户余额为: {usdt_balance}")
    return usdt_balance

def place_order():
    usdt_balance = get_wallet_balance()
    market_price = get_coin_price()
    buy_quantity = float(usdt_balance) * trade_quantity / market_price
    buy_quantity = math.ceil(buy_quantity)

    # 计算卖出目标价格
    # target_price = market_price * (1 + profit_threshold)
    # stop_loss_price = market_price * (1 - stop_loss_threshold)
    # 测试买入功能
    order_result = session.place_order(
        category="linear",
        symbol="SEIUSDT",
        side="Buy",
        orderType="Market",
        qty="50",
        isLeverage=0,
        orderFilter="Order",
        # takeProfit=target_price,
        # stopLoss=stop_loss_price,
    )
    logger.info(f"下单结果: {order_result}")
     #   下单测试成功
     #     下单结果: {'retCode': 0, 'retMsg': 'OK', 'result': {'orderId': '4e179fcb-d35b-4fe3-97a0-90bf5e4b86ed', 'orderLinkId': ''}, 'retExtInfo': {}, 'time': 1704784349475}

def take_profit_loss(position):
    logger.info(f"合约持仓信息: {position}")

    avgPrice = position["avgPrice"]
    markPrice = position["markPrice"]
    symbol = position["symbol"]
    side = position["side"]
    size = position["size"]
    current_price = markPrice

    # 判断持仓方向
    if side == "Buy":
        # 计算止盈和止损价格
        target_price = float(avgPrice) * (1 + profit_threshold)
        stop_loss_price = float(avgPrice) * (1 - stop_loss_threshold)
    elif side == "Sell":
        # 计算止盈和止损价格
        target_price = float(avgPrice) * (1 - profit_threshold)
        stop_loss_price = float(avgPrice) * (1 + stop_loss_threshold)
    else:
        logger.error("Invalid side parameter")
        return
    logger.info(f"合约币种: {symbol}止盈价格: {target_price}, 止损价格: {stop_loss_price}")
    reached_target_price = False
    while not reached_target_price:

        if (side == "Buy" and float(current_price) >= target_price) or (side == "Sell" and float(current_price) <= target_price):
            # 达到止盈价格，平仓
            if side == "Buy":
                logger.info(f"多仓止盈卖出，币种: {symbol}")
                session.place_order(
                    category="linear",
                    symbol=symbol,
                    side="Sell",
                    orderType="Market",
                    qty=size,
                    isLeverage=0,
                )
            elif side == "Sell":
                logger.info(f"空仓止盈买入，币种: {symbol}")
                session.place_order(
                    category="linear",
                    symbol=symbol,
                    side="Buy",
                    orderType="Market",
                    qty=size,
                    isLeverage=0,
                )
            reached_target_price = True
            break

        if (side == "Buy" and float(current_price) <= stop_loss_price) or (
                side == "Sell" and float(current_price) >= stop_loss_price):
            # 达到止损价格，平仓
            if side == "Buy":
                logger.info(f"多仓止损卖出，币种: {symbol}")
                session.place_order(
                    category="linear",
                    symbol=symbol,
                    side="Sell",
                    orderType="Market",
                    qty=size,
                    isLeverage=0,
                )
            elif side == "Sell":
                logger.info(f"空仓止损买入，币种: {symbol}")
                session.place_order(
                    category="linear",
                    symbol=symbol,
                    side="Buy",
                    orderType="Market",
                    qty=size,
                    isLeverage=0,
                )
            reached_target_price = True
            break

        # 每隔一段时间检查一次价格
        time.sleep(1)

def monitor_positions(positions):
    # 创建一个线程列表
    logger.info(f"开始多线程监控所有持仓币种")
    threads = []
    for position in positions:
        # 创建一个线程，并将take_profit_loss函数作为目标函数
        thread = threading.Thread(target=take_profit_loss, args=(position,))
        threads.append(thread)

    # 启动所有线程
    for thread in threads:
        thread.start()

    # 等待所有线程结束
    for thread in threads:
        thread.join()



def get_position():
    # 获取当前持仓
    position_result = session.get_positions(
        category="linear",
        settleCoin="USDT",
    )
    logger.info(f"当前持仓为: {position_result}")
    positions = position_result["result"]["list"]
    info_list = []
    for position in positions:
        symbol = position["symbol"]
        size = position["size"]
        side = position["side"]
        avgPrice = position["avgPrice"]
        markPrice = position["markPrice"]
        positionValue = position["positionValue"]
        leverage = position["leverage"]
        logger.info(f"当前合约币种信息包括，币种: {symbol}，持仓数量: {size}，多空方向: {side}，入场成本价格: {avgPrice}，最新标记价格: {markPrice}，合约价值: {positionValue}，杠杆倍数: {leverage}")
        info_list.append({
            "symbol": symbol,
            "size": size,
            "side": side,
            "avgPrice": avgPrice,
            "markPrice": markPrice,
            "positionValue": positionValue,
            "leverage": leverage
        })
    logger.info(f"当前合约币种持仓信息: {info_list}")
    return info_list


def convert_time(timestamp):
    # timestamp = 1673349000000
    # 根据毫秒时间戳创建datetime对象
    dt = datetime.datetime.fromtimestamp(timestamp / 1000)

    # 格式化datetime对象为指定格式
    formatted_datetime = dt.strftime('%Y-%m-%d %H:%M:%S')

    print(formatted_datetime)
    return dt


if __name__ == '__main__':
    # main()

    # get_coin_price()

    # get_wallet_balance()

    # place_order()

    # convert_time(1704727800000)

    # send_email_notification("放量长上影线卖出", "BTCUSDT", "2024-01-01 19:20:00")

    # get_position()

    # take_profit_loss()

    # 调用函数开始监控持仓
    positions = get_position()
    monitor_positions(positions)