import pandas as pd
import numpy as np
import random

def filter_and_sample_data(input_file, output_file):
    """
    处理Excel文件中的行政处罚数据：
    1. 过滤2018年及之后的处罚信息
    2. 按被罚单位名称和处罚年分层抽样1000条数据
    3. 保存为CSV文件
    
    Args:
        input_file (str): 输入Excel文件路径
        output_file (str): 输出CSV文件路径
    """
    try:
        # 读取Excel文件
        print("正在读取Excel文件...")
        df = pd.read_excel(input_file)
        
        # 检查必要的列是否存在
        required_columns = ['处罚年', '被罚单位名称']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Excel文件中未找到'{col}'列")
        
        # 过滤2018年及之后的数据
        print("过滤2018年及之后的数据...")
        # 确保处罚年是数值类型
        df['处罚年'] = pd.to_numeric(df['处罚年'], errors='coerce')
        df_filtered = df[df['处罚年'] >= 2018].copy()
        
        print(f"过滤后剩余 {len(df_filtered)} 条记录")
        
        # 分层抽样
        print("进行分层抽样...")
        
        # 确定每层的样本数量
        strata = df_filtered.groupby(['被罚单位名称', '处罚年']).size().reset_index(name='count')
        total_strata = len(strata)
        
        # 计算每层应该抽取的样本数
        # 确保每层至少抽取1条，但不超过该层的总记录数
        samples_per_stratum = max(1, min(1000 // total_strata, 100))
        
        # 如果计算出的样本数太少，增加样本数
        if total_strata * samples_per_stratum < 1000:
            samples_per_stratum = min(1000 // total_strata + 1, 100)
        
        print(f"共有 {total_strata} 个层级，每层抽取 {samples_per_stratum} 条数据")
        
        # 进行分层抽样
        sampled_data = []
        for _, stratum in strata.iterrows():
            company = stratum['被罚单位名称']
            year = stratum['处罚年']
            count = stratum['count']
            
            # 获取该层的所有数据
            stratum_data = df_filtered[
                (df_filtered['被罚单位名称'] == company) & 
                (df_filtered['处罚年'] == year)
            ]
            
            # 确定实际抽取的样本数（不超过该层总记录数）
            n_samples = min(samples_per_stratum, count)
            
            # 随机抽样
            if n_samples > 0:
                sampled_stratum = stratum_data.sample(n=n_samples, random_state=42)
                sampled_data.append(sampled_stratum)
        
        # 合并所有抽样数据
        df_sampled = pd.concat(sampled_data, ignore_index=True)
        
        # 如果样本量超过1000，随机抽取1000条
        if len(df_sampled) > 1000:
            df_sampled = df_sampled.sample(n=1000, random_state=42)
        
        print(f"最终抽样 {len(df_sampled)} 条记录")
        
        # 保存为CSV文件
        print(f"保存结果到 {output_file}...")
        df_sampled.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        # 打印抽样结果的统计信息
        print("\n抽样结果统计:")
        print(f"- 总记录数: {len(df_sampled)}")
        print(f"- 涉及公司数: {df_sampled['被罚单位名称'].nunique()}")
        print(f"- 涉及年份: {sorted(df_sampled['处罚年'].unique())}")
        
        # 按年份统计
        year_counts = df_sampled['处罚年'].value_counts().sort_index()
        print("\n按年份分布:")
        for year, count in year_counts.items():
            print(f"  {int(year)}年: {count}条")
            
        # 按公司统计（前10名）
        company_counts = df_sampled['被罚单位名称'].value_counts()
        print(f"\n按公司分布 (前10名):")
        for company, count in company_counts.head(10).items():
            print(f"  {company}: {count}条")
            
        return df_sampled
        
    except Exception as e:
        print(f"处理数据时出错: {e}")
        return None

# 主程序
if __name__ == "__main__":
    input_file = "/Users/chenyaxin/Desktop/bankcompetition/data/提取所属公司.xlsx"  # 输入的Excel文件路径
    output_file = "/Users/chenyaxin/Desktop/分层抽样结果.csv"  # 输出的CSV文件路径
    
    print("开始处理行政处罚数据...")
    result_df = filter_and_sample_data(input_file, output_file)
    
    if result_df is not None:
        print("\n处理完成！")
    else:
        print("\n处理失败！")