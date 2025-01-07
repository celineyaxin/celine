import os
import re
# 设定输入和输出文件夹路径
input_dir = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/文本'
output_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/merged_output.txt'

merged_content = []

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

def prepare_text_for_tokenization(text):
    # 去除字符串头尾的空白字符
    text = text.strip()
    # 替换多个空格、换行符、制表符等为一个空格
    text = ' '.join(text.split())
    # 替换连续的换行符为一个换行符
    text = '\n'.join(text.splitlines())
    return text

for filename in os.listdir(input_dir):
    if filename.endswith('.txt'):
        file_path = os.path.join(input_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            remove_content = remove_starting_words(content,starting_words)
            processed_text = prepare_text_for_tokenization(remove_content)
            merged_content.append(processed_text)

final_content = '\n'.join(merged_content)
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    output_file.write(final_content)

print(f'All .txt files have been merged into {output_file_path}')