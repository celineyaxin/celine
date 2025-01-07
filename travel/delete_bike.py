import pandas as pd

df = pd.read_csv('/Users/chenyaxin/Desktop/互联网旅游公约/extracted_complaints.csv')  # 或者使用 pd.read_excel('your_file.xlsx')
df['发起投诉内容'] = df['发起投诉内容'].astype(str)
filtered_df = df[df['投诉对象'] == '美团客服小美']
keywords = '单车|自行车｜充电宝'
contains_keywords = filtered_df['发起投诉内容'].str.contains(keywords, na=False, case=False)
# filtered_df = filtered_df[~contains_keywords]  # 不包含关键词的行
deleted_df = filtered_df[contains_keywords]    # 包含关键词的行
deleted_df.to_csv('/Users/chenyaxin/Desktop/互联网旅游公约/meituan_delete.csv', index=False)