import time
import random
from pybit.unified_trading import HTTP
from email1 import EmailSender
import logging
from kline import KLineChart

session = HTTP(
    testnet=False,
    api_key="GeS2xzvYScxnIjWEOU",
    api_secret="2JDubktuzxTvzkqE0AozIRcL5SByUrotzcCx",
)

# 配置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建一个文件处理器，将日志写入文件
file_handler = logging.FileHandler('bybit_quant_mainnet.log')
file_handler.setLevel(logging.INFO)

# 创建一个日志格式器，设置日志的输出格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 将文件处理器添加到日志记录器中
logger.addHandler(file_handler)

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)  # 设置日志级别为INFO，可以根据需要调整级别    本地运行用这个
# logging.basicConfig(filename='bybit_quant_mainnet.log', level=logging.INFO)  # 设置日志级别为INFO，可以根据需要调整级别   服务器运行用这个


def is_volume_spike(symbol):
    # 获取最近6小时的K线数据
    kline_data = session.get_kline(symbol=symbol,interval=5,limit=72)["result"]["list"]
    if len(kline_data) > 0:
        # 计算最近6小时内平均成交量
        average_volume = sum(float(kline[5]) for kline in kline_data) / len(kline_data)

        # 获取最新一次15分钟的K线数据
        current_kline = session.get_kline(symbol=symbol, interval=5, limit=1)["result"]["list"][0]
        current_volume = float(current_kline[5])
        logger.info(f"Current Volume: {current_volume}, Average Volume: {average_volume}")
        # 判断是否放量
        if current_volume >= 2 * average_volume:
            logger.info('满足放量条件，最近一次成交量是平均成交量的2倍以上')
            return True

    return False


def get_top_20_volume_symbols():
    tickers = session.get_tickers(category="linear", limit=100)["result"]["list"]
    tickers.sort(key=lambda x: float(x['turnover24h']), reverse=True)
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

def process_symbols(symbols):
    for symbol in symbols:
        symbol = "TRBUSDT"
        try:
            logger.info(f"Executing strategy for symbol: {symbol}")
            # 获取最新K线数据
            kline_data = session.get_kline(category="linear", symbol=symbol, interval=5)["result"]["list"]

            # # 创建KLineChart对象
            # kline_chart = KLineChart(kline_data)
            #
            # # 生成K线图
            # kline_chart.generate_chart()
            # kline_chart.save_chart()

            if len(kline_data) > 0:
                latest_kline = kline_data[0]
                open_price = float(latest_kline[1])
                high = float(latest_kline[2])
                low = float(latest_kline[3])
                volume = float(latest_kline[5])
                close = float(latest_kline[4])

                # spike_flag = is_volume_spike(symbol)

                # 判断条件并执行交易
                if close > open_price and (open_price - low) >= (2 * abs(close - open_price)):
                    logger.info(f"放量长下影线买入 for symbol: {symbol}, K线数据: {latest_kline}")
                    # 执行买入逻辑，可以调用相关函数   放量长上影线且阴线放量，做空卖出
                elif close < open_price and (high - open_price) >= (2 * abs(close - open_price)):
                    logger.info(f"放量长上影线卖出 for symbol: {symbol}, K线数据: {latest_kline}")
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