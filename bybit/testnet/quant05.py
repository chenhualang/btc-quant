import bybit
import time
import math
import requests
import pandas as pd
from datetime import datetime, timedelta
from dateutil import tz

# Bybit Testnet API Key and Secret
api_key = 'FtyBklKL3is4XWlZWS'
api_secret = '0QVMOut3yXx2R3MwdRLRzHAtQeKXwdFg2LJV'
BYBIT_ENDPOINT = "https://api-testnet.bybit.com"

bybit_api = bybit.bybit(test=True, api_key=api_key, api_secret=api_secret)
LOSS_RATIO = 0.05
SYMBOL = "BTCUSD"

# Initial order size and leverage
init_qty = 1000
init_leverage = 10

# Symbol to trade
symbol = 'BTCUSD'

# Time interval for data aggregation
interval = '1'

# Timeframe for technical indicators
timeframe = '15m'

# Stop loss percentage
stop_loss = 0.02

# API rate limit per minute
rate_limit = 50

# Bybit API client
client = bybit.bybit(test=True, api_key=api_key, api_secret=api_secret)

# Local time zone
local_tz = tz.tzlocal()

# Time delay between requests
time_delay = 60 / rate_limit

def get_data():
    # Get server time
    server_time = client.Common.Common_getTime().result()[0]['time_now']
    server_time = datetime.strptime(server_time, '%Y-%m-%d %H:%M:%S')

    # Get start time and end time for data aggregation
    end_time = server_time.replace(microsecond=0, second=0, minute=math.floor(server_time.minute / int(interval)) * int(interval))
    start_time = end_time - timedelta(minutes=int(interval))

    # Get K-line data
    kline = client.Kline.Kline_get(symbol=symbol, interval=interval, limit=2, **{'from': int(start_time.timestamp()), 'to': int(end_time.timestamp())}).result()[0]

    # Convert data to dataframe
    df = pd.DataFrame(kline, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Convert timestamp to datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    # Set timestamp as index
    df.set_index('timestamp', inplace=True)

    # Calculate technical indicators
    df['sma'] = df['close'].rolling(timeframe).mean()
    df['std'] = df['close'].rolling(timeframe).std()
    df['upper_band'] = df['sma'] + (2 * df['std'])
    df['lower_band'] = df['sma'] - (2 * df['std'])
    df['rsi'] = 100 - (100 / (1 + (df['close'].diff().fillna(0).apply(lambda x: x if x > 0 else 0).rolling(timeframe).mean() / df['close'].diff().fillna(0).apply(lambda x: abs(x)).rolling(timeframe).mean())))

    return df

def generate_auth_headers(http_method, api_path, api_secret):
    """Generate headers for authentication."""
    expires = int(time.time()) + 10
    signature = api_sign(api_secret, http_method, api_path, expires)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'{api_key}',
        'Expires': str(expires),
        'Signature': signature
    }
    return headers

def close_position():
    try:
        timestamp = int(time.time() * 1000)
        headers = {
            'Content-Type': 'application/json',
            'Referer': 'https://www.bybit.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299'
        }
        path = '/api/v5/position'
        params = f'symbol={SYMBOL}&api_key={api_key}&timestamp={timestamp}'
        pre_hash = path + str(timestamp) + params
        signature = hmac.new(api_secret.encode(), pre_hash.encode(), hashlib.sha256).hexdigest()
        url = BYBIT_ENDPOINT + path + '?' + params + '&sign=' + signature
        position_resp = requests.get(url, headers=headers)
        position_resp.raise_for_status()
        position_data = position_resp.json()['result'][0]
        if position_data['size'] > 0:
            order_resp = requests.post(f'{BYBIT_ENDPOINT}/api/v2/private/order/close-position', headers=headers, json={'symbol': SYMBOL})
            order_resp.raise_for_status()
            print('Close position!')
        elif position_data['size'] < 0:
            order_resp = requests.post(f'{BYBIT_ENDPOINT}/api/v2/private/order/close-position', headers=headers, json={'symbol': SYMBOL})
            order_resp.raise_for_status()
            print('Close position!')
        else:
            print('No position!')
    except requests.exceptions.RequestException as e:
        print(e)


def check_candle():
    try:
        klines = bybit_api.Kline.Kline_get(symbol=SYMBOL, interval='1', limit=2).result()[0]['result']
        if klines[0]['close'] > klines[1]['close']:
            return False
        else:
            return True
    except Exception as e:
        print(e)
        time.sleep(10)


def buy_position():
    try:
        url = f'{BYBIT_ENDPOINT}/v2/private/linear/order/create'
        params = {
            'api_key': api_key,
            'symbol': SYMBOL,
            'side': 'Buy',
            'order_type': 'Market',
            'qty': round((ACCOUNT_BALANCE * LEVERAGE * 0.7) / curr_price, 1)
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_secret}'
        }
        response = requests.post(url, headers=headers, params=params)
        if response.status_code == 200:
            print('Buy position!')
        else:
            print(response.json())
    except Exception as e:
        print(e)
        time.sleep(10)



# 4. 定义止损函数
def stop_loss():
    global current_pos, current_price
    if current_pos == 'Buy':
        loss_price = current_price * (1 - LOSS_RATIO)
    elif current_pos == 'Sell':
        loss_price = current_price * (1 + LOSS_RATIO)
    else:
        return
    tickers = bybit_api.get_tickers(SYMBOL)
    last_price = float(tickers[0]['last_price'])
    if (current_pos == 'Buy' and last_price <= loss_price) or (current_pos == 'Sell' and last_price >= loss_price):
        close_position(last_price)
        print(f"stop loss, price: {last_price}")

# 5. 定义主函数
def main():
    global current_pos, current_price, SYMBOL
    symbol_url = "https://api.bybit.com/v2/public/symbols"
    symbols = requests.get(symbol_url).json()['result']
    SYMBOL = symbols[0]['name']
    print(f'Starting trading on {SYMBOL}')
    while True:
        try:
            ticker_url = f"https://api.bybit.com/v2/public/tickers?symbol={SYMBOL}"
            tickers = requests.get(ticker_url).json()['result']
            last_price = float(tickers[0]['last_price'])
            if current_pos == '':
                if check_candle():
                    # 买入70%的仓位
                    buy_position(0.7, last_price)
            elif current_pos == 'Buy':
                # 检查止损
                stop_loss()
                # 判断是否达到10%的收益率
                if current_price * (1 + PROFIT_RATIO) <= last_price:
                    close_position(last_price)
                    print(f"sell, price: {last_price}")
            elif current_pos == 'Sell':
                # 检查止损
                stop_loss()
                # 判断是否达到10%的收益率
                if current_price * (1 - PROFIT_RATIO) >= last_price:
                    close_position(last_price)
                    print(f"buy, price: {last_price}")
            time.sleep(1)
        except Exception as e:
            print(e)
            time.sleep(10)


if __name__ == '__main__':
    PROFIT_RATIO = 0.1
    ACCOUNT_BALANCE = 69829.20  # 设定初始资金为69,829.20 USDT
    LEVERAGE = 5  # 设定杠杆倍数为5
    main()




# 在上面的代码中，我们定义了一个
# stop_loss
# 函数，用于检查是否需要进行止损。在主函数中，我们使用
# while 循环来不断获取当前的最新价格，并根据策略来执行交易操作。如果当前没有持仓，并且满足放量长下影线的条件，那么我们会使用 buy_position 函数来买入70 % 的仓位。如果当前持有多头仓位，并且满足卖出条件（即达到10 % 的收益率），那么我们会使用 close_position 函数来卖出所有持仓。如果当前持有空头仓位，并且满足买入条件（即达到10 % 的收益率），那么我们会使用 close_position 函数来买入所有持仓。在每个交易操作之前，我们会先使用 stop_loss 函数来检查是否需要进行止损操作。
#
# 请注意，这份代码需要您自己进行一些必要的配置，例如您需要将
# API_KEY
# 和
# SECRET_KEY
# 更改为您自己的
# Bybit
# API
# 密钥，并将
# SYMBOL
# 更改为您要交易的合约交易对。您还需要安装
# bybit





