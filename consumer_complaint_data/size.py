import pandas as pd

# csv_file_path = '/Users/chenyaxin/Desktop/websitdata/merge_data3/mergedSeller.csv'
csv_file_path = '/Users/chenyaxin/Desktop/websitdata/merge_data3/financial_complains.csv'
df = pd.read_csv(csv_file_path)

# 1. 统计缺失值
# missing_values = df['投诉内容'].isnull().sum()
# print(f"Number of missing values in '投诉内容': {missing_values}")
# 打印缺失文本
# missing_complaints = df[df['投诉内容'].isnull()]
# missing_complaint_ids = missing_complaints['投诉编号']
# # print(missing_complaint_ids)
# missing_complaints.to_csv('missing_complaints_specific_columns.csv', index=False)

# 2. 根据文本数据进行切分
# df['投诉发起时间'] = pd.to_datetime(df['投诉发起时间'], format='%Y年%m月%d日 %H:%M')
# start_date = '2019-03-01'
# end_date = '2023-03-31'
# filtered_df = df[(df['投诉发起时间'] >= start_date) & (df['投诉发起时间'] <= end_date)]
# print(filtered_df)
# filtered_df.to_csv('complaints_between_dates.csv', index=False)

# 3. 统计变量值的个数
value_counts_per_variable = df.count()
for variable, value_count in value_counts_per_variable.items():
    print(f"变量: {variable}, 值的数量: {value_count}")

# 4. check某个值的数目
# meituan_jieqian_rows = df[df['投诉商家'] == '美团借钱']
# count_meituan_jieqian = len(meituan_jieqian_rows)
# print(f"投诉商家是 '美团借钱' 的样本个数: {count_meituan_jieqian}")  


# 5. 统计变量中单个值的个数
# complaint_status_counts = df['匹配状态'].value_counts()
# print(f"投诉状态的每个值的数量:")
# print(complaint_status_counts)   

# 根据匹配状态筛选生成文件
# 筛选1
# df_filtered = df[df['匹配状态'] == 1]
# output_csv_path = 'one_records.csv'  # 指定输出文件的路径和名称
# df_filtered.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
# print(f"唯一记录已写入文件：{output_csv_path}")

# 剔除重复值
# df_filtered = df[df['匹配状态'] == 1]
# df_unique = df_filtered.drop_duplicates(subset='投诉商家', keep='first')
# output_csv_path = 'unique_one_records.csv'  # 指定输出文件的路径和名称
# df_unique.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
# print(f"唯一记录已写入文件：{output_csv_path}")

# 筛选0
# df_filtered = df[df['匹配状态'] == 0]
# output_csv_path = 'zero_records.csv'  # 指定输出文件的路径和名称
# df_filtered.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
# print(f"唯一记录已写入文件：{output_csv_path}")

# 剔除重复值
# df_filtered = df[df['匹配状态'] == 0]
# df_unique = df_filtered.drop_duplicates(subset='投诉商家', keep='first')
# output_csv_path = 'unique_zero_records.csv'  # 指定输出文件的路径和名称
# df_unique.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
# print(f"唯一记录已写入文件：{output_csv_path}")

# 删除空白行
# df = pd.read_csv(csv_file_path)
# df_cleaned = df.dropna()
# df_cleaned.to_csv('merge_file.csv', index=False)
