# 提取41结尾文件中的指定列
import os
import pandas as pd
from datetime import datetime

base_dir = '/Users/chenyaxin/Desktop/websitdata/merge_data4'  
output_filename = '/Users/chenyaxin/Desktop/商家信息匹配/complaint_object.csv'
start_date = '2018-01-01'
end_date = '2023-12-31'


# 转换时间区间为日期格式
all_data = pd.DataFrame()
start = datetime.strptime(start_date, '%Y-%m-%d')
end = datetime.strptime(end_date, '%Y-%m-%d')

# 需要提取的列名列表
columns_to_extract = ['投诉编号', '投诉对象']  

# 遍历时间区间内的每个月
current = start
while current <= end:
    # 格式化月份文件夹名称
    year = current.strftime('%Y')
    month = current.strftime('%m').zfill(2)  # 确保月份是两位数，例如04
    folder_name = f'output_{year}_{month}'

    # 构建文件夹路径
    folder_path = os.path.join(base_dir, folder_name)
    # 检查文件夹是否存在
    if os.path.exists(folder_path):
        target_filename = f'{year}_{month}_09.csv'
        if target_filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, target_filename)
            try:
                df = pd.read_csv(file_path, usecols=columns_to_extract)
                all_data = pd.concat([all_data, df])
                print(f"已提取文件 {file_path} 中的指定列。")
            except Exception as e:
                print(f"读取文件 {file_path} 时发生错误: {e}")

    current += pd.DateOffset(months=1)

all_data_grouped = all_data.groupby('投诉对象')['投诉编号'].count().reset_index(name='complaint_count')
final_data = all_data_grouped.merge(all_data, on='投诉对象', how='left')
final_data = final_data.drop_duplicates(subset='投诉对象')
final_data.to_csv(output_filename, index=False)
print(f"所有数据已写入 {output_filename}")