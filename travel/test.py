import pandas as pd
import os

# 设置文件夹路径和Excel文件路径
folder_path = '/Users/chenyaxin/Desktop/互联网旅游公约/原始数据处理'
csv_path = '/Users/chenyaxin/Desktop/互联网旅游公约/treat.csv'
output_csv_path = '/Users/chenyaxin/Desktop/互联网旅游公约/treat_with_time.csv'

# 读取Excel文件
complaints_df = pd.read_csv(csv_path)
complaint_times_df = pd.DataFrame()

# 遍历文件夹中的所有CSV文件
for filename in os.listdir(folder_path):
    if filename.endswith('.csv') and not filename.startswith('.'):
        file_path = os.path.join(folder_path, filename)
        temp_df = pd.read_csv(file_path)
        temp_df = temp_df.dropna(how='all', axis=1)  # 排除全部为NA的列
        temp_df = temp_df.dropna(how='all', axis=0)  # 排除全部为空的行
        if '投诉编号' in temp_df.columns and '发布时间' in temp_df.columns:
            complaint_times_df = pd.concat([complaint_times_df, temp_df[['投诉编号', '发布时间']]], ignore_index=True)
 
# 确保投诉编号是字符串类型，以便进行匹配
complaints_df['投诉编号'] = complaints_df['投诉编号'].astype(str)
complaint_times_df['投诉编号'] = complaint_times_df['投诉编号'].astype(str)

# 通过投诉编号将投诉时间信息匹配到原始Excel文件中
complaints_df = pd.merge(complaints_df, complaint_times_df[['投诉编号', '发布时间']], on='投诉编号', how='left')

# 保存匹配后的数据到新的Excel文件中
complaints_df.to_csv(output_csv_path, index=False)
print(f"匹配后的数据已保存至 '{output_csv_path}'")