import pandas as pd

input_csv_path = '/Users/chenyaxin/Desktop/互联网旅游公约/treat.csv'
output_path = '/Users/chenyaxin/Desktop/互联网旅游公约/treatment_sample.csv'

# 读取CSV文件到DataFrame
treatment_df = pd.read_csv(input_csv_path)
sample_size = 3000  # 您可以根据需要调整这个数字

# 随机抽取样本
treatment_sample = treatment_df.sample(n=sample_size, random_state=42)
print(treatment_sample)
treatment_sample.to_csv(output_path, index=False)
print(f"抽取的样本已保存至 {output_path}")