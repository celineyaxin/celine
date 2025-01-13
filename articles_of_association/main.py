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
        '三十': 30, '三十一': 31, '〇': 0
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
            import pdb
            pdb.set_trace()
            raise ValueError(f"未知的中文数字: {char}")
    result += temp
    return result

def contains_revision(filename):
    """判断文件名中的括号内是否包含'修订'两个字"""
    # 使用正则表达式查找括号内的内容
    patterns = [
        r'（[^）]*修订[^）]*）',
        r'（[^）]*修正稿[^）]*）?',
        r'\([^\)]*修订[^\)]*\)',
        r'\([^\)]*修正稿[^\)]*\)?'
    ]
    for pattern in patterns:
        matches = re.finditer(pattern, filename, re.IGNORECASE | re.DOTALL)
        # 将迭代器转换为列表
        matches_list = list(matches)
        # import pdb
        # pdb.set_trace()
        if matches_list:
            return False # 如果找到匹配项，返回 False；否则返回 True
    return True

class CninfoSpider:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.search_url = 'http://www.cninfo.com.cn/new/fulltextSearch/full'
        self.download_url = 'http://static.cninfo.com.cn/'
        self.head_keyword = ["序号", "条款"]
        self.original_keyword = ["原内容","原章程","原条款","原规定","原规则","原规章","原规范","原第", "原议事", "现条款", "修订前", "原《公司章程》", "原表述"]
        self.modified_keyword = ["修改后","修订后","修订为","现修订","修改为","修订为", "新增", "变更后", "变更为", "修订条款", "修订规定", "修订规则", "修订规章", "修订规范", "修订第", "增加第", "改为：", "更为：", "更改为", "删除", "改为第", "改为“"]
        self.taboo_keyword = ["审议机构", "修订内容"]
        self.append_keyword = ["增加第", "新增第", "新增一"]
        self.break_page_keyword = ["附：《公司章程"]
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

    def format_date(self,date_str):
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

            # # 创建北京时间时区对象
            # beijing_tz = pytz.timezone('Asia/Shanghai')

            # # 将 UTC 时间转换为北京时间
            # beijing_date = utc_date.astimezone(beijing_tz)

            # 格式化为 YYYYMMDD 格式的字符串
            date_str = utc_date.strftime('%Y%m%d')
            # import pdb
            # pdb.set_trace()
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

    def extract_meeting_date(self, text):
        """从文本中提取会议日期"""
        # 匹配常见的会议日期模式
        patterns = [
            r'(\d{4}年\d{1,2}月\d{1,2}日).*?召开',
            r'于(\d{4}年\d{1,2}月\d{1,2}日).*?举行',
            r'(\d{4}年\d{1,2}月\d{1,2}日).*?表决',
            r'(\d{4}.*?\d{1,2}.*?\d{1,2}.*?)召开',
            r'(\d{4}.*?\d{1,2}.*?\d{1,2}.*?)举行',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                try:
                    # 统一日期格式
                    date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
                    parsed_date = parser.parse(date_str)
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    continue
        return None

    def extract_shareholders_meeting_info(self, text):
        """提取股东大会相关信息"""
        info = {
            'shareholders_meeting': None,  # 股东大会名称
            'meeting_type': None,  # 会议类型
            'need_approval': False,  # 是否需要提交股东大会审议
            'exchange_website': None  # 交易所网站
        }

        # 匹配股东大会名称和类型
        meeting_patterns = [
            r'(\d{4}年.*?股东大会)',
            r'(\d{4}年.*?临时股东大会)',
            r'(第.*?次.*?股东大会)'
        ]

        for pattern in meeting_patterns:
            match = re.search(pattern, text)
            if match:
                info['shareholders_meeting'] = match.group(1)
                if '临时' in match.group(1):
                    info['meeting_type'] = '临时股东大会'
                else:
                    info['meeting_type'] = '年度股东大会'
                break

        # 匹配是否需要提交股东大会审议
        if re.search(r'需.*?提交.*?股东大会.*?审议', text) or re.search(r'尚需.*?股东大会.*?审议', text):
            info['need_approval'] = True

        # 匹配交易所网站
        website_patterns = [
            r'(上海证券交易所网站.*?)\)',
            r'(深圳证券交易所网站.*?)\)',
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        ]

        for pattern in website_patterns:
            match = re.search(pattern, text)
            if match:
                info['exchange_website'] = match.group(1)
                break

        return info

    def extract_info_from_pdf(self, pdf_path):
        """从PDF中提取信息"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 只读取前几页，通常会议信息在开头
                text = ''
                for i in range(min(3, len(pdf.pages))):
                    text += pdf.pages[i].extract_text()

                # 提取会议日期
                meeting_date = self.extract_meeting_date(text)

                # 提取股东大会信息
                shareholders_info = self.extract_shareholders_meeting_info(text)

                return {
                    'pdf_path': pdf_path,
                    'meeting_date': meeting_date,
                    'first_page_text': text[:1000],  # 保存前1000个字符用于调试
                    'shareholders_meeting': shareholders_info['shareholders_meeting'],
                    'meeting_type': shareholders_info['meeting_type'],
                    'need_approval': shareholders_info['need_approval'],
                    'exchange_website': shareholders_info['exchange_website']
                }
        except Exception as e:
            print(f"PDF处理出错 {pdf_path}: {e}")
            return {
                'pdf_path': pdf_path,
                'meeting_date': None,
                'first_page_text': None,
                'shareholders_meeting': None,
                'meeting_type': None,
                'need_approval': None,
                'exchange_website': None
            }

    def extract_basic_info(self, text):
        """提取基本信息"""
        info = {
            'board_meeting_date': None,  # 董事会议案公告日期
            'shareholders_meeting_date': None,  # 股东大会决议公告日期
        }
        board_patterns = [
            r'董事会.*?(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)',
            r'(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日).*?董事会',
            r'董事会.*?([一二三四五六七八九十〇零一二三四五六七八九十]+\s*年\s*[一二三四五六七八九十〇零一二三四五六七八九十]+\s*月\s*[一二三四五六七八九十〇零一二三四五六七八九十]+\s*日)'
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
            if any(keyword in line for keyword in self.break_page_keyword):
                break
            if any(keyword in line for keyword in self.append_keyword):
                not_append = False
            if any(keyword in line for keyword in self.original_keyword):
                not_append = True
            if any(keyword in line for keyword in self.modified_keyword):
                enable_original = False
                enable_modified = True
            # 检查是否是条款行
            article_match = re.search(r'(第[一二三四五六七八九十百千]+条)(?=.+)', line)
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
                
                if any(keyword in line for keyword in self.modified_keyword):
                    enable_original = False
                    enable_modified = True
                
                # 如果有未处理的条款，先保存
                if current_original != "" or current_modified != "":
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
                current_original = ""
                current_modified = ""

                # 判断是原始内容还是修改内容
                if enable_modified:
                    current_modified = line
                elif enable_original:
                    current_original = line  
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
        original_index = 0
        modified_index = 0
        special_case = False
        finded_head = False
        table_original = "123"
        table_modified = "456"
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                tables = [item for sublist in tables for item in sublist]
                # import pdb
                # pdb.set_trace()
                if tables:
                    for table in tables:
                        if len(table) > 5:
                            table = [item for item in table if item is not None and item != ""]
                        if len(table) == 2:
                            if  any(keyword in table[0] for keyword in self.original_keyword) and any(keyword in table[1] for keyword in self.modified_keyword):
                                finded_head = True
                                enable_case1 = False
                                enable_write = True
                                continue
                            if enable_write and not enable_case1:
                                current_original = table[0]
                                current_modified = table[1]
                            if any(keyword in table[0] for keyword in self.head_keyword) and any(keyword in table[1] for keyword in self.modified_keyword):
                                finded_head = True
                                enable_case1 = True
                                enable_write = True
                                continue
                            if enable_write and enable_case1:
                                current_original = None
                                current_modified = table[1]
                            if any(keyword in table[1] for keyword in self.taboo_keyword) :
                                enable_write = False
                        if len(table) == 3:
                            if  any(keyword in table[1] for keyword in self.original_keyword) \
                            and any(keyword in table[2] for keyword in self.modified_keyword):
                                finded_head = True
                                enable_write = True
                                continue
                            current_original = table[1]
                            current_modified = table[2]
                            if any(keyword in table[1] for keyword in self.taboo_keyword) or any(keyword in table[2] for keyword in self.taboo_keyword):
                                enable_write = False
                                continue
                        if len(table) == 4:
                            if  any(keyword in table[1] for keyword in self.original_keyword) \
                            and any(keyword in table[3] for keyword in self.modified_keyword):
                                finded_head = True
                                enable_write = True
                                continue
                            current_original = table[1]
                            current_modified = table[3]
                            if any(keyword in table[1] for keyword in self.taboo_keyword) or any(keyword in table[2] for keyword in self.taboo_keyword):
                                enable_write = False
                                continue
                        if not finded_head and not special_case:
                            for index, item in enumerate(table):    
                                for keyword in self.original_keyword:
                                    if keyword in item:
                                        table_original = table
                                        original_index = index
                                for keyword in self.modified_keyword:
                                    if keyword in item:
                                        table_modified = table
                                        modified_index = index
                            if table_original is table_modified:
                                finded_head = True
                                enable_write = True
                                special_case = True
                                continue
                        if special_case and finded_head:
                            current_original = table[original_index]
                            current_modified = table[modified_index]
                        if enable_write:
                            if len(table) == 5:
                                current_original = table[1] + table[2]
                                current_modified = table[3] + table[4]
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
        # import pdb
        # pdb.set_trace()
        return clause_df


    def process_stock_list(self, stock_list):
        """处理股票列表"""

        excel_path = 'announcement_list.xlsx'
        existing_df = pd.DataFrame(columns=['pdfID','文件名', '股票代码', '董事会议案公告日期', '股东大会决议公告日期', 'pdf链接'])
        clause_df = pd.DataFrame(columns=['pdfID', 'original_content', 'modified_content', 'category'])
        stock_idx = 0
        idx = 0

        for stock in tqdm(stock_list, desc="处理公司进度"):
        # for stock in stock_list:
            print(f"\n正在处理: {stock}")
            stock_idx += 1
            announcements = self.search_announcements(stock)

            if not announcements:
                print(f"未找到{stock}的相关公告")
                continue

            print(f"找到 {len(announcements)} 份公告")

            for announcement in tqdm(announcements, desc="下载公告进度"):
            # for announcement in announcements:
                if "章程" in announcement['announcementTitle'] and "修" in announcement['announcementTitle'] and contains_revision(announcement['announcementTitle']):
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

                                # 提取基本信息
                                basic_info = self.extract_basic_info(text)

                                # 更新Excel中对应行的信息
                                existing_df.at[idx, 'pdfID'] = 100000 + idx
                                existing_df.at[idx, '文件名'] = pdf_path
                                existing_df.at[idx, '股票代码'] = stock
                                existing_df.at[idx, 'pdf链接'] = self.download_url + announcement['adjunctUrl']
                                existing_df.at[idx, '董事会议案公告日期'] = basic_info['board_meeting_date']
                                existing_df.at[idx, '股东大会决议公告日期'] = basic_info[
                                    'shareholders_meeting_date']

                                clause_df = self.extract_pdf_table_info(pdf_path,  100000 + idx, clause_df)

                                time.sleep(1)  # 避免请求过快
                        except Exception as e:
                            print(f"处理PDF出错: {e}")
                            continue
            
        #     # 每5个公告处理后写入文件并清空 DataFrame
        #     if stock_idx % 5 == 0 and stock_idx > 0:
        #         with pd.ExcelWriter(excel_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
        #             existing_df.to_excel(writer, sheet_name='Announcements', index=False, header=False, startrow=writer.sheets['Announcements'].max_row)

        #         with pd.ExcelWriter(clause_excel_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
        #             clause_df.to_excel(writer, sheet_name='Clauses', index=False, header=False, startrow=writer.sheets['Clauses'].max_row)

        #         print(f"\n数据已追加到文件: {excel_path} 和 {clause_excel_path}")
        #         existing_df = pd.DataFrame(columns=['pdfID', '文件名', '股票代码', '董事会议案公告日期', '股东大会决议公告日期', 'pdf链接'])
        #         clause_df = pd.DataFrame(columns=['pdfID', 'original_content', 'modified_content', 'category'])

        # # 最后一次保存剩余的数据
        # if not existing_df.empty or not clause_df.empty:
        #     with pd.ExcelWriter(excel_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
        #         existing_df.to_excel(writer, sheet_name='Announcements', index=False, header=False, startrow=writer.sheets['Announcements'].max_row)

        #     with pd.ExcelWriter(clause_excel_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
        #         clause_df.to_excel(writer, sheet_name='Clauses', index=False, header=False, startrow=writer.sheets['Clauses'].max_row)

        #     print(f"\n剩余数据已追加到文件: {excel_path} 和 {clause_excel_path}")
        # 保存更新后的Excel文件
        existing_df.to_excel(excel_path, index=False)
        print(f"\n基本信息已更新到: {excel_path}")
        clause_df.to_excel('clause_changes.xlsx', index=False)
        print(f"\n章程修改内容已更新到: clause_changes.xlsx")

        # # 保存章程修改内容到新的Excel文件
        # if article_changes_data:
        #     changes_path = os.path.join(self.results_dir, 'article_changes.xlsx')
        #     df_changes = pd.DataFrame(article_changes_data)
        #     df_changes.columns = ['股票代码', '公告日期', '原始内容', '修改内容', '分类']

        #     # 创建Excel写入器
        #     with pd.ExcelWriter(changes_path, engine='openpyxl') as writer:
        #         # 保存完整数据到第一个sheet
        #         df_changes.to_excel(writer, sheet_name='全部修改内容', index=False)

        #         # 按分类创建不同的sheet
        #         for category in self.category_keywords.keys():
        #             category_df = df_changes[df_changes['分类'] == category]
        #             if not category_df.empty:
        #                 category_df.to_excel(writer, sheet_name=category, index=False)

        #         # 其他类别
        #         other_df = df_changes[df_changes['分类'] == '其他']
        #         if not other_df.empty:
        #             other_df.to_excel(writer, sheet_name='其他', index=False)

        #     print(f"\n章程修改内容已保存到: {changes_path}")

        # except Exception as e:
        #     print(f"处理过程出错: {e}")
        #     return

    def read_stock_codes_from_excel(self, excel_path, code_column='Symbol'):
        """从Excel文件中读取股票代码列表"""
        try:
            # 读取Excel文件，将第一列作为字符串读取
            df = pd.read_excel(excel_path, dtype={0: str})

            # 确保股票代码列存在
            if code_column not in df.columns:
                raise ValueError(f"Excel文件中未找到'{code_column}'列")

            # 提取股票代码并去重
            stock_codes = df[code_column].unique().tolist()

            # 移除可能的前导零，然后重新格式化为6位数字
            stock_codes = [str(int(code)).zfill(6) for code in stock_codes if str(code).strip()]

            print(f"从Excel中读取到 {len(stock_codes)} 个股票代码")
            return stock_codes

        except Exception as e:
            print(f"读取Excel文件出错: {e}")
            return []


def main():
    spider = CninfoSpider()

    # 从Excel文件读取股票代码
    excel_path = '股票代码.xlsx'  # Excel文件路径
    if os.path.exists(excel_path):
        stock_list = spider.read_stock_codes_from_excel(excel_path, code_column='Symbol')
        if stock_list:
            spider.process_stock_list(stock_list)
        else:
            print("未能从Excel文件中读取到有效的股票代码")
    else:
        print(f"未找到Excel文件: {excel_path}")
        print("请确保在程序同目录下存在包含股票代码的Excel文件")
        # 使用默认股票代码作为备选
        stock_list = ['000016','000017','000018','000019','000020']
        print(f"使用默认股票代码: {stock_list}")
        spider.process_stock_list(stock_list)
        # clause_df = pd.DataFrame(columns=['pdfID', 'original_content', 'modified_content', 'category'])
        # clause_df = spider.extract_pdf_table_info("downloads/000009_中国宝安/20020528_深宝安Ａ：修改公司章程的预案等.pdf",  100000, clause_df)
        # import pdb
        # pdb.set_trace()
       
# 

if __name__ == "__main__":
    main()
