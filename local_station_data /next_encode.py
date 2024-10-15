import pandas as pd
import os
import re
import chardet
import csv

def merge_csv_to_excel(folder_path, output_excel_path, url_column):
    merged_df = pd.DataFrame()
    csv_file_count = 0 
    if not os.path.exists(folder_path):
        print(f"文件夹路径不存在: {folder_path}")
        return
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

    cells_count = merged_df[merged_df[url_column].astype(str).str.contains('hb', na=False)].shape[0] 
    print(cells_count)
    gd_pattern = r"https://hb\.tousu\.sina\.com\.cn/complaint/view/(\d{11})/?" 
    merged_df[url_column] = merged_df[url_column].astype(str)
    merged_df['gd_complaint_id'] = merged_df[url_column].apply(lambda x: re.search(gd_pattern, x).group(1) if re.search(gd_pattern, x) else None)
    df_guangdong = merged_df.dropna(subset=['gd_complaint_id'])
    # df_guangdong = df_guangdong.drop_duplicates(subset=['gd_complaint_id'])
    print(len(df_guangdong))
    print(f"一共读取了 {csv_file_count} 个CSV文件。") 
    try:
        df_guangdong.to_excel(output_excel_path, index=False)
        print(f"提取的湖北地区编号已添加到 '{output_excel_path}' 的新列中")
    except Exception as e:
        print(f"保存修改后的Excel文件时出错: {e}")

def remove_complaint_ids(original_csv_path, merged_excel_path, output_csv_path, url_column):
    original_df = pd.read_csv(original_csv_path, usecols=['投诉编号'])  
    merged_df = pd.read_excel(merged_excel_path, usecols=['gd_complaint_id'])  

    remaining_ids = original_df[~original_df['投诉编号'].isin(merged_df['gd_complaint_id'])]
    print(len(remaining_ids))
    remaining_ids.to_csv(output_csv_path, index=False)
    print(f"剩下的编号已保存到 {output_csv_path}")

if __name__ == "__main__":
    folder_path = '/Users/chenyaxin/Desktop/地方站导出数据/湖北站/导出'  # 替换为包含CSV文件的文件夹路径
    output_excel_path = '/Users/chenyaxin/Desktop/地方站导出数据/湖北站/merged.xlsx'  
    url_column = '页面网址'
    merge_csv_to_excel(folder_path, output_excel_path, url_column)

    original_csv_path = '/Users/chenyaxin/Desktop/地方站导出数据/湖北站/complaint_ids_classfy_hb.csv'  
    output_csv_path = '/Users/chenyaxin/Desktop/地方站导出数据/四川站/complaint_ids_classfy_sc.csv' 
    remove_complaint_ids(original_csv_path, output_excel_path, output_csv_path, url_column)
