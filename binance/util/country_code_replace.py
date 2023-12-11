import json


def main():
    # 从txt文件中读取JSON字符串
    with open('/Users/hk00068ml/Downloads/CountryCode.txt', 'r') as file:
        json_str = file.read()

    # 解析JSON字符串
    data = json.loads(json_str)

    # 提取code字段的值
    codes = [item['code'] for item in data['result']]

    # 拼接新的字符串
    result_str = '{"language":[],"nation":' + json.dumps(codes) + '}'

    # 输出结果
    print(result_str)

if __name__ == '__main__':
    main()