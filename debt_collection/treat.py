import pandas as pd

# 读取CSV文件
df_predictions = pd.read_csv('/Users/chenyaxin/Desktop/privacy/data/fraud_predictions_20180101_0000_20231231_2359.csv')
df_predictions['发布时间'] = pd.to_datetime(df_predictions['发布时间'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
print(f"源文件的行数: {len(df_predictions)}")
df_predictions['年份'] = df_predictions['发布时间'].dt.year
df_filtered = df_predictions[(df_predictions['prediction'] == 1) & (df_predictions['年份'] >= 2020)]
print(f"欺诈的行数: {len(df_filtered)}")

# 读取编码文件
df_treat = pd.read_csv('/Users/chenyaxin/Desktop/privacy/treat.csv')
print(f"原始编码文件的行数: {len(df_treat)}")

df_treat_filtered = df_treat[df_treat['treat'] > 0]
df_merged = pd.merge(df_filtered, df_treat_filtered[['编码', 'treat']], on='编码', how='left')
print(f"输出的行数: {len(df_merged )}")
df_merged = df_merged[df_merged['treat'] > 0]
print(f"输出的行数: {len(df_merged )}")
df_result = df_merged.sort_values(by='treat', ascending=False)
print(f"输出的行数: {len(df_result)}")
# 保存结果到新的CSV文件
df_result.to_csv('/Users/chenyaxin/Desktop/privacy/fraud_treat.csv', index=False)

print("筛选完成！结果已保存到 filtered_fraud_bank.csv")

# 再看等于0的