import pandas as pd

# 定义三个 CSV 文件的路径
file1 = '/Users/chenyaxin/Desktop/debt_collection/bert/result/financial_predictions_20180101_0000_20201231_2359.csv'
file2 = '/Users/chenyaxin/Desktop/debt_collection/bert/result/financial_predictions_20210101_0000_20221231_2359.csv'
file3 = '/Users/chenyaxin/Desktop/debt_collection/bert/result/financial_predictions_20230101_0000_20231231_2359.csv'

# 读取三个 CSV 文件
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)
df3 = pd.read_csv(file3)

merged_df = pd.concat([df1, df2, df3], ignore_index=True)

# 统计 prediction 列取值为 1 的数量
count_prediction_1 = (merged_df['prediction'] == 1).sum()
print(f"prediction 列取值为 1 的数量: {count_prediction_1}")

# 统计投诉商家名称包含“银行”且 prediction 取值为 1 的数量
count_bank= (merged_df['投诉商家'].str.contains('银行', na=False)).sum()
print(f"投诉商家名称包含‘银行’的数量: {count_bank}")

count_bank_prediction_1 = (
    (merged_df['投诉商家'].str.contains('银行', na=False)) & (merged_df['prediction'] == 1)
).sum()
print(f"投诉商家名称包含‘银行’且 prediction 取值为 1 的数量: {count_bank_prediction_1}")