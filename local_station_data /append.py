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
    # pattern = r"/complaint/view/(\d{11})/"
    pattern = r"/complaint/view/(\d{11})(/)?$"
    # 提取编号并创建新的列
    merged_df['Complaint_ID'] = merged_df[url_column].apply(lambda x: re.search(pattern, x).group(1) if re.search(pattern, x) else 'N/A')

    # 将合并后的数据保存到Excel文件中
    try:
        merged_df.to_excel(output_excel_path, index=False)
        print(f"所有CSV文件已合并，编号提取完毕，并保存到 {output_excel_path}")
    except Exception as e:
        print(f"保存Excel文件时出错: {e}")
        

# 指定包含CSV文件的文件夹路径
folder_path = '/Volumes/yaxindedisk 1/导出'  # 替换为包含CSV文件的文件夹路径
# 指定合并后的Excel文件的路径
output_excel_path = '/Users/chenyaxin/Desktop/地方站导出数据/广东站重新分类/merged.xlsx'  # 合并后的Excel文件路径
url_column = '页面网址'
merge_csv_to_excel(folder_path, output_excel_path,url_column)