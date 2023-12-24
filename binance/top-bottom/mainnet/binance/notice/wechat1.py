import requests
import json

#todo: 1. 从微信公众平台获取app_id和app_secret

def send_wechat_message(app_id, app_secret, template_id, openid, data):
    access_token = get_access_token(app_id, app_secret)
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    payload = {
        "touser": openid,
        "template_id": template_id,
        "data": data
    }
    response = requests.post(url, json=payload)
    response_json = response.json()
    if response.status_code == 200 and response_json["errcode"] == 0:
        print("消息发送成功")
    else:
        print("消息发送失败")

def get_access_token(app_id, app_secret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    response = requests.get(url)
