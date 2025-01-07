
import csv
import os

def split_csv(file_path, num_parts):
    # 打开原始CSV文件
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        # 读取标题行
        headers = next(reader)

        # 计算每个小文件应该包含的行数
        total_rows = sum(1 for row in reader) + 1  # 加1包括标题行
        part_size = (total_rows + num_parts - 1) // num_parts  # 向上取整

        # 重置文件指针到开始
        csvfile.seek(0)
        reader = csv.reader(csvfile)
        next(reader)  # 跳过标题行

        current_row = 0
        for i in range(num_parts):
            # 创建新的CSV文件
            part_file = f"{os.path.splitext(file_path)[0]}_part{i+1}.csv"
            with open(part_file, 'w', newline='', encoding='utf-8') as part_csv:
                writer = csv.writer(part_csv)
                # 写入标题行
                writer.writerow(headers)

                # 写入数据行
                for j in range(part_size):
                    try:
                        row = next(reader)
                        writer.writerow(row)
                        current_row += 1
                    except StopIteration:
                        # 如果没有更多的行可以读取，就跳出循环
                        break


# 使用函数
file_path = '/Users/chenyaxin/Desktop/互联网旅游公约/meituan_quna.csv' 
split_csv(file_path, 76)