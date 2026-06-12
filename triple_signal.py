import pymysql, pandas as pd

print('>>> 启动三重确认信号引擎...')

conn = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
df = pd.read_sql('SELECT ts_code, trade_date, close, k_value, d_value, j_value, kdj_signal, rsi_14, rsi_status, bb_upper, bb_lower, bb_mid FROM stock_daily ORDER BY trade_date;', conn)
conn.close()
print(f'读取 {len(df)} 条数据。')

df['triple_signal'] = '无'
for i in range(len(df)):
    if pd.isna(df.loc[i, 'k_value']) or pd.isna(df.loc[i, 'rsi_14']) or pd.isna(df.loc[i, 'bb_lower']):
        continue
    close = df.loc[i, 'close']
    kdj_sig = df.loc[i, 'kdj_signal']
    rsi_val = df.loc[i, 'rsi_14']
    bb_upper = df.loc[i, 'bb_upper']
    bb_lower = df.loc[i, 'bb_lower']
    if kdj_sig == '金叉' and rsi_val <= 30 and close <= bb_lower * 1.02:
        df.loc[i, 'triple_signal'] = '强买入'
    elif kdj_sig == '死叉' and rsi_val >= 70 and close >= bb_upper * 0.98:
        df.loc[i, 'triple_signal'] = '强卖出'

triple = df[df['triple_signal'] != '无']
print(f'三重信号: {len(triple)} 条')

conn = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
cur = conn.cursor()
try:
    cur.execute('ALTER TABLE stock_daily ADD COLUMN triple_signal VARCHAR(100)')
except:
    pass
for _, row in df.iterrows():
    cur.execute('UPDATE stock_daily SET triple_signal=%s WHERE ts_code=%s AND trade_date=%s', (str(row['triple_signal']), row['ts_code'], row['trade_date']))
conn.commit()
conn.close()
print('数据库更新完成。')
if len(triple) > 0:
    for _, row in triple.iterrows():
        print(f'{row.trade_date} | {row.close:.2f} | {row.triple_signal}')
else:
    print('当前无三重确认信号（信号严格，属正常）')
print('>>> 执行完毕！')
