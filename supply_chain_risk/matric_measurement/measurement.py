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

def calculate_supply_chain_risk(filtered_words, supply_chain_keywords, risk_keywords):
    supplychainrisk_score = 0 
    supply_chain_words_count = 0
    word_freq = Counter(filtered_words)
    total_words = len(filtered_words)
    word_frequency = {word: count / total_words for word, count in word_freq.items()}
    for i, word in enumerate(filtered_words):
        if word in supply_chain_keywords:
            supply_chain_words_count += 1
            supply_chain_freq = word_frequency[word]
            start = max(0, i-10)
            end = min(len(filtered_words), i+11)
            risk_count=0
            risk_count = sum(1 for w in filtered_words[start:end] if w in risk_keywords)
            risk_score = supply_chain_freq *risk_count
            # print(f"Word: {word}, Supply Chain Freq: {supply_chain_freq}, Risk Count: {risk_count}, Risk Score: {risk_score}")
            supplychainrisk_score += risk_score
    # 如果没有供应链关键词，则不计算风险指标
    if supply_chain_words_count == 0:
        return 0
    return supplychainrisk_score

def calculate_total_risk_word_frequency(filtered_words, risk_keywords):
    words = Counter(filtered_words)
    risk_word_freq = {word: words[word] for word in risk_keywords if word in words}
    total_risk_word_count = sum(risk_word_freq.values()) 
    total_words = len(filtered_words) 
    if total_words == 0:  # 避免除以零
        return 0
    Risk_score= total_risk_word_count / total_words  # 计算总频率
    # print(f"total_words: {total_words}, total_risk_word_count: {total_risk_word_count}, Risk Score: {Risk_score}")
    return Risk_score

def calculate_supply_chain_word_frequency(filtered_words, supply_chain_keywords):
    words = Counter(filtered_words)
    supply_chain_word_freq = {word: words[word] for word in supply_chain_keywords if word in words}
    total_supply_chain_word_count = sum(supply_chain_word_freq.values())
    total_words = len(filtered_words)
    if total_words == 0:  # 避免除以零
        return 0
    supply_chain_score = total_supply_chain_word_count / total_words  # 计算供应链词的总频率
    # print(f"total_words: {total_words}, total_supply_chain_word_count: {total_supply_chain_word_count}, supply_chain_score: {supply_chain_score}")
    return supply_chain_score

def add_risk_metrics_to_df(df, supply_chain_keywords, risk_keywords):
    df['Risk_score'] = df['分词后的文本'].apply(
        lambda text: calculate_total_risk_word_frequency(text.split(), risk_keywords)
    )
    df['supplychainrisk_score'] = df['分词后的文本'].apply(
        lambda text: calculate_supply_chain_risk(text.split(), supply_chain_keywords, risk_keywords)
    )
    df['supplychain_score'] = df['分词后的文本'].apply(
        lambda text: calculate_supply_chain_word_frequency(text.split(), supply_chain_keywords)
    )
    # df['filtered_words_string'] = df['分词后的文本'].apply(
    #     lambda text: ' '.join(text.split())  # 将分词结果连接为一个字符串
    # )
    # return df[['Scode', 'Year', 'filtered_words_string','supplychain_score', 'Risk_score',"supplychainrisk_score"]]
    return df[['Scode', 'Year', 'supplychain_score', 'Risk_score',"supplychainrisk_score"]]

user_dict_path="/Users/chenyaxin/Desktop/供应链风险指标测度/指标构造文件/selfdictionary.txt"
stopwords_file_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/指标构造文件/stopwords.txt"
supply_chain_file_path="/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/supplychain_words.txt"
risk_file_path="/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/risk_words.txt"

stopwords = load_unique_words(stopwords_file_path)
supply_chain_keywords = load_unique_words(supply_chain_file_path)
risk_keywords = load_unique_words(risk_file_path)
jieba.load_userdict(user_dict_path)


start_year = 2010
end_year = 2022

for year in range(start_year, end_year + 1):
    folder_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/groupqa.csv' 
    grouped_df=pd.read_csv(folder_path)
    grouped_df = grouped_df[grouped_df['Year'] == year].copy()
# grouped_df=pd.read_csv("/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/test.csv")
    merged_df = apply_cut_text(
    merged_df=grouped_df,
    text_column='Content',
    stopwords=stopwords
    )

    merged_df_with_risk_score = add_risk_metrics_to_df(
        df=merged_df,
        supply_chain_keywords=supply_chain_keywords,
        risk_keywords=risk_keywords
    )

    output_file_path =f'/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/final_version/Risk_frequency_{year}.csv'
    # output_file_path =f'/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/Risk_frequency_{year}.csv'
    merged_df_with_risk_score.to_csv(output_file_path, index=False)
