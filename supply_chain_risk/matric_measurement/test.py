import jieba
import pandas as pd
import os
import re
from tqdm import tqdm
from collections import Counter

def load_unique_words(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        words = {line.strip() for line in file}
    return words

def apply_cut_text(merged_df, text_column, stopwords):
    def cut_and_filter(merged_df):
        return ' '.join(cut_text_with_custom_dict(merged_df, stopwords))
    merged_df['分词后的文本'] = tqdm(merged_df[text_column].apply(cut_and_filter), desc='Cutting text', unit='text')
    return merged_df


def cut_text_with_custom_dict(text, stopwords):
    if not isinstance(text, str):  # 检查 text 是否为字符串
        text = str(text)  # 如果不是，转换为字符串
    words = jieba.cut(text, cut_all=False)  
    filtered_words = [word for word in words if word not in stopwords]
    return filtered_words

def count_words(words_list):
    word_counts = Counter(words_list)
    return word_counts

user_dict_path="/Users/chenyaxin/Desktop/供应链风险指标测度/指标构造文件/selfdictionary.txt"
stopwords_file_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/指标构造文件/stopwords.txt"
supply_chain_file_path="/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/supplychain_words.txt"
risk_file_path="/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/risk_words.txt"

stopwords = load_unique_words(stopwords_file_path)
supply_chain_keywords = load_unique_words(supply_chain_file_path)
risk_keywords = load_unique_words(risk_file_path)
jieba.load_userdict(user_dict_path)

similar_words_df = pd.read_excel('/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/按照相似度排列.xlsx')
words_to_count = similar_words_df['similar_word'].tolist()

# 读取groupqa.csv文件
folder_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/groupqa.csv'
# folder_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/test.csv'
grouped_df = pd.read_csv(folder_path)

# 应用分词
merged_df = apply_cut_text(
    merged_df=grouped_df,
    text_column='Content',
    stopwords=stopwords
)

# 统计每个词的出现次数
all_words = [word for text in merged_df['分词后的文本'] for word in text.split()]
total_counts = count_words(all_words)

word_counts_dict = {word: total_counts[word] for word in similar_words_df['similar_word'] if word in total_counts}

# 将统计结果添加到similar_words_df中
similar_words_df['Count'] = similar_words_df['similar_word'].map(word_counts_dict)

output_file_path = f'/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/count.xlsx'
similar_words_df.to_excel(output_file_path, index=False)
