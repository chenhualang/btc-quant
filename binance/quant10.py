import hmac
import json
import time
import hashlib
import requests

# 增加查询账户余额函数，并在main 方法中调用并打印输出

# API请求地址
API_URL = "https://testnet.binance.vision/api"

# API密钥（请勿泄露）
API_KEY = "kFnTdNxT4ZjKTyjYtZ4grjpWYlfvOb6l6GteFf4sARBdFe3sUApQA9mrF2sgB0N7"
API_SECRET = "praXZVYgy5erAXxgN2scw1PkyfExxt2UDlpfP2pKMSibcTKzMKIaO4uDmlzdJqWS"

# 生成签名
def generate_signature(query_string):
    return hmac.new(API_SECRET.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()

# 发送API请求
def send_signed_request(http_method, url_path, payload={}):
    # 获取当前时间戳
    timestamp = int(time.time() * 1000)
    # 生成签名所需的参数
    query_string = f"timestamp={timestamp}&recvWindow=5000"
    # 将payload中的参数加入query_string中
    for key, value in payload.items():
        query_string += f"&{key}={value}"
    # 加入API Key
    query_string += f"&apiKey={API_KEY}"
    # 生成签名并加入请求参数中
    signature = generate_signature(query_string)
    query_string += f"&signature={signature}"
    # 生成请求URL
    url = API_URL + url_path + "?" + query_string
    # 发送请求
    response = requests.request(http_method, url)
    # 解析响应数据
    return json.loads(response.text)

# 查询账户余额
def get_account_balance():
    # 发送请求
    response = send_signed_request("GET", "/v3/account")
    # 获取余额信息
    balances = {}
    for balance in response["balances"]:
        if float(balance["free"]) > 0 or float(balance["locked"]) > 0:
            balances[balance["asset"]] = {
                "free": float(balance["free"]),
                "locked": float(balance["locked"]),
            }
    # 返回余额信息
    return balances

# 主函数
def main():
    # 查询账户余额
    balances = get_account_balance()
    # 输出余额信息
    print("Account Balance:")
    for asset, balance in balances.items():
        print(f"{asset}: free {balance['free']}, locked {balance['locked']}")

if __name__ == "__main__":
    main()
