import pandas as pd
import random

# 设置随机种子，以便结果可复现
random.seed(0)

# 读取CSV文件
df = pd.read_csv('/Users/chenyaxin/Desktop/websitdata/bert/results/是否明示/delete_hostility.csv')

# 设置你想要提取的样本数量
num_samples = 1000  # 例如，提取1000个样本

# 随机选择样本
sampled_df = df.sample(n=num_samples)

# 保存到新的CSV文件
sampled_df.to_csv('/Users/chenyaxin/Desktop/websitdata/random_sample.csv', index=False)