import pymysql
import pandas as pd
import numpy as np
from datetime import date, timedelta

print(">>> FinMate 数据管道（全自动版）启动...")

# ---------- 1. 生成模拟股票日线数据 ----------
print("[1/3] 生成股票日线数据...")
dates = [date.today() - timedelta(days=i) for i in range(60, 0, -1)]
np.random.seed(42)
close_prices = (12 + np.cumsum(np.random.randn(60) * 0.2)).round(2)

df = pd.DataFrame({
    'ts_code': '000001.SZ',
    'trade_date': dates,
    'close': close_prices,
    'open': (close_prices - np.random.uniform(0.05, 0.15, 60)).round(2),
    'high': (close_prices + np.random.uniform(0.05, 0.20, 60)).round(2),
    'low': (close_prices - np.random.uniform(0.05, 0.20, 60)).round(2),
    'vol': np.random.randint(500000, 2000000, 60),
    'amount': (close_prices * np.random.randint(500000, 2000000, 60) * 100).round(2),
    'pct_chg': np.random.randn(60).round(4)
})

df['ma5'] = df['close'].rolling(5).mean().fillna(0).round(2)
df['ma20'] = df['close'].rolling(20).mean().fillna(0).round(2)
df['signal'] = '无'

for i in range(1, len(df)):
    if df.loc[i, 'ma5'] > df.loc[i, 'ma20'] and df.loc[i-1, 'ma5'] <= df.loc[i-1, 'ma20']:
        df.loc[i, 'signal'] = '金叉'
    elif df.loc[i, 'ma5'] < df.loc[i, 'ma20'] and df.loc[i-1, 'ma5'] >= df.loc[i-1, 'ma20']:
        df.loc[i, 'signal'] = '死叉'

df = df.replace([np.inf, -np.inf], 0).fillna(0)
df['signal'] = df['signal'].astype(str)

# ---------- 2. 写入 MySQL ----------
print("[2/3] 写入 MySQL 数据库...")
conn = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
cur = conn.cursor()
cur.execute("DELETE FROM stock_daily")

# 注意：`signal` 是 MySQL 保留字，必须用反引号包围
sql = "INSERT INTO stock_daily (ts_code, trade_date, close, open, high, low, vol, amount, pct_chg, ma5, ma20, `signal`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

for _, row in df.iterrows():
    cur.execute(sql, tuple(row))

conn.commit()
print(f"   成功写入 {len(df)} 条日线数据。")

# ---------- 3. 成交量分析 + 量价诊断 ----------
print("[3/3] 进行成交量分析与量价诊断...")

# 计算5日均量
df['ma_vol5'] = df['vol'].rolling(5).mean().fillna(0).round(0).astype(int)
df['vol_status'] = '平量'
for i in range(len(df)):
    if df.loc[i, 'ma_vol5'] == 0:
        continue
    ratio = df.loc[i, 'vol'] / df.loc[i, 'ma_vol5']
    if ratio >= 1.5:
        df.loc[i, 'vol_status'] = '放量'
    elif ratio <= 0.7:
        df.loc[i, 'vol_status'] = '缩量'

# 更新成交量字段
for _, row in df.iterrows():
    cur.execute("UPDATE stock_daily SET ma_vol5=%s, vol_status=%s WHERE ts_code=%s AND trade_date=%s",
                (int(row['ma_vol5']), row['vol_status'], row['ts_code'], row['trade_date']))
conn.commit()

# 量价诊断（最新一天）
latest = df.iloc[-1]
is_up = latest['pct_chg'] > 0
direction = "上涨" if is_up else "下跌" if latest['pct_chg'] < 0 else "平盘"
vol_status = latest['vol_status']

if is_up and vol_status == '放量':
    diagnosis = "价涨量增，买盘踊跃，趋势大概率延续。"
    action = "🟢 看涨信号较强，可持股或适量跟进。"
elif is_up and vol_status == '缩量':
    diagnosis = "价涨量缩，上涨缺乏资金支持，可能为诱多。"
    action = "🟡 谨慎看涨，不宜追高，注意见顶风险。"
elif not is_up and vol_status == '放量':
    diagnosis = "价跌量增，恐慌盘涌出，短期抛压较重。"
    action = "🔴 建议观望或减仓，等待企稳信号。"
elif not is_up and vol_status == '缩量':
    diagnosis = "价跌量缩，卖盘衰竭，可能接近阶段底部。"
    action = "🟡 不宜恐慌杀跌，可关注止跌信号。"
else:
    diagnosis = "量价正常，无明显背离。"
    action = "➡️ 保持现有仓位，继续观察。"

print(f"\n📊 今日诊断：{direction} + {vol_status}")
print(f"📝 分析：{diagnosis}")
print(f"💡 建议：{action}")

conn.close()
print("\n>>> FinMate 全自动管道执行完毕！")