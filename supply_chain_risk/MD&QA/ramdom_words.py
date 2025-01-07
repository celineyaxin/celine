import os
import pandas as pd
import jieba
from collections import Counter
import re
import shutil
import random

def load_unique_words(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        words = {line.strip() for line in file}
    return words

def cut_text_with_custom_dict(text, stopwords):
    if not isinstance(text, str):  # 检查 text 是否为字符串
        text = str(text)  # 如果不是，转换为字符串
    words = jieba.cut(text, cut_all=False)  
    filtered_words = [word.strip() for word in words if word not in stopwords and word.strip()]
    # num_pattern = re.compile(r'^\d+\.?\d*$|%\d+\.?\d*$')
    num_pattern = re.compile(r'^\d+(?:\.\d+)?%?$')
    filtered_words = [word for word in filtered_words if not num_pattern.match(word)]
    return filtered_words

def clear_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

def process_txt_files(directory, new_directory):
    user_dict_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/selfdictionary.txt"
    stopwords_file_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/stopwords.txt"

    stopwords = load_unique_words(stopwords_file_path)
    jieba.load_userdict(user_dict_path)

    # 确保新目录存在
    if not os.path.exists(new_directory):
        os.makedirs(new_directory)

    # 随机选择2000个txt文件并复制到新目录
    txt_files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    random.shuffle(txt_files)
    selected_files = txt_files[:5]
    for file in selected_files:
        shutil.copy(os.path.join(directory, file), new_directory)

    # 对新目录中的文件进行分词处理
    for filename in os.listdir(new_directory):
        if filename.endswith(".txt"):
            filepath = os.path.join(new_directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            filtered_words = cut_text_with_custom_dict(content, stopwords)
            print(f"File: {filename}")
            print(f"Sample of filtered words: {filtered_words[300:3000]}")
            print("-" * 80)

# 原始目录
directory = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/文本'
# 新目录
new_directory = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/test'

if os.path.exists(new_directory):
    clear_directory(new_directory)
else:
    os.makedirs(new_directory)
process_txt_files(directory, new_directory)