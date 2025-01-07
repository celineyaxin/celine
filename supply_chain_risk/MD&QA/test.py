import re

def remove_starting_words(text, starting_words):
    # 构建正则表达式模式，精确匹配列表中任一词语开头的部分
    pattern = re.compile(r'^({})'.format('|'.join(starting_words)), re.MULTILINE)
    # 删除匹配到的内容
    new_text = re.sub(pattern, '', text)
    return new_text

# 测试代码
starting_words = [
    '董事会报告', '董事局报告', '经营情况讨论与分析', '主要业务讨论与分析',
    '经营层讨论与分析', '管理层讨论与分析', '管理层分析与讨论',
    '董事会工作报告', '董事局工作报告'
]

file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/文本/000001_2011-12-31.txt'

with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

processed_text = remove_starting_words(content, starting_words)
print("Processed text:\n", processed_text)