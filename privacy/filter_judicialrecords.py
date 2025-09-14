import os
import pandas as pd
from tqdm import tqdm
import glob

# 读取企业名称
def read_company_names(excel_path, company_column_name):
    try:
        df = pd.read_excel(excel_path)
        # 假设企业名称在指定列
        company_names = df[company_column_name].dropna().tolist()
        return company_names
    except Exception as e:
        print(f"读取Excel文件时发生错误: {e}")
        return []

# 处理单个CSV文件
def process_csv_file(file_path, company_names, output_dir, chunk_size=10000):
    try:
        # 获取文件名（不含扩展名）用于创建临时文件
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        temp_file_path = os.path.join(output_dir, f"{file_name}_temp.csv")
        
        # 如果临时文件已经存在，跳过处理
        if os.path.exists(temp_file_path):
            print(f"临时文件 {temp_file_path} 已存在，跳过处理")
            return 0
        
        # 分块读取CSV文件
        chunks = pd.read_csv(file_path, encoding='utf-8', chunksize=chunk_size)
        
        # 打开临时文件用于写入
        with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
            first_chunk = True
            for chunk in tqdm(chunks, desc=f"处理文件 {file_path}"):
                required_columns = ['案号', '所属地区', '案件类型', '审理程序', '案件名称', '案由', '全文', '裁判日期']
                missing_columns = [col for col in required_columns if col not in chunk.columns]
                if missing_columns:
                    print(f"文件 {file_path} 中缺少列: {', '.join(missing_columns)}")
                    return 0
                
                chunk = chunk[required_columns]
                
                # 提取包含企业名称的案件名称及相关数据
                extracted_data = []
                for company_name in company_names:
                    mask = chunk['案件名称'].str.contains(company_name, na=False, regex=False)
                    if mask.any():
                        temp_df = chunk[mask].copy()
                        temp_df['企业名称'] = company_name
                        extracted_data.append(temp_df)
                
                if not extracted_data:
                    continue
                
                # 合并所有匹配的数据
                combined_df = pd.concat(extracted_data, ignore_index=True)
                combined_df.drop_duplicates(inplace=True)
                
                # 写入临时文件
                if first_chunk:
                    combined_df.to_csv(temp_file, index=False, encoding='utf-8', mode='w')
                    first_chunk = False
                else:
                    combined_df.to_csv(temp_file, index=False, encoding='utf-8', mode='a', header=False)
        
        print(f"文件 {file_path} 处理完成，生成临时文件: {temp_file_path}")
        return len(combined_df)
    except Exception as e:
        print(f"处理文件 {file_path} 时发生错误: {e}")
        return 0

# 主函数
def main(excel_path, company_column_name, base_folder_path, output_dir):
    # 创建临时文件目录
    temp_dir = os.path.join(output_dir, "temp_files")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 读取企业名称
    company_names = read_company_names(excel_path, company_column_name)
    if not company_names:
        print("未找到企业名称数据")
        return
    
    # 初始化写入条目计数
    total_entries_written = 0
    
    # 遍历所有年份文件夹
    for year in range(2019, 2025):
        year_folder_path = os.path.join(base_folder_path, str(year))
        if os.path.exists(year_folder_path):
            print(f"正在处理年份文件夹: {year_folder_path}")
            # 遍历每个月份的CSV文件
            for root, _, files in os.walk(year_folder_path):
                for file in files:
                    if file.endswith('.csv') and not file.startswith('.'):
                        file_path = os.path.join(root, file)
                        entries_written = process_csv_file(
                            file_path, company_names, temp_dir
                        )
                        total_entries_written += entries_written
                        print(f"文件 {file_path} 处理条目数量: {entries_written}")
    
    print(f"总处理条目数量: {total_entries_written}")
# 处理2018年
# def main(excel_path, company_column_name, base_folder_path, output_dir):
#     # 1. 临时目录直接用 output_dir，不再套两层 temp_files
#     os.makedirs(output_dir, exist_ok=True)

#     company_names = read_company_names(excel_path, company_column_name)
#     if not company_names:
#         print("未找到企业名称数据")
#         return

#     total_entries_written = 0

#     year_folder_path = os.path.join(base_folder_path, '2018')
#     if os.path.exists(year_folder_path):          # ← 这里的 if
#         print(f"正在处理文件夹: {year_folder_path}")
#         for root, _, files in os.walk(year_folder_path):
#             for file in files:
#                 if file.endswith('.csv') and not file.startswith('.'):
#                     file_path = os.path.join(root, file)
#                     entries = process_csv_file(file_path, company_names, output_dir)
#                     total_entries_written += entries
#                     print(f"文件 {file_path} 提取条目: {entries}")
#     else:                                        # ← 与 if 对齐
#         print("2018 文件夹不存在，请检查路径")

#     print(f"===== 总提取条目数量: {total_entries_written} =====")

# 示例用法
excel_path = '/Users/chenyaxin/Desktop/websitdata/merge_data6/企业基础工商信息.xlsx'  # 替换为你的Excel文件路径
company_column_name = 'compn'  # 替换为你的企业名称列名
base_folder_path = '/Volumes/yaxindedisk 1/裁判文书'  # 替换为你的裁判文书数据文件夹路径
output_dir = '/Volumes/yaxindedisk 1/'  # 替换为你的输出目录路径

if __name__ == "__main__":
    main(excel_path, company_column_name, base_folder_path, output_dir)