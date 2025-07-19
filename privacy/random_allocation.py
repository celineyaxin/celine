import pandas as pd

# 定义文件路径
input_file = '/Users/chenyaxin/Desktop/fruad_privacy_serious.xlsx'  # 替换为你的 Excel 文件路径
test_file = '/Users/chenyaxin/Desktop/test.csv'  # 输出的 CSV 文件路径
dev_file = '/Users/chenyaxin/Desktop/dev.csv'  # 输出的 CSV 文件路径
train_file = '/Users/chenyaxin/Desktop/train.csv'  # 输出的 CSV 文件路径

# 读取 Excel 文件
df = pd.read_excel(input_file)

df = df[['投诉内容', '是否隐私依赖']]

df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# 抽取 500 条数据生成 test 文件
test_df = df.iloc[:500]
test_df.to_csv(test_file, index=False, header=False)

# 剩余数据中再抽取 500 条数据生成 dev 文件
dev_df = df.iloc[500:1000]
dev_df.to_csv(dev_file, index=False, header=False)

# 剩下的部分生成 train 文件
train_df = df.iloc[1000:]
train_df.to_csv(train_file, index=False, header=False)

print(f"已抽取 500 条数据并写入 {test_file}")
print(f"已抽取 500 条数据并写入 {dev_file}")
print(f"剩余数据已写入 {train_file}")