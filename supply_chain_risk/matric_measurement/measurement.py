# 单独年份跑
import jieba
import pandas as pd
import os
import re
from tqdm import tqdm

def load_unique_words(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        words = {line.strip() for line in file}
    return words

def apply_cut_text(merged_df, text_column, user_dict_path, stopwords):
    def cut_and_filter(merged_df):
        return ' '.join(cut_text_with_custom_dict(merged_df, user_dict_path, stopwords))
    merged_df['分词后的文本'] = tqdm(merged_df[text_column].apply(cut_and_filter), desc='Cutting text', unit='text')
    return merged_df

def cut_text_with_custom_dict(text, user_dict_path, stopwords):
    jieba.load_userdict(user_dict_path)  # 加载自定义词典
    words = jieba.cut(text, cut_all=False)  # 使用精确模式分词
    filtered_words = [word for word in words if word not in stopwords]
    return filtered_words

# 计算供应链风险指标的函数
def calculate_supply_chain_risk(filtered_words, supply_chain_keywords, risk_keywords):
    total_risk_score = 0
    supply_chain_words_count = 0  
    
    total_words = len(filtered_words)
    word_freq = {} 
    for word in filtered_words:
        if word in word_freq:
            word_freq[word] += 1
        else:
            word_freq[word] = 1
  
    word_frequency = {word: count / total_words for word, count in word_freq.items()}
    for i, word in enumerate(filtered_words):
        if word in supply_chain_keywords:
            supply_chain_words_count += 1
            supply_chain_freq = word_frequency[word]
            risk_count = 0
            start = max(0, i-10)
            end = min(len(filtered_words), i+11)
            risk_count = sum(1 for w in filtered_words[start:end] if w in risk_keywords)
            risk_score = supply_chain_freq * risk_count
            # print(f"Word: {word}, Supply Chain Freq: {supply_chain_freq}, Risk Count: {risk_count}, Risk Score: {risk_score}")
            total_risk_score += risk_score

    # 如果没有供应链关键词，则不计算风险指标
    if supply_chain_words_count == 0:
        return 0
    return total_risk_score

def add_risk_score_to_df(df, supply_chain_keywords, risk_keywords):
    df['Total_Risk_Score'] = df['分词后的文本'].apply(
        lambda text: calculate_supply_chain_risk(text.split(), supply_chain_keywords, risk_keywords)
    )
    return df[['Scode', 'Year', 'Total_Risk_Score']]

# 读取文本数据
user_dict_path="/Users/chenyaxin/Desktop/供应链风险指标测度/指标构造文件/selfdictionary.txt"
stopwords_file_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/指标构造文件/stopwords.txt"
supply_chain_file_path="/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/supplychain_words.txt"
risk_file_path="/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/risk_words.txt"

user_dict = load_unique_words(user_dict_path)
stopwords = load_unique_words(stopwords_file_path)
supply_chain_keywords = load_unique_words(supply_chain_file_path)
risk_keywords = load_unique_words(risk_file_path)

folder_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/groupqa.csv' 
# grouped_df=pd.read_csv(folder_path, nrows=5)
grouped_df=pd.read_csv(folder_path)
grouped_df = grouped_df[grouped_df['Year'] == 2012].copy()

merged_df = apply_cut_text(
    merged_df=grouped_df,
    text_column='Content',
    user_dict_path=user_dict_path,
    stopwords=stopwords
)
merged_df_with_risk_score = add_risk_score_to_df(
    df=merged_df,
    supply_chain_keywords=supply_chain_keywords,
    risk_keywords=risk_keywords
)

output_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/Total_Risk_Score_2012.csv'
merged_df_with_risk_score.to_csv(output_file_path, index=False)


########用年份循环
import jieba
import pandas as pd
import os
import re
from tqdm import tqdm

def load_unique_words(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        words = {line.strip() for line in file}
    return words

def apply_cut_text(merged_df, text_column, user_dict_path, stopwords):
    def cut_and_filter(merged_df):
        return ' '.join(cut_text_with_custom_dict(merged_df, user_dict_path, stopwords))
    # merged_df['分词后的文本'] = merged_df[text_column].apply(cut_and_filter)
    # merged_df['分词后的文本'] = tqdm(merged_df[text_column].apply(cut_and_filter), desc='Cutting text', unit='text')
    merged_df.loc[:, '分词后的文本'] = merged_df[text_column].apply(cut_and_filter)
    return merged_df

def cut_text_with_custom_dict(text, user_dict_path, stopwords):
    jieba.load_userdict(user_dict_path)  # 加载自定义词典
    words = jieba.cut(text, cut_all=False)  # 使用精确模式分词
    filtered_words = [word for word in words if word not in stopwords]
    return filtered_words

# 计算供应链风险指标的函数
def calculate_supply_chain_risk(filtered_words, supply_chain_keywords, risk_keywords):
    total_risk_score = 0
    supply_chain_words_count = 0  
    
    total_words = len(filtered_words)
    word_freq = {} 
    for word in filtered_words:
        if word in word_freq:
            word_freq[word] += 1
        else:
            word_freq[word] = 1
  
    word_frequency = {word: count / total_words for word, count in word_freq.items()}
    for i, word in enumerate(filtered_words):
        if word in supply_chain_keywords:
            supply_chain_words_count += 1
            supply_chain_freq = word_frequency[word]
            risk_count = 0
            start = max(0, i-10)
            end = min(len(filtered_words), i+11)
            risk_count = sum(1 for w in filtered_words[start:end] if w in risk_keywords)
            risk_score = supply_chain_freq * risk_count
            # print(f"Word: {word}, Supply Chain Freq: {supply_chain_freq}, Risk Count: {risk_count}, Risk Score: {risk_score}")
            total_risk_score += risk_score

    # 如果没有供应链关键词，则不计算风险指标
    if supply_chain_words_count == 0:
        return 0
    return total_risk_score

def add_risk_score_to_df(df, supply_chain_keywords, risk_keywords):
    df.loc[:, 'Total_Risk_Score'] = df['分词后的文本'].apply(
        lambda text: calculate_supply_chain_risk(text.split(), supply_chain_keywords, risk_keywords)
    )
    return df[['Scode', 'Year', 'Total_Risk_Score']]

user_dict_path="/Users/chenyaxin/Desktop/供应链风险指标测度/指标构造文件/selfdictionary.txt"
stopwords_file_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/指标构造文件/stopwords.txt"
supply_chain_file_path="/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/supplychain_words.txt"
risk_file_path="/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/risk_words.txt"

user_dict = load_unique_words(user_dict_path)
stopwords = load_unique_words(stopwords_file_path)
supply_chain_keywords = load_unique_words(supply_chain_file_path)
risk_keywords = load_unique_words(risk_file_path)

folder_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/groupqa.csv' 
grouped_df=pd.read_csv(folder_path)

unique_years = grouped_df['Year'].unique()

for year in tqdm(unique_years, desc='Processing years'):
    year_df = grouped_df[grouped_df['Year'] == year]
    year_df = apply_cut_text(
        merged_df=year_df,
        text_column='Content',
        user_dict_path=user_dict_path,
        stopwords=stopwords
    )
    year_df = add_risk_score_to_df(
        df=year_df,
        supply_chain_keywords=supply_chain_keywords,
        risk_keywords=risk_keywords
    )
    output_file_path = f'/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/Total_Risk_Score_{year}.csv'
    year_df.to_csv(output_file_path, index=False)

print("Year-by-year processing completed.")

