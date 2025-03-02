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

class CninfoSpider:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.lenMax = 15
        self.search_url = 'http://www.cninfo.com.cn/new/fulltextSearch/full'
        self.download_url = 'http://static.cninfo.com.cn/'
        # 设置重试策略
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        # 创建会话
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 创建下载目录
        self.base_dir = 'downloads'
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

        # 创建结果目录
        self.results_dir = 'results'
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    def clean_filename(self, filename):
        """清理文件名，移除HTML标签和非法字符"""
        # 移除HTML标签
        filename = re.sub(r'<[^>]+>', '', filename)
        # 移除特殊字符
        filename = re.sub(r'[\\/:*?"<>|]', '', filename)
        # 移除多余的空格
        filename = ' '.join(filename.split())
        return filename

    def search_announcements(self, stock_code, keyword='章程', max_page=100):
        """搜索公告"""
        all_announcements = []

        for page in range(max_page):
            params = {
                'pageNum': page,
                'pageSize': 30,
                'category': 'announcement',
                'searchkey': f'{stock_code}+{keyword}',
                'column': 'szse',
                'tabName': 'fulltext',
                'sortName': '',
                'sortType': '',
                'limit': '',
                'seDate': '',
            }

            try:
                response = self.session.post(self.search_url, headers=self.headers, data=params)
                data = response.json()

                if not data['announcements']:
                    break

                all_announcements.extend(data['announcements'])
                time.sleep(2)  # 增加延迟时间

            except Exception as e:
                print(f"搜索出错: {e}")
                time.sleep(5)  # 出错时增加等待时间
                continue

        # 将列表转换为DataFrame
        df = pd.DataFrame(all_announcements)

        # 去除重复项，保持原始顺序
        df_unique = df.drop_duplicates(keep='first')

        # 将DataFrame转换回列表
        unique_announcements = df_unique.to_dict(orient='records')

        return unique_announcements

    def download_announcement(self, announcement):
        """下载单个公告"""
        try:
            # 提取公告信息
            title = self.clean_filename(announcement['announcementTitle'])
            date = announcement['announcementTime']
            # date_str = datetime.fromtimestamp(date / 1000).strftime('%Y%m%d')
            # 将毫秒转换为秒
            date_in_seconds = date / 1000

            # 使用时区感知的对象转换为 UTC 时间
            utc_date = datetime.datetime.fromtimestamp(date_in_seconds, datetime.UTC)

            # 格式化为 YYYYMMDD 格式的字符串
            date_str = utc_date.strftime('%Y%m%d')
            secCode = announcement['secCode']
            secName = self.clean_filename(announcement['secName'])
            adjunctUrl = announcement['adjunctUrl']

            # 创建公司目录
            company_dir = os.path.join(self.base_dir, f"{secCode}_{secName}")
            if not os.path.exists(company_dir):
                os.makedirs(company_dir)

            # 下载文件
            file_url = self.download_url + adjunctUrl
            response = self.session.get(file_url, headers=self.headers)

            # 保存文件
            file_name = f"{date_str}_{title}.pdf"
            file_path = os.path.join(company_dir, file_name)

            with open(file_path, 'wb') as f:
                f.write(response.content)

            return file_path

        except Exception as e:
            print(f"下载出错: {e}")
            time.sleep(5)  # 出错时增加等待时间
            return None

    def process_stock_list(self, stock_list, excel_path):
        """处理股票列表"""
        utils.ensure_file_exists(excel_path)
        existing_df = pd.DataFrame(columns=['pdfID','filenames', 'stocks', 'pdf_link'])
        stock_idx = 0
        idx = 0

        for stock in tqdm(stock_list, desc="处理公司进度"):
            print(f"\n正在处理: {stock}")
            stock_idx += 1
            announcements = self.search_announcements(stock)

            if not announcements:
                print(f"未找到{stock}的相关公告")
                continue

            print(f"找到 {len(announcements)} 份公告")

            for announcement in tqdm(announcements, desc="下载公告进度"):
                if "章程" in announcement['announcementTitle'] and "修" in announcement['announcementTitle'] and utils.contains_revision(announcement['announcementTitle']):
                    pdf_path = self.download_announcement(announcement)
                    if pdf_path:
                        print(f"成功下载: {announcement['announcementTitle']}")
                        idx += 1
                        try:
                            with pdfplumber.open(pdf_path) as pdf:
                                # 读取所有页面
                                text = ''
                                for page in pdf.pages:
                                    text += page.extract_text() + '\n'

                                # 更新Excel中对应行的信息
                                existing_df.at[idx, 'pdfID'] = 100000 + idx
                                existing_df.at[idx, 'filenames'] = pdf_path
                                existing_df.at[idx, 'stocks'] = stock
                                existing_df.at[idx, 'pdf_link'] = self.download_url + announcement['adjunctUrl']

                                time.sleep(1)  # 避免请求过快
                        except Exception as e:
                            print(f"处理PDF出错: {e}")
                            continue
            
            # 每50个公告处理后写入文件并清空 DataFrame
            if stock_idx % 50 == 0 and stock_idx > 0:
                utils.append_to_excel(existing_df, excel_path)
                existing_df = pd.DataFrame(columns=['pdfID', 'filenames', 'stocks', 'pdf_link'])
        
        # 最后一次保存剩余的数据
        if not existing_df.empty:
            utils.append_to_excel(existing_df, excel_path)


def main():
    spider = CninfoSpider()

    # 从Excel文件读取股票代码
    excel_path = 'test_stkcd.xlsx'  # Excel文件路径
    result_file_name = 'announcement_pdf_list.xlsx'
    result_full_path = os.path.join(spider.results_dir, result_file_name)
    utils.remove_file(result_full_path)
    utils.ensure_file_exists(result_full_path)
    if os.path.exists(excel_path):
        stock_list = utils.read_items_from_excel(excel_path, code_column='Symbol')
        stock_list = stock_list
        if stock_list:
            spider.process_stock_list(stock_list, result_full_path)
        else:
            print("未能从Excel文件中读取到有效的股票代码")
    else:
        print(f"未找到Excel文件: {excel_path}")
        print("请确保在程序同目录下存在包含股票代码的Excel文件")
       
# 

if __name__ == "__main__":
    main()
