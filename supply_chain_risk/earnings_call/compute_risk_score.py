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
# def apply_cut_text(merged_df, text_column, stopwords):
    def cut_and_filter(merged_df):
        return ' '.join(cut_text_with_custom_dict(merged_df, stopwords))
    merged_df['分词后的文本'] = tqdm(merged_df[text_column].apply(cut_and_filter), desc='Cutting text', unit='text')
    return merged_df


def cut_text_with_custom_dict(text, stopwords):
    if not isinstance(text, str):  # 检查 text 是否为字符串
        text = str(text)  # 如果不是，转换为字符串
    # jieba.load_userdict(user_dict_path)  # 加载自定义词典
    words = jieba.cut(text, cut_all=False)  # 使用精确模式分词
    filtered_words = [word for word in words if word not in stopwords]
    return filtered_words

def calculate_total_risk_word_frequency(text, risk_keywords):
    words = Counter(text)
    risk_word_freq = {word: words[word] for word in risk_keywords if word in words}
    total_risk_word_count = sum(risk_word_freq.values()) 
    total_words = sum(words.values())
    if total_words == 0:  # 避免除以零
        return 0
    total_risk_word_frequency = total_risk_word_count / total_words  # 计算总频率
    return total_risk_word_frequency

def add_total_risk_word_frequency_to_df(df, risk_keywords):
    df['Total_Risk_Word_Frequency'] = df['分词后的文本'].apply(
        lambda text: calculate_total_risk_word_frequency(text.split(), risk_keywords)
    )
    return df[['Scode', 'Year', 'Total_Risk_Word_Frequency']]


user_dict_path="/Users/chenyaxin/Desktop/供应链风险指标测度/指标构造文件/selfdictionary.txt"
stopwords_file_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/指标构造文件/stopwords.txt"
# supply_chain_file_path="/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/supplychain_words.txt"
risk_file_path="/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/risk_words.txt"

stopwords = load_unique_words(stopwords_file_path)
# supply_chain_keywords = load_unique_words(supply_chain_file_path)
risk_keywords = load_unique_words(risk_file_path)
jieba.load_userdict(user_dict_path)

folder_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/groupqa.csv' 
grouped_df=pd.read_csv(folder_path)
grouped_df = grouped_df[grouped_df['Year'] == 2019].copy()

# grouped_df=pd.read_csv("/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/test.csv")
merged_df = apply_cut_text(
    merged_df=grouped_df,
    text_column='Content',
    stopwords=stopwords
)

merged_df_with_risk_score = add_total_risk_word_frequency_to_df(
    df=merged_df,
    risk_keywords=risk_keywords
)

output_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/Risk_frequency_2019.csv'
merged_df_with_risk_score.to_csv(output_file_path, index=False)
