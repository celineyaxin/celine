import pandas as pd
csv_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/merged_output.xlsx'

# 读取CSV文件
df = pd.read_excel(csv_file_path)
sampled_df = df.sample(n=3000, replace=False)
output_csv_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/sampled_file.csv'
sampled_df.to_csv(output_csv_path, index=False)

print(f"随机抽取的3000行数据已保存至 {output_csv_path}")