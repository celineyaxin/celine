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