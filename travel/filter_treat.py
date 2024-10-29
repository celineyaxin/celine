import os
import pandas as pd
from tqdm import tqdm
# 读取Excel文件中的投诉对象数据
excel_path = '/Users/chenyaxin/Desktop/互联网旅游公约/处理组列表.xlsx'  # Excel文件路径
complaints_df = pd.read_excel(excel_path)
output_filename = '/Users/chenyaxin/Desktop/互联网旅游公约/travel_complaints.csv'
# 确保CSV文件夹路径正确
csv_directory = '/Volumes/yaxindedisk 1/黑猫原始网页数据备份/merge_data2'  # CSV文件所在文件夹路径
results_df = pd.DataFrame()
# total_files = len([name for name in os.listdir(csv_directory) if name.endswith(".csv") and not name.startswith('.')])
# for filename in tqdm(os.listdir(csv_directory), total=total_files, desc='Processing files'):
for filename in os.listdir(csv_directory):
    if filename.endswith(".csv") and not filename.startswith('.'):
        filepath = os.path.join(csv_directory, filename)
        df = pd.read_csv(filepath,low_memory=False)
        matched_df = df[df['投诉对象'].isin(complaints_df['投诉对象'])]

        if not matched_df.empty:
            extracted_data = matched_df[['投诉编号', '投诉对象', '发起投诉内容']]
            results_df = pd.concat([results_df, extracted_data], ignore_index=True)

results_df.to_csv(output_filename, index=False)
print(f"提取的数据已写入 {output_filename}")
