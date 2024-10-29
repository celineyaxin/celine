##complaints_part_3已经完成了文件分类需要替换分期易

import pandas as pd
file2_path = '/Users/chenyaxin/Desktop/websitdata/merge_data4/分期易.csv'  
df2 = pd.read_csv(file2_path)

code_and_business_dict = dict(zip(df2['投诉编号'], 
                                   list(zip(df2['编码'], df2['投诉商家']))))

file1_path = '/Users/chenyaxin/Desktop/websitdata/similarity/complaints_part_3.csv'  
# file1_path = '/Users/chenyaxin/Desktop/websitdata/test.csv'  

df1 = pd.read_csv(file1_path)

# 遍历文件1中的每一行，并更新编码和投诉商家
for index, row in df1.iterrows():
    if row['投诉编号'] in code_and_business_dict:
        code, business = code_and_business_dict[row['投诉编号']]
        df1.at[index, '编码'] = code
        df1.at[index, '投诉商家'] = business


output_path = '/Users/chenyaxin/Desktop/websitdata/similarity/updated_complaints_part_3.csv'  # 输出文件路径
df1.to_csv(output_path, index=False)
print(f"更新完成，结果已保存到 '{output_path}'")