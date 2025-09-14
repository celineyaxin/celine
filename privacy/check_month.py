import csv
from datetime import datetime

# 指定文件路径
file_path = '/Volumes/yaxindedisk 1/裁判文书/2021年裁判文书数据/ws_2021_12.csv'

# 初始化一个集合来存储年份和月份
years_months = set()

# 打开文件并提取“裁判日期”列的年份和月份
try:
    with open(file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        # 打印所有列名
        print("列名:", csv_reader.fieldnames)
        # 遍历文件并提取“裁判日期”列的年份和月份
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

# 判断是否只包含2021年11月的数据
if len(years_months) == 1 and (2021, 12) in years_months:
    print("文件中只包含2021年12月的数据")
else:
    print("文件中包含其他月份的数据")