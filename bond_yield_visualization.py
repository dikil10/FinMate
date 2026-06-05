import pymysql
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date

print(">>> 启动国债收益率可视化引擎...")

# 1. 从你的数据中台读取数据
connection = pymysql.connect(host='localhost', user='root', password='123456', db='finance_learning')
df = pd.read_sql("SELECT * FROM china_bond_yield ORDER BY record_date;", connection)
connection.close()
df['record_date'] = pd.to_datetime(df['record_date'])
print(f"成功读取 {len(df)} 条数据。")

# 2. 设置画布
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1]})
fig.suptitle('中国国债收益率与期限利差 · 个人金融数据中台', fontsize=16, fontweight='bold')

# 3. 上图：收益率走势
ax1.plot(df['record_date'], df['yield_10y'], color='#1f77b4', linewidth=2, marker='o', markersize=4, label='10年期收益率')
ax1.plot(df['record_date'], df['yield_6m'], color='#ff7f0e', linewidth=2, marker='s', markersize=4, label='6个月期收益率')
ax1.set_ylabel('收益率 (%)', fontsize=12)
ax1.set_title('国债收益率曲线', fontsize=13)
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
ax1.fill_between(df['record_date'], df['yield_10y'], df['yield_6m'], alpha=0.1, color='gray')

# 4. 下图：期限利差
colors = ['#d62728' if x >= 0 else '#2ca02c' for x in df['spread']]
ax2.bar(df['record_date'], df['spread'], color=colors, width=0.6, edgecolor='white', linewidth=0.3)
ax2.axhline(y=0, color='black', linewidth=0.8, linestyle='-')
ax2.set_xlabel('日期', fontsize=12)
ax2.set_ylabel('期限利差 (10Y-6M, %)', fontsize=12)
ax2.set_title('期限利差（正=正常，负=倒挂预警）', fontsize=13)
ax2.grid(True, alpha=0.3, axis='y')
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

# 5. 标注关键信息
latest = df.iloc[-1]
ax2.annotate(f'最新利差: {latest["spread"]:.3f}%',
             xy=(latest['record_date'], latest['spread']),
             xytext=(10, 20), textcoords='offset points',
             arrowprops=dict(arrowstyle='->', color='black'),
             fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('bond_yield_dashboard.png', dpi=150)
print("图表已保存为 bond_yield_dashboard.png")
plt.show()