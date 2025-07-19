import pandas as pd

# 定义文件夹路径
folder_path = '/Users/chenyaxin/Desktop/privacy/data/'

# 定义文件路径
fraud_file = folder_path + 'fraud_predictions_20180101_0000_20231231_2359.csv'
clear_file = '/Users/chenyaxin/Desktop/websitdata/bert/results/是否明示/delete_hostility.csv'

# 读取两个 CSV 文件
fraud_df = pd.read_csv(fraud_file)
clear_df = pd.read_csv(clear_file)

# 筛选 prediction 为 1 的行
fraud_filtered = fraud_df[fraud_df['prediction'] == 1]
clear_filtered = clear_df[clear_df['prediction'] == 1]

filtered_complaints = fraud_filtered[~fraud_filtered['投诉编号'].isin(clear_filtered['投诉编号'])]

# 将重合的行写入新的 CSV 文件
output_file = folder_path + 'delete_clearcomplaints.csv'
filtered_complaints.to_csv(output_file, index=False)

# 统计条目
print(f"投诉编号条目数：{len(fraud_filtered)}")
print(f"投诉编号条目数：{len(clear_filtered)}")
print(f"投诉编号条目数：{len(filtered_complaints)}")