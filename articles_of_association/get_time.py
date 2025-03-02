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

def chinese_to_arabic_num(chinese_num):
    """将中文数字转换为阿拉伯数字"""
    num_map = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
        '十': 10, '十一': 11, '十二': 12, '十三': 13,
        '十四': 14, '十五': 15, '十六': 16, '十七': 17,
        '十八': 18, '十九': 19, '二十': 20, '二十一': 21,
        '二十二': 22, '二十三': 23, '二十四': 24, '二十五': 25,
        '二十六': 26, '二十七': 27, '二十八': 28, '二十九': 29,
        '三十': 30, '三十一': 31, '〇': 0, '0': 0, '1': 1,
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
        '8':8, '9':9, '○':0
    }
    result = 0
    temp = 0
    for char in chinese_num:
        if char in num_map:
            if num_map[char] == 10:
                result += temp * 10
                temp = 0
            else:
                temp = temp * 10 + num_map[char]
        else:
            raise ValueError(f"未知的中文数字: {char}")
    result += temp
    return result

class GetTime:
    def __init__(self):
        # 创建结果目录
        self.results_dir = 'results'
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    def format_date(self,date_str):
        # 去除日期字符串中的空格和换行符
        date_str = date_str.replace(' ', '').replace('\n', '')
        """格式化日期字符串为YYYY-MM-DD"""
        try:
            date_str_n = date_str.replace('年', '-').replace('月', '-').replace('日', '')
            return parser.parse(date_str_n).strftime('%Y-%m-%d')
        except parser.ParserError:
            # 尝试将中文数字转换为阿拉伯数字
            parts = date_str.split('年')
            year = chinese_to_arabic_num(parts[0])
            parts = parts[1].split('月')
            month = chinese_to_arabic_num(parts[0])
            day = chinese_to_arabic_num(parts[1].replace('日', ''))
            return f"{year:04d}-{month:02d}-{day:02d}"
        except Exception as e:
            print(f"日期解析失败: {date_str} - {e}")
            return None

    def extract_basic_info(self, text):
        """提取基本信息"""
        info = {
            'board_meeting_date': None,  # 董事会议案公告日期
            'shareholders_meeting_date': None,  # 股东大会决议公告日期
        }
        board_patterns = [
            r'董事会.*?(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)',
            r'(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日).*?董事会',
            r'董事会.*?([一二三四五六七八九十○〇零一二三四五六七八九十]+\s*年\s*[一二三四五六七八九十○〇零一二三四五六七八九十]+\s*月\s*[一二三四五六七八九十○〇零一二三四五六七八九十]+\s*日)'
        ]
        for pattern in board_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                date_str = match.group(1)
                formatted_date = self.format_date(date_str)
                if formatted_date:
                    info['board_meeting_date'] = formatted_date
                    break
            if info['board_meeting_date']:
                break

        shareholders_patterns = [
            r'(\d{4})\s*年\s*年度股东大会',
            r'(\d{4})\s*年\s*.*?股东大会\s*.*?审议',
            r'(\d{4})\s*年度股东大会',
            r'(\d{4})\s*年\s*股东大会',
            r'(\d{4})\s*股东大会'
        ]

        for pattern in shareholders_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                year = match.group(1)
                info['shareholders_meeting_date'] = year
                break

        return info

    def process(self, input_name, output_name):
        # 读取输入的Excel文件
        input_df = pd.read_excel(input_name)
        
        # 创建一个新的DataFrame来存储扩展后的数据
        existing_df = pd.DataFrame(columns=['pdfID', 'filenames', 'stocks', 'board_meeting_data', 'shareholders_meeting_data', 'pdf_link'])
        
        # 使用tqdm显示进度条
        for idx, row in tqdm(input_df.iterrows(), total=input_df.shape[0]):
            pdf_path = row['filenames']
            stock = str(row['stocks']).zfill(6)
            pdf_link = row['pdf_link']
            if not utils.contains_revision(pdf_path):
                print(f"skip this file: {pdf_path}")
                continue
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    # 读取所有页面
                    text = ''
                    for page in pdf.pages:
                        text += page.extract_text() + '\n'
                    
                    # 提取基本信息
                    basic_info = self.extract_basic_info(text)
                    
                    # 更新existing_df中对应行的信息
                    existing_df.at[idx, 'pdfID'] = row['pdfID']
                    existing_df.at[idx, 'filenames'] = pdf_path
                    existing_df.at[idx, 'stocks'] = stock
                    existing_df.at[idx, 'pdf_link'] = pdf_link
                    existing_df.at[idx, 'board_meeting_data'] = basic_info['board_meeting_date']
                    existing_df.at[idx, 'shareholders_meeting_data'] = basic_info['shareholders_meeting_date']
                    
            except Exception as e:
                print(f"处理PDF出错: {e}")
                continue
        # 每5个数据保存一次并清空existing_df
            if (idx + 1) % 50 == 0:
                utils.append_to_excel(existing_df, output_name)
                existing_df = pd.DataFrame(columns=['pdfID', 'filenames', 'stocks', 'board_meeting_data', 'shareholders_meeting_data', 'pdf_link'])
        
        # 保存剩余的数据
        if not existing_df.empty:
            utils.append_to_excel(existing_df, output_name)
        

if __name__ == "__main__":
    get_time = GetTime()
    input_file_name = 'announcement_pdf_list.xlsx'
    input_full_path = os.path.join(get_time.results_dir, input_file_name)
    output_file_name = 'announcement_list_with_time.xlsx'
    output_full_path = os.path.join(get_time.results_dir, output_file_name)
    utils.remove_file(output_full_path)
    utils.ensure_file_exists(output_full_path)
    get_time.process(input_full_path, output_full_path)