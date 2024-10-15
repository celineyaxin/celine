##生成jason文件
import json
import jieba
import csv
import pandas as pd
from tqdm import tqdm

text_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/merged_output.txt'
stop_words_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/stopwords.txt'
userdict_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/selfdictionary.txt'  # 自定义词典文件路径

with open(stop_words_file_path, 'r', encoding='utf-8') as file:
    stop_words = set(line.strip() for line in file)
with open(userdict_file_path, 'r', encoding='utf-8') as file:
    userdict = {line.strip(): 1 for line in file}  # 假设自定义词典中的词频都为1
  
input_texts = []
process_texts = []
jieba.load_userdict(userdict)
with open(text_file_path, 'r', encoding='utf-8',errors='ignore') as file:
        process_texts = file.readlines()
process_texts = [text.strip() for text in process_texts]

for text in process_texts:
    complaint_text_lower = text.lower()
    words = jieba.cut(complaint_text_lower)
    filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
    input_texts.append(filtered_words)
           

import json # 将大列表存储到JSON文件 
with open('./input.json', 'w') as f: 
    json.dump(input_texts, f) # 从JSON文件读取大列表 
