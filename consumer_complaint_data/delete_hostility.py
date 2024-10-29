import pandas as pd
df1 = pd.read_csv('/Users/chenyaxin/Desktop/websitdata/filtered_data.csv')
df2 = pd.read_csv('/Users/chenyaxin/Desktop/websitdata/bert/results/贷款/combined_output.csv')
    
complaint_ids = df1['投诉编号'].drop_duplicates()

# 使用 isin 函数和投诉编号列表来筛选 df2
df2_filtered = df2[~df2['投诉编号'].isin(complaint_ids)]

# 将筛选后的 df2 保存为新的 CSV 文件
df2_filtered.to_csv('/Users/chenyaxin/Desktop/websitdata/bert/results/贷款/delete_hostility.csv', index=False)

print("df2 中的投诉编号已删除，新文件已保存。")