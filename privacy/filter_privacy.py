import os
import pandas as pd
from datetime import datetime
import re
from tqdm import tqdm
import signal
import sys
import json
import atexit
import logging

# 设置文件夹路径
data_folder = "/Volumes/T9/裁判文书"  # 修改为实际路径
excel_path = '/Users/chenyaxin/Desktop/websitdata/merge_data6/企业基础工商信息.xlsx'
output_file = "/Users/chenyaxin/Desktop/隐私相关案件分析_精确版.xlsx"
checkpoint_file = "/Users/chenyaxin/Desktop/checkpoint.json"  # 断点文件
log_file = "/Users/chenyaxin/Desktop/privacy_analysis_log.txt"  # 日志文件

# 设置时间范围
START_DATE = pd.to_datetime('2018-08-01')
END_DATE = pd.to_datetime('2021-07-31')

# 全局变量，用于保存处理状态
processed_files = set()
all_privacy_cases = []

# 设置日志
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# 同时输出到控制台
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# 中断处理函数
def signal_handler(sig, frame):
    logging.info("\n检测到中断信号，正在保存已处理的数据...")
    save_checkpoint()
    save_results()
    logging.info("数据已保存，程序退出")
    sys.exit(0)

# 注册中断信号处理
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# 程序退出时的处理
def exit_handler():
    logging.info("程序退出，保存处理进度...")
    save_checkpoint()
    save_results()

atexit.register(exit_handler)

# 保存断点信息
def save_checkpoint():
    checkpoint_data = {
        "processed_files": list(processed_files),
        "last_processed_year": current_year if 'current_year' in globals() else None,
        "last_processed_file": current_file if 'current_file' in globals() else None
    }
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

# 加载断点信息
def load_checkpoint():
    global processed_files
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
                processed_files = set(checkpoint_data.get("processed_files", []))
                logging.info(f"从断点文件加载了 {len(processed_files)} 个已处理文件记录")
                return checkpoint_data
        except Exception as e:
            logging.error(f"读取断点文件时出错: {str(e)}")
    return {}

# 保存结果到Excel
def save_results():
    if all_privacy_cases:
        try:
            final_privacy_cases = pd.concat(all_privacy_cases, ignore_index=True)
            final_privacy_cases.to_excel(output_file, index=False)
            logging.info(f"已保存 {len(final_privacy_cases)} 个隐私相关案件到: {output_file}")
        except Exception as e:
            logging.error(f"保存文件时出错: {str(e)}")
    else:
        logging.info("尚无隐私相关案件可保存")

# 读取企业列表
try:
    company_df = pd.read_excel(excel_path)
    target_companies = set(company_df['compn'].dropna().str.strip().unique())
    logging.info(f"从企业基础工商信息中读取了 {len(target_companies)} 家企业")
except Exception as e:
    logging.error(f"读取企业列表时出错: {str(e)}")
    exit()

# 优化后的关键词列表 - 分层结构
# 第一层：高精准度核心词
high_precision_keywords = [
    # 核心侵权表述
    '侵犯隐私', '隐私侵权', '侵犯个人信息', '个人信息侵权',
    '侵害隐私权', '侵害个人信息权益',
    # 核心违法行为表述
    '隐私泄露', '信息泄露', '数据泄露', '泄露隐私',
    '非法获取个人信息', '非法收集个人信息', '非法使用个人信息',
    '非法买卖个人信息', '非法提供个人信息', '非法出售个人信息',
    '侵犯公民个人信息罪',  # 这是刑事案由，精准度极高
    # 核心法律案由
    '隐私权纠纷', '个人信息保护纠纷'
]

# 第二层：需上下文判断的触发词
contextual_keywords = {
    'actions': [  # 行为
        '未经同意', '未经授权', '未获授权', '未经许可',
        '过度收集', '超范围收集', '强制收集', '默认勾选',
        '大数据杀熟', '用户画像', '精准营销', '个性化推荐',
        '滥用个人信息', '不当使用', '违规使用',
        '未明示', '未告知', '一揽子授权'
    ],
    'concepts': [  # 概念/原则
        '知情同意', '明示同意', '默示同意', '同意原则',
        '个人信息保护', '数据安全', '网络安全',
        '告知同意',
    ],
    'tech_scenarios': [  # 技术场景
        '人脸识别', '生物识别', '指纹信息', '基因信息',
        '行踪轨迹', '位置信息', '通讯录信息', '短信内容',
        'cookie', '网络追踪', '行为广告',
        '身份证号码', '银行账号', '家庭住址', '私密信息',
        '手机号码', '电话号码'
    ]
}


# 正则表达式模式匹配
patterns = [
    r"未经[^，。]*同意[^，。]*(收集|使用|处理)[^，。]*个人信息",
    r"非法[^，。]*(获取|提供|买卖)[^，。]*公民个人信息",
    r"因[^，。]*(人脸识别|泄露信息)[^，。]*(被告|起诉|索赔)",
    r"违反[^，。]*个人信息保护[^，。]*规定",
    r"未明示[^，。]*收集[^，。]*使用目的",
]

# 关键词匹配函数
def contains_high_precision_keywords(text):
    """检查是否包含高精度关键词"""
    for keyword in high_precision_keywords:
        if keyword in text:
            return True
    return False

def contains_multiple_contextual_keywords(text):
    """检查是否包含多个不同类别的上下文关键词"""
    found_categories = set()
    for category, keywords in contextual_keywords.items():
        for keyword in keywords:
            if keyword in text:
                found_categories.add(category)
                # 如果已经找到两个不同类别的词，提前返回True
                if len(found_categories) >= 2:
                    return True
    return False

def check_patterns(text):
    """使用正则表达式检查模式"""
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False

def is_privacy_related(content):
    """综合判断是否为隐私相关案件"""
    # 1. 首先检查高精准度词
    if contains_high_precision_keywords(content):
        return True, "高精度关键词"
    
    # 2. 检查多重上下文关键词
    if contains_multiple_contextual_keywords(content):
        return True, "多重上下文关键词"
    
    # 3. 检查正则表达式模式
    if check_patterns(content):
        return True, "正则模式匹配"
    
    return False, ""

# 时间处理函数
def parse_date(date_str, date_format='%Y-%m-%d'):
    """尝试解析日期字符串"""
    if pd.isna(date_str) or date_str == '':
        return None
        
    # 尝试多种日期格式
    formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y年%m月%d日',
        '%Y.%m.%d',
        '%Y%m%d'
    ]
    
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except:
            continue
            
    # 如果所有格式都失败，尝试使用pandas的灵活解析
    try:
        return pd.to_datetime(date_str)
    except:
        return None

def filter_by_date(df, date_columns):
    """根据日期列过滤数据"""
    date_col = None
    for col in date_columns:
        if col in df.columns:
            date_col = col
            break
            
    if date_col is None:
        logging.warning("未找到日期字段，跳过日期过滤")
        return df
        
    # 解析日期
    df['parsed_date'] = df[date_col].apply(parse_date)
    
    # 过滤掉无法解析的日期
    valid_dates = df['parsed_date'].notna()
    df_valid = df[valid_dates].copy()
    
    if len(df_valid) == 0:
        logging.warning("所有日期都无法解析，跳过日期过滤")
        return df
        
    # 过滤指定时间范围内的数据
    date_filter = (df_valid['parsed_date'] >= START_DATE) & (df_valid['parsed_date'] <= END_DATE)
    df_filtered = df_valid[date_filter].copy()
    
    # 移除临时列
    if 'parsed_date' in df_filtered.columns:
        df_filtered = df_filtered.drop('parsed_date', axis=1)
    
    logging.info(f"日期过滤: 原始 {len(df)} 条记录, 有效日期 {len(df_valid)} 条, 时间范围内 {len(df_filtered)} 条")
    
    return df_filtered

# 主处理函数
def process_files():
    global current_year, current_file
    
    # 加载断点信息
    checkpoint_data = load_checkpoint()
    
    # 遍历年份文件夹 (2018, 2019, 2020, 2021)
    for year in ['2018', '2019', '2020', '2021']:
        current_year = year
        year_folder = os.path.join(data_folder, year)
        if not os.path.exists(year_folder):
            logging.info(f"跳过不存在的年份文件夹: {year_folder}")
            continue
            
        logging.info(f"\n处理 {year}年 的数据")
        
        # 获取该年份下的所有CSV文件
        csv_files = [f for f in os.listdir(year_folder) 
                    if f.endswith('.csv') and 
                    not f.startswith('.') and
                    not f.startswith('~')]
        
        # 过滤掉已处理的文件
        csv_files_to_process = [f for f in csv_files if f not in processed_files]
        
        if not csv_files_to_process:
            logging.info(f"  {year}年所有文件已处理过，跳过")
            continue
            
        # 为当前年份的文件处理添加进度条
        for file_index, file in enumerate(tqdm(csv_files_to_process, desc=f"处理 {year}年文件", unit="文件")):
            current_file = file
            
            try:
                file_path = os.path.join(year_folder, file)
                
                # 读取CSV文件
                df = pd.read_csv(file_path)
                
                # 时间过滤 - 添加日期字段识别和过滤
                possible_date_columns = ['裁判日期', '判决日期', '案件日期', '日期', '立案时间', '裁判时间']
                df = filter_by_date(df, possible_date_columns)
                
                if len(df) == 0:
                    logging.info(f"  文件 {file} 在时间范围 {START_DATE.date()} 到 {END_DATE.date()} 内无数据，跳过")
                    processed_files.add(file)
                    save_checkpoint()
                    continue
                
                # 检查是否有案件名称字段
                case_name_field = None
                case_name_fields = ['案件名称', '案由', '标题', '案件名']
                for field in case_name_fields:
                    if field in df.columns:
                        case_name_field = field
                        break
                
                if case_name_field is None:
                    logging.info(f"  文件 {file} 中未找到案件名称字段，跳过")
                    processed_files.add(file)
                    save_checkpoint()
                    continue
                
                # 确定案件内容字段
                content_field = None
                content_fields = ['案件内容', '案情摘要', '事实', '裁判要旨', '全文', '内容']
                for field in content_fields:
                    if field in df.columns:
                        content_field = field
                        break
                
                if content_field is None:
                    logging.info(f"  文件 {file} 中未找到内容字段，跳过")
                    processed_files.add(file)
                    save_checkpoint()
                    continue
                
                # 第一步：筛选案件名称中包含目标企业的案件
                target_data_list = []
                matched_companies_list = []  # 存储匹配的企业名称
                
                for company_name in target_companies:
                    # 使用正则表达式确保匹配完整的企业名称
                    mask = df[case_name_field].str.contains(company_name, na=False, regex=False)
                    if mask.any():
                        matched_cases = df[mask].copy()
                        # 添加企业名称列
                        matched_cases['匹配企业名称'] = company_name
                        target_data_list.append(matched_cases)
                        matched_companies_list.append(company_name)
                
                if not target_data_list:
                    logging.info(f"  文件 {file} 中没有找到目标企业的案件，跳过")
                    processed_files.add(file)
                    save_checkpoint()
                    continue
                
                # 合并所有匹配的案件
                target_data = pd.concat(target_data_list, ignore_index=True)
                target_data = target_data.drop_duplicates()  # 去除重复项
                
                logging.info(f"  文件 {file} 中找到 {len(target_data)} 个目标企业的案件，涉及 {len(matched_companies_list)} 家企业")
                
                # 第二步：在这些案件中搜索隐私关键词
                target_data['包含隐私关键词'] = False
                target_data['匹配原因'] = ''
                
                # 检查每个案件是否包含隐私关键词
                privacy_count = 0
                for idx, row in target_data.iterrows():
                    content = str(row[content_field]) if pd.notna(row[content_field]) else ""
                     
                    # 综合判断是否为隐私相关案件
                    is_related, reason = is_privacy_related(content)
                    
                    if is_related:
                        target_data.at[idx, '包含隐私关键词'] = True
                        target_data.at[idx, '匹配原因'] = reason
                        privacy_count += 1
                
                logging.info(f"  在 {len(target_data)} 个目标企业案件中，找到 {privacy_count} 个隐私相关案件")
                
                # 提取包含隐私关键词的行
                privacy_cases_in_file = target_data[target_data['包含隐私关键词']].copy()
                
                if len(privacy_cases_in_file) > 0:
                    # 添加来源文件信息
                    privacy_cases_in_file['来源文件'] = file
                    privacy_cases_in_file['来源年份'] = year
                    all_privacy_cases.append(privacy_cases_in_file)
                    logging.info(f"  已处理文件: {file} - 发现 {len(privacy_cases_in_file)} 个隐私相关案件")
                else:
                    logging.info(f"  文件 {file} 中没有找到隐私相关案件")
                    
                # 标记文件为已处理
                processed_files.add(file)
                save_checkpoint()
                
                # 每处理5个文件保存一次结果
                if (file_index + 1) % 5 == 0:
                    save_results()
                    logging.info(f"已处理 {file_index + 1} 个文件，当前已找到 {sum(len(batch) for batch in all_privacy_cases)} 个隐私相关案件")
                    
            except Exception as e:
                logging.error(f"处理文件 {file} 时出错: {str(e)}")
                import traceback
                traceback.print_exc()
                # 即使出错也标记为已处理，避免重复处理
                processed_files.add(file)
                save_checkpoint()

# 主程序
if __name__ == "__main__":
    logging.info("开始分析隐私相关案件")
    logging.info(f"时间范围: {START_DATE.date()} 到 {END_DATE.date()}")
    
    try:
        process_files()
        
        # 最终保存结果
        save_results()
        
        # 删除断点文件（如果存在），表示处理完成
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
            logging.info("处理完成，已删除断点文件")
        
        # 输出统计信息
        if all_privacy_cases:
            final_privacy_cases = pd.concat(all_privacy_cases, ignore_index=True)
            
            logging.info("\n最终统计信息:")
            logging.info(f"总共找到 {len(final_privacy_cases)} 个隐私相关案件")
            logging.info(f"涉及企业数量: {final_privacy_cases['匹配企业名称'].nunique()}")
            logging.info(f"涉及文件数量: {final_privacy_cases['来源文件'].nunique()}")
            
            # 按年份统计
            year_stats = final_privacy_cases['来源年份'].value_counts()
            logging.info("\n按年份统计:")
            for year, count in year_stats.items():
                logging.info(f"  {year}年: {count} 个案件")
                
            # 按企业统计
            company_stats = final_privacy_cases['匹配企业名称'].value_counts()
            logging.info("\n按企业统计 (前10):")
            for company, count in company_stats.head(10).items():
                logging.info(f"  {company}: {count} 个案件")
            
            # 按匹配原因统计
            reason_stats = final_privacy_cases['匹配原因'].value_counts()
            logging.info("\n按匹配原因统计:")
            for reason, count in reason_stats.items():
                logging.info(f"  {reason}: {count} 次")
        else:
            logging.info("未找到任何隐私相关案件。")
            
    except Exception as e:
        logging.error(f"程序执行过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        save_checkpoint()
        save_results()