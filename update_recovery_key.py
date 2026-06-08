import sys
from datetime import date

key_content = sys.argv[1]
today = date.today().strftime("%Y-%m-%d")

with open("d:/learn/FinMate_恢复密钥.md", "w", encoding="utf-8") as f:
    f.write(key_content)

print(f"✅ 恢复密钥已更新 ({today})")

with open("d:/learn/FinMate_密钥历史记录.md", "a", encoding="utf-8") as f:
    f.write(f"\n---\n## {today} 更新记录\n{key_content}\n")