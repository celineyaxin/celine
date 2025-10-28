import pandas as pd
import numpy as np
import os

def deduplicate_and_sample(data_file, output_file, sample_size=1000):
    """
    对银行问答数据进行去重和分层抽样
    
    参数:
    data_file: 银行问答数据文件路径
    output_file: 输出文件路径
    sample_size: 抽样数量，默认为1000
    """
    
    # 读取银行问答数据
    df = pd.read_excel(data_file)
    print(f"原始数据共 {len(df)} 条记录")
    
    # 1. 删除重复值（基于股票代码、提问内容和回复内容）
    # 先创建一个标识重复值的列
    df['内容标识'] = df['股票代码'].astype(str) + '_' + df['提问内容'].astype(str) + '_' + df['回复内容'].astype(str)
    
    # 删除重复值
    df_deduplicated = df.drop_duplicates(subset=['内容标识'])
    print(f"去重后剩余 {len(df_deduplicated)} 条记录")
    
    # 删除临时列
    df_deduplicated = df_deduplicated.drop(columns=['内容标识'])
    
    # 2. 分层抽样：按照年份和股票代码分层
    # 计算每个分层的样本量
    strata = df_deduplicated.groupby(['年份', '股票代码']).size().reset_index(name='count')
    total_count = len(df_deduplicated)
    
    # 计算每个分层应抽取的样本数（按比例）
    strata['sample_size'] = (strata['count'] / total_count * sample_size).round().astype(int)
    
    # 调整样本量以确保总样本量等于目标值
    total_sample = strata['sample_size'].sum()
    if total_sample != sample_size:
        # 计算差异并调整最大的分层
        diff = sample_size - total_sample
        if diff > 0:
            # 增加最大分层的样本量
            max_idx = strata['count'].idxmax()
            strata.loc[max_idx, 'sample_size'] += diff
        else:
            # 减少最大分层的样本量
            max_idx = strata['count'].idxmax()
            strata.loc[max_idx, 'sample_size'] += diff  # diff为负数
    
    # 3. 执行分层抽样
    sampled_data = pd.DataFrame()
    
    for _, row in strata.iterrows():
        year = row['年份']
        stock_code = row['股票代码']
        n_samples = row['sample_size']
        
        # 获取该分层的所有数据
        stratum_data = df_deduplicated[
            (df_deduplicated['年份'] == year) & 
            (df_deduplicated['股票代码'] == stock_code)
        ]
        
        # 如果该分层的数据量小于需要抽取的样本量，则全部抽取
        if len(stratum_data) <= n_samples:
            sampled_stratum = stratum_data
        else:
            # 随机抽样
            sampled_stratum = stratum_data.sample(n=n_samples, random_state=42)
        
        # 添加到总样本中
        sampled_data = pd.concat([sampled_data, sampled_stratum])
    
    print(f"分层抽样后得到 {len(sampled_data)} 条样本")
    
    # 4. 保存结果
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 保存抽样结果
    sampled_data.to_excel(output_file, index=False)
    print(f"抽样结果已保存到 {output_file}")
    
    # 打印抽样分布情况
    sample_distribution = sampled_data.groupby(['年份', '股票代码']).size().reset_index(name='样本量')
    print("\n=== 抽样分布 ===")
    print(sample_distribution)
    
    return sampled_data

# 使用示例
if __name__ == "__main__":
    # 设置参数
    data_file = "/Users/chenyaxin/Desktop/银行互动易问答数据.xlsx"  # 银行问答数据文件
    output_file = "/Users/chenyaxin/Desktop/银行问答样本_1000条.xlsx"  # 输出文件
    
    # 执行去重和抽样
    sampled_data = deduplicate_and_sample(data_file, output_file, sample_size=1000)