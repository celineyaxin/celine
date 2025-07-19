import pandas as pd

# 读取两个Excel文件
df_main = pd.read_excel('/Users/chenyaxin/Desktop/不依赖个人信息.xlsx')  # 替换为实际文件名
df_secondary = pd.read_excel('/Users/chenyaxin/Desktop/fruad_privacy_serious.xlsx')  # 替换为实际文件名

merged_df = pd.merge(
    df_main, 
    df_secondary, 
    on='投诉编号', 
    how='left',  # 关键修改：使用左连接
    suffixes=('', '_附表')  # 自动区分重名列
)

# 保存合并结果
merged_df.to_excel('合并结果.xlsx', index=False)