import pandas as pd
import os

# 设置文件夹路径
folder_path = '/Users/chenyaxin/Downloads/科研数据/皮皮虾/高级永久数据/上市公司绿色新闻数据库（2013-2023）'
merged_df = pd.DataFrame()
files = [f for f in os.listdir(folder_path) if f.endswith('.xlsx') and not f.startswith('.')]

# 遍历文件夹中的所有Excel文件
for file in files:
    file_path = os.path.join(folder_path, file)
    # 读取Excel文件
    xls_df = pd.read_excel(file_path)
    # 合并数据
    merged_df = pd.concat([merged_df, xls_df], ignore_index=True)
filtered_df = merged_df[merged_df['证券类别'] == 'A股']

# 打印合并后DataFrame的大小
print(f"Merged DataFrame size: {filtered_df.shape}")

# 保存合并后的数据到新的CSV文件中
output_csv_path_all = '/Users/chenyaxin/Desktop/人工智能/data/绿色新闻/合并后的所有数据.csv'
filtered_df.to_csv(output_csv_path_all, index=False)
print(f"合并后的所有数据已保存至 '{output_csv_path_all}'")

sampled_df = filtered_df.sample(n=5000, random_state=1)

# 保存随机抽取的数据到新的CSV文件中
output_csv_path_sampled = '/Users/chenyaxin/Desktop/人工智能/data/绿色新闻/随机抽取的数据.csv'
sampled_df.to_csv(output_csv_path_sampled, index=False)
print(f"随机抽取的数据已保存至 '{output_csv_path_sampled}'")