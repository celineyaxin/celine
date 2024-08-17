import jieba
import pandas as pd
import os
# 定义供应链和风险相关的关键词列表

def load_unique_words(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        words = {line.strip() for line in file}
    return words

def merge_excel_files(folder_path, file1, file2,columns_to_keep):
    file1_path = os.path.join(folder_path, file1)
    df1 = pd.read_excel(file1_path)
    file2_path = os.path.join(folder_path, file2)
    df2 = pd.read_excel(file2_path)

    merged_df = pd.concat([df1, df2], ignore_index=True)
    merged_df = merged_df[columns_to_keep]
    return merged_df

def group_and_merge_texts(merged_df, group_columns, text_column, output_column_name):
    grouped = merged_df.groupby(group_columns)
    merged_df[output_column_name] = grouped.apply(merge_texts_by_year, text_column=text_column)
    return merged_df

def merge_texts_by_year(group, text_column):
    full_text = ' '.join(group[text_column])
    words = cut_text_with_custom_dict(full_text, user_dict_path, stopwords)
    return ' '.join(words)

def cut_text_with_custom_dict(text, user_dict_path, stopwords):
    jieba.load_userdict(user_dict_path)  # 加载自定义词典
    words = jieba.cut(text, cut_all=False)  # 使用精确模式分词
    # 过滤掉停用词
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
    print( word_frequency)
    for i, word in enumerate(filtered_words):
        if word in supply_chain_keywords:
            print(word)
            supply_chain_words_count += 1
            supply_chain_freq = word_frequency[word]
            risk_count = 0
            start = max(0, i-10)
            end = min(len(filtered_words), i+11)
            risk_count = sum(1 for w in filtered_words[start:end] if w in risk_keywords)
            print(risk_count)
            risk_score = supply_chain_freq * risk_count
            total_risk_score += risk_score

    # 如果没有供应链关键词，则不计算风险指标
    if supply_chain_words_count == 0:
        return 0
    return total_risk_score

# 读取文本数据
user_dict_path="/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/selfdictionary.txt"
stopwords_file_path = "/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/stopwords.txt"
supply_chain_file_path="/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/supplychain_words.txt"
risk_file_path="/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/risk_words.txt"

user_dict = load_unique_words(user_dict_path)
stopwords = load_unique_words(stopwords_file_path)
supply_chain_keywords = load_unique_words(supply_chain_file_path)
risk_keywords = load_unique_words(risk_file_path)


merged_texts['Risk_Indicator'] = merged_texts.apply(lambda row: calculate_supply_chain_risk(row, supply_chain_risk_keywords))
output_file_path = 'supply_chain_risk_indicators.csv'
merged_texts.to_csv(output_file_path, index=False)

print(f"供应链风险指标已经计算完成，并保存到 {output_file_path}")

# 读取 Excel 文件
excel_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/原始数据/业绩说明会问答文本分析/业绩说明会问答文本分析_1.xlsx'
df = pd.read_excel(excel_file_path)



# 示例使用
folder_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/原始数据/业绩说明会问答文本分析'  # 替换为你的文件夹路径
file1 = '业绩说明会问答文本分析_1.xlsx'  # 替换为第一个Excel文件的名称
file2 = '业绩说明会问答文本分析_2.xlsx'  # 替换为第二个Excel文件的名称
columns_to_keep = ['Scode', 'Year', 'Qnumbr', 'Qcntet','Acntet']
merged_df=merge_excel_files(folder_path, file1, file2, columns_to_keep)
merged_df['合并后的问答内容'] = merged_df['Qcntet'] + ' ' + merged_df['Acntet']
grouped_df = group_and_merge_texts(
    merged_df=merged_df,
    group_columns=['Scode', 'Year'],
    text_column='合并后的问答内容',  # 使用新创建的列名
    output_column_name='Content'
)
filtered_words=cut_text_with_custom_dict(merged_df, user_dict_path, stopwords)