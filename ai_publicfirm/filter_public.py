# import os
# import pandas as pd
# from tqdm import tqdm
# # 读取Excel文件中的投诉对象数据
# excel_path = '/Users/chenyaxin/Desktop/人工智能/上市公司信息筛选/投诉对象匹配列表.xlsx'  # Excel文件路径
# complaints_df = pd.read_excel(excel_path)
# output_filename = '/Users/chenyaxin/Desktop/人工智能/上市公司信息筛选/public_complaints_all.csv'
# # 确保CSV文件夹路径正确
# # csv_directory = '/Users/chenyaxin/Desktop/互联网旅游公约/原始数据处理'  # CSV文件所在文件夹路径
# csv_directory = '/Volumes/yaxindedisk 1/黑猫原始网页数据备份/merge_data2'
# results_df = pd.DataFrame()
# total_files = len([name for name in os.listdir(csv_directory) if name.endswith(".csv") and not name.startswith('.')])
# for filename in tqdm(os.listdir(csv_directory), total=total_files, desc='Processing files'):
# # for filename in os.listdir(csv_directory):
#     if filename.endswith(".csv") and not filename.startswith('.'):
#         filepath = os.path.join(csv_directory, filename)
#         df = pd.read_csv(filepath,low_memory=False)
#         matched_df = df[df['投诉对象'].isin(complaints_df['投诉对象'])]

#         if not matched_df.empty:
#             extracted_data = matched_df[['发布时间','投诉编号', '投诉对象', '发起投诉内容']]
#             results_df = pd.concat([results_df, extracted_data], ignore_index=True)

# results_df.to_csv(output_filename, index=False)
# print(f"提取的数据已写入 {output_filename}")

import pandas as pd
csv_file_path = '/Users/chenyaxin/Desktop/人工智能/上市公司信息筛选/public_complaints_all.csv'
df = pd.read_csv(csv_file_path)
total_rows = len(df)
unique_complaint_objects = df['投诉对象'].nunique()

print(f"CSV文件总行数: {total_rows}")
print(f"'投诉对象'列中唯一值的数量: {unique_complaint_objects}")