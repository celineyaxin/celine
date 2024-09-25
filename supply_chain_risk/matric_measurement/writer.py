import pandas as pd
import os

# 设置文件夹路径和输出文件名
folder_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/final_version'
output_excel_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/final_version/Risk_Score.xlsx'
csv_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith('.csv')]

dfs = []
for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    dfs.append(df)
merged_df = pd.concat(dfs, ignore_index=True)
merged_df.to_excel(output_excel_path, index=False, sheet_name='Merged Data')



