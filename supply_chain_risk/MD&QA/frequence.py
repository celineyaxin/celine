##统计词频完善一下自用词和停用词库
import csv
from collections import Counter
import jieba
from tqdm import tqdm
import pandas as pd
import re

def load_stop_words_and_userdict(stop_words_file, userdict_file):
    with open(stop_words_file, 'r', encoding='utf-8') as file:
        stop_words = set(line.strip() for line in file)
    with open(userdict_file, 'r', encoding='utf-8') as file:
        userdict = {line.strip(): 1 for line in file}  # 假设自定义词典中的词频都为1
    return stop_words, userdict

def segment_and_remove_stopwords(text, stop_words):
    text_lower = text.lower()
    words = jieba.cut(text_lower)
    pattern = re.compile(r'\d+(\.\d+)?%?')
    filtered_words = [word for word in words if word not in stop_words and len(word) > 1 and not word.isdigit() and not pattern.search(word)]
    return filtered_words

def generate_word_frequency(text_list, stop_words, userdict,min_freq=5):
    jieba.load_userdict(userdict)
    all_words = []
    print("step in generate_word_frequency")
    for text in tqdm(text_list, desc='Processing Texts'):
        filtered_words = segment_and_remove_stopwords(text, stop_words)
        all_words.extend(filtered_words)
    print("segment and romove success")
    word_freq = Counter(all_words)
    print("counter success")
    filtered_freq = {word: count for word, count in word_freq.items() if count >= min_freq}
    return filtered_freq

# 将筛选后的词频写入CSV文件
def write_word_freq_to_csv(filtered_freq, output_csv_file):
    with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['word', 'frequency']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for word, freq in filtered_freq.items():
            writer.writerow({'word': word, 'frequency': freq})

def main():
    text_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/merged_output.txt'
    stop_words_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/stopwords.txt'
    output_csv_file = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/word_frequency.csv'
    userdict_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/selfdictionary.txt'

    stop_words, userdict = load_stop_words_and_userdict(stop_words_file_path, userdict_file_path)
    process_texts = []
    with open(text_file_path, 'r', encoding='utf-8',errors='ignore') as file:
        process_texts = file.readlines()
    process_texts = [text.strip() for text in process_texts]
    word_freq = generate_word_frequency(process_texts, stop_words, userdict)
    write_word_freq_to_csv(word_freq, output_csv_file)

if __name__ == "__main__":
    main()

