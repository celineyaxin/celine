import os
import pandas as pd
import sys
# input_dir = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/A股年报TXT'
input_dir = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/test'

output_dir = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/outtest'

title=['董事会报告','董事局报告','经营情况讨论与分析','主要业务讨论与分析','经营层讨论与分析','管理层讨论与分析','管理层分析与讨论','董事会工作报告','董事局工作报告']
nexttitle=['监事会工作报告\n','监事会工作报告 \n','监事会报告 \n','重要事项 \n','公司治理 \n','监事会报告\n','重要事项\n','公司治理\n']

def extract_content(file_path, output_path):
    topic = None
    minindex1 = sys.maxsize
    result = '' 
    nexttopic = None 
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            for i in range(len(title)):
                pos = text.find(title[i])
                while pos != -1:
                    if text[pos + len(title[i]):pos + len(title[i]) + 1] not in ['“', '。', '分', '一', '中', '关', '之', '》', '"', '—', '”', '第',"."]:
                        if pos < minindex1:
                            minindex1 = pos
                            topic = title[i]
                    pos = text.find(title[i], pos + 1)

            if topic is None:
                print(f"No relevant topic found in {file_path}")
                return  
         
            splittext=text.split(topic)
            print(topic)
         
            for ind,j in enumerate(splittext[1:]):
                if j.startswith(('\n', ' ', '\t')):
                    result = ''.join(splittext[ind+1:])
                    break
            if not result:
                result = ''

            minindex2 = sys.maxsize
            for k in range(len(nexttitle)):
                    pos = result.find(nexttitle[k])
                    if pos != -1 and pos < minindex2:
                        minindex2 = pos
                        nexttopic = nexttitle[k]

            result = result[:minindex2] if nexttopic else result     
            with open(output_path,'w',encoding='utf-8') as w:
                w.write(result)
                print(f"Processed {file_path}, index {ind}")

    except Exception as e:
        print(f'Error processing file {file_path}: {e}')

for root, dirs, files in os.walk(input_dir):
    for file in files:
        if file.endswith('.txt'):
            file_path = os.path.join(root, file)
            output_path = os.path.join(output_dir, file)
            extract_content(file_path, output_path)

# 用正则表达式定位
import os
import glob
import re
from tqdm import tqdm

# 可能的章节标题
chapter_titles = [
    '董事会报告', '董事局报告', '经营情况讨论与分析', '主要业务讨论与分析',
    '业务回顾与展望', '年度经营报告', '总裁报告', '执行董事报告',
    '独立董事报告', '管理层讨论与分析','经营层讨论与分析','管理层分析与讨论',
    '董事会工作报告','董事局工作报告'
]

# 用于匹配章节标题的正则表达式，假设章节标题在正文中且可能有自己的段落
# pattern = re.compile(r'(\n[^\S\n]*\*+[^\S\n]*\n|\n[^\S\n]*\d+\.[^\S\n]*\n)?[^\S\n]*(?:{}):[^\S\n]*\n'.format('|'.join(chapter_titles)), re.MULTILINE)
pattern = re.compile(r'(?:\n[^\S\n]*\*+[^\S\n]*\n|\n[^\S\n]*\d+\.[^\S\n]*\n)?[^\S\n]*(?:{}):[^\S\n]*\n'.format('|'.join(chapter_titles)), re.MULTILINE)
# 读取文件
def read_annual_report(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# 提取董事会报告
def extract_board_report(content):
    matches = pattern.finditer(content)
    for match in matches:
        chapter_title = match.group(0)
        start = match.end()
        # 找到当前章节的结束位置，这里假设章节内容至少有300个字符，并且以空行结束
        end = content.find('\n\n', start + 300)
        if end == -1:
            end = len(content)
        yield chapter_title + content[start:end]

# 存储提取的内容
def save_extracted_content(content, file_name):
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(content)
              
def extract_content(input_file_path, output_file_path):
    content = read_annual_report(input_file_path)
    board_reports = extract_board_report(content)
    
    base_name = os.path.basename(input_file_path)
    output_base = os.path.splitext(base_name)[0]
    for i, report in enumerate(board_reports):
        output_file_name = f"{os.path.dirname(output_file_path)}/{output_base}_board_report_{i}.txt"
        save_extracted_content(report, output_file_name)
        print(f"Extracted: {output_file_name}")

def process_folder(input_dir, output_dir):
    # 遍历文件夹中的所有TXT文件
    for root, dirs, files in tqdm(os.walk(input_dir), desc='Processing files'):
        for file in files:
            if file.endswith('.txt'):
                input_file_path = os.path.join(root, file)
                output_file_path = os.path.join(output_dir, os.path.relpath(input_file_path, input_dir) + '.txt')
                extract_content(input_file_path, output_file_path)

# 指定文件夹路径
input_dir = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/test'
output_dir = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/outtest'

# 确保输出文件夹存在
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

process_folder(input_dir, output_dir)