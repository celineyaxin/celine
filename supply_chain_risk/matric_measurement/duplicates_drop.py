import os

# 定义文件路径
folder_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/指标构造文件'  # 替换为您的文件夹路径
stopwords_file_path = os.path.join(folder_path, 'stopwords.txt')
def clean_words(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        words = set(line.strip() for line in file if line.strip())
    return list(words)

# 保存清洗后的词语到原文件
def save_cleaned_words(words, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        for word in words:
            file.write(word + '\n')

# 执行清洗和保存操作
cleaned_words = clean_words(stopwords_file_path)
save_cleaned_words(cleaned_words, stopwords_file_path)

print(f"清洗后的词语已保存至 {stopwords_file_path}")