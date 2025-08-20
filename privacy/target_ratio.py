import pandas as pd
from sklearn.utils import resample

# 读取Excel文件
data = pd.read_excel('/Users/chenyaxin/Desktop/子分类_3.xlsx')  # 替换为你的Excel文件路径
print("原始数据：")
print(data.head())

# 检查每个类别的数量
print("\n原始数据中每个类别的数量：")
class_counts = data['子分类'].value_counts()
print(class_counts)

# 设置目标比例
target_ratio = 2.5  # 多数类是少数类的1.5倍

# 分离多数类和少数类
majority_classes = data[data['子分类'].isin(class_counts[class_counts > class_counts.min()].index)]
minority_classes = data[data['子分类'].isin(class_counts[class_counts == class_counts.min()].index)]

# 下采样多数类
downsampled_majority_classes = []
for class_label in majority_classes['子分类'].unique():
    class_data = majority_classes[majority_classes['子分类'] == class_label]
    target_sample_size = min(len(class_data), int(target_ratio * class_counts.min()))
    downsampled_class = resample(class_data, 
                                 replace=False, 
                                 n_samples=target_sample_size, 
                                 random_state=42)
    downsampled_majority_classes.append(downsampled_class)

# 合并下采样后的多数类和少数类
balanced_data = pd.concat(downsampled_majority_classes + [minority_classes])

# 检查均衡后的数据
print("\n均衡后的数据中每个类别的数量：")
print(balanced_data['子分类'].value_counts())

# 保存均衡后的数据
balanced_data.to_excel('/Users/chenyaxin/Desktop/balanced_data.xlsx', index=False)
print("\n均衡后的数据已保存到 balanced_data.xlsx")