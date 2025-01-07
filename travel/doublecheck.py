import pandas as pd
import shutil
from openpyxl import load_workbook

existing_excel_path = '/Users/chenyaxin/Desktop/互联网旅游公约/merchant_results.xlsx'
with pd.ExcelWriter(existing_excel_path, engine='openpyxl', mode='a') as writer:
    filtered_df = pd.read_excel(existing_excel_path, sheet_name='Rejected Data')

business_names_path = '/Users/chenyaxin/Desktop/互联网旅游公约/需要剔除的商家名称.xlsx'
business_names_df = pd.read_excel(business_names_path)
business_names_df['商家名称'] = business_names_df['商家名称'].astype(str).str.strip()
business_names = set(business_names_df['商家名称'])

financial_business_names_path = '/Users/chenyaxin/Desktop/websitdata/金融类企业全称.xlsx'
financial_business_names_df = pd.read_excel(financial_business_names_path)
financial_business_names_df['投诉商家'] = financial_business_names_df['投诉商家'].astype(str).str.strip()
financial_business_names = set(financial_business_names_df['投诉商家'])

df_filtered = filtered_df[~filtered_df['投诉商家'].isin(business_names) & ~filtered_df['投诉商家'].isin(financial_business_names)]
df_rejected = filtered_df[filtered_df['投诉商家'].isin(business_names) | filtered_df['投诉商家'].isin(financial_business_names)]

excel_path = '/Users/chenyaxin/Desktop/互联网旅游公约/doublecheck.xlsx'

# 使用ExcelWriter保存数据到两个工作表
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    df_filtered.to_excel(writer, sheet_name='Filtered Data', index=False)
    df_rejected.to_excel(writer, sheet_name='Rejected Data', index=False)
    print(f"处理后的数据已保存至 '{excel_path}'，其中包含两个新的工作表：'Filtered Data' 和 'Rejected Data'")
