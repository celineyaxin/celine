import pandas as pd
import os
import re 

def merge_csv_to_excel(folder_path, output_excel_path,url_column):
    merged_df = pd.DataFrame()

    if not os.path.exists(folder_path):
        print(f"文件夹路径不存在: {folder_path}")
        return
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(folder_path, filename)
            print(f"正在处理文件: {file_path}")
            try:
                # 读取CSV文件
                csv_df = pd.read_csv(file_path)
                print(f"文件 {filename} 读取成功，数据行数: {len(csv_df)}")
                
                # 将读取的数据追加到merged_df中
                merged_df = pd.concat([merged_df, csv_df], ignore_index=True)
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
        
    gd_pattern = r"https://gd\.tousu\.sina\.com\.cn/complaint/view/(\d{11})/?"

    merged_df['gd_complaint_id'] = merged_df[url_column].apply(lambda x: re.search(gd_pattern, x).group(1) if re.search(gd_pattern, x) else None)
    df_guangdong = merged_df.dropna(subset=['gd_complaint_id'])
    try:
        df_guangdong.to_excel(output_excel_path, index=False)
        print(f"提取的广东地区编号已添加到 '{output_excel_path}' 的新列中")
    except Exception as e:
        print(f"保存修改后的Excel文件时出错: {e}")
# 指定包含CSV文件的文件夹路径
folder_path = '/Users/chenyaxin/Desktop/地方站导出数据'  # 替换为包含CSV文件的文件夹路径
# 指定合并后的Excel文件的路径
output_excel_path = '/Users/chenyaxin/Desktop/地方站导出数据/merged.xlsx'  # 合并后的Excel文件路径
url_column = '页面网址'
merge_csv_to_excel(folder_path, output_excel_path,url_column)