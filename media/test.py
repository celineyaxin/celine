import os
import re
from collections import defaultdict
import pandas as pd
import random

# keywords = ["砍头息", "阴阳合同", "手续费","金融欺诈"]
keywords = ["利息", "利率","金融欺诈"]
loan_keyword = "贷款"
def search_keywords_in_files(directories, keywords, loan_keyword):
    pattern = re.compile(r'\b(' + '|'.join(keywords) + r')\b')
    loan_pattern = re.compile(r'\b' + re.escape(loan_keyword) + r'\b')
    file_count_by_date = defaultdict(int)  # 用于存储每个日期的文件计数
    for directory in directories:
        for filename in os.listdir(directory):
            if filename.endswith(".txt"):
                date_str = filename[:-4]
                year_month = date_str[:7]  # 格式为 "YYYY-MM"

                filepath = os.path.join(directory, filename)
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    matches = pattern.findall(content)
                    loan_matches = loan_pattern.findall(content)

                    if matches and loan_matches:
                        file_count_by_date[year_month] += 1  # 增加对应日期的计数
                        sentences = re.split(r'[。？！]+', content)
                        relevant_sentences = [sentence.strip() + '。' for sentence in sentences if any(keyword in sentence for keyword in keywords) or loan_keyword in sentence]
                        if relevant_sentences:
                            print(f"File: {filename}")
                            for _ in range(min(3, len(relevant_sentences))):  # 随机打印3个或更少的句子
                                print(random.choice(relevant_sentences))
                            print("-" * 80)
                    # print(f"File: {filename}")
                    # for match in matches:
                    #     sentences = re.split(r'[。？！]+', content)
                    #     for sentence in sentences:
                    #         if match in sentence:
                    #             print(sentence.strip() + '。')
                    # print("-" * 80)

    # 打印每年每个月的文件数量
    results = sorted(file_count_by_date.items())
    # for date, count in file_count_by_date.items():
    #     print(f"{date}: {count} files")
    # results = [(date, count) for date, count in file_count_by_date.items()]
    df = pd.DataFrame(results, columns=['Year-Month', 'File_Count'])
    csv_path = '/Users/chenyaxin/Desktop/媒体文本/file_counts.csv'
    df.to_csv(csv_path, index=False)
    print(f"Results have been written to {csv_path}")
# directory = '/Users/chenyaxin/Downloads/经济日报'
directories = [
    '/Users/chenyaxin/Desktop/媒体文本/经济日报',
    '/Users/chenyaxin/Desktop/媒体文本/人民日报',
    '/Users/chenyaxin/Desktop/媒体文本/南方周末'
]
search_keywords_in_files(directories, keywords, loan_keyword)