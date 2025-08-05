import pandas as pd
import os

# 1. 读文件
src_file = "/Users/chenyaxin/Desktop/business_classify_dp.xlsx"
df = pd.read_excel(src_file)

# 2. 构造布尔条件
cond1 = df['投诉商家'].str.contains('信用卡|银行', na=False, regex=True)
cond2 = (df['投诉商家'] == '中国平安') & df['投诉内容'].str.contains('信用卡|贷记卡', na=False, regex=True)
mask = cond1 | cond2          # 满足任一条件即命中

# 3. 提取命中行
hit_rows = df[mask].copy()
cleaned_df = df[~mask].copy()
# 4. 把原表中命中的单元格内容设为空字符串
df.loc[mask, ['投诉商家', '投诉内容']] = ''

clean_file = '/Users/chenyaxin/Desktop/cleaned.xlsx'
hit_file   = '/Users/chenyaxin/Desktop/hit_rows.xlsx'

cleaned_df.to_excel(clean_file, index=False)
hit_rows.to_excel(hit_file, index=False)

print('处理完毕！')
print(f'已生成：{clean_file}（删除后） 和 {hit_file}（被删除行）')