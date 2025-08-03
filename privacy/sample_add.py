import pandas as pd
import numpy as np
from collections import defaultdict
import random

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

# 4. 筛选未匹配的欺诈投诉作为补充池
unmatched_fraud = fraud_df[~fraud_df['投诉编号'].isin(merged_complaint_ids)].copy()
print(f"未匹配的欺诈投诉数量: {len(unmatched_fraud)}")

# 5. 从投诉时间提取年份信息
# 假设'投诉时间'列包含日期字符串，如"2023-05-15"
unmatched_fraud.loc[:, '年份'] = pd.to_datetime(unmatched_fraud['发布时间']).dt.year

# 6. 确保年份和商家分类列存在
if '年份' not in unmatched_fraud.columns:
    raise ValueError("数据集中缺少'年份'列")
if '投诉商家' not in unmatched_fraud.columns:
    raise ValueError("数据集中缺少'投诉商家'列")

# 7. 分层抽样函数
def stratified_sample(df, strata_columns, sample_size):
    """
    分层抽样函数
    :param df: 数据框
    :param strata_columns: 分层列名列表，如['年份', '投诉商家']
    :param sample_size: 需要抽取的总样本量
    :return: 分层抽样后的数据框
    """
    # 计算每个分层的样本比例
    strata_counts = df.groupby(strata_columns).size()
    strata_props = strata_counts / strata_counts.sum()
    
    # 计算每个分层应抽取的样本数
    strata_samples = (strata_props * sample_size).round().astype(int)
    
    # 确保样本总数等于目标样本量
    total = strata_samples.sum()
    if total < sample_size:
        # 补充不足部分
        diff = sample_size - total
        # 优先补充样本量较大的分层
        largest_strata = strata_counts.nlargest(diff).index
        for idx in largest_strata:
            strata_samples[idx] += 1
            diff -= 1
            if diff == 0:
                break
    elif total > sample_size:
        # 减少多余部分
        diff = total - sample_size
        # 优先减少样本量较小的分层
        smallest_strata = strata_counts.nsmallest(diff).index
        for idx in smallest_strata:
            if strata_samples[idx] > 1:
                strata_samples[idx] -= 1
                diff -= 1
            if diff == 0:
                break
    
    # 执行分层抽样
    samples = []
    for (strata_values, count) in strata_samples.items():
        stratum = df
        for col, val in zip(strata_columns, strata_values):
            stratum = stratum[stratum[col] == val]
        
        # 如果该分层的样本量小于需要抽取的数量，则全部抽取
        n = min(count, len(stratum))
        if n > 0:
            samples.append(stratum.sample(n, random_state=42))
    
    # 合并所有抽样结果
    return pd.concat(samples) if samples else pd.DataFrame()

# 8. 执行分层抽样
target_sample_size = 3000
supplement_sample = stratified_sample(
    unmatched_fraud,
    strata_columns=['年份', '投诉商家'],
    sample_size=target_sample_size
)

# 9. 检查抽样结果
print("\n=== 抽样结果 ===")
print(f"实际抽取样本量: {len(supplement_sample)}")

# 检查年份分布
print("\n年份分布:")
print(supplement_sample['年份'].value_counts().sort_index())

# 检查商家分类分布
print("\n商家分类分布:")
print(supplement_sample['投诉商家'].value_counts())

# 10. 保存结果
output_path = '/Users/chenyaxin/Desktop/privacy/分类数据处理/supplement_fraud_sample_3000.csv'
supplement_sample.to_csv(output_path, index=False)
print(f"\n补充样本已保存至: {output_path}")

# 11. 如果需要，合并所有欺诈样本
final_fraud_set = pd.concat([matched_fraud, supplement_sample], ignore_index=True)
print(f"\n最终欺诈样本总量: {len(final_fraud_set)}")