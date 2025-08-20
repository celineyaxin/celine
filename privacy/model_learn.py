import pandas as pd
import matplotlib.pyplot as plt

def auto_sample_excel(file_path, content_col, id_col, target_samples=200, 
                     top_n=3, min_per_class=8, random_state=42):
    """
    从Excel自动抽样，样本多的类别多抽
    
    参数:
        file_path: Excel文件路径
        content_col: 投诉内容列名
        id_col: 编号列名
        target_samples: 目标样本数(约200)
        top_n: 自动选择前n个样本量多的类别多抽
        min_per_class: 每个类别最小样本数
        random_state: 随机种子
    
    返回:
        抽样后的DataFrame
    """
    # 读取数据
    data = pd.read_excel(file_path, usecols=[content_col, id_col])
    data[id_col] = data[id_col].astype(str)  # 统一编号格式
    
    # 分析原始分布
    id_counts = data[id_col].value_counts()
    print("原始数据分布:")
    print(id_counts.sort_index())
    
    # 自动确定重要类别(样本量最多的top_n个)
    important_ids = id_counts.nlargest(top_n).index.tolist()
    print(f"\n自动选择多抽样类别: {important_ids}")
    
    # 计算抽样数量
    n_classes = len(id_counts)
    base_samples = min_per_class
    remaining_samples = target_samples - base_samples * n_classes
    
    # 分配额外样本给重要类别
    samples_per_class = {id: base_samples for id in id_counts.index}
    if remaining_samples > 0:
        extra_per_important = remaining_samples // top_n
        for id in important_ids:
            samples_per_class[id] += extra_per_important
    
    # 执行抽样
    sampled_data = pd.DataFrame()
    for id, count in id_counts.items():
        n_samples = min(samples_per_class[id], count)
        sampled = data[data[id_col] == id].sample(
            n=n_samples, random_state=random_state, replace=False)
        sampled_data = pd.concat([sampled_data, sampled], ignore_index=True)
    
    # 结果分析
    print("\n抽样结果分布:")
    print(sampled_data[id_col].value_counts().sort_index())
    
    return sampled_data  # 添加这行返回抽样结果


# 使用示例
if __name__ == "__main__":
    sampled_data = auto_sample_excel(
        file_path="/Users/chenyaxin/Desktop/合并结果.xlsx",
        content_col="投诉内容",
        id_col="编号",
        target_samples=200,
        top_n=8,  # 自动选择样本量最多的8个类别多抽
        min_per_class=8,
        random_state=42
    )
    
    # 保存结果
    sampled_data.to_excel("/Users/chenyaxin/Desktop/auto_sampled_complaints.xlsx", index=False)
    print("\n抽样结果已保存到: auto_sampled_complaints.xlsx")