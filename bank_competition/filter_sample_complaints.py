import pandas as pd
import numpy as np

# 读取CSV文件
df = pd.read_csv('/Users/chenyaxin/Desktop/websitdata/merge_data6/delete_hostility.csv')

# 筛选包含"银行"的投诉对象
bank_complaints = df[df['投诉商家'].str.contains('银行', na=False)].copy()

print(f"找到 {len(bank_complaints)} 条银行相关投诉记录")

# 提取年份信息 - 使用正确的日期格式
bank_complaints['年份'] = pd.to_datetime(
    bank_complaints['发布时间'], 
    format='%Y年%m月%d日 %H:%M', 
    errors='coerce'
).dt.year

# 移除无法解析日期的记录
bank_complaints = bank_complaints.dropna(subset=['年份'])
print(f"有效日期记录数: {len(bank_complaints)}")

# 按银行和年份进行分层抽样
def stratified_sample(df, strata_cols, n=1000):
    # 计算每层的样本数量
    strata_counts = df.groupby(strata_cols).size()
    
    # 按比例分配样本
    sample_sizes = (strata_counts / len(df) * n).round().astype(int)
    
    # 确保总样本数不超过n
    while sample_sizes.sum() > n:
        # 从最大的层中减少一个样本
        max_idx = sample_sizes.idxmax()
        sample_sizes[max_idx] -= 1
    
    # 确保总样本数不少于n
    while sample_sizes.sum() < n:
        # 从最大的层中增加一个样本
        max_idx = sample_sizes.idxmax()
        sample_sizes[max_idx] += 1
    
    # 从每层抽取样本
    samples = []
    for stratum, size in sample_sizes.items():
        # 筛选该层的记录
        mask = True
        for i, col in enumerate(strata_cols):
            mask = mask & (df[col] == stratum[i])
        
        stratum_df = df[mask]
        if len(stratum_df) > 0:
            sampled = stratum_df.sample(n=min(size, len(stratum_df)), random_state=42)
            samples.append(sampled)
    
    # 合并样本
    result = pd.concat(samples)
    
    # 如果样本数不足，从剩余数据中随机补充
    if len(result) < n:
        remaining = df[~df.index.isin(result.index)]
        additional = remaining.sample(n=n - len(result), random_state=42)
        result = pd.concat([result, additional])
    
    return result

# 执行分层抽样
sampled_data = stratified_sample(bank_complaints, ['投诉商家', '年份'], 1000)

# 保存结果
sampled_data.to_csv('/Users/chenyaxin/Desktop/bank_complaints_stratified_sample.csv', index=False, encoding='utf-8-sig')

# 输出抽样结果统计
print(f"\n抽样结果:")
print(f"总样本数: {len(sampled_data)}")
print(f"覆盖银行数量: {sampled_data['投诉商家'].nunique()}")
print(f"覆盖年份数量: {sampled_data['年份'].nunique()}")
print(f"各银行样本分布:")
print(sampled_data['投诉商家'].value_counts().head(10))
print(f"\n各年份样本分布:")
print(sampled_data['年份'].value_counts().sort_index())