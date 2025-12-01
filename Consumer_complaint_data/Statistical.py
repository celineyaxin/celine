########1. 统计查看案件类型
import pandas as pd

# 读取CSV文件
file_path = "/Volumes/T9/temp_files/s41_202401_temp.csv"  # 请替换为你的文件路径
df = pd.read_csv(file_path, encoding='utf-8-sig')

# 检查"案件类型"列的分布
if '案件类型' in df.columns:
    print("案件类型分布:")
    print("=" * 50)
    
    # 获取案件类型的频数统计
    case_type_counts = df['案件类型'].value_counts()
    
    # 计算百分比
    case_type_percentages = df['案件类型'].value_counts(normalize=True) * 100
    
    # 创建结果DataFrame
    result_df = pd.DataFrame({
        '频数': case_type_counts,
        '百分比': case_type_percentages
    })
    
    # 添加累计百分比
    result_df['累计百分比'] = result_df['百分比'].cumsum()
    
    # 打印结果
    print(f"总记录数: {len(df)}")
    print(f"非空记录数: {df['案件类型'].notna().sum()}")
    print(f"缺失值数量: {df['案件类型'].isna().sum()}")
    print()
    
    # 打印前20个最常见的案件类型
    print("前20个案件类型分布:")
    print(result_df.head(20))
    
    # 如果有更多类型，显示总数
    if len(result_df) > 20:
        print(f"\n... 还有 {len(result_df) - 20} 个其他类型")
    
    # 保存结果到CSV文件
    result_df.to_csv('案件类型分布统计.csv', encoding='utf-8-sig')
    print(f"\n完整分布已保存到: 案件类型分布统计.csv")
    
else:
    print("数据集中没有找到'案件类型'列")
    print("可用的列有:", df.columns.tolist())



########2. 统计每年份涉及到的企业的数量
import pandas as pd
import os
import glob
from collections import Counter

def analyze_extracted_data(input_dir):
    """
    分析已提取的原被告数据
    """
    # 获取所有年份的结果文件
    result_files = glob.glob(os.path.join(input_dir, "原被告提取结果_*.csv"))
    print(f"找到 {len(result_files)} 个结果文件")
    
    # 初始化统计变量
    stats = {
        'total_companies': set(),
        'yearly_companies': {},
        'all_case_reasons': Counter(),
        'yearly_case_reasons': {},
        'role_distribution': Counter(),
        'yearly_role_distribution': {},
        'total_records': 0
    }
    
    # 处理每个年份文件
    for result_file in sorted(result_files):
        # 提取年份信息
        year = os.path.basename(result_file).replace("原被告提取结果_", "").replace(".csv", "")
        print(f"分析 {year} 年数据...")
        
        try:
            # 读取数据
            df = pd.read_csv(result_file, encoding='utf-8-sig')
            stats['total_records'] += len(df)
            
            # 统计企业数量
            companies_this_year = set(df['企业名称'].dropna().unique())
            stats['total_companies'].update(companies_this_year)
            stats['yearly_companies'][year] = len(companies_this_year)
            
            # 统计案由分布
            case_reasons_this_year = Counter(df['案由'].dropna().value_counts().to_dict())
            stats['all_case_reasons'].update(case_reasons_this_year)
            stats['yearly_case_reasons'][year] = case_reasons_this_year
            
            # 统计角色分布
            role_dist_this_year = Counter(df['企业角色'].value_counts().to_dict())
            stats['role_distribution'].update(role_dist_this_year)
            stats['yearly_role_distribution'][year] = role_dist_this_year
            
            print(f"  {year}年: {len(companies_this_year):,} 家企业, {len(df):,} 条记录")
            
        except Exception as e:
            print(f"  分析 {year} 年数据时出错: {e}")
    
    return stats

def print_statistics(stats):
    """
    打印统计信息
    """
    print("\n" + "="*60)
    print("数据统计汇总")
    print("="*60)
    
    # 基本信息
    print(f"数据覆盖时间范围: {min(stats['yearly_companies'].keys())} - {max(stats['yearly_companies'].keys())}")
    print(f"总覆盖企业数量: {len(stats['total_companies']):,}")
    print(f"总记录数量: {stats['total_records']:,}")
    
    # 按年份企业覆盖
    print("\n按年份企业覆盖:")
    for year, count in sorted(stats['yearly_companies'].items()):
        print(f"  {year}年: {count:,} 家企业")
    
    # 角色分布
    print("\n企业角色分布:")
    for role, count in stats['role_distribution'].items():
        percentage = count / stats['total_records'] * 100
        print(f"  {role}: {count:,} 次 ({percentage:.2f}%)")
    
    # 案由分布
    print("\n前20个最常见案由:")
    top_case_reasons = stats['all_case_reasons'].most_common(20)
    for i, (case_reason, count) in enumerate(top_case_reasons, 1):
        percentage = count / stats['total_records'] * 100
        print(f"  {i:2d}. {case_reason}: {count:,} 次 ({percentage:.2f}%)")

def save_statistics_to_csv(stats, output_dir):
    """
    保存统计结果到CSV文件
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 企业覆盖统计
    company_stats_file = os.path.join(output_dir, "企业覆盖统计.csv")
    company_data = []
    for year, count in sorted(stats['yearly_companies'].items()):
        company_data.append({
            '年份': year,
            '企业数量': count
        })
    
    # 添加总计
    company_data.append({
        '年份': '总计',
        '企业数量': len(stats['total_companies'])
    })
    
    company_df = pd.DataFrame(company_data)
    company_df.to_csv(company_stats_file, index=False, encoding='utf-8-sig')
    print(f"\n企业覆盖统计已保存到: {company_stats_file}")
    
    # 2. 案由详细统计
    case_reason_file = os.path.join(output_dir, "案由分布统计.csv")
    case_reason_data = []
    for case_reason, count in stats['all_case_reasons'].most_common():
        percentage = count / stats['total_records'] * 100
        case_reason_data.append({
            '案由': case_reason,
            '出现次数': count,
            '占比%': round(percentage, 2)
        })
    
    case_reason_df = pd.DataFrame(case_reason_data)
    case_reason_df.to_csv(case_reason_file, index=False, encoding='utf-8-sig')
    print(f"案由分布统计已保存到: {case_reason_file}")
    
    # 3. 角色分布统计
    role_stats_file = os.path.join(output_dir, "角色分布统计.csv")
    role_data = []
    for role, count in stats['role_distribution'].items():
        percentage = count / stats['total_records'] * 100
        role_data.append({
            '角色': role,
            '出现次数': count,
            '占比%': round(percentage, 2)
        })
    
    role_df = pd.DataFrame(role_data)
    role_df.to_csv(role_stats_file, index=False, encoding='utf-8-sig')
    print(f"角色分布统计已保存到: {role_stats_file}")
    
    # 4. 年份详细统计
    yearly_stats_file = os.path.join(output_dir, "年份详细统计.csv")
    yearly_data = []
    for year in sorted(stats['yearly_companies'].keys()):
        yearly_data.append({
            '年份': year,
            '企业数量': stats['yearly_companies'][year],
            '原告数量': stats['yearly_role_distribution'][year].get('原告', 0),
            '被告数量': stats['yearly_role_distribution'][year].get('被告', 0),
            '未知数量': stats['yearly_role_distribution'][year].get('未知', 0),
            '总记录数': sum(stats['yearly_role_distribution'][year].values())
        })
    
    yearly_df = pd.DataFrame(yearly_data)
    yearly_df.to_csv(yearly_stats_file, index=False, encoding='utf-8-sig')
    print(f"年份详细统计已保存到: {yearly_stats_file}")

# 主程序
if __name__ == "__main__":
    input_dir = "/Volumes/T9/原被告提取结果"  # 原被告提取结果目录
    output_dir = "/Volumes/T9/数据统计结果"   # 统计结果输出目录
    
    print("开始分析原被告数据...")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    # 检查输入目录是否存在
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在 - {input_dir}")
        exit(1)
    
    # 分析数据
    stats = analyze_extracted_data(input_dir)
    
    # 打印统计信息
    print_statistics(stats)
    
    # 保存统计结果到CSV
    save_statistics_to_csv(stats, output_dir)
    
    print("\n分析完成!")


########3. 针对被告数据的统计
import pandas as pd
import os
import glob
from collections import Counter

def analyze_extracted_data(input_dir):
    """
    分析已提取的原被告数据
    """
    # 获取所有年份的结果文件
    result_files = glob.glob(os.path.join(input_dir, "原被告提取结果_*.csv"))
    print(f"找到 {len(result_files)} 个结果文件")
    
    # 初始化统计变量
    stats = {
        'total_companies': set(),
        'yearly_companies': {},
        'all_case_reasons': Counter(),
        'yearly_case_reasons': {},
        'role_distribution': Counter(),
        'yearly_role_distribution': {},
        'total_records': 0,
        # 新增：被告企业相关统计
        'defendant_companies': set(),
        'yearly_defendant_companies': {},
        'defendant_case_reasons': Counter(),
        'yearly_defendant_case_reasons': {}
    }
    
    # 处理每个年份文件
    for result_file in sorted(result_files):
        # 提取年份信息
        year = os.path.basename(result_file).replace("原被告提取结果_", "").replace(".csv", "")
        print(f"分析 {year} 年数据...")
        
        try:
            # 读取数据
            df = pd.read_csv(result_file, encoding='utf-8-sig')
            stats['total_records'] += len(df)
            
            # 统计所有企业数量
            companies_this_year = set(df['企业名称'].dropna().unique())
            stats['total_companies'].update(companies_this_year)
            stats['yearly_companies'][year] = len(companies_this_year)
            
            # 统计被告企业数量
            defendant_df = df[df['企业角色'] == '被告']
            defendant_companies_this_year = set(defendant_df['企业名称'].dropna().unique())
            stats['defendant_companies'].update(defendant_companies_this_year)
            stats['yearly_defendant_companies'][year] = len(defendant_companies_this_year)
            
            # 统计所有案由分布
            case_reasons_this_year = Counter(df['案由'].dropna().value_counts().to_dict())
            stats['all_case_reasons'].update(case_reasons_this_year)
            stats['yearly_case_reasons'][year] = case_reasons_this_year
            
            # 统计被告案由分布
            defendant_case_reasons_this_year = Counter(defendant_df['案由'].dropna().value_counts().to_dict())
            stats['defendant_case_reasons'].update(defendant_case_reasons_this_year)
            stats['yearly_defendant_case_reasons'][year] = defendant_case_reasons_this_year
            
            # 统计角色分布
            role_dist_this_year = Counter(df['企业角色'].value_counts().to_dict())
            stats['role_distribution'].update(role_dist_this_year)
            stats['yearly_role_distribution'][year] = role_dist_this_year
            
            print(f"  {year}年: {len(companies_this_year):,} 家企业, {len(defendant_companies_this_year):,} 家被告企业, {len(df):,} 条记录")
            
        except Exception as e:
            print(f"  分析 {year} 年数据时出错: {e}")
    
    return stats

def print_statistics(stats):
    """
    打印统计信息
    """
    print("\n" + "="*60)
    print("数据统计汇总")
    print("="*60)
    
    # 基本信息
    print(f"数据覆盖时间范围: {min(stats['yearly_companies'].keys())} - {max(stats['yearly_companies'].keys())}")
    print(f"总覆盖企业数量: {len(stats['total_companies']):,}")
    print(f"总被告企业数量: {len(stats['defendant_companies']):,}")
    print(f"总记录数量: {stats['total_records']:,}")
    
    # 按年份企业覆盖
    print("\n按年份企业覆盖:")
    for year, count in sorted(stats['yearly_companies'].items()):
        defendant_count = stats['yearly_defendant_companies'].get(year, 0)
        print(f"  {year}年: {count:,} 家企业, {defendant_count:,} 家被告企业")
    
    # 角色分布
    print("\n企业角色分布:")
    for role, count in stats['role_distribution'].items():
        percentage = count / stats['total_records'] * 100
        print(f"  {role}: {count:,} 次 ({percentage:.2f}%)")
    
    # 所有案由分布
    print("\n前20个最常见案由:")
    top_case_reasons = stats['all_case_reasons'].most_common(20)
    for i, (case_reason, count) in enumerate(top_case_reasons, 1):
        percentage = count / stats['total_records'] * 100
        print(f"  {i:2d}. {case_reason}: {count:,} 次 ({percentage:.2f}%)")
    
    # 被告案由分布
    print("\n前20个最常见被告案由:")
    top_defendant_case_reasons = stats['defendant_case_reasons'].most_common(20)
    for i, (case_reason, count) in enumerate(top_defendant_case_reasons, 1):
        percentage = count / sum(stats['defendant_case_reasons'].values()) * 100 if sum(stats['defendant_case_reasons'].values()) > 0 else 0
        print(f"  {i:2d}. {case_reason}: {count:,} 次 ({percentage:.2f}%)")

def save_statistics_to_csv(stats, output_dir):
    """
    保存统计结果到CSV文件
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 企业覆盖统计
    company_stats_file = os.path.join(output_dir, "企业覆盖统计.csv")
    company_data = []
    for year, count in sorted(stats['yearly_companies'].items()):
        defendant_count = stats['yearly_defendant_companies'].get(year, 0)
        company_data.append({
            '年份': year,
            '企业数量': count,
            '被告企业数量': defendant_count,
            '被告企业占比%': round(defendant_count / count * 100, 2) if count > 0 else 0
        })
    
    # 添加总计
    company_data.append({
        '年份': '总计',
        '企业数量': len(stats['total_companies']),
        '被告企业数量': len(stats['defendant_companies']),
        '被告企业占比%': round(len(stats['defendant_companies']) / len(stats['total_companies']) * 100, 2) if len(stats['total_companies']) > 0 else 0
    })
    
    company_df = pd.DataFrame(company_data)
    company_df.to_csv(company_stats_file, index=False, encoding='utf-8-sig')
    print(f"\n企业覆盖统计已保存到: {company_stats_file}")
    
    # 2. 案由详细统计
    case_reason_file = os.path.join(output_dir, "案由分布统计.csv")
    case_reason_data = []
    for case_reason, count in stats['all_case_reasons'].most_common():
        percentage = count / stats['total_records'] * 100
        defendant_count = stats['defendant_case_reasons'].get(case_reason, 0)
        defendant_percentage = defendant_count / count * 100 if count > 0 else 0
        case_reason_data.append({
            '案由': case_reason,
            '出现次数': count,
            '占比%': round(percentage, 2),
            '被告出现次数': defendant_count,
            '被告占比%': round(defendant_percentage, 2)
        })
    
    case_reason_df = pd.DataFrame(case_reason_data)
    case_reason_df.to_csv(case_reason_file, index=False, encoding='utf-8-sig')
    print(f"案由分布统计已保存到: {case_reason_file}")
    
    # 3. 被告案由统计
    defendant_case_reason_file = os.path.join(output_dir, "被告案由统计.csv")
    defendant_case_reason_data = []
    total_defendant_cases = sum(stats['defendant_case_reasons'].values())
    for case_reason, count in stats['defendant_case_reasons'].most_common():
        percentage = count / total_defendant_cases * 100 if total_defendant_cases > 0 else 0
        defendant_case_reason_data.append({
            '案由': case_reason,
            '被告出现次数': count,
            '占比%': round(percentage, 2)
        })
    
    defendant_case_reason_df = pd.DataFrame(defendant_case_reason_data)
    defendant_case_reason_df.to_csv(defendant_case_reason_file, index=False, encoding='utf-8-sig')
    print(f"被告案由统计已保存到: {defendant_case_reason_file}")
    
    # 4. 角色分布统计
    role_stats_file = os.path.join(output_dir, "角色分布统计.csv")
    role_data = []
    for role, count in stats['role_distribution'].items():
        percentage = count / stats['total_records'] * 100
        role_data.append({
            '角色': role,
            '出现次数': count,
            '占比%': round(percentage, 2)
        })
    
    role_df = pd.DataFrame(role_data)
    role_df.to_csv(role_stats_file, index=False, encoding='utf-8-sig')
    print(f"角色分布统计已保存到: {role_stats_file}")
    
    # 5. 年份详细统计
    yearly_stats_file = os.path.join(output_dir, "年份详细统计.csv")
    yearly_data = []
    for year in sorted(stats['yearly_companies'].keys()):
        defendant_count = stats['yearly_defendant_companies'].get(year, 0)
        yearly_data.append({
            '年份': year,
            '企业数量': stats['yearly_companies'][year],
            '被告企业数量': defendant_count,
            '原告数量': stats['yearly_role_distribution'][year].get('原告', 0),
            '被告数量': stats['yearly_role_distribution'][year].get('被告', 0),
            '未知数量': stats['yearly_role_distribution'][year].get('未知', 0),
            '总记录数': sum(stats['yearly_role_distribution'][year].values())
        })
    
    yearly_df = pd.DataFrame(yearly_data)
    yearly_df.to_csv(yearly_stats_file, index=False, encoding='utf-8-sig')
    print(f"年份详细统计已保存到: {yearly_stats_file}")

# 主程序
if __name__ == "__main__":
    input_dir = "/Volumes/T9/原被告提取结果"  # 原被告提取结果目录
    output_dir = "/Volumes/T9/数据统计结果"   # 统计结果输出目录
    
    print("开始分析原被告数据...")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    # 检查输入目录是否存在
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在 - {input_dir}")
        exit(1)
    
    # 分析数据
    stats = analyze_extracted_data(input_dir)
    
    # 打印统计信息
    print_statistics(stats)
    
    # 保存统计结果到CSV
    save_statistics_to_csv(stats, output_dir)
    
    print("\n分析完成!")
