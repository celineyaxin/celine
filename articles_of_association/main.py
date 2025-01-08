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


class CninfoSpider:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
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

        return all_announcements

    def download_announcement(self, announcement):
        """下载单个公告"""
        try:
            # 提取公告信息
            title = self.clean_filename(announcement['announcementTitle'])
            date = announcement['announcementTime']
            date_str = datetime.fromtimestamp(date / 1000).strftime('%Y%m%d')
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
            'pdf_url': None,  # PDF链接
        }

        # 提取董事会议案公告日期
        board_patterns = [
            r'董事会.*?(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{4}年\d{1,2}月\d{1,2}日).*?董事会'
        ]

        for pattern in board_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                try:
                    date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
                    info['board_meeting_date'] = parser.parse(date_str).strftime('%Y-%m-%d')
                    break
                except:
                    continue

        # 提取股东大会决议公告日期（从年度股东大会的年份）
        shareholders_patterns = [
            r'(\d{4})年年度股东大会',
            r'(\d{4})年.*?股东大会.*?审议'
        ]

        for pattern in shareholders_patterns:
            match = re.search(pattern, text)
            if match:
                year = match.group(1)
                info['shareholders_meeting_date'] = year
                break

        # 提取PDF链接
        url_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        ]

        for pattern in url_patterns:
            match = re.search(pattern, text)
            if match:
                info['pdf_url'] = match.group(0)
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

    def extract_article_changes(self, text):
        """提取章程修改内容"""
        changes = []

        # 分割文本为行
        lines = text.split('\n')
        current_original = None
        current_modified = None

        for i, line in enumerate(lines):
            # 检查是否是条款行
            article_match = re.search(r'第[一二三四五六七八九十百千]+条', line)
            if article_match:
                # 如果有未处理的条款，先保存
                if current_original is not None or current_modified is not None:
                    # 对内容进行分类
                    category = self.classify_article_content(current_modified or current_original)
                    changes.append({
                        'original_content': current_original,
                        'modified_content': current_modified,
                        'category': category
                    })

                # 重置当前条款
                current_original = None
                current_modified = None

                # 判断是原始内容还是修改内容
                if '原' in line or '修改前' in line:
                    current_original = line.strip()
                elif '修改后' in line or '现' in line:
                    current_modified = line.strip()
                else:
                    # 如果没有明确标识，根据上下文判断
                    if i > 0 and ('原' in lines[i - 1] or '修改前' in lines[i - 1]):
                        current_original = line.strip()
                    elif i > 0 and ('修改后' in lines[i - 1] or '现' in lines[i - 1]):
                        current_modified = line.strip()
            else:
                # 继续累积当前条款的内容
                if current_original is not None:
                    current_original += ' ' + line.strip()
                elif current_modified is not None:
                    current_modified += ' ' + line.strip()

        # 处理最后一个条款
        if current_original is not None or current_modified is not None:
            category = self.classify_article_content(current_modified or current_original)
            changes.append({
                'original_content': current_original,
                'modified_content': current_modified,
                'category': category
            })

        return changes

    def process_stock_list(self, stock_list):
        """处理股票列表"""
        try:
            # 读取现有的Excel文件
            excel_path = '股票代码.xlsx'  # 修改为与main函数相同的文件名
            if os.path.exists(excel_path):
                existing_df = pd.read_excel(excel_path)
                # 添加所需的列
                if 'pdf链接' not in existing_df.columns:
                    existing_df.insert(1, 'pdf链接', None)  # 在第二列插入
                if '董事会议案公告日期' not in existing_df.columns:
                    existing_df.insert(2, '董事会议案公告日期', None)  # 在第三列插入
                if '股东大会决议公告日期' not in existing_df.columns:
                    existing_df.insert(3, '股东大会决议公告日期', None)  # 在第四列插入
            else:
                raise FileNotFoundError("未找到股票代码Excel文件")

            # 创建章程修改DataFrame
            article_changes_data = []

            for stock in tqdm(stock_list, desc="处理公司进度"):
                print(f"\n正在处理: {stock}")
                announcements = self.search_announcements(stock)

                if not announcements:
                    print(f"未找到{stock}的相关公告")
                    continue

                print(f"找到 {len(announcements)} 份公告")

                # 获取该股票代码在Excel中的所有行
                stock_rows = existing_df[existing_df['Symbol'] == stock].index

                for announcement in tqdm(announcements, desc="下载公告进度"):
                    if "章程" in announcement['announcementTitle'] and "修" in announcement['announcementTitle']:
                        pdf_path = self.download_announcement(announcement)
                        if pdf_path:
                            print(f"成功下载: {announcement['announcementTitle']}")

                            try:
                                with pdfplumber.open(pdf_path) as pdf:
                                    # 读取所有页面
                                    text = ''
                                    for page in pdf.pages:
                                        text += page.extract_text() + '\n'

                                    # 提取基本信息
                                    basic_info = self.extract_basic_info(text)

                                    # 更新Excel中对应行的信息
                                    for idx in stock_rows:
                                        if pd.isna(existing_df.at[idx, 'pdf链接']):
                                            existing_df.at[idx, 'pdf链接'] = basic_info['pdf_url'] or announcement[
                                                'adjunctUrl']
                                        if pd.isna(existing_df.at[idx, '董事会议案公告日期']):
                                            existing_df.at[idx, '董事会议案公告日期'] = basic_info['board_meeting_date']
                                        if pd.isna(existing_df.at[idx, '股东大会决议公告日期']):
                                            existing_df.at[idx, '股东大会决议公告日期'] = basic_info[
                                                'shareholders_meeting_date']

                                    # 提取章程修改内容
                                    changes = self.extract_article_changes(text)
                                    for change in changes:
                                        article_changes_data.append({
                                            'stock_code': announcement['secCode'],
                                            'announce_date': datetime.fromtimestamp(
                                                announcement['announcementTime'] / 1000).strftime('%Y-%m-%d'),
                                            'original_content': change['original_content'],
                                            'modified_content': change['modified_content'],
                                            'category': change['category']
                                        })
                            except Exception as e:
                                print(f"处理PDF出错 {pdf_path}: {e}")
                                continue

                        time.sleep(1)  # 避免请求过快

            # 保存更新后的Excel文件
            existing_df.to_excel(excel_path, index=False)
            print(f"\n基本信息已更新到: {excel_path}")

            # 保存章程修改内容到新的Excel文件
            if article_changes_data:
                changes_path = os.path.join(self.results_dir, 'article_changes.xlsx')
                df_changes = pd.DataFrame(article_changes_data)
                df_changes.columns = ['股票代码', '公告日期', '原始内容', '修改内容', '分类']

                # 创建Excel写入器
                with pd.ExcelWriter(changes_path, engine='openpyxl') as writer:
                    # 保存完整数据到第一个sheet
                    df_changes.to_excel(writer, sheet_name='全部修改内容', index=False)

                    # 按分类创建不同的sheet
                    for category in self.category_keywords.keys():
                        category_df = df_changes[df_changes['分类'] == category]
                        if not category_df.empty:
                            category_df.to_excel(writer, sheet_name=category, index=False)

                    # 其他类别
                    other_df = df_changes[df_changes['分类'] == '其他']
                    if not other_df.empty:
                        other_df.to_excel(writer, sheet_name='其他', index=False)

                print(f"\n章程修改内容已保存到: {changes_path}")

        except Exception as e:
            print(f"处理过程出错: {e}")
            return

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
        stock_list = ['600159']
        print(f"使用默认股票代码: {stock_list}")
        spider.process_stock_list(stock_list)


if __name__ == "__main__":
    main()
