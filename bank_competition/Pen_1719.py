import pandas as pd

# 读取两个 Excel 文件
df1 = pd.read_excel('/Users/chenyaxin/Desktop/信息规范/data/2017-2018行政处罚分类结果_消费者.xlsx')
df2 = pd.read_excel('/Users/chenyaxin/Desktop/信息规范/data/2019行政处罚数据_分类结果.xlsx')

# 纵向合并（按行合并）
merged_df = pd.concat([df1, df2], axis=0, ignore_index=True)

# 保存合并后的文件
merged_df.to_excel('/Users/chenyaxin/Desktop/信息规范/data/2017-2019行政处罚数据合并.xlsx', index=False)

print(f"合并完成！")
print(f"第一个文件行数: {len(df1)}")
print(f"第二个文件行数: {len(df2)}")
print(f"合并后总行数: {len(merged_df)}")