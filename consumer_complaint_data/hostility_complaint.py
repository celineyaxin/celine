import pandas as pd
import os

# 文件路径和基本文件名
base_path = '/Users/chenyaxin/Desktop/websitdata/filter_similirity/'
file_prefix = 'similar_complaints_'
file_suffix = '.csv'
output_file = '/Users/chenyaxin/Desktop/websitdata/filtered_data_90.csv'

file_list = [f"{base_path}{file_prefix}{i}{file_suffix}" for i in range(0, 20)]
results = []

# 循环处理每个文件
for file_path in file_list:
    df1 = pd.read_csv(file_path)
    df2 = pd.read_csv('/Users/chenyaxin/Desktop/websitdata/merge_data5/financial_complains.csv')
    df1['投诉编号1'] = df1['投诉编号1'].astype(int)
    df1['投诉编号2'] = df1['投诉编号2'].astype(int)
    df2['投诉编号'] = df2['投诉编号'].astype(int)
    df2 = df2.drop_duplicates(subset='投诉编号')
    df1.rename(columns={'投诉编号1': '投诉编号'}, inplace=True)
    merged_df1 = pd.merge(df1, df2, on='投诉编号', how='left')

    merged_df1.rename(columns={'投诉编号': '投诉编号1'}, inplace=True)
    merged_df1.rename(columns={'发布时间': '发布时间1'}, inplace=True)
    merged_df1.rename(columns={'投诉编号2': '投诉编号'}, inplace=True)
    merged_df2 = pd.merge(merged_df1, df2, on='投诉编号', how='left')
    merged_df2.rename(columns={'发布时间': '发布时间2'}, inplace=True)
    merged_df2.rename(columns={'投诉编号': '投诉编号2'}, inplace=True)

    merged_df2['发布时间2'] = pd.to_datetime(merged_df2['发布时间2'], format='%Y年%m月%d日 %H:%M')
    merged_df2['发布时间1'] = pd.to_datetime(merged_df2['发布时间1'], format='%Y年%m月%d日 %H:%M')

    merged_df2['时间差'] = (merged_df2['发布时间2'] - merged_df2['发布时间1']).dt.days
    df2_filtered = merged_df2[merged_df2['时间差'] < 90]

    df2_filtered_high_similarity = df2_filtered[df2_filtered['相似度'] >= 90]
    results.append(df2_filtered_high_similarity)

# 循环结束后，合并所有的结果
merged_results = pd.concat(results, ignore_index=True)

# 将合并后的结果保存到CSV文件中
merged_results.to_csv(output_file, index=False)

print(f"所有文件处理完成，合并结果已保存到 '{output_file}'")