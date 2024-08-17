import json
import jieba
import csv
import pandas as pd
from tqdm import tqdm

text_file_path = './merged_output.xlsx'
stop_words_file_path = './stopwords.txt'
userdict_file_path = './selfdictionary.txt'  # 自定义词典文件路径

with open(stop_words_file_path, 'r', encoding='utf-8') as file:
    stop_words = set(line.strip() for line in file)
with open(userdict_file_path, 'r', encoding='utf-8') as file:
    userdict = {line.strip(): 1 for line in file}  # 假设自定义词典中的词频都为1
  
input_texts = []
process_texts = []
jieba.load_userdict(userdict)
df = pd.read_excel(text_file_path)
for index, row in df.iterrows():
    process_text1 = row['Qcntet']
    process_text2 = row['Acntet']
    combined_text = f"{process_text1} {process_text2}"
    process_texts.append(combined_text)

for text in process_texts:
    complaint_text_lower = text.lower()
    words = jieba.cut(complaint_text_lower)
    filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
    input_texts.append(filtered_words)
           

import json # 将大列表存储到JSON文件 
with open('./input.json', 'w') as f: 
    json.dump(input_texts, f) # 从JSON文件读取大列表 
