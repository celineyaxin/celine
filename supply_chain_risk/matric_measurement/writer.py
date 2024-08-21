import pandas as pd
import os

# 设置文件夹路径和输出文件名
folder_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/risk_score'
output_excel_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/risk_score/Total_Risk_Score.xlsx'

# 获取文件夹中所有 CSV 文件的列表
csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

# 读取所有 CSV 文件并存储到列表中
dfs = []
for file in csv_files:
    file_path = os.path.join(folder_path, file)
    df = pd.read_csv(file_path)
    dfs.append(df)

merged_df = pd.concat(dfs, ignore_index=True)

with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
    merged_df.to_excel(writer, index=False, sheet_name='Merged Data')

print(f"All CSV files have been merged into {output_excel_path}")