import pandas as pd
import os
import glob
from datetime import datetime
import numpy as np

def generate_complete_timeseries(input_dir, output_dir):
    """
    生成完整的时间序列数据：企业名称-季度-是否被告-被告次数
    """
    print("开始生成完整时间序列数据...")
    
    # 读取所有文件
    result_files = glob.glob(os.path.join(input_dir, "原被告提取结果_*.csv"))
    
    # 准备存储所有被告记录
    all_defendant_records = []
    
    # 统计信息
    stats = {
        'total_files': len(result_files),
        'total_records': 0,
        'defendant_records': 0,
        'companies': set(),
        'quarters': set(),
        'start_date': None,
        'end_date': None
    }
    
    for result_file in sorted(result_files):
        try:
            print(f"处理文件: {os.path.basename(result_file)}")
            
            # 读取数据，限制全文列长度
            df = pd.read_csv(result_file, encoding='utf-8-sig')
            
            # 如果存在全文列，截断为前300个字符
            if '全文' in df.columns:
                df['全文'] = df['全文'].astype(str).str[:300] + '...'
            
            stats['total_records'] += len(df)
            
            # 筛选被告记录
            defendant_df = df[df['企业角色'] == '被告'].copy()
            
            if len(defendant_df) > 0:
                # 使用裁判日期
                date_column = '裁判日期'
                
                if date_column in defendant_df.columns:
                    defendant_df[date_column] = pd.to_datetime(defendant_df[date_column], errors='coerce')
                    
                    # 提取季度信息
                    defendant_df['季度'] = defendant_df[date_column].dt.to_period('Q')
                    
                    # 移除日期无效的记录
                    defendant_df = defendant_df[defendant_df['季度'].notna()]
                    
                    if len(defendant_df) > 0:
                        # 选择需要的字段
                        useful_columns = ['企业名称', date_column, '季度', '案件名称', '案由']
                        if '全文' in defendant_df.columns:
                            useful_columns.append('全文')
                        
                        selected_data = defendant_df[useful_columns].copy()
                        selected_data['来源文件'] = os.path.basename(result_file)
                        all_defendant_records.append(selected_data)
                        
                        # 更新统计
                        stats['defendant_records'] += len(defendant_df)
                        stats['companies'].update(defendant_df['企业名称'].unique())
                        stats['quarters'].update(defendant_df['季度'].unique())
                        
                        # 更新日期范围
                        if stats['start_date'] is None or defendant_df[date_column].min() < stats['start_date']:
                            stats['start_date'] = defendant_df[date_column].min()
                        if stats['end_date'] is None or defendant_df[date_column].max() > stats['end_date']:
                            stats['end_date'] = defendant_df[date_column].max()
                        
                        print(f"  找到 {len(defendant_df)} 条被告记录")
                    else:
                        print(f"  无有效日期记录")
                else:
                    print(f"  未找到日期字段")
            else:
                print(f"  无被告记录")
                
        except Exception as e:
            print(f"  处理文件时出错: {e}")
    
    if not all_defendant_records:
        print("未找到任何被告记录")
        return None
    
    # 合并所有被告记录
    print("合并所有数据...")
    all_defendant_data = pd.concat(all_defendant_records, ignore_index=True)
    
    # 按企业和季度聚合
    print("按企业和季度聚合数据...")
    quarterly_stats = all_defendant_data.groupby(['企业名称', '季度']).agg(
        被告次数=('企业名称', 'count')
    ).reset_index()
    
    # 添加是否被告列
    quarterly_stats['是否被告'] = 1
    
    # 创建完整的时间序列面板
    print("创建完整时间序列面板...")
    complete_panel = create_complete_panel(quarterly_stats, stats)
    
    # 更新统计信息
    stats['total_companies'] = len(stats['companies'])
    stats['total_quarters'] = len(stats['quarters'])
    stats['panel_companies'] = complete_panel['企业名称'].nunique()
    stats['panel_quarters'] = complete_panel['季度'].nunique()
    stats['panel_records'] = len(complete_panel)
    
    return complete_panel, all_defendant_data, stats

def create_complete_panel(quarterly_stats, stats):
    """
    创建完整的时间序列面板数据
    """
    # 获取所有唯一企业和季度
    all_companies = list(stats['companies'])
    all_quarters = sorted(list(stats['quarters']))
    
    # 创建所有可能的组合
    from itertools import product
    complete_index = list(product(all_companies, all_quarters))
    complete_panel = pd.DataFrame(complete_index, columns=['企业名称', '季度'])
    
    # 合并实际数据
    complete_panel = complete_panel.merge(quarterly_stats, on=['企业名称', '季度'], how='left')
    
    # 填充缺失值
    complete_panel['被告次数'] = complete_panel['被告次数'].fillna(0)
    complete_panel['是否被告'] = complete_panel['是否被告'].fillna(0).astype(int)
    
    # 按企业和季度排序
    complete_panel = complete_panel.sort_values(['企业名称', '季度']).reset_index(drop=True)
    
    return complete_panel

def save_complete_timeseries(panel_data, raw_data, stats, output_dir):
    """
    保存完整的时间序列数据
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成时间戳用于文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"企业被告时间序列_{timestamp}.xlsx")
    
    print(f"保存结果到: {output_file}")
    
    # 创建Excel写入器
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 1. 保存时间序列面板数据
        panel_data.to_excel(writer, sheet_name='时间序列面板', index=False)
        
        # 2. 保存原始被告记录（前10000行，避免文件过大）
        raw_data.head(10000).to_excel(writer, sheet_name='原始被告记录', index=False)
        
        # 3. 保存统计摘要
        stats_df = pd.DataFrame([
            {'统计项': '处理文件数', '数值': stats['total_files']},
            {'统计项': '总记录数', '数值': stats['total_records']},
            {'统计项': '被告记录数', '数值': stats['defendant_records']},
            {'统计项': '涉及企业数', '数值': stats['total_companies']},
            {'统计项': '时间跨度(季度数)', '数值': stats['total_quarters']},
            {'统计项': '开始日期', '数值': stats['start_date']},
            {'统计项': '结束日期', '数值': stats['end_date']},
            {'统计项': '面板数据企业数', '数值': stats['panel_companies']},
            {'统计项': '面板数据季度数', '数值': stats['panel_quarters']},
            {'统计项': '面板数据记录数', '数值': stats['panel_records']}
        ])
        stats_df.to_excel(writer, sheet_name='统计摘要', index=False)
        
        # 4. 保存企业汇总统计
        company_summary = panel_data.groupby('企业名称').agg({
            '是否被告': 'sum',
            '被告次数': 'sum'
        }).reset_index()
        company_summary.columns = ['企业名称', '有被告记录的季度数', '总被告次数']
        company_summary = company_summary.sort_values('总被告次数', ascending=False)
        company_summary.to_excel(writer, sheet_name='企业汇总', index=False)
        
        # 5. 保存季度汇总统计
        quarter_summary = panel_data.groupby('季度').agg({
            '是否被告': 'sum',  # 有被告记录的企业数量
            '被告次数': 'sum'   # 总被告次数
        }).reset_index()
        quarter_summary.columns = ['季度', '有被告记录的企业数', '总被告次数']
        quarter_summary = quarter_summary.sort_values('季度')
        quarter_summary.to_excel(writer, sheet_name='季度汇总', index=False)
    
    print("数据保存完成!")
    
    # 同时保存CSV格式的时间序列面板（便于其他分析）
    csv_file = os.path.join(output_dir, f"企业被告时间序列_{timestamp}.csv")
    panel_data.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"CSV格式数据已保存到: {csv_file}")
    
    return output_file

def print_final_summary(stats, output_file):
    """
    打印最终汇总信息
    """
    print("\n" + "="*60)
    print("时间序列生成完成!")
    print("="*60)
    print(f"输出文件: {output_file}")
    print(f"处理文件数: {stats['total_files']}")
    print(f"总记录数: {stats['total_records']:,}")
    print(f"被告记录数: {stats['defendant_records']:,}")
    print(f"涉及企业数: {stats['total_companies']:,}")
    print(f"时间跨度: {stats['start_date']} 到 {stats['end_date']}")
    print(f"季度数: {stats['total_quarters']}")
    print(f"面板数据: {stats['panel_companies']:,} 家企业 × {stats['panel_quarters']} 个季度 = {stats['panel_records']:,} 条记录")
    
    # 计算覆盖率
    if stats['panel_records'] > 0:
        defendant_coverage = (stats['defendant_records'] / stats['panel_records']) * 100
        print(f"被告记录覆盖率: {defendant_coverage:.4f}%")
    
    print("\n数据文件包含以下工作表:")
    print("  - 时间序列面板: 完整的企业-季度面板数据")
    print("  - 原始被告记录: 所有被告记录的抽样")
    print("  - 统计摘要: 整体统计信息")
    print("  - 企业汇总: 按企业汇总的被告统计")
    print("  - 季度汇总: 按季度汇总的被告统计")

# 主程序
if __name__ == "__main__":
    input_dir = "/Volumes/T9/原被告提取结果"
    output_dir = "/Volumes/T9/时间序列完整数据"
    
    print("开始生成企业被告时间序列数据...")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # 生成完整时间序列
    panel_data, raw_data, stats = generate_complete_timeseries(input_dir, output_dir)
    
    if panel_data is not None:
        # 保存结果
        output_file = save_complete_timeseries(panel_data, raw_data, stats, output_dir)
        
        # 打印汇总信息
        print_final_summary(stats, output_file)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"\n总处理时间: {duration:.2f} 秒")
    else:
        print("未能生成时间序列数据，请检查输入文件。")