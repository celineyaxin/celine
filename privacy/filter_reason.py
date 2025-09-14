import os
import pandas as pd
import numpy as np
from datetime import datetime
import re

# 设置文件夹路径
data_folder = "/Volumes/T9/temp_files"
output_file = "/Users/chenyaxin/Desktop/案由统计结果.xlsx"

# 定义时间范围
start_date = datetime(2019, 1, 1)
end_date = datetime(2021, 7, 31)

print(f"开始提取 {start_date.strftime('%Y年%m月')} 到 {end_date.strftime('%Y年%m月')} 的案由信息")

# 获取所有CSV文件，排除隐藏文件和临时文件
all_files = [f for f in os.listdir(data_folder) 
             if f.endswith('.csv') and 
             not f.startswith('.') and  # 排除以点开头的文件
             not f.startswith('~')]     # 排除以波浪线开头的临时文件

# 用于存储所有案由信息
all_causes = []

# 处理每个文件
for file in all_files:
    try:
        file_path = os.path.join(data_folder, file)
        
        # 读取CSV文件
        df = pd.read_csv(file_path)
        
        # 检查是否有裁判日期字段和案由字段
        if '裁判日期' not in df.columns:
            print(f"跳过文件: {file} (没有找到'裁判日期'字段)")
            continue
            
        # 确定案由字段名称
        cause_field = None
        cause_fields = ['案由', '事由', '案件类型', '案件事由', '处罚事由']
        for field in cause_fields:
            if field in df.columns:
                cause_field = field
                break
        
        if cause_field is None:
            print(f"跳过文件: {file} (未找到案由相关字段)")
            continue
            
        # 转换日期格式
        df['裁判日期'] = pd.to_datetime(df['裁判日期'], errors='coerce')
        
        # 移除无效日期
        df = df[df['裁判日期'].notna()]
        
        if len(df) == 0:
            print(f"跳过文件: {file} (没有有效的日期数据)")
            continue
            
        # 筛选指定时间范围内的数据
        period_data = df[(df['裁判日期'] >= start_date) & (df['裁判日期'] <= end_date)]
        
        if len(period_data) == 0:
            print(f"跳过文件: {file} (筛选后没有符合时间范围的数据)")
            continue
        
        # 提取案由信息
        causes = period_data[cause_field].dropna().unique().tolist()
        all_causes.extend(causes)
        
        print(f"已处理文件: {file} - 提取到 {len(causes)} 个案由")
        
    except Exception as e:
        print(f"处理文件 {file} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()

# 处理案由数据
if all_causes:
    # 创建案由DataFrame
    cause_df = pd.DataFrame({'案由': all_causes})
    
    # 基本数据清洗
    cause_df['案由'] = cause_df['案由'].str.strip()  # 去除前后空格
    
    # 删除重复值
    unique_causes = cause_df.drop_duplicates()
    
    # 按案由排序
    unique_causes = unique_causes.sort_values('案由')
    
    # 保存结果到Excel
    unique_causes.to_excel(output_file, index=False)
    print(f"\n统计完成! 共找到 {len(unique_causes)} 个不同的案由")
    print(f"结果已保存到: {output_file}")
    
    # 显示前20个案由
    print("\n前20个案由:")
    for i, cause in enumerate(unique_causes['案由'].head(20), 1):
        print(f"{i}. {cause}")
    
    # 可选: 统计案由出现频率
    cause_counts = cause_df['案由'].value_counts().reset_index()
    cause_counts.columns = ['案由', '出现次数']
    cause_counts = cause_counts.sort_values('出现次数', ascending=False)
    
    # 保存频率统计
    freq_output_file = "/Users/chenyaxin/Desktop/案由频率统计.xlsx"
    cause_counts.to_excel(freq_output_file, index=False)
    print(f"\n案由频率统计已保存到: {freq_output_file}")
    
    # 显示前10个最常见的案由
    print("\n前10个最常见的案由:")
    for i, row in cause_counts.head(10).iterrows():
        print(f"{i+1}. {row['案由']} (出现 {row['出现次数']} 次)")
    
else:
    print("未找到符合时间范围的案由数据")
