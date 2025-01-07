import os
import pandas as pd

folder_path = '/Users/chenyaxin/Desktop/互联网旅游公约/业务分类结果'  # 替换为CSV文件所在的文件夹路径
output_filename = '/Users/chenyaxin/Desktop/互联网旅游公约/extracted_complaints.csv'  # 替换为输出CSV文件的路径

travel_complaints_path = '/Users/chenyaxin/Desktop/互联网旅游公约/travel_complaints.csv'
travel_complaints_df = pd.read_csv(travel_complaints_path)
csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv') and not f.startswith('.')]

merged_df = pd.DataFrame()

for csv_file in csv_files:
    csv_path = os.path.join(folder_path, csv_file)
    df = pd.read_csv(csv_path)
    filtered_df = df[df['使用服务'].isin(['去哪儿网出行服务', '美团出行服务'])]
    merged_df = pd.concat([merged_df, filtered_df], ignore_index=True)

# 提取投诉编号
complaint_ids = merged_df['投诉编号'].drop_duplicates()  # 使用drop_duplicates()确保编号唯一
extracted_complaints = travel_complaints_df[travel_complaints_df['投诉编号'].isin(complaint_ids)]
# 将结果保存到CSV文件
extracted_complaints.to_csv(output_filename, index=False, header=True)
print(f"提取的投诉编号已写入 {output_filename}")