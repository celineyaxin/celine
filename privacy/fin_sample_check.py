import pandas as pd
import numpy as np

# 1. 读取原始文件
df = pd.read_csv('/Users/chenyaxin/Desktop/privacy/分类数据处理/classify_fin.csv')

# 2. 删除重复的投诉内容（基于投诉内容列）
df = df.drop_duplicates(subset=['投诉内容'], keep='first')

# 3. 删除部分360借款的投诉（随机删除一定数量）
# 假设商家名称列名为'商家名称'，360借款的投诉太多，我们保留一定数量
# 定义每个商家的最大投诉数量（可根据需求调整）
max_complaints_per_merchant = {
    '360借条': 30,    # 限制360借条最多100条
    '支付宝': 120,      # 限制支付宝最多150条
    '捷信金融': 80,        # 限制还呗最多80条
    '京东金融': 80,
    '来分期': 40,
    '马上消费金融': 40,
    '浦发银行': 20,
    '中信银行': 20,
    '分期乐': 100,
    # 可以继续添加其他商家...
}
# 遍历每个商家，控制其投诉数量
for merchant, max_allowed in max_complaints_per_merchant.items():
    mask = df['投诉商家'] == merchant  # 筛选当前商家的投诉
    current_count = mask.sum()  # 当前商家的投诉数量
    
    if current_count > max_allowed:
        # 随机选择要删除的索引（超出部分）
        to_drop = df[mask].sample(n=current_count - max_allowed).index
        df = df.drop(to_drop)
        print(f"已限制商家【{merchant}】的投诉数量至 {max_allowed} 条，删除了 {len(to_drop)} 条重复投诉。")

# 检查剩余数据量
print("\n处理后数据量:", len(df))
print("各商家投诉分布:")
print(df['投诉商家'].value_counts())

# 4. 从delete_hostility.csv中补充数据
# 读取补充文件
supp_df = pd.read_csv('/Users/chenyaxin/Desktop/websitdata/merge_data6/delete_hostility.csv')

# 确保补充数据不重复（与现有数据比较）
supp_df = supp_df[~supp_df['投诉内容'].isin(df['投诉内容'])]

banned_merchants = ['360借条', '支付宝', '捷信金融', '京东金融', '来分期', '马上消费金融', '浦发银行', 
                    '中信银行', '分期乐']  # 可根据实际情况调整

# 过滤掉禁止补充的商家
supp_df_filtered = supp_df[~supp_df['投诉商家'].isin(banned_merchants)]

# 确保补充数据不重复（与现有数据比较）
supp_df_filtered = supp_df_filtered[~supp_df_filtered['投诉内容'].isin(df['投诉内容'])]

# 按商家分组，从每个商家随机抽取一定数量
needed = 5000 - len(df)
supp_groups = supp_df_filtered.groupby('投诉商家')  # 只对未被禁止的商家分组

# 从每个商家抽取大致相同数量的投诉（按比例）
sample_per_group = max(1, needed // len(supp_groups.groups))
supp_samples = []

for name, group in supp_groups:
    # 确保不抽取超过该商家可用的投诉数量
    n = min(sample_per_group, len(group))
    if n > 0:
        supp_samples.append(group.sample(n=n))

# 如果还不够，再随机补充
if len(pd.concat(supp_samples)) < needed:
    remaining = needed - len(pd.concat(supp_samples))
    # 从剩余数据中随机抽取（确保不重复）
    remaining_data = supp_df_filtered[~supp_df_filtered.index.isin([i for s in supp_samples for i in s.index])]
    if len(remaining_data) > 0:
        supp_samples.append(remaining_data.sample(n=min(remaining, len(remaining_data))))

# 合并补充数据
supp_final = pd.concat(supp_samples) if supp_samples else pd.DataFrame()
df_final = pd.concat([df, supp_final]).sample(frac=1).reset_index(drop=True)  # 打乱顺序

# 确保最终是5000条
df_final = df_final.head(5000)

# 保存结果
df_final.to_csv('/Users/chenyaxin/Desktop/privacy/分类数据处理/classify_fin_processed.csv', index=False)

print(f"处理完成！最终数据量: {len(df_final)}条")
print("商家分布统计:")
print(df_final['投诉商家'].value_counts())
