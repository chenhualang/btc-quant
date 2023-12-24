import itchat

def send_message(message):
    # 获取自己的微信账号信息
    myself = itchat.search_friends()
    # 发送消息给自己的微信账号
    itchat.send(message, toUserName=myself[0]['UserName'])

if __name__ == '__main__':
    itchat.auto_login()
    message = input("请输入要发送的消息：")
    send_message(message)