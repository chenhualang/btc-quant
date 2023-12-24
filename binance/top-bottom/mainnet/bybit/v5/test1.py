from pybit.unified_trading import HTTP
from ..notice.email1 import EmailSender
import concurrent.futures
import logging

session = HTTP(
    testnet=False,
    api_key="GeS2xzvYScxnIjWEOU",
    api_secret="2JDubktuzxTvzkqE0AozIRcL5SByUrotzcCx",
)

# logging.basicConfig(level=logging.INFO)  # 设置日志级别为INFO，可以根据需要调整级别    本地运行用这个


def is_volume_spike(symbol):
    # 获取最近6小时的K线数据
    kline_data = session.get_kline(symbol=symbol,interval=5,limit=72)
    if len(kline_data) > 0:
        # 计算最近6小时内平均成交量
        average_volume = sum(float(kline['volume']) for kline in kline_data) / len(kline_data)

        # 获取最新一次15分钟的K线数据
        current_kline = session.get_kline(symbol, '5', limit=1)[-1]
        current_volume = float(current_kline['volume'])

        # 判断是否放量
        if current_volume >= 2 * average_volume:
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



# 主函数
if __name__ == '__main__':
    trade_quantity = 0.3  # 三成仓位
    profit_threshold = 0.02  # 盈利2%
    stop_loss_threshold = 0.02  # 止损2%

    # 获取24h成交量最高的20个币
    symbols = get_top_20_volume_symbols()
    logging.info(f"24h成交量最高的20个币: {symbols}")


    def process_symbol(symbol):
        try:
            logging.info(f"Executing strategy for symbol: {symbol}")
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

                # 判断条件并执行交易
                if spike_flag and (high - close) >= (3 * (close - low)):
                    logging.info(f"放量长下影线买入 for symbol: {symbol}")
                    send_email_notification("放量长下影线买入", symbol)
                elif spike_flag and close > open_price and (high - close) >= (3 * (close - low)):
                    logging.info(f"放量长上影线卖出 for symbol: {symbol}")
                    send_email_notification("放量长上影线卖出", symbol)
                else:
                    logging.info('不满足做多做空条件，继续等待')
        except Exception as e:
            logging.info(f"Error occurred for symbol: {symbol}")
            logging.info(f"Error message: {str(e)}")


    # 使用多线程处理每个币种
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(process_symbol, symbols)