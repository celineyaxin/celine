import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# 定义文件路径
input_file = '/Users/chenyaxin/Desktop/信息规范/文本分类/合并类别数据_平衡后.xlsx'
test_file = '/Users/chenyaxin/Desktop/test.csv'
dev_file = '/Users/chenyaxin/Desktop/dev.csv'
train_file = '/Users/chenyaxin/Desktop/train.csv'

# 读取Excel文件
df = pd.read_excel(input_file)

# 选择需要的列 - 现在使用机制类别
df = df[['发起投诉内容', '机制类别']]

# 重命名列，使其更清晰
df = df.rename(columns={'发起投诉内容': 'text', '机制类别': 'label'})

# 对三个机制类别进行编码
label_encoder = LabelEncoder()
df['label_encoded'] = label_encoder.fit_transform(df['label'])

# 打印类别映射关系和数据集大小
print("机制类别编码映射:")
for i, category in enumerate(label_encoder.classes_):
    print(f"{category} -> {i}")

print(f"\n总数据量: {len(df)} 条")

# 使用分层抽样划分数据集
# 先划分训练集和临时集（测试+验证），训练集占80%
train_df, temp_df = train_test_split(
    df, 
    test_size=0.2, 
    random_state=42,
    stratify=df['label']  # 按机制类别分层
)

# 再从临时集中划分测试集和验证集，各占一半
test_df, dev_df = train_test_split(
    temp_df,
    test_size=0.5,  # 临时集的一半作为验证集
    random_state=42,
    stratify=temp_df['label']  # 按机制类别分层
)

# 打印数据集统计信息
print(f"\n数据集分布:")
print(f"训练集: {len(train_df)} 条 ({len(train_df)/len(df)*100:.1f}%)")
print(f"验证集: {len(dev_df)} 条 ({len(dev_df)/len(df)*100:.1f}%)")
print(f"测试集: {len(test_df)} 条 ({len(test_df)/len(df)*100:.1f}%)")

print(f"\n各机制类别分布:")
for dataset_name, dataset in [("训练集", train_df), ("验证集", dev_df), ("测试集", test_df)]:
    print(f"\n{dataset_name}:")
    label_counts = dataset['label'].value_counts().sort_index()
    for label in label_encoder.classes_:
        count = label_counts.get(label, 0)
        percentage = count / len(dataset) * 100
        print(f"  {label}: {count} 条 ({percentage:.1f}%)")

# 保存数据集（只保存文本和编码后的标签）
train_df[['text', 'label_encoded']].to_csv(train_file, index=False, header=False)
dev_df[['text', 'label_encoded']].to_csv(dev_file, index=False, header=False)
test_df[['text', 'label_encoded']].to_csv(test_file, index=False, header=False)

print(f"\n文件已保存:")
print(f"训练集: {train_file}")
print(f"验证集: {dev_file}")
print(f"测试集: {test_file}")

# 保存标签映射关系为txt文件（便于查看）
label_mapping_file = '/Users/chenyaxin/Desktop/mechanism_label_mapping.txt'
with open(label_mapping_file, 'w', encoding='utf-8') as f:
    f.write("机制类别标签编码映射表\n")
    f.write("======================\n")
    for i, category in enumerate(label_encoder.classes_):
        f.write(f"{i}: {category}\n")
    
    f.write(f"\n总计: {len(label_encoder.classes_)} 个机制类别\n")
    f.write(f"生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

print(f"\n机制类别标签映射已保存到: {label_mapping_file}")