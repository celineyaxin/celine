import os
import jieba
from collections import Counter
import re

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
    # 过滤掉数字和百分比表达式
    filtered_words = [word for word in filtered_words if not num_pattern.match(word)]
    return filtered_words

def view_cut_text_results(directory, stopwords):
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            filtered_words = cut_text_with_custom_dict(content, stopwords)
            print(f"File: {filename}")
            print(f"Sample of filtered words: {filtered_words[3000:5000]}")
            print("-" * 80)

# 加载停用词
stopwords_file_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/stopwords.txt"
user_dict_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/selfdictionary.txt"
jieba.load_userdict(user_dict_path)    
stopwords = load_unique_words(stopwords_file_path)

# 指定目录
directory = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/test'

# 查看分词结果
view_cut_text_results(directory, stopwords)