##统计词频完善一下自用词和停用词库
import csv
from collections import Counter
import jieba
from tqdm import tqdm
import pandas as pd

def load_stop_words_and_userdict(stop_words_file, userdict_file):
    with open(stop_words_file, 'r', encoding='utf-8') as file:
        stop_words = set(line.strip() for line in file)
    with open(userdict_file, 'r', encoding='utf-8') as file:
        userdict = {line.strip(): 1 for line in file}  # 假设自定义词典中的词频都为1
    return stop_words, userdict

def segment_and_remove_stopwords(text, stop_words,userdict):
    text_lower = text.lower()
    words = jieba.cut(text_lower)
    filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
    return filtered_words

def generate_word_frequency(text_list, stop_words, userdict,min_freq=5):
    jieba.load_userdict(userdict)
    all_words = []
    print("step in generate_word_frequency")
    for text in tqdm(text_list, desc='Processing Texts'):
        filtered_words = segment_and_remove_stopwords(text, stop_words,userdict)
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
    # text_file_path = '/Users/chenyaxin/Desktop/websitdata/merge_data3/financial_complains.csv'
    text_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/code/merged_output.xlsx'
    stop_words_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/code/stopwords.txt'
    output_csv_file = '/Users/chenyaxin/Desktop/供应链风险指标测度/code/word_frequency.csv'
    userdict_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/code/selfdictionary.txt'

    stop_words, userdict = load_stop_words_and_userdict(stop_words_file_path, userdict_file_path)
    process_texts = []
    df = pd.read_excel(text_file_path)
    for index, row in df.iterrows():
        process_text1 = row['Qcntet']
        process_text2 = row['Acntet']
        combined_text = f"{process_text1} {process_text2}"
        process_texts.append(combined_text)
    word_freq = generate_word_frequency(process_texts, stop_words,userdict)
    write_word_freq_to_csv(word_freq, output_csv_file)
    # print_top_ten_words(word_freq)

if __name__ == "__main__":
    main()

