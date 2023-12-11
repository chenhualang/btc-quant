import pandas as pd

def main():
    # 读取Excel文件
    df = pd.read_excel('/Users/hk00068ml/Downloads/data.xlsx', sheet_name='sheet1')

    # 构造SQL语句
    sql = 'UPDATE admin_withdraws_switch_config\nSET aml_withdraw_fee = CASE\n'
    for index, row in df.iterrows():
        coin = row['coin']
        coin_chain = row['coin_chain']
        aml_withdraw_fee = row['aml_withdraw_fee']
        sql += f"    WHEN coin = '{coin}' AND coin_chain = '{coin_chain}' THEN {aml_withdraw_fee}\n"

    sql += '    ELSE aml_withdraw_fee\nEND\n'
    sql += 'WHERE (coin, coin_chain) IN (\n'
    for index, row in df.iterrows():
        coin = row['coin']
        coin_chain = row['coin_chain']
        sql += f"    ('{coin}', '{coin_chain}'),\n"

    sql = sql[:-2] + ')'

    # 打印SQL语句
    print(sql)

    # 将SQL语句写入文件
    with open('/Users/hk00068ml/Downloads/update.sql', 'w') as f:
        f.write(sql)

if __name__ == '__main__':
    main()