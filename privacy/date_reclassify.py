import os
import pandas as pd
from datetime import datetime
from tqdm import tqdm

# 设置文件夹路径
source_folder = "/Volumes/T9/temp_files"
target_folder = "/Volumes/T9/classify_date"

# 创建目标文件夹（如果不存在）
os.makedirs(target_folder, exist_ok=True)

# 获取所有以'ws'或's41'开头的CSV文件
csv_files = [f for f in os.listdir(source_folder) 
             if (f.startswith('ws') or f.startswith('s41')) and f.endswith('.csv')
             and not f.startswith('.')]
print(f"找到 {len(csv_files)} 个需要处理的文件")
print("开始处理文件...")

success_count = 0
error_count = 0
# 逐个处理文件
for file in tqdm(csv_files, desc="处理文件中"):
    file_path = os.path.join(source_folder, file)
    
    try:
        # 读取CSV文件
        df = pd.read_csv(file_path)
        
        # 确保有裁判日期列（根据实际列名调整）
        if '裁判日期' in df.columns:
            # 转换日期格式
            df['裁判日期'] = pd.to_datetime(df['裁判日期'])
            
            # 提取年月信息
            df['年月'] = df['裁判日期'].dt.to_period('M')
            
            # 按年月分组并保存
            for period, group in df.groupby('年月'):
                # 构建目标文件名
                year_month = str(period).replace('-', '')
                target_file = f"data_{year_month}.csv"
                target_path = os.path.join(target_folder, target_file)
                
                # 写入文件（追加模式）
                if os.path.exists(target_path):
                    group.to_csv(target_path, mode='a', header=False, index=False)
                else:
                    group.to_csv(target_path, index=False)
            tqdm.write(f"✓ 已成功处理: {file}")
            success_count += 1      

        else:
            tqdm.write(f"✗ 文件 {file} 中没有找到'裁判日期'列，跳过处理")
            error_count += 1
            
    except Exception as e:
        tqdm.write(f"✗ 处理文件 {file} 时出错: {str(e)}")
        error_count += 1

print("\n处理完成!")
print(f"成功处理: {success_count} 个文件")
print(f"处理失败: {error_count} 个文件")

# 显示创建的文件统计
target_files = [f for f in os.listdir(target_folder) if f.endswith('.csv')]
print(f"共创建 {len(target_files)} 个按年月整理的文件")
print(f"目标文件夹: {target_folder}")

print("\n开始删除2021年8月之前的文件...")
deleted_count = 0

# 获取目标文件夹中的所有CSV文件
target_files = [f for f in os.listdir(target_folder) if f.startswith('data_') and f.endswith('.csv')]

for file in target_files:
    try:
        # 从文件名中提取年月信息
        # 文件名格式: data_YYYYMM.csv
        year_month_str = file.replace('data_', '').replace('.csv', '')
        
        if len(year_month_str) == 6 and year_month_str.isdigit():
            year = int(year_month_str[:4])
            month = int(year_month_str[4:6])
            
            # 检查是否早于2021年8月
            if year < 2021 or (year == 2021 and month < 8):
                file_path = os.path.join(target_folder, file)
                os.remove(file_path)
                print(f"已删除: {file}")
                deleted_count += 1
                
    except Exception as e:
        print(f"删除文件 {file} 时出错: {str(e)}")

# 显示最终统计信息
target_files_after = [f for f in os.listdir(target_folder) if f.endswith('.csv')]
print(f"\n清理完成! 删除了 {deleted_count} 个文件")
print(f"现在目标文件夹中有 {len(target_files_after)} 个文件")
print(f"目标文件夹: {target_folder}")