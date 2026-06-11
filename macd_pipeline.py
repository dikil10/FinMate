import pymysql
import pandas as pd
import numpy as np

print(">>> 启动MACD指标计算管道...")

# 1. 从数据库读取已有的日线数据
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
df = pd.read_sql("SELECT ts_code, trade_date, close FROM stock_daily ORDER BY trade_date;", connection)
connection.close()
print(f"读取 {len(df)} 条日线数据。")

# 2. 计算MACD指标
# EMA(12) 和 EMA(26)
df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
# DIF = EMA12 - EMA26
df['dif'] = (df['ema12'] - df['ema26']).round(4)
# DEA = DIF的9日EMA
df['dea'] = df['dif'].ewm(span=9, adjust=False).mean().round(4)
# MACD柱 = DIF - DEA
df['macd_bar'] = (df['dif'] - df['dea']).round(4)

# 识别MACD金叉死叉
df['macd_signal'] = '无'
for i in range(1, len(df)):
    if pd.notna(df.loc[i, 'dif']) and pd.notna(df.loc[i, 'dea']):
        if df.loc[i, 'dif'] > df.loc[i, 'dea'] and df.loc[i-1, 'dif'] <= df.loc[i-1, 'dea']:
            df.loc[i, 'macd_signal'] = '金叉'
        elif df.loc[i, 'dif'] < df.loc[i, 'dea'] and df.loc[i-1, 'dif'] >= df.loc[i-1, 'dea']:
            df.loc[i, 'macd_signal'] = '死叉'

golden = df[df['macd_signal'] == '金叉']
death = df[df['macd_signal'] == '死叉']
print(f"MACD计算完成：发现 {len(golden)} 次金叉，{len(death)} 次死叉。")

# 3. 更新到数据库
print("正在更新数据库...")
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
cursor = connection.cursor()
for _, row in df.iterrows():
    sql = """UPDATE stock_daily 
             SET dif=%s, dea=%s, macd_bar=%s
             WHERE ts_code=%s AND trade_date=%s;"""
    cursor.execute(sql, (row['dif'], row['dea'], row['macd_bar'], 
                         row['ts_code'], row['trade_date']))
connection.commit()
print(f"成功更新 {len(df)} 条MACD数据。")
connection.close()

# 4. 验证
print("正在验证数据...")
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
df_verify = pd.read_sql("""
    SELECT trade_date, close, dif, dea, macd_bar 
    FROM stock_daily 
    WHERE dif IS NOT NULL 
    ORDER BY trade_date DESC 
    LIMIT 5;
""", connection)
print(df_verify)
connection.close()
print(">>> MACD指标计算管道运行成功！FinMate已能追踪动量变化。")