import os
import pandas as pd
import numpy as np
from datetime import datetime
import re

# 设置文件夹路径
data_folder = "/Volumes/T9/temp_files"
output_file = "/Users/chenyaxin/Desktop/企业处罚记录面板数据.xlsx"

# 定义时间范围
start_date = datetime(2016, 8, 1)
end_date = datetime(2021, 7, 31)

print(f"开始统计 {start_date.strftime('%Y年%m月')} 到 {end_date.strftime('%Y年%m月')} 的企业处罚记录")

all_files = [f for f in os.listdir(data_folder) 
             if f.endswith('.csv') and 
             not f.startswith('.') and  # 排除以点开头的文件
             not f.startswith('~') and  # 排除以波浪线开头的临时文件
             not f.startswith('ws') and # 排除以ws开头的文件
             not f.startswith('s41')]   # 排除以s41开头的文件
# 用于存储所有企业处罚记录
all_penalties = []

# 处理每个文件
for file in all_files:
    try:
        file_path = os.path.join(data_folder, file)
        
        # 读取CSV文件
        df = pd.read_csv(file_path)
        
        # 检查是否有裁判日期字段
        if '裁判日期' not in df.columns:
            print(f"跳过文件: {file} (没有找到'裁判日期'字段)")
            continue
            
        # 转换日期格式
        df['裁判日期'] = pd.to_datetime(df['裁判日期'], errors='coerce')
        
        # 移除无效日期
        df = df[df['裁判日期'].notna()]
        
        if len(df) == 0:
            print(f"跳过文件: {file} (没有有效的日期数据)")
            continue
            
        # 提取年月信息
        df['年月'] = df['裁判日期'].dt.to_period('M')
        df['年月_str'] = df['年月'].astype(str).str.replace('-', '')
            
        # 筛选指定时间范围内的数据
        period_data = df[(df['裁判日期'] >= start_date) & (df['裁判日期'] <= end_date)].copy()
        
        if len(period_data) == 0:
            print(f"跳过文件: {file} (筛选后没有符合时间范围的数据)")
            continue
        
        # 确定企业名称字段
        company_field = None
        company_fields = ['企业名称', '企业名', '公司名称', '公司名', '被处罚企业', '当事人']
        for field in company_fields:
            if field in period_data.columns:
                company_field = field
                break
        
        if company_field is None:
            print(f"跳过文件: {file} (未找到企业名称相关字段)")
            continue
        
        period_data['企业名称_清洗'] = period_data[company_field].str.strip().fillna('未知企业')
        
        # 按企业和年月分组统计
        for (company, year_month), group in period_data.groupby(['企业名称_清洗', '年月_str']):
            # 添加到结果列表
            all_penalties.append({
                '企业名称': company,
                '年月': year_month,
                '处罚记录数': len(group),
                '来源文件': file
            })
        
        print(f"已处理文件: {file}")
        
    except Exception as e:
        print(f"处理文件 {file} 时出错: {str(e)}")
        import traceback
        traceback.print_exc()

# 创建面板数据
if all_penalties:
    panel_data = pd.DataFrame(all_penalties)
    
    # 按企业和年月汇总
    panel_summary = panel_data.groupby(['企业名称', '年月']).agg({
        '处罚记录数': 'sum',
        '来源文件': lambda x: ', '.join(x.unique())
    }).reset_index()
    
    # 提取年份和月份
    panel_summary['年份'] = panel_summary['年月'].str[:4].astype(int)
    panel_summary['月份'] = panel_summary['年月'].str[4:].astype(int)
    
    # 排序
    panel_summary = panel_summary.sort_values(['企业名称', '年份', '月份'])
    
    # 保存结果到Excel
    panel_summary.to_excel(output_file, index=False)
    print(f"\n统计完成! 结果已保存到: {output_file}")
    
    # 打印汇总统计
    total_companies = panel_summary['企业名称'].nunique()
    total_months = panel_summary['年月'].nunique()
    total_records = panel_summary['处罚记录数'].sum()
    
    print(f"\n汇总统计:")
    print(f"涉及企业数: {total_companies}")
    print(f"涉及月份数: {total_months}")
    print(f"总处罚记录数: {total_records}")
    
    # 显示前几行数据
    print("\n数据示例:")
    print(panel_summary.head(10))
    
    # 可选: 创建透视表格式的数据
    pivot_table = panel_summary.pivot_table(
        values='处罚记录数', 
        index='企业名称', 
        columns='年月', 
        fill_value=0
    )
    
    pivot_output_file = "/Users/chenyaxin/Desktop/企业处罚记录透视表.xlsx"
    pivot_table.to_excel(pivot_output_file)
    print(f"透视表已保存到: {pivot_output_file}")
    
else:
    print("未找到符合时间范围的数据")