import akshare as ak
import pymysql
import pandas as pd
from datetime import date

print(">>> 启动公开市场操作数据管道...")

# 1. 尝试从AkShare获取数据
try:
    df = ak.macro_china_open_market_operation()
    df = df[['操作日期', '操作方式', '期限', '投放量', '逆回购利率']].tail(20)
    df.columns = ['record_date', 'operation_type', 'maturity_days', 'amount_billion_yuan', 'rate_percent']
    # 清洗数据
    df['amount_billion_yuan'] = df['amount_billion_yuan'].astype(str).str.replace(',', '')
    df['amount_billion_yuan'] = pd.to_numeric(df['amount_billion_yuan'], errors='coerce').fillna(0)
    df['maturity_days'] = pd.to_numeric(df['maturity_days'], errors='coerce').fillna(0).astype(int)
    df['rate_percent'] = pd.to_numeric(df['rate_percent'], errors='coerce').fillna(0)
    df['record_date'] = pd.to_datetime(df['record_date']).dt.date
    print(f"成功获取 {len(df)} 条公开市场操作记录。")
except Exception as e:
    print(f"AkShare接口报错: {e}")
    print("使用模拟数据...")
    # 模拟最近5天的逆回购操作
    from datetime import timedelta
    dates = [date.today() - timedelta(days=i) for i in range(5)]
    df = pd.DataFrame({
        'record_date': dates,
        'operation_type': ['逆回购'] * 5,
        'maturity_days': [7] * 5,
        'amount_billion_yuan': [100, 200, 150, 200, 100],
        'rate_percent': [1.80] * 5
    })

# 2. 存入MySQL
print("正在连接本机MySQL并写入数据...")
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
cursor = connection.cursor()
for _, row in df.iterrows():
    sql = """INSERT INTO open_market_ops (record_date, operation_type, maturity_days, amount_billion_yuan, rate_percent)
             VALUES (%s, %s, %s, %s, %s)
             ON DUPLICATE KEY UPDATE amount_billion_yuan=VALUES(amount_billion_yuan), rate_percent=VALUES(rate_percent);"""
    cursor.execute(sql, (row['record_date'], row['operation_type'], row['maturity_days'], 
                         row['amount_billion_yuan'], row['rate_percent']))
connection.commit()
print(f"成功写入 {len(df)} 条数据到 open_market_ops 表。")
connection.close()

# 3. 验证
print("正在验证数据...")
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
df_verify = pd.read_sql("SELECT * FROM open_market_ops ORDER BY record_date DESC LIMIT 5;", connection)
print(df_verify)
connection.close()
print(">>> 公开市场操作数据管道运行成功！")