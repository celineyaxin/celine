import pandas as pd
import os
import re 
import chardet

def merge_csv_to_excel(folder_path, output_excel_path,url_column):
    merged_df = pd.DataFrame()
    csv_file_count = 0 

    if not os.path.exists(folder_path):
        print(f"文件夹路径不存在: {folder_path}")
        return
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv') and not filename.startswith('.'):
            file_path = os.path.join(folder_path, filename)
            print(f"正在处理文件: {file_path}")
            try:
                with open(file_path, 'rb') as f:
                    result = chardet.detect(f.read(10000))  # 读取前10000字节来猜测编码
                    encoding = result['encoding']

                csv_df = pd.read_csv(file_path, encoding=encoding)
                print(f"文件 {filename} 读取成功，数据行数: {len(csv_df)}")
                merged_df = pd.concat([merged_df, csv_df], ignore_index=True)
                csv_file_count += 1 
            except Exception as e:
                print(f"读取文件 {filename} 时出错: {e}")

    # 检查合并后的数据是否为空
    if merged_df.empty:
        print("合并后的数据为空。")
        return

    try:
        merged_df.to_excel(output_excel_path, index=False)
        print(f"所有CSV文件已合并，编号提取完毕，并保存到 {output_excel_path}")
    except Exception as e:
        print(f"保存Excel文件时出错: {e}")
    cells_count = merged_df[merged_df[url_column].astype(str).str.contains('sx', na=False)].shape[0] 
    print(cells_count)
    gd_pattern = r"https://sx\.tousu\.sina\.com\.cn/complaint/view/(\d{11})/?"
    merged_df[url_column] = merged_df[url_column].astype(str)
    merged_df['gd_complaint_id'] = merged_df[url_column].apply(lambda x: re.search(gd_pattern, x).group(1) if re.search(gd_pattern, x) else None)
    df_guangdong = merged_df.dropna(subset=['gd_complaint_id'])
    print(len(df_guangdong))
    print(f"一共读取了 {csv_file_count} 个CSV文件。") 
    try:
        df_guangdong.to_excel(output_excel_path, index=False)
        print(f"提取的浙江地区编号已添加到 '{output_excel_path}' 的新列中")
    except Exception as e:
        print(f"保存修改后的Excel文件时出错: {e}")
# 指定包含CSV文件的文件夹路径
folder_path = '/Volumes/yaxindedisk 1/地方站数据/陕西站/导出'  # 替换为包含CSV文件的文件夹路径
# 指定合并后的Excel文件的路径
output_excel_path = '/Volumes/yaxindedisk 1/地方站数据/陕西站/导出/merged.xlsx'  # 合并后的Excel文件路径
url_column = '页面网址'
merge_csv_to_excel(folder_path, output_excel_path,url_column)