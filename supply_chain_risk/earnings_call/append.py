##合并原始文件
import pandas as pd
import os

def merge_excel_files(folder_path, file1, file2, output_file,columns_to_keep):
    file1_path = os.path.join(folder_path, file1)
    df1 = pd.read_excel(file1_path)

    file2_path = os.path.join(folder_path, file2)
    df2 = pd.read_excel(file2_path)

    merged_df = pd.concat([df1, df2], ignore_index=True)
    # merged_df = merged_df[merged_df["Year"] != 2024]

    # 提取指定的两列
    merged_df = merged_df[columns_to_keep]

    merged_df.to_excel(output_file, index=False)

# 示例使用
folder_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/原始数据/业绩说明会问答文本分析'  # 替换为你的文件夹路径
file1 = '业绩说明会问答文本分析_1.xlsx'  # 替换为第一个Excel文件的名称
file2 = '业绩说明会问答文本分析_2.xlsx'  # 替换为第二个Excel文件的名称

columns_to_keep= ['Qcntet', 'Acntet'] 
output_file = 'merged_output.xlsx'  # 替换为你想要保存的合并文件的名称

merge_excel_files(folder_path, file1, file2, output_file,columns_to_keep)
