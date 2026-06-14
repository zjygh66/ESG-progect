"""
检查CSV文件记录数
"""
import csv

f = open('outputs/results/base_records.csv', 'r', encoding='utf-8-sig')
reader = csv.reader(f)
rows = list(reader)
print(f'总记录数: {len(rows)}')
print(f'平安银行记录数: {len([r for r in rows if r[0] == "000001"])}')
f.close()

# 打印平安银行记录摘要
print("\n平安银行记录摘要:")
for r in rows:
    if r[0] == "000001":
        print(f"  {r[2]}: risk_tone={r[9]}, verifiability_score={r[14]}")