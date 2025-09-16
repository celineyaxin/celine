import pandas as pd
import numpy as np
from collections import defaultdict

# 数据分析相关关键词（中英文对照）
data_analysis_keywords = [
    "3D可视化", "数据探索解决方案", "可视化能力", "数据洞察", "高级数据录入", 
    "商业分析", "可视化软件", "数据生产流程", "数据分析", "临床数据交换", 
    "商业智能", "数据看板", "数据分析师", "临床数据分析", "业务洞察", 
    "数据输入", "数据录入", "信息可视化", "公司数据", "数据输入优先级", 
    "数据录入优先级", "客户洞察", "智能数据", "数据管理平台（DMP）", 
    "分析可视化", "显示数据", "气候数据分析", "数据平台即服务", "动态图表", 
    "市场洞察", "源数据", "数据科学家", "可视化分析", "图像数据", 
    "监控数据", "数据使用", "可视化产品", "报告展示", "税务局数据", 
    "数据可视化", "可视化信息", "挖掘分析", "营销云", "分析", 
    "可视化分析", "挖掘数据价值", "可视化", "BI分析", "可视化演示", 
    "探索数据可能性", "计算数据", "BI可视化", "可视化图表", "数据专线", 
    "账单数据分析", "BI商业智能", "可视化处理", "数据交换", "透视分析", 
    "BI系统", "可视化大屏", "银联数据", "商业分析", "可视化显示", 
    "数据处理", "银行数据", "可视化展览", "集团数据", "数据发现", 
    "可视化工具", "数据大屏", "预测分析", "数据科学", "可视化平台", 
    "数据展示", "高级分析", "可视化技术", "数据应用", "信息分析师", 
    "可视化报告", "数据接口", "机器工程师", "可视化数据", "数据运营", 
    "报告分析师", "可视化解决方案", "数据智能", "大规模数据探索解决方案", 
    "可视化界面", "数据服务"
]

def filter_data_analysis_jobs(csv_file, job_desc_column):
    """
    筛选包含数据分析关键词的职位
    
    参数:
    csv_file: CSV文件路径
    job_desc_column: 职位描述列名
    
    返回:
    筛选后的DataFrame
    """
    # 读取CSV文件
    df = pd.read_csv(csv_file)
    
    # 检查必要的列是否存在
    required_columns = [job_desc_column, '招聘发布年份', '来源', '企业名称']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"CSV文件中缺少必要的列: {col}")
    
    # 筛选包含关键词的职位
    def contains_keyword(text):
        if pd.isna(text):
            return False
        text = str(text)
        return any(keyword in text for keyword in data_analysis_keywords)
    
    mask = df[job_desc_column].apply(contains_keyword)
    filtered_df = df[mask].copy()
    
    print(f"原始数据行数: {len(df)}")
    print(f"筛选后数据行数: {len(filtered_df)}")
    
    return filtered_df

def remove_duplicate_job_descriptions(df, job_desc_column):
    """
    去除职位描述重复的行
    
    参数:
    df: DataFrame
    job_desc_column: 职位描述列名
    
    返回:
    去重后的DataFrame
    """
    # 去除完全重复的行
    df_no_duplicates = df.drop_duplicates(subset=[job_desc_column], keep='first')
    
    print(f"去重前行数: {len(df)}")
    print(f"去重后行数: {len(df_no_duplicates)}")
    
    return df_no_duplicates

def stratified_sampling(df, sample_size=5000):
    """
    按年份和来源进行分层抽样，并确保企业分布均匀
    
    参数:
    df: DataFrame
    sample_size: 目标样本量
    
    返回:
    抽样后的DataFrame
    """
    # 如果数据量小于目标样本量，直接返回所有数据
    if len(df) <= sample_size:
        return df
    
    # 计算每个年份-来源组合的样本数（按比例）
    stratum_counts = df.groupby(['招聘发布年份', '来源']).size()
    total_count = len(df)
    stratum_samples = {}
    
    for (year, source), count in stratum_counts.items():
        proportion = count / total_count
        stratum_samples[(year, source)] = max(1, round(proportion * sample_size))
    
    # 调整样本数，确保总和等于目标样本量
    total_allocated = sum(stratum_samples.values())
    if total_allocated != sample_size:
        # 按比例调整样本数
        for key in stratum_samples:
            stratum_samples[key] = round(stratum_samples[key] * sample_size / total_allocated)
        
        # 确保每个层至少有一个样本
        for key in stratum_samples:
            if stratum_samples[key] < 1:
                stratum_samples[key] = 1
        
        # 再次调整总和
        total_allocated = sum(stratum_samples.values())
        if total_allocated != sample_size:
            # 简单调整最大的层
            max_key = max(stratum_samples, key=stratum_samples.get)
            stratum_samples[max_key] += sample_size - total_allocated
    
    # 进行分层抽样，同时考虑企业分布
    sampled_dfs = []
    
    for (year, source), n_samples in stratum_samples.items():
        stratum_df = df[(df['招聘发布年份'] == year) & (df['来源'] == source)]
        
        # 如果该层的样本数少于或等于目标样本数，直接取全部
        if len(stratum_df) <= n_samples:
            sampled_dfs.append(stratum_df)
            continue
        
        # 计算每个企业在该层中的分布
        company_counts = stratum_df['企业名称'].value_counts()
        company_weights = 1 / company_counts  # 企业出现次数越少，权重越大
        
        # 将权重映射到每个职位
        stratum_df = stratum_df.copy()
        stratum_df['weight'] = stratum_df['企业名称'].map(company_weights)
        
        # 归一化权重
        total_weight = stratum_df['weight'].sum()
        stratum_df['normalized_weight'] = stratum_df['weight'] / total_weight
        
        # 按权重抽样
        sampled_stratum = stratum_df.sample(
            n=n_samples, 
            weights='normalized_weight', 
            random_state=42,  # 设置随机种子以确保可重复性
            replace=False
        )
        
        sampled_dfs.append(sampled_stratum)
    
    # 合并所有抽样结果
    result_df = pd.concat(sampled_dfs, ignore_index=True)
    
    # 如果最终样本量不等于目标样本量，进行简单调整
    if len(result_df) != sample_size:
        if len(result_df) > sample_size:
            result_df = result_df.sample(n=sample_size, random_state=42)
        else:
            # 从原始数据中补充样本，优先选择企业分布较少的数据
            remaining_df = df[~df.index.isin(result_df.index)]
            company_counts = result_df['企业名称'].value_counts()
            
            # 计算每个企业的权重（出现次数越少，权重越大）
            company_weights = 1 / (company_counts + 1)  # 加1避免除零错误
            
            # 将权重映射到剩余数据
            remaining_df = remaining_df.copy()
            remaining_df['weight'] = remaining_df['企业名称'].map(
                lambda x: company_weights.get(x, 1)  # 如果企业未在抽样中出现，权重为1
            )
            
            # 归一化权重
            total_weight = remaining_df['weight'].sum()
            remaining_df['normalized_weight'] = remaining_df['weight'] / total_weight
            
            # 补充抽样
            additional_samples = remaining_df.sample(
                n=sample_size - len(result_df),
                weights='normalized_weight',
                random_state=42,
                replace=False
            )
            
            result_df = pd.concat([result_df, additional_samples], ignore_index=True)
    
    print(f"最终抽样样本量: {len(result_df)}")
    return result_df

def main():
    # 文件路径和列名配置
    csv_file_path = '/Users/chenyaxin/Desktop/上市公司投诉数据探究/人工智能/上市公司招聘大数据/上市公司招聘大数据2014-2023年.csv'  # 替换为你的CSV文件路径
    job_description_column = "职位描述"  # 替换为您的职位描述列名
    
    try:
        # 步骤1: 筛选数据分析相关职位
        print("正在筛选数据分析相关职位...")
        filtered_jobs = filter_data_analysis_jobs(csv_file_path, job_description_column)
        
        # 步骤2: 去除职位描述重复的行
        print("正在去除重复的职位描述...")
        unique_jobs = remove_duplicate_job_descriptions(filtered_jobs, job_description_column)
        
        # 步骤3: 分层抽样
        print("正在进行分层抽样...")
        sampled_jobs = stratified_sampling(unique_jobs, sample_size=5000)
        
        # 保存结果
        output_file = "/Users/chenyaxin/Desktop/数据分析职位样本.csv"
        sampled_jobs.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"抽样结果已保存到: {output_file}")
        
        # 打印抽样分布信息
        print("\n抽样分布情况:")
        print("按年份分布:")
        print(sampled_jobs['招聘发布年份'].value_counts())
        print("\n按来源分布:")
        print(sampled_jobs['来源'].value_counts())
        print("\n按企业分布 (前20名):")
        print(sampled_jobs['企业名称'].value_counts().head(20))
        
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")

if __name__ == "__main__":
    main()