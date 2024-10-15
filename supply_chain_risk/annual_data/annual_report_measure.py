import os
import pandas as pd
import jieba
from collections import Counter
from tqdm import tqdm

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
            supplychainrisk_score += risk_score
    if supply_chain_words_count == 0:
        return 0
    return supplychainrisk_score

def calculate_total_risk_word_frequency(filtered_words, risk_keywords):
    words = Counter(filtered_words)
    risk_word_freq = {word: words[word] for word in risk_keywords if word in words}
    total_risk_word_count = sum(risk_word_freq.values()) 
    total_words = len(filtered_words) 
    if total_words == 0:  
        return 0
    Risk_score= total_risk_word_count / total_words  
    return Risk_score

def calculate_supply_chain_word_frequency(filtered_words, supply_chain_keywords):
    words = Counter(filtered_words)
    supply_chain_word_freq = {word: words[word] for word in supply_chain_keywords if word in words}
    total_supply_chain_word_count = sum(supply_chain_word_freq.values())
    total_words = len(filtered_words)
    if total_words == 0:  
        return 0
    supply_chain_score = total_supply_chain_word_count / total_words  
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
    return df[['Scode', 'Year', 'supplychain_score', 'Risk_score', "supplychainrisk_score"]]

def process_txt_files(directory):
    user_dict_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/selfdictionary.txt"
    stopwords_file_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/stopwords.txt"
    supply_chain_file_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/supplychain_words.txt"
    risk_file_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/risk_words.txt"

    stopwords = load_unique_words(stopwords_file_path)
    supply_chain_keywords = load_unique_words(supply_chain_file_path)
    risk_keywords = load_unique_words(risk_file_path)
    jieba.load_userdict(user_dict_path)

    results_df = pd.DataFrame(columns=['Stock_Code', 'Year', 'Supply_Chain_Score', 'Risk_Score', 'Supply_Chain_Risk_Score'])

    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            stock_code, date = filename.split('_')[0], filename.split('_')[1].split('.')[0]
            year = date.split('-')[0]
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()

            filtered_words = cut_text_with_custom_dict(content, stopwords)
            word_count = len(filtered_words)
            supply_chain_words_count = sum(1 for word in filtered_words if word in supply_chain_keywords)
            risk_words_count = sum(1 for word in filtered_words if word in risk_keywords)

            print(f"File: {filename}")
            print(f"Total words in text: {word_count}")
            print(f"Supply chain related words count: {supply_chain_words_count}")
            print(f"Risk related words count: {risk_words_count}")
            print(f"Sample of filtered words: {filtered_words[:50]}")

            supply_chain_score = calculate_supply_chain_word_frequency(filtered_words, supply_chain_keywords)
            risk_score = calculate_total_risk_word_frequency(filtered_words, risk_keywords)
            supply_chain_risk_score = calculate_supply_chain_risk(filtered_words, supply_chain_keywords, risk_keywords)
            
            new_row = pd.DataFrame({
                'Stock_Code': [stock_code],
                'Date': [date],
                'Year': [year],
                'Supply_Chain_Score': [supply_chain_score],
                'Risk_Score': [risk_score],
                'Supply_Chain_Risk_Score': [supply_chain_risk_score]
            })
            results_df = results_df.astype({
                'Stock_Code': 'str',
                'Year': 'int64',
                'Supply_Chain_Score': 'float64',
                'Risk_Score': 'float64',
                'Supply_Chain_Risk_Score': 'float64'
            })

            results_df = pd.concat([results_df, new_row], ignore_index=True)

    return results_df

# directory = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/文本'
directory = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/test'
results_df = process_txt_files(directory)

excel_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/supply_chain_risk_indicators.xlsx'
results_df.to_excel(excel_path, index=False)

print(f"Results have been written to {excel_path}")