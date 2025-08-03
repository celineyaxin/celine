import pandas as pd
from sklearn.model_selection import train_test_split
import numpy as np

# 定义文件路径
input_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/fraud_classify/子分类_2.xlsx'
test_file = '/Users/chenyaxin/Desktop/test.csv'
dev_file = '/Users/chenyaxin/Desktop/dev.csv'
train_file = '/Users/chenyaxin/Desktop/train.csv'

# 读取Excel文件
df = pd.read_excel(input_file)
df = df[['投诉内容', '分类']]

# 1. 合并稀有类别（样本数少于3的类别）
min_samples = 3
class_counts = df['分类'].value_counts()
rare_classes = class_counts[class_counts < min_samples].index.tolist()

print(f"原始类别数量: {len(class_counts)}")
print(f"稀有类别(样本数<{min_samples}): {rare_classes}")

if rare_classes:
    print(f"\n合并以下稀有类别为'其他': {rare_classes}")
    df['adjusted_class'] = df['分类'].apply(
        lambda x: '其他' if x in rare_classes else str(x)
    )
else:
    df['adjusted_class'] = df['分类'].astype(str)

# 2. 确保调整后类别都有足够样本
adjusted_counts = df['adjusted_class'].value_counts()
print("\n调整后类别分布:")
print(adjusted_counts)

# 3. 分层抽样
# 第一次分层抽样：分出测试集 (500条)
train_dev_df, test_df = train_test_split(
    df, 
    test_size=1000, 
    stratify=df['adjusted_class'],
    random_state=42
)

# 第二次分层抽样：从剩余数据中分出开发集 (500条)
train_df, dev_df = train_test_split(
    train_dev_df, 
    test_size=1000, 
    stratify=train_dev_df['adjusted_class'],
    random_state=42
)

# 4. 确保每个子集都有所有调整后类别
def ensure_category_coverage(df_set, set_name, all_classes):
    # 检查是否有缺失的类别
    unique_classes = df_set['adjusted_class'].unique()
    missing_classes = set(all_classes) - set(unique_classes)
    
    if missing_classes:
        print(f"\n⚠️ {set_name}集中缺失以下类别: {list(missing_classes)}")
        print("正在补充缺失类别...")
        
        for cls in missing_classes:
            # 从完整数据集中获取该类别样本
            cls_samples = df[df['adjusted_class'] == cls]
            
            if len(cls_samples) == 0:
                print(f"  警告: 数据集没有'{cls}'类别的样本")
                continue
                
            # 添加缺失类别的样本
            new_sample = cls_samples.sample(1)
            df_set = pd.concat([df_set, new_sample])
            
            print(f"  已添加1条'{cls}'类别的样本")
    
    return df_set

# 获取所有调整后类别
all_adjusted_classes = df['adjusted_class'].unique()

# 确保每个子集都有所有类别
test_df = ensure_category_coverage(test_df, "测试", all_adjusted_classes)
dev_df = ensure_category_coverage(dev_df, "开发", all_adjusted_classes)
train_df = ensure_category_coverage(train_df, "训练", all_adjusted_classes)

# 5. 保存结果（使用调整后的类别）
test_df[['投诉内容', 'adjusted_class']].to_csv(test_file, index=False, header=False)
dev_df[['投诉内容', 'adjusted_class']].to_csv(dev_file, index=False, header=False)
train_df[['投诉内容', 'adjusted_class']].to_csv(train_file, index=False, header=False)

# 6. 详细检查各类别分布
def check_coverage(df_set, set_name):
    coverage = df_set['adjusted_class'].value_counts()
    print(f"\n{set_name}集类别覆盖情况:")
    print(f"总样本数: {len(df_set)}")
    print(f"覆盖类别数: {len(coverage)}")
    
    # 打印每个类别的样本数
    print("\n类别分布:")
    for cls, count in coverage.items():
        print(f"  {cls}: {count}条样本")
    
    # 检查是否有样本数少于3的类别
    low_count_classes = coverage[coverage < 3].index.tolist()
    if low_count_classes:
        print(f"\n⚠️ 样本数少于3的类别: {low_count_classes}")
        for cls in low_count_classes:
            cls_count = coverage[cls]
            print(f"  类别 '{cls}': {cls_count}条样本")
    else:
        print("\n所有类别至少有3条样本")

check_coverage(test_df, "测试")
check_coverage(dev_df, "开发")
check_coverage(train_df, "训练")

print("\n处理完成!")
print(f"测试集已写入: {test_file}")
print(f"开发集已写入: {dev_file}")
print(f"训练集已写入: {train_file}")