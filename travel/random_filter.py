import pandas as pd
import numpy as np

input_csv_path = '/Users/chenyaxin/Desktop/InternetTourismConvention/data/travel_complaints.csv'
output_path = '/Users/chenyaxin/Desktop/InternetTourismConvention/travel_sample.csv'

# 读取CSV文件到DataFrame
treatment_df = pd.read_csv(input_csv_path)
total_sample_size = 5000

# 确保数据中有"投诉对象"列
if '投诉对象' not in treatment_df.columns:
    raise ValueError("CSV文件必须包含'投诉对象'列")
treatment_df = treatment_df.drop_duplicates(subset=['发起投诉内容'], keep='first')
# 1. 统计每个商家的投诉数量
merchant_counts = treatment_df['投诉对象'].value_counts().reset_index()
merchant_counts.columns = ['投诉对象', '投诉数量']
merchant_counts = merchant_counts.sort_values('投诉数量', ascending=False)

print(f"共有 {len(merchant_counts)} 个商家")
print(f"投诉最多的前5个商家:")
print(merchant_counts.head(5))

# 2. 设置每个商家的最大样本数
max_per_merchant = 50  # 每个商家最多抽取的样本数
min_per_merchant = 1   # 每个商家至少抽取的样本数

# 3. 确定要覆盖的商家数量
# 目标覆盖60%的商家，但至少覆盖30个商家
target_coverage = min(max(30, int(len(merchant_counts) * 0.6)), len(merchant_counts))
print(f"目标覆盖 {target_coverage} 个商家")

# 4. 选择要覆盖的商家
# 优先选择投诉量中等的商家（避免投诉最多和最少的商家）
sorted_merchants = merchant_counts.sort_values('投诉数量', ascending=True)
selected_merchants = sorted_merchants.iloc[int(len(sorted_merchants)*0.2):int(len(sorted_merchants)*0.8)]
selected_merchants = selected_merchants.sample(n=target_coverage, random_state=42)['投诉对象']

print(f"选择了 {len(selected_merchants)} 个商家进行覆盖")

# 5. 过滤数据，只包含选中的商家
filtered_df = treatment_df[treatment_df['投诉对象'].isin(selected_merchants)]

# 6. 计算每个商家的样本分配
# 基础分配：每个商家至少1个样本
sample_allocations = {merchant: min_per_merchant for merchant in selected_merchants}
remaining_samples = total_sample_size - len(selected_merchants)

# 按商家投诉比例分配剩余样本
merchant_weights = filtered_df['投诉对象'].value_counts(normalize=True)
for merchant in selected_merchants:
    # 计算该商家可分配的最大额外样本
    max_extra = min(max_per_merchant - min_per_merchant, 
                   len(filtered_df[filtered_df['投诉对象'] == merchant]) - min_per_merchant)
    
    # 按比例分配额外样本
    extra_samples = int(merchant_weights[merchant] * remaining_samples)
    
    # 确保不超过最大限制
    sample_allocations[merchant] += min(extra_samples, max_extra)

# 如果总样本数不足，按投诉量从大到小补充
total_allocated = sum(sample_allocations.values())
if total_allocated < total_sample_size:
    remaining = total_sample_size - total_allocated
    # 按投诉量从大到小排序
    sorted_by_count = merchant_counts[merchant_counts['投诉对象'].isin(selected_merchants)]
    sorted_by_count = sorted_by_count.sort_values('投诉数量', ascending=False)
    
    for _, row in sorted_by_count.iterrows():
        merchant = row['投诉对象']
        if remaining <= 0:
            break
            
        # 计算还可增加的样本数
        current = sample_allocations[merchant]
        max_possible = min(max_per_merchant - current, 
                          len(filtered_df[filtered_df['投诉对象'] == merchant]) - current)
        
        if max_possible > 0:
            add_samples = min(remaining, max_possible)
            sample_allocations[merchant] += add_samples
            remaining -= add_samples

# 7. 进行分层抽样
sampled_dfs = []
for merchant, sample_size in sample_allocations.items():
    merchant_df = filtered_df[filtered_df['投诉对象'] == merchant]
    
    if len(merchant_df) <= sample_size:
        # 如果商家样本量不足，取全量
        sampled_dfs.append(merchant_df)
    else:
        sampled_dfs.append(merchant_df.sample(n=sample_size, random_state=42))

# 合并抽样结果
treatment_sample = pd.concat(sampled_dfs, ignore_index=True)

# 8. 如果总样本数不足，从其他商家补充
if len(treatment_sample) < total_sample_size:
    remaining_samples = total_sample_size - len(treatment_sample)
    other_merchants = treatment_df[~treatment_df['投诉对象'].isin(selected_merchants)]
    
    if len(other_merchants) > 0:
        supplement = other_merchants.sample(n=min(remaining_samples, len(other_merchants)), 
                             random_state=42)
        treatment_sample = pd.concat([treatment_sample, supplement], ignore_index=True)

# 9. 最终样本调整（确保正好1000个样本）
if len(treatment_sample) > total_sample_size:
    treatment_sample = treatment_sample.sample(n=total_sample_size, random_state=42)

# 10. 打印抽样统计信息
print("\n===== 抽样统计信息 =====")
print(f"目标样本量: {total_sample_size}")
print(f"实际样本量: {len(treatment_sample)}")
print(f"覆盖商家数量: {treatment_sample['投诉对象'].nunique()}")

# 按商家的分布统计
merchant_dist = treatment_sample['投诉对象'].value_counts()
print("\n按商家分布:")
print(merchant_dist)

# 保存抽样结果
treatment_sample.to_csv(output_path, index=False)
print(f"\n均衡抽样结果已保存至 {output_path}")