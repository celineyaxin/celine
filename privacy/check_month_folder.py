import os
import csv
from datetime import datetime

# 设置字段大小限制为一个较大的值，例如 10MB
csv.field_size_limit(10 * 1024 * 1024)

# 指定根文件夹路径
year_folder_path = '/Volumes/yaxindedisk 1/裁判文书/2024'

# 检查文件夹是否存在
if not os.path.exists(year_folder_path):
    print(f"指定的文件夹路径不存在: {year_folder_path}")
    exit(1)

# 遍历年份文件夹中的每个文件
for month_file in os.listdir(year_folder_path):
    file_path = os.path.join(year_folder_path, month_file)
    
    # # 检查是否是文件且文件名以 ws 开头
    # if os.path.isfile(file_path) and month_file.startswith('ws') and month_file.endswith('.csv'):
    if os.path.isfile(file_path) and month_file.startswith('s41') and month_file.endswith('.csv'):
        print(f"正在检查文件: {month_file}")
        
        # 初始化一个集合来存储年份和月份
        years_months = set()
        
        # 打开文件并提取“裁判日期”列的年份和月份
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    date_str = row.get('裁判日期', '')
                    if date_str:
                        try:
                            # 解析日期字符串
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                            # 提取年份和月份
                            year_month = (date_obj.year, date_obj.month)
                            years_months.add(year_month)
                        except ValueError:
                            print(f"无法解析日期: {date_str}")
        except FileNotFoundError:
            print(f"文件未找到: {file_path}")
        except Exception as e:
            print(f"读取文件时发生错误: {e}")
        
        # 从文件名中提取预期的年份和月份
        expected_year = int(os.path.basename(year_folder_path))
        # expected_month = int(month_file.split('_')[2].split('.')[0])
        expected_month = int(month_file.split('_')[1].split('.')[0])
        # 判断文件中的数据是否只包含对应年份和月份的数据
        if len(years_months) == 1 and (expected_year, expected_month) in years_months:
            print(f"文件 {month_file} 只包含 {expected_year} 年 {expected_month} 月的数据")
        else:
            print(f"文件 {month_file} 包含其他年份或月份的数据: {years_months}")