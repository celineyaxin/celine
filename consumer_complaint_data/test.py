import pandas as pd

merge_file = pd.read_csv('/Users/chenyaxin/Desktop/商家信息匹配/merge_file.csv')
complaint_object = pd.read_csv('/Users/chenyaxin/Desktop/商家信息匹配/complaint_object.csv')

filtered_data = merge_file[merge_file['投诉编号'].isin(complaint_object['投诉编号'])]

# 将筛选后的数据保存到新的CSV文件
filtered_data.to_csv('/Users/chenyaxin/Desktop/商家信息匹配/filtered_merge_file.csv', index=False)

print("筛选完成，结果已保存到 '/Users/chenyaxin/Desktop/商家信息匹配/filtered_merge_file.csv'")