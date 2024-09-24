import pandas as pd
word_path1='/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/supplychain_words.txt'
word_path2='/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/risk_words.txt'

with open(word_path1, 'r', encoding='utf-8') as file:
    wordlist1 = [line.strip() for line in file.readlines()]

with open(word_path2, 'r', encoding='utf-8') as file:
    wordlist2 = [line.strip() for line in file.readlines()]

combined_wordlist = wordlist1 + wordlist2
similar_words_df = pd.read_csv('/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/supplychainrisk.csv')

matched_results = pd.DataFrame(columns=['original_word', 'similar_word', 'similarity'])
unmatched_words = []
# 遍历合并后的词汇列表
for word in combined_wordlist:
    matched_data = similar_words_df[similar_words_df['similar_word'] == word]
    if not matched_data.empty:
        matched_results = pd.concat([matched_results, matched_data], ignore_index=True)
    else:
        unmatched_words.append(word)
print(unmatched_words)
# 保存匹配结果到新的CSV文件
output_matched_csv_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/matched_similarity.csv'
matched_results.to_csv(output_matched_csv_path, index=False, encoding='utf-8-sig')
print(f"The matched words and their similarity scores have been written to {output_matched_csv_path}")

combined_wordlist_set = set(combined_wordlist)

# 找出similar_words_df中存在，但combined_wordlist中没有的词汇
extra_words = []
for index, row in similar_words_df.iterrows():
    if row['similar_word'] not in combined_wordlist_set:
        extra_words.append(row['similar_word'])
print(extra_words)