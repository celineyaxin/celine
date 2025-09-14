import pandas as pd
from sklearn.model_selection import train_test_split
import numpy as np

input_file = '/Users/chenyaxin/Desktop/旅游分类.xlsx'
test_file = '/Users/chenyaxin/Desktop/test.csv'
dev_file = '/Users/chenyaxin/Desktop/dev.csv'
train_file = '/Users/chenyaxin/Desktop/train.csv'

# 读取Excel文件
df = pd.read_excel(input_file)
df = df[['投诉内容', '分类']]

unique_classes = df['分类'].unique()
if len(unique_classes) != 2:
    raise ValueError("数据集中类别数量不是2，无法进行二分类任务。")

train_dev_df, test_df = train_test_split(
    df, 
    test_size=500, 
    stratify=df['分类'],
    random_state=42
)

# 第二次分层抽样：从剩余数据中分出开发集 (500条)
train_df, dev_df = train_test_split(
    train_dev_df, 
    test_size=500, 
    stratify=train_dev_df['分类'],
    random_state=42
)

# 4. 确保每个子集都有所有调整后类别
def ensure_category_coverage(df_set, set_name, all_classes):
    # 检查是否有缺失的类别
    unique_classes = df_set['分类'].unique()
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


# 确保每个子集都有所有类别
test_df = ensure_category_coverage(test_df, "测试", unique_classes)
dev_df = ensure_category_coverage(dev_df, "开发", unique_classes)
train_df = ensure_category_coverage(train_df, "训练", unique_classes)

# 5. 保存结果（使用调整后的类别）
test_df[['投诉内容', '分类']].to_csv(test_file, index=False, header=False)
dev_df[['投诉内容', '分类']].to_csv(dev_file, index=False, header=False)
train_df[['投诉内容', '分类']].to_csv(train_file, index=False, header=False)

# 6. 详细检查各类别分布
def check_coverage(df_set, set_name):
    coverage = df_set['分类'].value_counts()
    print(f"\n{set_name}集类别覆盖情况:")
    print(f"总样本数: {len(df_set)}")
    print(f"覆盖类别数: {len(coverage)}")
    
    # 打印每个类别的样本数
    print("\n类别分布:")
    for cls, count in coverage.items():
        print(f"  {cls}: {count}条样本")
    

check_coverage(test_df, "测试")
check_coverage(dev_df, "开发")
check_coverage(train_df, "训练")

print("\n处理完成!")
print(f"测试集已写入: {test_file}")
print(f"开发集已写入: {dev_file}")
print(f"训练集已写入: {train_file}")