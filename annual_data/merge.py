import os

# 设定输入和输出文件夹路径
input_dir = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/提取文本txt'
output_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/merged_output.txt'

merged_content = []

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
            processed_text = prepare_text_for_tokenization(content)
            merged_content.append(processed_text)

final_content = '\n'.join(merged_content)
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    output_file.write(final_content)

print(f'All .txt files have been merged into {output_file_path}')