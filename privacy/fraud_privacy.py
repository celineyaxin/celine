import pandas as pd

# 定义文件夹路径
folder_path = '/Users/chenyaxin/Desktop/privacy/data/'

# 定义文件路径
fraud_file = folder_path + 'fraud_predictions_20180101_0000_20231231_2359.csv'
privacy_file = folder_path + 'privacy_predictions_20180101_0000_20231231_2359.csv'

# 读取两个 CSV 文件
fraud_df = pd.read_csv(fraud_file)
privacy_df = pd.read_csv(privacy_file)

# 筛选 prediction 为 1 的行
fraud_filtered = fraud_df[fraud_df['prediction'] == 1]
privacy_filtered = privacy_df[privacy_df['prediction'] == 1]

# 找到重合的投诉编号
common_complaints = fraud_filtered[fraud_filtered['投诉编号'].isin(privacy_filtered['投诉编号'])]

# 将重合的行写入新的 CSV 文件
output_file = folder_path + 'common_fraud_and_privacy_complaints.csv'
common_complaints.to_csv(output_file, index=False)

# 统计条目
print(f"重合的投诉编号条目数：{len(common_complaints)}")