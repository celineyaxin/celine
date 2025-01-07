import pandas as pd

# 读取Excel文件
merged_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/未完全提取数据/江西站/merged.xlsx'
merged_df = pd.read_excel(merged_path)

jx_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/未完全提取数据/江西站/jx.csv'
jx_df = pd.read_csv(jx_path)

urls_set = set(jx_df['页面网址'])
filtered_df = merged_df[merged_df['页面网址'].isin(urls_set)]

output_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/未完全提取数据/江西站/filtered_merged.xlsx'
filtered_df.to_excel(output_path, index=False)

print(f"筛选后的结果已保存至 {output_path}")