import os

# 指定目录
directory = '/Users/chenyaxin/Downloads/2023-12'

# 遍历目录中的所有文件
for filename in os.listdir(directory):
    if filename.endswith(".txt") and "wkky" in filename:
        new_filename = filename.replace("wkky", "")
        # 获取文件的原始路径
        old_filepath = os.path.join(directory, filename)
        # 获取新文件的路径
        new_filepath = os.path.join(directory, new_filename)
        # 重命名文件
        os.rename(old_filepath, new_filepath)
        print(f"Renamed '{filename}' to '{new_filename}'")