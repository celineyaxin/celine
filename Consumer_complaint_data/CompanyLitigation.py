import os
import pandas as pd
import glob
import re
from tqdm import tqdm
import json
from datetime import datetime

# 定义必需的列
REQUIRED_COLUMNS = ['案号', '所属地区', '案件类型', '审理程序', '案件名称', '案由', '全文', '裁判日期']

def extract_year_from_filename(filename):
    """
    从不同类型的文件名中提取年份
    """
    # 第一种格式: 2021年10月裁判文书数据_temp.csv
    match1 = re.search(r'(\d{4})年', filename)
    if match1:
        return int(match1.group(1))
    
    # 第二种格式: s41_202401_temp.csv
    match2 = re.search(r'_(\d{6})_', filename)
    if match2:
        year_month = match2.group(1)
        return int(year_month[:4])
    
    # 第三种格式: ws_2023_07_temp.csv
    match3 = re.search(r'_(\d{4})_', filename)
    if match3:
        return int(match3.group(1))
    
    # 如果都不匹配，尝试从文件名中查找4位数字作为年份
    match4 = re.search(r'\d{4}', filename)
    if match4:
        year = int(match4.group(0))
        if 2000 <= year <= 2024:
            return year
    
    return None

def merge_and_analyze_temp_files(temp_folder, output_file):
    """
    合并临时文件并进行统计分析
    """
    # 检查文件夹是否存在
    if not os.path.exists(temp_folder):
        print(f"错误：文件夹不存在 - {temp_folder}")
        return
    
    # 创建处理日志
    processing_log = {
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temp_folder": temp_folder,
        "output_file": output_file,
        "total_files_found": 0,
        "files_processed": [],
        "files_skipped": [],
        "files_with_errors": [],
        "year_distribution": {},
        "records_per_file": {}
    }
    
    # 查找所有临时文件
    temp_files = glob.glob(os.path.join(temp_folder, "*_temp.csv"))
    processing_log["total_files_found"] = len(temp_files)
    print(f"找到 {len(temp_files)} 个临时文件")
    
    if not temp_files:
        print("没有找到任何临时文件！")
        return
    
    # 按年份筛选文件
    filtered_files = []
    year_count = {}
    
    for file_path in temp_files:
        filename = os.path.basename(file_path)
        year = extract_year_from_filename(filename)
        
        if year and 2020 <= year <= 2024:
            filtered_files.append((file_path, year, filename))
            if year in year_count:
                year_count[year] += 1
            else:
                year_count[year] = 1
        else:
            processing_log["files_skipped"].append({
                "file": filename,
                "reason": "年份不在2020-2024范围内或无法解析年份"
            })
    
    print(f"2020-2024年的文件数量: {len(filtered_files)}")
    for year in sorted(year_count.keys()):
        print(f"  {year}年: {year_count[year]} 个文件")
    
    # 记录年份分布
    processing_log["year_distribution"] = year_count
    
    if not filtered_files:
        print("没有找到2020-2024年的文件")
        processing_log["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_processing_log(processing_log)
        return
    
    # 读取并合并所有文件
    all_data = []
    for file_path, year, filename in tqdm(filtered_files, desc="读取文件"):
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            record_count = len(df)
            
            # 确保所有必需的列都存在，如果不存在则创建空列
            missing_columns = []
            for col in REQUIRED_COLUMNS:
                if col not in df.columns:
                    df[col] = None
                    missing_columns.append(col)
            
            # 只保留必需的列和企业名称列
            columns_to_keep = REQUIRED_COLUMNS + ['企业名称']
            # 确保企业名称列存在
            if '企业名称' not in df.columns:
                df['企业名称'] = None
                missing_columns.append('企业名称')
            
            df = df[columns_to_keep]
            
            # 添加年份列（从文件名提取的）
            df['文件年份'] = year
            
            all_data.append(df)
            
            # 记录成功处理的文件
            processing_log["files_processed"].append({
                "file": filename,
                "year": year,
                "records": record_count,
                "missing_columns": missing_columns,
                "status": "成功"
            })
            processing_log["records_per_file"][filename] = record_count
            
        except Exception as e:
            error_msg = f"读取文件 {file_path} 时出错: {e}"
            print(error_msg)
            processing_log["files_with_errors"].append({
                "file": filename,
                "error": str(e),
                "status": "失败"
            })
    
    if not all_data:
        print("没有找到有效数据")
        processing_log["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_processing_log(processing_log)
        return
    
    # 合并数据
    print("合并数据中...")
    merged_df = pd.concat(all_data, ignore_index=True)
    
    # 去重处理（基于案号和企业名称）
    before_dedup = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=['案号', '企业名称'], keep='first')
    after_dedup = len(merged_df)
    
    print(f"去重前: {before_dedup} 条记录")
    print(f"去重后: {after_dedup} 条记录")
    print(f"移除重复记录: {before_dedup - after_dedup} 条")
    
    # 保存合并后的数据，确保包含所有必需的列
    final_columns = REQUIRED_COLUMNS + ['企业名称', '文件年份']
    merged_df = merged_df[final_columns]
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"合并后的数据已保存到: {output_file}")
    
    # 更新处理日志
    processing_log["total_records_before_dedup"] = before_dedup
    processing_log["total_records_after_dedup"] = after_dedup
    processing_log["duplicates_removed"] = before_dedup - after_dedup
    processing_log["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 保存处理日志
    save_processing_log(processing_log)
    
    # 生成处理报告
    generate_processing_report(processing_log)
    
    # 统计分析
    analyze_temp_data(merged_df)

def save_processing_log(processing_log):
    """保存处理日志到JSON文件"""
    log_file = "文件处理日志.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(processing_log, f, ensure_ascii=False, indent=2)
    print(f"处理日志已保存到: {log_file}")

def generate_processing_report(processing_log):
    """生成处理报告"""
    report_file = "文件处理报告.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("司法处罚数据文件处理报告\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"处理时间: {processing_log['start_time']} - {processing_log['end_time']}\n")
        f.write(f"数据文件夹: {processing_log['temp_folder']}\n")
        f.write(f"输出文件: {processing_log['output_file']}\n\n")
        
        f.write(f"找到的临时文件总数: {processing_log['total_files_found']}\n")
        f.write(f"成功处理的文件数: {len(processing_log['files_processed'])}\n")
        f.write(f"跳过的文件数: {len(processing_log['files_skipped'])}\n")
        f.write(f"处理失败的文件数: {len(processing_log['files_with_errors'])}\n\n")
        
        # 年份分布
        f.write("年份分布:\n")
        for year, count in processing_log['year_distribution'].items():
            f.write(f"  {year}年: {count} 个文件\n")
        f.write("\n")
        
        # 记录统计
        if 'total_records_before_dedup' in processing_log:
            f.write(f"去重前总记录数: {processing_log['total_records_before_dedup']:,}\n")
            f.write(f"去重后总记录数: {processing_log['total_records_after_dedup']:,}\n")
            f.write(f"移除重复记录: {processing_log['duplicates_removed']:,}\n\n")
        
        # 跳过的文件
        if processing_log['files_skipped']:
            f.write("跳过的文件:\n")
            for file_info in processing_log['files_skipped']:
                f.write(f"  {file_info['file']}: {file_info['reason']}\n")
            f.write("\n")
        
        # 处理失败的文件
        if processing_log['files_with_errors']:
            f.write("处理失败的文件:\n")
            for file_info in processing_log['files_with_errors']:
                f.write(f"  {file_info['file']}: {file_info['error']}\n")
            f.write("\n")
        
        # 文件详情
        f.write("文件处理详情:\n")
        total_records = 0
        for file_info in processing_log['files_processed']:
            f.write(f"  {file_info['file']} ({file_info['year']}年): {file_info['records']} 条记录")
            if file_info['missing_columns']:
                f.write(f" [缺少列: {', '.join(file_info['missing_columns'])}]")
            f.write("\n")
            total_records += file_info['records']
        
        f.write(f"\n所有文件原始记录总数: {total_records:,}\n")
    
    print(f"处理报告已保存到: {report_file}")

def analyze_temp_data(df):
    """
    对合并后的临时文件数据进行统计分析
    """
    print("\n" + "="*50)
    print("临时文件数据统计分析结果")
    print("="*50)
    
    # 基本统计
    total_records = len(df)
    unique_companies = df['企业名称'].nunique()
    
    print(f"总处罚记录数量: {total_records:,} 条")
    print(f"覆盖公司数量: {unique_companies:,} 家")
    
    # 按文件年份统计
    if '文件年份' in df.columns:
        yearly_stats = df['文件年份'].value_counts().sort_index()
        print("\n按文件年份分布:")
        for year, count in yearly_stats.items():
            print(f"  {year}年: {count:,} 条")
    
    # 按裁判日期统计
    if '裁判日期' in df.columns:
        try:
            df['裁判年份'] = pd.to_datetime(df['裁判日期'], errors='coerce').dt.year
            judge_year_stats = df['裁判年份'].value_counts().sort_index()
            print("\n按裁判年份分布:")
            for year, count in judge_year_stats.items():
                if not pd.isna(year):
                    print(f"  {int(year)}年: {count:,} 条")
        except Exception as e:
            print(f"解析裁判日期时出错: {e}")
    
    # 按案件类型统计
    if '案件类型' in df.columns:
        case_type_stats = df['案件类型'].value_counts()
        print("\n按案件类型分布:")
        for case_type, count in case_type_stats.items():
            print(f"  {case_type}: {count:,} 条")
    
    # 按地区统计
    if '所属地区' in df.columns:
        region_stats = df['所属地区'].value_counts().head(10)
        print("\n处罚记录最多的前10个地区:")
        for region, count in region_stats.items():
            print(f"  {region}: {count:,} 条")
    
    # 按案由统计
    if '案由' in df.columns:
        reason_stats = df['案由'].value_counts().head(10)
        print("\n最常见的10个案由:")
        for reason, count in reason_stats.items():
            print(f"  {reason}: {count:,} 条")
    
    # 公司处罚次数统计
    company_case_counts = df['企业名称'].value_counts()
    print(f"\n公司处罚次数统计:")
    print(f"  平均每家公司的处罚次数: {company_case_counts.mean():.2f} 次")
    print(f"  处罚次数最多的公司: {company_case_counts.idxmax()} ({company_case_counts.max()} 次)")
    print(f"  只有1次处罚记录的公司: {(company_case_counts == 1).sum():,} 家")
    
    # 处罚次数分布
    print(f"\n处罚次数分布:")
    distribution = company_case_counts.value_counts().sort_index()
    for count, companies in distribution.head(10).items():
        print(f"  处罚{count}次的公司: {companies:,} 家")
    
    # 保存统计摘要
    save_temp_statistics_summary(df, company_case_counts)

def save_temp_statistics_summary(df, company_case_counts):
    """
    保存临时文件统计摘要
    """
    summary_file = "临时文件数据统计摘要.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("临时文件司法处罚数据统计摘要\n")
        f.write("="*50 + "\n\n")
        
        f.write(f"数据覆盖时间范围: 2020-2024年\n")
        f.write(f"总处罚记录数量: {len(df):,} 条\n")
        f.write(f"覆盖公司数量: {df['企业名称'].nunique():,} 家\n\n")
        
        # 按文件年份统计
        if '文件年份' in df.columns:
            f.write("按文件年份分布:\n")
            yearly_stats = df['文件年份'].value_counts().sort_index()
            for year, count in yearly_stats.items():
                f.write(f"  {year}年: {count:,} 条\n")
            f.write("\n")
        
        # 按裁判年份统计
        if '裁判年份' in df.columns:
            f.write("按裁判年份分布:\n")
            judge_year_stats = df['裁判年份'].value_counts().sort_index()
            for year, count in judge_year_stats.items():
                if not pd.isna(year):
                    f.write(f"  {int(year)}年: {count:,} 条\n")
            f.write("\n")
        
        # 按案件类型统计
        if '案件类型' in df.columns:
            f.write("按案件类型分布:\n")
            case_type_stats = df['案件类型'].value_counts()
            for case_type, count in case_type_stats.items():
                f.write(f"  {case_type}: {count:,} 条\n")
            f.write("\n")
        
        # 处罚次数最多的公司
        f.write("处罚次数最多的前20家公司:\n")
        top_companies = company_case_counts.head(20)
        for i, (company, count) in enumerate(top_companies.items(), 1):
            f.write(f"  {i:2d}. {company}: {count} 次\n")
        
        # 数据列信息
        f.write(f"\n数据包含的列: {', '.join(df.columns.tolist())}\n")
        f.write(f"数据总行数: {len(df):,}\n")
        f.write(f"数据总列数: {len(df.columns)}\n")
    
    print(f"\n详细统计摘要已保存到: {summary_file}")

# 主程序入口
if __name__ == "__main__":
    print("开始处理司法处罚数据...")
    
    # 直接使用你指定的路径
    temp_folder = "/Volumes/T9/temp_files"
    output_file = "/Volumes/T9/合并的司法处罚数据_2020-2024.csv"
    
    print(f"临时文件文件夹: {temp_folder}")
    print(f"输出文件: {output_file}")
    print("-" * 50)
    
    # 执行合并和统计分析
    merge_and_analyze_temp_files(temp_folder, output_file)
    
    print("\n处理完成！")