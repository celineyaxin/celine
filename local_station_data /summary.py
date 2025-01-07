# import os
# import pandas as pd

# # 读取汇总表格
# complaint_summary_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/原始数据处理/financial_complains.csv'
# complaint_summary_df = pd.read_csv(complaint_summary_path)

# # 遍历地区文件夹
# region_directory = '/Users/chenyaxin/Desktop/处理黑猫地方站/地方站导出数据'
# complaint_region_dict = {}
# region_complaints_df = pd.DataFrame()
# region_name_map = {
#     "广东站": "广东省",
#     "江苏站": "江苏省",
#     "陕西站": "陕西省",
#     "安徽站": "安徽省",
#     "重庆站": "重庆市",
#     "福建站": "福建省",
#     "广西站": "广西壮族自治区",
#     "海南站": "海南省",
#     "河北站": "河北省",
#     "河南站": "河南省",
#     "黑龙江站": "黑龙江省",
#     "湖北站": "湖北省",
#     "湖南站": "湖南省",
#     "吉林站": "吉林省",
#     "江西站": "江西省",
#     "辽宁站": "辽宁省",
#     "上海站": "上海市",
#     "四川站": "四川省",
#     "天津站": "天津市",
#     "浙江站": "浙江省",
#     "其他站": "其他地区",
# }
# # 遍历文件夹中的所有子文件夹
# for subfolder in os.listdir(region_directory):
#     subfolder_path = os.path.join(region_directory, subfolder)
#     if os.path.isdir(subfolder_path):
#         if subfolder == "其他站":
#             csv_file_name = 'complaint_ids_classfy_others.csv'        
#         else:
#             csv_file_name = 'merged.xlsx'
#         csv_path = os.path.join(subfolder_path, csv_file_name)
#         if os.path.exists(csv_path):
#             if csv_file_name.endswith('.csv'):
#                 regional_complaints_df = pd.read_csv(csv_path)
#                 regional_complaints_df = regional_complaints_df.rename(columns={'投诉编号': 'gd_complaint_id'})
#             elif csv_file_name.endswith('.xlsx'):
#                 regional_complaints_df = pd.read_excel(csv_path)
#             if 'gd_complaint_id' in regional_complaints_df.columns:
#                 regional_complaints_df = regional_complaints_df.rename(columns={'gd_complaint_id': '投诉编号'})
#                 regional_complaints = pd.DataFrame({'投诉编号': regional_complaints_df['投诉编号'], '地区': [region_name_map.get(subfolder, subfolder)] * len(regional_complaints_df)})
#                 # regional_complaints = pd.DataFrame({'投诉编号': regional_complaints_df['投诉编号'], '地区': [subfolder] * len(regional_complaints_df)})
#                 region_complaints_df = pd.concat([region_complaints_df, regional_complaints], ignore_index=True)

# # 将地区信息添加到汇总表格中
# summary_df = complaint_summary_df.merge(region_complaints_df, on='投诉编号', how='left')

# # 保存更新后的汇总表格
# updated_summary_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/原始数据处理/updated_complaint_summary.csv' 
# summary_df.to_csv(updated_summary_path, index=False)
# print(f"更新后的汇总表格已保存至 {updated_summary_path}")

# 补充了一些数据
import os
import pandas as pd

# 读取汇总表格
complaint_summary_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/原始数据处理/updated_complaint_summary.csv'
complaint_summary_df = pd.read_csv(complaint_summary_path,low_memory=False)

# 遍历地区文件夹
region_directory = '/Users/chenyaxin/Desktop/处理黑猫地方站/未完全提取数据'
complaint_region_dict = {}
region_complaints_df = pd.DataFrame()
region_name_map = {
    "广东站": "广东省",
    "江苏站": "江苏省",
    "陕西站": "陕西省",
    "安徽站": "安徽省",
    "重庆站": "重庆市",
    "福建站": "福建省",
    "广西站": "广西壮族自治区",
    "海南站": "海南省",
    "河北站": "河北省",
    "河南站": "河南省",
    "黑龙江站": "黑龙江省",
    "湖北站": "湖北省",
    "湖南站": "湖南省",
    "吉林站": "吉林省",
    "江西站": "江西省",
    "辽宁站": "辽宁省",
    "上海站": "上海市",
    "四川站": "四川省",
    "天津站": "天津市",
    "浙江站": "浙江省",
    "其他站": "其他地区",
}
# 遍历文件夹中的所有子文件夹
for subfolder in os.listdir(region_directory):
    subfolder_path = os.path.join(region_directory, subfolder)
    if os.path.isdir(subfolder_path):
        if subfolder == "其他站":
            csv_file_name = 'add_classfy_others.csv'        
        else:
            csv_file_name = 'filtered_merged.xlsx'
        csv_path = os.path.join(subfolder_path, csv_file_name)
        if os.path.exists(csv_path):
            if csv_file_name.endswith('.csv'):
                regional_complaints_df = pd.read_csv(csv_path)
                regional_complaints_df = regional_complaints_df.rename(columns={'投诉编号': 'gd_complaint_id'})
            elif csv_file_name.endswith('.xlsx'):
                regional_complaints_df = pd.read_excel(csv_path)
            if 'gd_complaint_id' in regional_complaints_df.columns:
                regional_complaints_df = regional_complaints_df.rename(columns={'gd_complaint_id': '投诉编号'})
                regional_complaints = pd.DataFrame({'投诉编号': regional_complaints_df['投诉编号'], '地区': [region_name_map.get(subfolder, subfolder)] * len(regional_complaints_df)})
                region_complaints_df = pd.concat([region_complaints_df, regional_complaints], ignore_index=True)

summary_df = complaint_summary_df.merge(region_complaints_df[['投诉编号', '地区']], 
                                        on='投诉编号', 
                                        how='left',
                                        suffixes=('_summary', '_region'))

# 合并'地区_summary'和'地区_region'列，如果两者都为空，则结果为'未知地区'
summary_df['地区'] = summary_df.apply(lambda row: row['地区_region'] if pd.isnull(row['地区_summary']) and not pd.isnull(row['地区_region']) else row['地区_summary'], axis=1)

# 如果'地区_summary'列有值而'地区_region'列没有值，则使用'地区_summary'列的值
summary_df['地区'] = summary_df['地区'].fillna(summary_df['地区_summary'])

# 删除不再需要的列
summary_df.drop(columns=['地区_summary', '地区_region'], inplace=True)

summary_df['年份'] = summary_df['发布时间'].str.extract('(\d{4})年').astype(int)
summary_df = summary_df[summary_df['年份'] > 2018]
summary_df.drop(columns=['年份'], inplace=True)
# 保存更新后的汇总表格
updated_summary_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/原始数据处理/updated_complaint.csv' 
summary_df.to_csv(updated_summary_path, index=False)
print(f"更新后的汇总表格已保存至 {updated_summary_path}")
