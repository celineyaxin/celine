import jieba
import pandas as pd

# 定义供应链和风险相关的关键词列表
supply_chain_keywords = {"供应链", "物流", "库存", "采购", "生产"}  # 根据需要添加更多关键词
risk_keywords = {"风险", "不确定性", "问题", "中断", "故障", "危机"}  # 根据需要添加更多风险关键词

def load_unique_words(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        words = {line.strip() for line in file}
    return words


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
text = "公司的核心竞争力是最短供应链，最低总成本，有一定的不确定性。成霖股份的核心竞争力是规模和成本，需要考虑物流的问题。海鸥的优势并没有体现出来，恰恰是人们认为生产“低档货”没有议价优势的成霖股份给人们交了一个满意的答券。"  # 示例文本
user_dict_path="./selfdictionary.txt"
stopwords_file_path = "./stopwords.txt"

user_dict = load_unique_words(user_dict_path)
stopwords = load_unique_words(stopwords_file_path)

# 计算风险指标
filtered_words=cut_text_with_custom_dict(text, user_dict_path, stopwords)
risk_indicator = calculate_supply_chain_risk(filtered_words, supply_chain_keywords, risk_keywords)

# 读取 Excel 文件
excel_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/原始数据/业绩说明会问答文本分析/业绩说明会问答文本分析_1.xlsx'
df = pd.read_excel(excel_file_path)

# 计算风险指数
df['Question_Risk_Index'] = df['Qcntet'].apply(calculate_supply_chain_risk)
df['Answer_Risk_Index'] = df['Acntet'].apply(calculate_supply_chain_risk)

columns_to_save = ['Scode', 'Year', 'Qnumbr', 'Qcntet','Acntet']
df_to_save = df[columns_to_save]

output_excel_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/output_AR.xlsx'
df_to_save.to_excel(output_excel_file_path, index=False)

print(f"供应链风险指数已经计算完成，并写入到 {output_excel_file_path}")
# print(f"供应链风险测度指标为: {risk_indicator}")