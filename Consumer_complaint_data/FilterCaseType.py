import pandas as pd
import os
from tqdm import tqdm
import shutil

def process_and_split_data(input_file, output_dir):
    """
    处理数据：筛选条件 + 按年份切分
    """
    # 创建输出目录
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)  # 清空目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取文件大小
    file_size = os.path.getsize(input_file)
    print(f"输入文件大小: {file_size / (1024**3):.2f} GB")
    
    # 初始化统计变量
    stats = {
        'original_total': 0,
        'after_date_filter': 0,
        'after_case_filter': 0,
        'year_counts': {},
        'deleted_by_date': 0,
        'deleted_by_case': 0
    }
    
    # 分块读取并处理
    chunk_size = 50000
    year_files = {}  # 存储各年份的文件句柄
    
    # 先读取一行获取列名
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        header = f.readline().strip()
    
    # 计算总行数用于进度条
    total_rows = sum(1 for _ in open(input_file, 'r', encoding='utf-8-sig')) - 1
    stats['original_total'] = total_rows
    print(f"原始总行数: {total_rows:,}")
    
    # 分块读取并处理
    with tqdm(total=total_rows, desc="处理数据") as pbar:
        for chunk_idx, chunk in enumerate(pd.read_csv(input_file, encoding='utf-8-sig', chunksize=chunk_size)):
            # 步骤1: 按裁判日期筛选（保留2020年及以后）
            if '裁判日期' in chunk.columns:
                chunk['裁判日期'] = pd.to_datetime(chunk['裁判日期'], errors='coerce')
                chunk['裁判年份'] = chunk['裁判日期'].dt.year
                
                # 统计筛选前的年份分布
                if chunk_idx == 0:
                    print("\n原始数据年份分布:")
                    year_counts_before = chunk['裁判年份'].value_counts().sort_index()
                    for year, count in year_counts_before.items():
                        if pd.notna(year):
                            print(f"  {int(year)}年: {count:,} 条")
                
                # 筛选2020年及以后
                before_date_filter = len(chunk)
                chunk = chunk[chunk['裁判年份'] >= 2020].copy()
                after_date_filter = len(chunk)
                stats['deleted_by_date'] += (before_date_filter - after_date_filter)
                stats['after_date_filter'] += after_date_filter
                
                # 步骤2: 按案件类型筛选（仅保留民事案件）
                if '案件类型' in chunk.columns:
                    before_case_filter = len(chunk)
                    chunk = chunk[chunk['案件类型'] == '民事案件'].copy()
                    after_case_filter = len(chunk)
                    stats['deleted_by_case'] += (before_case_filter - after_case_filter)
                    stats['after_case_filter'] += after_case_filter
                    
                    # 步骤3: 按年份切分并保存
                    for year, year_group in chunk.groupby('裁判年份'):
                        year = int(year) if not pd.isna(year) else '未知年份'
                        
                        # 初始化年份文件
                        if year not in year_files:
                            year_file = os.path.join(output_dir, f"民事案件数据_{year}.csv")
                            year_files[year] = open(year_file, 'w', encoding='utf-8-sig')
                            year_files[year].write(header + '\n')
                            stats['year_counts'][year] = 0
                        
                        # 写入年份数据
                        year_group.to_csv(year_files[year], mode='a', index=False, header=False, encoding='utf-8-sig')
                        stats['year_counts'][year] += len(year_group)
            
            pbar.update(len(chunk))
    
    # 关闭所有文件句柄
    for year, file_handle in year_files.items():
        file_handle.close()
    
    return stats

def print_statistics(stats, output_dir):
    """
    打印详细的统计信息
    """
    print("\n" + "="*60)
    print("数据处理统计报告")
    print("="*60)
    
    print(f"原始总记录数: {stats['original_total']:,}")
    print(f"删除2020年之前记录: {stats['deleted_by_date']:,}")
    print(f"删除非民事案件记录: {stats['deleted_by_case']:,}")
    print(f"最终保留记录数: {stats['after_case_filter']:,}")
    
    print(f"\n删除记录比例:")
    date_ratio = stats['deleted_by_date'] / stats['original_total'] * 100
    case_ratio = stats['deleted_by_case'] / stats['original_total'] * 100
    retained_ratio = stats['after_case_filter'] / stats['original_total'] * 100
    print(f"  按日期删除: {date_ratio:.2f}%")
    print(f"  按案件类型删除: {case_ratio:.2f}%")
    print(f"  最终保留: {retained_ratio:.2f}%")
    
    print(f"\n按年份切分结果:")
    total_after_split = 0
    for year, count in sorted(stats['year_counts'].items()):
        print(f"  {year}年: {count:,} 条记录")
        total_after_split += count
    
    # 验证数据一致性
    if total_after_split == stats['after_case_filter']:
        print(f"\n✓ 数据一致性验证通过: 切分后总记录数 ({total_after_split:,}) = 筛选后总记录数 ({stats['after_case_filter']:,})")
    else:
        print(f"\n⚠ 数据一致性警告: 切分后总记录数 ({total_after_split:,}) ≠ 筛选后总记录数 ({stats['after_case_filter']:,})")
    
    # 显示输出文件信息
    print(f"\n输出文件位置: {output_dir}")
    year_files = [f for f in os.listdir(output_dir) if f.startswith('民事案件数据_') and f.endswith('.csv')]
    print(f"生成文件数量: {len(year_files)}")
    
    for year_file in sorted(year_files):
        file_path = os.path.join(output_dir, year_file)
        file_size = os.path.getsize(file_path) / (1024**2)  # MB
        year = year_file.replace('民事案件数据_', '').replace('.csv', '')
        count = stats['year_counts'].get(int(year) if year.isdigit() else year, 0)
        print(f"  {year_file} - {count:,} 条记录 - {file_size:.2f} MB")

# 主程序
if __name__ == "__main__":
    input_file = "/Volumes/T9/合并的司法处罚数据_2020-2024.csv"
    output_dir = "/Volumes/T9/民事案件数据_按年份切分"
    
    print("开始处理数据: 筛选 + 按年份切分")
    print("="*60)
    print(f"输入文件: {input_file}")
    print(f"输出目录: {output_dir}")
    print("-"*60)
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在 - {input_file}")
        exit(1)
    
    # 执行处理
    stats = process_and_split_data(input_file, output_dir)
    
    # 打印统计报告
    print_statistics(stats, output_dir)
    
    print("\n处理完成!")