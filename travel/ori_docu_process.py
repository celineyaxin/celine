import os
import pandas as pd
from tqdm import tqdm
import chardet

folder_path = '/Volumes/yaxindedisk 1/黑猫原始网页数据备份/merge_data2'
output_folder = '/Users/chenyaxin/Desktop/互联网旅游公约/原始数据处理'
csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv") and not f.startswith('.')]
columns_to_extract = ['发布时间', '投诉编号', '投诉对象', '发起投诉内容']

for csv_file in tqdm(csv_files, desc='Processing files'):
    csv_path = os.path.join(folder_path, csv_file)
    with open(csv_path, 'rb') as f:
        result = chardet.detect(f.read(10000))  # 读取前10000字节来猜测编码
        encoding = result['encoding']
        print(f"Detected encoding for {csv_file}: {encoding}")  # 打印检测到的编码

    try:
        df = pd.read_csv(csv_path, usecols=columns_to_extract, encoding=encoding)
        df = df.dropna(subset=columns_to_extract)
        df = df.drop_duplicates(subset=['投诉编号'], keep='first')
        if df.empty:
            print(f"文件 {csv_file} 读取为空")
        else:
            print(f"文件 {csv_file} 读取成功，数据行数: {len(df)}")
            print(df.head())
            df['发布时间'] = pd.to_datetime(df['发布时间'], format='%Y年%m月%d日 %H:%M', errors='coerce')
            df = df[df['发布时间'].dt.year <= 2023]
            output_filename = f"{os.path.splitext(csv_file)[0]}_filtered.csv"
            output_path = os.path.join(output_folder, output_filename)
            df.to_csv(output_path, index=False)
            print(f"处理后的数据已保存至 {output_path}")
    except Exception as e:
        print(f"处理文件 {csv_file} 时发生错误: {e}")