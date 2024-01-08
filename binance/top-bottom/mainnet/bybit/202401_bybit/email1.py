import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import imaplib

class EmailSender:
    def __init__(self, sender_email, sender_password, smtp_server, smtp_port):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send_email(self, receiver_email, subject, body):
        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        ctx = ssl._create_unverified_context()  # 起到忽略证书校验的作用
        ctx.set_ciphers('DEFAULT')  # 与老服务器握手搭配

        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=ctx) as server:
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, receiver_email, message.as_string())

if __name__ == "__main__":
    # 你的邮箱地址和授权密码
    sender_email = "chenhualang_1988@sina.com"
    sender_password = "b1f3558e5244792f"

    # 邮件服务器的地址和端口（使用 sina 邮箱作为示例）
    smtp_server = "smtp.sina.com"
    smtp_port = 465  # 使用 SMTP_SSL，端口改为465

    # 接收邮件的邮箱地址
    receiver_email = "charliechen1207@gmail.com"

    # 邮件主题和内容
    subject = "Test Email"
    body = "Hello, world!"

    # 创建 EmailSender 实例
    email_sender = EmailSender(sender_email, sender_password, smtp_server, smtp_port)

    # 发送邮件
    email_sender.send_email(receiver_email, subject, body)

    print("Email sent successfully!")
