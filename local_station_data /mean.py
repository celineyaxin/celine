import pandas as pd

# 读取CSV文件
file_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/原始数据处理/complaints_by_province_and_year.csv'
df = pd.read_csv(file_path, low_memory=False)

# 读取Excel文件
additional_info_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/原始数据处理/各省金融素养得分排序.xlsx'
additional_info_df = pd.read_excel(additional_info_path)

# 根据地区和省份信息合并两个表格，仅保留匹配的行
merged_df = pd.merge(df, additional_info_df, left_on='地区', right_on='省份', how='inner')

# 确保年份列是整数类型
merged_df['年份'] = merged_df['年份'].astype(int)

# 删除没有列名的列
if 'Unnamed: 0' in merged_df.columns:
    merged_df.drop(columns=['Unnamed: 0'], inplace=True)

# 打印列名以检查'分组一'列是否存在
print("列名：", merged_df.columns)

# 检查'分组一'列是否存在
if '分组一' in merged_df.columns:
    # 计算每个分组一内所有企业在不同年份的投诉数量的均值
    complaint_mean_by_group = merged_df.groupby(['分组一', '年份'])['投诉数量'].mean().reset_index(name='投诉数量均值')
    # 输出结果
    output_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/原始数据处理/complaints_by_group_and_year_mean.csv'
    complaint_mean_by_group.to_csv(output_path, index=False)
    print(f"按分组和年份统计的投诉数量均值已保存至 {output_path}")
else:
    print("错误：'分组一'列不存在。请检查列名。")