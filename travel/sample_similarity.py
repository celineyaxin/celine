import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from tqdm import tqdm
import chardet 

np.random.seed(42)
vectorizer = TfidfVectorizer()

treatment_group_path = '/Users/chenyaxin/Desktop/互联网旅游公约/treatment_sample.csv'
treatment_df = pd.read_csv(treatment_group_path, low_memory=False)
treatment_df = treatment_df.dropna(subset=['发起投诉内容'])
treatment_vectors = vectorizer.fit_transform(treatment_df['发起投诉内容'])

csv_directory = '/Users/chenyaxin/Desktop/互联网旅游公约/原始数据处理'  # 请替换为实际的文件夹路径
# csv_directory = '/Users/chenyaxin/Desktop/互联网旅游公约/test'  # 请替换为实际的文件夹路径
total_files = len([name for name in os.listdir(csv_directory) if name.endswith(".csv") and not name.startswith('.')])
all_complaints = {}
complaint_counts = {} 
for csv_file in tqdm([name for name in os.listdir(csv_directory) if name.endswith(".csv") and not name.startswith('.')], total=total_files, desc='Processing files'):
    csv_path = os.path.join(csv_directory, csv_file)
    try:
        with open(csv_path, 'rb') as f:
            result = chardet.detect(f.read(10000))  # 读取前10000字节来猜测编码
            encoding = result['encoding']
        df = pd.read_csv(csv_path, encoding=encoding)  # 使用检测到的编码读取文件

# 增加了投诉对象投诉数量的统计
        for complaint_object in df['投诉对象'].unique():
            if complaint_object not in all_complaints:
                all_complaints[complaint_object] = []
                complaint_counts[complaint_object] = 0  # 初始化计数器
            all_complaints[complaint_object].extend(df[df['投诉对象'] == complaint_object]['发起投诉内容'].tolist())
            complaint_counts[complaint_object] += len(df[df['投诉对象'] == complaint_object]['发起投诉内容'])
    except Exception as e:
        print(f"读取文件 {csv_file} 时出错: {e}")
similarity_scores = {}
sample_size = 300

for complaint_object, complaints in all_complaints.items():
    num_complaints = min(len(complaints), sample_size)
    if num_complaints == 0:
        print(f"没有样本抽取自 {complaint_object}，跳过...")
        continue
    sampled_texts = [text for text in np.random.choice(complaints, size=num_complaints, replace=False) if pd.notna(text)]
    if len(sampled_texts) == 0:
        print(f"样本抽取失败，跳过 {complaint_object}...")
        continue
    object_vectors = vectorizer.transform(sampled_texts)  
    if object_vectors.shape[0] == 0:
        print(f"样本向量化失败，跳过 {complaint_object}...")
        continue
    sim_scores = cosine_similarity(treatment_vectors, object_vectors)
    mean_sim_score = np.mean(sim_scores.diagonal())
    similarity_scores[complaint_object] = mean_sim_score

combined_data = []
for obj in set(complaint_counts.keys()) | set(similarity_scores.keys()):
    count = complaint_counts.get(obj, 0)
    score = similarity_scores.get(obj, None)
    combined_data.append({'投诉对象': obj, '相似度均值': score, '投诉数目': count})

similarity_df = pd.DataFrame(combined_data)
sorted_similarity_df = similarity_df.sort_values(by='相似度均值', ascending=False)

# 保存排序结果
out_path = '/Users/chenyaxin/Desktop/互联网旅游公约/sample_similarity_count.xlsx'
sorted_similarity_df.to_excel(out_path, index=False)
print(f"排序结果已保存至 {out_path}")