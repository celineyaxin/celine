import pandas as pd
import os

# 设置文件夹路径
folder_path = '/Users/chenyaxin/Downloads/RESSET_1'
output_folder_path = '/Users/chenyaxin/Downloads/RESSET_1/append'

merged_df = pd.DataFrame()

# 遍历文件夹中的所有.xls文件
for filename in os.listdir(folder_path):
    if filename.endswith('.xls') and not filename.startswith('.'):
        file_path = os.path.join(folder_path, filename)
        xls_df = pd.read_excel(file_path)
        required_columns = ['A股股票代码_A_StkCd', '上市标识_LstFlg','年末标识_YrFlg',	
        '季末标识_QtrFlg', '截止日期_EndDt','信息发布日期_InfoPubDt',	
        '信息来源_InfoSource', '信息类别编码()_InfoTypeCd', '股东排名_ShRank', 
        '股东名单_SHLst', '股东性质_SHChrct','股东类别_SHType',	'股东资格是否为合格境内机构投资者QDII()_SHQual_QDII',
        '股东资格是否为人民币合格境外投资者RQFII()_SHQual_RQFII', '持股数量增减(股)_HoldSumChg', '持股变动类型_HoldChgTp',
        '公司总股数(股)_ComFullShr', '流通股总股数(股)_TrdShr']
        xls_df = xls_df[required_columns]
        merged_df = pd.concat([merged_df, xls_df], ignore_index=True)
        
# 计算每个文件的最大行数
max_rows_per_file = 1048570
# 分割数据到多个文件
num_files = (len(merged_df) + max_rows_per_file - 1) // max_rows_per_file
for i in range(num_files):
    start_row = i * max_rows_per_file
    end_row = min((i + 1) * max_rows_per_file, len(merged_df))
    output_file_path = os.path.join(output_folder_path, f'merged_file_{i+1}.xlsx')
    merged_df.iloc[start_row:end_row].to_excel(output_file_path, index=False)

print(f"合并后的数据已保存至 '{output_folder_path}'")



