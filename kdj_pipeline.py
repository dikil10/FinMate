import pymysql, pandas as pd, numpy as np

print(">>> 启动 KDJ 指标计算管道...")

# 1. 读取收盘价和最高最低价
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
df = pd.read_sql("SELECT ts_code, trade_date, close, high, low FROM stock_daily ORDER BY trade_date;", connection)
connection.close()
print(f"读取 {len(df)} 条日线数据。")

# 2. 计算 KDJ (9,3,3)
# RSV = (close - 9日最低) / (9日最高 - 9日最低) * 100
low_min = df['low'].rolling(window=9).min()
high_max = df['high'].rolling(window=9).max()
rsv = ((df['close'] - low_min) / (high_max - low_min) * 100).fillna(50)

# 递推计算 K、D、J
k_list, d_list, j_list = [], [], []
for i in range(len(rsv)):
    if i == 0:
        k = 50.0
        d = 50.0
    else:
        k = k_list[-1] * 2/3 + rsv.iloc[i] * 1/3
        d = d_list[-1] * 2/3 + k * 1/3
    k_list.append(round(k, 2))
    d_list.append(round(d, 2))
    j_list.append(round(3*k - 2*d, 2))

df['k_value'] = k_list
df['d_value'] = d_list
df['j_value'] = j_list

# 3. 判断KDJ金叉死叉
df['kdj_signal'] = '无'
for i in range(1, len(df)):
    if df.loc[i, 'k_value'] > df.loc[i, 'd_value'] and df.loc[i-1, 'k_value'] <= df.loc[i-1, 'd_value']:
        df.loc[i, 'kdj_signal'] = '金叉'
    elif df.loc[i, 'k_value'] < df.loc[i, 'd_value'] and df.loc[i-1, 'k_value'] >= df.loc[i-1, 'd_value']:
        df.loc[i, 'kdj_signal'] = '死叉'

golden = df[df['kdj_signal'] == '金叉']
death = df[df['kdj_signal'] == '死叉']
print(f"计算完成：发现 {len(golden)} 次KDJ金叉，{len(death)} 次KDJ死叉。")

# 4. 更新数据库
print("正在更新数据库...")
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
cursor = connection.cursor()
# 如果 kdj_signal 列不存在，先添加
try:
    cursor.execute("ALTER TABLE stock_daily ADD COLUMN kdj_signal VARCHAR(10) COMMENT 'KDJ信号'")
    print("已添加 kdj_signal 列。")
except:
    pass

for _, row in df.iterrows():
    cursor.execute("""UPDATE stock_daily 
                      SET k_value=%s, d_value=%s, j_value=%s, kdj_signal=%s
                      WHERE ts_code=%s AND trade_date=%s;""",
                   (float(row['k_value']), float(row['d_value']), float(row['j_value']),
                    str(row['kdj_signal']), row['ts_code'], row['trade_date']))
connection.commit()
print(f"成功更新 {len(df)} 条KDJ数据。")
connection.close()

# 5. 验证
print("正在验证数据...")
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
df_verify = pd.read_sql("""
    SELECT trade_date, close, k_value, d_value, j_value, kdj_signal 
    FROM stock_daily 
    WHERE kdj_signal != '无' 
    ORDER BY trade_date DESC 
    LIMIT 5;
""", connection)
print("最近的KDJ信号：")
print(df_verify if len(df_verify) > 0 else "当前无KDJ金叉/死叉信号")
connection.close()
print(">>> KDJ指标计算管道运行成功！")