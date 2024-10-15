import os
import glob

# 指定文件夹路径
input_dir = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/文本'

# 获取文件夹中所有txt文件的路径列表
txt_files = glob.glob(os.path.join(input_dir, '*.txt'))

# 遍历并删除包含'06-30'的文件
for file_path in txt_files:
    file_name = os.path.basename(file_path)
    if '06-30' in file_name or file_name.startswith('8'):
        os.remove(file_path)
        print(f"Deleted: {file_path}")