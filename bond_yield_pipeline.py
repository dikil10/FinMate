import pymysql
import pandas as pd
from datetime import date, timedelta

print(">>> 启动国债收益率数据管道（模拟数据验证模式）...")

# 1. 生成最近30天的模拟国债收益率数据
base_date = date.today() - timedelta(days=1)
dates = [base_date - timedelta(days=i) for i in range(30)]
yield_10y = [2.85 - i*0.005 + (i%5)*0.01 for i in range(30)]
yield_6m = [2.30 - i*0.002 + (i%4)*0.01 for i in range(30)]
spread = [y10 - y6 for y10, y6 in zip(yield_10y, yield_6m)]

df = pd.DataFrame({
    'record_date': dates,
    'yield_10y': yield_10y,
    'yield_6m': yield_6m,
    'spread': spread
})
print("模拟数据生成完成。")

# 2. 存入本机MySQL
print("正在连接本机MySQL并写入数据...")
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
cursor = connection.cursor()
for _, row in df.iterrows():
    sql = """INSERT INTO china_bond_yield (record_date, yield_10y, yield_6m, spread)
             VALUES (%s, %s, %s, %s)
             ON DUPLICATE KEY UPDATE yield_10y=VALUES(yield_10y), yield_6m=VALUES(yield_6m), spread=VALUES(spread);"""
    cursor.execute(sql, (row['record_date'], row['yield_10y'], row['yield_6m'], row['spread']))
connection.commit()
print(f"成功写入 {len(df)} 条数据到 china_bond_yield 表。")
connection.close()

# 3. 验证查询
print("正在验证数据...")
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
df_verify = pd.read_sql("SELECT * FROM china_bond_yield ORDER BY record_date DESC LIMIT 5;", connection)
print(df_verify)
connection.close()
print(">>> 国债收益率数据管道运行成功！（模拟数据模式）")

# 4. 导出CSV
df.to_csv('bond_yield_latest.csv', index=False)
print("CSV已导出为 bond_yield_latest.csv，准备上传HDFS。")