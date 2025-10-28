import pandas as pd
from collections import Counter

def process_institution_names(input_file, output_file, name_column='所属公司'):
    """
    处理金融机构名称，按频率排序并保存到Excel
    
    参数:
    input_file: 输入文件路径 (支持.xlsx, .xls)
    output_file: 输出Excel文件路径
    name_column: 包含机构名称的列名，默认为'所属公司'
    """
    
    try:
        # 读取文件 - 修正了文件类型判断逻辑
        if input_file.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(input_file)
        else:
            raise ValueError("不支持的文件格式，请使用Excel文件(.xlsx或.xls)")
        
        # 检查指定列是否存在
        if name_column not in df.columns:
            available_columns = ', '.join(df.columns.tolist())
            raise ValueError(f"列 '{name_column}' 不存在。可用列: {available_columns}")
        
        # 提取机构名称并清理数据
        names = df[name_column].dropna().astype(str).str.strip()
        
        # 统计频率
        name_counter = Counter(names)
        
        # 创建频率统计DataFrame并按频率降序排列
        freq_df = pd.DataFrame({
            '机构名称': list(name_counter.keys()),
            '出现频率': list(name_counter.values())
        })
        
        freq_df = freq_df.sort_values('出现频率', ascending=False).reset_index(drop=True)
        
        # 添加序号列
        freq_df.insert(0, '序号', range(1, len(freq_df) + 1))
        
        # 保存到Excel
        freq_df.to_excel(output_file, index=False)
        
        print(f"处理完成！")
        print(f"总共有 {len(freq_df)} 个不同的机构名称")
        print(f"最高频率: {freq_df['出现频率'].max()}, 最低频率: {freq_df['出现频率'].min()}")
        print(f"结果已保存到: {output_file}")
        
        return freq_df
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        return None

# 使用示例
if __name__ == "__main__":
    # 请根据实际情况修改文件路径和列名
    input_file = "/Users/chenyaxin/Desktop/信息规范/提取所属公司.xlsx"  # 替换为您的文件路径
    output_file = "/Users/chenyaxin/Desktop/机构名称频率统计.xlsx"  # 输出文件名
    
    # 如果您的列名不是'所属公司'，请修改下面的参数
    result_df = process_institution_names(
        input_file=input_file,
        output_file=output_file,
        name_column='所属公司'  # 替换为您的实际列名
    )
    
    # 显示前10个最高频的名称
    if result_df is not None:
        print("\n前10个最高频的机构名称:")
        print(result_df.head(10)[['序号', '机构名称', '出现频率']])