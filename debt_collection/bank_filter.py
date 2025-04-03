import pandas as pd

# 输入和输出文件路径
csv_file = '/Users/chenyaxin/Desktop/催收/financial_final.csv'
output_file = '/Users/chenyaxin/Desktop/催收/bank_complaints.csv'

# 加载CSV文件
df = pd.read_csv(csv_file)

bank_complaints = df[df['投诉商家'].str.contains('银行', na=False)]

# 保存提取结果到新的CSV文件
bank_complaints.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"提取完成，包含'银行'的投诉内容已保存到 {output_file}")