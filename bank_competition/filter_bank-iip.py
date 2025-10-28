import pandas as pd
import os
import glob
from datetime import datetime

def extract_bank_interaction_data(bank_codes_file, base_dir, years_to_extract, output_file):
    """
    从互动易平台数据中提取指定银行的问答数据
    支持同一年份多个Excel文件的情况，并提供详细处理统计
    
    参数:
    bank_codes_file: 包含银行股票代码的Excel文件路径
    base_dir: 互动易数据根目录
    years_to_extract: 要提取的年份列表，如[2019, 2020, 2021]
    output_file: 输出文件路径
    """
    
    # 1. 读取银行股票代码列表
    bank_codes_df = pd.read_excel(bank_codes_file)
    # 将股票代码转换为字符串并确保格式一致
    bank_codes = bank_codes_df['股票代码'].astype(str).str.zfill(6).tolist()
    print(f"需要提取的银行代码: {bank_codes}")
    
    # 2. 初始化结果DataFrame和统计信息
    all_bank_data = pd.DataFrame()
    processing_stats = []  # 存储每个文件的处理统计
    
    # 3. 遍历指定年份
    for year in years_to_extract:
        year_dir = os.path.join(base_dir, str(year))
        
        # 检查年份目录是否存在
        if not os.path.exists(year_dir):
            print(f"警告: {year_dir} 目录不存在，跳过该年份")
            processing_stats.append({
                '年份': year,
                '文件名': '整个年份目录',
                '状态': '目录不存在',
                '总记录数': 0,
                '银行记录数': 0,
                '处理时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            continue
            
        print(f"正在处理 {year} 年数据...")
        
        # 查找该年份目录下所有相关的Excel文件
        pattern = os.path.join(year_dir, f"用户与公司问答-{year}*.xlsx")
        excel_files = glob.glob(pattern)
        
        if not excel_files:
            print(f"警告: 在 {year_dir} 中未找到匹配的Excel文件")
            processing_stats.append({
                '年份': year,
                '文件名': '所有文件',
                '状态': '未找到文件',
                '总记录数': 0,
                '银行记录数': 0,
                '处理时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            continue
        
        print(f"找到 {len(excel_files)} 个文件: {[os.path.basename(f) for f in excel_files]}")
        
        # 处理每个文件
        year_data = pd.DataFrame()
        for excel_file in excel_files:
            file_start_time = datetime.now()
            filename = os.path.basename(excel_file)
            file_stats = {
                '年份': year,
                '文件名': filename,
                '状态': '成功',
                '总记录数': 0,
                '银行记录数': 0,
                '处理时间': file_start_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            try:
                # 读取Excel文件，跳过第一行(英文标题)
                df = pd.read_excel(excel_file, header=1)
                file_stats['总记录数'] = len(df)
                
                # 确保股票代码列是字符串类型并进行格式化
                if '股票代码' in df.columns:
                    df['股票代码'] = df['股票代码'].astype(str).str.zfill(6)
                    
                    # 筛选银行数据
                    bank_data = df[df['股票代码'].isin(bank_codes)].copy()
                    file_stats['银行记录数'] = len(bank_data)
                    
                    # 添加文件名信息以便追踪来源
                    bank_data['源文件'] = filename
                    
                    # 添加到年度数据中
                    year_data = pd.concat([year_data, bank_data], ignore_index=True)
                    
                    print(f"  {filename} 提取到 {len(bank_data)} 条银行问答记录")
                else:
                    print(f"警告: {excel_file} 中没有找到'股票代码'列")
                    file_stats['状态'] = '缺少股票代码列'
                    
            except Exception as e:
                error_msg = str(e)
                print(f"处理 {filename} 时出错: {error_msg}")
                file_stats['状态'] = f'错误: {error_msg[:50]}...'  # 截断长错误信息
                
            # 记录处理时间
            file_stats['处理耗时(秒)'] = (datetime.now() - file_start_time).total_seconds()
            processing_stats.append(file_stats)
        
        # 添加年份列
        if not year_data.empty:
            year_data['年份'] = year
            # 添加到总数据中
            all_bank_data = pd.concat([all_bank_data, year_data], ignore_index=True)
            print(f"{year} 年共提取 {len(year_data)} 条记录")
    
    # 4. 保存结果
    if not all_bank_data.empty:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        all_bank_data.to_excel(output_file, index=False)
        print(f"数据已保存到 {output_file}, 共提取 {len(all_bank_data)} 条记录")
    else:
        print("未提取到任何数据")
    
    # 5. 生成并保存处理统计
    stats_df = pd.DataFrame(processing_stats)
    stats_file = os.path.join(os.path.dirname(output_file), "处理统计报告.xlsx")
    stats_df.to_excel(stats_file, index=False)
    print(f"处理统计已保存到 {stats_file}")
    
    # 6. 打印汇总统计
    print("\n=== 处理汇总统计 ===")
    total_files = len(stats_df)
    successful_files = len(stats_df[stats_df['状态'] == '成功'])
    total_records = stats_df['总记录数'].sum()
    bank_records = stats_df['银行记录数'].sum()
    
    print(f"处理文件总数: {total_files}")
    print(f"成功处理文件数: {successful_files}")
    print(f"失败/跳过文件数: {total_files - successful_files}")
    print(f"总记录数: {total_records}")
    print(f"提取的银行记录数: {bank_records}")
    print(f"提取比例: {bank_records/total_records*100:.2f}%" if total_records > 0 else "提取比例: N/A")
    
    # 打印每个文件的简要统计
    if not stats_df.empty:
        print("\n=== 各文件处理详情 ===")
        for _, row in stats_df.iterrows():
            status_icon = "✓" if row['状态'] == '成功' else "✗"
            print(f"{status_icon} {row['年份']}/{row['文件名']}: {row['状态']} "
                  f"(总记录: {row['总记录数']}, 银行记录: {row['银行记录数']})")
    
    return all_bank_data, stats_df

# 使用示例
if __name__ == "__main__":
    # 设置参数
    bank_codes_file = "/Users/chenyaxin/Desktop/上市银行.xlsx"  # 包含银行股票代码的Excel文件
    base_dir = "/Users/chenyaxin/Downloads/IRMD"  # 互动易数据根目录
    years_to_extract = [2017, 2018, 2019, 2020, 2021, 2022, 2023]  # 要提取的年份
    output_file = "/Users/chenyaxin/Desktop/银行互动易问答数据.xlsx"  # 输出文件
    
    # 执行提取
    result, stats = extract_bank_interaction_data(
        bank_codes_file, 
        base_dir, 
        years_to_extract, 
        output_file
    )