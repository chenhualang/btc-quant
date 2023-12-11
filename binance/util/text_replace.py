import re



def main():
    # 读取文件内容
    with open('/Users/hk00068ml/Downloads/rediskey.txt', 'r') as file:
        content = file.read()

    # 使用正则表达式替换文本
    new_content = re.sub(r'\d+\)\s+"wallet-admin:', 'unlink ', content)
    new_content = re.sub(r'-\w+"', '', new_content)

    # 将修改后的内容写回文件
    with open('/Users/hk00068ml/Downloads/rediskey.txt', 'w') as file:
        file.write(new_content)

if __name__ == '__main__':
    main()