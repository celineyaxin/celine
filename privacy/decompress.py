import zipfile
import os

# 指定 ZIP 文件路径
zip_file_path = '/Volumes/yaxindedisk 1/2020年裁判文书数据.zip'

# 指定解压目标文件夹路径
extract_to_path = '/Volumes/yaxindedisk 1/裁判文书'  # 替换为你的目标文件夹路径

# 确保解压目标文件夹存在
os.makedirs(extract_to_path, exist_ok=True)

# 打开 ZIP 文件并解压到目标文件夹
with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    zip_ref.extractall(extract_to_path)

print(f"解压完成: {zip_file_path} 到 {extract_to_path}")
