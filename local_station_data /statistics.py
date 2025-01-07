import pandas as pd

# 读取CSV文件
file_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/原始数据处理/updated_complaint_summary.csv'
df = pd.read_csv(file_path, low_memory=False)
df['地区'] = df['地区'].astype(str)
df['发布时间'] = pd.to_datetime(df['发布时间'], format='%Y年%m月%d日 %H:%M', errors='coerce')
df = df[(df['发布时间'].dt.year >= 2020) & (df['发布时间'].dt.year <= 2023)]
df['年份'] = df['发布时间'].dt.year
print(df.head())
province_complaint_count = df.groupby(['地区', '年份']).size().reset_index(name='投诉数量')

# 输出结果
output_path = '/Users/chenyaxin/Desktop/处理黑猫地方站/原始数据处理/complaints_by_province_and_year.csv'
province_complaint_count.to_csv(output_path, index=False)

print(f"统计结果已保存至 {output_path}")