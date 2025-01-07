import pandas as pd
import os

# 设置文件夹路径和输出Excel文件路径
folder_path = '/Users/chenyaxin/Downloads/RESSET_1/append'
output_excel_path = '/Users/chenyaxin/Downloads/RESSET_1/filtered_results.xlsx'

# 定义列名
hold_sum_chg_column = '持股数量增减(股)_HoldSumChg'

# 初始化一个空的DataFrame来存储所有筛选后的数据
all_filtered_df = pd.DataFrame()

# 遍历文件夹中的所有Excel文件
for filename in os.listdir(folder_path):
    if filename.endswith('.xlsx') and not filename.startswith('.'):
        file_path = os.path.join(folder_path, filename)
        
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 筛选'持股数量增减(股)_HoldSumChg'列值为负的行
        filtered_df = df[df[hold_sum_chg_column] < 0]
        
        # 将筛选后的数据追加到all_filtered_df中
        all_filtered_df = pd.concat([all_filtered_df, filtered_df], ignore_index=True)

# 将所有筛选后的数据写入一个新的Excel文件
all_filtered_df.to_excel(output_excel_path, sheet_name='Filtered Data', index=False)

print(f"筛选后的数据已保存至 '{output_excel_path}'")