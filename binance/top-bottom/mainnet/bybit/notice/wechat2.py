import requests
import json

class WeChatNotifier:
    def __init__(self, corpid, corpsecret, agent_id):
        self.corpid = corpid
        self.corpsecret = corpsecret
        self.agent_id = agent_id
        self.access_token = None

    def get_access_token(self):
        url = f'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corpid}&corpsecret={self.corpsecret}'
        response = requests.get(url)
        access_token = response.json().get('access_token')
        return access_token

    def send_text_message(self, content):
        if not self.access_token:
            self.access_token = self.get_access_token()

        url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}'
        data = {
            "touser": "@all",  # 发送给所有人
            "toparty": "",
            "totag": "",
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {"content": content},
            "safe": 0
        }

        response = requests.post(url, data=json.dumps(data))
        return response.json()

# 企业微信配置信息
corpid = 'your_corpid'
corpsecret = 'your_corpsecret'
agent_id = 'your_agent_id'

wechat_notifier = WeChatNotifier(corpid, corpsecret, agent_id)

# 示例：发送文本消息
message_content = '策略监测到符合买入卖出条件，符合策略要求。'
response = wechat_notifier.send_text_message(message_content)
print(response)
