# 分文件编码提取投诉内容
import pandas as pd
import numpy as np
import os

# 定义文件路径
financial_file_path = '/Users/chenyaxin/Desktop/websitdata/merge_data3/financial_complains.csv'
# financial_file_path = '/Users/chenyaxin/Desktop/websitdata/merge_data3/test.csv'

# 读取和筛选 financial_complaints.csv 文件
df = pd.read_csv(financial_file_path)
df_financial = df.drop_duplicates(subset=['投诉内容'])
date_format = "%Y年%m月%d日 %H:%M"
df_financial.loc[:, '发布时间'] = pd.to_datetime(df_financial['发布时间'], format=date_format)
# df_financial['发布时间'] = pd.to_datetime(df_financial['发布时间'], format=date_format)
cutoff_date = pd.Timestamp('2020-01-01')
off_date = pd.Timestamp('2024-01-01')
df_filtered = df_financial[(cutoff_date < df_financial['发布时间']) & (df_financial['发布时间'] < off_date)]
df_filtered = df_filtered[~(df_filtered['编码'].astype(str).str.startswith('2'))]
df_filtered.sort_values(by=['编码', '发布时间'], inplace=True)

编码文件分配 = {i: [] for i in range(20)}  # 创建20个文件的空列表

编码列表 = df_filtered['编码'].unique()
编码计数 = {codec: 0 for codec in 编码列表}
for index, row in df_filtered.iterrows():
    编码计数[row['编码']] += 1

# 分配编码到文件，尝试保持文件大小均匀
累积计数 = np.zeros(20)
for codec, count in 编码计数.items():
    min_index = np.argmin(累积计数)
    编码文件分配[min_index].append(codec)
    累积计数[min_index] += count

output_dir = './similarity'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
# 根据分配结果写入文件
for file_index, codecs in 编码文件分配.items():
    part_data = df_filtered[df_filtered['编码'].isin(codecs)]
    output_file_path = os.path.join(output_dir, f'complaints_part_{file_index}.csv')
    part_data.to_csv(output_file_path, index=False)
    print(f"数据已成功写入 '{output_file_path}'")

print("所有文件生成完毕。")