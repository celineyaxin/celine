import pandas as pd
import os
from tqdm import tqdm

# 定义文件夹路径和需要的列
folder_path = '/Volumes/yaxindedisk 1/黑猫数据库/黑猫原始网页数据备份/merge_data2'
needed_columns = ["投诉编号", "涉诉金额", "投诉进度", "发起投诉时间", "商家回复时间1"]

# 定义输出CSV文件的路径
output_csv_path = '/Users/chenyaxin/Desktop/上市公司投诉数据探究/上市公司信息筛选/complaints_character.csv'
listed_complaints_path = '/Users/chenyaxin/Desktop/上市公司投诉数据探究/上市公司信息筛选/listed-complaints.csv'
columns_of_interest = [
    "发布时间", "投诉编号_x", "投诉对象", "发起投诉内容", "complaint_count",
    "Stkcd", "ShortName", "tag1", "tag2", "tag", "Nnindcd", "Nnindnme"
]
listed_df = pd.read_csv(listed_complaints_path, usecols=columns_of_interest).rename(columns={"投诉编号_x": "投诉编号"})
# print(listed_df)
file_count = 0
# 逐个读取文件夹中的CSV文件
for filename in sorted(tqdm(os.listdir(folder_path), desc="处理文件")):
    if filename.endswith(".csv") and not filename.startswith('.'):
        file_path = os.path.join(folder_path, filename)
        df = pd.read_csv(file_path)
        df = df.dropna(how='all')
        filtered_df = df[needed_columns]
        if file_count == 0:
            filtered_df.to_csv(output_csv_path, index=False)
        else:
            # 否则，追加到文件中，不写入列头
            filtered_df.to_csv(output_csv_path, mode='a', header=False, index=False)
        
        # 增加计数器
        file_count += 1
        if file_count == 80:
            break
del filtered_df
print("初步处理完成，筛选后的数据已保存到", output_csv_path)

df = pd.read_csv(output_csv_path)
merged_df = pd.merge(df, listed_df, on="投诉编号", how="inner")
print(f"合并后的DataFrame包含 {len(merged_df)} 行数据。")
print("合并后的DataFrame的前几行数据：")
print(merged_df.head())
merged_df.to_csv(output_csv_path, index=False)

print("上市公司代码筛选完成，结果已保存到", output_csv_path)