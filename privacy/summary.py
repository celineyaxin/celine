import csv
from collections import Counter
from datetime import datetime
import pandas as pd
# 指定 CSV 文件路径
# file_path = '/Volumes/yaxindedisk 1/裁判文书/2024/s41_202401.csv'  # 替换为你的 CSV 文件路径
# file_path = '/Volumes/yaxindedisk 1/裁判文书/2020年裁判文书数据/2020年01月裁判文书数据.csv'  # 替换为你的 CSV 文件路径
file_path = '/Users/chenyaxin/Desktop/临时输出.csv'  # 替换为你的 CSV 文件路径
df = pd.read_csv(file_path)

# 打印前几行
print(df.head())
# 1. 打开文件并读取列名
# try:
#     with open(file_path, 'r', encoding='utf-8') as file:
#         csv_reader = csv.reader(file)
#         # 读取第一行作为列名
#         columns = next(csv_reader)
#         print("列名:", columns)
# except FileNotFoundError:
#     print(f"文件未找到: {file_path}")
# except Exception as e:
#     print(f"读取文件时发生错误: {e}")



# 2. 打开文件并读取“裁判日期”列（因为2024年的数据比较混乱）
# year_count = Counter()
# try:
#     with open(file_path, 'r', encoding='utf-8') as file:
#         csv_reader = csv.DictReader(file)
#         # 打印“裁判日期”列的内容
#         print("裁判日期列的内容:")
#         for row in csv_reader:
#             date_str = row.get('裁判日期', '')
#             if date_str:
#                 try:
#                     # 解析日期字符串
#                     date_obj = datetime.strptime(date_str, '%Y-%m-%d')
#                     # 提取年份
#                     year = date_obj.year
#                     # 更新年份计数器
#                     year_count[year] += 1
#                     # 打印日期
#                     print(date_str)
#                 except ValueError:
#                     print(f"无法解析日期: {date_str}")
# except FileNotFoundError:
#     print(f"文件未找到: {file_path}")
# except Exception as e:
#     print(f"读取文件时发生错误: {e}")

# # 打印每个年份的记录数
# print("\n每个年份的记录数:")
# for year, count in year_count.items():
#     print(f"{year} 年: {count} 条")

# 3. 看看一列的内容格式
# try:
#     # file_path = '/Volumes/yaxindedisk 1/裁判文书/2020年裁判文书数据/2020年01月裁判文书数据.csv'  # 替换为你的 CSV 文件路径
#     file_path = '/Volumes/yaxindedisk 1/裁判文书/2024/s41_202401.csv'  # 替换为你的 CSV 文件路径

#     with open(file_path, 'r', encoding='utf-8') as file:
#         csv_reader = csv.reader(file)
#         # 读取第一行作为列名
#         columns = next(csv_reader)
#         print("列名:", columns)
        
#         # 找到“案件名称”这一列的索引
#         if '案件名称' in columns:
#             case_name_index = columns.index('案件名称')
#         # if '全文' in columns:
#         #     case_name_index = columns.index('全文')
#         else:
#             print("未找到'案件名称'这一列")
#             exit()
        
#         # 读取“案件名称”这一列的前几十条内容
#         case_names = []
#         for i, row in enumerate(csv_reader):
#             if i >= 50:  # 限制为前50条
#                 break
#             if len(row) > case_name_index:
#                 case_names.append(row[case_name_index])
        
#         print("案件名称的前几十条内容:")
#         for case_name in case_names:
#             print(case_name)
# except FileNotFoundError:
#     print(f"文件未找到: {file_path}")
# except Exception as e:
#     print(f"读取文件时发生错误: {e}")