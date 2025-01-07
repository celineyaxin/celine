import pandas as pd

# 读取 travel_complaints.csv 文件
travel_complaints_path = '/Users/chenyaxin/Desktop/互联网旅游公约/travel_complaints.csv'
travel_complaints_df = pd.read_csv(travel_complaints_path)
filtered_travel_complaints_df = travel_complaints_df[~travel_complaints_df['投诉对象'].isin(['美团客服小美', '去哪儿网客服'])]

# 读取 extracted_complaints.csv 文件
extracted_complaints_path = '/Users/chenyaxin/Desktop/互联网旅游公约/extracted_complaints.csv'
extracted_complaints_df = pd.read_csv(extracted_complaints_path)

# 合并两个 DataFrame
merged_df = pd.concat([filtered_travel_complaints_df, extracted_complaints_df], ignore_index=True)

# 读取 deleted_complaints.csv 文件中的投诉编号
deleted_complaints_path = '/Users/chenyaxin/Desktop/互联网旅游公约/meituan_delete.csv'
deleted_complaints_df = pd.read_csv(deleted_complaints_path)
complaint_ids_to_remove = deleted_complaints_df['投诉编号'].unique()

# 从 merged_df 中剔除 deleted_complaints.csv 中的投诉编号
final_df = merged_df[~merged_df['投诉编号'].isin(complaint_ids_to_remove)]

# 保存合并后的结果到一个新的 CSV 文件中
output_filename = '/Users/chenyaxin/Desktop/互联网旅游公约/treat.csv'
final_df.to_csv(output_filename, index=False)
print(f"合并后的投诉内容已写入 {output_filename}")