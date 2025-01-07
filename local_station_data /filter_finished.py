import pandas as pd

# 指定文件路径
original_csv_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/未完全提取数据/天津站/add_classfy_tj.csv'  # 替换为原始数据文件的路径
merged_excel_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/未完全提取数据/天津站/filtered_merged.xlsx'  # 替换为合并后的Excel文件的路径
output_csv_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/未完全提取数据/其他站/add_classfy_others.csv'  # 输出CSV文件的路径

# 读取原始数据文件中的编号列
original_df = pd.read_csv(original_csv_path, usecols=['投诉编号'])  # 假设列名是'编号'，根据实际情况调整

# 读取合并后的Excel文件中的Complaint_ID列
merged_df = pd.read_excel(merged_excel_path, usecols=['gd_complaint_id'])  # 假设列名是'Complaint_ID'，根据实际情况调整

# 剔除merged.xlsx中的Complaint_ID列中的编号
remaining_ids = original_df[~original_df['投诉编号'].isin(merged_df['gd_complaint_id'])]
print(len(remaining_ids))
# 将剩下的编号保存到新的CSV文件中
remaining_ids.to_csv(output_csv_path, index=False)

print(f"剩下的编号已保存到 {output_csv_path}")