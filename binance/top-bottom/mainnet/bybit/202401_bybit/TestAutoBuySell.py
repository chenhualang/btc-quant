import json
import math
import threading
import random
from pybit.unified_trading import HTTP
from email1 import EmailSender
import logging
import time
import schedule
import concurrent.futures
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import traceback



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


class AutoBuySell:
    def __init__(self, part_ratio, coin_num, remaining_balance, profit_threshold, stop_loss_threshold, interval, latest_hour, volumn_spike_times, top_bottom_shadow_times, pending_order_scan_inteval, profit_loss_scan_inteval, kline_job_interval):

        self.part_ratio = part_ratio
        self.coin_num = coin_num
        self.remaining_balance = self.get_wallet_balance()
        self.profit_threshold = profit_threshold
        self.stop_loss_threshold = stop_loss_threshold
        self.interval = interval
        self.latest_hour = latest_hour
        self.volumn_spike_times = volumn_spike_times
        self.top_bottom_shadow_times = top_bottom_shadow_times
        self.pending_order_scan_inteval = pending_order_scan_inteval
        self.profit_loss_scan_inteval = profit_loss_scan_inteval
        self.kline_job_interval = kline_job_interval

    def is_volume_spike(self, symbol):
        # 获取最近6小时的K线数据
        limit = 60 / self.interval * self.latest_hour
        kline_data = session.get_kline(symbol=symbol,interval=self.interval,limit=limit)["result"]["list"]
        if len(kline_data) > 0:
            # 计算最近6小时内平均成交量
            average_volume = sum(float(kline[5]) for kline in kline_data) / len(kline_data)

            # 获取最新一次5分钟的K线数据
            current_kline = session.get_kline(symbol=symbol, interval=self.interval, limit=1)["result"]["list"][0]
            current_volume = float(current_kline[5])
            logger.info(f"币种: {symbol}, 最新成交量: {current_volume}, 最近6小时平均成交量: {average_volume}, 时间戳: {current_kline[0]}")
            # 判断是否放量
            if current_volume >= self.volumn_spike_times * average_volume:
                logger.info(f"满足放量条件，最近一次成交量是平均成交量的2倍以上, 币种: {symbol}, 时间: {self.convert_time(int(current_kline[0]))}, 最新成交量: {current_volume}, 最近6小时平均成交量: {average_volume}, 时间戳: {current_kline[0]}")
                return True

        return False

    def get_top_20_volume_symbols(self):
        tickers = session.get_tickers(category="linear", limit=100)["result"]["list"]
        tickers.sort(key=lambda x: float(x['turnover24h']), reverse=True)
        top_symbols = [ticker['symbol'] for ticker in tickers[:20]]
        return top_symbols

    def send_email_notification(self, action, symbol, info):
        # 你的邮箱地址和授权密码
        sender_email = "chenhualang_1988@sina.com"
        sender_password = "b1f3558e5244792f"
        # 邮件服务器的地址和端口（使用 sina 邮箱作为示例）
        smtp_server = "smtp.sina.com"
        smtp_port = 465  # 使用 SMTP_SSL，端口改为465
        # 接收邮件的邮箱地址
        receiver_email = "charliechen1207@gmail.com"
        # 邮件主题和内容
        if isinstance(info, dict) and "orderId" in info:
            subject = f"{action}币种 : {symbol}, 订单状态: {info['orderStatus']}"
            body = f"{action}币种 : {symbol}, 详细信息: {info}"
        elif isinstance(info, list):
            subject = f"{action}币种 : {symbol}, 时间: {self.convert_time(int(info[0]))}"
            body = f"{action}币种 : {symbol}, 详细信息: {info}"
        else:
            subject = f"{action} 数量 : {symbol}"
            body = f"{action}数量 : {symbol}, 详细信息: {info}"
        # 创建 EmailSender 实例
        email_sender = EmailSender(sender_email, sender_password, smtp_server, smtp_port)
        # 发送邮件
        email_sender.send_email(receiver_email, subject, body)

    def process_symbol(self, symbol):
        try:
            logger.info(f"Executing strategy for symbol: {symbol}")
            if float(self.remaining_balance) < 10:
                logger.info(f"钱包余额不足，请检查并账户充值划转，币种: {symbol}，钱包余额: {self.remaining_balance}")
                return
            # 获取最新K线数据
            kline_data = session.get_kline(category="linear", symbol=symbol, interval=self.interval)["result"]["list"]
            if len(kline_data) > 0:
                latest_kline = kline_data[0]
                open_price = float(latest_kline[1])
                high = float(latest_kline[2])
                low = float(latest_kline[3])
                volume = float(latest_kline[5])
                close = float(latest_kline[4])

                # 判断是否放量
                spike_flag = self.is_volume_spike(symbol)
                # 获取当前币种的市价
                market_price = self.get_coin_price(symbol)
                # 查询账户余额
                account_balance = self.get_wallet_balance()
                logging.info(f"binance 合约账户余额为:{account_balance}")

                # 判断条件并执行交易
                if spike_flag and close > open_price and (open_price - low) >= (self.top_bottom_shadow_times * abs(close - open_price)):
                    logger.info(f"放量长下影线买入 for symbol: {symbol}, K线数据: {latest_kline}")
                    self.send_email_notification("放量长下影线买入", symbol, latest_kline)
                    # 执行买入逻辑，可以调用相关函数   放量长下影线且阳线放量，做多买入
                    # side = "Buy"
                    # self.buy_in_multiple_parts(symbol, side, market_price, self.remaining_balance, self.coin_num)

                elif spike_flag and close < open_price and (high - open_price) >= (self.top_bottom_shadow_times * abs(close - open_price)):
                    logger.info(f"放量长上影线卖出 for symbol: {symbol}, K线数据: {latest_kline}")
                    self.send_email_notification("放量长上影线卖出", symbol, latest_kline)
                    # 执行卖出逻辑，可以调用相关函数     放量长上影线且阴线放量，做空卖出
                    # side = "Sell"
                    # self.buy_in_multiple_parts(symbol, side, market_price, self.remaining_balance, self.coin_num)
                else:
                    logger.info(f"不满足做多做空条件，继续等待 for symbol: {symbol}")
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Error occurred for symbol: {symbol}, Error message: {str(e)}, Traceback: {tb}")

    def buy_in_multiple_parts(self, symbol, side, market_price, remaining_balance, coin_num):
        # 计算本次购买的比例
        ratio = self.part_ratio[self.coin_num]
        # 计算本次购买的金额
        buy_amount = float(self.remaining_balance) * ratio
        # 计算本次购买的数量
        buy_quantity = buy_amount / market_price
        buy_quantity = math.ceil(buy_quantity)

        # 下单购买
        self.place_order(symbol, side, market_price, buy_quantity)
        # self.remaining_balance -= buy_amount
        self.remaining_balance = str(
            float(self.remaining_balance) - buy_amount)  # Convert to float and subtract buy_amount
        self.coin_num += 1
        return self.remaining_balance, self.coin_num

    def get_coin_price(self, symbol):
        # symbol = 'BTCUSDT'
        # 查詢最新行情信息, GET / v5 / market / tickers, https: // bybit - exchange.github.io / docs / zh - TW / v5 / market / tickers
        price_data = session.get_tickers(category="linear", symbol=symbol)["result"]["list"][0]
        # 这里取的是lastPrice,最新市场成交价
        last_price = float(price_data['lastPrice'])
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"币种:{symbol}, 当前时间：{current_time}, 当前最新成交价为: {last_price}")
        return last_price

    def get_wallet_balance(self):
        # 获取账户余额
        wallet_balance = session.get_wallet_balance(accountType="CONTRACT", coin="USDT")["result"]["list"][0]
        logger.info(f"账户余额为: {wallet_balance}")
        # 目前简单处理，获取第一个币种的余额，这里第一个币种为USDT
        usdt_balance = wallet_balance['coin'][0]['equity']
        logger.info(f"账户余额为: {usdt_balance}")
        return usdt_balance

    def get_order_status(self, symbol):
        # 查询订单状态
        order_result = session.get_open_orders(
            category="linear",
            symbol=symbol,
            openOnly=0,
        )
        return order_result

    def get_pending_orders_status(self):
        # 查询订单状态
        order_result = session.get_open_orders(
            category="linear",
            settleCoin="USDT",
            openOnly=0,
        )
        return order_result

    def place_order(self, symbol, side, market_price, buy_quantity):
        # 测试买入功能
        order_result = session.place_order(
            category="linear",
            symbol=symbol,
            side=side,
            orderType="Limit",
            qty=buy_quantity,
            price=market_price,
            isLeverage=0,
            orderFilter="Order",
            # takeProfit=target_price,
            # stopLoss=stop_loss_price,
        )
        logger.info(f"下单结果: {order_result}")
        return order_result
         #   下单测试成功
         #     下单结果: {'retCode': 0, 'retMsg': 'OK', 'result': {'orderId': '4e179fcb-d35b-4fe3-97a0-90bf5e4b86ed', 'orderLinkId': ''}, 'retExtInfo': {}, 'time': 1704784349475}

    def take_profit_loss(self, position):
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
            target_price = float(avgPrice) * (1 + self.profit_threshold)
            stop_loss_price = float(avgPrice) * (1 - self.stop_loss_threshold)
        elif side == "Sell":
            # 计算止盈和止损价格
            target_price = float(avgPrice) * (1 - self.profit_threshold)
            stop_loss_price = float(avgPrice) * (1 + self.stop_loss_threshold)
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
                    result = session.place_order(
                        category="linear",
                        symbol=symbol,
                        side="Sell",
                        orderType="Market",
                        qty=size,
                        isLeverage=0,
                    )
                    if result["retCode"] == 0:
                        logger.info(f"多仓止盈卖出成功，币种: {symbol}")
                elif side == "Sell":
                    logger.info(f"空仓止盈买入，币种: {symbol}")
                    result = session.place_order(
                        category="linear",
                        symbol=symbol,
                        side="Buy",
                        orderType="Market",
                        qty=size,
                        isLeverage=0,
                    )
                    if result["retCode"] == 0:
                        logger.info(f"空仓止盈买入成功，币种: {symbol}")
                reached_target_price = True
                break

            if (side == "Buy" and float(current_price) <= stop_loss_price) or (
                    side == "Sell" and float(current_price) >= stop_loss_price):
                # 达到止损价格，平仓
                if side == "Buy":
                    logger.info(f"多仓止损卖出，币种: {symbol}")
                    result = session.place_order(
                        category="linear",
                        symbol=symbol,
                        side="Sell",
                        orderType="Market",
                        qty=size,
                        isLeverage=0,
                    )
                    if result["retCode"] == 0:
                        logger.info(f"多仓止损卖出成功，币种: {symbol}")
                elif side == "Sell":
                    logger.info(f"空仓止损买入，币种: {symbol}")
                    result = session.place_order(
                        category="linear",
                        symbol=symbol,
                        side="Buy",
                        orderType="Market",
                        qty=size,
                        isLeverage=0,
                    )
                    if result["retCode"] == 0:
                        logger.info(f"空仓止损买入成功，币种: {symbol}")
                reached_target_price = True
                break

            # 每隔一段时间检查一次价格
            time.sleep(self.profit_loss_scan_inteval)

    def monitor_positions(self, positions):
        # 创建一个线程列表
        logger.info(f"开始多线程监控所有持仓币种")
        threads = []
        for position in positions:
            # 创建一个线程，并将take_profit_loss函数作为目标函数
            thread = threading.Thread(target=self.take_profit_loss, args=(position,))
            threads.append(thread)

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程结束
        for thread in threads:
            thread.join()

    def get_position(self):
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

    def convert_time(self, timestamp):
        # timestamp = 1673349000000
        # 根据毫秒时间戳创建datetime对象
        dt = datetime.datetime.fromtimestamp(timestamp / 1000)

        # 格式化datetime对象为指定格式
        formatted_datetime = dt.strftime('%Y-%m-%d %H:%M:%S')

        print(formatted_datetime)
        return dt

    def convert_json(self, map):
        s = json.dumps(map)
        logger.info(f"转换后的json字符串为: {s}")
        return s

    def get_order_status_job(self):
        last_pending_orders = []
        email_sent = False

        while True:
            result = self.get_pending_orders_status()
            pending_orders = result["result"]["list"]
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if len(pending_orders) >= 2 and not email_sent:
                logger.error(f"当前挂单数量为: {len(pending_orders)}, 请改为手动成交或取消，时间: {current_time}")
                self.send_email_notification("当前挂单数量过大", len(pending_orders), "请改为手动成交或取消")
                email_sent = True

            filled_orders = [order for order in last_pending_orders if order not in pending_orders]
            for order in filled_orders:
                symbol = order["symbol"]
                qty = order["qty"]
                side = order["side"]
                order_id = order["orderId"]
                logger.info(f"订单: {order_id} 已成交，币种: {symbol}, 成交数量: {qty}, 方向: {side}，成交时间: {current_time}")
                self.send_email_notification("订单已成交", symbol, order+"成交时间:"+current_time)

            last_pending_orders = pending_orders
            time.sleep(1)

    def run_scheduler(self):
        # 每10秒执行一次定时任务
        schedule.every(self.pending_order_scan_inteval).seconds.do(self.get_order_status_job)

        while True:
            schedule.run_pending()
            time.sleep(1)

    def job(self):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Job is running at {current_time}")
        logger.info(f"Job is running at: {current_time}")
        self.auto_buy_sell()

    def start_scheduler(self):
        # 创建调度器
        scheduler = BlockingScheduler()

        # 在每个5分钟的最后30秒执行任务
        scheduler.add_job(self.job, 'cron', minute=self.kline_job_interval, second='30')

        # 开始调度器
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            # 如果有中断信号（如 Ctrl+C），停止调度器
            scheduler.shutdown()

    def auto_buy_sell(self):
        # 获取24h成交量最高的20个币
        symbols = self.get_top_20_volume_symbols()
        # symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'LTCUSDT']  # 你需要监控的币种列表
        logger.info(f"24h成交量最高的20个币: {symbols}")

        while True:
            # 执行监控任务
            # process_symbols(symbols)

            start_time = time.time()
            # 使用ThreadPoolExecutor进行并行处理
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(self.process_symbol, symbols)

            end_time = time.time()
            elapsed_time = end_time - start_time
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            random_sleep_time = random.uniform(10, 30)
            logger.info(
                f"时间: {formatted_time} - 扫描完一次20个币对，耗时: {elapsed_time}秒，随机休眠一段时间后继续扫描，休眠时间: {random_sleep_time}秒")
            time.sleep(random_sleep_time)  # 随机休眠60-120秒


if __name__ == '__main__':
    part_ratio = [1 / 3, 1 / 2, 1]  # 三次下单比例
    coin_num = 0  # 持仓币种数量
    remaining_balance = 0  # 余额

    profit_threshold = 0.02  # 盈利2%
    stop_loss_threshold = 0.02  # 止损2%

    interval = 5  # 间隔时间，5分钟K线级别，还是15 分钟K线级别
    latest_hour = 1 # 最近几个小时的K线数据

    volumn_spike_times = 2  # 成交量放量几倍
    top_bottom_shadow_times = 2  # 上线影线是实体长度的几倍

    pending_order_scan_inteval = 30  # 定时任务执行间隔时间，单位秒   每隔10秒扫描未成交订单状态
    profit_loss_scan_inteval = 3  # 止盈止损定时任务执行间隔时间，单位秒   每隔3秒止盈止损
    kline_job_interval = '4-59/5'  # K线定时任务执行间隔时间，单位分钟   每隔5/15分钟扫描K线   '4-59/5'  '14-59/15'

    auto_buy_sell = AutoBuySell(part_ratio, coin_num, remaining_balance, profit_threshold, stop_loss_threshold, interval, latest_hour, volumn_spike_times, top_bottom_shadow_times, pending_order_scan_inteval, profit_loss_scan_inteval, kline_job_interval)
    # auto_buy_sell.main()

    # auto_buy_sell.get_coin_price()

    # auto_buy_sell.get_wallet_balance()

    # result = auto_buy_sell.place_order(symbol="ADAUSDT", side="Buy", market_price="0.575", buy_quantity=10)
    # result = auto_buy_sell.place_order(symbol="SUIUSDT", side="Buy", market_price="1.16", buy_quantity=20)
    # result = auto_buy_sell.place_order(symbol="XRPUSD", side="Buy", market_price="0.598", buy_quantity=25)
    # logger.info(f"下单买入结果: {result}")

    # result = auto_buy_sell.get_order_status("XRPUSDT")
    # s = auto_buy_sell.convert_json(result)
    # logger.info(f"仓位信息: {s}")

    # auto_buy_sell.convert_time(1704727800000)

    # auto_buy_sell.send_email_notification("放量长上影线卖出", "BTCUSDT", "2024-01-01 19:20:00")

    # auto_buy_sell.get_position()

    # auto_buy_sell.take_profit_loss()

    # 调用函数开始监控持仓
    # positions = auto_buy_sell.get_position()
    # auto_buy_sell.monitor_positions(positions)

    # auto_buy_sell.buy_in_multiple_parts("BLURUSDT", "Buy", 0.6192, 15)
    # auto_buy_sell.buy_in_multiple_parts("SEIUSDT", "Buy", 0.70495,15,0)
    # auto_buy_sell.buy_in_multiple_parts("XRPUSDT", "Buy", 0.5749, 15)

    # 定时任务扫描未成交订单状态，如发现有很多未成交订单，邮件通知一次；如有订单成交，邮件通知一次
    # auto_buy_sell.run_scheduler()

    # result = auto_buy_sell.get_pending_orders_status()
    # s = auto_buy_sell.convert_json(result)
    # logger.info(f"委托订单(待成交订单)信息: {s}")

    # 在每个5分钟的最后30秒执行任务   scheduler.add_job(self.job, 'cron', minute='4-59/5', second='30')
    # auto_buy_sell.start_scheduler()

    # 开启自动买卖定时任务，在每个5分钟的最后30秒执行任务   4分30秒、9分30秒、14分30秒、...、59分30秒执行任务
    auto_buy_sell.start_scheduler()
    # 定时任务扫描未成交订单状态，如发现有很多未成交订单，邮件通知一次；如有订单成交，邮件通知一次  每隔30秒执行一次
    # auto_buy_sell.run_scheduler()
    # 调用函数开始监控持仓，进行止盈止损逻辑  每隔3秒执行一次
    # positions = auto_buy_sell.get_position()
    # auto_buy_sell.monitor_positions(positions)
