import pandas as pd

# 1. 读取欺诈预测结果并筛选欺诈投诉
fraud_df = pd.read_csv('/Users/chenyaxin/Desktop/privacy/data/fraud_predictions_20180101_0000_20231231_2359.csv')
fraud_df = fraud_df[fraud_df['prediction'] == 1].copy()

# 2. 读取合并结果并提取投诉编号
merged_df = pd.read_excel('/Users/chenyaxin/Desktop/合并结果.xlsx')
merged_complaint_ids = merged_df['投诉编号'].tolist()
print(f"合并结果中的投诉编号数量: {len(merged_complaint_ids)}")

# 3. 筛选匹配的欺诈投诉
matched_fraud = fraud_df[fraud_df['投诉编号'].isin(merged_complaint_ids)].copy()
print("\n=== 匹配结果验证 ===")
print(f"匹配到的欺诈投诉数量: {len(matched_fraud)}")
print(f"匹配结果是否全部来自欺诈样本: {all(matched_fraud['prediction'] == 1)}")
print(f"匹配结果中的投诉编号是否都在欺诈样本中: {all(id in fraud_df['投诉编号'].values for id in matched_fraud['投诉编号'])}")

# 4. 筛选未匹配的欺诈投诉作为补充池
unmatched_fraud = fraud_df[~fraud_df['投诉编号'].isin(merged_complaint_ids)].copy()

# 5. 计算需要补充的数量
num_matched = len(matched_fraud)
num_needed = max(0, 5001 - num_matched)

# 6. 从补充池中筛选非重复投诉
if num_needed > 0:
    # 提取所有投诉内容
    existing_contents = set(matched_fraud['投诉内容'].dropna().astype(str))

    # 筛选补充池中不重复的投诉
    supplement = unmatched_fraud.copy()
    supplement = supplement[~supplement['投诉内容'].astype(str).isin(existing_contents)]
    
    # 按商家和内容去重（保留每个商家的第一条记录）
    supplement = supplement.drop_duplicates(subset=['投诉商家', '投诉内容'])
    
    # 确保商家不重复（每个商家只取一条记录）
    supplement = supplement.drop_duplicates(subset=['投诉商家'])
    supplement = supplement.sample(frac=1, random_state=42).reset_index(drop=True)

    # 取所需数量的投诉
    if len(supplement) > num_needed:
        supplement = supplement.head(num_needed)
    else:
        print(f"警告: 只有 {len(supplement)} 条可用补充记录，总记录数为 {num_matched + len(supplement)}")
else:
    supplement = pd.DataFrame()

# 7. 合并最终结果
final_df = pd.concat([matched_fraud, supplement], ignore_index=True)

# 8. 检查最终记录数
print(f"匹配记录数: {num_matched}")
print(f"补充记录数: {len(supplement)}")
print(f"最终总记录数: {len(final_df)}")

# 9. 剔除 prediction 列并保存到 CSV 文件
final_df_without_prediction = final_df.drop(columns=['prediction'])
final_df_without_prediction.to_csv('/Users/chenyaxin/Desktop/privacy/分类数据处理/最终欺诈投诉数据集.csv', index=False)
print("处理完成! 结果已保存到 '最终欺诈投诉数据集.csv'")

# 10. 将补充数据追加到合并结果的 Excel 文件中
supplement_without_prediction = supplement.drop(columns=['prediction'], errors='ignore')

# 将补充数据追加到原始数据的下方
updated_merged_df = pd.concat([merged_df, supplement_without_prediction], ignore_index=True)

# 保存到新的 Excel 文件
updated_merged_df.to_excel('/Users/chenyaxin/Desktop/合并结果_更新.xlsx', index=False)
print("补充数据已追加到新的 Excel 文件 '合并结果_更新.xlsx' 的 Sheet1 中")