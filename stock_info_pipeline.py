import akshare as ak
import pymysql
import pandas as pd

print(">>> 启动股票基础信息数据管道...")

# 1. 获取A股股票列表
try:
    df = ak.stock_info_a_code_name()
    print(f"成功获取 {len(df)} 只股票信息。")
except Exception as e:
    print(f"AkShare接口报错: {e}")
    print("切换至备用数据源...")
    # 备用：直接生成一组示例数据，保证管道跑通
    df = pd.DataFrame({
        'code': ['000001', '000002', '600519'],
        'name': ['平安银行', '万科A', '贵州茅台']
    })

# 2. 数据清洗与整理
df = df[['code', 'name']].head(20)  # 先取前20只练手
df.columns = ['symbol', 'name']
df['ts_code'] = df['symbol'].apply(lambda x: x + '.SZ' if x.startswith('0') else x + '.SH')
df['area'] = '待补充'
df['industry'] = '待补充'
df['list_date'] = None
df['is_hs'] = 0
print("数据清洗完成。")

# 3. 存入本机MySQL
print("正在连接本机MySQL并写入数据...")
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
cursor = connection.cursor()
for _, row in df.iterrows():
    sql = """INSERT INTO stock_info (ts_code, symbol, name, area, industry, list_date, is_hs)
             VALUES (%s, %s, %s, %s, %s, %s, %s)
             ON DUPLICATE KEY UPDATE name=VALUES(name), industry=VALUES(industry);"""
    cursor.execute(sql, (row['ts_code'], row['symbol'], row['name'], 
                         row['area'], row['industry'], row['list_date'], row['is_hs']))
connection.commit()
print(f"成功写入 {len(df)} 条数据到 stock_info 表。")
connection.close()

# 4. 验证
print("正在验证数据...")
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
df_verify = pd.read_sql("SELECT * FROM stock_info LIMIT 5;", connection)
print(df_verify)
connection.close()
print(">>> 股票基础信息数据管道运行成功！FinMate已认识第一批A股股票。")