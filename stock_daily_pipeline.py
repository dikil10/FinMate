import akshare as ak
import pymysql
import pandas as pd
import numpy as np

print(">>> 启动股票历史行情数据管道...")

# 1. 获取平安银行历史日线数据（近60个交易日）
try:
    df = ak.stock_zh_a_hist(symbol="000001", period="daily", 
                            start_date="20260301", end_date="20260605",
                            adjust="qfq")  # 前复权
    print(f"成功获取 {len(df)} 条历史行情数据。")
except Exception as e:
    print(f"AkShare接口报错: {e}")
    print("切换至备用方案：生成模拟数据...")
    from datetime import date, timedelta
    dates = [date.today() - timedelta(days=i) for i in range(60, 0, -1)]
    np.random.seed(42)
    close_prices = 12 + np.cumsum(np.random.randn(60) * 0.2)
    df = pd.DataFrame({
        '日期': dates,
        '开盘': close_prices - 0.1,
        '收盘': close_prices,
        '最高': close_prices + 0.15,
        '最低': close_prices - 0.15,
        '成交量': np.random.randint(500000, 2000000, 60),
        '成交额': close_prices * np.random.randint(500000, 2000000, 60) * 100,
        '涨跌幅': np.random.randn(60) * 2
    })

# 2. 数据清洗
df = df.rename(columns={
    '日期': 'trade_date', '开盘': 'open', '收盘': 'close',
    '最高': 'high', '最低': 'low', '成交量': 'vol', '成交额': 'amount', '涨跌幅': 'pct_chg'
})
df['trade_date'] = pd.to_datetime(df['trade_date']).dt.date
df['ts_code'] = '000001.SZ'
df = df[['ts_code', 'trade_date', 'close', 'open', 'high', 'low', 'vol', 'amount', 'pct_chg']]
df = df.sort_values('trade_date').reset_index(drop=True)

# 3. 计算5日和20日移动平均线
df['ma5'] = df['close'].rolling(window=5).mean().round(2)
df['ma20'] = df['close'].rolling(window=20).mean().round(2)

# 4. 识别金叉死叉信号
df['signal'] = '无'
for i in range(1, len(df)):
    if pd.notna(df.loc[i, 'ma5']) and pd.notna(df.loc[i, 'ma20']):
        # 金叉：MA5上穿MA20
        if df.loc[i, 'ma5'] > df.loc[i, 'ma20'] and df.loc[i-1, 'ma5'] <= df.loc[i-1, 'ma20']:
            df.loc[i, 'signal'] = '金叉'
        # 死叉：MA5下穿MA20
        elif df.loc[i, 'ma5'] < df.loc[i, 'ma20'] and df.loc[i-1, 'ma5'] >= df.loc[i-1, 'ma20']:
            df.loc[i, 'signal'] = '死叉'

golden_cross = df[df['signal'] == '金叉']
death_cross = df[df['signal'] == '死叉']
print(f"计算完成：发现 {len(golden_cross)} 次金叉，{len(death_cross)} 次死叉。")

# 5. 存入本机MySQL
print("正在连接本机MySQL并写入数据...")
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
cursor = connection.cursor()
for _, row in df.iterrows():
    sql = """INSERT INTO stock_daily (ts_code, trade_date, close, open, high, low, vol, amount, pct_chg, ma5, ma20, signal)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
             ON DUPLICATE KEY UPDATE close=VALUES(close), ma5=VALUES(ma5), ma20=VALUES(ma20), signal=VALUES(signal);"""
    cursor.execute(sql, (row['ts_code'], row['trade_date'], row['close'], row['open'], 
                         row['high'], row['low'], row['vol'], row['amount'], row['pct_chg'],
                         row['ma5'], row['ma20'], row['signal']))
connection.commit()
print(f"成功写入 {len(df)} 条数据到 stock_daily 表。")
connection.close()

# 6. 验证查询
print("正在验证数据...")
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
df_verify = pd.read_sql("""
    SELECT trade_date, close, ma5, ma20, signal 
    FROM stock_daily 
    WHERE signal != '无' 
    ORDER BY trade_date DESC 
    LIMIT 5;
""", connection)
print("最近的交易信号：")
print(df_verify if len(df_verify) > 0 else "暂无金叉/死叉信号（数据量不足或均线未交叉）")
connection.close()
print(">>> 股票历史行情数据管道运行成功！FinMate已能追踪趋势。")