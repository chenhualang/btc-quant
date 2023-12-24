import requests
import json

class LarkNotifier:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None

    def get_access_token(self):
        url = f'https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/'
        headers = {'Content-Type': 'application/json'}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        access_token = response.json().get('app_access_token')
        return access_token

    def send_text_message(self, content):
        if not self.access_token:
            self.access_token = self.get_access_token()

        url = 'https://open.feishu.cn/open-apis/message/v4/send/'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        data = {
            "open_id": "",  # 如果需要指定用户，填写用户的 open_id
            "user_id": "",  # 如果需要指定用户，填写用户的 user_id
            "email": "",  # 如果需要指定用户，填写用户的 email
            "msg_type": "text",
            "content": {
                "text": content
            }
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        return response.json()

# 飞书应用配置信息
app_id = 'your_app_id'
app_secret = 'your_app_secret'

lark_notifier = LarkNotifier(app_id, app_secret)

# 示例：发送文本消息
message_content = '策略监测到符合买入卖出条件，符合策略要求。'
response = lark_notifier.send_text_message(message_content)
print(response)
