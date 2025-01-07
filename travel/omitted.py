import pandas as pd
import os
import re
import chardet

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
    try:
        merged_df.to_csv(output_excel_path, index=False)
        print(merged_df)
        print(f"所有CSV文件已合并，编号提取完毕，并保存到 {output_excel_path}")
    except Exception as e:
        print(f"保存Excel文件时出错: {e}")
    print(f"一共读取了 {csv_file_count} 个CSV文件。") 
  
def remove_complaint_ids(original_csv_path, merged_excel_path, output_csv_path):
    original_df = pd.read_csv(original_csv_path, usecols=['投诉编号'])  
    merged_df = pd.read_csv(merged_excel_path, usecols=['投诉编号'])  

    remaining_ids = original_df[~original_df['投诉编号'].isin(merged_df['投诉编号'])]
    print(len(remaining_ids))
    remaining_ids.to_csv(output_csv_path, index=False)
    print(f"剩下的编号已保存到 {output_csv_path}")

if __name__ == "__main__":
    folder_path = '/Users/chenyaxin/Desktop/互联网旅游公约/业务分类结果'  
    output_excel_path = '/Users/chenyaxin/Desktop/互联网旅游公约/业务分类结果/finish.csv'  
    url_column = '页面网址'
    merge_csv_to_excel(folder_path, output_excel_path, url_column)

    original_csv_path = '/Users/chenyaxin/Desktop/互联网旅游公约/meituan_quna.csv'  
    output_csv_path = '/Users/chenyaxin/Desktop/互联网旅游公约/爬取服务数据/add_meituan_quna.csv' 
    remove_complaint_ids(original_csv_path, output_excel_path, output_csv_path)
