import pandas as pd

# 读取 travel_complaints.csv 文件
travel_complaints_path = '/Users/chenyaxin/Desktop/InternetTourismConvention/travel_complaint_results.csv'
travel_complaints_df = pd.read_csv(travel_complaints_path)
original_count = len(travel_complaints_df)
print(f"原始旅游投诉数据行数: {original_count:,}")

# 读取 extracted_complaints.csv 文件
extracted_complaints_path = '/Users/chenyaxin/Desktop/InternetTourismConvention/extracted_complaints.csv'
extracted_complaints_df = pd.read_csv(extracted_complaints_path)
extracted_count = len(extracted_complaints_df)
print(f"额外提取的投诉数据行数: {extracted_count:,}")

# 读取 deleted_complaints.csv 文件中的投诉编号
deleted_complaints_path = '/Users/chenyaxin/Desktop/InternetTourismConvention/meituan_delete.csv'
deleted_complaints_df = pd.read_csv(deleted_complaints_path)
complaint_ids_to_remove = deleted_complaints_df['投诉编号'].unique()
to_remove_count = len(complaint_ids_to_remove)
print(f"需要删除的投诉编号数量: {to_remove_count:,}")

# 筛选出投诉对象为“美团客服小美”和“去哪儿网客服”的记录
specific_complaints_df = travel_complaints_df[travel_complaints_df['投诉对象'].isin(['美团客服小美', '去哪儿网客服'])]
specific_count = len(specific_complaints_df)
print(f"筛选出的特定投诉对象记录数: {specific_count:,}")

# 从 extracted_complaints.csv 中筛选出投诉编号相同的记录
filtered_specific_complaints_df = specific_complaints_df[specific_complaints_df['投诉编号'].isin(extracted_complaints_df['投诉编号'])]
filtered_specific_count = len(filtered_specific_complaints_df)
print(f"筛选后特定投诉对象记录数: {filtered_specific_count:,}")

# 保留非特定投诉对象的记录
other_complaints_df = travel_complaints_df[~travel_complaints_df['投诉对象'].isin(['美团客服小美', '去哪儿网客服'])]
other_count = len(other_complaints_df)
print(f"其他投诉对象记录数: {other_count:,}")

# 合并筛选后的特定投诉对象记录和其他投诉对象记录
merged_df = pd.concat([other_complaints_df, filtered_specific_complaints_df], ignore_index=True)
merged_count = len(merged_df)
print(f"合并后总行数: {merged_count:,} (其他投诉对象记录 {other_count:,} + 筛选后的特定投诉对象记录 {filtered_specific_count:,})")

# 从合并后的数据中剔除 deleted_complaints.csv 中的投诉编号
final_df = merged_df[~merged_df['投诉编号'].isin(complaint_ids_to_remove)]
final_count = len(final_df)
removed_by_deletion = merged_count - final_count
print(f"删除指定投诉后最终行数: {final_count:,} (移除了 {removed_by_deletion:,} 条记录)")

gaode_transport_keywords = [
    "打车", "网约车", "出租车", "快车", "专车", "代驾", "司机", "车主",
    "一口价", "预估费", "高速费", "附加费", "多收费", "未打表", "返程费", "车费",
    "派单", "接单", "爽约", "未上车", "未到达", "绕路", "偏离路线", "未按导航",
    "开车打电话", "超速", "急刹车", "有责取消",
    "导航错误", "GPS不准", "定位漂移", "播报延迟", "路况更新", "地图数据", "闯红灯", "违章", "电子眼",
    "判责", "判责不公", "扣分", "封号", "账号处罚", "客服判责", "申诉"
]

gaode_hotel_protected_keywords = [
    "酒店", "宾馆", "住宿", "预订", "客房", "入住", "前台", "房费", "房价", "民宿",
    "房间", "床单", "卫生间", "浴室", "空调", "热水", "Wi-Fi", "宽带",
    "景区", "门票", "景点", "公园", "博物馆",
    "办理入住", "确认预订", "无房", "房型不符", "卫生差", "服务态度", "虚假宣传", "设施旧"
]

def is_gaode_travel_complaint(complaint_text):
    """
    优化后的判断函数。
    返回 True: 是酒旅投诉 (应保留)
    返回 False: 是非酒旅投诉 (应筛除)
    """
    text = complaint_text.strip()
    has_transport_word = any(keyword in text for keyword in gaode_transport_keywords)
    has_hotel_word = any(keyword in text for keyword in gaode_hotel_protected_keywords)
    if has_transport_word and not has_hotel_word:
        return False
    return True
final_df = final_df.copy()
final_df.loc[:, '发起投诉内容'] = final_df['发起投诉内容'].astype(str)
final_df.loc[:, '保留'] = final_df['发起投诉内容'].apply(is_gaode_travel_complaint)
filtered_final_df = final_df[final_df['保留']]

initial_count = len(final_df)
filtered_count = len(filtered_final_df)
removed_count = initial_count - filtered_count
print(f"删除的记录数: {removed_count:,}")

filtered_final_count = len(filtered_final_df)
# 保存合并后的结果到一个新的 CSV 文件中
output_filename = '/Users/chenyaxin/Desktop/InternetTourismConvention/travel_complaints.csv'
filtered_final_df.to_csv(output_filename, index=False)
print(f"合并后的投诉内容已写入 {output_filename}")

print("\n===== 数据处理总结 =====")
print(f"初始旅游投诉数据: {original_count:,} 条")
print(f"  特定投诉对象记录: {specific_count:,} 条")
print(f"  筛选后特定投诉对象记录: {filtered_specific_count:,} 条")
print(f"  其他投诉对象记录: {other_count:,} 条")
print(f"合并后总记录: {merged_count:,} 条")
print(f"根据删除列表移除: {removed_by_deletion:,} 条")
print(f"最终保留记录: {filtered_final_count:,} 条")
print("========================")