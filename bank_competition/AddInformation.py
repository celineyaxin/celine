import pandas as pd
from collections import Counter

def enrich_frequency_data_specific_columns(original_file, frequency_file, output_file, name_column='所属公司'):
    """
    从原始文件中提取特定列信息，丰富频率统计文件
    
    参数:
    original_file: 原始数据文件路径
    frequency_file: 频率统计文件路径
    output_file: 输出文件路径
    name_column: 包含机构名称的列名
    """
    
    try:
        # 读取原始数据文件
        if original_file.endswith(('.xlsx', '.xls')):
            original_df = pd.read_excel(original_file)
        else:
            raise ValueError("不支持的文件格式，请使用Excel文件(.xlsx或.xls)")
        
        # 读取频率统计文件
        if frequency_file.endswith(('.xlsx', '.xls')):
            freq_df = pd.read_excel(frequency_file)
        else:
            raise ValueError("不支持的文件格式，请使用Excel文件(.xlsx或.xls)")
        
        # 检查必要的列是否存在
        required_columns = [name_column, '被罚个人所属单位', '被罚单位名称']
        # 检查文书号列是否存在
        has_penalty_number = '行政处罚决定书文号' in original_df.columns
        
        missing_columns = [col for col in required_columns if col not in original_df.columns]
        if missing_columns:
            raise ValueError(f"原始文件中缺少以下列: {', '.join(missing_columns)}")
        
        # 创建一个字典来存储每个机构名称对应的所有被罚个人所属单位、被罚单位名称和文书号
        penalty_units = {}
        penalty_orgs = {}
        penalty_numbers = {}  # 新增：存储文书号
        
        # 遍历原始数据，收集每个机构名称对应的所有相关数据
        for _, row in original_df.iterrows():
            org_name = str(row[name_column]).strip()
            penalty_unit = str(row['被罚个人所属单位']).strip() if pd.notna(row['被罚个人所属单位']) else ""
            penalty_org = str(row['被罚单位名称']).strip() if pd.notna(row['被罚单位名称']) else ""
            
            # 处理文书号（如果存在）
            if has_penalty_number:
                penalty_number = str(row['行政处罚决定书文号']).strip() if pd.notna(row['行政处罚决定书文号']) else ""
            else:
                penalty_number = ""
            
            # 初始化集合（如果尚未存在）
            if org_name not in penalty_units:
                penalty_units[org_name] = set()
            if org_name not in penalty_orgs:
                penalty_orgs[org_name] = set()
            if org_name not in penalty_numbers:
                penalty_numbers[org_name] = set()
            
            # 添加非空值到集合中（自动去重）
            if penalty_unit:
                penalty_units[org_name].add(penalty_unit)
            if penalty_org:
                penalty_orgs[org_name].add(penalty_org)
            if penalty_number:
                penalty_numbers[org_name].add(penalty_number)
        
        # 将集合转换为分号分隔的字符串
        penalty_units_str = {k: '; '.join(sorted(v)) for k, v in penalty_units.items()}
        penalty_orgs_str = {k: '; '.join(sorted(v)) for k, v in penalty_orgs.items()}
        penalty_numbers_str = {k: '; '.join(sorted(v)) for k, v in penalty_numbers.items()}
        
        # 将信息添加到频率统计DataFrame中
        freq_df['被罚个人所属单位列表'] = freq_df['机构名称'].map(penalty_units_str).fillna('')
        freq_df['被罚单位名称列表'] = freq_df['机构名称'].map(penalty_orgs_str).fillna('')
        
        # 添加文书号列（如果原始数据中有文书号）
        if has_penalty_number:
            freq_df['行政处罚决定书文号列表'] = freq_df['机构名称'].map(penalty_numbers_str).fillna('')
        
        # 保存到新的Excel文件
        freq_df.to_excel(output_file, index=False)
        
        print(f"处理完成！")
        print(f"已为 {len(freq_df)} 个机构名称添加了特定列的信息")
        if has_penalty_number:
            print(f"已添加行政处罚决定书文号列表")
        print(f"结果已保存到: {output_file}")
        
        return freq_df
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        return None

# 使用示例
if __name__ == "__main__":
    # 文件路径
    original_file = "/Users/chenyaxin/Desktop/信息规范/行政处罚需要完整的全称/提取所属公司.xlsx"
    frequency_file = "/Users/chenyaxin/Desktop/信息规范/行政处罚需要完整的全称/机构名称全称匹配结果.xlsx"
    output_file = "/Users/chenyaxin/Desktop/机构名称频率统计_增强版.xlsx"
    
    # 执行函数
    result_df = enrich_frequency_data_specific_columns(
        original_file=original_file,
        frequency_file=frequency_file,
        output_file=output_file,
        name_column='所属公司'
    )
    
    # 显示前几个结果
    if result_df is not None:
        print("\n前5个机构及其相关信息:")
        columns_to_show = ['序号', '机构名称', '出现频率', '被罚个人所属单位列表', '被罚单位名称列表']
        if '行政处罚决定书文号列表' in result_df.columns:
            columns_to_show.append('行政处罚决定书文号列表')
        print(result_df.head()[columns_to_show])