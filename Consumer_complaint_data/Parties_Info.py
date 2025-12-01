import pandas as pd
import os
import re
import glob
import csv
from tqdm import tqdm
import sys

def extract_role_from_case_name(case_name, company_name):
    """
    从案件名称中提取企业角色（原告/被告）
    """
    if not case_name or not company_name:
        return "未知", "数据缺失"
    
    case_name = str(case_name)
    company_name = str(company_name)
    
    # 清理案件名称
    case_name_clean = re.sub(
        r'民事判决书|民事裁定书|民事调解书|一审民事判决书|一审民事裁定书|'
        r'特别程序民事裁定书|民事一审民事裁定书|民事一审民事判决书|'
        r'\d{4,}|申请确认人民调解协议效力', 
        '', case_name
    ).strip()
    
    # 规则1: "与"字规则
    if '与' in case_name_clean:
        parts = case_name_clean.split('与', 1)
        plaintiff = parts[0].strip()
        defendant = parts[1].strip()
        
        # 使用部分匹配
        if company_name in plaintiff or plaintiff in company_name:
            return "原告", "与字规则-企业在前"
        elif company_name in defendant or defendant in company_name:
            return "被告", "与字规则-企业在后"
    
    # 规则2: "、"字规则
    elif '、' in case_name_clean:
        # 按顿号分割
        parts = case_name_clean.split('、')
        
        # 如果只有两部分，假设前面是原告，后面是被告
        if len(parts) == 2:
            plaintiff = parts[0].strip()
            defendant = parts[1].strip()
            
            # 使用部分匹配
            if company_name in plaintiff or plaintiff in company_name:
                return "原告", "顿号规则-企业在前(两部分)"
            elif company_name in defendant or defendant in company_name:
                return "被告", "顿号规则-企业在后(两部分)"
        
        # 如果有多个部分，查找企业名称的位置
        for i, part in enumerate(parts):
            # 使用部分匹配
            if company_name in part or part in company_name:
                # 如果企业在第一个位置，很可能是原告
                if i == 0:
                    return "原告", "顿号规则-企业在首位"
                # 如果企业在其他位置，很可能是被告
                else:
                    return "被告", "顿号规则-企业在中间"
    
    # 规则3: "诉"字规则
    elif '诉' in case_name_clean:
        parts = case_name_clean.split('诉', 1)
        plaintiff = parts[0].strip()
        defendant = parts[1].strip()
        
        # 使用部分匹配
        if company_name in plaintiff or plaintiff in company_name:
            return "原告", "诉字规则-企业在前"
        elif company_name in defendant or defendant in company_name:
            return "被告", "诉字规则-企业在后"
    
    return "未知", "无法匹配"

def safe_process_row(row, headers):
    """
    安全处理单行数据，截断过长的字段
    """
    row_dict = {}
    for i, header in enumerate(headers):
        if i < len(row):
            # 截断过长的字段，避免CSV解析错误
            field_value = str(row[i]) if row[i] is not None else ""
            # 对全文字段进行特殊处理，限制长度
            if header == '全文' and len(field_value) > 100000:  # 限制全文字段为100K字符
                field_value = field_value[:100000] + "...[已截断]"
            row_dict[header] = field_value
        else:
            row_dict[header] = ""
    return row_dict

def process_all_data_batch(input_dir, output_dir):
    """
    批量处理所有年份的数据，使用逐条处理和分段写入
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 增加字段大小限制
    csv.field_size_limit(50 * 1024 * 1024)  # 50MB 限制
    
    # 获取所有年份文件
    year_files = glob.glob(os.path.join(input_dir, "民事案件数据_*.csv"))
    print(f"找到 {len(year_files)} 个年份文件")
    
    # 总体统计
    overall_stats = {
        'total_files': len(year_files),
        'total_records': 0,
        'processed_records': 0,
        'error_records': 0,
        'role_distribution': {},
        'rule_distribution': {},
        'file_details': {}
    }
    
    # 处理每个年份文件
    for year_file in sorted(year_files):
        # 提取年份信息
        year = os.path.basename(year_file).replace("民事案件数据_", "").replace(".csv", "")
        print(f"\n处理 {year} 年数据...")
        
        # 输出文件路径
        output_file = os.path.join(output_dir, f"原被告提取结果_{year}.csv")
        
        # 文件统计
        file_stats = {
            'total_records': 0,
            'processed_records': 0,
            'error_records': 0,
            'role_distribution': {},
            'rule_distribution': {}
        }
        
        try:
            # 读取表头
            with open(year_file, 'r', encoding='utf-8-sig') as f:
                header_line = f.readline().strip()
                headers = header_line.split(',')
            
            print(f"  表头字段数: {len(headers)}")
            
            # 计算文件总行数用于进度条
            with open(year_file, 'r', encoding='utf-8-sig') as f:
                total_lines = sum(1 for line in f) - 1  # 减去标题行
            
            print(f"  总记录数: {total_lines:,}")
            file_stats['total_records'] = total_lines
            
            # 打开输入和输出文件
            with open(year_file, 'r', encoding='utf-8-sig') as infile, \
                 open(output_file, 'w', encoding='utf-8-sig', newline='') as outfile:
                
                # 跳过标题行
                next(infile)
                
                # 定义输出字段 - 只使用表头中的字段，忽略多余的字段
                fieldnames = headers + ['企业角色', '使用规则']
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # 创建CSV读取器
                csv_reader = csv.reader(infile)
                
                # 分段处理：每处理10000条记录就刷新一次缓冲区
                batch_size = 10000
                batch_count = 0
                
                # 处理每一行数据
                for row_num, row in enumerate(tqdm(csv_reader, total=total_lines, desc=f"处理{year}年"), 1):
                    try:
                        # 安全处理行数据，截断过长的字段
                        row_dict = safe_process_row(row, headers)
                        
                        # 确保关键字段存在
                        case_name = row_dict.get('案件名称', '')
                        company_name = row_dict.get('企业名称', '')
                        
                        # 提取角色
                        role, rule_used = extract_role_from_case_name(case_name, company_name)
                        
                        # 更新统计
                        file_stats['role_distribution'][role] = file_stats['role_distribution'].get(role, 0) + 1
                        file_stats['rule_distribution'][rule_used] = file_stats['rule_distribution'].get(rule_used, 0) + 1
                        file_stats['processed_records'] += 1
                        
                        # 写入结果
                        row_dict['企业角色'] = role
                        row_dict['使用规则'] = rule_used
                        writer.writerow(row_dict)
                        
                        # 每处理batch_size条记录，刷新一次缓冲区
                        batch_count += 1
                        if batch_count >= batch_size:
                            outfile.flush()
                            batch_count = 0
                        
                    except csv.Error as e:
                        # 处理CSV解析错误，包括字段大小限制错误
                        file_stats['error_records'] += 1
                        if file_stats['error_records'] <= 10:  # 只显示前10个错误
                            print(f"  第 {row_num} 行CSV解析出错: {e}")
                        # 跳过这一行，继续处理下一行
                        continue
                    except Exception as e:
                        file_stats['error_records'] += 1
                        # 记录错误但继续处理
                        if file_stats['error_records'] <= 10:  # 只显示前10个错误
                            print(f"  第 {row_num} 行处理出错: {e}")
                        # 尝试写入错误标记
                        try:
                            row_dict = safe_process_row(row, headers)
                            row_dict['企业角色'] = '错误'
                            row_dict['使用规则'] = f'处理出错: {str(e)[:100]}'  # 限制错误信息长度
                            writer.writerow(row_dict)
                        except:
                            pass  # 如果连错误标记都无法写入，则跳过该行
            
            # 更新总体统计
            overall_stats['total_records'] += file_stats['total_records']
            overall_stats['processed_records'] += file_stats['processed_records']
            overall_stats['error_records'] += file_stats['error_records']
            
            # 合并角色分布
            for role, count in file_stats['role_distribution'].items():
                overall_stats['role_distribution'][role] = overall_stats['role_distribution'].get(role, 0) + count
            
            # 合并规则分布
            for rule, count in file_stats['rule_distribution'].items():
                overall_stats['rule_distribution'][rule] = overall_stats['rule_distribution'].get(rule, 0) + count
            
            # 保存文件详情
            overall_stats['file_details'][year] = file_stats
            
            print(f"  成功处理: {file_stats['processed_records']:,} 条记录")
            print(f"  处理错误: {file_stats['error_records']:,} 条记录")
            if file_stats['total_records'] > 0:
                success_rate = file_stats['processed_records'] / file_stats['total_records'] * 100
                print(f"  处理成功率: {success_rate:.2f}%")
            print(f"  角色分布: {file_stats['role_distribution']}")
            print(f"  输出文件: {output_file}")
                
        except Exception as e:
            print(f"  处理 {year} 年数据时出错: {e}")
            overall_stats['file_details'][year] = {'error': str(e)}
    
    return overall_stats

def save_statistics_report(stats, output_dir):
    """
    保存统计报告
    """
    report_file = os.path.join(output_dir, "处理统计报告.txt")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("原被告提取处理统计报告\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"处理时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"总文件数: {stats['total_files']}\n")
        f.write(f"总记录数: {stats['total_records']:,}\n")
        f.write(f"成功处理: {stats['processed_records']:,}\n")
        f.write(f"处理错误: {stats['error_records']:,}\n")
        
        if stats['total_records'] > 0:
            success_rate = stats['processed_records'] / stats['total_records'] * 100
            f.write(f"处理成功率: {success_rate:.2f}%\n\n")
        
        # 总体角色分布
        f.write("总体角色分布:\n")
        for role, count in sorted(stats['role_distribution'].items()):
            percentage = count / stats['processed_records'] * 100 if stats['processed_records'] > 0 else 0
            f.write(f"  {role}: {count:,} 条 ({percentage:.2f}%)\n")
        
        f.write("\n总体规则使用分布:\n")
        for rule, count in sorted(stats['rule_distribution'].items()):
            percentage = count / stats['processed_records'] * 100 if stats['processed_records'] > 0 else 0
            f.write(f"  {rule}: {count:,} 次 ({percentage:.2f}%)\n")
        
        # 各年份详情
        f.write("\n各年份处理详情:\n")
        for year, details in sorted(stats['file_details'].items()):
            f.write(f"\n{year}年:\n")
            if 'error' in details:
                f.write(f"  处理失败: {details['error']}\n")
            else:
                f.write(f"  总记录数: {details['total_records']:,}\n")
                f.write(f"  成功处理: {details['processed_records']:,}\n")
                f.write(f"  处理错误: {details['error_records']:,}\n")
                if details['total_records'] > 0:
                    success_rate = details['processed_records'] / details['total_records'] * 100
                    f.write(f"  处理成功率: {success_rate:.2f}%\n")
                f.write(f"  角色分布:\n")
                for role, count in details['role_distribution'].items():
                    percentage = count / details['processed_records'] * 100 if details['processed_records'] > 0 else 0
                    f.write(f"    {role}: {count:,} 条 ({percentage:.2f}%)\n")
    
    print(f"\n统计报告已保存到: {report_file}")
    
    # 同时保存CSV格式的统计报告
    csv_report_file = os.path.join(output_dir, "处理统计报告.csv")
    
    # 创建年份统计表
    year_data = []
    for year, details in sorted(stats['file_details'].items()):
        if 'error' not in details:
            year_data.append({
                '年份': year,
                '总记录数': details['total_records'],
                '成功处理': details['processed_records'],
                '处理错误': details['error_records'],
                '成功率%': details['processed_records'] / details['total_records'] * 100 if details['total_records'] > 0 else 0,
                '原告数量': details['role_distribution'].get('原告', 0),
                '被告数量': details['role_distribution'].get('被告', 0),
                '未知数量': details['role_distribution'].get('未知', 0)
            })
    
    if year_data:
        year_df = pd.DataFrame(year_data)
        year_df.to_csv(csv_report_file, index=False, encoding='utf-8-sig')
        print(f"CSV统计报告已保存到: {csv_report_file}")

# 主程序
if __name__ == "__main__":
    input_dir = "/Volumes/T9/民事案件数据_按年份切分"
    output_dir = "/Volumes/T9/原被告提取结果"
    
    print("开始批量提取原被告信息...")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    # 检查输入目录是否存在
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在 - {input_dir}")
        exit(1)
    
    # 执行批量处理
    stats = process_all_data_batch(input_dir, output_dir)
    
    # 保存统计报告
    save_statistics_report(stats, output_dir)
    
    print("\n批量处理完成!")
    print(f"处理了 {stats['total_files']} 个文件")
    print(f"处理了 {stats['total_records']:,} 条记录")
    print(f"成功处理 {stats['processed_records']:,} 条记录")
    print(f"处理错误 {stats['error_records']:,} 条记录")
    
    if stats['processed_records'] > 0:
        success_rate = stats['processed_records'] / stats['total_records'] * 100
        print(f"总体成功率: {success_rate:.2f}%")
        
        # 显示总体角色分布
        print("\n总体角色分布:")
        for role, count in sorted(stats['role_distribution'].items()):
            percentage = count / stats['processed_records'] * 100
            print(f"  {role}: {count:,} 条 ({percentage:.2f}%)")