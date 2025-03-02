import requests
import pandas as pd
import time
import os
from tqdm import tqdm
from bs4 import BeautifulSoup
import json
from datetime import datetime
import pdfplumber
import re
from dateutil import parser
import csv
import html
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import datetime
import pytz
import tabula
import utils

def length_without_parentheses(s):
    # 定义括号模式
    patterns = [
        r'\([^)]*\)',
        r'（[^）]*）'
    ]
    
    # 使用正则表达式替换括号及其内容为空字符串
    new_s = s
    for pattern in patterns:
        new_s = re.sub(pattern, '', new_s)
    
    # 计算替换后字符串的长度
    length = len(new_s)
    
    return length

def remove_n_nones(lst, n):
    # 统计None的数量
    none_count = lst.count(None)

    if n == 0 :
        return lst
    
    # 如果None的数量少于n，直接返回原列表
    if none_count < n:
        return lst
    
    # 找到所有None的位置
    none_indices = [i for i, x in enumerate(lst) if x is None]
    
    # 从后往前找到最后n个None的位置
    none_indices_to_remove = none_indices[-n:]
    
    # 从后往前删除这些None值，以避免索引变化问题
    for index in sorted(none_indices_to_remove, reverse=True):
        del lst[index]
    
    return lst

def remove_n_blanks(lst, n):
    # 统计blank的数量
    blank_count = lst.count('')
    
    if n == 0 :
        return lst
    # 如果blank的数量少于n，直接返回原列表
    if blank_count < n:
        return lst
    
    # 找到所有blank的位置
    blank_indices = [i for i, x in enumerate(lst) if x == '']
    
    # 从后往前找到最后n个blank的位置
    blank_indices_to_remove = blank_indices[-n:]
    
    # 从后往前删除这些blank值，以避免索引变化问题
    for index in sorted(blank_indices_to_remove, reverse=True):
        del lst[index]
    
    return lst


def is_all_digits_or_float(s):
    return re.match(r'^\d+(\.\d+)?$', s) is not None

class Clause:
    def __init__(self):
        # 创建结果目录
        self.results_dir = 'results'
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
        self.head_keyword = ["序号", "条款"]
        self.original_keyword = ["原内容","原章程","原条款","原规定","原规则","原规章","原规范","原第", "原议事", "现条款", "修订前", "原《公司章程》", "原表述", "原文","变更前","修改前", \
         "现有章程","原制度","原公司章程", "原条文", "原“第", "原：“第", "现章程", "现行《公司章程》", "现行条款", "现有条文", "先行章程", "现行公司章程", "现行章程"]
        self.modified_keyword = ["修改后","修订后","修订为","现修订","修改为","修订为", "新增", "变更后", "变更为", "修订条款", "修订规定", "修订规则", "修订规章", "修订规范", "修订第", \
            "增加第", "改为：", "更为：", "更改为", "删除", "改为第", "改为“","增加第", "新增第", "新增一","新增条款", "顺延为", "增加“", "顺延：","顺延，", "增加一", "增加二", "增加三", \
            "增加四", "增加五", "增加六", "增加七", "增加八", "增加九", "增加十", "增加了", "新条款", "修改内容", "修改作为", "拟修订", "修订建议", "修订内容","建议修改内容", "次会议修订", "增加如下", \
            "条款内容", "新增以下", "增加条目","如下修改：", "修订稿"]
        self.taboo_keyword = ["审议机构", "年", "是否提交股东大会", "持股比例"]
        self.append_keyword = ["增加第", "新增第", "新增一","新增条款","增加“", "增加一", "增加二", "增加三", "增加四", "增加五", "增加六", "增加七", "增加八", "增加九", "增加十", "增加了", \
             "顺延为", "增加如下", "新增以下", "增加条目"]
        self.break_page_keyword = ["附：《公司章程","（修订稿）","《公司章程》全文如下", "《公司章程》（草案）全文","股东大会议事规则"]
        self.lenMax = 15
        # 添加内容分类关键词
        self.category_keywords = {
            '公司基本信息变更': [
                '注册资本', '经营范围', '经营宗旨', '公司名称',
                '公司住所', '法人代表', '营业执照', '办公地址'
            ],
            '涉及中小投资者保护的相关条例': [
                '中小投资者', '表决权', '投票权', '利润分配',
                '网络投票', '累积投票', '征集投票', '独立董事',
                '提案权', '股东权益保护', '小股东'
            ],
            '反收购条款': [
                '收购', '要约收购', '恶意收购', '反收购',
                '全仓牌', '董事提名权', '监事提名', '高管资格',
                '投票比例限制', '职工董事', '决议方法', '表决权限制'
            ],
            '基于法规的公司内部权力配置条款': [
                '股东大会', '董事会', '监事会', '总经理',
                '权力', '职权', '权限', '议事规则'
            ],
            '自主安排的管理层权力配置条款': [
                '董事会', '监事会', '高管', '总经理',
                '管理层', '决策权', '任免权', '薪酬'
            ]
        }

    def stop_process(self, text1, text2):
        return ((length_without_parentheses(text1) < self.lenMax) and (length_without_parentheses(text2) < self.lenMax) and \
        (any(keyword in text1 for keyword in self.taboo_keyword) or any(keyword in text2 for keyword in self.taboo_keyword))) \
        or (is_all_digits_or_float(text1) or is_all_digits_or_float(text2))

    def classify_article_content(self, content):
        """对章程条款内容进行分类"""
        if not content:
            return '其他'

        # 对每个分类进行关键词匹配
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in content:
                    return category
        return '其他'

    def extract_article_changes(self, text, df, pdfID):
        """提取章程修改内容"""

        # 分割文本为行
        lines = text.split('\n')
        current_original = ""
        current_modified = ""
        enable_original = False
        enable_modified = False
        not_append = True
        terms = []

        for i, line in enumerate(lines):
            if line is not None:
                if (len(line) < self.lenMax) and (any(keyword in line for keyword in self.break_page_keyword)):
                    break
            if any(keyword in line for keyword in self.original_keyword):
                not_append = True
                enable_original = True
                enable_modified = False
            if any(keyword in line for keyword in self.append_keyword):
                not_append = False
            if any(keyword in line for keyword in self.modified_keyword):
                enable_original = False
                enable_modified = True
                # import pdb
                # pdb.set_trace()
                # 如果有未处理的条款，先保存
                if (current_original != "" and current_modified == "") or (len(current_modified) >= self.lenMax) :
                    # 对内容进行分类
                    category = self.classify_article_content(current_modified or current_original)
                    new_row = {
                        'pdfID': pdfID,
                        'original_content': current_original,
                        'modified_content': current_modified,
                        'category': category
                    }
                    # 将字典转换为 DataFrame
                    new_row_df = pd.DataFrame([new_row])
                    df = pd.concat([df, new_row_df], ignore_index=True)
                    # 重置当前条款
                    if current_original != "":
                        current_original = ""
                    if current_modified != "":
                        current_modified = ""
                current_modified += line
                continue
            # 检查是否是条款行
            # article_match = re.search(r'(第[一二三四五六七八九十百千]+条\s*)(?=[\u4e00-\u9fff]{2,})', line)
            article_match = re.search(r'(第[一二三四五六七八九十百千]+条\s*).{0,100}[\u4e00-\u9fff].{0,100}[\u4e00-\u9fff]', line)
            if article_match:
                term = article_match.group(1)
                if not_append and term not in terms:
                    not_append = True
                    terms.append(term)
                    enable_original = True
                    enable_modified = False
                elif term in terms:
                    not_append = True
                    enable_original = False
                    enable_modified = True
                    terms.remove(term)
                if any(keyword in line for keyword in self.original_keyword) :
                    enable_original = True
                    enable_modified = False
                if any(keyword in line for keyword in self.modified_keyword) :
                    enable_original = False
                    enable_modified = True
                
                # 如果有未处理的条款，先保存
                if (current_original != "" and current_modified == "") or (len(current_modified) >= self.lenMax) :
                    # 对内容进行分类
                    category = self.classify_article_content(current_modified or current_original)
                    new_row = {
                        'pdfID': pdfID,
                        'original_content': current_original,
                        'modified_content': current_modified,
                        'category': category
                    }
                    # 将字典转换为 DataFrame
                    # import pdb
                    # pdb.set_trace()
                    new_row_df = pd.DataFrame([new_row])
                    df = pd.concat([df, new_row_df], ignore_index=True)
                    # 重置当前条款
                    if current_original != "":
                        current_original = ""
                    if current_modified != "":
                        current_modified = ""

                # 判断是原始内容还是修改内容
                if enable_modified:
                    current_modified += line
                elif enable_original:
                    current_original += line  
            else:
                # 继续累积当前条款的内容
                if enable_original:
                    current_original += line
                elif enable_modified:
                    current_modified += line

        # 处理最后一个条款
        if current_original != "" or current_modified != "":
            category = self.classify_article_content(current_modified or current_original)
            new_row = {
                        'pdfID': pdfID,
                        'original_content': current_original,
                        'modified_content': current_modified,
                        'category': category
                    }
            # 将字典转换为 DataFrame
            new_row_df = pd.DataFrame([new_row])
            df = pd.concat([df, new_row_df], ignore_index=True)

        return df

    def extract_pdf_table_info(self, pdf_path, pdfID, clause_df):
        current_original = None
        current_modified = None
        enable_write = False
        enable_case1 = False
        enable_case2 = False
        original_index = 0
        modified_index = 0
        general_case = False
        finded_head = False
        table_original = "123"
        table_modified = "456"
        len_none = 0
        len_blank = 0
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                tables = [item for sublist in tables for item in sublist]
                if tables:
                    for table in tables:
                        # import pdb
                        # pdb.set_trace()
                        if table is None:
                            continue
                        if all(x is None or x == "" for x in table):
                            continue
                        # if len(table) > 5:
                        #     table = [item for item in table if item is not None and item != ""]
                        
                        if not finded_head and not general_case:
                            len_none = table.count(None)
                            len_blank = table.count('')
                            remove_n_nones(table, len_none)
                            remove_n_blanks(table, len_blank)
                            if len_blank == 0 and len_none != 0:
                                len_blank = len_none
                            elif len_none == 0 and len_blank != 0:
                                len_none = len_blank
                            for index, item in enumerate(table):    
                                for keyword in self.original_keyword:
                                    if item is not None:
                                        if length_without_parentheses(item) < self.lenMax and keyword in item:
                                            table_original = table
                                            original_index = index
                                for keyword in self.modified_keyword:
                                    if item is not None :
                                        if length_without_parentheses(item) < self.lenMax and keyword in item:
                                            table_modified = table
                                            modified_index = index
                            if not finded_head and table_original is table_modified:
                                finded_head = True
                                enable_write = True
                                general_case = True
                                continue
                        if general_case and finded_head:
                            try:
                                remove_n_nones(table, len_none)
                                remove_n_blanks(table, len_blank)
                                if table[original_index] is None or table[modified_index] is None:
                                    continue
                                current_original = table[original_index]
                                current_modified = table[modified_index]
                            except Exception as e:
                                print(f"pdfID is {pdfID} 发生异常：{e}")
                                continue
                            if (current_original is not None) and (current_modified is not None) :
                                    if self.stop_process(current_original, current_modified):
                                        enable_write = False
                                        continue

                        if len(table) == 1:
                            if not finded_head and table[0] is not None :
                                if length_without_parentheses(table[0]) < self.lenMax and any(keyword in table[0] for keyword in self.modified_keyword):
                                    finded_head = True
                                    enable_write = True
                                    continue
                            if not finded_head and enable_write and not enable_case1 and not general_case:
                                current_original = None
                                current_modified = table[0]
                            if current_modified is not None :
                                if self.stop_process(current_modified, current_modified):
                                    enable_write = False
                                    continue
                        if len(table) == 2:
                            if not finded_head and table[0] is not None and table[1] is not None :
                                if length_without_parentheses(table[0]) < self.lenMax and any(keyword in table[0] for keyword in self.original_keyword) and length_without_parentheses(table[1]) < self.lenMax and any(keyword in table[1] for keyword in self.modified_keyword):
                                    finded_head = True
                                    enable_case1 = False
                                    enable_write = True
                                    continue
                            if not finded_head and table[0] is not None and table[1] is not None :
                                if length_without_parentheses(table[0]) < self.lenMax and any(keyword in table[0] for keyword in self.head_keyword) and length_without_parentheses(table[1]) < self.lenMax and any(keyword in table[1] for keyword in self.modified_keyword):
                                    finded_head = True
                                    enable_case1 = True
                                    enable_write = True
                                    continue
                            if enable_write and not enable_case1 and not general_case:
                                current_original = table[0]
                                current_modified = table[1]
                            if enable_write and enable_case1 and not general_case:
                                current_original = ''
                                current_modified = table[1]
                            if (current_original is not None) and (current_modified is not None) :
                                if self.stop_process(current_original, current_modified):
                                    enable_write = False
                                    continue
                        if len(table) == 3:
                            if not finded_head and table[1] is not None and table[2] is not None :
                                if length_without_parentheses(table[1]) < self.lenMax and any(keyword in table[1] for keyword in self.original_keyword) \
                                and length_without_parentheses(table[2]) < self.lenMax and any(keyword in table[2] for keyword in self.modified_keyword):
                                    enable_case1 = True
                                    enable_case2 = False
                                    finded_head = True
                                    enable_write = True
                                    continue
                            if not finded_head and table[0] is not None and table[1] is not None :
                                if length_without_parentheses(table[0]) < self.lenMax and any(keyword in table[0] for keyword in self.original_keyword) \
                                and length_without_parentheses(table[1]) < self.lenMax and any(keyword in table[1] for keyword in self.modified_keyword):
                                    enable_case1 = False
                                    enable_case2 = True
                                    finded_head = True
                                    enable_write = True
                                    continue
                            if not finded_head and table[1] is not None :
                                if length_without_parentheses(table[1]) < self.lenMax and any(keyword in table[1] for keyword in self.modified_keyword) :
                                    enable_case1 = False
                                    enable_case2 = False
                                    finded_head = True
                                    enable_write = True
                                    continue
                            if enable_write and enable_case1 and not enable_case2 and not general_case:
                                current_original = table[1]
                                current_modified = table[2]
                            if enable_write and not enable_case1 and enable_case2 and not general_case:
                                current_original = table[0]
                                current_modified = table[1]
                            if enable_write and not enable_case1 and not enable_case2 and not general_case:
                                current_original = ''
                                current_modified = table[1]
                            if (current_original is not None) and (current_modified is not None) :
                                if self.stop_process(current_original, current_modified):
                                    enable_write = False
                                    continue
                        if enable_write:
                            if len(table) == 5:
                                current_original = (table[1] or '') + (table[2] or '')
                                current_modified = (table[3] or '') + (table[4] or '')
                            if (current_original == '' or None) and (current_modified == '' or None):
                                continue
                            if current_original is None or current_modified is None:
                                continue
                            if current_modified != None:
                                if length_without_parentheses(current_modified) < self.lenMax and any(keyword in current_modified for keyword in self.modified_keyword):
                                    continue
                                if length_without_parentheses(current_modified) < self.lenMax and length_without_parentheses(current_modified) > 0:
                                    continue
                            # 对内容进行分类
                            category = self.classify_article_content(current_modified or current_original)
                            new_row = {
                                'pdfID': pdfID,
                                'original_content': current_original,
                                'modified_content': current_modified,
                                'category': category
                            }
                            # 将字典转换为 DataFrame
                            new_row_df = pd.DataFrame([new_row])
                            clause_df = pd.concat([clause_df, new_row_df], ignore_index=True)

        if (not enable_write) and (current_original is None and current_modified is None):
            with pdfplumber.open(pdf_path) as pdf:
                # 读取所有页面
                text = ''
                for page in pdf.pages:
                    text += page.extract_text()

                # 提取基本信息
                clause_df = self.extract_article_changes(text, clause_df, pdfID)

        return clause_df

    def process(self, input_name, output_name):
        # 读取输入的Excel文件
        input_df = pd.read_excel(input_name)
        
        # 创建一个新的DataFrame来存储扩展后的数据
        clause_df = pd.DataFrame(columns=['pdfID', 'original_content', 'modified_content', 'category'])
        
        # 使用tqdm显示进度条
        for idx, row in tqdm(input_df.iterrows(), total=input_df.shape[0]):
            pdf_path = row['filenames']
            pdfID = row['pdfID']
            if not utils.contains_revision(pdf_path):
                print(f"skip this file: {pdf_path}")
                continue
            
            try:                  
                clause_df = self.extract_pdf_table_info(pdf_path,  pdfID, clause_df)
                    
            except Exception as e:
                # import pdb
                # pdb.set_trace()
                print(f"处理PDF出错: {e}")
                continue
        # 每50个数据保存一次并清空clause_df
            if (idx + 1) % 50 == 0:
                utils.append_to_excel(clause_df, output_name)
                clause_df = pd.DataFrame(columns=['pdfID', 'original_content', 'modified_content', 'category'])
        
        # 保存剩余的数据
        if not clause_df.empty:
            utils.append_to_excel(clause_df, output_name)
        

if __name__ == "__main__":
    get_clause = Clause()
    input_file_name = 'announcement_pdf_list.xlsx'
    input_full_path = os.path.join(get_clause.results_dir, input_file_name)
    output_file_name = 'announcement_list_with_concrete_clause.xlsx'
    output_full_path = os.path.join(get_clause.results_dir, output_file_name)
    utils.remove_file(output_full_path)
    utils.ensure_file_exists(output_full_path)
    get_clause.process(input_full_path, output_full_path)
    # clause_df = pd.DataFrame(columns=['pdfID', 'original_content', 'modified_content', 'category'])
    # clause_df = get_clause.extract_pdf_table_info("downloads/000089_深圳机场/20201029_深圳机场：《深圳市机场股份有限公司章程》修正案.pdf",  100000, clause_df)
    # import pdb
    # pdb.set_trace()