import pandas as pd

# 读取CSV文件
file_path = '/Users/chenyaxin/Desktop/privacy/data/fraud_predictions_20180101_0000_20231231_2359.csv'
df = pd.read_csv(file_path)
print(f"原始数据的行数: {len(df)}")
df['发布时间'] = df['发布时间'].str.strip()
df['发布时间'] = pd.to_datetime(df['发布时间'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
print(df['发布时间'])
df['年份'] = df['发布时间'].dt.year
# print(df['年份'])

filtered_by_prediction = df[df['prediction'] == 1]
print(f"筛选出 prediction 为 1 后的数据行数: {len(filtered_by_prediction)}")

filtered_by_year = filtered_by_prediction[(filtered_by_prediction['年份'] >= 2020) & (filtered_by_prediction['年份'] <= 2023)]
print(f"筛选出 2020-2023 年后的数据行数: {len(filtered_by_year)}")
sample_size = 5000
if len(filtered_by_year) >= sample_size:
    sampled_df = filtered_by_year.sample(n=sample_size, random_state=42)
else:
    sampled_df = filtered_by_year  # 如果数据不足5000条，就取全部

print(f"抽样后的数据行数: {len(sampled_df)}")

output_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/sampled_fraud.xlsx'
sampled_df.to_excel(output_file, index=False)

print(f"处理完成！结果已保存到 {output_file}")