import os
import pandas as pd
from tqdm import tqdm

csv_path = '/Users/chenyaxin/Desktop/互联网旅游公约/travel_complaints.csv'
out_path = '/Users/chenyaxin/Desktop/互联网旅游公约/meituan_quna.csv'

df = pd.read_csv(csv_path)

# 筛选出投诉对象为“美团”或“去哪儿”的行
filtered_df = df[df['投诉对象'].isin(['美团客服小美', '去哪儿网客服'])]

# 提取投诉编号
complaint_ids = filtered_df['投诉编号'].drop_duplicates()  # 使用drop_duplicates()确保编号唯一

# 将结果保存到CSV文件
complaint_ids.to_csv(out_path, index=False, header=['投诉编号'])
print(f"提取的投诉编号已写入 {out_path}")

