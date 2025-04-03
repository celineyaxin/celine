import pandas as pd

input_csv_path = '/Users/chenyaxin/Desktop/催收/financial_final.csv'
output_path = '/Users/chenyaxin/Desktop/催收/classify_sample.csv'

# 读取CSV文件到DataFrame
df = pd.read_csv(input_csv_path)
sample_size = 5000  # 您可以根据需要调整这个数字
df['发布时间'] = pd.to_datetime(df['发布时间'], format='%Y年%m月%d日 %H:%M', errors='coerce')
df['年份'] = df['发布时间'].dt.year

sample_size_per_year = 1000
sample_size_2018_2019 = 1000

final_sample = pd.DataFrame()
for year in range(2018, 2024):
    if year in [2018, 2019]:
        year_sample_size = sample_size_2018_2019 // 2  # 2018和2019年各抽取500条
    else:
        year_sample_size = sample_size_per_year

    year_df = df[df['年份'] == year]
    year_sample = year_df.sample(n=year_sample_size, random_state=42)
    final_sample = pd.concat([final_sample, year_sample], ignore_index=True)
    print(f"年份 {year} 抽取的样本数量：{len(year_sample)}")
final_sample = final_sample[['发布时间', '投诉编号', '编码', '投诉商家', '投诉内容']]
# 保存样本到CSV文件
final_sample.to_csv(output_path, index=False)
print(f"抽取的样本已保存至 {output_path}")

unique_business_count = len(final_sample['投诉商家'].unique())
print(f"包含的不同投诉商家数量：{unique_business_count}")