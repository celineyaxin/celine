import pandas as pd


file_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/原始数据处理/updated_complaint_summary.csv'
df = pd.read_csv(file_path)
df = df.drop_duplicates(subset=['投诉编号'])
print(len(df))


df['发布时间'] = pd.to_datetime(df['发布时间'], format='%Y年%m月%d日 %H:%M', errors='coerce')
first_region_date = df[df['地区'].notna()]['发布时间'].min()
print(f"最早包含地区信息的日期是：{first_region_date}")

# df = df[df['发布时间'] >= first_region_date]
# print(len(df))
df = df[df['发布时间'].dt.year < 2024]
print(len(df))
df = df[df['发布时间'].dt.year > 2018]
print(len(df))

no_region_df = df[df['地区'].isna()]
no_region_info = no_region_df[['投诉编号']] 

gd_complaint_ids_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/地方站导出数据/广东站/complaint_ids_classfy_gd.csv'
gd_df = pd.read_csv(gd_complaint_ids_path)
gd_complaint_ids = set(gd_df['投诉编号'])  # 转换为集合以提高搜索效率
filtered_no_region_df = no_region_df[~no_region_df['投诉编号'].isin(gd_complaint_ids)]
print(len(filtered_no_region_df))

output_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/原始数据处理/no_region_info.csv'
filtered_no_region_df.to_csv(output_path, index=False, columns=['投诉编号'])
print(f"没有地区信息的行已保存至 {output_path}")
