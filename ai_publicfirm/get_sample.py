import pandas as pd

input_csv_path = '/Users/chenyaxin/Desktop/上市公司投诉数据探究/上市公司信息筛选/listed-complaints.csv'
output_path = '/Users/chenyaxin/Desktop/上市公司投诉数据探究/上市公司信息筛选/classify_sample.csv'

# 读取CSV文件到DataFrame
treatment_df = pd.read_csv(input_csv_path)
sample_size = 5000  # 您可以根据需要调整这个数字

# 随机抽取样本
treatment_sample = treatment_df.sample(n=sample_size, random_state=42)
treatment_sample = treatment_sample[['发布时间', '投诉编号_x', '投诉对象', '发起投诉内容', 'Stkcd']]
treatment_sample.rename(columns={'投诉编号_x': '投诉编号'}, inplace=True)
print(treatment_sample)
treatment_sample.to_csv(output_path, index=False)
print(f"抽取的样本已保存至 {output_path}")