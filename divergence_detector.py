import pymysql
import pandas as pd
import numpy as np

print(">>> 启动MACD背离检测引擎...")

connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
df = pd.read_sql("SELECT trade_date, close, dif, dea, macd_bar FROM stock_daily WHERE dif IS NOT NULL ORDER BY trade_date;", connection)
connection.close()
print(f"读取 {len(df)} 条数据。")

def find_local_peaks(series, window=5):
    peaks = []
    for i in range(window, len(series) - window):
        if series.iloc[i] == max(series.iloc[i-window:i+window+1]):
            peaks.append(i)
    return peaks

def find_local_troughs(series, window=5):
    troughs = []
    for i in range(window, len(series) - window):
        if series.iloc[i] == min(series.iloc[i-window:i+window+1]):
            troughs.append(i)
    return troughs

print("\n===== 顶背离检测 =====")
price_peaks_idx = find_local_peaks(df['close'], window=5)
dif_peaks_idx = find_local_peaks(df['dif'], window=5)

if len(price_peaks_idx) >= 2:
    for i in range(len(price_peaks_idx)-1):
        idx1 = price_peaks_idx[i]
        idx2 = price_peaks_idx[i+1]
        if df.loc[idx2, 'close'] > df.loc[idx1, 'close'] and df.loc[idx2, 'dif'] < df.loc[idx1, 'dif']:
            print(f"⚠️ 顶背离：{df.loc[idx1, 'trade_date']} -> {df.loc[idx2, 'trade_date']}")
            print(f"   股价: {df.loc[idx1, 'close']:.2f} -> {df.loc[idx2, 'close']:.2f} (↑)")
            print(f"   DIF: {df.loc[idx1, 'dif']:.4f} -> {df.loc[idx2, 'dif']:.4f} (↓)")
            print(f"   信号：上涨动能衰竭，可能见顶回落。\n")

print("===== 底背离检测 =====")
price_troughs_idx = find_local_troughs(df['close'], window=5)
dif_troughs_idx = find_local_troughs(df['dif'], window=5)

if len(price_troughs_idx) >= 2:
    for i in range(len(price_troughs_idx)-1):
        idx1 = price_troughs_idx[i]
        idx2 = price_troughs_idx[i+1]
        if df.loc[idx2, 'close'] < df.loc[idx1, 'close'] and df.loc[idx2, 'dif'] > df.loc[idx1, 'dif']:
            print(f"📈 底背离：{df.loc[idx1, 'trade_date']} -> {df.loc[idx2, 'trade_date']}")
            print(f"   股价: {df.loc[idx1, 'close']:.2f} -> {df.loc[idx2, 'close']:.2f} (↓)")
            print(f"   DIF: {df.loc[idx1, 'dif']:.4f} -> {df.loc[idx2, 'dif']:.4f} (↑)")
            print(f"   信号：下跌动能衰竭，可能见底反弹。\n")

print(">>> 背离检测完成。")
