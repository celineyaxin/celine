import pandas as pd
import os
import pandas as pd

# 1. 读 CSV（默认 utf-8；如遇中文乱码可改为 encoding='gbk'）
src_file = "./financial_final.csv"
df = pd.read_csv(src_file, encoding='utf-8')

# 2. 构造筛选条件
cond1 = df['投诉商家'].str.contains('信用卡|银行', na=False, regex=True)
cond2 = (df['投诉商家'] == '中国平安') & \
        df['投诉内容'].str.contains('信用卡|贷记卡', na=False, regex=True)
mask = cond1 | cond2

# 3. 提取被删除行
removed_rows = df[mask].copy()

# 4. 删除这些行
cleaned_df = df[~mask].copy()

# 5. 写出 CSV（index=False 去掉行号）
cleaned_file = './business_classify.csv'
removed_file = './creditcard.csv'

cleaned_df.to_csv(cleaned_file, index=False, encoding='utf-8-sig')   # utf-8-sig 兼容 Excel
removed_rows.to_csv(removed_file, index=False, encoding='utf-8-sig')

print('处理完成！')
print(f'已生成：{cleaned_file}（删除后） 和 {removed_file}（被删除行）')
